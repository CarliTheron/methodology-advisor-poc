# Sprint 3: Evidence-Sourced Calibration, Close-Call Flag, Documentation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Sprint 3 of the methodology-advisor PoC: C3 (a configurable "close call"
flag when the top two scores are within a margin), US-08 (trace every methodology's weights
to the specific Chapter 4 finding that supports them, bumping `config/rules.json` to
1.1.0), and US-09 (documentation covering installation, commands and the meaning of scores).

**Architecture:** C3 adds one new top-level field (`close_call_margin`) to the rules schema,
one new computed property on `engine.Recommendation`, and one new output block to each of
`cli.py`'s three `recommend` formatters — no new files, same layering as every prior factor
addition. US-08 is a content-only edit to `config/rules.json` (rationale/sources/caveat text
and the version string) — **no weight values change**, because reviewing Sprint 1's initial
weights against Chapter 4 Table 4.5 found them already directionally consistent with the
evidence for four of five original factors; what was missing was traceability, not different
numbers. US-09 is a documentation-only edit to `README.md`, done last so it can describe the
finished C3/US-08 behavior accurately rather than guessing ahead of it.

**Tech Stack:** Same as Sprint 1/2 — Python 3.10+, pytest/pytest-cov, ruff, argparse, no new
dependencies.

**Evidence basis:** `Theron_DST481_Chapter4_Findings.pdf` (Chapter 4, "Research Findings"),
specifically Table 4.5 ("Preliminary context-based selection framework") and the Finding IDs
it cites (F1.1, F1.2, F2.1, F2.2, F3.2, F4.1, F4.3). Citation keys used below
(`Boehm2002`, `Serrador2015`, `Kuhrmann2017`, `Forsgren2018`, `Dikert2016`, `Edison2022`,
`SchwaberSutherland2020`, `Anderson2010`, `HumbleFarley2010`) match the `.bib` keys already
used in `config/rules.json` and the `DST481_Literature_Review_Workbook.pdf` Extraction sheet.

---

## Do not start this plan until Sprint 3 has actually been planned

Do not run this plan while Sprint 2 is still the active, unreviewed sprint. Before Task 1:

1. Hold the Sprint 2 review (`process/reviews/sprint-2.md` from the template).
2. Set real Sprint 3 dates in `process/sprints.json` (`"start"` to the actual day you begin,
   `"end"` to the actual day one week later). Leave `"completed"` empty.
3. In `process/backlog.md`, change the status of US-08, US-09, C3 from `todo` to
   `in progress`.
4. Commit that planning update by itself, e.g.
   `git commit -m "Sprint 3: planning -- evidence-sourced calibration, close-call flag, docs"`.

Only then start Task 1.

---

## File structure

| File | Change |
|---|---|
| `src/advisor/rules.py` | Add `close_call_margin` to schema validation, `RuleSet`, `parse_rules` (C3) |
| `config/rules.json` | Add `close_call_margin: 2` (C3); update `version`, `note`, every methodology's `rationale`/`sources`, four caveat messages (US-08) |
| `src/advisor/engine.py` | Add `Recommendation.close_call_margin`, `.close_call`, `.is_close_call` (C3) |
| `src/advisor/cli.py` | Add close-call output to `format_text`, `format_json`, `format_markdown` (C3) |
| `tests/test_rules.py` | Cover `close_call_margin` validation; bump expected version (C3, US-08) |
| `tests/test_engine.py` | Cover close-call boundary behavior (C3) |
| `tests/test_cli.py` | Cover close-call output; bump expected version string (C3, US-08) |
| `README.md` | Score-interpretation section, close-call docs, refreshed example output, factor-count fix (US-09) |

---

### Task 1: `close_call_margin` schema (C3)

**Files:**
- Modify: `src/advisor/rules.py`
- Modify: `config/rules.json`
- Modify: `tests/test_rules.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_rules.py`, after `test_weights_must_be_bounded_integers`:

```python
@pytest.mark.parametrize("bad_margin", [-1, 1.5, True, "2", None])
def test_close_call_margin_must_be_a_non_negative_integer(rules_data, bad_margin):
    rules_data["close_call_margin"] = bad_margin
    assert "'close_call_margin' must be a non-negative integer" in validate_rules(rules_data)


def test_missing_close_call_margin_is_reported(rules_data):
    del rules_data["close_call_margin"]
    assert "'close_call_margin' must be a non-negative integer" in validate_rules(rules_data)
```

