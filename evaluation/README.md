# Evaluation of the selection rules (changes C4, C5 and C6)

Requested in the supervisor's feedback on the draft report (received 26 October 2026):
evaluate the tool against independently defined scenarios, justify the weights, and test
whether reasonable changes to the weights produce different recommendations.

Rules version evaluated: **1.2.0** (`config/rules.json`), re-encoded on 29 October 2026
(change C6) to follow the selection framework as revised after the full literature synthesis
(report Table 4.5). The evaluation of rules 1.1.0, released in v0.3.0, is kept unchanged in
Appendix A below.

## 1. Procedure

1. The five scenarios (A-E) follow the supervisor's scenario matrix. Their factor values are
   in `scenarios.json` and have not changed since they were first committed.
2. Before the tool was run on them, the expected outcome of each scenario was written from the
   report's selection framework and committed separately:
   * rules 1.1.0: `expectations-v1.1.json`, commit `947288f`, ahead of the evaluation commands;
   * rules 1.2.0: `expectations.json`, commit `dc13ef8`, written from the revised framework
     before `config/rules.json` was changed.
3. `check-scenarios` compares each recommendation with its expectation, including any caveat
   the framework says must be shown.
4. `sensitivity` changes each weight that a scenario uses, one at a time, by +/-1 and then
   +/-2 (changes that would leave the -3...+3 range are skipped), and records whether the top
   recommendation changes.

**What this does and does not show.** The expectations are researcher-defined, written with
the same AI assistance as the rules, and come from the same framework the weights encode.
Committing them first fixes the order; it does not make them independent. Agreement shows
that the encoded weights reproduce the framework consistently across contexts other than the
proof of concept's own; it does **not** show that the framework's recommendations are correct
or that following them improves project outcomes. That would need evaluation by independent,
qualified reviewers or field data.

## 2. What changed in rules 1.2.0 (C6)

* **Magnitude rule.** The largest weight a factor may carry now depends on the confidence in
  its evidence: up to 3 for moderate or high confidence, at most 1 for low confidence or a
  design assumption.
* **Regulation** (low confidence) is capped at +/-1, and its weights no longer separate
  plan-driven methods from adapted agile or hybrid processes under strict regulation, because
  the empirical sources found in the search report adapted agile processes meeting regulatory
  demands (Ribeiro et al., 2025; Smith et al., 2019).
* **Coordination at scale** and **training for low maturity** (both high confidence) are now
  caveats shown whichever methodology is recommended, not only for agile methods.
* All other weights are unchanged. See `source-to-rule-matrix.md`.

Before re-encoding, rules 1.1.0 were run against the new expectations. They agreed in 3 of 5
scenarios; B and C failed because the coordination guidance was not shown for a plan-driven or
hybrid recommendation:

| Scenario | Top recommendation | Margin over 2nd | Expected | Agrees | Notes |
|---|---|---|---|---|---|
| A: small project, frequently changing requirements | scrum (12) | 5 (vs agile_devops) | scrum, kanban | yes | -- |
| B: large project, stable requirements, formal compliance | plan_driven (10) | 2 (vs hybrid) | plan_driven, hybrid | NO | no caveat mentions 'coordination' |
| C: multiple distributed teams with integration dependencies | hybrid (11) | 6 (vs agile_devops) | hybrid | NO | no caveat mentions 'coordination' |
| D: small team with limited methodology experience | scrum (8) | 4 (vs kanban) | scrum, kanban, hybrid, plan_driven | yes | -- |
| E: frequent releases and operational stability | agile_devops (10) | 3 (vs scrum) | agile_devops | yes | -- |

Agreement: 3 of 5 scenarios.

## 3. Results: agreement with the pre-registered expectations (rules 1.2.0)

Reproduce with:
`python -m advisor check-scenarios --input evaluation/scenarios.json --expected evaluation/expectations.json`

| Scenario | Top recommendation | Margin over 2nd | Expected | Agrees | Notes |
|---|---|---|---|---|---|
| A: small project, frequently changing requirements | scrum (11) | 4 (vs kanban) | scrum, kanban | yes | -- |
| B: large project, stable requirements, formal compliance | plan_driven (8) | 1 (vs hybrid) | plan_driven, hybrid | yes | -- |
| C: multiple distributed teams with integration dependencies | hybrid (10) | 5 (vs agile_devops) | hybrid | yes | -- |
| D: small team with limited methodology experience | scrum (7) | 3 (vs kanban) | scrum, kanban, hybrid, plan_driven | yes | -- |
| E: frequent releases and operational stability | agile_devops (10) | 3 (vs scrum) | agile_devops | yes | -- |

Agreement: 5 of 5 scenarios.

## 4. Results: weight sensitivity (rules 1.2.0)

Reproduce with: `python -m advisor sensitivity --input evaluation/scenarios.json --step 1` (and `--step 2`)

Each relevant weight changed by +/-1, one at a time.

| Scenario | Top | Single-weight changes | Changes that alter the top | Share |
|---|---|---|---|---|
| A: small project, frequently changing requirements | scrum | 56 | 0 | 0% |
| B: large project, stable requirements, formal compliance | plan_driven | 57 | 11 | 19% |
| C: multiple distributed teams with integration dependencies | hybrid | 59 | 0 | 0% |
| D: small team with limited methodology experience | scrum | 58 | 0 | 0% |
| E: frequent releases and operational stability | agile_devops | 57 | 0 | 0% |

