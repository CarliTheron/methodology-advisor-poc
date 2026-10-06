# Product backlog

Product: **Methodology Advisor**, a command-line tool that applies the context-based
methodology selection framework from the research report (Section 4.6) to a project's
characteristics and explains its recommendation.

Process: hybrid Agile-DevOps. Three one-week sprints inside a fixed plan (phase gate:
supervisor-approved scope), with continuous integration on every push and a tagged
release at the end of each sprint.

Status values: `todo`, `in progress`, `done`. Update this file during the sprints and
commit the change, so the board history is preserved in git.

## Sprint 1: baseline (rules-driven core)

| ID | User story | Acceptance criteria | Status |
|---|---|---|---|
| US-01 | As a project lead, I want to describe my project with five context factors so that the tool can assess it. | Context model with requirement volatility, team size, regulation, release frequency and team maturity; invalid input is rejected with a clear message. | in progress |
| US-02 | As a researcher, I want the selection rules stored as data so that they can change without code changes. | Rules in `config/rules.json`; loader rejects incomplete or out-of-range rules and lists every error. | in progress |
| US-03 | As a project lead, I want a ranked recommendation so that I can compare methodologies. | All methodologies ranked by score; ties resolved deterministically. | in progress |
| US-04 | As a project lead, I want to see why a methodology was recommended so that I can challenge it. | Output shows each factor's contribution and any applicable caveats. | in progress |
| US-05 | As a developer, I want a CLI so that the tool can be used and tested from the terminal. | `recommend` (text and JSON output) and `validate-rules` commands with exit codes. | in progress |
| US-06 | As a team, we want automated quality gates so that broken changes cannot be merged unnoticed. | CI runs lint, rules validation and tests with a 90% coverage threshold on every push. | in progress |

## Sprint 2: planned stories and requirement changes

| ID | User story / change | Acceptance criteria | Status |
|---|---|---|---|
| US-07 | As a researcher, I want to evaluate a batch of project scenarios from a file so that I can compare the framework's output across cases. | `evaluate --input scenarios.json` prints one recommendation per scenario. | done |
| C1 | **Requirement change (introduced mid-sprint):** add a sixth factor, *distributed team* (yes/no). | Factor added to rules, model and CLI; rules validation forces weights for every methodology; tests updated. | done |
| C2 | **Requirement change (introduced mid-sprint):** export the recommendation as a Markdown report. | `--format markdown` and `--output FILE`; report includes ranking, contributions and caveats. | done |

## Sprint 3: calibration and hardening

| ID | User story / change | Acceptance criteria | Status |
|---|---|---|---|
| US-08 | As a researcher, I want the rule weights calibrated against the Chapter 4 findings so that the tool reflects the evidence. | Rules version 1.1.0; every changed weight has a source in `rules.json`. | todo |
| US-09 | As a user, I want documentation so that I can run the tool without help. | README covers installation, commands and the meaning of scores. | todo |
| C3 | **Requirement change (introduced mid-sprint):** flag a "close call" when the top two scores are within a configurable margin. | Margin set in `rules.json`; output names both options when it applies; tests cover the boundary. | todo |

## Definition of done

- Code reviewed against the acceptance criteria.
- All CI gates pass on `main`.
- Backlog status and `process/changes.json` updated in the same commit or pull request.
