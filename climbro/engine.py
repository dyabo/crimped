"""
climbro — engine (v1)

Assembles a concrete plan from a validated Config:
  Config -> Macrocycle (periodization) -> per-week session allocation
            + planned bodyweight curve + finger-strength norms + metric flags.

The output (`Plan`) is the single structure the xlsx renderer consumes. This module
contains the scheduling logic but defers phase structure to periodization.py and
norm numbers to norms.py.

Allocation rules (agreed):
- Deterministic by priority. Quality sessions (fingers / limit) go on the freshest
  slots first, spaced apart (never two heavy days back-to-back, >=48h between finger
  sessions). Then volume/technique. Then Zone-2 cardio. Rest fills the remainder.
- If available_days is not given, take the first N weekdays.
- Equipment gates content: no fingerboard -> finger work becomes active pulls / wall;
  no gym -> strength becomes bodyweight/board; wearable gates which metrics exist.
- Mobility/nutrition are optional flags carried through to the renderer.
"""

from __future__ import annotations
from dataclasses import dataclass, field

from .schema import Config, Goal, WEEKDAYS
from .periodization import build_macrocycle, Macrocycle
from . import norms


# --------------------------------------------------------------------------- #
# Session model
# --------------------------------------------------------------------------- #
@dataclass
class Session:
    day: str          # weekday label (Mon..Sun)
    kind: str         # session type (English label, see SESSION_KINDS)
    intent: str       # short descriptor
    quality: bool     # True = high-CNS/fingers (needs freshness & spacing)


# Canonical session kinds (align with the tracker's journal dropdown, English).
K_HANG = "Max hangs"
K_PULLS = "Active pulls"
K_LIMIT = "Limit bouldering"
K_VOL = "Volume / technique"
K_WALL = "Strength on the wall"
K_PE = "Power-endurance"
K_GYM = "Gym strength"
K_Z2 = "Zone 2 cardio"
K_LEAD = "Lead climbing"
K_REST = "Rest / mobility"

FINGER_KINDS = {K_HANG, K_PULLS}
QUALITY_KINDS = {K_HANG, K_PULLS, K_LIMIT}
CLIMBING_KINDS = {K_LIMIT, K_VOL, K_WALL, K_PE, K_LEAD}  # at least one survives any week


# --------------------------------------------------------------------------- #
# Per-phase session "recipe": how many of each kind we want in a normal week.
# Adjusted afterwards for equipment, days available, deload and deficit.
# --------------------------------------------------------------------------- #
def _phase_recipe(phase_key: str, emphasis: str, is_comp: bool) -> dict[str, int]:
    """Desired weekly counts by kind for a full (non-deload) week of this phase."""
    if phase_key == "assess":
        return {K_HANG: 1, K_VOL: 1, K_GYM: 1, K_Z2: 1}
    if phase_key == "base":
        r = {K_HANG: 2, K_LIMIT: 1, K_VOL: 2, K_GYM: 1, K_Z2: 2}
    elif phase_key == "contact":
        r = {K_PULLS: 2, K_LIMIT: 2, K_WALL: 1, K_GYM: 1, K_Z2: 1}
    elif phase_key == "bridge":
        r = {K_PULLS: 1, K_LIMIT: 2, K_PE: 1, K_WALL: 1, K_GYM: 1, K_Z2: 1}
    elif phase_key == "peak":
        r = {K_LIMIT: 2, K_PULLS: 1, K_PE: 1, K_GYM: 1, K_Z2: 1}
        if is_comp:
            r[K_PE] = 2  # comp simulations weigh more
    elif phase_key == "taper":
        r = {K_LIMIT: 1, K_VOL: 1, K_PE: 1, K_Z2: 1}
    else:
        r = {K_VOL: 2, K_Z2: 1}

    # emphasis tilt
    if emphasis == "technique":
        r[K_VOL] = r.get(K_VOL, 0) + 1
    elif emphasis == "power":
        r[K_LIMIT] = r.get(K_LIMIT, 0) + (1 if phase_key in ("bridge", "peak") else 0)
    return r


