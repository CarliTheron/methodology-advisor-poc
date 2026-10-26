# Source-to-rule matrix (rules v1.1.0)

Links every factor's weights in `config/rules.json` to the evidence in the report (Chapter 4) and states how much confidence that evidence supports. Weights run from -3 (strongly unsuited) to +3 (strongly suited).

**How the weights were set.** The *direction* of each weight (favoured, neutral, penalised) follows the cited findings. The *magnitude* (1, 2 or 3) is a design judgement: none of the sources reports effect sizes that can be converted into points. Where the sources are silent, the weight is identified below as a design assumption. The sensitivity analysis in `evaluation/README.md` tests whether recommendations depend on these exact magnitudes.

## requirement_volatility

**Evidence:** Boehm (2002); Serrador & Pinto (2015); Kuhrmann et al. (2017). Findings 1.1, 1.2, 2.1  
**Confidence:** Moderate  
**Note:** Direction: iterative methods favoured as volatility rises, plan-driven penalised. No source isolates volatility as a moderator, so magnitudes are judgement (as the supervisor noted for P1).

| Level | Plan | Scrum | Kanban | DevOps | Hybrid |
|---|---|---|---|---|---|
| low | +3 | -1 | 0 | -1 | +1 |
| medium | 0 | +2 | +1 | +1 | +2 |
| high | -3 | +3 | +2 | +3 | +1 |

## team_size

**Evidence:** Dikert et al. (2016); Edison et al. (2022); Kuhrmann et al. (2017). Findings 1.1, 4.1, 4.3  
**Confidence:** Moderate  
**Note:** Direction: single-team frameworks penalised at scale, defined hybrid/scaled favoured. Evidence is mostly experience reports.

| Level | Plan | Scrum | Kanban | DevOps | Hybrid |
|---|---|---|---|---|---|
| small | -1 | +3 | +2 | +1 | -2 |
| medium | +1 | +1 | +1 | +2 | +2 |
| large | +2 | -2 | -1 | +1 | +3 |

## regulation

**Evidence:** Boehm (2002). Finding 2.2  
**Confidence:** Low  
**Note:** Direction: plan-driven and hybrid favoured under strict regulation. Conceptual argument only; no empirical source in the current core set.

| Level | Plan | Scrum | Kanban | DevOps | Hybrid |
|---|---|---|---|---|---|
| none | -1 | +2 | +1 | +2 | -1 |
| moderate | +1 | 0 | 0 | +1 | +2 |
| strict | +3 | -2 | -2 | -1 | +2 |

## release_frequency

**Evidence:** Forsgren et al. (2018). Finding 3.2  
**Confidence:** Moderate  
**Note:** Direction: Agile with DevOps favoured for frequent releases. Survey-based, self-reported delivery measures.

| Level | Plan | Scrum | Kanban | DevOps | Hybrid |
|---|---|---|---|---|---|
| low | +2 | -1 | -1 | -3 | +1 |
| medium | 0 | +2 | +1 | +1 | +2 |
| high | -3 | +1 | +2 | +3 | 0 |

## team_maturity

**Evidence:** Dikert et al. (2016); Forsgren et al. (2018). Findings 2.2, 3.2, 4.1  
**Confidence:** Moderate  
**Note:** Direction: methods that demand practice maturity (DevOps, Scrum) penalised for low maturity. The +1 for plan-driven and hybrid at low maturity is a design assumption with no direct source.

| Level | Plan | Scrum | Kanban | DevOps | Hybrid |
|---|---|---|---|---|---|
| low | +1 | -2 | -1 | -3 | +1 |
| medium | 0 | +1 | +1 | 0 | +1 |
| high | -1 | +2 | +2 | +3 | 0 |

## distributed_team

**Evidence:** None in the Chapter 4 core set  
**Confidence:** Unsourced  
**Note:** Added as requirement change C1 in Sprint 2. Weights (Scrum -1/+1, others 0/+1) are design assumptions and should be treated as such.

| Level | Plan | Scrum | Kanban | DevOps | Hybrid |
|---|---|---|---|---|---|
| no | 0 | +1 | 0 | 0 | 0 |
| yes | +1 | -1 | +1 | +1 | +1 |

## Conflicting or missing evidence

- **Regulation:** the only support for plan-driven methods in regulated settings is conceptual (Boehm, 2002). The rules keep the weight but attach a caveat to agile recommendations under strict regulation, and the sensitivity analysis shows this is where recommendations are least stable (scenario B).
- **Distributed teams:** not covered by the reviewed evidence; its weights are small (−1 to +1). No ±1 change to them altered any scenario's top recommendation; at ±2, two of them produced the plan-driven/hybrid tie in scenario B.
- **Culture:** organisational culture is the most consistently supported factor in Chapter 4 but is not a scored factor, because it conditions *whether* any methodology succeeds rather than *which* one to choose. It enters the tool through the low-maturity caveat instead.