Change `test_load_rules_parses_shipped_file` by adding one line after the existing
`assert len(rules.factors) == 6`:

```python
    assert rules.close_call_margin == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_rules.py -v`
Expected: the two new tests FAIL (`'close_call_margin' must be a non-negative integer` not
yet produced by `validate_rules`), and `test_load_rules_parses_shipped_file` FAILS with
`AttributeError: 'RuleSet' object has no attribute 'close_call_margin'`.

- [ ] **Step 3: Add validation to `rules.py`**

In `validate_rules`, directly after the `version` check (after the line
`errors.append("'version' must be a non-empty string")` and before the `factors = data.get("factors")`
line), add:

```python
    margin = data.get("close_call_margin")
    if not _is_int(margin) or margin < 0:
        errors.append("'close_call_margin' must be a non-negative integer")
```

In `RuleSet`, add the new field **before** `caveats` (it has no default, and a
non-default field cannot follow a defaulted one):

```python
@dataclass(frozen=True)
class RuleSet:
    version: str
    factors: dict[str, tuple[str, ...]]
    methodologies: dict[str, Methodology]
    close_call_margin: int
    caveats: tuple[Caveat, ...] = field(default_factory=tuple)
```

In `parse_rules`, add `close_call_margin=data["close_call_margin"],` to the `RuleSet(...)`
call (order doesn't matter for a keyword call):

```python
    return RuleSet(
        version=data["version"],
        factors={name: tuple(levels) for name, levels in data["factors"].items()},
        close_call_margin=data["close_call_margin"],
        methodologies={
            ...
        },
        caveats=tuple(
            ...
        ),
    )
```

- [ ] **Step 4: Add the field to `config/rules.json`**

Add `"close_call_margin": 2,` directly after the `"note"` line (before `"factors"`):

```json
  "note": "...",
  "close_call_margin": 2,
  "factors": {
```

(Leave the `"note"` text itself exactly as it currently reads — Task 4 rewrites it.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_rules.py -v`
Expected: PASS (all tests in the file). NOTE: `tests/test_engine.py` and `tests/test_cli.py`
will now fail with `TypeError: Recommendation.__init__() missing 1 required positional
argument: 'close_call_margin'` once Task 2 starts constructing it — that's expected and
fixed by Task 2, not this task. Confirm only `tests/test_rules.py` and `tests/test_models.py`
are green right now.

- [ ] **Step 6: Commit**

```bash
git add src/advisor/rules.py config/rules.json tests/test_rules.py
git commit -m "C3: add close_call_margin to the rules schema"
```

---

### Task 2: Close-call engine logic (C3)

**Files:**
- Modify: `src/advisor/engine.py`
- Modify: `tests/test_engine.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_engine.py`, after `test_rules_version_is_reported`:

```python
def test_close_call_margin_is_reported(startup_context, rules):
    assert recommend(startup_context, rules).close_call_margin == rules.close_call_margin


def test_close_call_within_margin(rules_data, startup_context):
    rules_data["close_call_margin"] = 2
    for method in rules_data["methodologies"].values():
        for factor_weights in method["weights"].values():
            for level in factor_weights:
                factor_weights[level] = 0
    rules_data["methodologies"]["scrum"]["weights"]["team_size"]["small"] = 3
    rules_data["methodologies"]["kanban"]["weights"]["team_size"]["small"] = 1
    result = recommend(startup_context, parse_rules(rules_data))
    assert result.is_close_call
    assert {score.key for score in result.close_call} == {"scrum", "kanban"}


def test_close_call_outside_margin(rules_data, startup_context):
    rules_data["close_call_margin"] = 1
    for method in rules_data["methodologies"].values():
        for factor_weights in method["weights"].values():
            for level in factor_weights:
                factor_weights[level] = 0
    rules_data["methodologies"]["scrum"]["weights"]["team_size"]["small"] = 3
    rules_data["methodologies"]["kanban"]["weights"]["team_size"]["small"] = 1
    result = recommend(startup_context, parse_rules(rules_data))
    assert not result.is_close_call
    assert result.close_call == (result.ranking[0],)
```

These two tests cover the boundary precisely: the same raw score gap (2 points, scrum vs
kanban) is a close call when `close_call_margin == 2` (included, `<=`) and is not one when
`close_call_margin == 1` (excluded). All other methodologies score 0 in both tests (every
weight zeroed except the one `team_size="small"` entry touched above), so scrum is always
the outright best and the only question being tested is whether kanban counts as "close."

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_engine.py -v`
Expected: FAIL — `TypeError: Recommendation.__init__() missing 1 required positional
argument: 'close_call_margin'` (the fixture-based tests) and `AttributeError:
'Recommendation' object has no attribute 'close_call_margin'` (the new tests), since
`recommend()` doesn't pass it yet.

- [ ] **Step 3: Implement the close-call properties**

In `src/advisor/engine.py`, add the field to `Recommendation` and two properties:

```python
@dataclass(frozen=True)
class Recommendation:
    ranking: tuple[Score, ...]
    caveats: tuple[str, ...]
    rules_version: str
    close_call_margin: int

    @property
    def best(self) -> Score:
        return self.ranking[0]

    @property
    def close_call(self) -> tuple[Score, ...]:
        """Scores within close_call_margin points of the best score, including the best."""
        best_total = self.ranking[0].total
        return tuple(
            score for score in self.ranking if best_total - score.total <= self.close_call_margin
        )

    @property
    def is_close_call(self) -> bool:
        return len(self.close_call) > 1
```

In `recommend()`, change the final `return` statement:

```python
    return Recommendation(
        ranking=ranking,
        caveats=caveats,
        rules_version=rules.version,
        close_call_margin=rules.close_call_margin,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_engine.py -v`
Expected: PASS (all tests in the file). NOTE: `tests/test_cli.py` and `tests/test_batch.py`
will still fail at this point with the same `TypeError`/`AttributeError` pattern, since
nothing outside `engine.py`/`test_engine.py` has changed yet — that's Task 3's job for
`cli.py`. `batch.py` itself needs no change (it only calls `recommend()`, never constructs
`Recommendation` directly), but `tests/test_batch.py` will transiently fail too; do not
touch it — it will pass again once Task 3 lands, since the failure is purely that
`Recommendation` now needs an extra field `recommend()` already supplies.

- [ ] **Step 5: Commit**

```bash
git add src/advisor/engine.py tests/test_engine.py
git commit -m "C3: compute the close-call flag in the recommendation engine"
```

---

### Task 3: Close-call CLI output (C3)

**Files:**
- Modify: `src/advisor/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_cli.py`, after `test_text_output_lists_caveats`:

```python
def test_recommend_text_shows_close_call(capsys):
    assert cli.main(BASE_ARGS) == 0
    assert "Close call:" in capsys.readouterr().out


def test_recommend_json_includes_close_call(capsys):
    assert cli.main([*BASE_ARGS, "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["close_call"]["is_close_call"] is True
    assert "agile_devops" in payload["close_call"]["candidates"]


def test_recommend_markdown_shows_close_call(capsys):
    assert cli.main([*BASE_ARGS, "--format", "markdown"]) == 0
    assert "## Close call" in capsys.readouterr().out


def test_recommend_no_close_call_when_clear_winner(capsys):
    args = [
        "recommend",
        "--volatility",
        "low",
        "--team-size",
        "80",
        "--regulation",
        "strict",
        "--release-frequency",
        "low",
        "--maturity",
        "low",
        "--distributed-team",
        "no",
    ]
    assert cli.main(args) == 0
    out = capsys.readouterr().out
    assert "Close call:" not in out
```

`BASE_ARGS` (volatility high, team-size 6, regulation none, release-frequency high,
maturity medium, distributed-team no) scores Scrum 11 and Agile-with-DevOps 9 against the
real shipped rules — a 2-point gap, exactly at the shipped `close_call_margin: 2`, so it's
a genuine close call. The large/regulated/strict scenario in the fourth test scores
plan_driven 11 and hybrid 8 — a 3-point gap, outside the margin — so it must NOT show a
close call. If these exact numbers don't match what you observe (e.g. because Task 4's
rationale/source edits are mistakenly thought to change scores — they don't, Task 4 is
text-only), stop and report rather than adjusting the margin or the test data yourself.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -v -k close_call`
Expected: FAIL — all four new tests fail (no close-call output exists in any formatter yet).

- [ ] **Step 3: Add close-call output to the three formatters**

In `format_text`, insert a close-call block directly after the ranking loop and before the
existing `lines.append("")` / `"Factor contributions..."` lines:

```python
def format_text(result: Recommendation) -> str:
    lines = [f"Recommended: {result.best.label} (score {result.best.total})", ""]
    lines.append("Ranking:")
    for position, score in enumerate(result.ranking, start=1):
        lines.append(f"  {position}. {score.label:<40} {score.total:>3}")
    if result.is_close_call:
        names = ", ".join(score.label for score in result.close_call)
        lines.append("")
        lines.append(
            f"Close call: {names} are within {result.close_call_margin} point(s) of each other."
        )
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
```

In `format_json`, add a `"close_call"` object between `"ranking"` and `"caveats"`:

```python
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
            "close_call": {
                "is_close_call": result.is_close_call,
                "margin": result.close_call_margin,
                "candidates": (
                    [score.key for score in result.close_call] if result.is_close_call else []
                ),
            },
            "caveats": list(result.caveats),
        },
        indent=2,
    )
