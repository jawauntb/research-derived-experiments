"""The runner finds every `# MUTATION-POINT:` in `src/rules/sections/*.py`.

Count is checked against an INDEPENDENT line scan built directly in this
test (not derived from `eval.mutation.runner`'s own code -- that would
just test the code against itself), so a discovery regression that drops
or double-counts a marker actually fails this test.
"""

from __future__ import annotations

import re
from pathlib import Path

from eval.mutation.runner import discover_points

_MARKER_RE = re.compile(r"^\s*#\s*MUTATION-POINT:")


def _independent_marker_count(sections_dir: Path) -> int:
    total = 0
    for path in sorted(sections_dir.glob("*.py")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if _MARKER_RE.match(line):
                total += 1
    return total


def test_discovered_count_matches_independent_scan(sections_dir: Path) -> None:
    expected = _independent_marker_count(sections_dir)
    points = discover_points(sections_dir)
    assert len(points) == expected
    # 31 as of this Phase 5a pass, across the 11 section files (one of
    # which, _shared.py, backs the R-CTX-01..06 sub-rules shared by every
    # section that narrows on context). A floor, not a ceiling: expected
    # to grow as new rules are added, each with its own MUTATION-POINT.
    assert expected == 31


def test_every_section_file_contributes_at_least_one_point(sections_dir: Path) -> None:
    points = discover_points(sections_dir)
    files_with_points = {p.rel_file for p in points}
    all_section_files = {
        f"src/rules/sections/{path.name}" for path in sections_dir.glob("*.py") if path.name != "__init__.py"
    }
    missing = all_section_files - files_with_points
    assert not missing, f"section file(s) with no MUTATION-POINT at all: {sorted(missing)}"


def test_every_hinge_line_is_real_code(sections_dir: Path) -> None:
    """The hinge line discovery attributes to each marker is never blank
    or itself a bare comment -- it must be the actual decision statement.
    """
    points = discover_points(sections_dir)
    file_lines = {path.name: path.read_text(encoding="utf-8").splitlines() for path in sections_dir.glob("*.py")}
    for point in points:
        filename = Path(point.rel_file).name
        hinge_text = file_lines[filename][point.hinge_lineno - 1].strip()
        assert hinge_text, point.site_id
        assert not hinge_text.startswith("#"), point.site_id


def test_points_are_unique_sites(sections_dir: Path) -> None:
    points = discover_points(sections_dir)
    site_ids = [p.site_id for p in points]
    assert len(site_ids) == len(set(site_ids)), "duplicate mutation site discovered"
