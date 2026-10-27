# Sprint 3 review

- **Date:** 2026-10-27
- **Attendees (roles only, no personal details without consent):** researcher (developer and product owner) only. No other stakeholder attended.
- **Release reviewed:** `v0.3.0` (tagged after this review).
- **How the review was held:** the researcher does not have Git or Python installed on her
  own computer, so the demos were run by the AI assistant (Claude) on the latest `main`
  (commit `23b67c0`) and the output was shown to the researcher, who made the acceptance
  decisions below. Her decisions and her process observation are recorded in her own words.

## Sprint goal and outcome

Goal: Calibrate rules against Chapter 4 findings; documentation; change C3. The supervisor's
feedback on the draft report (26 Oct) added C4, C5 and US-10.

Met / partly met / not met, and why: **Met.** "I accept all five deliverables (US-08, US-09,
C3, C4, C5) — they meet the criteria and complete the required scope." US-10 (release
workflow) is accepted when the `v0.3.0` release publishes.

## Items demonstrated

| ID | Accepted? | Feedback |
|---|---|---|
| US-08 | Accepted (2026-10-27) | `validate-rules`: "Rules OK: version 1.1.0, 6 factors, 5 methodologies, 5 caveats". |
| US-09 | Accepted (2026-10-27) | README covers installation, commands, the meaning of scores, evaluation and releases. |
| C3 | Accepted (2026-10-27) | PoC's own context: "Close call: Scrum, Agile with DevOps (CI/CD) are within 2 point(s) of each other." |
| C4 | Accepted (2026-10-27) | `check-scenarios`: "Agreement: 5 of 5 scenarios." |
| C5 | Accepted (2026-10-27) | `sensitivity`: no ±1 change alters a top recommendation; at ±2 only scenario B changes (10 of 50 changes, all ties between plan-driven and hybrid). |
| US-10 | Pending | Accepted once the `v0.3.0` release is published by the release workflow. |

## Requirement changes requested

None requested at this review. C4 and C5 were requested earlier, in the supervisor's
written feedback on the draft report.

| ID | Change | Requested by (role) | Logged in `changes.json`? |
|---|---|---|---|
| C4 | Independent scenario evaluation | supervisor (draft feedback) | yes |
| C5 | Weight justification and sensitivity analysis | supervisor (draft feedback) | yes |

## Process observations

- Researcher: "What worked really well this sprint was keeping the scope tightly focused and
  moving systematically through the user stories and criteria without letting unnecessary
  overhead slow down the proof of concept."
- From the record: on 20 Oct the CI pipeline stayed red for about 74 minutes (lint failures
  on a planning document) while further commits were pushed.
- From the record: only one release (`v0.2.0`) was made before this review.
- From the record: stakeholder collaboration was not evaluated; no stakeholder other than the
  researcher took part in any review.

## Decisions for the next sprint

No further sprints are planned; the proof of concept closes with `v0.3.0`.
