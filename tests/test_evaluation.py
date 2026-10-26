import json
from pathlib import Path

import pytest

from advisor import cli
from advisor.evaluation import (
    ExpectationError,
    check_expectations,
    format_checks_markdown,
    format_sensitivity_markdown,
    load_expectations,
    sensitivity,
)
from advisor.rules import load_rules, parse_rules

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "evaluation" / "scenarios.json"
EXPECTED = ROOT / "evaluation" / "expectations.json"

SMALL_VOLATILE = {
    "name": "small volatile",
    "requirement_volatility": "high",
    "team_size": 5,
    "regulation": "none",
    "release_frequency": "medium",
    "team_maturity": "medium",
    "distributed_team": "no",
}


def write_json(path: Path, data) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ------------------------------------------------------------------ expectations file


def test_load_expectations_reads_shipped_file():
    expectations = load_expectations(EXPECTED)
    assert len(expectations) == 5


def test_load_expectations_missing_file(tmp_path):
    with pytest.raises(ExpectationError, match="not found"):
        load_expectations(tmp_path / "missing.json")


def test_load_expectations_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ExpectationError, match="not valid JSON"):
        load_expectations(path)


@pytest.mark.parametrize(
    "data",
    [[], {"scenarios": {}}, {"scenarios": {"x": {"acceptable_top": []}}}, {"scenarios": {"x": 1}}],
)
def test_load_expectations_rejects_bad_structure(tmp_path, data):
    with pytest.raises(ExpectationError):
        load_expectations(write_json(tmp_path / "e.json", data))


# ------------------------------------------------------------------ expectation checks


def test_shipped_scenarios_agree_with_expectations(rules_path):
    rules = load_rules(rules_path)
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    checks = check_expectations(scenarios, load_expectations(EXPECTED), rules)
    assert len(checks) == 5
    assert all(check.agrees for check in checks)


def test_check_reports_unexpected_top(rules_path):
    rules = load_rules(rules_path)
    checks = check_expectations(
        [SMALL_VOLATILE], {"small volatile": {"acceptable_top": ["plan_driven"]}}, rules
    )
    assert not checks[0].agrees
    assert "not one of plan_driven" in checks[0].problems[0]


def test_check_reports_not_top_and_missing_caveat(rules_path):
    rules = load_rules(rules_path)
    expected = {
        "small volatile": {
            "acceptable_top": ["scrum"],
            "not_top": ["scrum"],
            "required_caveat_keyword": "training",
        }
    }
    problems = check_expectations([SMALL_VOLATILE], expected, rules)[0].problems
    assert any("NOT to be the top" in problem for problem in problems)
    assert any("no caveat mentions 'training'" in problem for problem in problems)


def test_check_requires_an_expectation_for_every_scenario(rules_path):
    rules = load_rules(rules_path)
    with pytest.raises(ExpectationError, match="no expectation"):
        check_expectations([SMALL_VOLATILE], {"other": {"acceptable_top": ["scrum"]}}, rules)


def test_check_with_single_methodology_has_zero_margin(rules_data):
    rules_data["methodologies"] = {"scrum": rules_data["methodologies"]["scrum"]}
    rules_data["caveats"] = []
    rules = parse_rules(rules_data)
    check = check_expectations(
        [SMALL_VOLATILE], {"small volatile": {"acceptable_top": ["scrum"]}}, rules
    )[0]
    assert check.runner_up == "scrum"
    assert check.margin == 0


def test_format_checks_markdown_summarises_agreement(rules_path):
    rules = load_rules(rules_path)
    expected = {"small volatile": {"acceptable_top": ["plan_driven"]}}
    text = format_checks_markdown(check_expectations([SMALL_VOLATILE], expected, rules))
    assert "| NO |" in text
    assert "Agreement: 0 of 1 scenarios." in text


# ------------------------------------------------------------------ sensitivity


def context_of(entry):
    from advisor.models import ProjectContext

    return ProjectContext.from_dict(entry)


def test_sensitivity_counts_only_in_range_changes(rules_path):
    rules = load_rules(rules_path)
    result = sensitivity("small volatile", context_of(SMALL_VOLATILE), rules)
    # 5 methodologies x 6 factors x 2 directions = 60, minus changes that would leave [-3, 3].
    assert 0 < result.perturbations < 60
    assert result.step == 1
    assert result.top == "scrum"


def test_sensitivity_finds_flips_in_a_close_call(rules_data):
    # Make plan_driven and hybrid tie-adjacent so a single change flips the top.
    rules = parse_rules(rules_data)
    entry = dict(SMALL_VOLATILE, requirement_volatility="low", team_size=60, regulation="strict")
    entry["release_frequency"] = "low"
    result = sensitivity("B", context_of(entry), rules, step=2)
    assert result.flips
    assert 0 < result.flip_share <= 1
    assert all(flip.new_top != result.top for flip in result.flips)


def test_sensitivity_flip_share_is_zero_without_perturbations(rules_data):
    for method in rules_data["methodologies"].values():
        for levels in method["weights"].values():
            for level in levels:
                levels[level] = 3
    rules = parse_rules(rules_data)
    result = sensitivity("x", context_of(SMALL_VOLATILE), rules, step=2)
    # Every weight is +3, so only -2 changes are allowed and +2 changes are skipped.
    assert result.perturbations == 5 * 6
    empty = type(result)(name="x", top="scrum", step=1, perturbations=0, flips=())
    assert empty.flip_share == 0.0


def test_format_sensitivity_markdown_lists_flips(rules_path):
    rules = load_rules(rules_path)
    entry = dict(SMALL_VOLATILE, requirement_volatility="low", team_size=60, regulation="strict")
    entry["release_frequency"] = "low"
    text = format_sensitivity_markdown([sensitivity("B", context_of(entry), rules, step=2)])
    assert "+/-2" in text
    assert "Changes that alter the top recommendation:" in text


def test_format_sensitivity_markdown_without_flips(rules_path):
    rules = load_rules(rules_path)
    text = format_sensitivity_markdown([sensitivity("A", context_of(SMALL_VOLATILE), rules)])
    assert "Changes that alter the top recommendation:" not in text
    assert format_sensitivity_markdown([]).startswith("Each relevant weight changed by +/-1")


# ------------------------------------------------------------------ CLI


def test_cli_check_scenarios(capsys):
    args = ["check-scenarios", "--input", str(SCENARIOS), "--expected", str(EXPECTED)]
    assert cli.main(args) == 0
    assert "Agreement: 5 of 5 scenarios." in capsys.readouterr().out


def test_cli_sensitivity(capsys):
    assert cli.main(["sensitivity", "--input", str(SCENARIOS), "--step", "2"]) == 0
    assert "+/-2" in capsys.readouterr().out


def test_cli_check_scenarios_reports_bad_expectations(tmp_path, capsys):
    bad = write_json(tmp_path / "e.json", {"scenarios": {}})
    assert cli.main(["check-scenarios", "--input", str(SCENARIOS), "--expected", str(bad)]) == 1
    assert "Error:" in capsys.readouterr().err


def test_cli_sensitivity_reports_bad_scenario(tmp_path, capsys):
    bad = write_json(tmp_path / "s.json", [{"name": "incomplete"}])
    assert cli.main(["sensitivity", "--input", str(bad)]) == 1
    assert "Error:" in capsys.readouterr().err
