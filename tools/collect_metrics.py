"""Collect proof-of-concept process metrics from real project records.

Data sources (all produced by actually running the project):

* git history            -> commits and lines changed per sprint
* git tags (v*)          -> releases (deployments) per sprint
* process/sprints.json   -> sprint dates, planned and completed stories
* process/changes.json   -> requirement change log (lead time, effort, failures)
* process/ci_runs.json   -> GitHub Actions run history, exported from the GitHub API

Nothing is simulated: if a source is missing or empty, the corresponding
metric is reported as unavailable ("--").

Usage::

    python tools/collect_metrics.py                      # Markdown summary
    python tools/collect_metrics.py --latex reports/poc_tables.tex --json reports/metrics.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MISSING = "--"


# --------------------------------------------------------------------------- parsing helpers


def parse_dt(value: str | None, end_of_day: bool = False) -> datetime | None:
    """Parse an ISO date or datetime; naive values are treated as UTC."""
    if not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    if len(text) == 10:
        day = date.fromisoformat(text)
        moment = datetime.combine(day, time.max if end_of_day else time.min)
    else:
        moment = datetime.fromisoformat(text)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else default


def median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def fmt(value: float | int | None, digits: int = 1, suffix: str = "") -> str:
    if value is None:
        return MISSING
    if isinstance(value, int):
        return f"{value}{suffix}"
    return f"{value:.{digits}f}{suffix}"


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


# --------------------------------------------------------------------------- data sources


@dataclass
class Commit:
    sha: str
    when: datetime
    added: int = 0
    deleted: int = 0


def run_git(args: list[str], repo: Path) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True, check=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""
    return result.stdout


def git_commits(repo: Path) -> list[Commit]:
    output = run_git(["log", "--pretty=format:@@%H|%aI", "--numstat"], repo)
    commits: list[Commit] = []
    for line in output.splitlines():
        if line.startswith("@@"):
            sha, when = line[2:].split("|", 1)
            commits.append(Commit(sha=sha, when=parse_dt(when)))
        elif line.strip() and commits:
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                commits[-1].added += int(parts[0])
                commits[-1].deleted += int(parts[1])
    return commits


def git_tags(repo: Path, prefix: str = "v") -> list[tuple[str, datetime]]:
    output = run_git(
        [
            "for-each-ref",
            f"refs/tags/{prefix}*",
            "--format=%(refname:short)|%(creatordate:iso-strict)",
        ],
        repo,
    )
    tags = []
    for line in output.splitlines():
        if "|" in line:
            name, when = line.split("|", 1)
            tags.append((name, parse_dt(when)))
    return sorted(tags, key=lambda item: item[1])


# --------------------------------------------------------------------------- metrics


@dataclass
class Sprint:
    id: int
    goal: str
    start: datetime | None
    end: datetime | None
    planned: list[str] = field(default_factory=list)
    completed: list[str] = field(default_factory=list)

    def contains(self, moment: datetime | None) -> bool:
        return bool(moment and self.start and self.end and self.start <= moment <= self.end)


def load_sprints(data: dict) -> list[Sprint]:
    return [
        Sprint(
            id=item["id"],
            goal=item.get("goal", ""),
            start=parse_dt(item.get("start")),
            end=parse_dt(item.get("end"), end_of_day=True),
            planned=list(item.get("planned", [])),
            completed=list(item.get("completed", [])),
        )
        for item in data.get("sprints", [])
    ]


def lead_time_hours(change: dict) -> float | None:
    """Hours from the change being requested to the release that delivered it."""
    requested = parse_dt(change.get("requested_at"))
    released = parse_dt(change.get("released_at"))
    if not requested or not released or released < requested:
        return None
    return (released - requested).total_seconds() / 3600


def ci_runs_on_branch(data: dict, branch: str = "main") -> list[dict]:
    runs = data.get("workflow_runs", []) if isinstance(data, dict) else []
    return [
        run
        for run in runs
        if run.get("head_branch") == branch and run.get("status", "completed") == "completed"
    ]


def run_duration_minutes(run: dict) -> float | None:
    started = parse_dt(run.get("run_started_at") or run.get("created_at"))
    finished = parse_dt(run.get("updated_at"))
    if not started or not finished or finished < started:
        return None
    return (finished - started).total_seconds() / 60


def ci_summary(runs: list[dict]) -> dict[str, Any]:
    concluded = [run for run in runs if run.get("conclusion") in {"success", "failure"}]
    passed = sum(1 for run in concluded if run["conclusion"] == "success")
    durations = [d for d in (run_duration_minutes(run) for run in runs) if d is not None]
    return {
        "runs": len(concluded),
        "passed": passed,
        "pass_rate": passed / len(concluded) if concluded else None,
        "median_duration_min": median(durations),
    }


def change_failure_rate(changes: list[dict]) -> float | None:
    """Share of released changes that caused a failure needing remediation (DORA)."""
    released = [change for change in changes if change.get("released_at")]
    if not released:
        return None
    return sum(1 for change in released if change.get("caused_failure")) / len(released)


def compute(root: Path) -> dict[str, Any]:
    sprints = load_sprints(load_json(root / "process" / "sprints.json", {}))
    changes = load_json(root / "process" / "changes.json", {}).get("changes", [])
    ci_data = load_json(root / "process" / "ci_runs.json", {})
    commits = git_commits(root)
    tags = git_tags(root)
    runs = ci_runs_on_branch(ci_data)

    per_sprint = []
    for sprint in sprints:
        sprint_commits = [c for c in commits if sprint.contains(c.when)]
        sprint_tags = [name for name, when in tags if sprint.contains(when)]
        sprint_changes = [c for c in changes if c.get("sprint") == sprint.id]
        sprint_runs = [r for r in runs if sprint.contains(parse_dt(r.get("created_at")))]
        lead_times = [t for t in (lead_time_hours(c) for c in sprint_changes) if t is not None]
        per_sprint.append(
            {
                "sprint": sprint.id,
                "goal": sprint.goal,
                "planned": len(sprint.planned),
                "completed": len(sprint.completed),
                "commits": len(sprint_commits),
                "lines_added": sum(c.added for c in sprint_commits),
                "lines_deleted": sum(c.deleted for c in sprint_commits),
                "releases": sprint_tags,
                "median_lead_time_h": median(lead_times),
                "ci": ci_summary(sprint_runs),
            }
        )

    all_lead_times = [t for t in (lead_time_hours(c) for c in changes) if t is not None]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "totals": {
            "commits": len(commits),
            "lines_added": sum(c.added for c in commits),
            "lines_deleted": sum(c.deleted for c in commits),
            "releases": [name for name, _ in tags],
            "changes_logged": len(changes),
            "changes_released": sum(1 for c in changes if c.get("released_at")),
            "median_lead_time_h": median(all_lead_times),
            "change_failure_rate": change_failure_rate(changes),
            "ci": ci_summary(runs),
        },
        "sprints": per_sprint,
        "changes": [
            {
                "id": c.get("id", ""),
                "description": c.get("description", ""),
                "sprint": c.get("sprint"),
                "effort_hours": c.get("effort_hours"),
                "lead_time_h": lead_time_hours(c),
                "caused_failure": bool(c.get("caused_failure")),
            }
            for c in changes
        ],
    }


# --------------------------------------------------------------------------- output


def pct(value: float | None) -> str:
    return MISSING if value is None else f"{value * 100:.0f}%"


def to_markdown(metrics: dict[str, Any]) -> str:
    totals = metrics["totals"]
    lines = [
        "# Proof of concept metrics",
        f"_Generated {metrics['generated_at']} from git history and process/*.json_",
        "",
        "## Totals",
        f"- Commits: {totals['commits']} "
        f"(+{totals['lines_added']} / -{totals['lines_deleted']} lines)",
        f"- Releases (tags): {len(totals['releases'])} {', '.join(totals['releases'])}",
        f"- Requirement changes logged / released: "
        f"{totals['changes_logged']} / {totals['changes_released']}",
        f"- Median lead time for changes: {fmt(totals['median_lead_time_h'], suffix=' h')}",
        f"- Change failure rate: {pct(totals['change_failure_rate'])}",
        f"- CI runs on main: {totals['ci']['runs']}, pass rate {pct(totals['ci']['pass_rate'])}, "
        f"median duration {fmt(totals['ci']['median_duration_min'], suffix=' min')}",
        "",
        "## Per sprint",
        "| Sprint | Stories done | Commits | Releases | Median lead time (h) | CI pass rate |",
        "|---|---|---|---|---|---|",
    ]
    for row in metrics["sprints"]:
        lines.append(
            f"| {row['sprint']} | {row['completed']}/{row['planned']} | {row['commits']} | "
            f"{len(row['releases'])} | {fmt(row['median_lead_time_h'])} | "
            f"{pct(row['ci']['pass_rate'])} |"
        )
    lines += ["", "## Requirement changes", "| ID | Change | Sprint | Effort (h) | Lead time (h) |"]
    lines.append("|---|---|---|---|---|")
    for change in metrics["changes"]:
        lines.append(
            f"| {change['id']} | {change['description']} | {change['sprint'] or MISSING} | "
            f"{fmt(change['effort_hours'])} | {fmt(change['lead_time_h'])} |"
        )
    return "\n".join(lines)


def to_latex(metrics: dict[str, Any]) -> str:
    totals = metrics["totals"]
    out = [
        "% Generated by tools/collect_metrics.py on " + metrics["generated_at"],
        "% Paste the rows into the matching tables of the report.",
        "",
        "% --- Table tbl:PoCMetrics",
        "%     Sprint & Stories done & Releases & Median lead time (h) & CI pass rate",
    ]
    for row in metrics["sprints"]:
        out.append(
            f"{row['sprint']} & {row['completed']}/{row['planned']} & {len(row['releases'])} & "
            f"{fmt(row['median_lead_time_h'])} & {latex_escape(pct(row['ci']['pass_rate']))} \\\\"
        )
    out += [
        "",
        "% --- Table tbl:ChangeLog (ID & Change & Sprint & Effort (h) & Released after (days))",
    ]
    for change in metrics["changes"]:
        days = None if change["lead_time_h"] is None else change["lead_time_h"] / 24
        out.append(
            f"{latex_escape(change['id'])} & {latex_escape(change['description'])} & "
            f"{change['sprint'] or MISSING} & {fmt(change['effort_hours'])} & {fmt(days)} \\\\"
        )
    out += [
        "",
        "% --- Summary values for the text of Chapter 5",
        f"\\newcommand{{\\pocCommits}}{{{totals['commits']}}}",
        f"\\newcommand{{\\pocReleases}}{{{len(totals['releases'])}}}",
        f"\\newcommand{{\\pocChanges}}{{{totals['changes_released']}}}",
        f"\\newcommand{{\\pocMedianLeadTime}}{{{fmt(totals['median_lead_time_h'])}}}",
        f"\\newcommand{{\\pocChangeFailureRate}}{{{latex_escape(pct(totals['change_failure_rate']))}}}",
        f"\\newcommand{{\\pocCIRuns}}{{{totals['ci']['runs']}}}",
        f"\\newcommand{{\\pocCIPassRate}}{{{latex_escape(pct(totals['ci']['pass_rate']))}}}",
        f"\\newcommand{{\\pocCIMedianMinutes}}{{{fmt(totals['ci']['median_duration_min'])}}}",
    ]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root")
    parser.add_argument("--latex", type=Path, help="write LaTeX table rows to this file")
    parser.add_argument("--json", type=Path, help="write raw metrics as JSON to this file")
    args = parser.parse_args(argv)

    metrics = compute(args.root)
    print(to_markdown(metrics))
    for path, content in (
        (args.latex, to_latex(metrics) if args.latex else None),
        (args.json, json.dumps(metrics, indent=2, default=str) if args.json else None),
    ):
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"\nWrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
