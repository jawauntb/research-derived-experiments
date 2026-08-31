"""`MutationRunner`: discovers `# MUTATION-POINT:` sites and mutation-tests each.

## Discovery

`discover_points()` line-scans `src/rules/sections/*.py` for a comment
matching `# MUTATION-POINT:` (optionally continued across following
comment-only lines), then takes the first following non-blank, non-comment
line as the site's "hinge line" -- the decision-hinge statement the marker
describes. In every section file this is a plain `if`/`elif` line except
one (`signs.py`'s R-SIGN-02 zero/directionless carve-out), which hinges on
the boolean-valued assignment feeding the `if` two lines later; the mutator
below handles both shapes (and `return` statements, for forward
compatibility) via `ast`, not brittle text-column guessing.

## The three mutants

For each site, `apply_delete_line` / `apply_invert_condition` /
`apply_always_none` (below) each transform the ORIGINAL SOURCE TEXT in
memory into a new string -- no file on disk is ever touched by these
functions. `MutationRunner._run_one` is the only place a mutated string is
written to disk, and it is always written under a fresh
`tempfile.TemporaryDirectory()`, never under `src/rules/`.

## Execution

Each mutant gets `bio-claim-firewall/` (plus the workspace-root
`conftest.py` that bootstraps `sys.path`, see that file's own docstring)
copied into the tmp dir, the one mutated file overwritten in the copy, and
`pytest bio-claim-firewall/tests/rules/ -x --tb=no -q -rA` run against the
copy in a fresh subprocess (`PYTHONPATH` is also set explicitly, belt and
suspenders alongside the copied `conftest.py`). `-rA`'s short summary
(beyond the literal task-spec command) is how the runner tells a NEW
failure from a pre-existing one -- see the `# PHASE5A-DECISION` on
`baseline_failed_tests()`.
"""

from __future__ import annotations

import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from .report import MutationReport

MUTATION_KINDS: tuple[str, ...] = ("delete_line", "invert_condition", "always_none")

PROJECT_DIR_NAME = "bio-claim-firewall"
SECTIONS_REL_DIR = "src/rules/sections"
DEFAULT_TEST_REL_PATH = "tests/rules"

_MARKER_RE = re.compile(r"^\s*#\s*MUTATION-POINT:\s*(.*)$")
_COMMENT_LINE_RE = re.compile(r"^\s*#")
_RULE_ID_RE = re.compile(r"\bR-[A-Z]+-\d+\b")
_SUMMARY_RE = re.compile(r"^(?:FAILED|ERROR)\s+(\S+)")


class MutationError(Exception):
    """A mutation site could not be discovered, or a mutant could not be
    safely produced (unsupported statement shape, generated invalid
    syntax). Callers treat this as `status="skipped"`, never as
    `"survived"` -- an inconclusive mutant must never count as coverage.
    """


@dataclass(frozen=True)
class MutationPoint:
    """One `# MUTATION-POINT:` site."""

    rel_file: str  # e.g. "src/rules/sections/signs.py", relative to the project dir
    marker_lineno: int  # 1-indexed line of the "# MUTATION-POINT:" comment itself
    hinge_lineno: int  # 1-indexed line of the decision-hinge statement the comment describes
    comment_text: str  # the marker comment(s), flattened to one string
    rule_ids: tuple[str, ...]  # rule ids (e.g. "R-SIGN-01") mentioned in the comment, best-effort

    @property
    def site_id(self) -> str:
        return f"{self.rel_file}:{self.hinge_lineno}"


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_points(sections_dir: Path) -> list[MutationPoint]:
    """Every `# MUTATION-POINT:` site in `sections_dir/*.py`, file-then-line order."""
    points: list[MutationPoint] = []
    for path in sorted(Path(sections_dir).glob("*.py")):
        rel_file = f"{SECTIONS_REL_DIR}/{path.name}"
        points.extend(_discover_in_file(path, rel_file))
    return points


