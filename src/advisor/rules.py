"""Loading and validation of the selection rules.

The rules are data, not code: they live in ``config/rules.json`` so that a
change in requirements (for example a new contextual factor) can be made and
validated without rewriting the engine. ``validate_rules`` is also run as a
quality gate in the CI pipeline.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

WEIGHT_MIN = -3
WEIGHT_MAX = 3


class RulesError(ValueError):
    """Raised when a rules file cannot be loaded or fails validation."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass(frozen=True)
class Methodology:
    key: str
    label: str
    weights: dict[str, dict[str, int]]
    rationale: str = ""
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class Caveat:
    when: dict[str, str]
    applies_to: tuple[str, ...]
    message: str


@dataclass(frozen=True)
class RuleSet:
    version: str
    factors: dict[str, tuple[str, ...]]
    methodologies: dict[str, Methodology]
    caveats: tuple[Caveat, ...] = field(default_factory=tuple)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_rules(data: Any) -> list[str]:
    """Return a list of validation errors; an empty list means the rules are valid."""
    if not isinstance(data, dict):
        return ["rules must be a JSON object"]

    errors: list[str] = []

    if not isinstance(data.get("version"), str) or not data.get("version"):
        errors.append("'version' must be a non-empty string")

    factors = data.get("factors")
    if not isinstance(factors, dict) or not factors:
        errors.append("'factors' must be a non-empty object")
        factors = {}
    for name, levels in factors.items():
        if (
            not isinstance(levels, list)
            or not levels
            or not all(isinstance(level, str) for level in levels)
        ):
            errors.append(f"factor '{name}' must list its levels as strings")
        elif len(set(levels)) != len(levels):
            errors.append(f"factor '{name}' has duplicate levels")

    methodologies = data.get("methodologies")
    if not isinstance(methodologies, dict) or not methodologies:
        errors.append("'methodologies' must be a non-empty object")
        methodologies = {}
    for key, method in methodologies.items():
        prefix = f"methodology '{key}'"
        if not isinstance(method, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if not isinstance(method.get("label"), str) or not method.get("label"):
            errors.append(f"{prefix} needs a non-empty 'label'")
        weights = method.get("weights")
        if not isinstance(weights, dict):
            errors.append(f"{prefix} needs a 'weights' object")
            continue
        for factor, levels in factors.items():
            factor_weights = weights.get(factor)
            if not isinstance(factor_weights, dict):
                errors.append(f"{prefix} has no weights for factor '{factor}'")
                continue
            for level in levels if isinstance(levels, list) else []:
                value = factor_weights.get(level)
                if value is None:
                    errors.append(f"{prefix} has no weight for {factor}={level}")
                elif not _is_int(value) or not WEIGHT_MIN <= value <= WEIGHT_MAX:
                    errors.append(
                        f"{prefix} weight for {factor}={level} must be an integer "
                        f"between {WEIGHT_MIN} and {WEIGHT_MAX}"
                    )
        unknown = sorted(set(weights) - set(factors))
        if unknown:
            errors.append(f"{prefix} has weights for unknown factors: {', '.join(unknown)}")

    caveats = data.get("caveats", [])
    if not isinstance(caveats, list):
        errors.append("'caveats' must be a list")
        caveats = []
    for index, caveat in enumerate(caveats):
        prefix = f"caveat {index + 1}"
        if not isinstance(caveat, dict):
            errors.append(f"{prefix} must be an object")
            continue
        when = caveat.get("when")
        if not isinstance(when, dict) or not when:
            errors.append(f"{prefix} needs a non-empty 'when' object")
        else:
            for factor, level in when.items():
                if factor not in factors:
                    errors.append(f"{prefix} refers to unknown factor '{factor}'")
                elif level not in factors[factor]:
                    errors.append(f"{prefix} refers to unknown level {factor}={level}")
        applies_to = caveat.get("applies_to")
        if not isinstance(applies_to, list) or not applies_to:
            errors.append(f"{prefix} needs a non-empty 'applies_to' list")
        else:
            for key in applies_to:
                if key not in methodologies:
                    errors.append(f"{prefix} refers to unknown methodology '{key}'")
        if not isinstance(caveat.get("message"), str) or not caveat.get("message"):
            errors.append(f"{prefix} needs a non-empty 'message'")

    return errors


def parse_rules(data: Any) -> RuleSet:
    """Validate raw rules data and convert it into a RuleSet."""
    errors = validate_rules(data)
    if errors:
        raise RulesError(errors)
    return RuleSet(
        version=data["version"],
        factors={name: tuple(levels) for name, levels in data["factors"].items()},
        methodologies={
            key: Methodology(
                key=key,
                label=method["label"],
                weights=method["weights"],
                rationale=method.get("rationale", ""),
                sources=tuple(method.get("sources", [])),
            )
            for key, method in data["methodologies"].items()
        },
        caveats=tuple(
            Caveat(
                when=caveat["when"],
                applies_to=tuple(caveat["applies_to"]),
                message=caveat["message"],
            )
            for caveat in data.get("caveats", [])
        ),
    )


def load_rules(path: str | Path) -> RuleSet:
    """Read, validate and parse a rules file."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RulesError([f"rules file not found: {path}"]) from exc
    except json.JSONDecodeError as exc:
        raise RulesError([f"rules file is not valid JSON: {exc}"]) from exc
    return parse_rules(data)