# --------------------------------------------------------------------------- #
# Equipment adaptation
# --------------------------------------------------------------------------- #
def _apply_lead(recipe: dict[str, int], phase_key: str, cfg: Config) -> dict[str, int]:
    """
    If the user opted into lead/rope sessions, convert ONE weekly slot per phase rules:
      - base / contact: replaces a volume/technique slot (skill + time-under-tension);
        falls back to wall-strength, then Zone 2 if no volume slot exists.
      - bridge / peak: takes the power-endurance slot (linked routes / route 4x4s).
      - assess / taper: no lead (tests / freshness).
    Never more than one lead session per week — routes create pump-adaptation
    interference with max strength if overdone during a boulder-focused cycle.
    """
    if not cfg.options.include_lead:
        return recipe
    r = dict(recipe)
    if phase_key in ("base", "contact"):
        for k in (K_VOL, K_WALL, K_Z2):
            if r.get(k, 0) > 0:
                r[k] -= 1
                if r[k] == 0:
                    del r[k]
                r[K_LEAD] = r.get(K_LEAD, 0) + 1
                break
    elif phase_key in ("bridge", "peak"):
        for k in (K_PE, K_VOL, K_WALL):
            if r.get(k, 0) > 0:
                r[k] -= 1
                if r[k] == 0:
                    del r[k]
                r[K_LEAD] = r.get(K_LEAD, 0) + 1
                break
    return r


def _adapt_for_equipment(recipe: dict[str, int], cfg: Config) -> dict[str, int]:
    r = dict(recipe)
    eq = cfg.equipment
    # no fingerboard -> hangs become active pulls; pulls also fine without board
    if not eq.has_fingerboard and K_HANG in r:
        r[K_PULLS] = r.get(K_PULLS, 0) + r.pop(K_HANG)
    # active pulls / wall need *something* to pull on; if no board and no fingerboard,
    # keep active pulls (can be done on edges/rungs), but strength-on-the-wall needs a
    # system board -> fold into limit if absent.
    if not eq.has_system_board and K_WALL in r:
        r[K_LIMIT] = r.get(K_LIMIT, 0) + r.pop(K_WALL)
    # no gym -> strength folds into limit/pulls (bodyweight + board strength)
    if not eq.has_gym and K_GYM in r:
        moved = r.pop(K_GYM)
        r[K_PULLS] = r.get(K_PULLS, 0) + moved
    return r


# --------------------------------------------------------------------------- #
# Fit the recipe to the number of training days available
# --------------------------------------------------------------------------- #
# Drop priority when we have FEWER days than the recipe wants (cut least-important first).
_DROP_ORDER = [K_Z2, K_GYM, K_VOL, K_LEAD, K_WALL, K_PE, K_PULLS, K_LIMIT, K_HANG]
# Add priority when we have MORE days than the recipe needs.
_ADD_ORDER = [K_VOL, K_Z2, K_LIMIT, K_PULLS]


