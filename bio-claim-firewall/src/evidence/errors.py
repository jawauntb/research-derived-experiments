"""The one exception type this module raises."""

from __future__ import annotations


class EvidenceError(Exception):
    """Raised when the evidence module cannot serve trustworthy data.

    This module raises it with exactly two `fault_code` values:

    - ``"BAD_CITATION"`` -- an ``evidence_ids[i]`` in a claim does not
      resolve in the frozen ledger (``EvidenceLedger.get``). This is the
      signal for R-CITE-01 in ``spec/inference_rules.md`` and maps to
      ``REJECTED_BAD_CITATION`` per ``spec/fault_taxonomy.md``'s closed
      enum -- a fault of the *claim*, not of the checker.

    - ``"HASH_MISMATCH"`` -- a frozen snapshot file on disk does not match
      the sha256 recorded in its manifest, or the data root is otherwise
      unreadable/malformed (``load_bundle``). ``HASH_MISMATCH`` is
      deliberately **not** a member of the closed ``fault_code`` enum in
      ``spec/fault_taxonomy.md``: it is the checker itself failing to load
      trustworthy data, which ``spec/verdict.schema.json`` routes to the
      ``checker_error`` verdict branch ("snapshot hash mismatch" is named
      there explicitly), not to a ``REJECTED_<FAULT_CODE>`` verdict. The
      top-level verifier is expected to catch this and fail closed into
      ``CHECKER_ERROR``, never auto-repairing it into a rejection.

    ``fault_code`` and any keyword details are attached as attributes so a
    catching layer can render them without re-parsing the message string.
    """

    def __init__(self, fault_code: str, **details: object) -> None:
        self.fault_code = fault_code
        self.details = details
        detail_str = ", ".join(f"{key}={value!r}" for key, value in details.items())
        message = fault_code if not detail_str else f"{fault_code} ({detail_str})"
        super().__init__(message)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"EvidenceError({self.fault_code!r}, **{self.details!r})"
