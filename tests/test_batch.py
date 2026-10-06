import json

import pytest

from advisor.batch import ScenarioError, evaluate_scenarios, load_scenarios
from advisor.rules import load_rules


@pytest.fixture
def rules(rules_path):
    return load_rules(rules_path)


def test_load_scenarios_reads_json_array(tmp_path):
    path = tmp_path / "scenarios.json"
    path.write_text(json.dumps([{"name": "a", "team_size": 5}]), encoding="utf-8")
    assert load_scenarios(path) == [{"name": "a", "team_size": 5}]


def test_load_scenarios_missing_file(tmp_path):
    with pytest.raises(ScenarioError, match="not found"):
        load_scenarios(tmp_path / "missing.json")


def test_load_scenarios_invalid_json(tmp_path):
    path = tmp_path / "scenarios.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ScenarioError, match="not valid JSON"):
        load_scenarios(path)


def test_load_scenarios_rejects_non_array(tmp_path):
    path = tmp_path / "scenarios.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ScenarioError, match="non-empty JSON array"):
        load_scenarios(path)


def test_load_scenarios_rejects_non_object_entries(tmp_path):
    path = tmp_path / "scenarios.json"
    path.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ScenarioError, match="scenario 1 must be a JSON object"):
        load_scenarios(path)


def test_evaluate_scenarios_returns_one_result_per_entry(rules):
    scenarios = [
        {
            "name": "Startup",
            "requirement_volatility": "high",
            "team_size": 6,
            "regulation": "none",
            "release_frequency": "high",
            "team_maturity": "medium",
            "distributed_team": "yes",
        },
        {
            "name": "Enterprise",
            "requirement_volatility": "low",
            "team_size": 80,
            "regulation": "strict",
            "release_frequency": "low",
            "team_maturity": "low",
            "distributed_team": "no",
        },
    ]
    results = evaluate_scenarios(scenarios, rules)
    assert [r.name for r in results] == ["Startup", "Enterprise"]
    assert results[0].recommendation is not None
    assert results[0].error is None
    assert results[1].recommendation.best.key == "plan_driven"


def test_evaluate_scenarios_captures_invalid_context(rules):
    results = evaluate_scenarios([{"name": "Broken", "team_size": 6}], rules)
    assert results[0].recommendation is None
    assert "missing context fields" in results[0].error


def test_evaluate_scenarios_names_unlabelled_entries_by_position(rules):
    scenarios = [
        {
            "requirement_volatility": "high",
            "team_size": 6,
            "regulation": "none",
            "release_frequency": "high",
            "team_maturity": "medium",
            "distributed_team": "yes",
        }
    ]
    results = evaluate_scenarios(scenarios, rules)
    assert results[0].name == "scenario 1"
