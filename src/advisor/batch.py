"""Batch evaluation of multiple project scenarios from a single input file.

Supports US-07: comparing the framework's recommendation across many project
contexts at once, without invoking the CLI once per scenario.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from advisor.engine import Recommendation, recommend
from advisor.models import ContextError, ProjectContext
from advisor.rules import RuleSet


class ScenarioError(ValueError):
    """Raised when a scenario file itself is invalid (not a single bad scenario)."""


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    recommendation: Recommendation | None
    error: str | None = None


def load_scenarios(path: str | Path) -> list[dict[str, Any]]:
    """Read a JSON array of scenario objects from ``path``."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ScenarioError(f"scenario file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ScenarioError(f"scenario file is not valid JSON: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise ScenarioError("scenario file must contain a non-empty JSON array")
    for index, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise ScenarioError(f"scenario {index + 1} must be a JSON object")
    return data


def evaluate_scenarios(scenarios: list[dict[str, Any]], rules: RuleSet) -> list[ScenarioResult]:
    """Run ``recommend`` for every scenario, capturing per-scenario context errors.

    A malformed individual scenario (e.g. a missing field) is reported as that
    scenario's error rather than aborting the whole batch.
    """
    results = []
    for index, entry in enumerate(scenarios):
        name = str(entry.get("name", f"scenario {index + 1}"))
        try:
            context = ProjectContext.from_dict(entry)
            recommendation = recommend(context, rules)
            results.append(ScenarioResult(name=name, recommendation=recommendation))
        except ContextError as exc:
            results.append(ScenarioResult(name=name, recommendation=None, error=str(exc)))
    return results
