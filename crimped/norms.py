"""
crimped — finger-strength norms (v1)

Maps bouldering grade (internal V-int) -> expected finger strength, expressed as
MAX 7-second two-hand hang on a 20 mm edge as a percentage of bodyweight (%BW),
including added load. This is the de-facto standard test (Lattice / Eva Lopez).

  %BW = (bodyweight + added_load) / bodyweight        e.g. 150% = +0.5 x BW added

NOTES / HONESTY:
- These are POPULATION ORIENTATION VALUES with large individual spread
  (finger strength explains only ~half of grade variance; technique, RFD,
  and skill carry the rest). Treat as a target band, not a law.
- Numbers are anchored to commonly cited Lattice figures: ~145-150% for the
  V6-V7 range (men) with roughly ~6 percentage points per V-grade through the
  mid-range, and a female column set lower at the same grade (women tend to
  pull a smaller %BW added at equivalent grade).
- The engine reads `target_pct(sex, v)` to compute the finger-strength target,
  and `pct_to_added_kg` / `added_kg_to_pct` to translate to/from board load.

This module has no training logic beyond the lookup + arithmetic.
"""

from __future__ import annotations
from .schema import Sex, V_MIN, V_MAX


# %BW (max 7 s, 20 mm, two hands) by grade, as a decimal (1.52 == 152% total).
# Anchored to the figures used in our plan and the tracker file: V7 ~146%, V8 ~152%
# (~6 percentage points per grade). Female column set ~6 pts lower at equal grade.
# Low end sized so a real V5-V6 climber lands plausibly (e.g. +15kg @ 83kg ~ 118%
# reads as "fingers lagging climbing level", a common ex-lifter pattern).
_NORMS: dict[int, dict[str, float]] = {
    #  V :   male,  female
    0:  {"male": 1.04, "female": 0.98},
    1:  {"male": 1.10, "female": 1.04},
    2:  {"male": 1.16, "female": 1.10},
    3:  {"male": 1.22, "female": 1.16},
    4:  {"male": 1.28, "female": 1.22},
    5:  {"male": 1.34, "female": 1.28},
    6:  {"male": 1.40, "female": 1.34},
    7:  {"male": 1.46, "female": 1.40},   # ~V7 — primary anchor (146%)
    8:  {"male": 1.52, "female": 1.46},   # ~V8 — primary anchor (152%)
    9:  {"male": 1.58, "female": 1.52},
    10: {"male": 1.64, "female": 1.58},
    11: {"male": 1.70, "female": 1.64},
    12: {"male": 1.76, "female": 1.70},
    13: {"male": 1.82, "female": 1.76},
    14: {"male": 1.88, "female": 1.82},
    15: {"male": 1.94, "female": 1.88},
    16: {"male": 2.00, "female": 1.94},
    17: {"male": 2.06, "female": 2.00},
}

# Standard test definition (kept here so the file + engine never drift).
EDGE_MM = 20
HANG_SECONDS = 7
HANDS = 2


def target_pct(sex: Sex, v: int) -> float:
    """Target finger strength (%BW as a decimal, e.g. 1.52) for a grade and sex."""
    v = max(V_MIN, min(V_MAX, int(v)))
    key = "female" if sex == Sex.FEMALE else "male"
    return _NORMS[v][key]


def pct_to_added_kg(pct: float, bodyweight_kg: float) -> float:
    """Convert a target %BW into the added load (kg) on the edge for this bodyweight."""
    return round((pct - 1.0) * bodyweight_kg, 1)


def added_kg_to_pct(added_kg: float, bodyweight_kg: float) -> float:
    """Convert a measured added load (kg) at this bodyweight into %BW (decimal)."""
    if bodyweight_kg <= 0:
        raise ValueError("bodyweight_kg must be positive")
    return round((bodyweight_kg + added_kg) / bodyweight_kg, 4)


def gap_to_target(sex: Sex, target_v: int, current_pct: float) -> float:
    """
    Percentage-points still missing to reach the target grade's norm.
    <= 0 means the finger-strength norm for the target grade is already met.
    Returned as a decimal (0.10 == 10 percentage points).
    """
    return round(target_pct(sex, target_v) - current_pct, 4)


def estimate_current_v(sex: Sex, current_pct: float) -> int:
    """
    Rough inverse: which V-grade does this finger strength correspond to (by norm)?
    Used only for context/sanity (e.g. 'your fingers are ~V7 strong'); never as a
    substitute for actual climbing level.
    """
    key = "female" if sex == Sex.FEMALE else "male"
    best = V_MIN
    for v in range(V_MIN, V_MAX + 1):
        if current_pct >= _NORMS[v][key]:
            best = v
    return best


if __name__ == "__main__":
    # self-check against the file we built (Bo: male, 83 kg, +15 on 20 mm)
    bw = 83.0
    cur_pct = added_kg_to_pct(15, bw)
    print(f"test: {EDGE_MM}mm / {HANG_SECONDS}s / {HANDS} hands")
    print(f"Bo current: +15kg @ {bw} -> {cur_pct*100:.1f}%BW; fingers ~V{estimate_current_v(Sex.MALE, cur_pct)} strong")
    print(f"V8 norm (male):   {target_pct(Sex.MALE, 8)*100:.0f}%BW  = +{pct_to_added_kg(target_pct(Sex.MALE,8), bw)}kg @ {bw}")
    print(f"V8 norm (female): {target_pct(Sex.FEMALE, 8)*100:.0f}%BW")
    print(f"gap to V8: {gap_to_target(Sex.MALE, 8, cur_pct)*100:.1f} pts "
          f"(~+{pct_to_added_kg(target_pct(Sex.MALE,8), bw) - 15:.1f}kg more)")
