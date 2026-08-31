"""End-to-end: run real mutants against the real tree, produce a report,
assert every fault code in spec/fault_taxonomy.md has at least one
covered mutation.

# PHASE5A-DECISION: "end-to-end against the real tree" here means one
# representative MUTATION-POINT per closed fault code (11 points x 3
# mutation kinds = 33 real subprocess pytest runs), not the full 31-point
# / 93-mutant sweep -- the task brief's "do NOT run the full mutation
# suite in this test (it's slow...)" note is read as scoping the whole
# `tests/eval/mutation/` directory, and this file is the one place in it
# that legitimately needs REAL mutants (the others use synthetic
# fixtures or check one hand-picked site). A representative-per-fault-
# code run is genuinely end-to-end (real source, real subprocess pytest,
# a real rendered report) while staying fast enough for every-commit CI;
# `python -m eval.mutation` (no --limit) is the actual full pass.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from eval.mutation.report import summarize, to_markdown
from eval.mutation.runner import MutationPoint, MutationRunner, discover_points

_QUOTED_RULE_ID_RE = re.compile(r'"(R-[A-Z]+-\d+)"')


def _closed_fault_codes(project_dir: Path) -> list[str]:
    schema = json.loads((project_dir / "spec" / "verdict.schema.json").read_text(encoding="utf-8"))
    return sorted(code for code in schema["properties"]["fault_code"]["enum"] if code is not None)


def _resolve_rule_id(section_path: Path, hinge_lineno: int, window: int = 20) -> str | None:
    """Best-effort: the nearest quoted `"R-XXX-NN"` rule id token within
    `window` lines after the hinge. Every firing branch constructs its
    `Reason` (`rule_id="R-..."` , or a bare `"R-CTX-0N"` string literal in
    `_shared.context_ok`) close to the decision that triggers it. A few
    hinges build the rule id dynamically instead (`context.py`'s single
    MUTATION-POINT delegates to `context_ok`'s return value; `entities.py`'s
    R-ENT-02/03 hinge passes a variable, not a literal) and resolve to
    `None` here -- acceptable, since this test only needs ONE resolvable
    representative per fault code, not all 31 points resolved.
    """
    lines = section_path.read_text(encoding="utf-8").splitlines()
    for line in lines[hinge_lineno - 1 : hinge_lineno - 1 + window]:
        match = _QUOTED_RULE_ID_RE.search(line)
        if match:
            return match.group(1)
    return None


def _one_representative_point_per_fault_code(
    sections_dir: Path, fault_code_by_rule: dict[str, str]
) -> dict[str, MutationPoint]:
    by_fault_code: dict[str, MutationPoint] = {}
    for point in discover_points(sections_dir):
        section_path = sections_dir / Path(point.rel_file).name
        rule_id = _resolve_rule_id(section_path, point.hinge_lineno)
        if rule_id is None or rule_id not in fault_code_by_rule:
            continue
        fault_code = fault_code_by_rule[rule_id]
        by_fault_code.setdefault(fault_code, point)  # first (source-order) hit wins
    return by_fault_code


def test_every_closed_fault_code_has_a_covered_mutation(
    tmp_path: Path, workspace_root: Path, project_dir: Path, sections_dir: Path
) -> None:
    closed_codes = _closed_fault_codes(project_dir)

    # Imported here (rather than at module scope) since it's only needed
    # for this real-tree check, and only resolvable once bio-claim-
    # firewall's own conftest.py has put `src/` on sys.path.
    from rules.engine import _FAULT_CODE_BY_RULE

    by_fault_code = _one_representative_point_per_fault_code(sections_dir, _FAULT_CODE_BY_RULE)
    missing = set(closed_codes) - set(by_fault_code)
    assert not missing, f"could not resolve a representative MUTATION-POINT for fault code(s): {sorted(missing)}"

    runner = MutationRunner(workspace_root=workspace_root, timeout_s=30)
    reports = list(runner.run(list(by_fault_code.values())))
    assert len(reports) == len(by_fault_code) * 3

    # A rendered report is a real deliverable of this end-to-end run --
    # written under tmp_path, never into the tracked eval/mutation/reports/.
    report_path = tmp_path / "full_report_sample.md"
    report_path.write_text(to_markdown(reports), encoding="utf-8")
    assert report_path.exists()
    assert "Mutation test report" in report_path.read_text(encoding="utf-8")

    summary = summarize(reports)
    skipped = [r for r in reports if r.status == "skipped"]
    assert not skipped, f"mutant(s) could not be run at all (infra problem, not a coverage finding): {skipped}"

    def _covered(point: MutationPoint) -> bool:
        return any(r.status == "killed" for r in reports if r.rel_file == point.rel_file and r.hinge_lineno == point.hinge_lineno)

    uncovered = sorted(fc for fc, point in by_fault_code.items() if not _covered(point))
    assert not uncovered, (
        f"fault code(s) whose representative mutation point no test in tests/rules/ caught: {uncovered}. "
        f"Fix by adding a test that exercises this rule's positive and negative case -- see "
        f"eval/mutation/README.md's 'What surviving a mutation means'. (summary: {summary})"
    )
