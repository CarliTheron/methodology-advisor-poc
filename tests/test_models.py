import pytest

from advisor.models import ContextError, Level, ProjectContext, Regulation, YesNo


def make(team_size=5, **overrides):
    values = {
        "requirement_volatility": Level.MEDIUM,
        "team_size": team_size,
        "regulation": Regulation.NONE,
        "release_frequency": Level.MEDIUM,
        "team_maturity": Level.MEDIUM,
        "distributed_team": YesNo.NO,
    }
    values.update(overrides)
    return ProjectContext(**values)


@pytest.mark.parametrize(
    ("size", "band"),
    [(1, "small"), (9, "small"), (10, "medium"), (50, "medium"), (51, "large"), (1000, "large")],
)
def test_size_band_boundaries(size, band):
    assert make(team_size=size).size_band == band


@pytest.mark.parametrize("size", [0, -3, 1001])
def test_team_size_out_of_range_is_rejected(size):
    with pytest.raises(ContextError):
        make(team_size=size)


@pytest.mark.parametrize("size", [5.0, "5", True])
def test_team_size_must_be_integer(size):
    with pytest.raises(ContextError):
        make(team_size=size)


def test_factor_values_cover_all_factors():
    values = make(team_size=12).factor_values()
    assert values == {
        "requirement_volatility": "medium",
        "team_size": "medium",
        "regulation": "none",
        "release_frequency": "medium",
        "team_maturity": "medium",
        "distributed_team": "no",
    }


@pytest.mark.parametrize(("flag", "value"), [(YesNo.NO, "no"), (YesNo.YES, "yes")])
def test_distributed_team_factor_value(flag, value):
    assert make(distributed_team=flag).factor_values()["distributed_team"] == value


def test_from_dict_builds_context():
    context = ProjectContext.from_dict(
        {
            "requirement_volatility": "high",
            "team_size": 4,
            "regulation": "strict",
            "release_frequency": "low",
            "team_maturity": "high",
            "distributed_team": "yes",
        }
    )
    assert context.regulation is Regulation.STRICT
    assert context.size_band == "small"


def test_from_dict_reports_missing_fields():
    with pytest.raises(ContextError, match="team_size"):
        ProjectContext.from_dict(
            {
                "requirement_volatility": "high",
                "regulation": "none",
                "release_frequency": "low",
                "team_maturity": "high",
                "distributed_team": "yes",
            }
        )


def test_from_dict_rejects_unknown_level():
    with pytest.raises(ContextError):
        ProjectContext.from_dict(
            {
                "requirement_volatility": "extreme",
                "team_size": 4,
                "regulation": "none",
                "release_frequency": "low",
                "team_maturity": "high",
                "distributed_team": "yes",
            }
        )


def test_from_dict_preserves_context_error():
    with pytest.raises(ContextError, match="between 1"):
        ProjectContext.from_dict(
            {
                "requirement_volatility": "low",
                "team_size": 0,
                "regulation": "none",
                "release_frequency": "low",
                "team_maturity": "high",
                "distributed_team": "yes",
            }
        )


def test_from_dict_rejects_unknown_distributed_team_value():
    with pytest.raises(ContextError):
        ProjectContext.from_dict(
            {
                "requirement_volatility": "high",
                "team_size": 4,
                "regulation": "none",
                "release_frequency": "low",
                "team_maturity": "high",
                "distributed_team": "maybe",
            }
        )