```

In `format_markdown`, insert a `## Close call` section directly after the ranking table and
before `## Factor contributions`:

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
    if result.is_close_call:
        names = ", ".join(score.label for score in result.close_call)
        lines.append("")
        lines.append("## Close call")
        lines.append("")
        lines.append(f"{names} are within {result.close_call_margin} point(s) of each other.")
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

Do not change `format_batch_text` or `format_batch_json` — close-call output for the batch
`evaluate` command is out of scope for C3's acceptance criteria (which refer to "the
recommendation", singular).

- [ ] **Step 4: Run the full suite**

Run: `.\.venv\Scripts\python.exe -m pytest --cov --cov-fail-under=90 --cov-report=term-missing`
Expected: all tests pass, coverage still at or above 90% (should be 100%, since every new
branch — `is_close_call` true and false — is hit by the tests above). `tests/test_batch.py`
should be green again now (it only failed transiently because `recommend()` momentarily
required a field `evaluate_scenarios` didn't know about yet — nothing in `batch.py` itself
needed to change).

- [ ] **Step 5: Lint, format, validate rules**

```bash
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format .
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m advisor validate-rules
```

- [ ] **Step 6: Commit**

```bash
git add src/advisor/cli.py tests/test_cli.py
git commit -m "C3: show the close-call flag in text, JSON and Markdown output"
```

