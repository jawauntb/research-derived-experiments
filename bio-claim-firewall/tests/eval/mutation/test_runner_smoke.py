"""Framework smoke test: a synthetic 2-rule fake source tree with 2 known
tests, and the runner correctly tells which rule is actually covered.

Rule A (`alpha.py`) has a test asserting on both its positive and
negative branch -- every mutant should be `killed`. Rule B (`beta.py`)
has a test that calls its `check()` but never asserts on the result --
no mutant can ever be `killed`, regardless of how its guard is mutated.
This is the exact distinction the whole framework exists to surface, so
this is the one test file allowed to assert `"survived"` as the CORRECT
outcome rather than a finding to chase down.
"""

from __future__ import annotations

from pathlib import Path

from eval.mutation.runner import MutationRunner, discover_points

_CONFTEST = '''\
"""Fake workspace bootstrap, mirroring bio-claim-firewall/conftest.py."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_PROJECT = _ROOT / "fakeproj"
_SRC = _PROJECT / "src"

for _p in (_PROJECT, _SRC):
    _pstr = str(_p)
    if _pstr not in sys.path:
        sys.path.insert(0, _pstr)
'''

_ALPHA_SOURCE = '''\
"""Fake rule A -- covered by a test that checks both branches."""
from __future__ import annotations


def check(x: int) -> str | None:
    # MUTATION-POINT: x must be strictly positive to pass.
    if x > 0:
        return "POS"
    return None
'''

_BETA_SOURCE = '''\
"""Fake rule B -- exercised by a test that asserts nothing about its result."""
from __future__ import annotations


def check(y: bool) -> str | None:
    # MUTATION-POINT: y must be truthy to pass.
    if y:
        return "YES"
    return None
'''

_TEST_ALPHA = """\
from rules.sections import alpha


def test_alpha_positive_fires():
    assert alpha.check(5) == "POS"


def test_alpha_negative_is_none():
    assert alpha.check(-1) is None
"""

_TEST_BETA = """\
from rules.sections import beta


def test_beta_does_not_raise():
    # Deliberately asserts nothing about the return value -- the "known
    # uncovered" test: it can never notice beta.check()'s guard being
    # deleted, inverted, or neutered.
    beta.check(True)
"""


def _write_fake_workspace(tmp_path: Path) -> Path:
    (tmp_path / "conftest.py").write_text(_CONFTEST, encoding="utf-8")

    src_sections = tmp_path / "fakeproj" / "src" / "rules" / "sections"
    src_sections.mkdir(parents=True)
    (tmp_path / "fakeproj" / "src" / "rules" / "__init__.py").write_text("", encoding="utf-8")
    (src_sections / "__init__.py").write_text("", encoding="utf-8")
    (src_sections / "alpha.py").write_text(_ALPHA_SOURCE, encoding="utf-8")
    (src_sections / "beta.py").write_text(_BETA_SOURCE, encoding="utf-8")

    tests_rules = tmp_path / "fakeproj" / "tests" / "rules"
    tests_rules.mkdir(parents=True)
    (tests_rules / "test_alpha.py").write_text(_TEST_ALPHA, encoding="utf-8")
    (tests_rules / "test_beta.py").write_text(_TEST_BETA, encoding="utf-8")

    return tmp_path


def test_discovery_finds_both_fake_rules(tmp_path: Path) -> None:
    _write_fake_workspace(tmp_path)
    sections_dir = tmp_path / "fakeproj" / "src" / "rules" / "sections"

    points = discover_points(sections_dir)

    rel_files = sorted(p.rel_file for p in points)
    assert rel_files == ["src/rules/sections/alpha.py", "src/rules/sections/beta.py"]


def test_runner_tells_covered_rule_from_uncovered_rule(tmp_path: Path) -> None:
    _write_fake_workspace(tmp_path)
    runner = MutationRunner(workspace_root=tmp_path, project_dir_name="fakeproj", timeout_s=30)

    points = runner.discover()
    assert len(points) == 2

    reports = list(runner.run(points))
    assert len(reports) == 6  # 2 points x 3 mutation kinds

    alpha_reports = [r for r in reports if r.rel_file.endswith("alpha.py")]
    beta_reports = [r for r in reports if r.rel_file.endswith("beta.py")]
    assert len(alpha_reports) == 3
    assert len(beta_reports) == 3

    assert all(r.status == "killed" for r in alpha_reports), alpha_reports
    assert all(r.status == "survived" for r in beta_reports), beta_reports
