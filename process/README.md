# Process records

These files are the evidence base for Chapter 5 and Appendix D of the research report.
Record events **when they happen**, never afterwards from memory, and commit each
update so that git timestamps corroborate them.

| File | What to record | When |
|---|---|---|
| `backlog.md` | Status of every story and change | Whenever a status changes |
| `sprints.json` | Sprint start and end dates (`YYYY-MM-DD`), completed items | At sprint planning and sprint review |
| `changes.json` | Each requirement change (schema below) | When requested, and again when released |
| `ci_runs.json` | GitHub Actions run history | Export once at the end of Sprint 3 |
| `reviews/sprint-N.md` | Notes from each sprint review: who attended, feedback, decisions | At each review |

## `changes.json` entry

```json
{
  "id": "C1",
  "description": "Add a distributed-team factor",
  "sprint": 2,
  "requested_by": "role of the stakeholder, e.g. supervisor",
  "requested_at": "2026-10-14T09:30:00+02:00",
  "released_at": "2026-10-15T16:10:00+02:00",
  "release_tag": "v0.2.0",
  "effort_hours": 3.5,
  "caused_failure": false,
  "notes": "CI failed once on a missing weight; fixed before release"
}
```

* `requested_at`: when the change was introduced (the stakeholder message or review).
* `released_at`: when the tagged release containing the change was published.
* `effort_hours`: your own time log for implementing the change.
* `caused_failure`: `true` if the released change later needed a fix (used for the
  change failure rate).

## Exporting CI run history

Using the GitHub CLI on your own computer (replace OWNER/REPO):

```bash
gh api "repos/OWNER/REPO/actions/runs?per_page=100" > process/ci_runs.json
```

Or open `https://api.github.com/repos/OWNER/REPO/actions/runs?per_page=100` in a browser
(public repository) and save the page as `process/ci_runs.json`.

## Generating the report tables

```bash
python tools/collect_metrics.py --latex reports/poc_tables.tex --json reports/metrics.json
```
