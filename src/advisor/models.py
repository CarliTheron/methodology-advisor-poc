"""Domain model: the project context that drives methodology selection.

The five factors mirror the "contextual drivers" tier of the conceptual
framework in the research report (Figure 2.1).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Level(str, Enum):
    """Ordinal level used for volatility, release frequency and maturity."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Regulation(str, Enum):
    """Degree of external regulatory or documentation constraint."""

    NONE = "none"
    MODERATE = "moderate"
    STRICT = "strict"


# Team size bands. Upper bounds are inclusive.
SMALL_TEAM_MAX = 9
MEDIUM_TEAM_MAX = 50
MAX_TEAM_SIZE = 1000


class ContextError(ValueError):
    """Raised when a project context is incomplete or invalid."""


@dataclass(frozen=True)
class ProjectContext:
    """Characteristics of a software project relevant to methodology choice."""

    requirement_volatility: Level
    team_size: int
    regulation: Regulation
    release_frequency: Level
    team_maturity: Level

    def __post_init__(self) -> None:
        if isinstance(self.team_size, bool) or not isinstance(self.team_size, int):
            raise ContextError("team_size must be an integer")
        if not 1 <= self.team_size <= MAX_TEAM_SIZE:
            raise ContextError(f"team_size must be between 1 and {MAX_TEAM_SIZE}")

    @property
    def size_band(self) -> str:
        """Classify the team size as small, medium or large."""
        if self.team_size <= SMALL_TEAM_MAX:
            return "small"
        if self.team_size <= MEDIUM_TEAM_MAX:
            return "medium"
        return "large"

    def factor_values(self) -> dict[str, str]:
        """Return the categorical value of every factor, keyed by factor name."""
        return {
            "requirement_volatility": self.requirement_volatility.value,
            "team_size": self.size_band,
            "regulation": self.regulation.value,
            "release_frequency": self.release_frequency.value,
            "team_maturity": self.team_maturity.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectContext:
        """Build a context from plain values, e.g. parsed CLI arguments or JSON."""
        required = (
            "requirement_volatility",
            "team_size",
            "regulation",
            "release_frequency",
            "team_maturity",
        )
        missing = [key for key in required if key not in data]
        if missing:
            raise ContextError(f"missing context fields: {', '.join(missing)}")
        try:
            return cls(
                requirement_volatility=Level(data["requirement_volatility"]),
                team_size=data["team_size"],
                regulation=Regulation(data["regulation"]),
                release_frequency=Level(data["release_frequency"]),
                team_maturity=Level(data["team_maturity"]),
            )
        except ValueError as exc:
            if isinstance(exc, ContextError):
                raise
            raise ContextError(str(exc)) from exc
