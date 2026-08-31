"""Load and hash-verify frozen snapshots (ontologies + evidence ledgers).

Exposes an in-memory ``SnapshotBundle`` that satisfies the ``Snapshot``
protocol needed by ``src/normalize/`` and ``src/rules/``, and refuses to
serve data that has been tampered with -- see ``loader.load_bundle`` and
``errors.EvidenceError``.
"""

from __future__ import annotations

from .errors import EvidenceError
from .ledger import EvidenceLedger
from .loader import load_bundle
from .manifest import Manifest
from .snapshot import SnapshotBundle

__all__ = [
    "SnapshotBundle",
    "EvidenceLedger",
    "Manifest",
    "load_bundle",
    "EvidenceError",
]
