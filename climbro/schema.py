"""
climbro — config schema (v1)

Single source of truth for everything the survey collects and the engine reads.

Design rules agreed for v1:
- Language: English or Russian (see i18n.py). `language` drives both the survey
  and the generated workbook; the engine still keys off stable English identifiers.
- Goals coded for v1: SEND_GRADE, COMPETITION. (Others reserved, NOT implemented.)
- Grades: user may pick display scale (V or Font), but everything is normalized
  to an integer V-grade internally for simplicity.
- Weight-loss (cut) block is optional. If disabled, the engine drops the deficit
  phase and the weight curve.
- Mobility block is optional.
- Units kg/lb for display; normalized to kg internally.
- Equipment (fingerboard / system board / gym / wearable) gates which sessions
  and which metrics appear.
- Days-per-week is required and drives session allocation.
- Templates, not AI: the engine will pick + parameterize a periodization template
  from these fields. This file does NOT contain training logic — only inputs.

This module intentionally has no training logic and no hard dependency on PyYAML
(import is local to load/dump so the schema can be used/tested without it).
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import date
from enum import Enum
import math

from .i18n import Language, translator


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #
class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"


class Units(str, Enum):
    KG = "kg"
    LB = "lb"


class GradeScale(str, Enum):
    V = "V"        # Hueco / V-scale
    FONT = "Font"  # Fontainebleau


class Goal(str, Enum):
    SEND_GRADE = "send_grade"     # break a target grade by a date (may include cut)
    COMPETITION = "competition"   # peak for a comp date (adds comp prep + taper)
    # --- reserved for later, NOT implemented in v1 ---
    # STRENGTH = "strength"
    # ENDURANCE = "endurance"
    # GENERAL = "general"


class Wearable(str, Enum):
    GARMIN = "garmin"  # enables HRV + resting HR + Body Battery autoregulation
    OTHER = "other"    # device that tracks HRV/RHR but not Body Battery
    NONE = "none"      # no recovery metrics; advisor falls back to subjective only


WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# --------------------------------------------------------------------------- #
# Grade normalization (everything internal is an int V-grade, 0..17)
# --------------------------------------------------------------------------- #
_V_TO_FONT = {
    0: "4", 1: "5", 2: "5+", 3: "6A", 4: "6B", 5: "6C", 6: "7A", 7: "7A+",
    8: "7B", 9: "7C", 10: "7C+", 11: "8A", 12: "8A+", 13: "8B", 14: "8B+",
    15: "8C", 16: "8C+", 17: "9A",
}
_FONT_TO_V = {
    "4": 0, "4+": 0, "5": 1, "5+": 2,
    "6a": 3, "6a+": 3, "6b": 4, "6b+": 4, "6c": 5, "6c+": 5,
    "7a": 6, "7a+": 7, "7b": 8, "7b+": 8, "7c": 9, "7c+": 10,
    "8a": 11, "8a+": 12, "8b": 13, "8b+": 14, "8c": 15, "8c+": 16, "9a": 17,
}
V_MIN, V_MAX = 0, 17


def parse_grade(scale: GradeScale, raw) -> int:
    """Parse a user grade (in the given display scale) to an internal int V-grade."""
    s = str(raw).strip().lower().replace(" ", "")
    if scale == GradeScale.V:
        s = s.lstrip("v")
        if not s.isdigit():
            raise ValueError(f"Invalid V-grade: {raw!r} (expected e.g. 'V5' or '5')")
        v = int(s)
    else:
        if s not in _FONT_TO_V:
            raise ValueError(f"Invalid Font grade: {raw!r} (expected e.g. '7A', '6C+')")
        v = _FONT_TO_V[s]
    if not (V_MIN <= v <= V_MAX):
        raise ValueError(f"Grade out of supported range V{V_MIN}–V{V_MAX}: {raw!r}")
    return v


def format_grade(scale: GradeScale, v: int) -> str:
    """Render an internal V-grade back into the user's chosen display scale."""
    v = max(V_MIN, min(V_MAX, int(v)))
    return f"V{v}" if scale == GradeScale.V else _V_TO_FONT[v]


