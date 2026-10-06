import json
import runpy
import sys

import pytest

from advisor import cli

BASE_ARGS = [
    "recommend",
    "--volatility",
    "high",
    "--team-size",
    "6",
    "--regulation",
    "none",
    "--release-frequency",
    "high",
    "--maturity",
    "medium",
    "--distributed-team",
    "no",
]


def test_recommend_text_output(capsys):
    assert cli.main(BASE_ARGS) == 0
    out = capsys.readouterr().out
    assert out.startswith("Recommended: ")
    assert "Ranking:" in out
    assert "Rules version: 1.0.0" in out


def test_recommend_json_output(capsys):
    assert cli.main([*BASE_ARGS, "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["recommended"] == payload["ranking"][0]["key"]
    assert len(payload["ranking"]) == 5


def test_text_output_lists_caveats(capsys):
    args = [*BASE_ARGS]
    args[args.index("medium")] = "low"  # --maturity low
    assert cli.main(args) == 0
    assert "Caveats:" in capsys.readouterr().out


def test_recommend_markdown_output(capsys):
    assert cli.main([*BASE_ARGS, "--format", "markdown"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# Methodology recommendation:")
    assert "## Ranking" in out
    assert "| Rank | Methodology | Score |" in out


def test_markdown_output_lists_caveats(capsys):
    args = [*BASE_ARGS]
    args[args.index("medium")] = "low"  # --maturity low
    assert cli.main([*args, "--format", "markdown"]) == 0
    assert "## Caveats" in capsys.readouterr().out


def test_recommend_writes_markdown_to_file(tmp_path):
    output = tmp_path / "report.md"
    assert cli.main([*BASE_ARGS, "--format", "markdown", "--output", str(output)]) == 0
    content = output.read_text(encoding="utf-8")
    assert content.startswith("# Methodology recommendation:")


def test_recommend_text_output_can_be_written_to_file(tmp_path):
    output = tmp_path / "report.txt"
    assert cli.main([*BASE_ARGS, "--output", str(output)]) == 0
    assert output.read_text(encoding="utf-8").startswith("Recommended: ")


def test_validate_rules_ok(capsys):
    assert cli.main(["validate-rules"]) == 0
    assert "Rules OK" in capsys.readouterr().out


def test_validate_rules_fails_on_invalid_file(tmp_path, capsys):
    bad = tmp_path / "rules.json"
    bad.write_text('{"version": "x"}', encoding="utf-8")
    assert cli.main(["--rules", str(bad), "validate-rules"]) == 1
    assert "Rules validation failed" in capsys.readouterr().err


def test_rules_path_from_environment(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("ADVISOR_RULES", str(tmp_path / "missing.json"))
    assert cli.main(["validate-rules"]) == 1
    assert "not found" in capsys.readouterr().err


def test_invalid_team_size_returns_error(capsys):
    args = [*BASE_ARGS]
    args[args.index("6")] = "0"
    assert cli.main(args) == 2
    assert "team_size" in capsys.readouterr().err


def test_invalid_choice_exits(capsys):
    with pytest.raises(SystemExit):
        cli.main(["recommend", "--volatility", "extreme"])


def test_module_entry_point(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["advisor", "validate-rules"])
    with pytest.raises(SystemExit) as info:
        runpy.run_module("advisor", run_name="__main__")
    assert info.value.code == 0
