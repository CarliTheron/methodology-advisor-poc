# Source-to-rule matrix (rules v1.2.0)

Links every factor's weights in `config/rules.json` to the evidence in the report (Chapter 4) and states how much confidence that evidence supports. Weights run from -3 (strongly unsuited) to +3 (strongly suited).

**How the weights were set.** The *direction* of each weight (favoured, neutral, penalised) follows the cited findings. The *magnitude* (1, 2 or 3) is a design judgement: none of the sources reports effect sizes that can be converted into points. Where the sources are silent, the weight is identified below as a design assumption. Since rules 1.2.0 (change C6), the largest magnitude a factor may carry depends on the confidence in its evidence: up to 3 for moderate or high confidence, at most 1 for low confidence or a design assumption. The sensitivity analysis in `evaluation/README.md` tests whether recommendations depend on these exact magnitudes.


Confidence ratings follow the report's revised selection framework (Table 4.5, after the full synthesis of 35 sources). Rules 1.1.0 (release v0.3.0) were encoded from the twelve core sources; where a rating changed, the earlier one is given in brackets.

## requirement_volatility

**Evidence:** Boehm (2002); Serrador & Pinto (2015); Kuhrmann et al. (2017); Binboga & Altin Gumussoy (2024); Akbar et al. (2018). Findings 1.2, 1.4, 2.1  
**Confidence:** Moderate  
**Note:** Direction: iterative methods favoured as volatility rises, plan-driven penalised. No source isolates volatility as a moderator, so magnitudes are judgement (as the supervisor noted for P1).

| Level | Plan | Scrum | Kanban | DevOps | Hybrid |
|---|---|---|---|---|---|
| low | +3 | -1 | 0 | -1 | +1 |
| medium | 0 | +2 | +1 | +1 | +2 |
| high | -3 | +3 | +2 | +3 | +1 |

## team_size

**Evidence:** Dikert et al. (2016); Edison et al. (2022); Kula et al. (2022); Berntzen et al. (2023); Bick et al. (2018). Findings 2.2, 3.3, 4.4  
**Confidence:** High (was Moderate), for the need to design coordination at scale  
**Note:** Direction: single-team frameworks penalised at scale, defined hybrid favoured. The high-confidence finding concerns coordination, not the choice of framework, so since 1.2.0 a coordination caveat is shown for every methodology when the team is large. Weights unchanged.

| Level | Plan | Scrum | Kanban | DevOps | Hybrid |
|---|---|---|---|---|---|
| small | -1 | +3 | +2 | +1 | -2 |
| medium | +1 | +1 | +1 | +2 | +2 |
| large | +2 | -2 | -1 | +1 | +3 |

## regulation

**Evidence:** Boehm (2002, conceptual); Ribeiro et al. (2025); Smith et al. (2019). Finding 2.3  
**Confidence:** Low  
**Note:** Re-encoded in 1.2.0. The empirical sources report adapted agile processes meeting regulatory demands (DO-178C; NASA independent verification), which contradicts favouring plan-driven methods. All weights are capped at +/-1; under strict regulation plan-driven and hybrid (+1), Scrum and DevOps (0) are close, and Kanban (-1) has no supporting source. Caveats require explicit documentation and assurance whichever method is chosen. Weights in 1.1.0 were: none -1/+2/+1/+2/-1, moderate +1/0/0/+1/+2, strict +3/-2/-2/-1/+2.

| Level | Plan | Scrum | Kanban | DevOps | Hybrid |
|---|---|---|---|---|---|
| none | -1 | +1 | +1 | +1 | -1 |
| moderate | +1 | 0 | 0 | +1 | +1 |
| strict | +1 | 0 | -1 | 0 | +1 |

## release_frequency

**Evidence:** Forsgren et al. (2018); Offerman et al. (2022); López-Fernández et al. (2022). Finding 3.2  
**Confidence:** Moderate (was Low)  
**Note:** Direction: Agile with DevOps favoured for frequent releases. Several research groups, but mainly self-reported delivery measures. Weights unchanged.

| Level | Plan | Scrum | Kanban | DevOps | Hybrid |
|---|---|---|---|---|---|
| low | +2 | -1 | -1 | -3 | +1 |
| medium | 0 | +2 | +1 | +1 | +2 |
| high | -3 | +1 | +2 | +3 | 0 |

## team_maturity

**Evidence:** Dikert et al. (2016); Forsgren et al. (2018); McKenzie et al. (2021); Uludağ et al. (2019); Kula et al. (2022). Findings 2.2, 4.2, 4.3  
**Confidence:** High (was Moderate), that maturity and culture matter; not how much  
**Note:** Direction: methods that demand practice maturity (DevOps, Scrum) penalised for low maturity. Since 1.2.0 the training and change-management caveat is shown for every methodology when maturity is low. Weights unchanged. The +1 for plan-driven and hybrid at low maturity is a design assumption with no direct source.

| Level | Plan | Scrum | Kanban | DevOps | Hybrid |
|---|---|---|---|---|---|
| low | +1 | -2 | -1 | -3 | +1 |
| medium | 0 | +1 | +1 | 0 | +1 |
| high | -1 | +2 | +2 | +3 | 0 |

## distributed_team

**Evidence:** None that compares methodologies; Alzoubi & Gill (2020) and Aizaz et al. (2021) concern distributed agile only  
**Confidence:** Unsourced  
**Note:** Added as requirement change C1 in Sprint 2. Weights (Scrum -1/+1, others 0/+1) are design assumptions and should be treated as such.

| Level | Plan | Scrum | Kanban | DevOps | Hybrid |
|---|---|---|---|---|---|
| no | 0 | +1 | 0 | 0 | 0 |
| yes | +1 | -1 | +1 | +1 | +1 |

## Conflicting or missing evidence

- **Regulation:** the conceptual case for plan-driven methods (Boehm, 2002) is contradicted by two weak empirical sources reporting adapted agile processes in regulated settings. Since 1.2.0 the weights are small and near-neutral, and scenario B is a deliberate close call between plan-driven and hybrid.
- **Distributed teams:** not covered by the reviewed evidence; its weights are small (−1 to +1). No ±1 change to them altered any scenario's top recommendation; at ±2, two of them produced the plan-driven/hybrid tie in scenario B.
- **Culture:** organisational culture is the most consistently supported factor in Chapter 4 but is not a scored factor, because it conditions *whether* any methodology succeeds rather than *which* one to choose. It enters the tool through the low-maturity caveat instead, which since 1.2.0 applies to every methodology.