def _discover_in_file(path: Path, rel_file: str) -> list[MutationPoint]:
    lines = path.read_text(encoding="utf-8").splitlines()
    n = len(lines)
    points: list[MutationPoint] = []
    i = 0
    while i < n:
        m = _MARKER_RE.match(lines[i])
        if not m:
            i += 1
            continue
        marker_lineno = i + 1
        comment_chunks = [m.group(1).strip()]
        j = i + 1
        # Gobble plain comment-continuation lines (but stop at the next marker).
        while j < n and _COMMENT_LINE_RE.match(lines[j]) and not _MARKER_RE.match(lines[j]):
            comment_chunks.append(lines[j].strip().lstrip("#").strip())
            j += 1
        while j < n and not lines[j].strip():
            j += 1
        if j >= n:
            raise MutationError(f"{rel_file}:{marker_lineno}: MUTATION-POINT has no following code line")
        hinge_lineno = j + 1
        comment_text = " ".join(c for c in comment_chunks if c)
        rule_ids = tuple(dict.fromkeys(_RULE_ID_RE.findall(comment_text)))
        points.append(
            MutationPoint(
                rel_file=rel_file,
                marker_lineno=marker_lineno,
                hinge_lineno=hinge_lineno,
                comment_text=comment_text,
                rule_ids=rule_ids,
            )
        )
        i = j + 1
    return points


# ---------------------------------------------------------------------------
# Mutators -- pure string -> string, never touch disk
# ---------------------------------------------------------------------------


def _find_statement(tree: ast.Module, lineno: int) -> ast.stmt:
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.Return, ast.Assign, ast.AugAssign)) and node.lineno == lineno:
            return node
    raise MutationError(f"no If/Return/Assign statement starts at line {lineno}")


def _find_enclosing_function(tree: ast.Module, lineno: int) -> ast.FunctionDef:
    best: ast.FunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.lineno <= lineno <= (node.end_lineno or node.lineno):
            if best is None or (node.end_lineno - node.lineno) < (best.end_lineno - best.lineno):
                best = node
    if best is None:
        raise MutationError(f"no enclosing function def for line {lineno}")
    return best


def _replace_span(lines: list[str], start_lineno: int, end_lineno: int, replacement_line: str) -> list[str]:
    """1-indexed, inclusive `[start_lineno, end_lineno]` span replacement."""
    return lines[: start_lineno - 1] + [replacement_line] + lines[end_lineno:]


def _finish(lines: list[str], source: str) -> str:
    text = "\n".join(lines)
    return text + ("\n" if source.endswith("\n") else "")


def _assign_target_source(source: str, node: ast.Assign | ast.AugAssign) -> str:
    target = node.targets[0] if isinstance(node, ast.Assign) else node.target
    segment = ast.get_source_segment(source, target)
    if segment is None:  # pragma: no cover - defensive; get_source_segment only fails on synthetic nodes
        raise MutationError("could not recover assignment target source text")
    return segment


def apply_delete_line(source: str, hinge_lineno: int) -> str:
    """Delete the hinge statement's effect.

    A guard (`if`/`elif <cond>:`) becomes `if False:` (its body can never
    run again -- syntactically it must stay an `if`, but semantically the
    guard is gone). A `return` statement is replaced by `pass` (falls
    through instead of returning). An assignment feeding a later boolean
    check (e.g. `signs.py`'s R-SIGN-02 hinge) has its value deleted to
    `None`, which is falsy in every `if <name>:` use downstream.
    """
    tree = ast.parse(source)
    node = _find_statement(tree, hinge_lineno)
    lines = source.splitlines()
    indent = " " * node.col_offset

    if isinstance(node, ast.If):
        keyword = "elif" if lines[node.lineno - 1].strip().startswith("elif") else "if"
        mutated = _replace_span(lines, node.lineno, node.test.end_lineno, f"{indent}{keyword} False:")
    elif isinstance(node, ast.Return):
        mutated = _replace_span(lines, node.lineno, node.end_lineno, f"{indent}pass")
    elif isinstance(node, (ast.Assign, ast.AugAssign)):
        target_src = _assign_target_source(source, node)
        mutated = _replace_span(lines, node.lineno, node.end_lineno, f"{indent}{target_src} = None")
    else:  # pragma: no cover - guarded by _find_statement's isinstance filter
        raise MutationError(f"unsupported statement type for delete_line: {type(node).__name__}")
    return _finish(mutated, source)


