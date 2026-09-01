"""Shared acquisition, hashing, and contract-preflight primitives.

This module deliberately has no project dependencies.  Network acquisition is
an explicit caller action; importing or preflighting a contract never fetches a
source and never treats a rolling re-fetch as corruption of a retained world.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping

CONTRACT_STATES = frozenset(
    {"RESEARCHED", "RESEARCHED_DEFERRED", "FROZEN", "PREFLIGHT_PASSED", "EVALUATED", "ADMITTED", "WITHHELD_LICENSE", "WITHHELD_INTEGRITY", "WITHHELD_SCIENTIFIC"}
)
SOURCE_KINDS = frozenset({"immutable_release", "rolling_snapshot"})
GATE_STATES = frozenset({"pass", "fail", "unknown", "not_run"})
REQUIRED_CONTRACT_FIELDS = ("schema_version", "world_id", "version", "rank", "modality", "state", "sources", "fatal_gates", "evidence_paths")


class ContractError(ValueError):
    """The source contract is structurally invalid."""


class SourceIntegrityError(RuntimeError):
    """A downloaded byte sequence cannot be admitted to the retained cache."""

    def __init__(self, code: str, message: str, *, new_version_required: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.new_version_required = new_version_required


def canonical_json(value: Any) -> bytes:
    """Stable UTF-8 JSON bytes used for contract and derived-artifact digests."""
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def contract_digest(contract: Mapping[str, Any]) -> str:
    """Digest a contract independent of its optional self-digest field."""
    payload = {key: value for key, value in contract.items() if key not in {"contract_sha256", "generated_at"}}
    return sha256_bytes(canonical_json(payload))


def load_contract(path: Path) -> dict[str, Any]:
    path = Path(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read JSON contract {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"contract {path} must contain an object")
    validate_contract(value, path=path)
    return value


def validate_contract(contract: Mapping[str, Any], *, path: Path | None = None) -> None:
    label = str(path or contract.get("world_id", "<contract>"))
    missing = [field for field in REQUIRED_CONTRACT_FIELDS if field not in contract]
    if missing:
        raise ContractError(f"{label}: missing required field(s): {', '.join(missing)}")
    if not isinstance(contract["world_id"], str) or not contract["world_id"]:
        raise ContractError(f"{label}: world_id must be a non-empty string")
    if not isinstance(contract["version"], str) or not contract["version"]:
        raise ContractError(f"{label}: version must be a non-empty string")
    if isinstance(contract["rank"], bool) or not isinstance(contract["rank"], int) or contract["rank"] < 1:
        raise ContractError(f"{label}: rank must be a positive integer")
    if contract["state"] not in CONTRACT_STATES:
        raise ContractError(f"{label}: unsupported state {contract['state']!r}")
    sources = contract["sources"]
    if not isinstance(sources, list) or not sources:
        raise ContractError(f"{label}: sources must be a non-empty list")
    seen_sources: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ContractError(f"{label}: every source must be an object")
        for field in ("source_id", "official_url", "source_kind", "license", "custody", "refresh_cadence", "staleness_horizon"):
            if field not in source:
                raise ContractError(f"{label}: source missing {field!r}")
        source_id = source["source_id"]
        if not isinstance(source_id, str) or not source_id or source_id in seen_sources:
            raise ContractError(f"{label}: source_id must be unique and non-empty")
        seen_sources.add(source_id)
        if not isinstance(source["official_url"], str) or not source["official_url"].startswith("https://"):
            raise ContractError(f"{label}: official_url must be an HTTPS URL")
        if source["source_kind"] not in SOURCE_KINDS:
            raise ContractError(f"{label}: unsupported source_kind {source['source_kind']!r}")
        license_info = source["license"]
        if not isinstance(license_info, dict) or not {"id", "status", "reference_url", "redistribution", "commercial_demo"}.issubset(license_info):
            raise ContractError(f"{label}: license must include id/status/reference_url/redistribution/commercial_demo")
        if license_info["status"] not in {"verified", "unknown", "failed"}:
            raise ContractError(f"{label}: invalid license status")
    gates = contract["fatal_gates"]
    if not isinstance(gates, list) or not gates:
        raise ContractError(f"{label}: fatal_gates must be a non-empty list")
    gate_ids: set[str] = set()
    for gate in gates:
        if not isinstance(gate, dict) or not isinstance(gate.get("id"), str) or gate["id"] in gate_ids:
            raise ContractError(f"{label}: fatal gates need unique object ids")
        gate_ids.add(gate["id"])
        if gate.get("status") not in GATE_STATES:
            raise ContractError(f"{label}: invalid status for gate {gate['id']!r}")
    if not isinstance(contract["evidence_paths"], dict):
        raise ContractError(f"{label}: evidence_paths must be an object")


def preflight_contract(contract_path: Path) -> dict[str, Any]:
    """Return a deterministic, no-network readiness record for one contract."""
    contract = load_contract(contract_path)
    gates = tuple(gate["status"] for gate in contract["fatal_gates"])
    failures = [gate["id"] for gate in contract["fatal_gates"] if gate["status"] == "fail"]
    unknown = [gate["id"] for gate in contract["fatal_gates"] if gate["status"] in {"unknown", "not_run"}]
    return {
        "world_id": contract["world_id"],
        "version": contract["version"],
        "state": contract["state"],
        "contract_sha256": contract_digest(contract),
        "fatal_gate_failures": failures,
        "fatal_gate_unknown_or_not_run": unknown,
        "ready_for_acquisition": not failures and not unknown,
        "source_count": len(contract["sources"]),
        "gate_statuses": list(gates),
    }


def acquire_bytes(
    url: str,
    destination: Path,
    *,
    expected_sha256: str | None,
    source_kind: str,
    fetcher: Callable[[str], bytes] | None = None,
) -> dict[str, Any]:
    """Fetch or reuse bytes without silently replacing a retained snapshot.

    ``fetcher`` is injectable so fixture tests never need network access.
    For immutable releases, a changed cache is integrity failure.  For rolling
    snapshots, changed bytes are drift requiring a new version and are never
    written over the retained file.
    """
    if source_kind not in SOURCE_KINDS:
        raise ValueError(f"unsupported source_kind {source_kind!r}")
    destination = Path(destination)
    if destination.exists():
        existing_sha = sha256_file(destination)
        if expected_sha256 and existing_sha != expected_sha256:
            code = "IMMUTABLE_DRIFT" if source_kind == "immutable_release" else "ROLLING_DRIFT_NEW_VERSION_REQUIRED"
            raise SourceIntegrityError(code, f"cached bytes at {destination} do not match expected digest", new_version_required=source_kind == "rolling_snapshot")
        return {"status": "cached", "path": str(destination), "sha256": existing_sha, "changed": False}
    if fetcher is None:
        def fetcher(target: str) -> bytes:
            with urllib.request.urlopen(target, timeout=60) as response:  # noqa: S310 - URL is a caller-selected official source
                return response.read()
    payload = fetcher(url)
    if not isinstance(payload, bytes):
        raise TypeError("fetcher must return bytes")
    digest = sha256_bytes(payload)
    if expected_sha256 and digest != expected_sha256:
        raise SourceIntegrityError("FETCH_HASH_MISMATCH", f"downloaded bytes from {url} do not match expected digest")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=f".{destination.name}.", dir=destination.parent, delete=False) as handle:
        handle.write(payload)
        temp_path = Path(handle.name)
    os.replace(temp_path, destination)
    return {"status": "fetched", "path": str(destination), "sha256": digest, "changed": True}


def fixture_manifest(root: Path) -> dict[str, Any]:
    """Build a stable inventory for a bounded fixture directory."""
    root = Path(root)
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and item.name != "fixture-manifest.json"):
        files.append({"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    payload = {"schema_version": "1.0.0", "files": files}
    return {**payload, "sha256": sha256_bytes(canonical_json(payload))}


__all__ = ["CONTRACT_STATES", "ContractError", "SourceIntegrityError", "acquire_bytes", "canonical_json", "contract_digest", "fixture_manifest", "load_contract", "preflight_contract", "sha256_bytes", "sha256_file", "validate_contract"]
