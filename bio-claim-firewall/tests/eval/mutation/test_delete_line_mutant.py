"""For R-SIGN-01 specifically, `delete_line` breaks a specific test in
`tests/rules/test_r_sign.py`.

Runs the real `MutationRunner` against the real (unmodified) tree, scoped
to just `test_r_sign.py` (via `test_rel_path`) so the assertion is
unambiguous about WHICH file's test caught it, rather than relying on
whatever test happens to be collected first in the full `tests/rules/`
sweep under `-x`.
"""

from __future__ import annotations

from pathlib import Path

from eval.mutation.runner import MutationPoint, MutationRunner, discover_points


def _r_sign_01_point(sections_dir: Path) -> MutationPoint:
    signs_points = [p for p in discover_points(sections_dir) if p.rel_file.endswith("signs.py")]
    assert signs_points, "expected at least one MUTATION-POINT in signs.py"
    # signs.py's first MUTATION-POINT in source order is R-SIGN-01's own
    # sign-match hinge (`if matched: return None, False` inside the
    # `relation in RELATION_CANONICAL_SIGN` branch) -- see
    # src/rules/sections/signs.py's module docstring for why R-SIGN-01 is
    # checked before R-SIGN-02.
    return signs_points[0]


def test_delete_line_on_r_sign_01_breaks_test_r_sign(workspace_root: Path, sections_dir: Path) -> None:
    point = _r_sign_01_point(sections_dir)

    runner = MutationRunner(
        workspace_root=workspace_root,
        test_rel_path="tests/rules/test_r_sign.py",
        timeout_s=30,
    )
    report = next(runner.run([point], kinds=["delete_line"]))

    assert report.status == "killed", report.detail
    assert "test_r_sign.py" in report.detail, report.detail
    assert report.returncode == 1
