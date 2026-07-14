#!/usr/bin/env python3
"""Validate the canonical program evidence registry without third-party packages.

The registry is intentionally small and strict.  It is the shared contract for
the six primer backlogs: experiment packages may add records, but they may not
invent a second status vocabulary or silently reuse an evidence identifier.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import cast

try:
    from scripts.research_contracts import (
        CLAIM_ID,
        EVIDENCE_ID,
        EVIDENCE_STATUSES,
        SCHEMA_VERSION,
        SHA256,
    )
except ModuleNotFoundError:  # Direct execution: python scripts/validate_evidence_registry.py
    from research_contracts import CLAIM_ID, EVIDENCE_ID, EVIDENCE_STATUSES, SCHEMA_VERSION, SHA256

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "docs" / "program_evidence_registry.json"

STATUSES = EVIDENCE_STATUSES
ROOT_FIELDS = {"schema_version", "generated_by", "statuses", "records"}
RECORD_REQUIRED = {"evidence_id", "experiment", "status", "claim_ids", "artifact_refs"}
RECORD_OPTIONAL = {"gate_ids", "supersedes", "source_sha256", "notes"}


def fail(message: str) -> None:
    raise ValueError(message)


def require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")
    return cast(str, value)


def require_unique_strings(value: object, label: str, pattern: re.Pattern[str] | None = None) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        fail(f"{label} must be a list of non-empty strings")
    strings = cast(list[str], value)
    if len(strings) != len(set(strings)):
        fail(f"{label} contains duplicate values")
    if pattern and any(pattern.fullmatch(item) is None for item in strings):
        fail(f"{label} contains an invalid identifier")
    return strings


def validate(path: Path = REGISTRY) -> dict:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {path}: {exc}")
    if not isinstance(payload, dict):
        fail("registry root must be an object")
    if set(payload) != ROOT_FIELDS:
        fail(f"registry root fields must be exactly {sorted(ROOT_FIELDS)}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        fail(f"schema_version must be '{SCHEMA_VERSION}'")
    require_string(payload.get("generated_by"), "generated_by")
    statuses = payload.get("statuses")
    if not isinstance(statuses, dict) or set(statuses) != STATUSES:
        fail("statuses must define exactly the six canonical statuses")
    for status, description in statuses.items():
        require_string(description, f"statuses.{status}")

    records = payload.get("records")
    if not isinstance(records, list):
        fail("records must be a list")
    seen: set[str] = set()
    supersession_edges: list[tuple[str, str]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            fail(f"records[{index}] must be an object")
        missing = RECORD_REQUIRED - set(record)
        if missing:
            fail(f"records[{index}] is missing required field: {sorted(missing)[0]}")
        unknown = set(record) - RECORD_REQUIRED - RECORD_OPTIONAL
        if unknown:
            fail(f"records[{index}] contains unknown field: {sorted(unknown)[0]}")
        evidence_id = require_string(record.get("evidence_id"), f"records[{index}].evidence_id")
        if EVIDENCE_ID.fullmatch(evidence_id) is None:
            fail(f"records[{index}].evidence_id has invalid format: {evidence_id}")
        if evidence_id in seen:
            fail(f"duplicate evidence_id: {evidence_id}")
        seen.add(evidence_id)
        require_string(record.get("experiment"), f"records[{index}].experiment")
        status = require_string(record.get("status"), f"records[{index}].status")
        if status not in STATUSES:
            fail(f"records[{index}].status is not canonical: {status}")
        claim_ids = require_unique_strings(record.get("claim_ids"), f"records[{index}].claim_ids", CLAIM_ID)
        if not claim_ids:
            fail(f"records[{index}].claim_ids must not be empty")
        artifact_refs = require_unique_strings(record.get("artifact_refs"), f"records[{index}].artifact_refs")
        if not artifact_refs:
            fail(f"records[{index}].artifact_refs must not be empty")
        if "gate_ids" in record:
            require_unique_strings(record["gate_ids"], f"records[{index}].gate_ids", CLAIM_ID)
        if "supersedes" in record and record["supersedes"] is not None:
            supersedes = require_string(record["supersedes"], f"records[{index}].supersedes")
            if EVIDENCE_ID.fullmatch(supersedes) is None:
                fail(f"records[{index}].supersedes has invalid format: {supersedes}")
            supersession_edges.append((evidence_id, supersedes))
        if "source_sha256" in record:
            source_sha256 = require_string(record["source_sha256"], f"records[{index}].source_sha256")
            if SHA256.fullmatch(source_sha256) is None:
                fail(f"records[{index}].source_sha256 must be a lowercase SHA-256 digest")
        if "notes" in record and not isinstance(record["notes"], str):
            fail(f"records[{index}].notes must be a string")
    for evidence_id, supersedes in supersession_edges:
        if supersedes not in seen:
            fail(f"{evidence_id} supersedes unknown evidence: {supersedes}")
        if supersedes == evidence_id:
            fail(f"{evidence_id} cannot supersede itself")
    return payload


def main() -> int:
    try:
        payload = validate()
    except ValueError as exc:
        print(f"[evidence] FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"[evidence] PASS: {len(payload['records'])} registry records; statuses={','.join(sorted(STATUSES))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