---

### Task 4: Evidence-sourced calibration (US-08)

**Files:**
- Modify: `config/rules.json`
- Modify: `tests/test_rules.py`
- Modify: `tests/test_cli.py`

This task changes **text only** — version, `note`, every methodology's `rationale` and
`sources`, and four caveat messages. **No weight numbers change.** Reviewing Sprint 1's
initial weights against Chapter 4 Table 4.5 (the evidence basis listed at the top of this
plan) found them already directionally consistent for `requirement_volatility`, `team_size`,
`release_frequency` and `team_maturity`; `regulation` rests on conceptual evidence only
(Finding 2.2) and is deliberately left unchanged rather than strengthened on weak evidence.
`distributed_team` is outside the five factors Chapter 4 covers (it was added in Sprint 2 as
client requirement C1) and is not touched here.

- [ ] **Step 1: Write the failing tests**

In `tests/test_rules.py`, change the one line in `test_load_rules_parses_shipped_file`:

```python
    assert rules.version == "1.1.0"
```

In `tests/test_cli.py`, change the one line in `test_recommend_text_output`:

```python
    assert "Rules version: 1.1.0" in out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_rules.py tests/test_cli.py -v`
Expected: exactly these two tests FAIL (`AssertionError`, still reading `1.0.0`); nothing
else regresses.

- [ ] **Step 3: Update `config/rules.json`**

Change `"version": "1.0.0"` to `"version": "1.1.0"`.

Change the `"note"` field (the line right after `"version"`) to:

```json
  "note": "Calibrated in Sprint 3 against Chapter 4 findings (Theron, DST481). Weights range from -3 (strongly unsuited) to +3 (strongly suited). Reviewing Sprint 1's initial weights against Chapter 4 Table 4.5 found them already directionally consistent with the evidence for requirement_volatility, team_size, release_frequency and team_maturity, so no weight values were changed; each methodology's rationale and sources now cite the specific findings that support it. The regulation factor rests on conceptual evidence only (Finding 2.2, Boehm 2002), so its weights were deliberately left unchanged rather than strengthened. The distributed_team factor (added in Sprint 2 as requirement change C1) is outside the five factors covered by the Chapter 4 literature review (Figure 2.1) and is not addressed by this calibration.",
```

For each methodology, change only `"rationale"` and `"sources"` (leave every `"weights"`
number exactly as it is):

`plan_driven`:
```json
      "rationale": "Home ground: stable requirements and strict regulation (Table 4.5; Finding 2.2 -- conceptual evidence only, Boehm 2002).",
      "sources": ["Boehm2002"],
```

