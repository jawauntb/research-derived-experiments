"""Canonicalization module for the bio-claim-firewall verifier.

Takes a schema-valid Claim (and EvidenceRecord) dict and returns a canonical,
frozen form the rule engine can compare cheaply, resolving every CURIE
against a frozen ontology `Snapshot` along the way.
"""

from __future__ import annotations

from .errors import NormalizationError
from .normalize import normalize_claim, normalize_evidence
from .snapshot import Snapshot
from .types import CanonicalClaim, CanonicalEffect, CanonicalEvidence

__all__ = [
    "normalize_claim",
    "normalize_evidence",
    "Snapshot",
    "CanonicalClaim",
    "CanonicalEffect",
    "CanonicalEvidence",
    "NormalizationError",
]
