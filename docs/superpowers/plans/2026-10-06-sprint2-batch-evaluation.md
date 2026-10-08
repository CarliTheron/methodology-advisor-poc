# Sprint 2: Batch Evaluation, Distributed-Team Factor, Markdown Export — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Sprint 2 of the methodology-advisor PoC: US-07 (batch evaluation from a
file), C1 (add a sixth context factor, `distributed_team`), and C2 (Markdown export of a
recommendation), each with real tests and CI runs so Sprint 2 generates its own authentic
git/CI history.

**Architecture:** No new layers. C1 extends the existing `models.py` → `rules.py` →
`engine.py` pipeline with one more factor, which `cli.py` already propagates generically
through `contributions`. C2 adds one more output formatter to `cli.py`, following the
existing `format_text` / `format_json` pattern. US-07 adds one new module,
`src/advisor/batch.py`, that wraps the existing `recommend()` in a loop over scenarios
loaded from a JSON file, plus a new `evaluate` CLI subcommand.

**Tech Stack:** Python 3.10+, pytest/pytest-cov, ruff, argparse (stdlib) — no new
dependencies.

---

## Do not start this plan until Sprint 2 has actually been planned

This plan must not be executed while Sprint 1 is still the active sprint (currently
2026-10-06 to 2026-10-12, 0/6 stories done). Running Sprint 2 code inside Sprint 1's
window would make the git history misrepresent which sprint the work happened in, which
undermines the exact evidence the report cites. Before Task 1:

1. Hold the Sprint 1 review (`process/reviews/sprint-1.md` from the template) and confirm
   its outcome.
2. Set real Sprint 2 dates in `process/sprints.json` (`"start"` to the actual day you
   begin, `"end"` to the actual day one week later). Leave `"completed"` empty.
3. In `process/backlog.md`, change the status of US-07, C1, C2 from `todo` to
   `in progress`.
4. Commit that planning update by itself, e.g.
   `git commit -m "Sprint 2: planning — batch evaluation, distributed-team factor, markdown export"`.

Only then start Task 1.

---

## File structure

