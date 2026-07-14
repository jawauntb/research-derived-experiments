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

# Experiment contract registry (package coverage + run bindings).
PACKAGE_ID_PATTERN = r"^[a-z0-9][a-z0-9_-]{1,63}$"
GIT_COMMIT_PATTERN = r"^[0-9a-f]{40}$"
ISO_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"
PACKAGE_ID = re.compile(PACKAGE_ID_PATTERN)
GIT_COMMIT = re.compile(GIT_COMMIT_PATTERN)
ISO_DATE = re.compile(ISO_DATE_PATTERN)
COVERAGE_MODES = {"structured_manifest", "legacy_exception"}
PROVENANCE_MODES = {"structured_manifest", "legacy_report"}
INTEGRITY_STATES = {"valid", "invalid", "not_assessed"}
RUN_COVERAGE_STATES = {"complete", "partial"}
EXCEPTION_REASON_CODES = {
    "pre_manifest_publication",
    "multi_run_ambiguity",
    "scaffold_pending_contract",
}
# A legacy exception may never be granted or renewed further out than this.
MAX_EXCEPTION_HORIZON_DAYS = 180
# Normal validation warns this many days before an exception expires.
EXPIRY_WARNING_DAYS = 30
LEGACY_ADJUDICATION_STATEMENT = (
    "This exception records migration debt only; "
    "it does not adjudicate scientific claims."
)
