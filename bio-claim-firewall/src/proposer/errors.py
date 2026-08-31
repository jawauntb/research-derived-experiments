"""ProposerError: the one exception type owned by src/proposer.

Raised whenever the untrusted proposer model's response violates the
proposer-side contract (spec/claim.schema.json shape, the "response is a
single JSON array" rule, etc). Never raised for a claim that is merely
*rejectable* by the checker (wrong CURIE prefix, unsupported relation,
overclaimed certainty, ...) -- those are legitimate `Claim` dicts and flow
through to `verify()` to become `REJECTED_<FAULT_CODE>` verdicts. This
class exists strictly for "the model did not even produce data shaped like
a claim bundle."
"""

from __future__ import annotations

from typing import Any


class ProposerError(Exception):
    """Raised on a proposer-contract violation.

    Attributes:
        code: short machine-readable violation code, e.g.
            `"contract_violated"`.
        message: human-readable detail.
        details: arbitrary extra kwargs recorded for debugging/trajectory
            logging (e.g. `raw_response`, `field_path`, `claim_index`).
    """

    def __init__(self, code: str, message: str = "", **details: Any) -> None:
        self.code = code
        self.message = message or code
        self.details = details
        super().__init__(f"[{code}] {self.message}")
