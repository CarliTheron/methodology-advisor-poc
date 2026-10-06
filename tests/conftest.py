import copy
import json
from pathlib import Path

import pytest

from advisor.models import Level, ProjectContext, Regulation, YesNo

RULES_PATH = Path(__file__).resolve().parents[1] / "config" / "rules.json"


@pytest.fixture
def rules_path() -> Path:
    return RULES_PATH


@pytest.fixture
def rules_data() -> dict:
    """A fresh, mutable copy of the shipped rules for each test."""
    return copy.deepcopy(json.loads(RULES_PATH.read_text(encoding="utf-8")))


@pytest.fixture
def startup_context() -> ProjectContext:
    """Small, distributed team, volatile requirements, unregulated, frequent releases."""
    return ProjectContext(
        requirement_volatility=Level.HIGH,
        team_size=6,
        regulation=Regulation.NONE,
        release_frequency=Level.HIGH,
        team_maturity=Level.MEDIUM,
        distributed_team=YesNo.YES,
    )


@pytest.fixture
def regulated_context() -> ProjectContext:
    """Large co-located team, stable requirements, strictly regulated, infrequent releases."""
    return ProjectContext(
        requirement_volatility=Level.LOW,
        team_size=80,
        regulation=Regulation.STRICT,
        release_frequency=Level.LOW,
        team_maturity=Level.LOW,
        distributed_team=YesNo.NO,
    )
