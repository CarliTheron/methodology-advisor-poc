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
    --release-frequency high --maturity medium --distributed-team no
```

```
Recommended: Scrum (score 11)

Ranking:
  1. Scrum                                     11
  2. Agile with DevOps (CI/CD)                  9
  3. Kanban                                     8
  4. Defined hybrid (phase gates + iterations)  -1
  5. Plan-driven (Waterfall / V-Model)         -8

Close call: Scrum, Agile with DevOps (CI/CD) are within 2 point(s) of each other.

Factor contributions for Scrum:
  requirement_volatility   +3
  team_size                +3
  regulation               +2
  release_frequency        +1
  team_maturity            +1
  distributed_team         +1

Rules version: 1.1.0
```

Other commands:

```bash
advisor recommend ... --format json     # machine-readable output
advisor validate-rules                  # check config/rules.json (CI gate)
advisor --rules other.json recommend .. # use another rules file
advisor evaluate --input scenarios.json          # batch evaluation, one result per scenario
advisor recommend ... --format markdown --output report.md   # write a Markdown report
```

Without installing, use `PYTHONPATH=src python -m advisor ...` instead of `advisor`.

## How recommendations are made

Each methodology in `config/rules.json` has a weight from -3 (strongly unsuited) to +3
(strongly suited) for every level of six context factors:

| Factor | Levels |
|---|---|
| Requirement volatility | low, medium, high |
| Team size | small (1-9), medium (10-50), large (51+) |
| Regulation | none, moderate, strict |
| Release frequency | low, medium, high |
| Team agile maturity | low, medium, high |
| Distributed team | no, yes |

A methodology's score is the sum of its weights for the project's factor values, so scores
are an ordinal ranking, not a probability or a percentage -- a score of 11 means "ranked
ahead of a score of 9 by 2 points," not "11% more suitable." The output shows every
factor's contribution and any caveats, so the reasoning can be inspected and challenged
rather than taken on trust.

Each methodology's `rationale` and `sources` in `config/rules.json` cite the specific
Chapter 4 finding that supports its weights (e.g. Table 4.5, Finding 3.2 for Agile with
DevOps). Reviewing Sprint 1's initial weights against those findings in Sprint 3 (story
US-08) found them already directionally consistent for four of the five original factors,
so the weight values themselves did not change -- only their sourcing did. The `regulation`
factor is flagged in `rules.json`'s `note` field as resting on conceptual evidence only
(no direct empirical test was found). The `distributed_team` factor (added in Sprint 2,
story C1) falls outside the five factors the literature review covers and is not
evidence-sourced.

### Close calls

When the top two (or more) methodologies score within `close_call_margin` points of each
other -- a configurable value in `config/rules.json`, currently 2 -- the output names all of
them as a close call instead of presenting a single winner as clear-cut:

```
Close call: Scrum, Agile with DevOps (CI/CD) are within 2 point(s) of each other.
```

The JSON format exposes the same information as `close_call: {"is_close_call": ...,
"margin": ..., "candidates": [...]}`.

## Evaluating the rules

Two commands test the rules themselves (changes C4 and C5):

```bash
# Compare recommendations for scenarios A-E with expectations recorded before the tool was run
python -m advisor check-scenarios --input evaluation/scenarios.json --expected evaluation/expectations.json

# Change each relevant weight by +/-1 (or --step 2) and report changes to the top recommendation
python -m advisor sensitivity --input evaluation/scenarios.json --step 2
```

Results, and what they do and do not show, are in `evaluation/README.md`. The evidence
behind every weight is in `evaluation/source-to-rule-matrix.md`.

## Releases

Pushing a version tag that matches `advisor.__version__` (for example `v0.3.0`) runs
`.github/workflows/release.yml`: it re-runs the quality gates, builds a wheel with the rules
bundled, checks that the wheel runs outside the repository, and publishes a GitHub release
with the evaluation results attached. Each release counts as one deployment in
`tools/collect_metrics.py`.

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
