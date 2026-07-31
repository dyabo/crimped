# crimped — browser app

A zero-install front door for non-technical users. It's a single static page that
runs the **actual** crimped Python engine **in the browser** via
[Pyodide](https://pyodide.org) (Python compiled to WebAssembly). The user answers
the survey, clicks a button, and the `.xlsx` is generated and downloaded locally —
**nothing is uploaded**, so bodyweight/health answers never leave the device.

## How it works

- `index.html` — the whole app (form UI + glue). It:
  1. loads Pyodide from a CDN,
  2. installs the vendored `openpyxl` wheels (see `vendor/`),
  3. fetches the pure-Python `crimped` package straight from this repo into
     Pyodide's virtual filesystem,
  4. calls `crimped.web.survey_for(lang)` to render the localized form and
     `crimped.web.generate(answers, lang)` to build the workbook.
- The survey, validation, translations and the engine are the **same code** the
  CLI uses — the page adds no training logic of its own (single source of truth).

## Run locally

From the repo root:

```bash
python3 -m http.server 8777
# then open http://localhost:8777/web/index.html
```

It must be served over HTTP (not opened as a `file://`) so the browser can fetch
the package modules and wheels.

## Deploy (GitHub Pages)

Enable Pages for the repo, serving from the repository root (branch `main`, folder
`/`). The app then lives at `https://<user>.github.io/<repo>/web/`. No backend, no
build step, free hosting. Everything it needs (`../crimped/*.py` and `vendor/*.whl`)
is served as static files from the same origin.

## Vendored wheels

`openpyxl` isn't part of the Pyodide distribution, and fetching it from PyPI at
runtime is fragile (and blocked in some environments). So the two pure-Python
wheels it needs are committed under `vendor/` and installed from our own origin.

To refresh them (e.g. on an openpyxl bump), re-download and update the two
filenames referenced in `index.html`:

```bash
pip download openpyxl -d web/vendor --no-cache-dir
```
