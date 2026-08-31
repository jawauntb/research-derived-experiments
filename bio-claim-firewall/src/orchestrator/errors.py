"""OrchestratorError: the one exception type owned by src/orchestrator.

Raised only when the untrusted *proposer's* own response violates its
contract before any claim ever reaches `verify()` (a `proposer.ProposerError`
propagating out of `Proposer.propose()`). This is deliberately kept
distinct from a `CHECKER_ERROR` verdict -- PHASE_4_PLAN.md's fault-split
invariant table is explicit that a proposer-side pipeline failure ("Keep
`FAILED_PIPELINE` → maps to a distinct proposer-side pipeline error (never
confuse with `CHECKER_ERROR`)") must never be folded into the checker's own
fail-closed vocabulary. Since `OrchestratorResult.status` is a closed
four-value enum with no fifth "the proposer never even produced a claim"
slot, that failure surfaces as a raised exception instead of a fabricated
status value -- see `orchestrator.py`'s PHASE4B-DECISION docstring.
"""

from __future__ import annotations

from typing import Any


class OrchestratorError(Exception):
    """Raised when the orchestrator cannot even begin the verify/repair
    loop (currently: only a proposer-contract violation).

    Attributes:
        code: short machine-readable failure code, e.g. `"propose_failed"`.
        message: human-readable detail.
        details: arbitrary extra kwargs (e.g. `trajectory_id`).
    """

    def __init__(self, code: str, message: str = "", **details: Any) -> None:
        self.code = code
        self.message = message or code
        self.details = details
        super().__init__(f"[{code}] {self.message}")