# --------------------------------------------------------------------------- #
# Config sections (nested -> map cleanly to YAML sections)
# --------------------------------------------------------------------------- #
@dataclass
class Profile:
    sex: Sex                      # required: norms differ by sex
    bodyweight: float             # in `units`
    units: Units = Units.KG
    age: int | None = None        # optional; lightly affects deload cadence
    name: str | None = None       # optional; only used to personalize the file


@dataclass
class Climbing:
    current_grade: int            # normalized V-int (parsed from display scale)
    target_grade: int             # normalized V-int
    grade_scale: GradeScale = GradeScale.V   # display only
    years_climbing: float = 1.0   # influences technique-vs-strength emphasis
    max_hang_added: float | None = None   # added load on 20 mm, 7 s (in `units`); optional
    max_pullup_added: float | None = None # added load on weighted pull-up (in `units`); optional


@dataclass
class GoalSpec:
    goal: Goal
    goal_date: date               # comp date, or "by when"
    start_date: date = field(default_factory=date.today)


@dataclass
class Weight:
    """Optional cut block. If enabled=False, engine drops deficit phase + weight curve."""
    enabled: bool = False
    target_bodyweight: float | None = None  # required if enabled; in `units`
    max_rate_pct: float = 0.7     # max weekly loss as % of bodyweight (engine clamps)


@dataclass
class Availability:
    days_per_week: int = 4        # required driver of session allocation (2..7)
    available_days: list[str] | None = None  # optional explicit weekdays; len must == days_per_week


@dataclass
class Equipment:
    has_fingerboard: bool = True
    has_system_board: bool = False   # MoonBoard / Kilter / Tension
    has_gym: bool = True             # weights for strength sessions
    wearable: Wearable = Wearable.NONE


@dataclass
class Options:
    include_mobility: bool = False
    include_nutrition: bool = True   # nutrition sheet is useful even without a cut
    include_lead: bool = False       # mix 1 rope/lead session per week into the plan
    output_path: str | None = None   # where to write the xlsx


@dataclass
class Config:
    profile: Profile
    climbing: Climbing
    goal: GoalSpec
    weight: Weight = field(default_factory=Weight)
    availability: Availability = field(default_factory=Availability)
    equipment: Equipment = field(default_factory=Equipment)
    options: Options = field(default_factory=Options)
    language: Language = Language.EN   # UI + workbook language (en | ru)

    # ----- derived helpers (no training logic, just unit/scale normalization) -----
    @property
    def bw_kg(self) -> float:
        return _to_kg(self.profile.bodyweight, self.profile.units)

    @property
    def target_bw_kg(self) -> float | None:
        if not self.weight.enabled or self.weight.target_bodyweight is None:
            return None
        return _to_kg(self.weight.target_bodyweight, self.profile.units)

    @property
    def max_hang_kg(self) -> float | None:
        return None if self.climbing.max_hang_added is None else _to_kg(self.climbing.max_hang_added, self.profile.units)

    @property
    def total_weeks(self) -> int:
        days = (self.goal.goal_date - self.goal.start_date).days
        return max(0, math.ceil(days / 7))

    @property
    def metrics(self) -> dict:
        """Which recovery metrics the file should expose, from the wearable choice."""
        w = self.equipment.wearable
        return {
            "hrv": w in (Wearable.GARMIN, Wearable.OTHER),
            "resting_hr": w in (Wearable.GARMIN, Wearable.OTHER),
            "body_battery": w == Wearable.GARMIN,
        }


# --------------------------------------------------------------------------- #
# Unit helpers
# --------------------------------------------------------------------------- #
_LB_PER_KG = 2.2046226218
LB_PER_KG = _LB_PER_KG  # public alias for render-layer conversion

# Shortest horizon the periodization can compress into (sum of phase floors).
# validate() hard-errors below this; periodization keeps it as a safety net.
MIN_CYCLE_WEEKS = 9