Changes that alter the top recommendation:

- B: large project, stable requirements, formal compliance: plan_driven.requirement_volatility=low -1 -> hybrid
- B: large project, stable requirements, formal compliance: plan_driven.team_size=large -1 -> hybrid
- B: large project, stable requirements, formal compliance: plan_driven.regulation=strict -1 -> hybrid
- B: large project, stable requirements, formal compliance: plan_driven.release_frequency=low -1 -> hybrid
- B: large project, stable requirements, formal compliance: plan_driven.team_maturity=medium -1 -> hybrid
- B: large project, stable requirements, formal compliance: plan_driven.distributed_team=no -1 -> hybrid
- B: large project, stable requirements, formal compliance: hybrid.requirement_volatility=low +1 -> hybrid
- B: large project, stable requirements, formal compliance: hybrid.regulation=strict +1 -> hybrid
- B: large project, stable requirements, formal compliance: hybrid.release_frequency=low +1 -> hybrid
- B: large project, stable requirements, formal compliance: hybrid.team_maturity=medium +1 -> hybrid
- B: large project, stable requirements, formal compliance: hybrid.distributed_team=no +1 -> hybrid

Each relevant weight changed by +/-2, one at a time.

| Scenario | Top | Single-weight changes | Changes that alter the top | Share |
|---|---|---|---|---|
| A: small project, frequently changing requirements | scrum | 51 | 0 | 0% |
| B: large project, stable requirements, formal compliance | plan_driven | 54 | 11 | 20% |
| C: multiple distributed teams with integration dependencies | hybrid | 53 | 0 | 0% |
| D: small team with limited methodology experience | scrum | 51 | 0 | 0% |
| E: frequent releases and operational stability | agile_devops | 50 | 0 | 0% |

Changes that alter the top recommendation:

- B: large project, stable requirements, formal compliance: plan_driven.requirement_volatility=low -2 -> hybrid
- B: large project, stable requirements, formal compliance: plan_driven.team_size=large -2 -> hybrid
- B: large project, stable requirements, formal compliance: plan_driven.regulation=strict -2 -> hybrid
- B: large project, stable requirements, formal compliance: plan_driven.release_frequency=low -2 -> hybrid
- B: large project, stable requirements, formal compliance: plan_driven.team_maturity=medium -2 -> hybrid
- B: large project, stable requirements, formal compliance: plan_driven.distributed_team=no -2 -> hybrid
- B: large project, stable requirements, formal compliance: hybrid.requirement_volatility=low +2 -> hybrid
- B: large project, stable requirements, formal compliance: hybrid.regulation=strict +2 -> hybrid
- B: large project, stable requirements, formal compliance: hybrid.release_frequency=low +2 -> hybrid
- B: large project, stable requirements, formal compliance: hybrid.team_maturity=medium +2 -> hybrid
- B: large project, stable requirements, formal compliance: hybrid.distributed_team=no +2 -> hybrid

**Interpretation.** Scenarios A, C, D and E keep their top recommendation under every single
one- or two-point change. Scenario B (large, stable, strictly regulated) is now closer than in
rules 1.1.0: plan-driven leads the defined hybrid by one point (8 to 7), so the tool flags it as
a close call and names both. With the regulation weights reduced, 11 of 57 one-point changes
make the two scores equal, and the engine breaks the tie alphabetically in favour of `hybrid`;
11 of 54 two-point changes make the hybrid strictly higher. Every change moves the
recommendation only between plan-driven and the hybrid, both of which the revised framework
accepts for this scenario, and the coordination and regulation caveats are shown either way.
This instability is intended: the evidence on regulated settings is the weakest in the review
(low confidence), and the rules should not present either option as clearly better.

## Appendix A. Evaluation of rules 1.1.0 (release v0.3.0)

Kept as recorded on 26-27 October 2026; the expectations file has been renamed
`expectations-v1.1.json`. Rules 1.1.0 are in the v0.3.0 release and in git history.

### A.1 Agreement with the v1.1 expectations

Reproduce with:
`python -m advisor --rules <rules 1.1.0> check-scenarios --input evaluation/scenarios.json --expected evaluation/expectations-v1.1.json`

| Scenario | Top recommendation | Margin over 2nd | Expected | Agrees | Notes |
|---|---|---|---|---|---|
| A: small project, frequently changing requirements | scrum (12) | 5 (vs agile_devops) | scrum, kanban | yes | -- |
| B: large project, stable requirements, formal compliance | plan_driven (10) | 2 (vs hybrid) | plan_driven, hybrid | yes | -- |
| C: multiple distributed teams with integration dependencies | hybrid (11) | 6 (vs agile_devops) | hybrid | yes | -- |
| D: small team with limited methodology experience | scrum (8) | 4 (vs kanban) | scrum, kanban, hybrid, plan_driven | yes | -- |
| E: frequent releases and operational stability | agile_devops (10) | 3 (vs scrum) | agile_devops | yes | -- |

Agreement: 5 of 5 scenarios.

### A.2 Weight sensitivity

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
