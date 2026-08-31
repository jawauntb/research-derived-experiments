"""RepairerError: the one exception type owned by src/repairer.

Raised only when the untrusted repair model's response violates the
repairer-side contract (not JSON, not one of the two allowed shapes, or a
`repaired_claim` that isn't schema-shaped). Mirrors `proposer.errors.ProposerError`
-- see that module's docstring for why this is a narrow, syntactic contract
check and not a re-run of the checker's own full JSON-Schema validator.
"""

from __future__ import annotations

from typing import Any


class RepairerError(Exception):
    """Raised on a repairer-contract violation.

    Attributes:
        code: short machine-readable violation code, e.g.
            `"contract_violated"`.
        message: human-readable detail.
        details: arbitrary extra kwargs recorded for debugging/trajectory
            logging (e.g. `raw_response`, `field_path`).
    """

    def __init__(self, code: str, message: str = "", **details: Any) -> None:
        self.code = code
        self.message = message or code
        self.details = details
        super().__init__(f"[{code}] {self.message}")