`scrum`:
```json
      "rationale": "Iterative delivery for small teams facing changing requirements (Table 4.5: volatile requirements and small team favour an iterative method; Findings 1.1, 1.2, 2.1).",
      "sources": ["Boehm2002", "SchwaberSutherland2020", "Serrador2015", "Kuhrmann2017"],
```

`kanban`:
```json
      "rationale": "Continuous flow with work-in-progress limits; suited to unpredictable, steady demand (Table 4.5: volatile requirements and small team favour an iterative method -- Scrum or Kanban; Findings 1.1, 2.1).",
      "sources": ["Anderson2010", "Kuhrmann2017"],
```

`agile_devops`:
```json
      "rationale": "Frequent releases with automated build, test and deployment; demands technical maturity (Table 4.5: frequent releases and a mature team favour Agile with DevOps and delivery measures; Finding 3.2 -- Forsgren et al. 2018).",
      "sources": ["Forsgren2018", "HumbleFarley2010"],
```

`hybrid`:
```json
      "rationale": "Plan-driven governance with iterative delivery inside phases; suited to larger or regulated settings (Table 4.5: a large or multi-team project favours an explicitly defined hybrid or scaled approach with cross-team coordination designed in; Findings 1.1, 4.1, 4.3).",
      "sources": ["Kuhrmann2017", "Dikert2016", "Edison2022"],
```

For the caveats, change only the `"message"` field of these four (the `distributed_team`
caveat is untouched — it has no Chapter 4 basis, see the note above). Each change is a pure
append to the existing message text; do not alter the leading sentence of any of them (some
tests match on it).

The `team_maturity: low` caveat — append `; Table 4.5, F2.2/F4.1/F4.3` inside the existing
parenthesis:
```json
      "message": "Team agile maturity is low: plan training and coaching before and during adoption (Dikert et al., 2016; Table 4.5, F2.2/F4.1/F4.3).",
```

The `regulation: strict` caveat — append a new sentence:
```json
      "message": "Strict regulation: add explicit documentation and approval gates to the iterative process. Evidence for this is conceptual only (Boehm, 2002; Table 4.5, F2.2) and has not yet been empirically tested.",
```

The `team_size: large` caveat — append inside the existing parenthesis:
```json
      "message": "Large team: a single-team framework needs added cross-team coordination (Dikert et al., 2016; Edison et al., 2022; Table 4.5, F4.1).",
```

The `requirement_volatility: high` / `plan_driven` caveat — append inside the existing
parenthesis:
```json
      "message": "High requirement volatility: late changes are costly in a sequential process; add prototyping and iterative testing (Boehm, 2002; Table 4.5, F1.1).",
```

- [ ] **Step 4: Run the full suite**

Run: `.\.venv\Scripts\python.exe -m pytest --cov --cov-fail-under=90 --cov-report=term-missing`
Expected: all tests pass, 100% coverage. Since no weight numbers changed, every ranking
outcome in `tests/test_engine.py` and `tests/test_cli.py` (including the two close-call
scenarios from Task 3) must be unaffected — if anything other than the two version-string
tests changes behavior, STOP and report rather than editing more tests, since that would
mean a weight was accidentally touched.

- [ ] **Step 5: Validate rules and lint**

```bash
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m advisor validate-rules
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format .
```
Expected: `Rules OK: version 1.1.0, 6 factors, 5 methodologies, 5 caveats`.

- [ ] **Step 6: Commit**

```bash
git add config/rules.json tests/test_rules.py tests/test_cli.py
git commit -m "US-08: cite Chapter 4 findings for every methodology's weights (rules v1.1.0)"
```

---

### Task 5: Documentation (US-09)

**Files:**
- Modify: `README.md`

Run this task last, after C3 and US-08 both exist, so the documented behavior and example
output are accurate.

- [ ] **Step 1: Fix the factor count and table**

In the "How recommendations are made" section, change:
```markdown
Each methodology in `config/rules.json` has a weight from -3 (strongly unsuited) to +3
(strongly suited) for every level of five context factors:
```
to:
```markdown
Each methodology in `config/rules.json` has a weight from -3 (strongly unsuited) to +3
(strongly suited) for every level of six context factors:
```
(The factor table below it already lists all six rows correctly — only the prose count was
stale.)

- [ ] **Step 2: Replace the "weights are an initial encoding" sentence**

