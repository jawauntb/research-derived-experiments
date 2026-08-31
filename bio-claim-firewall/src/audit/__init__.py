"""Append-only, tamper-evident audit ledger for (claim, verdict) pairs.

This is the ONLY place a verdict, once issued, is recorded. See
spec/non_goals.md's "Prohibited moves": "Post-hoc rewriting of a verdict.
The audit ledger is append-only. A superseded verdict gets a new
verdict_id; the old one stays visible." Nothing in this package can
delete or rewrite a line once it's fsynced to disk.
"""

from .entry import LedgerEntry
from .errors import AuditError
from .hashing import canonicalize_for_hash, compute_verdict_id
from .ledger import AuditLedger

__all__ = [
    "AuditLedger",
    "LedgerEntry",
    "compute_verdict_id",
    "canonicalize_for_hash",
    "AuditError",
]