def _to_kg(value: float, units: Units) -> float:
    return round(float(value) / _LB_PER_KG, 2) if units == Units.LB else float(value)


def from_kg(value_kg: float, units: Units) -> float:
    """Convert an internal kg value into the user's display units."""
    return round(value_kg * _LB_PER_KG, 1) if units == Units.LB else round(value_kg, 1)


# --------------------------------------------------------------------------- #
# Build from a plain dict (what YAML / the CLI produces)
# --------------------------------------------------------------------------- #
def from_dict(d: dict) -> Config:
    p = d.get("profile", {})
    c = d.get("climbing", {})
    g = d.get("goal", {})
    scale = GradeScale(c.get("grade_scale", "V"))
    return Config(
        profile=Profile(
            sex=Sex(p["sex"]),
            bodyweight=float(p["bodyweight"]),
            units=Units(p.get("units", "kg")),
            age=p.get("age"),
            name=p.get("name"),
        ),
        climbing=Climbing(
            current_grade=parse_grade(scale, c["current_grade"]),
            target_grade=parse_grade(scale, c["target_grade"]),
            grade_scale=scale,
            years_climbing=float(c.get("years_climbing", 1.0)),
            max_hang_added=c.get("max_hang_added"),
            max_pullup_added=c.get("max_pullup_added"),
        ),
        goal=GoalSpec(
            goal=Goal(g["goal"]),
            goal_date=_as_date(g["goal_date"]),
            start_date=_as_date(g["start_date"]) if g.get("start_date") else date.today(),
        ),
        weight=Weight(
            enabled=bool(d.get("weight", {}).get("enabled", False)),
            target_bodyweight=d.get("weight", {}).get("target_bodyweight"),
            max_rate_pct=float(d.get("weight", {}).get("max_rate_pct", 0.7)),
        ),
        availability=Availability(
            days_per_week=int(d.get("availability", {}).get("days_per_week", 4)),
            available_days=d.get("availability", {}).get("available_days"),
        ),
        equipment=Equipment(
            has_fingerboard=bool(d.get("equipment", {}).get("has_fingerboard", True)),
            has_system_board=bool(d.get("equipment", {}).get("has_system_board", False)),
            has_gym=bool(d.get("equipment", {}).get("has_gym", True)),
            wearable=Wearable(d.get("equipment", {}).get("wearable", "none")),
        ),
        options=Options(
            include_mobility=bool(d.get("options", {}).get("include_mobility", False)),
            include_nutrition=bool(d.get("options", {}).get("include_nutrition", True)),
            include_lead=bool(d.get("options", {}).get("include_lead", False)),
            output_path=d.get("options", {}).get("output_path"),
        ),
        language=Language(d.get("language", "en")),
    )


def _as_date(x) -> date:
    if isinstance(x, date):
        return x
    return date.fromisoformat(str(x))