Replace:
```markdown
A methodology's score is the sum of its weights for the project's factor values. The
output shows every factor's contribution and any caveats, so the reasoning can be
checked. The weights are an initial encoding of the framework and are recalibrated
against the report's findings in Sprint 3 (story US-08).
```
with:
```markdown
A methodology's score is the sum of its weights for the project's factor values, so scores
are an ordinal ranking, not a probability or a percentage -- a score of 11 means "ranked
ahead of a score of 9 by 2 points," not "11% more suitable." The output shows every
factor's contribution and any caveats, so the reasoning can be inspected and challenged
rather than taken on trust.

Each methodology's `rationale` and `sources` in `config/rules.json` cite the specific
Chapter 4 finding that supports its weights (e.g. Table 4.5, Finding 3.2 for Agile with
DevOps). Reviewing Sprint 1's initial weights against those findings in Sprint 3 (story
US-08) found them already directionally consistent for four of the five original factors,
so the weight values themselves did not change -- only their sourcing did. The `regulation`
factor is flagged in `rules.json`'s `note` field as resting on conceptual evidence only
(no direct empirical test was found). The `distributed_team` factor (added in Sprint 2,
story C1) falls outside the five factors the literature review covers and is not
evidence-sourced.

### Close calls

When the top two (or more) methodologies score within `close_call_margin` points of each
other -- a configurable value in `config/rules.json`, currently 2 -- the output names all of
them as a close call instead of presenting a single winner as clear-cut:

```
Close call: Scrum, Agile with DevOps (CI/CD) are within 2 point(s) of each other.
```

The JSON format exposes the same information as `close_call: {"is_close_call": ...,
"margin": ..., "candidates": [...]}`.
```

- [ ] **Step 3: Refresh the Quick start example output**

Run the exact command already in the README (`advisor recommend --volatility high
--team-size 6 --regulation none --release-frequency high --maturity medium
--distributed-team no`) against the real, post-Sprint-3 `config/rules.json`:

```bash
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m advisor recommend --volatility high --team-size 6 --regulation none --release-frequency high --maturity medium --distributed-team no
```

Replace the existing stale example block (which still shows `score 10` and only two
ranking lines from before `distributed_team` and the close-call flag existed) with the
**actual** output of that command, verbatim -- do not hand-write or guess the numbers.

- [ ] **Step 4: Verify the doc changes don't break anything**

Run: `.\.venv\Scripts\python.exe -m pytest --cov --cov-fail-under=90`
Expected: unaffected (README isn't imported by anything), still green and 100%.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "US-09: document score interpretation, close calls, and the evidence sourcing from Chapter 4"
```

---

## After all tasks

1. Push: `git push origin main`
2. Confirm CI is green: `https://github.com/CarliTheron/methodology-advisor-poc/actions`
3. Update `process/backlog.md`: flip US-08, C3 to `done` only after CI is confirmed green
   (same discipline as Sprint 2's Task 8 -- not before). US-09 likewise.
4. Re-run `tools/collect_metrics.py` for Sprint 3's real numbers.
5. Hold the Sprint 3 review, fill in `process/reviews/sprint-3.md`, and only then tag
   `v0.3.0` (or whatever version you and your supervisor agree on) yourself.

## Self-review notes

- **Spec coverage:** C3 (`close_call_margin` in rules.json, output names both/all options
  when it applies, tests cover the boundary -- Tasks 1-3) ✓. US-08 (rules version 1.1.0,
  every *changed* weight has a source -- Task 4; here, honestly, no weight values changed,
  so the criterion is satisfied vacuously on numbers but substantively on the sourcing that
  was actually missing) ✓. US-09 (README covers installation [already did], commands
  [already did after Sprint 2], meaning of scores [new in Task 5]) ✓.
- **Numeric safety:** Task 3's close-call CLI tests depend on exact score gaps (11 vs 9 for
  `BASE_ARGS`, 11 vs 8 for the regulated scenario) that only hold because Task 4 changes no
  weight values. Task 4's Step 4 explicitly re-runs the full suite and treats any
  unexpected behavior change as a stop-and-report condition, not something to silently
  paper over by adjusting tests.
- **Honesty of the calibration itself:** this plan does not invent weight changes to look
  like more work was done. Where Chapter 4 Table 4.5 genuinely supports the existing
  numbers, the plan says so and cites it. Where the evidence is explicitly weak
  (`regulation`, Finding 2.2 -- conceptual only), the plan says that too, in the shipped
  `rules.json` `note` field where a reader (including your supervisor) will actually see it.
