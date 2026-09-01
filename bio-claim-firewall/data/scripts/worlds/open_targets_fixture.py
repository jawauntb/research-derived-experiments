#!/usr/bin/env python3
"""Build the Open Targets 26.06 fixture from one official GraphQL response.

Raw responses stay outside git. The committed output contains only three exact,
source-specific association rows and the SHA-256 of the source response.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from worlds.open_targets.adapter import load_fixture

ENDPOINT = "https://api.platform.opentargets.org/api/v4/graphql"
TARGET_ID = "ENSG00000141510"
RELEASE = "26.06"
RETRIEVED_AT = "2026-09-01T22:31:00Z"
QUERY = """query BoundedAssociations($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    associatedDiseases(page: {index: 0, size: 5}) {
      rows { disease { id name } score datasourceScores { id score } }
    }
  }
}"""
PLAN = (
    ("MONDO_0018875", "Li-Fraumeni syndrome", "uniprot_variants"),
    ("MONDO_0007256", "hepatocellular carcinoma", "intogen"),
    ("MONDO_0010150", "head and neck squamous cell carcinoma", "clinical_precedence"),
)


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def fetch(destination: Path) -> Path:
    body = _canonical({"query": QUERY, "variables": {"ensemblId": TARGET_ID}})
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "Bio-Claim-Firewall/0.1"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return destination


def build(source: Path, destination: Path) -> dict[str, object]:
    raw = source.read_bytes()
    payload = json.loads(raw)
    if payload.get("errors"):
        raise ValueError(f"Open Targets returned errors: {payload['errors']}")
    target = payload.get("data", {}).get("target")
    if not isinstance(target, dict) or target.get("id") != TARGET_ID or target.get("approvedSymbol") != "TP53":
        raise ValueError("Open Targets target identity changed")
    rows = target.get("associatedDiseases", {}).get("rows")
    if not isinstance(rows, list):
        raise TypeError("Open Targets association rows are missing")
    by_disease = {row.get("disease", {}).get("id"): row for row in rows if isinstance(row, dict)}
    records: list[dict[str, object]] = []
    for disease_id, disease_name, datasource in PLAN:
        row = by_disease.get(disease_id)
        if not isinstance(row, dict) or row.get("disease", {}).get("name") != disease_name:
            raise ValueError(f"planned disease disappeared or changed: {disease_id}")
        scores = {item.get("id"): item.get("score") for item in row.get("datasourceScores", [])}
        score = scores.get(datasource)
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise TypeError(f"planned datasource disappeared: {disease_id}/{datasource}")
        records.append(
            {
                "record_id": f"ot:{TARGET_ID}:{disease_id}:{datasource}",
                "source": "open-targets-graphql-26-06",
                "target_id": TARGET_ID,
                "target_symbol": "TP53",
                "disease_id": disease_id,
                "disease_name": disease_name,
                "evidence_source": datasource,
                "release": RELEASE,
                "score": score,
                "score_definition": "Open Targets 26.06 source-defined datasource association score.",
            }
        )
    fixture: dict[str, object] = {
        "schema_version": "open-targets-association-ledger-0.1",
        "world_id": "open-targets",
        "version": RELEASE,
        "source_hashes": {"open-targets-graphql-26-06": hashlib.sha256(raw).hexdigest()},
        "records": records,
        "provenance": {
            "endpoint": ENDPOINT,
            "retrieved_at": RETRIEVED_AT,
            "query_sha256": hashlib.sha256(QUERY.encode()).hexdigest(),
            "raw_response_committed": False,
        },
    }
    integrity_payload = {key: fixture[key] for key in ("schema_version", "world_id", "version", "source_hashes", "records")}
    fixture["integrity_sha256"] = _digest(integrity_payload)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    load_fixture(destination)
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    source = args.source or args.destination.parent / "raw" / "open-targets-tp53.json"
    if args.source is None:
        fetch(source)
    fixture = build(source, args.destination)
    print(json.dumps({"record_count": len(fixture["records"]), "source_hashes": fixture["source_hashes"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
