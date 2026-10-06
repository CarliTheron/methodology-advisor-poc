# Methodology Advisor (DST481 proof of concept)

A small command-line tool that recommends a software development methodology from a
project's context. It implements the context-based selection framework developed in the
research report *A Comparative Analysis of Software Development Methodologies in
Contemporary Software Projects* (Carli Theron, DST481, Belgium Campus iTversity).

The project serves two purposes:

1. **Product:** it turns the framework into a transparent, testable tool.
2. **Process:** it is developed with a hybrid Agile-DevOps process (fixed phase plan,
   one-week sprints, CI quality gates, tagged releases), and its process records are the
   evidence for Chapter 5 of the report.

## Quick start

Requires Python 3.10 or later.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .
```

Recommend a methodology:

```bash
advisor recommend --volatility high --team-size 6 --regulation none \
    --release-frequency high --maturity medium
```

```
Recommended: Scrum (score 10)

Ranking:
  1. Scrum                                     10
  2. Agile with DevOps (CI/CD)                  9
  ...
Factor contributions for Scrum:
  requirement_volatility   +3
  ...
```

Other commands:

```bash
advisor recommend ... --format json     # machine-readable output
advisor validate-rules                  # check config/rules.json (CI gate)
advisor --rules other.json recommend .. # use another rules file
```

Without installing, use `PYTHONPATH=src python -m advisor ...` instead of `advisor`.

## How recommendations are made

Each methodology in `config/rules.json` has a weight from -3 (strongly unsuited) to +3
(strongly suited) for every level of five context factors:

| Factor | Levels |
|---|---|
| Requirement volatility | low, medium, high |
| Team size | small (1-9), medium (10-50), large (51+) |
| Regulation | none, moderate, strict |
| Release frequency | low, medium, high |
| Team agile maturity | low, medium, high |

A methodology's score is the sum of its weights for the project's factor values. The
output shows every factor's contribution and any caveats, so the reasoning can be
checked. The weights are an initial encoding of the framework and are recalibrated
against the report's findings in Sprint 3 (story US-08).

## Quality gates (GitHub Actions)

Every push to `main` and every pull request runs `.github/workflows/ci.yml`:

1. **Lint and formatting:** `ruff check .` and `ruff format --check .`
2. **Rules validation:** `python -m advisor validate-rules`
3. **Tests and coverage:** `pytest --cov --cov-fail-under=90`
4. **Smoke test:** one end-to-end recommendation

Run the same checks locally before pushing:

```bash
ruff check . && ruff format --check . && PYTHONPATH=src python -m advisor validate-rules \
  && pytest --cov --cov-fail-under=90
```

## Project structure

```
config/rules.json            selection rules (data, versioned)
src/advisor/                 application code
  models.py                  project context and validation
  rules.py                   rules loading and validation
  engine.py                  scoring and ranking
  cli.py                     command-line interface
tests/                       unit and CLI tests
tools/collect_metrics.py     extracts process metrics from git and process records
process/                     backlog, sprint and change records (research evidence)
.github/workflows/ci.yml     CI pipeline
```

## Process records and metrics

See [`process/README.md`](process/README.md) for what to record and when. At the end of
the project:

```bash
python tools/collect_metrics.py --latex reports/poc_tables.tex --json reports/metrics.json
```

The script reads only real records (git history, tags, `process/*.json`, the exported CI
run history). Missing data are shown as `--`, never estimated.

## Acknowledgement

The Sprint 1 code was drafted with the assistance of an AI tool (Claude, Anthropic) and
reviewed, run and maintained by the author. This is disclosed in the research report.
