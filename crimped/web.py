"""
crimped.web — a thin, framework-free adapter for a browser front-end.

The static web page (see /web) runs this module inside Pyodide:
  - `survey_for(lang)` returns the questionnaire, fully localized, as plain data
    so JavaScript can render the form (single source of truth = schema.SURVEY).
  - `generate(answers, lang)` validates the answers and returns the .xlsx as
    base64 (plus any warnings/errors). No disk I/O, nothing leaves the browser.

Kept dependency-free (stdlib only) so it loads cleanly under Pyodide/WASM.
"""

from __future__ import annotations
import base64

from .schema import SURVEY, WEEKDAYS, from_dict, validate
from .i18n import translator
from .engine import build_plan
from .render import render_bytes


def survey_for(lang: str = "en") -> list[dict]:
    """The questionnaire as JSON-able data, localized for `lang`.

    Each field: {key, kind, optional, depends_on, prompt, example, choices}.
    `choices` is a list of {value, label} (value = the canonical stored value).
    """
    t = translator(lang)
    out: list[dict] = []
    for key, prompt, kind, opts in SURVEY:
        field = {
            "key": key,
            "kind": kind,
            "optional": bool(opts.get("optional", False)),
            "depends_on": opts.get("depends_on"),
            "prompt": t(prompt),
            "example": t(opts["example"]) if opts.get("example") else None,
            "choices": None,
        }
        if kind == "choice":
            field["choices"] = [{"value": c, "label": t(c)} for c in opts["choices"]]
        elif kind == "weekdays":
            field["choices"] = [{"value": d, "label": t(d)} for d in WEEKDAYS]
        out.append(field)
    return out


def _nest(answers: dict) -> dict:
    """Turn flat dotted answers ({'profile.sex': 'male', ...}) into a nested dict."""
    cfg: dict = {}
    for dotted, value in answers.items():
        if value is None or value == "":
            continue
        if "." in dotted:
            section, k = dotted.split(".", 1)
            cfg.setdefault(section, {})[k] = value
        else:
            cfg[dotted] = value
    return cfg


def generate(answers: dict, lang: str = "en") -> dict:
    """Validate `answers` and build the workbook.

    Returns {ok, errors, warnings, filename, xlsx_b64}. On invalid input,
    ok=False and `errors` explains why (already localized).
    """
    t = translator(lang)
    cfg_dict = _nest(dict(answers))
    cfg_dict["language"] = lang

    try:
        cfg = from_dict(cfg_dict)
    except (KeyError, ValueError) as e:
        return {"ok": False, "errors": [str(e)], "warnings": [], "filename": None, "xlsx_b64": None}

    errors, warnings = validate(cfg)
    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings, "filename": None, "xlsx_b64": None}

    plan = build_plan(cfg)
    data = render_bytes(plan)
    name = (cfg.profile.name or "crimped").strip().replace(" ", "_") or "crimped"
    return {
        "ok": True,
        "errors": [],
        "warnings": warnings,
        "filename": f"{name}_plan.xlsx",
        "xlsx_b64": base64.b64encode(data).decode("ascii"),
    }
