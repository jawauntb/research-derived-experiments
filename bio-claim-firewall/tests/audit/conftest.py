"""Make the `audit` package (bio-claim-firewall/src/audit) importable.

bio-claim-firewall has no installed package / pyproject of its own yet;
tests run via the workspace-root `uv run ... pytest bio-claim-firewall/tests/audit/`.
This just puts `bio-claim-firewall/src` on sys.path so `import audit` (and
`from audit import ...`) resolves to the module under test.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
