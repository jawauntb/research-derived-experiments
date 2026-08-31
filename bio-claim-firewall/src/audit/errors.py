"""Error type for the audit ledger.

A single exception class, distinguished by a stable `code` string, so
callers can branch on failure mode without parsing message text.
"""

from __future__ import annotations

from typing import Any


class AuditError(Exception):
    """Raised for any ledger-level failure: duplicate verdicts, tamper
    detection, or malformed ledger content.

    Attributes:
        code: Stable machine-readable failure code, e.g. ``"DUPLICATE_VERDICT_ID"``
            or ``"LEDGER_TAMPERED"``. Not part of the closed `fault_code` enum in
            `spec/fault_taxonomy.md` -- this is a ledger-mechanics error, not a
            claim-verification fault.
        details: Arbitrary structured context (line numbers, ids, etc.) passed
            in as keyword arguments.
    """

    def __init__(self, code: str, message: str | None = None, **details: Any) -> None:
        self.code = code
        self.details = details
        rendered = message or code
        if details:
            extra = ", ".join(f"{k}={v!r}" for k, v in details.items())
            rendered = f"{rendered} ({extra})"
        super().__init__(rendered)

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"AuditError(code={self.code!r}, details={self.details!r})"
