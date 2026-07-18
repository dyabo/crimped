"""
climbro — periodization templates (v1)

Turns a validated Config into an ordered list of Phases with week spans.

Agreed rules:
- Templates, not AI. Two goals coded: SEND_GRADE, COMPETITION.
- "Cut early, peak late": if a cut is enabled, the deficit lives in the first
  half; maintenance/peak in the second half on lighter bodyweight.
- Scaling priority when weeks are tight: the TAPER (fixed) and PEAK are protected;
  early phases (base / contact / deficit) compress first.
- Emphasis adapts to level: a climber with a real strength base + low years tends
  to be technique/relative-strength limited (less raw finger-strength chasing);
  a newer/weaker athlete needs more base + technique.

This module decides PHASE STRUCTURE only (names, focus, week spans, flags).
Session allocation across weekdays + the weight curve + norms live in engine.py.
"""

from __future__ import annotations
from dataclasses import dataclass
from .schema import Config, Goal


# --------------------------------------------------------------------------- #
# Phase model
# --------------------------------------------------------------------------- #
@dataclass
class Phase:
    key: str            # stable id: assess|base|contact|deficit_tail|bridge|peak|taper
    name: str           # human label (English)
    weeks: int          # number of weeks in this phase
    focus: str          # one-line training intent
    in_deficit: bool    # is the cut active during this phase?
    deload_last: bool   # does this phase end with a deload week?
    emphasis: str       # 'technique' | 'strength' | 'power' | 'comp' | 'mixed'


@dataclass
class Macrocycle:
    phases: list[Phase]
    cut_enabled: bool
    notes: list[str]

    @property
    def total_weeks(self) -> int:
        return sum(p.weeks for p in self.phases)

    def week_table(self) -> list[dict]:
        """Flatten to one row per week: {week, phase_key, phase_name, focus, deload, in_deficit, emphasis}."""
        rows, w = [], 0
        for p in self.phases:
            for i in range(p.weeks):
                w += 1
                deload = p.deload_last and (i == p.weeks - 1)
                rows.append({
                    "week": w,
                    "phase_key": p.key,
                    "phase_name": p.name,
                    "focus": p.focus,
                    "deload": deload,
                    "in_deficit": p.in_deficit,
                    "emphasis": p.emphasis,
                })
        return rows


# --------------------------------------------------------------------------- #
# Emphasis decision (level-aware)
# --------------------------------------------------------------------------- #
def _emphasis_profile(cfg: Config) -> dict:
    """
    Decide how much to weight technique vs raw strength, from level + base.
    Returns weights used to label phases and (later) bias session mix.
    """
    years = cfg.climbing.years_climbing
    cur_v = cfg.climbing.current_grade

    # crude 'has a strength base' signal: strong added pull-up relative to nothing,
    # or simply low experience at a non-trivial grade (climbs hard for time spent).
    pull = cfg.climbing.max_pullup_added or 0.0
    strong_base = pull >= 0.20 * cfg.bw_kg or (years <= 2 and cur_v >= 4)

    if years < 1 or cur_v <= 2:
        return {"label": "technique", "tech": 0.5, "strength": 0.3, "power": 0.2,
                "note": "Early climber: technique and base movement dominate; strength is rarely the limiter yet."}
    if strong_base:
        return {"label": "technique", "tech": 0.45, "strength": 0.2, "power": 0.35,
                "note": "Strong base + limited mileage: limiter is technique, contact strength and relative strength — not raw pulling. Bias skill + power application, keep gym to maintenance."}
    # default mid
    return {"label": "mixed", "tech": 0.35, "strength": 0.3, "power": 0.35,
            "note": "Balanced development across technique, strength and power."}


# --------------------------------------------------------------------------- #
# Base templates (ideal week counts) — get scaled to the real horizon
# --------------------------------------------------------------------------- #
def _ideal_phases(cfg: Config, emph: dict) -> list[Phase]:
    cut = cfg.weight.enabled
    is_comp = cfg.goal.goal == Goal.COMPETITION

    phases: list[Phase] = [
        Phase("assess", "Assess & baseline", 2,
              "Tests (max hang, pull-ups, body comp) + baseline HRV/weight. Maintenance eating.",
              in_deficit=False, deload_last=False, emphasis="mixed"),
        Phase("base", "Base — max hangs + technique", 8,
              "Max-hang finger strength + high technique volume." + (" Deficit starts." if cut else ""),
              in_deficit=cut, deload_last=True, emphasis="technique" if emph["label"] != "mixed" else "mixed"),
        Phase("contact", "Contact strength", 8,
              "Active recruitment pulls + strength-on-the-wall; limit bouldering 2x." + (" Deficit continues." if cut else ""),
              in_deficit=cut, deload_last=True, emphasis="strength"),
    ]

    # bridge: exit the deficit / build power; introduce power-endurance
    phases.append(
        Phase("bridge", "Bridge — exit deficit & build power" if cut else "Bridge — build power", 4,
              ("Return to maintenance eating; power rises; introduce power-endurance."
               if cut else "Raise intensity; introduce power-endurance."),
              in_deficit=False, deload_last=True, emphasis="power")
    )

    # peak: protected
    phases.append(
        Phase("peak", "Peak — power & RFD", 5,
              ("Peak contact strength, power and RFD on light bodyweight." if cut
               else "Peak contact strength, power and RFD.")
              + (" Comp-style simulations." if is_comp else ""),
              in_deficit=False, deload_last=False, emphasis="comp" if is_comp else "power")
    )

    # taper: fixed, protected
    taper_weeks = 2 if is_comp else 1
    phases.append(
        Phase("taper", "Taper", taper_weeks,
              ("Volume -50%, intensity held; carb-load into the comp." if is_comp
               else "Volume -50%, intensity held; arrive fresh for the send window."),
              in_deficit=False, deload_last=False, emphasis="comp" if is_comp else "power")
    )
    return phases


