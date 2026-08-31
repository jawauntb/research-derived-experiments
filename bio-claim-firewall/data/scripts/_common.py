"""Shared helpers for the data/scripts/download_*.py and build_manifests.py scripts.

Stdlib-only (urllib.request, gzip, json, csv, hashlib) plus `evidence.hashing`,
which is itself pure stdlib -- imported, never reimplemented, so the hashes
these scripts write can never drift from what `evidence/loader.py` verifies
at load time (same pattern as `tests/fixtures/synthetic_world/recompute_hashes.py`).

Every download script:
  1. fetches raw data into data/raw/<source>/
  2. writes the processed snapshot into data/ontology_snapshots/<source>/
     or data/evidence_records/<source>/records.jsonl
  3. writes data/LICENSES/<source>.txt (the source's own license text)
  4. writes an initial data/manifests/<source>.{yaml,json} pair with a
     correct sha256 (computed the same way evidence/loader.py verifies it)

`build_manifests.py` re-walks every manifest afterwards and recomputes
sha256/row_count in place -- a idempotent integrity pass, not a second
source of truth.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_ROOT = Path(__file__).resolve().parent.parent  # .../bio-claim-firewall/data
BCF_ROOT = DATA_ROOT.parent  # .../bio-claim-firewall
SRC_DIR = BCF_ROOT / "src"
for _p in (str(BCF_ROOT), str(SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from evidence.hashing import sha256_bytes, sha256_dir, sha256_file  # noqa: E402  (path bootstrap above)

RAW_DIR = DATA_ROOT / "raw"
ONTOLOGY_DIR = DATA_ROOT / "ontology_snapshots"
EVIDENCE_DIR = DATA_ROOT / "evidence_records"
MANIFESTS_DIR = DATA_ROOT / "manifests"
LICENSES_DIR = DATA_ROOT / "LICENSES"

USER_AGENT = "bio-claim-firewall-pilot-world/0.1 (research; contact: jawaun@generalintelligencecompany.com)"

_MANIFEST_FIELD_ORDER = (
    "schema_version",
    "source",
    "source_url",
    "retrieved_at",
    "license",
    "sha256",
    "row_count",
    "preprocessing_cmd",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    print(f"[data] {msg}", file=sys.stderr)


def fetch_bytes(url: str, *, timeout: int = 60) -> bytes:
    """GET url, stdlib-only, with a descriptive User-Agent. Raises on non-2xx."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (research script, allowlisted sources)
        return resp.read()


def fetch_to_file(url: str, dest: Path, *, timeout: int = 60) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = fetch_bytes(url, timeout=timeout)
    dest.write_bytes(data)
    return dest


def fetch_json(url: str, *, timeout: int = 30) -> Any:
    return json.loads(fetch_bytes(url, timeout=timeout))


def write_license_text(
    source_label: str, header: str, source_url: str, body: str
) -> Path:
    LICENSES_DIR.mkdir(parents=True, exist_ok=True)
    path = LICENSES_DIR / f"{source_label}.txt"
    path.write_text(
        f"{header}\nSource: {source_url}\n\n{body.strip()}\n", encoding="utf-8"
    )
    return path


def write_manifest_pair(source: str, fields: dict[str, Any]) -> None:
    """Write manifests/<source>.yaml (flat key: value, no pyyaml needed) + .json sibling."""
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    for key in _MANIFEST_FIELD_ORDER:
        if key not in fields or fields[key] is None:
            continue
        value = fields[key]
        if isinstance(value, str):
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}: "{escaped}"')
        else:
            lines.append(f"{key}: {value}")
    (MANIFESTS_DIR / f"{source}.yaml").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    json_fields = {
        k: fields[k]
        for k in _MANIFEST_FIELD_ORDER
        if k in fields and fields[k] is not None
    }
    (MANIFESTS_DIR / f"{source}.json").write_text(
        json.dumps(json_fields, indent=2) + "\n", encoding="utf-8"
    )


def ontology_row_count(source: str) -> int:
    curies_path = ONTOLOGY_DIR / source / "curies.txt"
    return len(
        [
            ln
            for ln in curies_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
    )


def write_ontology_manifest(
    *,
    source: str,
    source_url: str,
    retrieved_at: str,
    license_tag: str,
    preprocessing_cmd: str,
) -> str:
    """Compute sha256_dir over ontology_snapshots/<source>/ (same fn loader uses) and write the manifest."""
    onto_dir = ONTOLOGY_DIR / source
    digest = sha256_dir(onto_dir)
    row_count = ontology_row_count(source)
    write_manifest_pair(
        source,
        {
            "schema_version": "0.1.0",
            "source": source,
            "source_url": source_url,
            "retrieved_at": retrieved_at,
            "license": license_tag,
            "sha256": digest,
            "row_count": row_count,
            "preprocessing_cmd": preprocessing_cmd,
        },
    )
    log(f"manifest written: {source} sha256_dir={digest} row_count={row_count}")
    return digest


def write_evidence_manifest(
    *,
    source: str,
    source_url: str,
    retrieved_at: str,
    license_tag: str,
    preprocessing_cmd: str,
) -> str:
    """Compute sha256_file over evidence_records/<source>/records.jsonl and write the manifest."""
    records_path = EVIDENCE_DIR / source / "records.jsonl"
    digest = sha256_file(records_path)
    row_count = len(
        [
            ln
            for ln in records_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
    )
    write_manifest_pair(
        source,
        {
            "schema_version": "0.1.0",
            "source": source,
            "source_url": source_url,
            "retrieved_at": retrieved_at,
            "license": license_tag,
            "sha256": digest,
            "row_count": row_count,
            "preprocessing_cmd": preprocessing_cmd,
        },
    )
    log(f"manifest written: {source} sha256_file={digest} row_count={row_count}")
    return digest


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def record_hash16(record_without_id: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(record_without_id).encode("utf-8"))[:16]


def load_hgnc_symbol_map() -> dict[str, str]:
    """{symbol -> 'HGNC:<id>'} from the already-downloaded hgnc snapshot's labels.jsonl.

    Returns {} if the hgnc snapshot has not been built yet -- callers must
    handle that (skip / warn), never invent a mapping.
    """
    labels_path = None
    for candidate in ONTOLOGY_DIR.glob("hgnc.*/labels.jsonl"):
        labels_path = candidate
        break
    if labels_path is None or not labels_path.is_file():
        return {}
    mapping: dict[str, str] = {}
    for line in labels_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        mapping[row["label"]] = row["curie"]
    return mapping


__all__ = [
    "BCF_ROOT",
    "DATA_ROOT",
    "EVIDENCE_DIR",
    "LICENSES_DIR",
    "MANIFESTS_DIR",
    "ONTOLOGY_DIR",
    "RAW_DIR",
    "canonical_json",
    "fetch_bytes",
    "fetch_json",
    "fetch_to_file",
    "load_hgnc_symbol_map",
    "log",
    "now_iso",
    "ontology_row_count",
    "record_hash16",
    "sha256_bytes",
    "sha256_dir",
    "sha256_file",
    "write_evidence_manifest",
    "write_license_text",
    "write_manifest_pair",
    "write_ontology_manifest",
]
