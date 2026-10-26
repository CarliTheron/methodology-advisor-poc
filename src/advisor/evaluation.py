"""Evaluation of the selection rules: scenario checks and weight sensitivity.

Supports change C4 (independent scenario evaluation) and C5 (weight
sensitivity), both requested in the supervisor's feedback on the draft report.

* ``check_expectations`` compares the tool's recommendation for each scenario
  with an expected outcome that was written down *before* the tool was run.
* ``sensitivity`` changes one weight at a time by +1 or -1 (kept within the
  allowed range) and records whether the top recommendation changes. A
  recommendation that flips under many single-point changes rests on weights
  that are too finely balanced to be trusted.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from advisor.engine import Recommendation, recommend
from advisor.models import ProjectContext
from advisor.rules import WEIGHT_MAX, WEIGHT_MIN, RuleSet


class ExpectationError(ValueError):
    """Raised when an expectations file is invalid."""


@dataclass(frozen=True)
class ExpectationCheck:
    name: str
    top: str
    top_score: int
    runner_up: str
    margin: int
    acceptable_top: tuple[str, ...]
    caveats: tuple[str, ...]
    problems: tuple[str, ...]

    @property
    def agrees(self) -> bool:
        return not self.problems


def load_expectations(path: str | Path) -> dict[str, dict[str, Any]]:
    """Read the expectations file and return the per-scenario expectations."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ExpectationError(f"expectations file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ExpectationError(f"expectations file is not valid JSON: {exc}") from exc
    scenarios = data.get("scenarios") if isinstance(data, dict) else None
    if not isinstance(scenarios, dict) or not scenarios:
        raise ExpectationError("expectations file needs a non-empty 'scenarios' object")
    for name, expected in scenarios.items():
        acceptable = expected.get("acceptable_top") if isinstance(expected, dict) else None
        if not isinstance(acceptable, list) or not acceptable:
            raise ExpectationError(f"scenario '{name}' needs a non-empty 'acceptable_top' list")
    return scenarios


def _check_one(name: str, result: Recommendation, expected: dict[str, Any]) -> ExpectationCheck:
    top = result.best.key
    problems = []
    acceptable = tuple(expected["acceptable_top"])
    if top not in acceptable:
        problems.append(f"top recommendation '{top}' is not one of {', '.join(acceptable)}")
    if top in expected.get("not_top", []):
        problems.append(f"'{top}' was expected NOT to be the top recommendation")
    keyword = expected.get("required_caveat_keyword")
    if keyword and not any(keyword.lower() in caveat.lower() for caveat in result.caveats):
        problems.append(f"no caveat mentions '{keyword}'")
    runner_up = result.ranking[1] if len(result.ranking) > 1 else result.best
    return ExpectationCheck(
        name=name,
        top=top,
        top_score=result.best.total,
        runner_up=runner_up.key,
        margin=result.best.total - runner_up.total,
        acceptable_top=acceptable,
        caveats=result.caveats,
        problems=tuple(problems),
    )


def check_expectations(
    scenarios: list[dict[str, Any]],
    expectations: dict[str, dict[str, Any]],
    rules: RuleSet,
) -> list[ExpectationCheck]:
    """Run every scenario and compare its recommendation with its expectation."""
    checks = []
    for entry in scenarios:
        name = str(entry.get("name", ""))
        if name not in expectations:
            raise ExpectationError(f"no expectation recorded for scenario '{name}'")
        result = recommend(ProjectContext.from_dict(entry), rules)
        checks.append(_check_one(name, result, expectations[name]))
    return checks


@dataclass(frozen=True)
class Flip:
    methodology: str
    factor: str
    level: str
    delta: int
    new_top: str


@dataclass(frozen=True)
class SensitivityResult:
    name: str
    top: str
    step: int
    perturbations: int
    flips: tuple[Flip, ...]

    @property
    def flip_share(self) -> float:
        return len(self.flips) / self.perturbations if self.perturbations else 0.0


def _with_weight(rules: RuleSet, method: str, factor: str, level: str, value: int) -> RuleSet:
    original = rules.methodologies[method]
    weights = {f: dict(levels) for f, levels in original.weights.items()}
    weights[factor][level] = value
    methodologies = dict(rules.methodologies)
    methodologies[method] = replace(original, weights=weights)
    return replace(rules, methodologies=methodologies)


def sensitivity(
    name: str, context: ProjectContext, rules: RuleSet, step: int = 1
) -> SensitivityResult:
    """Change each weight that this context uses by +/-step and record top-ranking flips.

    Only the weights for the context's own factor levels can change its scores,
    so those are the ones perturbed. A change that would leave the allowed range
    is skipped rather than clamped, so every counted perturbation is real.
    """
    values = context.factor_values()
    baseline = recommend(context, rules).best.key
    flips = []
    count = 0
    for method_key, method in rules.methodologies.items():
        for factor, level in values.items():
            current = method.weights[factor][level]
            for delta in (-step, step):
                new_value = current + delta
                if not WEIGHT_MIN <= new_value <= WEIGHT_MAX:
                    continue
                count += 1
                top = recommend(context, _with_weight(rules, method_key, factor, level, new_value))
                if top.best.key != baseline:
                    flips.append(Flip(method_key, factor, level, delta, top.best.key))
    return SensitivityResult(
        name=name, top=baseline, step=step, perturbations=count, flips=tuple(flips)
    )


def format_checks_markdown(checks: list[ExpectationCheck]) -> str:
    lines = [
        "| Scenario | Top recommendation | Margin over 2nd | Expected | Agrees | Notes |",
        "|---|---|---|---|---|---|",
    ]
    for check in checks:
        notes = "; ".join(check.problems) if check.problems else "--"
        lines.append(
            f"| {check.name} | {check.top} ({check.top_score}) | {check.margin} "
            f"(vs {check.runner_up}) | {', '.join(check.acceptable_top)} | "
            f"{'yes' if check.agrees else 'NO'} | {notes} |"
        )
    agreed = sum(check.agrees for check in checks)
    lines += ["", f"Agreement: {agreed} of {len(checks)} scenarios."]
    return "\n".join(lines)


def format_sensitivity_markdown(results: list[SensitivityResult]) -> str:
    step = results[0].step if results else 1
    lines = [
        f"Each relevant weight changed by +/-{step}, one at a time.",
        "",
        "| Scenario | Top | Single-weight changes | Changes that alter the top | Share |",
        "|---|---|---|---|---|",
    ]
    for result in results:
        lines.append(
            f"| {result.name} | {result.top} | {result.perturbations} | "
            f"{len(result.flips)} | {result.flip_share:.0%} |"
        )
    if any(result.flips for result in results):
        lines += ["", "Changes that alter the top recommendation:", ""]
        for result in results:
            for flip in result.flips:
                lines.append(
                    f"- {result.name}: {flip.methodology}.{flip.factor}={flip.level} "
                    f"{flip.delta:+d} -> {flip.new_top}"
                )
    return "\n".join(lines)
