"""Shared fixtures for tests/eval/mutation/.

`workspace_root` / `sections_dir` point at the REAL repo -- read-only in
every fixture here. Nothing under `tests/eval/mutation/` ever writes into
`sections_dir`; mutants only ever land in a `tempfile.TemporaryDirectory()`
(see `eval/mutation/runner.py`'s own module docstring).
"""

from __future__ import annotations

from pathlib import Path

import pytest

# This file: bio-claim-firewall/tests/eval/mutation/conftest.py
# parents[0]=mutation, [1]=eval, [2]=tests, [3]=bio-claim-firewall, [4]=workspace root.
_WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
_PROJECT_DIR = _WORKSPACE_ROOT / "bio-claim-firewall"
_SECTIONS_DIR = _PROJECT_DIR / "src" / "rules" / "sections"


@pytest.fixture
def workspace_root() -> Path:
    return _WORKSPACE_ROOT


@pytest.fixture
def project_dir() -> Path:
    return _PROJECT_DIR


@pytest.fixture
def sections_dir() -> Path:
    return _SECTIONS_DIR
