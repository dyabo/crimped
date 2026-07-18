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
from .i18n import Language, translator
from .engine import build_plan
from .render import render


# --------------------------------------------------------------------------- #
# tiny prompt helpers (stdlib only)
# --------------------------------------------------------------------------- #
_BOOL_TRUE = {"y", "yes", "true", "1", "д", "да"}
_BOOL_FALSE = {"n", "no", "false", "0", "н", "нет"}


def _ask_language() -> Language:
    """First question, before we know the language — so it's bilingual."""
    while True:
        raw = input("Language / Язык [en/ru]: ").strip().lower()
        if raw == "":
            return Language.EN
        if raw in ("en", "ru"):
            return Language(raw)
        print("  invalid — try again / неверно, ещё раз")


def _ask(prompt: str, kind: str, opts: dict, ctx: dict, t):
    """Ask one localized question. Choices/weekdays accept the English canonical
    value OR its translation; the canonical value is always what gets stored."""
    optional = opts.get("optional", False)
    suffix = t(" [optional, Enter to skip]") if optional else ""
    example = opts.get("example")
    ex_hint = f" ({t('e.g. {ex}', ex=t(example))})" if example else ""
    p = t(prompt)
    while True:
        if kind == "choice":
            disp = [t(c) for c in opts["choices"]]
            raw = input(f"{p} {disp}{suffix}: ").strip()
        elif kind == "bool":
            raw = input(f"{p} {t('(y/n)')}{suffix}: ").strip().lower()
        elif kind == "weekdays":
            disp = [t(d) for d in WEEKDAYS]
            raw = input(f"{p} {disp}{ex_hint}{suffix}: ").strip()
        else:
            raw = input(f"{p}{ex_hint}{suffix}: ").strip()

        if raw == "" and optional:
            return None
        if raw == "" and not optional:
            print(t("  (required)"))
            continue

        try:
            if kind == "text":
                return raw
            if kind == "int":
                return int(raw)
            if kind == "float":
                return float(raw.replace(",", "."))
            if kind == "bool":
                if raw in _BOOL_TRUE:
                    return True
                if raw in _BOOL_FALSE:
                    return False
                raise ValueError
            if kind == "choice":
                low = raw.lower()
                for c in opts["choices"]:
                    if low in (c.lower(), t(c).lower()):
                        return c
                raise ValueError
            if kind == "weekdays":
                rev = {d.lower(): d for d in WEEKDAYS}
                rev.update({t(d).lower(): d for d in WEEKDAYS})
                out = []
                for x in raw.replace(",", " ").split():
                    key = x.lower()
                    if key not in rev:
                        raise ValueError
                    out.append(rev[key])
                return out
            if kind == "date":
                return date.fromisoformat(raw).isoformat()
            if kind == "grade":
                scale = GradeScale(ctx.get("climbing.grade_scale", "V"))
                parse_grade(scale, raw)  # validate parseable
                return raw
        except (ValueError, KeyError):
            print(t("  invalid — try again"))


def _set(d: dict, dotted: str, value) -> None:
    section, key = dotted.split(".")
    d.setdefault(section, {})[key] = value


def run_wizard() -> dict:
    lang = _ask_language()               # language first — it drives every prompt below
    t = translator(lang)
    print(t("\nclimbro — let's build your plan. Answer a few questions.\n"))
    flat: dict = {}   # dotted answers, for grade-scale context
    cfg: dict = {"language": lang.value}
    for dotted, prompt, kind, opts in SURVEY:
        # skip dependent question if its condition is False
        dep = opts.get("depends_on")
        if dep and not flat.get(dep):
            continue
        val = _ask(prompt, kind, opts, flat, t)
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

    t = translator(cfg.language)
    errors, warnings = validate(cfg)
    for w in warnings:
        print(f"  ! {w}")
    if errors:
        print(t("\nCan't generate — fix these:"))
        for e in errors:
            print(f"  ✗ {e}")
        return 1

    out = args.out if args.out else (cfg.options.output_path or "climbro_plan.xlsx")
    if cfg.options.output_path and args.out == "climbro_plan.xlsx":
        out = cfg.options.output_path

    plan = build_plan(cfg)
    path = render(plan, out)
    print(t("\n✓ Wrote {path}", path=path))
    print(t("  {weeks} weeks · goal V{v} · finger norm {pct}%BW (+{kg}{unit})",
            weeks=plan.macro.total_weeks, v=plan.target_v,
            pct=f"{plan.norm_target_pct*100:.0f}",
            kg=f"{plan.norm_target_added_kg:.1f}", unit=t("kg")))
    print(t("  Start on the Dashboard; log sessions in Journal and a weekly check-in in Week."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