| File | Change |
|---|---|
| `src/advisor/models.py` | Add `YesNo` enum and `distributed_team` field (C1) |
| `config/rules.json` | Add `distributed_team` factor, weights for all 5 methodologies, one caveat (C1) |
| `src/advisor/cli.py` | Add `--distributed-team` arg (C1); add `markdown` format + `--output` (C2); add `evaluate` subcommand (US-07) |
| `src/advisor/batch.py` | **New.** Scenario loading and batch evaluation (US-07) |
| `tests/conftest.py` | Add `distributed_team` to the two fixtures |
| `tests/test_models.py` | Cover `YesNo` / `distributed_team` |
| `tests/test_rules.py` | Rename the "new factor" placeholder away from `distributed_team` (it's now real) |
| `tests/test_engine.py` | Same rename; add `distributed_team` to inline contexts |
| `tests/test_cli.py` | Add `--distributed-team` to `BASE_ARGS`; cover markdown/output/evaluate |
| `tests/test_batch.py` | **New.** Unit tests for `batch.py` |
| `README.md` | Document the sixth factor and the `evaluate` command (chore) |
| `process/changes.json` | Log C1 and C2 with real timestamps (chore) |

---

### Task 1: `distributed_team` factor — domain model (C1)

**Files:**
- Modify: `src/advisor/models.py`
- Modify: `tests/conftest.py`
- Modify: `tests/test_models.py`

- [ ] **Step 1: Write the failing tests**

Replace the top of `tests/test_models.py` (imports and `make()` helper) with:

```python
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
```

Update `test_factor_values_cover_all_factors` to expect the new key:

```python
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
```

Add a new parametrized test directly below it:

```python
@pytest.mark.parametrize(("flag", "value"), [(YesNo.NO, "no"), (YesNo.YES, "yes")])
def test_distributed_team_factor_value(flag, value):
    assert make(distributed_team=flag).factor_values()["distributed_team"] == value
```

Add a plain `"distributed_team": "yes",` entry to the dict literals in
`test_from_dict_builds_context`, `test_from_dict_reports_missing_fields`,
`test_from_dict_rejects_unknown_level`, and `test_from_dict_preserves_context_error`. For
example, `test_from_dict_builds_context` becomes:

```python
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
```

Apply the same single added line (`"distributed_team": "yes",`) to the other three
dict literals, keeping every other line unchanged — this keeps
`test_from_dict_reports_missing_fields` isolated to testing a missing `team_size` only.

Add one more test at the end of the file:

```python
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
```

Update `tests/conftest.py` fixtures to pass the new required field:

```python
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
```

Add `YesNo` to the `advisor.models` import at the top of `tests/conftest.py`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_models.py -v`
Expected: FAIL — `ImportError: cannot import name 'YesNo' from 'advisor.models'`

- [ ] **Step 3: Implement `YesNo` and the `distributed_team` field**

In `src/advisor/models.py`, add the enum directly after the `Regulation` class (after
line 27):

```python
class YesNo(str, Enum):
    """Binary yes/no level, used for the distributed_team factor."""

    NO = "no"
    YES = "yes"
```

Add the field to `ProjectContext`, directly after `team_maturity: Level`:

```python
    distributed_team: YesNo
```

In `factor_values()`, add the new key after `team_maturity`:

```python
            "team_maturity": self.team_maturity.value,
            "distributed_team": self.distributed_team.value,
```

In `from_dict()`, add `"distributed_team"` to the `required` tuple and add the field to
the `cls(...)` call:

```python
        required = (
            "requirement_volatility",
            "team_size",
            "regulation",
            "release_frequency",
            "team_maturity",
            "distributed_team",
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
                distributed_team=YesNo(data["distributed_team"]),
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_models.py -v`
Expected: PASS (all tests in the file)

- [ ] **Step 5: Commit**

```bash
git add src/advisor/models.py tests/conftest.py tests/test_models.py
git commit -m "C1: add distributed_team factor to the context model"
```

---

### Task 2: `distributed_team` factor — rules data (C1)

**Files:**
- Modify: `config/rules.json`
- Modify: `tests/test_rules.py`
- Modify: `tests/test_engine.py`

The existing test suite already uses `distributed_team` as its example of a *hypothetical*
unadded factor (in `test_new_factor_requires_weights_for_every_methodology` and
`test_unknown_factor_in_rules_is_rejected`). Once it's a real factor, those two tests must
switch to a different placeholder name — `release_automation` — so they keep testing "a
factor the rules/model don't support," not the one we just added.

- [ ] **Step 1: Update the two tests that use `distributed_team` as a placeholder**

In `tests/test_rules.py`, change `test_new_factor_requires_weights_for_every_methodology`:

```python
def test_new_factor_requires_weights_for_every_methodology(rules_data):
    """A requirement change that adds a factor must be completed for all methodologies."""
    rules_data["factors"]["release_automation"] = ["no", "yes"]
    errors = validate_rules(rules_data)
    assert len(errors) == len(rules_data["methodologies"])
```

In `tests/test_engine.py`, change `test_unknown_factor_in_rules_is_rejected`:

```python
def test_unknown_factor_in_rules_is_rejected(rules_data, startup_context):
    rules_data["factors"]["release_automation"] = ["no", "yes"]
    for method in rules_data["methodologies"].values():
        method["weights"]["release_automation"] = {"no": 0, "yes": 0}
    with pytest.raises(EngineError, match="release_automation"):
        recommend(startup_context, parse_rules(rules_data))
```

- [ ] **Step 2: Run the rules and engine tests to verify they still pass against the current (pre-change) rules.json**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_rules.py tests/test_engine.py -v`
Expected: PASS — this is a rename, not a behavior change, so it should be green before you
touch `rules.json`.

- [ ] **Step 3: Add `distributed_team` to `config/rules.json`**

Add to `"factors"` (after `"team_maturity"`):

```json
    "team_maturity": ["low", "medium", "high"],
    "distributed_team": ["no", "yes"]
```

Add a `"distributed_team"` entry to **every** methodology's `"weights"` object:

```json
        "team_maturity": {"low": 1, "medium": 0, "high": -1},
        "distributed_team": {"no": 0, "yes": 1}
```
for `plan_driven`;

```json
        "team_maturity": {"low": -2, "medium": 1, "high": 2},
        "distributed_team": {"no": 1, "yes": -1}
```
for `scrum`;

```json
        "team_maturity": {"low": -1, "medium": 1, "high": 2},
        "distributed_team": {"no": 0, "yes": 1}
```
for `kanban`;

```json
        "team_maturity": {"low": -3, "medium": 0, "high": 3},
        "distributed_team": {"no": 0, "yes": 1}
```
for `agile_devops`;

```json
        "team_maturity": {"low": 1, "medium": 1, "high": 0},
        "distributed_team": {"no": 0, "yes": 1}
```
for `hybrid`.

Rationale (consistent with the file's existing `"note"` that weights are provisional
pending Chapter 4 recalibration): a distributed team adds coordination overhead that
Scrum's tight synchronous ceremonies absorb worst (-1 when distributed); plan-driven,
Kanban, DevOps and hybrid all tolerate it adequately given their documentation, flow-based,
automation-based or governance-based coordination mechanisms respectively (+1 when
distributed, 0 when co-located).

Add a fifth caveat to `"caveats"`:

```json
    {
      "when": {"distributed_team": "yes"},
      "applies_to": ["scrum"],
      "message": "Distributed team: invest in strong asynchronous communication and documentation to offset reduced face-to-face coordination (Boehm, 2002)."
    }
```

- [ ] **Step 4: Run `validate-rules` and the full test suite**

Run:
```bash
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m advisor validate-rules
.\.venv\Scripts\python.exe -m pytest -v
```
Expected: `Rules OK: version 1.0.0, 6 factors, 5 methodologies, 5 caveats`, and all tests
pass except the two inline-context tests in `tests/test_engine.py` touched in Task 3
below (they still construct `ProjectContext` without `distributed_team` and will now fail
with a `TypeError: missing 1 required positional argument`).

- [ ] **Step 5: Commit**

```bash
git add config/rules.json tests/test_rules.py tests/test_engine.py
git commit -m "C1: add distributed_team weights and caveat to config/rules.json"
```

---

### Task 3: Fix remaining inline contexts in `test_engine.py` (C1)

**Files:**
- Modify: `tests/test_engine.py`

- [ ] **Step 1: Add `distributed_team` to the three inline-constructed contexts**

`test_large_moderately_regulated_team_gets_hybrid`:

```python
def test_large_moderately_regulated_team_gets_hybrid(rules):
    context = ProjectContext(
        requirement_volatility=Level.MEDIUM,
        team_size=60,
        regulation=Regulation.MODERATE,
        release_frequency=Level.MEDIUM,
        team_maturity=Level.MEDIUM,
        distributed_team=YesNo.NO,
    )
    assert recommend(context, rules).best.key == "hybrid"
```

`test_high_maturity_shifts_towards_devops`:

```python
def test_high_maturity_shifts_towards_devops(startup_context, rules):
    mature = ProjectContext(
        requirement_volatility=startup_context.requirement_volatility,
        team_size=startup_context.team_size,
        regulation=startup_context.regulation,
        release_frequency=startup_context.release_frequency,
        team_maturity=Level.HIGH,
        distributed_team=startup_context.distributed_team,
    )
    assert recommend(mature, rules).best.key == "agile_devops"
```

`test_caveat_is_reported_for_matching_context`:

```python
def test_caveat_is_reported_for_matching_context(rules):
    context = ProjectContext(
        requirement_volatility=Level.HIGH,
        team_size=5,
        regulation=Regulation.NONE,
        release_frequency=Level.HIGH,
        team_maturity=Level.LOW,
        distributed_team=YesNo.NO,
    )
    result = recommend(context, rules)
    assert result.best.key in {"scrum", "kanban", "agile_devops"}
    assert any("maturity is low" in message for message in result.caveats)
```

Add `YesNo` to the `advisor.models` import at the top of `tests/test_engine.py`.

- [ ] **Step 2: Run the full suite and check coverage**

Run: `.\.venv\Scripts\python.exe -m pytest --cov --cov-fail-under=90`
Expected: all tests pass, coverage still at or above 90% (should still be 100%, since the
only new code is the `YesNo` branch exercised by Task 1's tests).

- [ ] **Step 3: Lint and format**

Run:
```bash
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format .
```
Expected: no errors; `ruff format` may reformat the files you just edited — re-run
`pytest` afterwards if it changes anything.

- [ ] **Step 4: Commit**

```bash
git add tests/test_engine.py
git commit -m "C1: cover distributed_team in the remaining engine tests"
```

---

### Task 4: `distributed_team` on the CLI (C1)

**Files:**
- Modify: `src/advisor/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

In `tests/test_cli.py`, add `--distributed-team` to `BASE_ARGS`:

```python
BASE_ARGS = [
    "recommend",
    "--volatility",
    "high",
    "--team-size",
    "6",
    "--regulation",
    "none",
    "--release-frequency",
    "high",
    "--maturity",
    "medium",
    "--distributed-team",
    "no",
]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -v`
Expected: FAIL — `argparse` exits with "unrecognized arguments: --distributed-team no"
(the existing tests call `cli.main(BASE_ARGS)`, so this surfaces as a `SystemExit`/`== 2`
mismatch depending on the test).

- [ ] **Step 3: Add the CLI argument**

In `src/advisor/cli.py`, add the import and argument. Change:

```python
from advisor.models import ContextError, Level, ProjectContext, Regulation
```
to:
```python
from advisor.models import ContextError, Level, ProjectContext, Regulation, YesNo
```

In `build_parser()`, after the `--maturity` argument on the `recommend` subparser, add:

```python
    rec.add_argument(
        "--distributed-team",
        required=True,
        choices=[flag.value for flag in YesNo],
        help="is the team geographically distributed",
    )
```

In `main()`, add the field to the `ProjectContext.from_dict(...)` call:

```python
        context = ProjectContext.from_dict(
            {
                "requirement_volatility": args.volatility,
                "team_size": args.team_size,
                "regulation": args.regulation,
                "release_frequency": args.release_frequency,
                "team_maturity": args.maturity,
                "distributed_team": args.distributed_team,
            }
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/advisor/cli.py tests/test_cli.py
git commit -m "C1: expose distributed_team on the recommend command"
```

---

### Task 5: Markdown export (C2)

**Files:**
- Modify: `src/advisor/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_cli.py`:

```python
def test_recommend_markdown_output(capsys):
    assert cli.main([*BASE_ARGS, "--format", "markdown"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# Methodology recommendation:")
    assert "## Ranking" in out
    assert "| Rank | Methodology | Score |" in out


def test_recommend_writes_markdown_to_file(tmp_path):
    output = tmp_path / "report.md"
    assert cli.main([*BASE_ARGS, "--format", "markdown", "--output", str(output)]) == 0
    content = output.read_text(encoding="utf-8")
    assert content.startswith("# Methodology recommendation:")


def test_recommend_text_output_can_be_written_to_file(tmp_path):
    output = tmp_path / "report.txt"
    assert cli.main([*BASE_ARGS, "--output", str(output)]) == 0
    assert output.read_text(encoding="utf-8").startswith("Recommended: ")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -v -k markdown`
Expected: FAIL — `argparse` rejects `--format markdown` (not in current choices) and
`--output` is unrecognized.

- [ ] **Step 3: Implement `format_markdown` and `--output`**

In `build_parser()`, change the `recommend` subparser's `--format` line and add
`--output` directly after it:

```python
    rec.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    rec.add_argument(
        "--output",
        type=Path,
        default=None,
        help="write the report to this file instead of stdout",
    )
```

Add a new formatter function after `format_json`:

```python
def format_markdown(result: Recommendation) -> str:
    lines = [f"# Methodology recommendation: {result.best.label}", ""]
    lines.append(f"**Score:** {result.best.total}  ")
    lines.append(f"**Rules version:** {result.rules_version}")
    lines.append("")
    lines.append("## Ranking")
    lines.append("")
    lines.append("| Rank | Methodology | Score |")
    lines.append("|---|---|---|")
    for position, score in enumerate(result.ranking, start=1):
        lines.append(f"| {position} | {score.label} | {score.total} |")
    lines.append("")
    lines.append(f"## Factor contributions for {result.best.label}")
    lines.append("")
    lines.append("| Factor | Contribution |")
    lines.append("|---|---|")
    for factor, weight in result.best.contributions.items():
        lines.append(f"| {factor} | {weight:+d} |")
    if result.caveats:
        lines.append("")
        lines.append("## Caveats")
        lines.append("")
        lines.extend(f"- {message}" for message in result.caveats)
    return "\n".join(lines) + "\n"
```

In `main()`, replace the final two lines of the `recommend` path —

```python
    print(format_json(result) if args.format == "json" else format_text(result))
    return 0
```

— with:

```python
    if args.format == "json":
        content = format_json(result)
    elif args.format == "markdown":
        content = format_markdown(result)
    else:
        content = format_text(result)

    if args.output:
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content)
    return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/advisor/cli.py tests/test_cli.py
git commit -m "C2: add markdown export and --output for the recommend command"
```

---

### Task 6: Batch evaluation core (US-07)

**Files:**
- Create: `src/advisor/batch.py`
- Create: `tests/test_batch.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_batch.py`:

```python
import json

import pytest

from advisor.batch import ScenarioError, evaluate_scenarios, load_scenarios
from advisor.rules import load_rules


@pytest.fixture
def rules(rules_path):
    return load_rules(rules_path)


def test_load_scenarios_reads_json_array(tmp_path):
    path = tmp_path / "scenarios.json"
    path.write_text(json.dumps([{"name": "a", "team_size": 5}]), encoding="utf-8")
    assert load_scenarios(path) == [{"name": "a", "team_size": 5}]


def test_load_scenarios_missing_file(tmp_path):
    with pytest.raises(ScenarioError, match="not found"):
        load_scenarios(tmp_path / "missing.json")


def test_load_scenarios_invalid_json(tmp_path):
    path = tmp_path / "scenarios.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ScenarioError, match="not valid JSON"):
        load_scenarios(path)


def test_load_scenarios_rejects_non_array(tmp_path):
    path = tmp_path / "scenarios.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ScenarioError, match="non-empty JSON array"):
        load_scenarios(path)


def test_load_scenarios_rejects_non_object_entries(tmp_path):
    path = tmp_path / "scenarios.json"
    path.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ScenarioError, match="scenario 1 must be a JSON object"):
        load_scenarios(path)


def test_evaluate_scenarios_returns_one_result_per_entry(rules):
    scenarios = [
        {
            "name": "Startup",
            "requirement_volatility": "high",
            "team_size": 6,
            "regulation": "none",
            "release_frequency": "high",
            "team_maturity": "medium",
            "distributed_team": "yes",
        },
        {
            "name": "Enterprise",
            "requirement_volatility": "low",
            "team_size": 80,
            "regulation": "strict",
            "release_frequency": "low",
            "team_maturity": "low",
            "distributed_team": "no",
        },
    ]
    results = evaluate_scenarios(scenarios, rules)
    assert [r.name for r in results] == ["Startup", "Enterprise"]
    assert results[0].recommendation is not None
    assert results[0].error is None
    assert results[1].recommendation.best.key == "plan_driven"


def test_evaluate_scenarios_captures_invalid_context(rules):
    results = evaluate_scenarios([{"name": "Broken", "team_size": 6}], rules)
    assert results[0].recommendation is None
    assert "missing context fields" in results[0].error


def test_evaluate_scenarios_names_unlabelled_entries_by_position(rules):
    scenarios = [
        {
            "requirement_volatility": "high",
            "team_size": 6,
            "regulation": "none",
            "release_frequency": "high",
            "team_maturity": "medium",
            "distributed_team": "yes",
        }
    ]
    results = evaluate_scenarios(scenarios, rules)
    assert results[0].name == "scenario 1"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_batch.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'advisor.batch'`

- [ ] **Step 3: Implement `src/advisor/batch.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_batch.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/advisor/batch.py tests/test_batch.py
git commit -m "US-07: add batch scenario loading and evaluation"
```

---

### Task 7: `evaluate` CLI command (US-07)

**Files:**
- Modify: `src/advisor/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_cli.py`:

```python
def test_evaluate_batch_text_output(tmp_path, capsys):
    scenarios = tmp_path / "scenarios.json"
    scenarios.write_text(
        json.dumps(
            [
                {
                    "name": "Startup",
                    "requirement_volatility": "high",
                    "team_size": 6,
                    "regulation": "none",
                    "release_frequency": "high",
                    "team_maturity": "medium",
                    "distributed_team": "yes",
                }
            ]
        ),
        encoding="utf-8",
    )
    assert cli.main(["evaluate", "--input", str(scenarios)]) == 0
    out = capsys.readouterr().out
    assert "=== Startup ===" in out
    assert "Recommended:" in out


def test_evaluate_batch_json_output(tmp_path, capsys):
    scenarios = tmp_path / "scenarios.json"
    scenarios.write_text(
        json.dumps(
            [
                {
                    "requirement_volatility": "low",
                    "team_size": 80,
                    "regulation": "strict",
                    "release_frequency": "low",
                    "team_maturity": "low",
                    "distributed_team": "no",
                }
            ]
        ),
        encoding="utf-8",
    )
    assert cli.main(["evaluate", "--input", str(scenarios), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["recommended"] == "plan_driven"


def test_evaluate_reports_scenario_errors(tmp_path, capsys):
    scenarios = tmp_path / "scenarios.json"
    scenarios.write_text(json.dumps([{"name": "Broken"}]), encoding="utf-8")
    assert cli.main(["evaluate", "--input", str(scenarios)]) == 0
    assert "Error:" in capsys.readouterr().out


def test_evaluate_missing_input_file(tmp_path, capsys):
    assert cli.main(["evaluate", "--input", str(tmp_path / "missing.json")]) == 1
    assert "not found" in capsys.readouterr().err
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -v -k evaluate`
Expected: FAIL — `argparse` rejects the unrecognized `evaluate` command.

- [ ] **Step 3: Wire `evaluate` into `cli.py`**

Add the import:

```python
from advisor.batch import ScenarioError, ScenarioResult, evaluate_scenarios, load_scenarios
```

In `build_parser()`, after the `validate-rules` subparser line, add:

```python
    ev = sub.add_parser("evaluate", help="evaluate a batch of project scenarios from a file")
    ev.add_argument("--input", required=True, type=Path, help="path to a JSON array of scenarios")
    ev.add_argument("--format", choices=["text", "json"], default="text")
```

Add two formatter functions after `format_markdown`:

```python
def format_batch_text(results: list[ScenarioResult]) -> str:
    lines = []
    for result in results:
        lines.append(f"=== {result.name} ===")
        if result.error:
            lines.append(f"  Error: {result.error}")
        else:
            lines.append(f"  Recommended: {result.recommendation.best.label}")
            for position, score in enumerate(result.recommendation.ranking, start=1):
                lines.append(f"    {position}. {score.label:<40} {score.total:>3}")
        lines.append("")
    return "\n".join(lines).rstrip()


def format_batch_json(results: list[ScenarioResult]) -> str:
    return json.dumps(
        [
            {
                "name": result.name,
                "error": result.error,
                "recommended": result.recommendation.best.key if result.recommendation else None,
                "ranking": (
                    [
                        {
                            "key": score.key,
                            "label": score.label,
                            "total": score.total,
                            "contributions": score.contributions,
                        }
                        for score in result.recommendation.ranking
                    ]
                    if result.recommendation
                    else []
                ),
            }
            for result in results
        ],
        indent=2,
    )
```

In `main()`, insert a new branch directly after the existing `validate-rules` branch
(before the `try: context = ProjectContext.from_dict(...)` block):

```python
    if args.command == "evaluate":
        try:
            scenarios = load_scenarios(args.input)
        except ScenarioError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        results = evaluate_scenarios(scenarios, rules)
        print(format_batch_json(results) if args.format == "json" else format_batch_text(results))
        return 0
```

- [ ] **Step 4: Run the full suite**

Run: `.\.venv\Scripts\python.exe -m pytest --cov --cov-fail-under=90`
Expected: all tests pass, coverage ≥ 90%.

- [ ] **Step 5: Lint, format, validate rules**

```bash
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format .
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m advisor validate-rules
```

- [ ] **Step 6: Commit**

```bash
git add src/advisor/cli.py tests/test_cli.py
git commit -m "US-07: add the evaluate batch command to the CLI"
```

---

### Task 8: Documentation and change log (chore)

**Files:**
- Modify: `README.md`
- Modify: `process/changes.json`
- Modify: `process/backlog.md`

- [ ] **Step 1: Update the factor table in `README.md`**

Add a row after "Team agile maturity":

```markdown
| Distributed team | no, yes |
```

Update the `recommend` example to include the new flag:

```bash
advisor recommend --volatility high --team-size 6 --regulation none \
    --release-frequency high --maturity medium --distributed-team no
```

Add a line documenting the new command under "Other commands":

```bash
advisor evaluate --input scenarios.json          # batch evaluation, one result per scenario
advisor recommend ... --format markdown --output report.md   # write a Markdown report
```

- [ ] **Step 2: Log C1 and C2 in `process/changes.json`**

This file's schema requires real timestamps. Run `date -Iseconds` (or, on Windows
PowerShell, `Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"`) at the moment you actually
finished each change and use that output — do not invent a time. Append two entries to
the `"changes"` array, for example:

```json
{
  "id": "C1",
  "description": "Add a distributed-team factor",
  "sprint": 2,
  "requested_by": "supervisor",
  "requested_at": "<timestamp from Sprint 1 review or backlog grooming>",
  "released_at": "<timestamp you tag v0.2.0>",
  "release_tag": "v0.2.0",
  "effort_hours": "<your real time log>",
  "caused_failure": false,
  "notes": ""
}
```

Add a second entry with `"id": "C2"` the same way. Leave `released_at` and
`release_tag` unset until the actual tag exists; `tools/collect_metrics.py` reports a
missing `released_at` as `--`, which is correct until that happens.

- [ ] **Step 3: Update `process/backlog.md` statuses as work actually completes**

Change US-07 from `in progress` to `done` only once Task 7 is merged and its tests pass
in CI — not before. Same for C1 (after Task 4) and C2 (after Task 5).

- [ ] **Step 4: Commit**

```bash
git add README.md process/changes.json process/backlog.md
git commit -m "Sprint 2: update docs and change log for US-07, C1, C2"
```

---

## After all tasks

1. Push: `git push origin main`
2. Confirm CI is green: `https://github.com/CarliTheron/methodology-advisor-poc/actions`
3. Re-run `tools/collect_metrics.py` to get Sprint 2's real numbers for Chapter 5 — do not
   reuse Sprint 1's numbers.
4. Hold the Sprint 2 review, fill in `process/reviews/sprint-2.md` from the template, and
   only then tag `v0.2.0` yourself.

## Self-review notes

- **Spec coverage:** US-07 (`evaluate --input`, Task 6/7) ✓. C1 (new factor in model,
  rules, CLI, forced validation on every methodology, Task 1/2/3/4) ✓. C2 (`--format
  markdown` and `--output FILE` with ranking/contributions/caveats, Task 5) ✓.
- **Weight-table arithmetic:** the `distributed_team` weights and the two fixtures'
  assigned values (`startup_context` = yes, `regulated_context` = no, both inline test
  contexts = no) were checked by hand against every existing `test_engine.py` assertion
  so none of them flip which methodology wins. If a future weight recalibration (US-08)
  changes this, the affected test will fail loudly and should be fixed then, not silently
  loosened.
- **Placeholder rename:** `distributed_team` is used in two existing tests as a stand-in
  for "a factor that doesn't exist yet." Task 2 renames those to `release_automation`
  before Task 2 adds the real factor, so no test silently stops testing what it claims to.
