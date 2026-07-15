#!/usr/bin/env python3
"""Validate declared public-artifact digest envelopes without third-party packages.

Envelopes hash tracked public payloads and preserve embedded raw-source receipts.
Clean-clone validation never claims access to ignored raw bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Never, cast

try:
    from scripts.research_contracts import CLAIM_ID, EVIDENCE_ID, SCHEMA_VERSION, SHA256
except ModuleNotFoundError:  # Direct execution
    from research_contracts import CLAIM_ID, EVIDENCE_ID, SCHEMA_VERSION, SHA256


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_NAME = "experiment_manifest.json"
ENVELOPE_SUFFIX = ".envelope.json"
REQUIRED_FIELDS = {
    "schema_version",
    "artifact_path",
    "artifact_sha256",
    "artifact_bytes",
    "producer_manifest_path",
    "source_verification",
    "raw_source_receipt",
    "included_fields",
    "omitted_fields",
    "expected_rows",
    "exported_rows",
    "generator_version",
    "public_safety",
    "claim_ids",
    "evidence_ids",
    "gate_verdict_paths",
    "adjudication",
}
RECEIPT_REQUIRED = {"artifact", "sha256", "bytes"}
RECEIPT_OPTIONAL = {"manifest_id", "implementation_fingerprint", "public_safe_export"}
PUBLIC_SAFETY_CLASSES = {"public_safe_summary", "public_safe_appendix"}
ADJUDICATIONS = {"bound", "unadjudicated"}


def fail(message: str) -> Never:
    raise ValueError(message)


def require_object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    return cast(dict[str, object], value)


def require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")
    return value


def require_int(value: object, label: str, *, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        fail(f"{label} must be an integer")
    if value < minimum:
        fail(f"{label} must be >= {minimum}")
    return value


def require_string_list(value: object, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        fail(f"{label} must be a list")
    if not allow_empty and not value:
        fail(f"{label} must not be empty")
    strings: list[str] = []
    for index, item in enumerate(value):
        strings.append(require_string(item, f"{label}[{index}]"))
    if len(strings) != len(set(strings)):
        fail(f"{label} contains duplicate values")
    return strings


def safe_repo_path(value: object, label: str, *, root: Path) -> tuple[str, Path]:
    relative = require_string(value, label)
    raw_path = Path(relative)
    if raw_path.is_absolute() or ".." in raw_path.parts:
        fail(f"{label} must be a safe repository-relative path: {relative}")
    if relative.endswith(ENVELOPE_SUFFIX):
        fail(f"{label} cannot point at an envelope sidecar: {relative}")
    resolved_root = root.resolve()
    resolved = (root / raw_path).resolve()
    if not resolved.is_relative_to(resolved_root):
        fail(f"{label} escapes the repository: {relative}")
    return relative, resolved


def tracked_files(root: Path) -> set[str]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        fail("git ls-files is required for envelope validation")
    return {path for path in completed.stdout.decode().split("\0") if path}


def require_tracked(relative: str, label: str, *, tracked: set[str]) -> None:
    if relative not in tracked:
        fail(f"{label} is not a tracked repository file: {relative}")


def discover_declared_envelopes(root: Path = ROOT) -> list[tuple[Path, str, str]]:
    """Return (manifest_path, artifact_path, envelope_path) triples."""

    declared: list[tuple[Path, str, str]] = []
    experiments = root / "experiments"
    if not experiments.exists():
        return declared
    for manifest_path in sorted(experiments.rglob(MANIFEST_NAME)):
        try:
            payload = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"cannot read {manifest_path}: {exc}")
        artifacts = payload.get("artifacts") if isinstance(payload, dict) else None
        if not isinstance(artifacts, list):
            continue
        for index, item in enumerate(artifacts):
            if not isinstance(item, dict) or "envelope_path" not in item:
                continue
            artifact_path = item.get("path")
            envelope_path = item.get("envelope_path")
            if not isinstance(artifact_path, str) or not isinstance(envelope_path, str):
                fail(
                    f"{manifest_path}: artifacts[{index}] envelope_path/path must be strings"
                )
            declared.append((manifest_path, artifact_path, envelope_path))
    return declared


def build_envelope_from_public_artifact(
    *,
    artifact_path: str,
    public_bytes: bytes,
    producer_manifest_path: str,
    claim_ids: list[str],
    evidence_ids: list[str],
    gate_verdict_paths: list[str],
    generator_version: str,
    included_fields: list[str],
    public_safety_classification: str = "public_safe_summary",
    public_safety_notes: str,
) -> dict[str, object]:
    """Bootstrap a receipt-only envelope from committed public JSON bytes."""

    public = json.loads(public_bytes)
    if not isinstance(public, dict):
        fail("public artifact must be a JSON object")
    source = public.get("source")
    coverage = public.get("coverage")
    if not isinstance(source, dict) or not isinstance(coverage, dict):
        fail("public artifact must embed source receipt and coverage")
    omitted = coverage.get("omitted_raw_fields")
    if not isinstance(omitted, list) or not omitted:
        fail("public artifact coverage.omitted_raw_fields must be a non-empty list")
    expected = coverage.get("expected_cells")
    exported = coverage.get("exported_cells")
    if not isinstance(expected, int) or not isinstance(exported, int):
        fail("public artifact coverage cell counts must be integers")
    cells = public.get("cells")
    if not isinstance(cells, list):
        fail("public artifact cells must be a list")
    if exported != len(cells) or expected != exported:
        fail("public artifact coverage counts do not match cells")

    adjudication = "bound" if claim_ids or evidence_ids or gate_verdict_paths else "unadjudicated"
    receipt = {
        "artifact": source["artifact"],
        "sha256": source["sha256"],
        "bytes": source["bytes"],
    }
    for optional in ("manifest_id", "implementation_fingerprint", "public_safe_export"):
        if optional in source:
            receipt[optional] = source[optional]

    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_path": artifact_path,
        "artifact_sha256": hashlib.sha256(public_bytes).hexdigest(),
        "artifact_bytes": len(public_bytes),
        "producer_manifest_path": producer_manifest_path,
        "source_verification": "receipt_only",
        "raw_source_receipt": receipt,
        "included_fields": included_fields,
        "omitted_fields": list(omitted),
        "expected_rows": expected,
        "exported_rows": exported,
        "generator_version": generator_version,
        "public_safety": {
            "classification": public_safety_classification,
            "notes": public_safety_notes,
        },
        "claim_ids": claim_ids,
        "evidence_ids": evidence_ids,
        "gate_verdict_paths": gate_verdict_paths,
        "adjudication": adjudication,
    }


def validate_envelope(
    path: Path,
    *,
    root: Path = ROOT,
    tracked: set[str] | None = None,
    expected_artifact_path: str | None = None,
    expected_producer_manifest: str | None = None,
) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {path}: {exc}")
    envelope = require_object(payload, "envelope")
    missing = REQUIRED_FIELDS - set(envelope)
    if missing:
        fail(f"envelope is missing required field: {sorted(missing)[0]}")
    unknown = set(envelope) - REQUIRED_FIELDS
    if unknown:
        fail(f"envelope contains unknown field: {sorted(unknown)[0]}")

    if envelope["schema_version"] != SCHEMA_VERSION:
        fail(f"envelope schema_version must be '{SCHEMA_VERSION}'")

    tracked_set = tracked if tracked is not None else tracked_files(root)
    relative_envelope = str(path.resolve().relative_to(root.resolve()))
    require_tracked(relative_envelope, "envelope path", tracked=tracked_set)

    artifact_rel, artifact_path = safe_repo_path(
        envelope["artifact_path"], "artifact_path", root=root
    )
    if expected_artifact_path is not None and artifact_rel != expected_artifact_path:
        fail(
            f"envelope artifact_path does not match manifest declaration: "
            f"{artifact_rel} != {expected_artifact_path}"
        )
    require_tracked(artifact_rel, "artifact_path", tracked=tracked_set)
    if not artifact_path.is_file():
        fail(f"artifact_path does not exist: {artifact_rel}")

    producer_rel, producer_path = safe_repo_path(
        envelope["producer_manifest_path"], "producer_manifest_path", root=root
    )
    if expected_producer_manifest is not None and producer_rel != expected_producer_manifest:
        fail(
            f"envelope producer_manifest_path does not match declaring manifest: "
            f"{producer_rel} != {expected_producer_manifest}"
        )
    require_tracked(producer_rel, "producer_manifest_path", tracked=tracked_set)
    if not producer_path.is_file():
        fail(f"producer_manifest_path does not exist: {producer_rel}")
    if producer_path.name != MANIFEST_NAME:
        fail(f"producer_manifest_path must be an experiment manifest: {producer_rel}")

    digest = require_string(envelope["artifact_sha256"], "artifact_sha256")
    if SHA256.fullmatch(digest) is None:
        fail("artifact_sha256 must be a SHA-256 digest")
    size = require_int(envelope["artifact_bytes"], "artifact_bytes")
    public_bytes = artifact_path.read_bytes()
    actual_digest = hashlib.sha256(public_bytes).hexdigest()
    if digest != actual_digest:
        fail(f"artifact_sha256 does not match tracked public bytes: {artifact_rel}")
    if size != len(public_bytes):
        fail(f"artifact_bytes does not match tracked public bytes: {artifact_rel}")

    if envelope["source_verification"] != "receipt_only":
        fail("source_verification must be receipt_only")

    receipt = require_object(envelope["raw_source_receipt"], "raw_source_receipt")
    receipt_unknown = set(receipt) - RECEIPT_REQUIRED - RECEIPT_OPTIONAL
    if RECEIPT_REQUIRED - set(receipt):
        fail(
            "raw_source_receipt is missing required field: "
            f"{sorted(RECEIPT_REQUIRED - set(receipt))[0]}"
        )
    if receipt_unknown:
        fail(f"raw_source_receipt contains unknown field: {sorted(receipt_unknown)[0]}")
    require_string(receipt["artifact"], "raw_source_receipt.artifact")
    receipt_digest = require_string(receipt["sha256"], "raw_source_receipt.sha256")
    if SHA256.fullmatch(receipt_digest) is None:
        fail("raw_source_receipt.sha256 must be a SHA-256 digest")
    require_int(receipt["bytes"], "raw_source_receipt.bytes")

    public = json.loads(public_bytes)
    if not isinstance(public, dict):
        fail(f"public artifact is not an object: {artifact_rel}")
    embedded = public.get("source")
    if not isinstance(embedded, dict):
        fail(f"public artifact is missing embedded source receipt: {artifact_rel}")
    for key in ("artifact", "sha256", "bytes"):
        if embedded.get(key) != receipt[key]:
            fail(
                f"raw_source_receipt.{key} does not match embedded public source receipt"
            )

    included = require_string_list(envelope["included_fields"], "included_fields")
    omitted = require_string_list(envelope["omitted_fields"], "omitted_fields")
    if set(included) & set(omitted):
        fail("included_fields and omitted_fields overlap")

    expected_rows = require_int(envelope["expected_rows"], "expected_rows")
    exported_rows = require_int(envelope["exported_rows"], "exported_rows")
    coverage = public.get("coverage")
    cells = public.get("cells")
    if not isinstance(coverage, dict) or not isinstance(cells, list):
        fail(f"public artifact missing coverage/cells: {artifact_rel}")
    if coverage.get("expected_cells") != expected_rows:
        fail("expected_rows does not match public coverage.expected_cells")
    if coverage.get("exported_cells") != exported_rows or exported_rows != len(cells):
        fail("exported_rows does not match public cells")
    if expected_rows != exported_rows:
        fail("expected_rows and exported_rows disagree")
    embedded_omitted = coverage.get("omitted_raw_fields")
    if not isinstance(embedded_omitted, list) or sorted(embedded_omitted) != sorted(omitted):
        fail("omitted_fields does not match public coverage.omitted_raw_fields")

    require_string(envelope["generator_version"], "generator_version")
    safety = require_object(envelope["public_safety"], "public_safety")
    if set(safety) != {"classification", "notes"}:
        fail("public_safety must contain only classification and notes")
    classification = require_string(safety["classification"], "public_safety.classification")
    if classification not in PUBLIC_SAFETY_CLASSES:
        fail(f"public_safety.classification is not canonical: {classification}")
    require_string(safety["notes"], "public_safety.notes")

    claim_ids = require_string_list(envelope["claim_ids"], "claim_ids", allow_empty=True)
    evidence_ids = require_string_list(
        envelope["evidence_ids"], "evidence_ids", allow_empty=True
    )
    gate_paths = require_string_list(
        envelope["gate_verdict_paths"], "gate_verdict_paths", allow_empty=True
    )
    for claim_id in claim_ids:
        if CLAIM_ID.fullmatch(claim_id) is None:
            fail(f"claim_ids contains an invalid identifier: {claim_id}")
    for evidence_id in evidence_ids:
        if EVIDENCE_ID.fullmatch(evidence_id) is None:
            fail(f"evidence_ids contains an invalid identifier: {evidence_id}")
    for index, gate_path in enumerate(gate_paths):
        gate_rel, gate_resolved = safe_repo_path(
            gate_path, f"gate_verdict_paths[{index}]", root=root
        )
        require_tracked(gate_rel, f"gate_verdict_paths[{index}]", tracked=tracked_set)
        if not gate_resolved.is_file():
            fail(f"gate_verdict_paths[{index}] does not exist: {gate_rel}")

    adjudication = require_string(envelope["adjudication"], "adjudication")
    if adjudication not in ADJUDICATIONS:
        fail(f"adjudication is not canonical: {adjudication}")
    if adjudication == "unadjudicated":
        if claim_ids or evidence_ids or gate_paths:
            fail("unadjudicated envelopes must use empty claim/evidence/gate arrays")
    elif not claim_ids or not evidence_ids:
        fail("bound envelopes require non-empty claim_ids and evidence_ids")

    return envelope


def validate_repository(root: Path = ROOT) -> list[dict[str, object]]:
    tracked = tracked_files(root)
    declared = discover_declared_envelopes(root)
    envelopes: list[dict[str, object]] = []
    declared_envelope_paths: set[str] = set()

    for manifest_path, artifact_path, envelope_path in declared:
        manifest_rel = str(manifest_path.resolve().relative_to(root.resolve()))
        envelope_rel = envelope_path
        raw_envelope = Path(envelope_path)
        if raw_envelope.is_absolute() or ".." in raw_envelope.parts:
            fail(f"envelope_path must be a safe repository-relative path: {envelope_path}")
        if not envelope_path.endswith(ENVELOPE_SUFFIX):
            fail(f"envelope_path must end with {ENVELOPE_SUFFIX}: {envelope_path}")
        if envelope_path == artifact_path:
            fail(f"envelope_path cannot equal artifact path: {envelope_path}")
        resolved = (root / raw_envelope).resolve()
        if not resolved.is_relative_to(root.resolve()):
            fail(f"envelope_path escapes the repository: {envelope_path}")
        require_tracked(envelope_rel, "envelope_path", tracked=tracked)
        declared_envelope_paths.add(envelope_rel)
        envelopes.append(
            validate_envelope(
                resolved,
                root=root,
                tracked=tracked,
                expected_artifact_path=artifact_path,
                expected_producer_manifest=manifest_rel,
            )
        )

    orphaned = sorted(
        path
        for path in tracked
        if path.endswith(ENVELOPE_SUFFIX) and path not in declared_envelope_paths
    )
    if orphaned:
        fail(f"undeclared envelope sidecar: {orphaned[0]}")
    return envelopes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "envelopes",
        nargs="*",
        type=Path,
        help="optional envelope JSON files (default: discover via manifest envelope_path)",
    )
    args = parser.parse_args(argv)
    try:
        if args.envelopes:
            tracked = tracked_files(ROOT)
            for path in args.envelopes:
                validate_envelope(path, tracked=tracked)
                print(f"[public-envelope] PASS: {path}")
        else:
            envelopes = validate_repository()
            print(f"[public-envelope] PASS: {len(envelopes)} declared envelopes")
    except ValueError as exc:
        print(f"[public-envelope] FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
