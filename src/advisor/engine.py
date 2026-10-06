"""Recommendation engine.

Each candidate methodology receives a score equal to the sum of its weights
for the project's factor values. Scores are transparent: every recommendation
reports the contribution of each factor, so the reasoning can be inspected and
challenged rather than taken on trust.
"""

from __future__ import annotations

from dataclasses import dataclass

from advisor.models import ProjectContext
from advisor.rules import RuleSet


class EngineError(ValueError):
    """Raised when a context cannot be evaluated against a rule set."""


@dataclass(frozen=True)
class Score:
    key: str
    label: str
    total: int
    contributions: dict[str, int]


@dataclass(frozen=True)
class Recommendation:
    ranking: tuple[Score, ...]
    caveats: tuple[str, ...]
    rules_version: str

    @property
    def best(self) -> Score:
        return self.ranking[0]


def recommend(context: ProjectContext, rules: RuleSet) -> Recommendation:
    """Rank all methodologies in ``rules`` for the given project context."""
    values = context.factor_values()

    for factor, levels in rules.factors.items():
        if factor not in values:
            raise EngineError(f"context does not provide factor '{factor}'")
        if values[factor] not in levels:
            raise EngineError(f"value '{values[factor]}' is not a level of factor '{factor}'")

    scores = []
    for method in rules.methodologies.values():
        contributions = {factor: method.weights[factor][values[factor]] for factor in rules.factors}
        scores.append(
            Score(
                key=method.key,
                label=method.label,
                total=sum(contributions.values()),
                contributions=contributions,
            )
        )

    # Highest score first; ties broken alphabetically so output is deterministic.
    ranking = tuple(sorted(scores, key=lambda score: (-score.total, score.key)))

    best_key = ranking[0].key
    caveats = tuple(
        caveat.message
        for caveat in rules.caveats
        if best_key in caveat.applies_to
        and all(values.get(factor) == level for factor, level in caveat.when.items())
    )

    return Recommendation(ranking=ranking, caveats=caveats, rules_version=rules.version)
