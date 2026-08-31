# `eval/mutation/` -- the Phase 5 mutation-test runner

This is the guardrail behind `spec/fault_taxonomy.md`'s claim that every
fault code has a real "Mutation test." A `# MUTATION-POINT:` comment marks
the exact line in `src/rules/sections/*.py` where a rule's decision
actually hinges. This runner mutates that line three different ways, in a
throwaway copy of the tree, and checks that `tests/rules/` notices. A
mutation nothing notices means the rule it guards is unvalidated -- the
tests only prove the rule *can* pass, never that it can *fail*.

## Running it

From the workspace root (`Research Derived Experiments/`):

```sh
cd bio-claim-firewall
uv run --no-sync python -m eval.mutation --limit 5
```

or, without `cd`:

```sh
PYTHONPATH=bio-claim-firewall uv run --no-sync python -m eval.mutation \
    --limit 5 --report bio-claim-firewall/eval/mutation/reports/latest.md
```

Useful flags:

- `--limit N` -- only run the first N mutation *points* (every point still
  gets all three mutation kinds; use this for a quick spot-check).
- `--kinds delete_line invert_condition` -- restrict to specific mutation
  kinds.
- `--report PATH` -- where to write the Markdown report (a sibling
  `.json` export is always written next to it too). Default:
  `eval/mutation/reports/latest.md`, resolved against the CWD.
- `--timeout SECONDS` -- per-mutant pytest subprocess timeout (default 60).

The full pass runs 31 mutation points x 3 mutants = 93 isolated `pytest`
subprocess invocations and takes on the order of a minute. It is
deliberately NOT run as part of `tests/eval/mutation/` (see below) --
that suite only exercises the framework itself against small synthetic
fixtures, fast enough for every-commit CI.

**Exit code**: `0` if every mutant was killed, `1` if at least one
survived (wire this into CI as the actual gate), `2` on a framework-level
problem (e.g. discovery itself failed).

## What "surviving a mutation" means

For each `(mutation site, mutation kind)` pair, the runner reports one of:

- **`killed`** -- at least one test in `tests/rules/` started failing
  against the mutant that wasn't already failing on the unmutated tree.
  The site is validated: something in the suite would actually notice if
  this exact line broke.
- **`survived`** -- no test noticed. **This is the finding that matters.**
  A fault code whose mutation point survives is, by this repo's own
  Phase 5 rule, unvalidated -- treat it exactly like a fault code with no
  test at all. **Fix it by adding a test that exercises the surviving
  line's positive AND negative case, never by deleting the mutation
  point, weakening the mutant, or declaring the rule "obviously
  correct."**
- **`skipped`** -- the mutant itself couldn't be safely produced or run
  (unsupported statement shape, generated code that doesn't parse, a
  timed-out subprocess, or another infra problem). This is deliberately
  its own status, distinct from `survived` -- an inconclusive run must
  never silently count as "covered."

Run `python -m eval.mutation` and read the "Surviving mutants" section of
the generated report; each entry names the exact `file:line` and mutation
kind that got past the suite.

## The three mutants

For a mutation site, all three are produced from the ORIGINAL source text
in memory (never from a previous mutant, and never written anywhere but a
`tempfile.TemporaryDirectory`):

1. **`delete_line`** -- deletes the hinge statement's effect.
   - A guard (`if <cond>:` / `elif <cond>:`) becomes `if False:` (its
     body can now never run).
   - A `return <expr>` statement becomes `pass` (falls through instead).
   - An assignment feeding a later boolean check (the one non-`if` hinge
     in this codebase, `signs.py`'s R-SIGN-02 carve-out) has its value
     replaced with `None`, which is falsy wherever it's later checked.
2. **`invert_condition`** -- wraps the hinge's boolean expression in
   `not (...)`, in place (an `if`'s test, a `return`'s value, or an
   assignment's right-hand side).
3. **`always_none`** -- replaces the entire body of the hinge line's
   innermost enclosing function with `return None` (the "this rule never
   fires at all" mutant). Several sites share one small private helper
   (e.g. `entities.py`'s `_check_curie`, `contradiction.py`'s
   `_check_record`, `_shared.py`'s `context_ok`); `always_none` targets
   that innermost function, not necessarily the section's public
   `check`/`check_all`.

Mutation is done with `ast` (`ast.parse` + `ast.get_source_segment`), not
raw string-column guessing, specifically so a multi-line condition (e.g.
`_shared.py`'s R-CTX-02 ancestor check, which spans three physical lines)
mutates correctly. Every produced mutant is `ast.parse`-validated before
any subprocess is spawned; one that fails to parse is recorded as
`skipped`, never run.

## Adding a new mutation point

1. In the rule function in `src/rules/sections/<file>.py`, add a
   `# MUTATION-POINT: <one-line description of what this line decides>`
   comment directly above the line the decision actually hinges on (an
   `if`/`elif` guard, a `return`, or -- if the hinge is a boolean-valued
   assignment consumed a line or two later -- that assignment).
   Multi-line marker comments (continuation lines starting with `#`) are
   supported; the first non-comment, non-blank line after the block is
   what gets discovered as the hinge.
2. Add (or confirm there already is) a positive test in `tests/rules/`
   that would fail if this exact line's decision were reversed or
   deleted -- per `spec/fault_taxonomy.md`'s "Mutation test" entry for
   the fault code this rule renders.
3. Run `python -m eval.mutation --limit <n>` targeting just the new file
   (or the full pass) and confirm all three mutants for the new site come
   back `killed`, not `survived`.

## How the isolation works (load-bearing)

- `MutationRunner._materialize()` copies the WHOLE `bio-claim-firewall/`
  tree (plus the workspace-root `conftest.py` that seeds `sys.path`) into
  a fresh `tempfile.TemporaryDirectory()`, then overwrites exactly one
  file in that copy with the mutated source. `src/rules/sections/` in the
  real checkout is never opened for writing anywhere in this package --
  only `Path.read_text()`.
- Every mutant runs `pytest bio-claim-firewall/tests/rules/ -x --tb=no -q
  -rA` in its own `subprocess.run(...)`, cwd'd into that tmp dir, with
  `PYTHONPATH` explicitly set to the tmp copy's `bio-claim-firewall/` and
  `bio-claim-firewall/src/` (the same two paths the copied `conftest.py`
  itself adds to `sys.path` -- belt and suspenders). Each subprocess is a
  fresh Python process; no import-cache leakage between mutants.
- `MutationRunner.baseline_failed_tests()` runs the unmutated tree once
  (also via `-rA`, without `-x`, cached for the run) so a pre-existing
  failing test never gets misreported as "this mutant was killed" -- see
  the `# PHASE5A-DECISION` on that method in `runner.py`.

## Files

- `runner.py` -- `MutationPoint`/`MutationRunner`, discovery, the three
  `ast`-based mutators, subprocess execution.
- `report.py` -- `MutationReport`, Markdown/JSON rendering.
- `cli.py` / `__main__.py` -- `python -m eval.mutation`.
- `reports/` -- default output directory for `--report` (git-ignored
  content is fine to regenerate; nothing here is hand-maintained).

The framework itself is exercised by `tests/eval/mutation/` against small
synthetic fixtures -- see that directory's own tests for what "the runner
works" means mechanically, separate from "the real rules are covered,"
which `tests/eval/mutation/test_full_report.py` checks against the real
tree (still without running the full 93-mutant sweep in CI).
