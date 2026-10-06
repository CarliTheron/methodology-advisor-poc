import json
import os
import subprocess
from datetime import timezone

import pytest

import collect_metrics as cm


def test_parse_dt_handles_dates_datetimes_and_z():
    assert cm.parse_dt(None) is None
    start = cm.parse_dt("2026-10-05")
    end = cm.parse_dt("2026-10-05", end_of_day=True)
    assert start.tzinfo is timezone.utc and start.hour == 0
    assert end.hour == 23
    assert cm.parse_dt("2026-10-05T10:00:00Z").tzinfo is not None


def test_lead_time_hours():
    change = {
        "requested_at": "2026-10-05T08:00:00+02:00",
        "released_at": "2026-10-06T08:00:00+02:00",
    }
    assert cm.lead_time_hours(change) == 24
    assert cm.lead_time_hours({"requested_at": "2026-10-05"}) is None
    assert cm.lead_time_hours({"requested_at": "2026-10-06", "released_at": "2026-10-05"}) is None


def test_change_failure_rate_uses_released_changes_only():
    changes = [
        {"released_at": "2026-10-06", "caused_failure": True},
        {"released_at": "2026-10-07"},
        {"released_at": None, "caused_failure": True},
    ]
    assert cm.change_failure_rate(changes) == 0.5
    assert cm.change_failure_rate([]) is None


def test_ci_summary_and_branch_filter():
    data = {
        "workflow_runs": [
            {
                "head_branch": "main",
                "status": "completed",
                "conclusion": "success",
                "run_started_at": "2026-10-05T10:00:00Z",
                "updated_at": "2026-10-05T10:02:00Z",
            },
            {
                "head_branch": "main",
                "status": "completed",
                "conclusion": "failure",
                "run_started_at": "2026-10-05T11:00:00Z",
                "updated_at": "2026-10-05T11:04:00Z",
            },
            {"head_branch": "feature", "status": "completed", "conclusion": "success"},
            {"head_branch": "main", "status": "in_progress", "conclusion": None},
        ]
    }
    summary = cm.ci_summary(cm.ci_runs_on_branch(data))
    assert summary["runs"] == 2
    assert summary["pass_rate"] == 0.5
    assert summary["median_duration_min"] == 3


def test_empty_sources_report_missing_values():
    summary = cm.ci_summary([])
    assert summary["pass_rate"] is None
    assert cm.pct(None) == cm.MISSING
    assert cm.fmt(None) == cm.MISSING


def test_latex_escape():
    assert cm.latex_escape("50% & a_b") == r"50\% \& a\_b"


@pytest.fixture
def repo(tmp_path):
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
        "GIT_AUTHOR_DATE": "2026-10-06T10:00:00+02:00",
        "GIT_COMMITTER_DATE": "2026-10-06T10:00:00+02:00",
    }

    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, env=env, check=True, capture_output=True)

    git("init", "-q")
    (tmp_path / "a.txt").write_text("one\ntwo\n")
    git("add", ".")
    git("commit", "-q", "-m", "first")
    git("tag", "-a", "v0.1.0", "-m", "release")

    process = tmp_path / "process"
    process.mkdir()
    (process / "sprints.json").write_text(
        json.dumps(
            {
                "sprints": [
                    {
                        "id": 1,
                        "goal": "g",
                        "start": "2026-10-05",
                        "end": "2026-10-09",
                        "planned": ["US-01", "US-02"],
                        "completed": ["US-01"],
                    },
                ]
            }
        )
    )
    (process / "changes.json").write_text(
        json.dumps(
            {
                "changes": [
                    {
                        "id": "C1",
                        "description": "Add factor",
                        "sprint": 1,
                        "effort_hours": 2,
                        "requested_at": "2026-10-06T08:00:00+02:00",
                        "released_at": "2026-10-06T20:00:00+02:00",
                    },
                ]
            }
        )
    )
    return tmp_path


def test_compute_from_git_and_process_files(repo):
    metrics = cm.compute(repo)
    assert metrics["totals"]["commits"] == 1
    assert metrics["totals"]["lines_added"] == 2
    assert metrics["totals"]["releases"] == ["v0.1.0"]
    sprint = metrics["sprints"][0]
    assert (sprint["completed"], sprint["planned"], sprint["commits"]) == (1, 2, 1)
    assert sprint["releases"] == ["v0.1.0"]
    assert sprint["median_lead_time_h"] == 12


def test_main_writes_outputs(repo, capsys):
    latex = repo / "out" / "tables.tex"
    raw = repo / "out" / "metrics.json"
    assert cm.main(["--root", str(repo), "--latex", str(latex), "--json", str(raw)]) == 0
    assert "# Proof of concept metrics" in capsys.readouterr().out
    assert "1 & 1/2 & 1 & 12.0 &" in latex.read_text()
    assert json.loads(raw.read_text())["totals"]["changes_released"] == 1


def test_compute_without_git_or_records(tmp_path):
    metrics = cm.compute(tmp_path)
    assert metrics["totals"]["commits"] == 0
    assert metrics["sprints"] == []