def apply_invert_condition(source: str, hinge_lineno: int) -> str:
    """Negate the hinge statement's boolean expression: wrap it in `not (...)`."""
    tree = ast.parse(source)
    node = _find_statement(tree, hinge_lineno)
    lines = source.splitlines()
    indent = " " * node.col_offset

    if isinstance(node, ast.If):
        keyword = "elif" if lines[node.lineno - 1].strip().startswith("elif") else "if"
        cond_src = ast.get_source_segment(source, node.test)
        mutated = _replace_span(lines, node.lineno, node.test.end_lineno, f"{indent}{keyword} not ({cond_src}):")
    elif isinstance(node, ast.Return):
        expr_src = ast.get_source_segment(source, node.value) if node.value is not None else "None"
        mutated = _replace_span(lines, node.lineno, node.end_lineno, f"{indent}return not ({expr_src})")
    elif isinstance(node, (ast.Assign, ast.AugAssign)):
        target_src = _assign_target_source(source, node)
        rhs_src = ast.get_source_segment(source, node.value)
        mutated = _replace_span(lines, node.lineno, node.end_lineno, f"{indent}{target_src} = not ({rhs_src})")
    else:  # pragma: no cover - guarded by _find_statement's isinstance filter
        raise MutationError(f"unsupported statement type for invert_condition: {type(node).__name__}")
    return _finish(mutated, source)


def apply_always_none(source: str, hinge_lineno: int) -> str:
    """Replace the whole body of the hinge's innermost enclosing function with `return None`.

    # PHASE5A-DECISION: "the rule function" is read as the innermost
    # enclosing `def`, not necessarily the section's public `check`/
    # `check_all`. Several sites share a private helper (e.g.
    # `entities._check_curie`, `contradiction._check_record`,
    # `_shared.context_ok`) that IS the actual per-record decision point;
    # neutering that helper is the mechanical "this rule never fires"
    # mutant the spec describes, and is more surgical than blanking out
    # the whole public function when multiple MUTATION-POINTs share one.
    """
    tree = ast.parse(source)
    func = _find_enclosing_function(tree, hinge_lineno)
    lines = source.splitlines()
    body_start = func.body[0].lineno
    body_end = func.end_lineno
    indent = " " * func.body[0].col_offset
    mutated = lines[: body_start - 1] + [f"{indent}return None"] + lines[body_end:]
    return _finish(mutated, source)


MUTATORS = {
    "delete_line": apply_delete_line,
    "invert_condition": apply_invert_condition,
    "always_none": apply_always_none,
}


def _parse_failed_node_ids(stdout: str) -> set[str]:
    ids: set[str] = set()
    for line in stdout.splitlines():
        m = _SUMMARY_RE.match(line.strip())
        if m:
            ids.add(m.group(1))
    return ids


# ---------------------------------------------------------------------------
# MutationRunner
# ---------------------------------------------------------------------------