# --------------------------------------------------------------------------- #
# Scaling to the real number of weeks
# --------------------------------------------------------------------------- #
# Protected (do not shrink unless we truly run out of weeks), in priority order.
_PROTECTED = ["taper", "peak", "assess"]
# Default compressible order, shrunk first -> last. Overridden per-emphasis.
_SHRINK_DEFAULT = ["base", "contact", "bridge"]
_SHRINK_TECHNIQUE = ["contact", "bridge", "base"]  # protect base/technique for these athletes
_MIN_WEEKS = {"assess": 1, "base": 2, "contact": 2, "bridge": 1, "peak": 2, "taper": 1}
# Soft caps so a long horizon doesn't dump everything into one phase.
_MAX_WEEKS = {"assess": 2, "base": 12, "contact": 10, "bridge": 6, "peak": 7, "taper": 2}
# Round-robin order for distributing extra weeks (quality first).
_PAD_ORDER = ["base", "contact", "peak", "bridge"]


def _scale(phases: list[Phase], target_weeks: int, shrink_order: list[str]) -> tuple[list[Phase], list[str]]:
    notes: list[str] = []
    ideal_total = sum(p.weeks for p in phases)
    by_key = {p.key: p for p in phases}

    if target_weeks == ideal_total:
        return phases, notes

    if target_weeks > ideal_total:
        extra = target_weeks - ideal_total
        # round-robin add, respecting soft caps -> even distribution, no lumps
        progressed = True
        while extra > 0 and progressed:
            progressed = False
            for key in _PAD_ORDER:
                if extra <= 0:
                    break
                if by_key[key].weeks < _MAX_WEEKS[key]:
                    by_key[key].weeks += 1
                    extra -= 1
                    progressed = True
        if extra > 0:
            by_key["base"].weeks += extra  # caps all hit; park remainder in base
            notes.append("Horizon is very long; consider splitting into two cycles.")
        notes.append(f"Horizon longer than the template; distributed {target_weeks - ideal_total} extra week(s) across base/contact/peak/bridge.")
        return list(by_key.values()), notes

    # target < ideal -> shrink compressible phases first, protect peak/taper/assess
    deficit = ideal_total - target_weeks
    for key in shrink_order:
        if deficit <= 0:
            break
        p = by_key[key]
        take = min(p.weeks - _MIN_WEEKS[key], deficit)
        if take > 0:
            p.weeks -= take
            deficit -= take

    if deficit > 0:  # still short: eat into peak down to its minimum
        p = by_key["peak"]
        take = min(p.weeks - _MIN_WEEKS["peak"], deficit)
        p.weeks -= take
        deficit -= take
        notes.append("Very short horizon: had to trim the peak block — consider a later date if possible.")

    if deficit > 0:  # last resort: assess then taper to floor
        for key in ["assess", "taper"]:
            p = by_key[key]
            take = min(p.weeks - _MIN_WEEKS[key], deficit)
            p.weeks -= take
            deficit -= take

    if deficit > 0:
        notes.append(f"Horizon is {deficit} week(s) shorter than even the compressed minimum; phases are at floor — the plan is aggressive.")

    scaled = [p for p in phases if p.weeks > 0]
    notes.append(f"Compressed template from {ideal_total} to {sum(p.weeks for p in scaled)} weeks to fit the date.")
    return scaled, notes


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def build_macrocycle(cfg: Config) -> Macrocycle:
    emph = _emphasis_profile(cfg)
    phases = _ideal_phases(cfg, emph)
    target = max(sum(_MIN_WEEKS[p.key] for p in phases), cfg.total_weeks)
    # technique-limited athletes (newbie or strong-base/low-mileage) keep base longest
    shrink_order = _SHRINK_TECHNIQUE if emph["label"] == "technique" else _SHRINK_DEFAULT
    phases, notes = _scale(phases, target, shrink_order)

    notes.insert(0, emph["note"])
    if cfg.weight.enabled:
        notes.append("Cut is active in the first half (base + contact); maintenance from the bridge phase onward.")
    else:
        notes.append("No cut: deficit phase omitted; eating supports performance throughout.")
    if cfg.total_weeks < sum(_MIN_WEEKS.values()):
        notes.append(f"Only {cfg.total_weeks} weeks available — shorter than the {sum(_MIN_WEEKS.values())}-week compressed minimum.")

    return Macrocycle(phases=phases, cut_enabled=cfg.weight.enabled, notes=notes)


if __name__ == "__main__":
    from .schema import from_dict
    demo = {
        "profile": {"sex": "male", "units": "kg", "bodyweight": 83},
        "climbing": {"grade_scale": "V", "current_grade": "V5", "target_grade": "V8",
                     "years_climbing": 1, "max_pullup_added": 20},
        "goal": {"goal": "competition", "start_date": "2026-06-08", "goal_date": "2026-12-28"},
        "weight": {"enabled": True, "target_bodyweight": 78},
        "availability": {"days_per_week": 6},
        "equipment": {"wearable": "garmin"},
    }
    cfg = from_dict(demo)
    mc = build_macrocycle(cfg)
    print(f"=== {cfg.total_weeks} weeks → {mc.total_weeks} scheduled ===")
    for p in mc.phases:
        print(f"  {p.weeks:2d}w  {p.key:12s} deficit={int(p.in_deficit)} deload={int(p.deload_last)}  {p.name}")
    print("notes:")
    for n in mc.notes:
        print("   -", n)
