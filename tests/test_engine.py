import pytest

from advisor.engine import EngineError, recommend
from advisor.models import Level, ProjectContext, Regulation
from advisor.rules import load_rules, parse_rules


@pytest.fixture
def rules(rules_path):
    return load_rules(rules_path)


def test_volatile_small_team_gets_agile_approach(startup_context, rules):
    result = recommend(startup_context, rules)
    assert result.best.key in {"scrum", "agile_devops"}
    assert result.ranking[-1].key == "plan_driven"


def test_stable_regulated_large_team_gets_plan_driven(regulated_context, rules):
    result = recommend(regulated_context, rules)
    assert result.best.key == "plan_driven"


def test_large_moderately_regulated_team_gets_hybrid(rules):
    context = ProjectContext(
        requirement_volatility=Level.MEDIUM,
        team_size=60,
        regulation=Regulation.MODERATE,
        release_frequency=Level.MEDIUM,
        team_maturity=Level.MEDIUM,
    )
    assert recommend(context, rules).best.key == "hybrid"


def test_high_maturity_shifts_towards_devops(startup_context, rules):
    mature = ProjectContext(
        requirement_volatility=startup_context.requirement_volatility,
        team_size=startup_context.team_size,
        regulation=startup_context.regulation,
        release_frequency=startup_context.release_frequency,
        team_maturity=Level.HIGH,
    )
    assert recommend(mature, rules).best.key == "agile_devops"


def test_scores_equal_sum_of_contributions(startup_context, rules):
    for score in recommend(startup_context, rules).ranking:
        assert score.total == sum(score.contributions.values())
        assert set(score.contributions) == set(rules.factors)


def test_ranking_is_sorted_and_complete(startup_context, rules):
    ranking = recommend(startup_context, rules).ranking
    totals = [score.total for score in ranking]
    assert totals == sorted(totals, reverse=True)
    assert {score.key for score in ranking} == set(rules.methodologies)


def test_ties_are_broken_alphabetically(rules_data, startup_context):
    for method in rules_data["methodologies"].values():
        for factor_weights in method["weights"].values():
            for level in factor_weights:
                factor_weights[level] = 0
    result = recommend(startup_context, parse_rules(rules_data))
    assert [score.key for score in result.ranking] == sorted(rules_data["methodologies"])


def test_caveat_applies_only_to_matching_recommendation(regulated_context, rules):
    # Low maturity caveat targets agile methods; plan-driven is recommended here.
    result = recommend(regulated_context, rules)
    assert not any("maturity" in message for message in result.caveats)


def test_caveat_is_reported_for_matching_context(rules):
    context = ProjectContext(
        requirement_volatility=Level.HIGH,
        team_size=5,
        regulation=Regulation.NONE,
        release_frequency=Level.HIGH,
        team_maturity=Level.LOW,
    )
    result = recommend(context, rules)
    assert result.best.key in {"scrum", "kanban", "agile_devops"}
    assert any("maturity is low" in message for message in result.caveats)


def test_rules_version_is_reported(startup_context, rules):
    assert recommend(startup_context, rules).rules_version == rules.version


def test_unknown_factor_in_rules_is_rejected(rules_data, startup_context):
    rules_data["factors"]["distributed_team"] = ["no", "yes"]
    for method in rules_data["methodologies"].values():
        method["weights"]["distributed_team"] = {"no": 0, "yes": 0}
    with pytest.raises(EngineError, match="distributed_team"):
        recommend(startup_context, parse_rules(rules_data))


def test_unsupported_level_is_rejected(rules_data, startup_context):
    rules_data["factors"]["regulation"] = ["moderate", "strict"]
    for method in rules_data["methodologies"].values():
        del method["weights"]["regulation"]["none"]
    rules_data["caveats"] = []
    with pytest.raises(EngineError, match="regulation"):
        recommend(startup_context, parse_rules(rules_data))