# --------------------------------------------------------------------------- #
# Validation: returns (errors, warnings). Errors block generation; warnings don't.
# --------------------------------------------------------------------------- #
def validate(cfg: Config) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    t = translator(cfg.language)

    # weights
    if cfg.profile.bodyweight <= 0:
        errors.append(t("profile.bodyweight must be positive."))
    if cfg.profile.age is not None and not (10 <= cfg.profile.age <= 100):
        warnings.append(t("profile.age looks unusual; double-check."))

    # grades
    if cfg.climbing.target_grade < cfg.climbing.current_grade:
        errors.append(t("climbing.target_grade is below current_grade — pick a target at or above your current level."))
    jump = cfg.climbing.target_grade - cfg.climbing.current_grade
    if jump >= 4:
        warnings.append(t("Target is {jump} V-grades above current — that is very ambitious for one cycle; consider a nearer target.", jump=jump))

    # dates / cycle length
    if cfg.goal.goal_date <= cfg.goal.start_date:
        errors.append(t("goal.goal_date must be after start_date."))
    else:
        wks = cfg.total_weeks
        if wks < MIN_CYCLE_WEEKS:
            errors.append(t(
                "Only {wks} weeks to the goal — climbro needs at least {min} for a sane cycle "
                "(otherwise the taper would land after your goal date). Move the date or pick a nearer goal.",
                wks=wks, min=MIN_CYCLE_WEEKS))
        elif wks < 12:
            warnings.append(t("{wks} weeks is tight — phases will be heavily compressed.", wks=wks))
        elif wks > 40:
            warnings.append(t("{wks} weeks is a long horizon; consider splitting into multiple cycles.", wks=wks))

    # cut block
    if cfg.weight.enabled:
        if cfg.target_bw_kg is None:
            errors.append(t("weight.enabled is true but weight.target_bodyweight is missing."))
        elif cfg.target_bw_kg >= cfg.bw_kg:
            errors.append(t("weight.target_bodyweight must be below current bodyweight when cutting."))
        else:
            wks = max(1, cfg.total_weeks)
            total_loss = cfg.bw_kg - cfg.target_bw_kg
            weekly_pct = (total_loss / wks) / cfg.bw_kg * 100
            if weekly_pct > cfg.weight.max_rate_pct:
                warnings.append(t(
                    "Implied loss ~{pct}%/wk exceeds your cap {cap}%/wk — "
                    "the engine will cap the rate and the cut won't finish by the goal date.",
                    pct=f"{weekly_pct:.2f}", cap=f"{cfg.weight.max_rate_pct:.2f}"))
        if not 0.2 <= cfg.weight.max_rate_pct <= 1.0:
            warnings.append(t("weight.max_rate_pct outside 0.2–1.0%/wk; >1% risks muscle/strength loss."))

    # availability
    if not (2 <= cfg.availability.days_per_week <= 7):
        errors.append(t("availability.days_per_week must be between 2 and 7."))
    ad = cfg.availability.available_days
    if ad is not None:
        bad = [d for d in ad if d not in WEEKDAYS]
        if bad:
            errors.append(t("availability.available_days has invalid weekday(s): {bad} (use {valid}).", bad=bad, valid=WEEKDAYS))
        if len(ad) != cfg.availability.days_per_week:
            errors.append(t("availability.available_days length must equal days_per_week."))

    # equipment sanity
    if not cfg.equipment.has_fingerboard:
        warnings.append(t("No fingerboard: finger-strength work will be redirected to on-the-wall protocols."))
    if not cfg.equipment.has_gym:
        warnings.append(t("No gym access: strength work will use bodyweight/board alternatives."))

    return errors, warnings


# --------------------------------------------------------------------------- #
# Optional YAML I/O (PyYAML imported locally so the schema works without it)
# --------------------------------------------------------------------------- #
def load_yaml(path: str) -> Config:
    import yaml  # local import: only needed for YAML I/O
    with open(path, "r", encoding="utf-8") as fh:
        return from_dict(yaml.safe_load(fh))


