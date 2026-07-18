"""
climbro.render.sheets_plan — sheets generated directly from the engine Plan:
  - Setup   (echoes the config so the workbook is self-describing + drives some cells)
  - Cycle   (the macrocycle: phases, auto-dated, planned weight, deload flags)

These are the dynamic, per-user sheets (no hardcoded plan).
"""

from __future__ import annotations
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font
from .style import h1, h2, th, td, note, inp, fill, widths, GREEN, ORANGE, GREY
from ..schema import Config, format_grade, from_kg
from ..engine import Plan


# --------------------------------------------------------------------------- #
# Setup — human-readable echo of the configuration
# --------------------------------------------------------------------------- #
def build_setup(ws, plan: Plan) -> None:
    cfg: Config = plan.cfg
    ws.sheet_view.showGridLines = False
    widths(ws, {"A": 32, "B": 18, "C": 3, "D": 60})
    ws.merge_cells("A1:D1"); h1(ws["A1"], "Setup — your inputs for this plan")
    ws.row_dimensions[1].height = 24

    gs = cfg.climbing.grade_scale
    rows = [
        ("Name", cfg.profile.name or "—", ""),
        ("Sex", cfg.profile.sex.value, "used for finger-strength norms"),
        ("Age", cfg.profile.age if cfg.profile.age is not None else "—", ""),
        ("Units", cfg.profile.units.value, ""),
        ("Start bodyweight", f"{cfg.profile.bodyweight} {cfg.profile.units.value}", ""),
        ("Current grade", format_grade(gs, cfg.climbing.current_grade), f"scale: {gs.value}"),
        ("Target grade", format_grade(gs, cfg.climbing.target_grade), ""),
        ("Years climbing", cfg.climbing.years_climbing, "influences technique vs strength emphasis"),
        ("Goal", cfg.goal.goal.value, ""),
        ("Start date", cfg.goal.start_date.isoformat(), ""),
        ("Goal date", cfg.goal.goal_date.isoformat(), f"{plan.macro.total_weeks} weeks"),
        ("Cut enabled", "yes" if cfg.weight.enabled else "no", ""),
        ("Target bodyweight", f"{cfg.weight.target_bodyweight} {cfg.profile.units.value}" if cfg.weight.enabled else "—", ""),
        ("Training days/week", cfg.availability.days_per_week, ""),
        ("Fingerboard", _yn(cfg.equipment.has_fingerboard), ""),
        ("System board", _yn(cfg.equipment.has_system_board), "MoonBoard / Kilter / Tension"),
        ("Gym access", _yn(cfg.equipment.has_gym), ""),
        ("Wearable", cfg.equipment.wearable.value, ""),
        ("Mobility block", _yn(cfg.options.include_mobility), ""),
        ("Lead sessions", _yn(cfg.options.include_lead), "1x/week: replaces volume (base) / PE slot (peak)"),
        ("Nutrition sheet", _yn(cfg.options.include_nutrition), ""),
    ]
    r = 3
    for label, value, desc in rows:
        td(ws.cell(r, 1), label, bold=True)
        td(ws.cell(r, 2), value, center=True)
        note(ws.cell(r, 4), desc)
        ws.row_dimensions[r].height = 22
        r += 1

    # finger-strength target headline
    r += 1
    h2(ws, r, 1, 4, "Finger-strength target"); ws.row_dimensions[r].height = 20
    r += 1
    tgt = format_grade(gs, cfg.climbing.target_grade)
    unit = cfg.profile.units.value
    added_disp = round((plan.norm_target_pct - 1.0) * cfg.profile.bodyweight, 1)
    msg = (f"To match the {tgt} norm: ~{plan.norm_target_pct*100:.0f}% bodyweight "
           f"(7 s, 20 mm, two hands) = about +{added_disp} {unit} added "
           f"at {cfg.profile.bodyweight} {unit}. Population guide, not a hard rule.")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
    note(ws.cell(r, 1), msg); ws.row_dimensions[r].height = 34


def _yn(b: bool) -> str:
    return "yes" if b else "no"


# --------------------------------------------------------------------------- #
# Cycle — the macrocycle table, auto-dated, with planned weight + deloads
# --------------------------------------------------------------------------- #
def build_cycle(ws, plan: Plan) -> None:
    cfg = plan.cfg
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:G1"); h1(ws["A1"], "Cycle — your macrocycle (dates & planned weight computed)")
    ws.row_dimensions[1].height = 24

    headers = ["Wk", "Dates", "Phase", "Deload", "Focus", "Plan wt", "Sessions"]
    widths(ws, {"A": 6, "B": 20, "C": 26, "D": 9, "E": 50, "F": 10, "G": 10})
    for i, htext in enumerate(headers, 1):
        th(ws.cell(3, i, htext))
    ws.row_dimensions[3].height = 30

    start = cfg.goal.start_date
    units = cfg.profile.units.value
    r = 4
    for w in plan.weeks:
        wk_start = start.toordinal() + (w.week - 1) * 7
        from datetime import date
        d0 = date.fromordinal(wk_start)
        d1 = date.fromordinal(wk_start + 6)
        td(ws.cell(r, 1), w.week, center=True)
        td(ws.cell(r, 2), f"{d0.strftime('%d.%m')}–{d1.strftime('%d.%m')}", center=True)
        td(ws.cell(r, 3), w.phase_name, bold=True)
        td(ws.cell(r, 4), "DELOAD" if w.deload else "", center=True)
        td(ws.cell(r, 5), w.focus)
        td(ws.cell(r, 6), f"{from_kg(w.planned_weight, cfg.profile.units)} {units}" if w.planned_weight is not None else "—", center=True)
        td(ws.cell(r, 7), w.planned_session_count, center=True)
        if w.deload:
            fill(ws.cell(r, 4), ORANGE)
        if w.in_deficit:
            fill(ws.cell(r, 6), GREEN)
        ws.row_dimensions[r].height = 26
        r += 1

    ws.merge_cells(start_row=r + 1, start_column=1, end_row=r + 1, end_column=7)
    note(ws.cell(r + 1, 1),
         "Planned weight follows your cut curve (green = deficit weeks). Day-by-day sessions "
         "are on the phase schedule sheets. What you actually do goes in Journal / Week.")
    ws.row_dimensions[r + 1].height = 30
