import pytest

from advisor.rules import RulesError, load_rules, parse_rules, validate_rules


def test_shipped_rules_are_valid(rules_data):
    assert validate_rules(rules_data) == []


def test_load_rules_parses_shipped_file(rules_path):
    rules = load_rules(rules_path)
    assert rules.version == "1.0.0"
    assert set(rules.methodologies) == {"plan_driven", "scrum", "kanban", "agile_devops", "hybrid"}
    assert len(rules.factors) == 5
    assert rules.caveats


def test_load_rules_missing_file(tmp_path):
    with pytest.raises(RulesError, match="not found"):
        load_rules(tmp_path / "missing.json")


def test_load_rules_invalid_json(tmp_path):
    bad = tmp_path / "rules.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(RulesError, match="not valid JSON"):
        load_rules(bad)


def test_rules_must_be_object():
    assert validate_rules([]) == ["rules must be a JSON object"]


def test_missing_version_and_sections():
    errors = validate_rules({})
    assert "'version' must be a non-empty string" in errors
    assert "'factors' must be a non-empty object" in errors
    assert "'methodologies' must be a non-empty object" in errors


def test_missing_weight_is_reported(rules_data):
    del rules_data["methodologies"]["scrum"]["weights"]["regulation"]["strict"]
    assert "methodology 'scrum' has no weight for regulation=strict" in validate_rules(rules_data)


def test_missing_factor_weights_are_reported(rules_data):
    del rules_data["methodologies"]["kanban"]["weights"]["team_size"]
    assert "methodology 'kanban' has no weights for factor 'team_size'" in validate_rules(
        rules_data
    )


@pytest.mark.parametrize("bad_weight", [4, -4, 1.5, True, "2"])
def test_weights_must_be_bounded_integers(rules_data, bad_weight):
    rules_data["methodologies"]["hybrid"]["weights"]["team_size"]["large"] = bad_weight
    errors = validate_rules(rules_data)
    assert any("hybrid" in error and "team_size=large" in error for error in errors)


def test_new_factor_requires_weights_for_every_methodology(rules_data):
    """A requirement change that adds a factor must be completed for all methodologies."""
    rules_data["factors"]["distributed_team"] = ["no", "yes"]
    errors = validate_rules(rules_data)
    assert len(errors) == len(rules_data["methodologies"])


def test_unknown_factor_in_weights(rules_data):
    rules_data["methodologies"]["scrum"]["weights"]["budget"] = {"low": 1}
    assert "methodology 'scrum' has weights for unknown factors: budget" in validate_rules(
        rules_data
    )


def test_bad_factor_definitions(rules_data):
    rules_data["factors"]["team_size"] = ["small", "small", "large"]
    rules_data["factors"]["regulation"] = []
    errors = validate_rules(rules_data)
    assert "factor 'team_size' has duplicate levels" in errors
    assert "factor 'regulation' must list its levels as strings" in errors


def test_bad_methodology_definitions(rules_data):
    rules_data["methodologies"]["scrum"] = "not an object"
    rules_data["methodologies"]["kanban"]["label"] = ""
    rules_data["methodologies"]["hybrid"]["weights"] = []
    errors = validate_rules(rules_data)
    assert "methodology 'scrum' must be an object" in errors
    assert "methodology 'kanban' needs a non-empty 'label'" in errors
    assert "methodology 'hybrid' needs a 'weights' object" in errors


def test_caveat_validation(rules_data):
    rules_data["caveats"] = [
        "not an object",
        {"when": {}, "applies_to": [], "message": ""},
        {"when": {"budget": "low"}, "applies_to": ["xp"], "message": "x"},
        {"when": {"regulation": "extreme"}, "applies_to": ["scrum"], "message": "x"},
    ]
    errors = validate_rules(rules_data)
    assert "caveat 1 must be an object" in errors
    assert "caveat 2 needs a non-empty 'when' object" in errors
    assert "caveat 2 needs a non-empty 'applies_to' list" in errors
    assert "caveat 2 needs a non-empty 'message'" in errors
    assert "caveat 3 refers to unknown factor 'budget'" in errors
    assert "caveat 3 refers to unknown methodology 'xp'" in errors
    assert "caveat 4 refers to unknown level regulation=extreme" in errors


def test_caveats_must_be_list(rules_data):
    rules_data["caveats"] = {}
    assert "'caveats' must be a list" in validate_rules(rules_data)


def test_parse_rules_raises_with_all_errors(rules_data):
    del rules_data["version"]
    with pytest.raises(RulesError) as info:
        parse_rules(rules_data)
    assert "'version' must be a non-empty string" in info.value.errors