def to_dict(cfg: Config) -> dict:
    """Round-trippable dict (enums -> values, dates -> ISO, grades stay in display scale)."""
    d = asdict(cfg)

    def fix(obj):
        if isinstance(obj, dict):
            return {k: fix(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [fix(v) for v in obj]
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, date):
            return obj.isoformat()
        return obj

    d = fix(d)
    # re-render grades into the chosen display scale for human-friendly YAML
    scale = cfg.climbing.grade_scale
    d["climbing"]["current_grade"] = format_grade(scale, cfg.climbing.current_grade)
    d["climbing"]["target_grade"] = format_grade(scale, cfg.climbing.target_grade)
    return d


def dump_yaml(cfg: Config, path: str) -> None:
    import yaml
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(to_dict(cfg), fh, sort_keys=False, allow_unicode=True)


# --------------------------------------------------------------------------- #
# Survey field metadata (drives the CLI wizard in the next step).
# Kept here so prompts and the schema never drift apart.
# --------------------------------------------------------------------------- #
SURVEY = [
    ("profile.name",            "Your name (optional, for the file)",                 "text",   {"optional": True, "example": "Alex"}),
    ("profile.sex",             "Sex (for strength norms)",                            "choice", {"choices": ["male", "female"]}),
    ("profile.age",             "Age (optional)",                                      "int",    {"optional": True, "example": "30"}),
    ("profile.units",           "Units",                                               "choice", {"choices": ["kg", "lb"]}),
    ("profile.bodyweight",      "Current bodyweight",                                  "float",  {"example": "72.5"}),
    ("climbing.grade_scale",    "Grade scale to display",                              "choice", {"choices": ["V", "Font"]}),
    ("climbing.current_grade",  "Current hardest grade (consistent, not one-off)",     "grade",  {"example": "V5 / 6C"}),
    ("climbing.target_grade",   "Target grade",                                        "grade",  {"example": "V8 / 7B"}),
    ("climbing.years_climbing", "Years climbing",                                      "float",  {"example": "3"}),
    ("climbing.max_hang_added", "Added load on a 20mm edge, 7s hang (optional)",       "float",  {"optional": True, "example": "15"}),
    ("climbing.max_pullup_added","Added load on a weighted pull-up (optional)",        "float",  {"optional": True, "example": "20"}),
    ("goal.goal",               "Primary goal",                                        "choice", {"choices": ["send_grade", "competition"]}),
    ("goal.start_date",         "Start date (blank = today)",                          "date",   {"optional": True, "example": "2026-06-08 (YYYY-MM-DD)"}),
    ("goal.goal_date",          "Goal / competition date",                             "date",   {"example": "2026-12-28 (YYYY-MM-DD)"}),
    ("weight.enabled",          "Do you want to lose weight as part of this?",         "bool",   {}),
    ("weight.target_bodyweight","Target bodyweight (if cutting)",                      "float",  {"optional": True, "depends_on": "weight.enabled", "example": "68"}),
    ("availability.days_per_week","Training days per week (2–7)",                      "int",    {"example": "4"}),
    ("availability.available_days","Which weekdays (optional)",                        "weekdays", {"optional": True, "example": "Mon Tue Thu Sat"}),
    ("equipment.has_fingerboard","Do you have a fingerboard/hangboard?",               "bool",   {}),
    ("equipment.has_system_board","Do you have a system board (MoonBoard/Kilter/Tension)?", "bool", {}),
    ("equipment.has_gym",       "Do you have gym/weights access?",                     "bool",   {}),
    ("equipment.wearable",      "Wearable for recovery metrics",                       "choice", {"choices": ["garmin", "other", "none"]}),
    ("options.include_mobility","Include a mobility block?",                           "bool",   {}),
    ("options.include_lead",    "Include lead / rope sessions in the plan?",           "bool",   {}),
    ("options.include_nutrition","Include the nutrition sheet?",                       "bool",   {}),
]


if __name__ == "__main__":
    # tiny self-check
    demo = {
        "profile": {"name": "Bo", "sex": "male", "age": 30, "units": "kg", "bodyweight": 83},
        "climbing": {"grade_scale": "V", "current_grade": "V5", "target_grade": "V8",
                     "years_climbing": 1, "max_hang_added": 15, "max_pullup_added": 20},
        "goal": {"goal": "competition", "start_date": "2026-06-08", "goal_date": "2026-12-28"},
        "weight": {"enabled": True, "target_bodyweight": 78, "max_rate_pct": 0.7},
        "availability": {"days_per_week": 6, "available_days": ["Mon", "Tue", "Wed", "Thu", "Sat", "Sun"]},
        "equipment": {"has_fingerboard": True, "has_system_board": True, "has_gym": True, "wearable": "garmin"},
        "options": {"include_mobility": True, "include_nutrition": True},
    }
    cfg = from_dict(demo)
    errs, warns = validate(cfg)
    print("weeks:", cfg.total_weeks, "| bw_kg:", cfg.bw_kg, "| target_bw_kg:", cfg.target_bw_kg)
    print("current V:", cfg.climbing.current_grade, "-> display:", format_grade(cfg.climbing.grade_scale, cfg.climbing.current_grade))
    print("metrics:", cfg.metrics)
    print("errors:", errs)
    print("warnings:", warns)
