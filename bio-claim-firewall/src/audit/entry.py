"""The unit of storage in the audit ledger: one (claim, verdict) row."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LedgerEntry:
    """One row of the audit ledger.

    Frozen (immutable) by construction: there is no setter, and the ledger
    never edits a written entry -- see AuditLedger's append-only contract
    and spec/non_goals.md's "Post-hoc rewriting of a verdict" prohibition.
    A correction is a new `LedgerEntry` with `supersedes` set inside its
    `verdict` dict; the superseded entry is untouched.

    Attributes:
        verdict_id: Tamper-evident id from `compute_verdict_id`.
        claim_id: The claim's own id (`claim["claim_id"]`), duplicated here
            as a top-level field so `find_by_claim_id` doesn't need to
            parse into `claim` for every entry.
        issued_at: ISO 8601 UTC timestamp with a literal `Z` suffix, e.g.
            `2026-08-31T12:00:00.000Z`.
        claim: The full claim object, verbatim.
        verdict: The full verdict object, verbatim (includes `verdict_id`
            redundantly as `verdict["verdict_id"]` if the caller put it
            there before calling `AuditLedger.append`; `AuditLedger` does
            not require or depend on that).
    """

    verdict_id: str
    claim_id: str
    issued_at: str
    claim: dict[str, Any]
    verdict: dict[str, Any]

    def write_line(self) -> str:
        """Render this entry as a single line of JSON, no trailing newline.

        `AuditLedger.append` is responsible for appending the `\\n`; keeping
        that here would make `write_line()`'s output not literally "one
        line" as a string.
        """
        payload = {
            "verdict_id": self.verdict_id,
            "claim_id": self.claim_id,
            "issued_at": self.issued_at,
            "claim": self.claim,
            "verdict": self.verdict,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_line(cls, line: str) -> "LedgerEntry":
        """Parse one ledger line back into a `LedgerEntry`.

        Raises `json.JSONDecodeError` on malformed JSON, `KeyError` if a
        required field is missing, or `TypeError` if `claim`/`verdict`
        aren't objects. `AuditLedger.verify_integrity` catches all three
        and re-raises as `AuditError("LEDGER_TAMPERED", ...)`.
        """
        data = json.loads(line)
        if not isinstance(data, dict):
            raise TypeError(f"ledger line did not decode to a JSON object: {type(data).__name__}")
        claim = data["claim"]
        verdict = data["verdict"]
        if not isinstance(claim, dict):
            raise TypeError("ledger entry field 'claim' must be a JSON object")
        if not isinstance(verdict, dict):
            raise TypeError("ledger entry field 'verdict' must be a JSON object")
        return cls(
            verdict_id=data["verdict_id"],
            claim_id=data["claim_id"],
            issued_at=data["issued_at"],
            claim=claim,
            verdict=verdict,
        )