def _fit_to_days(recipe: dict[str, int], n_days: int, deload: bool) -> dict[str, int]:
    r = {k: v for k, v in recipe.items() if v > 0}

    if deload:
        r = {k: max(1, v // 2) for k, v in r.items()}

    # never schedule 7 training days: cap capacity at 6 so a full-rest day always exists
    capacity = min(n_days, 6)

    def qtotal() -> int:
        return sum(r.get(k, 0) for k in QUALITY_KINDS)

    def ftotal() -> int:
        return sum(r.get(k, 0) for k in FINGER_KINDS)

    def ctotal() -> int:
        return sum(r.get(k, 0) for k in CLIMBING_KINDS)

    def clean():
        return {k: v for k, v in r.items() if v > 0}

    # ---- cap quality sessions so there's always recovery headroom ----
    # ~60% of training days may be high-CNS; on 2-3 day schedules allow up to 2
    # (rest days between cover recovery). Keep >=1 finger and (if room) >=1 limit.
    qmax = max(min(2, capacity), round(capacity * 0.6))
    while qtotal() > qmax:
        keep_limit = 1 if qmax >= 2 else 0
        if r.get(K_LIMIT, 0) > keep_limit:
            r[K_LIMIT] -= 1
        elif ftotal() > 1:
            for fk in (K_PULLS, K_HANG):
                if r.get(fk, 0) > 0:
                    r[fk] -= 1
                    break
        elif r.get(K_LIMIT, 0) > 0 and ftotal() >= 1:
            r[K_LIMIT] -= 1
        else:
            break
        r = clean()

    total = sum(r.values())

    # ---- too many sessions -> drop by priority (protect >=1 finger, >=1 climbing) ----
    while total > capacity:
        dropped = False
        for k in _DROP_ORDER:
            if r.get(k, 0) > 0:
                if k in FINGER_KINDS and ftotal() <= 1:
                    continue
                if k in CLIMBING_KINDS and ctotal() <= 1:
                    continue
                r[k] -= 1
                if r[k] == 0:
                    del r[k]
                total -= 1
                dropped = True
                break
        if not dropped:
            break

    # ---- fewer sessions than capacity -> pad, never exceeding the quality cap ----
    while total < capacity:
        added = False
        for k in _ADD_ORDER:
            if total >= capacity:
                break
            if k in QUALITY_KINDS and qtotal() >= qmax:
                continue
            cap = 2 if k in FINGER_KINDS else (3 if k == K_LIMIT else 4)
            if r.get(k, 0) < cap:
                r[k] = r.get(k, 0) + 1
                total += 1
                added = True
        if not added:
            break
    return r


# --------------------------------------------------------------------------- #
# Lay sessions onto specific weekdays with freshness spacing
# --------------------------------------------------------------------------- #
def _order_days(cfg: Config) -> list[str]:
    if cfg.availability.available_days:
        # keep canonical Mon..Sun order regardless of input order
        return [d for d in WEEKDAYS if d in cfg.availability.available_days]
    return WEEKDAYS[: cfg.availability.days_per_week]


def _schedule_week(recipe: dict[str, int], train_days: list[str]) -> list[Session]:
    """
    Place sessions on the given training weekdays so that:
    - quality (fingers/limit) land first and are spaced (no two adjacent),
    - then volume/wall/PE, then cardio, then rest fills any leftover day.
    """
    # build flat ordered list of sessions to place, quality first
    def intent_of(kind: str) -> str:
        return {
            K_HANG: "Max hangs on 20mm, fresh, before climbing",
            K_PULLS: "Active recruitment pulls into a fixed edge",
            K_LIMIT: "Limit bouldering, long rests, fresh",
            K_VOL: "Volume + footwork/technique, sub-limit",
            K_WALL: "Strength on the wall (system board), 4-7s holds",
            K_PE: "Power-endurance (4x4 / intervals / comp sim)",
            K_GYM: "Weighted pulls, antagonists, core",
            K_Z2: "Easy aerobic, conversational pace",
            K_LEAD: "Routes on a rope: mileage below limit (base) or linked circuits for power-endurance (bridge/peak); log honest RPE",
            K_REST: "Rest or mobility",
        }[kind]

    quality, secondary, easy = [], [], []
    for kind, n in recipe.items():
        for _ in range(n):
            (quality if kind in QUALITY_KINDS else
             easy if kind in (K_Z2,) else secondary).append(kind)
    # order quality so fingers come before limit when they share scheduling
    quality.sort(key=lambda k: 0 if k in FINGER_KINDS else 1)

    slots = {d: None for d in train_days}
    wd_idx = {d: WEEKDAYS.index(d) for d in train_days}  # real Mon..Sun positions

    # ---- place quality on maximally-spaced days (farthest-point) ----
    # seed with the two extreme training days, then repeatedly add the day whose
    # nearest already-chosen day is farthest (ties -> smallest weekday index).
    def pick_quality_days(k: int) -> list[str]:
        if k <= 0:
            return []
        days = sorted(train_days, key=lambda d: wd_idx[d])
        if k == 1:
            return [days[0]]
        chosen = [days[0], days[-1]]
        while len(chosen) < min(k, len(days)):
            best, best_dist = None, -1
            for d in days:
                if d in chosen:
                    continue
                dist = min(abs(wd_idx[d] - wd_idx[c]) for c in chosen)
                if dist > best_dist:
                    best, best_dist = d, dist
            chosen.append(best)
        # keep only k, ordered by weekday
        return sorted(chosen[:k], key=lambda d: wd_idx[d])

    qdays = pick_quality_days(len(quality))
    # assign FINGER sessions to the most-spaced quality days (>=48h apart),
    # limit sessions take the remaining quality days.
    fingers = [k for k in quality if k in FINGER_KINDS]
    others = [k for k in quality if k not in FINGER_KINDS]

    def even_indices(n: int, m: int) -> list[int]:
        if m <= 0 or n <= 0:
            return []
        if m == 1:
            return [0]
        return sorted({round(i * (n - 1) / (m - 1)) for i in range(m)})

    finger_pos = even_indices(len(qdays), len(fingers))
    used = set()
    for pos, item in zip(finger_pos, fingers):
        slots[qdays[pos]] = item
        used.add(pos)
    leftover_positions = [i for i in range(len(qdays)) if i not in used]
    for pos, item in zip(leftover_positions, others):
        slots[qdays[pos]] = item

    # ---- cross-week guard: the pattern repeats weekly, so a finger session on the
    # last weekday + one on the first weekday means <48h across the week boundary.
    fdays = sorted((d for d in train_days if slots[d] in FINGER_KINDS), key=lambda d: wd_idx[d])
    if len(fdays) >= 2:
        cross_gap = 7 - wd_idx[fdays[-1]] + wd_idx[fdays[0]]
        if cross_gap < 2:
            # swap the last finger day with the latest earlier quality slot
            # that holds a non-finger session (e.g. a limit day)
            candidates = [d for d in qdays
                          if slots[d] is not None and slots[d] not in FINGER_KINDS
                          and wd_idx[d] < wd_idx[fdays[-1]]]
            if candidates:
                swap = max(candidates, key=lambda d: wd_idx[d])
                slots[swap], slots[fdays[-1]] = slots[fdays[-1]], slots[swap]

    def place_fill(items):
        for it in items:
            for d in sorted(train_days, key=lambda x: wd_idx[x]):
                if slots[d] is None:
                    slots[d] = it
                    break

    place_fill(secondary)     # skill/strength on remaining days
    place_fill(easy)          # then cardio

    out: list[Session] = []
    for d in WEEKDAYS:
        if d not in slots:
            continue
        kind = slots[d] or K_REST
        out.append(Session(day=d, kind=kind, intent=intent_of(kind),
                            quality=kind in QUALITY_KINDS))
    return out


# --------------------------------------------------------------------------- #
# Weight curve + norms
# --------------------------------------------------------------------------- #
def _weight_curve(cfg: Config, total_weeks: int, deficit_last_week: int) -> list[float | None]:
    """Planned bodyweight per week (1..total_weeks). None if no cut."""
    if not cfg.weight.enabled or cfg.target_bw_kg is None:
        return [None] * total_weeks
    start, target = cfg.bw_kg, cfg.target_bw_kg
    # linear from week 3 to the last deficit week; flat before and after
    lo, hi = 2, max(3, deficit_last_week)  # week index (1-based) boundaries
    curve = []
    for w in range(1, total_weeks + 1):
        if w <= lo:
            curve.append(round(start, 1))
        elif w >= hi:
            curve.append(round(target, 1))
        else:
            frac = (w - lo) / (hi - lo)
            curve.append(round(start + (target - start) * frac, 1))
    return curve


# --------------------------------------------------------------------------- #
# Plan output
# --------------------------------------------------------------------------- #
@dataclass
class WeekPlan:
    week: int
    phase_key: str
    phase_name: str
    focus: str
    deload: bool
    in_deficit: bool
    planned_weight: float | None
    sessions: list[Session]
    planned_session_count: int


@dataclass
class Plan:
    cfg: Config
    macro: Macrocycle
    weeks: list[WeekPlan]
    # headline targets / context
    current_v: int
    target_v: int
    norm_target_pct: float            # finger-strength norm for target grade
    norm_target_added_kg: float       # same, as added kg at current bodyweight
    metrics: dict
    notes: list[str] = field(default_factory=list)


def build_plan(cfg: Config) -> Plan:
    macro = build_macrocycle(cfg)
    rows = macro.week_table()
    total = len(rows)
    is_comp = cfg.goal.goal == Goal.COMPETITION

    # last week that is still in deficit (for the weight curve end-point)
    deficit_weeks = [r["week"] for r in rows if r["in_deficit"]]
    deficit_last = max(deficit_weeks) if deficit_weeks else 0
    wcurve = _weight_curve(cfg, total, deficit_last)

    train_days = _order_days(cfg)

    weeks: list[WeekPlan] = []
    for r in rows:
        recipe = _phase_recipe(r["phase_key"], r["emphasis"], is_comp)
        recipe = _adapt_for_equipment(recipe, cfg)
        recipe = _apply_lead(recipe, r["phase_key"], cfg)
        recipe = _fit_to_days(recipe, len(train_days), r["deload"])
        sessions = _schedule_week(recipe, train_days)
        planned = sum(1 for s in sessions if s.kind != K_REST)
        weeks.append(WeekPlan(
            week=r["week"], phase_key=r["phase_key"], phase_name=r["phase_name"],
            focus=r["focus"], deload=r["deload"], in_deficit=r["in_deficit"],
            planned_weight=wcurve[r["week"] - 1], sessions=sessions,
            planned_session_count=planned,
        ))

    norm_pct = norms.target_pct(cfg.profile.sex, cfg.climbing.target_grade)
    plan = Plan(
        cfg=cfg, macro=macro, weeks=weeks,
        current_v=cfg.climbing.current_grade, target_v=cfg.climbing.target_grade,
        norm_target_pct=norm_pct,
        norm_target_added_kg=norms.pct_to_added_kg(norm_pct, cfg.bw_kg),
        metrics=cfg.metrics,
        notes=list(macro.notes),
    )
    return plan


if __name__ == "__main__":
    from .schema import from_dict
    demo = {
        "profile": {"sex": "male", "units": "kg", "bodyweight": 83},
        "climbing": {"grade_scale": "V", "current_grade": "V5", "target_grade": "V8",
                     "years_climbing": 1, "max_hang_added": 15, "max_pullup_added": 20},
        "goal": {"goal": "competition", "start_date": "2026-06-08", "goal_date": "2026-12-28"},
        "weight": {"enabled": True, "target_bodyweight": 78},
        "availability": {"days_per_week": 6, "available_days": ["Mon", "Tue", "Wed", "Thu", "Sat", "Sun"]},
        "equipment": {"has_fingerboard": True, "has_system_board": True, "has_gym": True, "wearable": "garmin"},
        "options": {"include_mobility": True, "include_nutrition": True},
    }
    cfg = from_dict(demo)
    plan = build_plan(cfg)
    print(f"target V{plan.target_v}: norm {plan.norm_target_pct*100:.0f}%BW (+{plan.norm_target_added_kg}kg @ {cfg.bw_kg})")
    for w in plan.weeks[:4] + plan.weeks[9:11]:
        days = " | ".join(f"{s.day}:{s.kind}" for s in w.sessions)
        wt = f"{w.planned_weight}kg" if w.planned_weight else "-"
        print(f"W{w.week:2d} {w.phase_key:8s} {'(deload)' if w.deload else '        '} {wt:>7} [{w.planned_session_count}] {days}")
