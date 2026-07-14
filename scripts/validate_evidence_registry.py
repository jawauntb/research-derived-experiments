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

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "docs" / "program_evidence_registry.json"

STATUSES = {
    "pass",
    "fail",
    "inconclusive",
    "not_run",
    "superseded",
    "retired",
}
EVIDENCE_ID = re.compile(r"^EVID-[A-Z0-9][A-Z0-9_-]{2,63}$")
CLAIM_ID = re.compile(r"^[A-Z][A-Z0-9_-]{2,63}$")


def fail(message: str) -> None:
    raise ValueError(message)


def require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")
    return value


def require_unique_strings(value: object, label: str, pattern: re.Pattern[str] | None = None) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        fail(f"{label} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        fail(f"{label} contains duplicate values")
    if pattern and any(pattern.fullmatch(item) is None for item in value):
        fail(f"{label} contains an invalid identifier")
    return value


def validate(path: Path = REGISTRY) -> dict:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {path}: {exc}")
    if not isinstance(payload, dict):
        fail("registry root must be an object")
    if payload.get("schema_version") != "1.0":
        fail("schema_version must be '1.0'")
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
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            fail(f"records[{index}] must be an object")
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
