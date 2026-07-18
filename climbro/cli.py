"""
climbro.cli — interactive survey wizard.

Walks the SURVEY spec from schema.py, builds a config dict, validates it,
generates the plan and writes the .xlsx. Also supports running straight from a
YAML config (skip the questions).

Usage:
    python -m climbro                      # interactive wizard
    python -m climbro --config my.yaml     # build from an existing config
    python -m climbro --out plan.xlsx      # choose output path
"""

from __future__ import annotations
import argparse
import sys
from datetime import date

from .schema import (SURVEY, from_dict, validate, parse_grade, GradeScale, WEEKDAYS)
from .engine import build_plan
from .render import render


# --------------------------------------------------------------------------- #
# tiny prompt helpers (stdlib only)
# --------------------------------------------------------------------------- #
def _ask(prompt: str, kind: str, opts: dict, ctx: dict):
    optional = opts.get("optional", False)
    suffix = " [optional, Enter to skip]" if optional else ""
    while True:
        if kind == "choice":
            choices = opts["choices"]
            raw = input(f"{prompt} {choices}{suffix}: ").strip()
        elif kind == "bool":
            raw = input(f"{prompt} (y/n){suffix}: ").strip().lower()
        elif kind == "weekdays":
            raw = input(f"{prompt} {WEEKDAYS}{suffix}: ").strip()
        else:
            raw = input(f"{prompt}{suffix}: ").strip()

        if raw == "" and optional:
            return None
        if raw == "" and not optional:
            print("  (required)")
            continue

        try:
            if kind == "text":
                return raw
            if kind == "int":
                return int(raw)
            if kind == "float":
                return float(raw.replace(",", "."))
            if kind == "bool":
                if raw in ("y", "yes", "true", "1"):
                    return True
                if raw in ("n", "no", "false", "0"):
                    return False
                raise ValueError
            if kind == "choice":
                if raw in opts["choices"]:
                    return raw
                raise ValueError
            if kind == "weekdays":
                days = raw.replace(",", " ").split()
                days = [d.capitalize() for d in days]
                if any(d not in WEEKDAYS for d in days):
                    raise ValueError
                return days
            if kind == "date":
                return date.fromisoformat(raw).isoformat()
            if kind == "grade":
                scale = GradeScale(ctx.get("climbing.grade_scale", "V"))
                parse_grade(scale, raw)  # validate parseable
                return raw
        except (ValueError, KeyError):
            print("  invalid — try again")


def _set(d: dict, dotted: str, value) -> None:
    section, key = dotted.split(".")
    d.setdefault(section, {})[key] = value


def run_wizard() -> dict:
    print("\nclimbro — let's build your plan. Answer a few questions.\n")
    flat: dict = {}   # dotted answers, for grade-scale context
    cfg: dict = {}
    for dotted, prompt, kind, opts in SURVEY:
        # skip dependent question if its condition is False
        dep = opts.get("depends_on")
        if dep and not flat.get(dep):
            continue
        val = _ask(prompt, kind, opts, flat)
        if val is None:
            continue
        flat[dotted] = val
        _set(cfg, dotted, val)
    return cfg


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="climbro", description="Generate a climbing training tracker.")
    ap.add_argument("--config", help="path to a YAML config (skips the wizard)")
    ap.add_argument("--out", default="climbro_plan.xlsx", help="output .xlsx path")
    args = ap.parse_args(argv)

    if args.config:
        try:
            import yaml
        except ImportError:
            print("PyYAML is required for --config (pip install pyyaml).", file=sys.stderr)
            return 2
        with open(args.config, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
        cfg = from_dict(raw)
    else:
        cfg = from_dict(run_wizard())

    errors, warnings = validate(cfg)
    for w in warnings:
        print(f"  ! {w}")
    if errors:
        print("\nCan't generate — fix these:")
        for e in errors:
            print(f"  ✗ {e}")
        return 1

    out = args.out if args.out else (cfg.options.output_path or "climbro_plan.xlsx")
    if cfg.options.output_path and args.out == "climbro_plan.xlsx":
        out = cfg.options.output_path

    plan = build_plan(cfg)
    path = render(plan, out)
    print(f"\n✓ Wrote {path}")
    print(f"  {plan.macro.total_weeks} weeks · goal V{plan.target_v} · "
          f"finger norm {plan.norm_target_pct*100:.0f}%BW (+{plan.norm_target_added_kg:.1f}kg)")
    print("  Start on the Dashboard; log sessions in Journal and a weekly check-in in Week.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
