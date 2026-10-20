# Sprint 2 review

- **Date:** 2026-10-20
- **Attendees (roles only, no personal details without consent):** supervisor
- **Release reviewed:** `v0.2.0` (tagged by the author following this review, 2026-10-20).

## Sprint goal and outcome

Goal: Batch evaluation; absorb requirement changes C1 and C2.

Met / partly met / not met, and why: **Met, on the objective/technical record** — all three
planned items (US-07, C1, C2) were implemented, tested (87 tests, 100% branch coverage),
independently spec-compliance- and code-quality-reviewed per task, and confirmed green on
GitHub Actions CI (commit `20b4601`, run
[37797746824](https://github.com/CarliTheron/methodology-advisor-poc/actions/runs/37797746824)
and later). Human acceptance of the actual behavior (below) is separate and still pending.

## Items demonstrated

| ID | Accepted? | Feedback |
|---|---|---|
| US-07 (batch `evaluate`) | Accepted (2026-10-20) | Demonstrated against 3 scenarios (2 valid, 1 deliberately malformed to show error handling). See demo output below. |
| C1 (`distributed_team` factor) | Accepted (2026-10-20) | Demonstrated: toggling `--distributed-team yes/no` changes the ranking and score as expected. See demo output below. |
| C2 (Markdown export) | Accepted (2026-10-20) | Demonstrated: `--format markdown` produces a well-formed report with ranking and contribution tables. See demo output below. |

### Demo output (real, captured 2026-10-20)

**C1 — `recommend --distributed-team yes` (small volatile team):**
```
Recommended: Agile with DevOps (CI/CD) (score 10)

Ranking:
  1. Agile with DevOps (CI/CD)                 10
  2. Kanban                                     9
  3. Scrum                                      9
  4. Defined hybrid (phase gates + iterations)   0
  5. Plan-driven (Waterfall / V-Model)         -7

Factor contributions for Agile with DevOps (CI/CD):
  requirement_volatility   +3
  team_size                +1
  regulation               +2
  release_frequency        +3
  team_maturity            +0
  distributed_team         +1

Rules version: 1.0.0
```

**C2 — `recommend --format markdown` (large regulated team):**
```
# Methodology recommendation: Plan-driven (Waterfall / V-Model)

**Score:** 11
**Rules version:** 1.0.0

## Ranking

| Rank | Methodology | Score |
|---|---|---|
| 1 | Plan-driven (Waterfall / V-Model) | 11 |
| 2 | Defined hybrid (phase gates + iterations) | 8 |
| 3 | Kanban | -5 |
| 4 | Agile with DevOps (CI/CD) | -7 |
| 5 | Scrum | -7 |

## Factor contributions for Plan-driven (Waterfall / V-Model)

| Factor | Contribution |
|---|---|
| requirement_volatility | +3 |
| team_size | +2 |
| regulation | +3 |
| release_frequency | +2 |
| team_maturity | +1 |
| distributed_team | +0 |
```

**US-07 — `evaluate --input scenarios.json`** (3 scenarios: small volatile startup, large
regulated enterprise, and one deliberately missing required fields):
```
=== Small volatile startup ===
  Recommended: Agile with DevOps (CI/CD)
    1. Agile with DevOps (CI/CD)                 10
    2. Kanban                                     9
    3. Scrum                                      9
    4. Defined hybrid (phase gates + iterations)   0
    5. Plan-driven (Waterfall / V-Model)         -7

=== Large regulated enterprise ===
  Recommended: Plan-driven (Waterfall / V-Model)
    1. Plan-driven (Waterfall / V-Model)         11
    2. Defined hybrid (phase gates + iterations)   8
    3. Kanban                                    -5
    4. Agile with DevOps (CI/CD)                 -7
    5. Scrum                                      -7

=== Missing a field (error case) ===
  Error: missing context fields: requirement_volatility, regulation, release_frequency, team_maturity, distributed_team
```

## Requirement changes requested

None requested at this review.

| ID | Change | Requested by (role) | Logged in `changes.json`? |
|---|---|---|---|
| | | | |

## Process observations

Not yet assessed.

## Decisions for the next sprint

All three Sprint 2 items accepted; `v0.2.0` tagged. Proceed to Sprint 3 (US-08 calibration,
US-09 documentation, C3 close-call flag) as planned.
