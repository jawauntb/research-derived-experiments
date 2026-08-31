"""Top-level pytest bootstrap for bio-claim-firewall.

bio-claim-firewall has no `pyproject.toml` of its own yet — its tests run
via the workspace-root command `uv run --no-sync python -m pytest
bio-claim-firewall/tests/…`. This conftest puts both

    - `bio-claim-firewall/`       (so `from src.evidence.xxx import ...` works)
    - `bio-claim-firewall/src/`   (so `from normalize.xxx import ...` works)

on `sys.path` once, replacing the per-directory sys.path hacks that would
otherwise disagree and make cross-module integration awkward.

Both import styles resolve independently and refer to the same underlying
module: `src.evidence.snapshot` and `evidence.snapshot` are aliases for the
same file. New modules should prefer the bare form (`from evidence.xxx`,
`from normalize.xxx`, `from audit.xxx`) for consistency; the `src.`-prefixed
form is retained only to keep the existing evidence tests green during the
Phase 3 fan-in.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"

for _p in (_ROOT, _SRC):
    _pstr = str(_p)
    if _pstr not in sys.path:
        sys.path.insert(0, _pstr)