@dataclass
class MutationRunner:
    """Discovers mutation sites under one `bio-claim-firewall/` checkout and
    mutation-tests each in an isolated subprocess against a tmp copy.

    `workspace_root` is the directory containing both `bio-claim-firewall/`
    and its `conftest.py` (the repo root, "Research Derived Experiments/"
    in production; a synthetic fixture root in the framework's own tests).
    """

    workspace_root: Path
    project_dir_name: str = PROJECT_DIR_NAME
    test_rel_path: str = DEFAULT_TEST_REL_PATH
    timeout_s: float = 60.0
    _baseline_failed: frozenset[str] | None = None

    def __post_init__(self) -> None:
        self.workspace_root = Path(self.workspace_root)

    @property
    def project_dir(self) -> Path:
        return self.workspace_root / self.project_dir_name

    @property
    def sections_dir(self) -> Path:
        return self.project_dir / SECTIONS_REL_DIR

    def discover(self) -> list[MutationPoint]:
        return discover_points(self.sections_dir)

    def baseline_failed_tests(self) -> frozenset[str]:
        """The set of test node ids already failing/erroring on the UNMUTATED tree.

        # PHASE5A-DECISION: the task-spec command is
        # `pytest tests/rules/ -x --tb=no -q`, a bare pass/fail signal.
        # Read literally, a suite with even one pre-existing failing test
        # would make every mutant look "killed" regardless of whether the
        # mutation itself was ever exercised -- silently defeating the
        # guardrail. Diffing each mutant's failing-test set against this
        # baseline (both collected with `-rA`'s short summary, layered on
        # top of the literal spec command) is a small addition that keeps
        # "killed" meaning what it claims to mean. On this repo's tree the
        # baseline is empty (`tests/rules/` passes clean), so this is a
        # no-op in practice today and only matters if that ever changes.
        """
        if self._baseline_failed is None:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", f"{self.project_dir_name}/{self.test_rel_path}", "--tb=no", "-q", "-rA"],
                cwd=self.workspace_root,
                env=os.environ.copy(),
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
            )
            self._baseline_failed = frozenset(_parse_failed_node_ids(proc.stdout))
        return self._baseline_failed

    def run(
        self,
        points: Sequence[MutationPoint] | None = None,
        kinds: Sequence[str] = MUTATION_KINDS,
        limit: int | None = None,
    ) -> Iterator[MutationReport]:
        """Yields one `MutationReport` per `(point, kind)` pair.

        `limit` caps the number of mutation POINTS (not mutants); each
        surviving point still gets all of `kinds` run against it.
        """
        if points is None:
            points = self.discover()
        if limit is not None:
            points = list(points)[:limit]
        baseline = self.baseline_failed_tests()
        for point in points:
            for kind in kinds:
                yield self._run_one(point, kind, baseline)

    def _run_one(self, point: MutationPoint, kind: str, baseline: frozenset[str]) -> MutationReport:
        source_path = self.project_dir / point.rel_file
        source = source_path.read_text(encoding="utf-8")

        try:
            mutated_source = MUTATORS[kind](source, point.hinge_lineno)
            ast.parse(mutated_source)
        except (MutationError, SyntaxError) as exc:
            return MutationReport(
                rel_file=point.rel_file,
                hinge_lineno=point.hinge_lineno,
                rule_ids=point.rule_ids,
                mutation_kind=kind,
                status="skipped",
                detail=f"could not produce a valid mutant: {exc}",
                returncode=None,
                duration_s=0.0,
            )

        start = time.monotonic()
        try:
            proc = self._run_pytest_against_mutant(point, mutated_source)
            duration = time.monotonic() - start
        except subprocess.TimeoutExpired:
            duration = time.monotonic() - start
            return MutationReport(
                rel_file=point.rel_file,
                hinge_lineno=point.hinge_lineno,
                rule_ids=point.rule_ids,
                mutation_kind=kind,
                status="skipped",
                detail=f"pytest subprocess timed out after {self.timeout_s}s",
                returncode=None,
                duration_s=duration,
            )

        failed_now = frozenset(_parse_failed_node_ids(proc.stdout))
        new_failures = sorted(failed_now - baseline)

        if new_failures:
            status = "killed"
            extra = f" (+{len(new_failures) - 1} more)" if len(new_failures) > 1 else ""
            detail = f"newly failing: {new_failures[0]}{extra}"
        elif proc.returncode == 0:
            status = "survived"
            detail = "all tests passed against the mutant"
        elif proc.returncode == 1:
            status = "survived"
            detail = "only pre-existing (baseline) failures observed; mutation not detected"
        else:
            status = "skipped"
            tail = (proc.stdout[-400:] + proc.stderr[-400:]).strip()
            detail = f"pytest exited {proc.returncode} (infra issue): {tail}"

        return MutationReport(
            rel_file=point.rel_file,
            hinge_lineno=point.hinge_lineno,
            rule_ids=point.rule_ids,
            mutation_kind=kind,
            status=status,
            detail=detail,
            returncode=proc.returncode,
            duration_s=duration,
        )

    def _run_pytest_against_mutant(self, point: MutationPoint, mutated_source: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="bcf-mutation-") as tmp:
            tmp_path = Path(tmp)
            self._materialize(tmp_path)

            dest_project = tmp_path / self.project_dir_name
            dest_file = dest_project / point.rel_file
            dest_file.write_text(mutated_source, encoding="utf-8")

            env = os.environ.copy()
            pythonpath_parts = [str(dest_project), str(dest_project / "src")]
            existing = env.get("PYTHONPATH")
            if existing:
                pythonpath_parts.append(existing)
            env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

            return subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    f"{self.project_dir_name}/{self.test_rel_path}",
                    "-x",
                    "--tb=no",
                    "-q",
                    "-rA",
                ],
                cwd=tmp_path,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
            )

    def _materialize(self, tmp_path: Path) -> None:
        """Copies `workspace_root/conftest.py` and the whole `project_dir` into `tmp_path`.

        NEVER writes into `self.project_dir` itself -- everything mutable
        happens only under `tmp_path`, a fresh `tempfile.TemporaryDirectory`
        the caller tears down afterwards.
        """
        top_conftest = self.workspace_root / "conftest.py"
        if top_conftest.exists():
            shutil.copy2(top_conftest, tmp_path / "conftest.py")
        shutil.copytree(
            self.project_dir,
            tmp_path / self.project_dir_name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
        )


def iter_mutation_kinds() -> Iterable[str]:
    return MUTATION_KINDS
