# climbro

A command-line generator for a **climbing training tracker** (Excel workbook) that
adapts to your level, goal, schedule and gear — then tracks your progress with
real sports-science analytics.

> **Open source under the MIT license.** See **[DISCLAIMER.md](DISCLAIMER.md)** — it is not
> medical or coaching advice.

## What it does

You answer a short survey (or hand a YAML config). climbro:

1. Picks and scales a **periodization template** to your dates (cut early, peak late;
   the taper and peak are protected when time is tight).
2. Lays out **sessions across your available weekdays** with recovery rules baked in
   (fingers ≤2×/week and ≥48 h apart, never an all-hard week, ≥1 easy/rest day).
3. Sets **finger-strength targets** from your grade and sex (population norms).
4. Builds an `.xlsx` you live in: a dashboard advisor, a per-session journal, a
   weekly check-in, and analytics — **sRPE load, ACWR overload risk, relative finger
   strength vs the target-grade norm, weight-vs-plan**, plus optional mobility and
   nutrition sheets and an injury log.

Goals supported in v1: **`send_grade`** and **`competition`**.
Grades display in **V or Font** (normalized to V internally). Units **kg or lb** — the workbook displays and accepts your unit everywhere; the engine computes in kg internally.
A **cut** (weight loss) block is optional; so are the mobility block and a weekly **lead/rope session** (replaces a volume slot in base phases, serves as power-endurance near the peak). If you don't
use a Garmin-style wearable, recovery-metric columns stay out of your way.

## Install & run

```bash
# Python 3.10+ required
pip install .          # installs the `climbro` command
# or: pip install -r requirements.txt

# interactive survey:
climbro                # or: python -m climbro

# or build from a config (see config.example.yaml):
climbro --config config.example.yaml --out my_plan.xlsx
```

Open the result, start on the **Dashboard**, log each session in **Journal**, and do
one **Week** check-in (weight + a few recovery numbers) weekly. Everything else is
computed.

## How it's built

```
climbro/                     # repo root: pyproject, README, LICENSE, config.example.yaml
  climbro/                   # the package
    schema.py              # config contract + survey field spec + validation
    norms.py               # finger-strength norms (V → %BW, by sex)
    periodization.py       # phase templates + scaling to the real horizon
    engine.py              # day-by-day session allocation + weight curve + norms
    cli.py                 # survey wizard / --config runner
    render/                # xlsx generation
      style.py
      sheets_plan.py       # Setup, Cycle
      sheets_schedule.py   # per-phase day-by-day schedules
      sheets_tracking.py   # Journal, Week, Injuries
      sheets_dashboard.py  # Dashboard advisor + Charts
      sheets_static.py     # Mobility, Nutrition, Recovery, Glossary
```

The numbers are **templates, not AI** — predictable and inspectable. Norm values are
orientation guides (finger strength explains only ~half of grade), used as a target
band, not a verdict.

## Contributing

Contributions are welcome — by submitting a change you agree it is provided under the
project's MIT license (inbound = outbound). No CLA required.

## License

[MIT](LICENSE). Do whatever you like; keep the copyright notice.
