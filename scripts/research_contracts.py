"""Shared vocabulary for structured research contracts.

JSON Schema remains the portable wire contract.  These constants keep the
dependency-free Python adapters aligned with one another; parity tests pin the
same values in the committed schemas.
"""

from __future__ import annotations

import re


SCHEMA_VERSION = "1.0"
CLAIM_TIERS = {"descriptive", "internal", "external", "causal", "theoretical"}
CLAIM_STATUSES = {"supported", "rejected", "open", "inconclusive"}
EVIDENCE_STATUSES = {"pass", "fail", "inconclusive", "not_run", "superseded", "retired"}
CLAIM_ID_PATTERN = r"^[A-Z][A-Z0-9_-]{2,63}$"
EVIDENCE_ID_PATTERN = r"^EVID-[A-Z0-9][A-Z0-9_-]{2,63}$"
SHA256_PATTERN = r"^[0-9a-f]{64}$"
CLAIM_ID = re.compile(CLAIM_ID_PATTERN)
EVIDENCE_ID = re.compile(EVIDENCE_ID_PATTERN)
SHA256 = re.compile(SHA256_PATTERN)
