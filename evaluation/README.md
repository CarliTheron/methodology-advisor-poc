# Evaluation of the selection rules (changes C4 and C5)

Requested in the supervisor's feedback on the draft report (received 26 October 2026):
evaluate the tool against independently defined scenarios, justify the weights, and test
whether reasonable changes to the weights produce different recommendations.

Rules version evaluated: 1.1.0 (`config/rules.json`).

## 1. Procedure

1. The five scenarios (A–E) follow the supervisor's scenario matrix. Their factor values are
   in `scenarios.json`.
2. Before the tool was run on them, the expected outcome of each scenario was written in
   `expectations.json` from the report's selection framework (Table 4.5). This was committed
   separately (commit `947288f`) ahead of the commands that run the evaluation, so the
   expectations could not be fitted to the tool's output.
3. `check-scenarios` compares each recommendation with its expectation.
4. `sensitivity` changes each weight that a scenario uses, one at a time, by ±1 and then ±2
   (changes that would leave the −3…+3 range are skipped), and records whether the top
   recommendation changes.

**What this does and does not show.** The expectations are researcher-defined and come from
the same framework the weights encode. Agreement therefore shows that the encoded weights
reproduce the evidence-based framework consistently across contexts other than the proof of
concept's own; it does **not** show that the framework's recommendations are correct or that
following them improves project outcomes. That would need evaluation by independent,
qualified reviewers or field data.

## 2. Results: agreement with pre-registered expectations

Reproduce with:
`python -m advisor check-scenarios --input evaluation/scenarios.json --expected evaluation/expectations.json`

| Scenario | Top recommendation | Margin over 2nd | Expected | Agrees | Notes |
|---|---|---|---|---|---|
| A: small project, frequently changing requirements | scrum (12) | 5 (vs agile_devops) | scrum, kanban | yes | -- |
| B: large project, stable requirements, formal compliance | plan_driven (10) | 2 (vs hybrid) | plan_driven, hybrid | yes | -- |
| C: multiple distributed teams with integration dependencies | hybrid (11) | 6 (vs agile_devops) | hybrid | yes | -- |
| D: small team with limited methodology experience | scrum (8) | 4 (vs kanban) | scrum, kanban, hybrid, plan_driven | yes | -- |
| E: frequent releases and operational stability | agile_devops (10) | 3 (vs scrum) | agile_devops | yes | -- |

Agreement: 5 of 5 scenarios.

## 3. Results: weight sensitivity

Reproduce with: `python -m advisor sensitivity --input evaluation/scenarios.json --step 1` (and `--step 2`)

Each relevant weight changed by +/-1, one at a time.

| Scenario | Top | Single-weight changes | Changes that alter the top | Share |
|---|---|---|---|---|
| A: small project, frequently changing requirements | scrum | 56 | 0 | 0% |
| B: large project, stable requirements, formal compliance | plan_driven | 56 | 0 | 0% |
| C: multiple distributed teams with integration dependencies | hybrid | 59 | 0 | 0% |
| D: small team with limited methodology experience | scrum | 58 | 0 | 0% |
| E: frequent releases and operational stability | agile_devops | 57 | 0 | 0% |

Each relevant weight changed by +/-2, one at a time.

| Scenario | Top | Single-weight changes | Changes that alter the top | Share |
|---|---|---|---|---|
| A: small project, frequently changing requirements | scrum | 49 | 0 | 0% |
| B: large project, stable requirements, formal compliance | plan_driven | 50 | 10 | 20% |
| C: multiple distributed teams with integration dependencies | hybrid | 52 | 0 | 0% |
| D: small team with limited methodology experience | scrum | 49 | 0 | 0% |
| E: frequent releases and operational stability | agile_devops | 49 | 0 | 0% |

Changes that alter the top recommendation:

- B: large project, stable requirements, formal compliance: plan_driven.requirement_volatility=low -2 -> hybrid
- B: large project, stable requirements, formal compliance: plan_driven.team_size=large -2 -> hybrid
- B: large project, stable requirements, formal compliance: plan_driven.regulation=strict -2 -> hybrid
- B: large project, stable requirements, formal compliance: plan_driven.release_frequency=low -2 -> hybrid
- B: large project, stable requirements, formal compliance: plan_driven.team_maturity=medium -2 -> hybrid
- B: large project, stable requirements, formal compliance: plan_driven.distributed_team=no -2 -> hybrid
- B: large project, stable requirements, formal compliance: hybrid.requirement_volatility=low +2 -> hybrid
- B: large project, stable requirements, formal compliance: hybrid.release_frequency=low +2 -> hybrid
- B: large project, stable requirements, formal compliance: hybrid.team_maturity=medium +2 -> hybrid
- B: large project, stable requirements, formal compliance: hybrid.distributed_team=no +2 -> hybrid

**Interpretation.** No single one-point change alters any recommendation. Under two-point
changes, scenarios A, C, D and E are unchanged; scenario B (large, stable, strictly regulated)
switches from plan-driven to the defined hybrid in 10 of 50 changes. Both outcomes are
acceptable under Table 4.5, and the tool already flags B as a close call (margin 2, equal to
`close_call_margin`). The choice between plan-driven and hybrid for regulated work is
therefore the least stable part of the rules, which matches the report's finding that the
evidence for plan-driven methods in regulated settings is the weakest (low confidence,
conceptual only). In all ten of these changes the two-point shift makes the plan-driven and hybrid scores
exactly equal (10 vs 8 becomes 8 vs 8 or 10 vs 10), and the engine breaks the tie
alphabetically in favour of `hybrid`. No single two-point change makes the hybrid score
strictly higher, so the result reflects a tie rather than a reversal; the close-call flag,
which names both options, is the more meaningful output for this scenario.
