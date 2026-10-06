"""Command-line interface.

Examples::

    python -m advisor recommend --volatility high --team-size 6 \\
        --regulation none --release-frequency high --maturity medium

    python -m advisor validate-rules
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from advisor import __version__
from advisor.engine import EngineError, Recommendation, recommend
from advisor.models import ContextError, Level, ProjectContext, Regulation
from advisor.rules import RulesError, load_rules

DEFAULT_RULES = Path(__file__).resolve().parents[2] / "config" / "rules.json"


def default_rules_path() -> Path:
    """Rules path from the ADVISOR_RULES environment variable, else the repo default."""
    return Path(os.environ.get("ADVISOR_RULES", DEFAULT_RULES))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="advisor",
        description="Context-based software development methodology advisor.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--rules",
        type=Path,
        default=None,
        help="path to the rules file (default: config/rules.json)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    levels = [level.value for level in Level]
    rec = sub.add_parser("recommend", help="recommend a methodology for a project context")
    rec.add_argument("--volatility", required=True, choices=levels, help="requirement volatility")
    rec.add_argument("--team-size", required=True, type=int, help="number of people on the team")
    rec.add_argument("--regulation", required=True, choices=[reg.value for reg in Regulation])
    rec.add_argument("--release-frequency", required=True, choices=levels)
    rec.add_argument("--maturity", required=True, choices=levels, help="team agile maturity")
    rec.add_argument("--format", choices=["text", "json"], default="text")

    sub.add_parser("validate-rules", help="validate the rules file (used as a CI gate)")
    return parser


def format_text(result: Recommendation) -> str:
    lines = [f"Recommended: {result.best.label} (score {result.best.total})", ""]
    lines.append("Ranking:")
    for position, score in enumerate(result.ranking, start=1):
        lines.append(f"  {position}. {score.label:<40} {score.total:>3}")
    lines.append("")
    lines.append(f"Factor contributions for {result.best.label}:")
    for factor, weight in result.best.contributions.items():
        lines.append(f"  {factor:<24} {weight:+d}")
    if result.caveats:
        lines.append("")
        lines.append("Caveats:")
        lines.extend(f"  - {message}" for message in result.caveats)
    lines.append("")
    lines.append(f"Rules version: {result.rules_version}")
    return "\n".join(lines)


def format_json(result: Recommendation) -> str:
    return json.dumps(
        {
            "recommended": result.best.key,
            "rules_version": result.rules_version,
            "ranking": [
                {
                    "key": score.key,
                    "label": score.label,
                    "total": score.total,
                    "contributions": score.contributions,
                }
                for score in result.ranking
            ],
            "caveats": list(result.caveats),
        },
        indent=2,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rules_path = args.rules or default_rules_path()

    try:
        rules = load_rules(rules_path)
    except RulesError as exc:
        print(f"Rules validation failed for {rules_path}:", file=sys.stderr)
        for error in exc.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if args.command == "validate-rules":
        print(
            f"Rules OK: version {rules.version}, {len(rules.factors)} factors, "
            f"{len(rules.methodologies)} methodologies, {len(rules.caveats)} caveats"
        )
        return 0

    try:
        context = ProjectContext.from_dict(
            {
                "requirement_volatility": args.volatility,
                "team_size": args.team_size,
                "regulation": args.regulation,
                "release_frequency": args.release_frequency,
                "team_maturity": args.maturity,
            }
        )
        result = recommend(context, rules)
    except (ContextError, EngineError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(format_json(result) if args.format == "json" else format_text(result))
    return 0
