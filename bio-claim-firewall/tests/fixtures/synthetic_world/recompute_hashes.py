#!/usr/bin/env python3
"""Regenerate every derived hash in the synthetic_world fixture pack.

Run this any time a fixture source file under `synthetic_world/` changes:

    python3 tests/fixtures/synthetic_world/recompute_hashes.py

What it does, in order:

1. For every `manifests/*.yaml`, reads its `snapshot_file:` line, computes
   `sha256(snapshot_file)` and rewrites the manifest's `sha256:` line in
   place (all other lines/formatting untouched).

2. For `perturbseq_v_test` specifically, additionally rebuilds
   `evidence_records/perturbseq_v_test/records.jsonl` from
   `evidence_records/perturbseq_v_test/raw_source.jsonl`:

   - Every record's `snapshot_hash` is set to `sha256(raw_source.jsonl)`
     (the same value written into the manifest's `sha256:` field).
   - Rows are processed in file order (R1..R6). A `contradicts` entry of
     the form `"$ref:<row_label>"` is resolved to the already-computed
     `evidence_id` of that earlier row (row order is chosen so every
     `$ref` points backward -- this is what makes the id computation
     non-circular).
   - Each record's `evidence_id` is computed as
     `f"{source}:{sha256(canonical_json(record_without_evidence_id))[:16]}"`
     where `canonical_json(obj) = json.dumps(obj, sort_keys=True,
     separators=(",", ":"))`. The `evidence_id` field itself is therefore
     never part of its own hash input.
   - Writes `evidence_records/perturbseq_v_test/RECORD_ID_MAP.md`
     documenting exactly which raw row produced which evidence_id, so the
     mapping used by tests/fixtures/claims/*.json is auditable without
     re-running the script.

This script uses only the standard library (hashlib, json, re, pathlib) so
it runs identically under a plain `python3` and under `uv run --no-sync`,
where third-party packages such as PyYAML are not guaranteed importable.
Manifests are therefore treated as flat `key: value` lines and rewritten
with a targeted regex substitution rather than a full YAML round-trip.

# FIXTURES-DECISION: manifest sha256 covers exactly one `snapshot_file`
# per source (the raw, hand-authored file). Companion files that are not
# independently re-fetched from an upstream (hgnc aliases.jsonl,
# cellontology cell_ontology.jsonl, and the derived records.jsonl for
# perturbseq) are documented in the manifest's `preprocessing_cmd` instead
# of being folded into the same hash, so each manifest's sha256 has one
# unambiguous referent.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent  # .../tests/fixtures/synthetic_world
MANIFESTS_DIR = ROOT / "manifests"
PERTURBSEQ_DIR = ROOT / "evidence_records" / "perturbseq_v_test"
RAW_SOURCE = PERTURBSEQ_DIR / "raw_source.jsonl"
RECORDS_OUT = PERTURBSEQ_DIR / "records.jsonl"
RECORD_ID_MAP_OUT = PERTURBSEQ_DIR / "RECORD_ID_MAP.md"

SHA256_LINE_RE = re.compile(r'^sha256:\s*.*$', re.MULTILINE)
SNAPSHOT_FILE_LINE_RE = re.compile(r'^snapshot_file:\s*(\S+)\s*$', re.MULTILINE)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def update_manifest_sha256(manifest_path: Path) -> tuple[str, str]:
    """Rewrite `sha256:` in manifest_path to match its snapshot_file. Returns (snapshot_file, sha256)."""
    text = manifest_path.read_text()
    m = SNAPSHOT_FILE_LINE_RE.search(text)
    if not m:
        raise SystemExit(f"{manifest_path}: no `snapshot_file:` line found")
    snapshot_rel = m.group(1)
    snapshot_path = ROOT / snapshot_rel
    if not snapshot_path.is_file():
        raise SystemExit(f"{manifest_path}: snapshot_file {snapshot_rel} does not exist")
    digest = sha256_file(snapshot_path)
    new_text, n = SHA256_LINE_RE.subn(f'sha256: "{digest}"', text, count=1)
    if n != 1:
        raise SystemExit(f"{manifest_path}: no `sha256:` line found to rewrite")
    manifest_path.write_text(new_text)
    return snapshot_rel, digest


def build_perturbseq_records(raw_sha256: str) -> list[dict]:
    raw_rows = []
    with RAW_SOURCE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw_rows.append(json.loads(line))

    id_by_label: dict[str, str] = {}
    built_records: list[dict] = []

    for row in raw_rows:
        row = dict(row)  # shallow copy
        row_label = row.pop("row_label")
        source = row["source"]

        # Resolve $ref:<label> contradicts pointers to already-computed ids.
        resolved_contradicts = []
        for c in row.get("contradicts", []):
            if isinstance(c, str) and c.startswith("$ref:"):
                ref_label = c[len("$ref:"):]
                if ref_label not in id_by_label:
                    raise SystemExit(
                        f"{row_label}: contradicts $ref:{ref_label} but that row "
                        f"has not been processed yet (rows must be ordered so every "
                        f"$ref points backward)"
                    )
                resolved_contradicts.append(id_by_label[ref_label])
            else:
                resolved_contradicts.append(c)
        row["contradicts"] = resolved_contradicts

        # Every record in this ledger was extracted from the same raw file.
        row["snapshot_hash"] = raw_sha256

        # Canonicalize *without* evidence_id (the field being computed) and
        # derive the id from that canonical form.
        record_hash = hashlib.sha256(canonical_json(row).encode("utf-8")).hexdigest()[:16]
        evidence_id = f"{source}:{record_hash}"

        final_record = {"evidence_id": evidence_id, **row}
        id_by_label[row_label] = evidence_id
        built_records.append((row_label, final_record))

    return built_records


def main() -> int:
    manifest_paths = sorted(MANIFESTS_DIR.glob("*.yaml"))
    if not manifest_paths:
        raise SystemExit(f"no manifests found under {MANIFESTS_DIR}")

    updated = {}
    for manifest_path in manifest_paths:
        snapshot_rel, digest = update_manifest_sha256(manifest_path)
        updated[manifest_path.name] = (snapshot_rel, digest)
        print(f"[manifest] {manifest_path.name}: sha256({snapshot_rel}) = {digest}")

    perturbseq_manifest = MANIFESTS_DIR / "perturbseq_v_test.yaml"
    if perturbseq_manifest.name not in updated:
        raise SystemExit("perturbseq_v_test.yaml manifest missing")
    _, raw_sha256 = updated[perturbseq_manifest.name]

    built = build_perturbseq_records(raw_sha256)

    with RECORDS_OUT.open("w") as f:
        for _label, record in built:
            f.write(canonical_json(record))
            f.write("\n")
    print(f"[records] wrote {len(built)} records to {RECORDS_OUT}")

    lines = [
        "# Perturb-seq fixture record id map",
        "",
        "Auto-generated by `recompute_hashes.py`. Do not hand-edit.",
        "",
        f"Raw source: `raw_source.jsonl`, sha256 = `{raw_sha256}`",
        "(this is also `snapshot_hash` on every record below, and `manifests/perturbseq_v_test.yaml`'s `sha256`).",
        "",
        "| row_label | evidence_id | subject -> object | relation-relevant summary |",
        "|---|---|---|---|",
    ]
    summaries = {
        "R1": "BRCA1 -> KRAS, CRISPRi, K562, resting, positive (interventional)",
        "R2": "BRCA1 -> KRAS, CRISPRi, RPE1, resting, positive (interventional; pairs with R1 for R-CAUS-04 established)",
        "R3": "TP53 ~ CDKN1A, bulk-RNA-seq co-expression, K562, IFNG_stimulated, positive pearson_r (observational)",
        "R4": "TP53 -> CDKN1A, CRISPRi, K562, resting, negative (interventional; different context than R3, no contradicts link)",
        "R5": "TP53 -> CDKN1A, CRISPRi, K562, IFNG_stimulated, negative (interventional; contradicts R3, same context)",
        "R6": "IL6 -- IL6R, co-IP physical_interaction, cell_type=CL:0000000, no perturbation",
    }
    for label, record in built:
        subj = record["subject"]["id"]
        obj = record["object"]["id"]
        lines.append(f"| {label} | `{record['evidence_id']}` | {subj} -> {obj} | {summaries.get(label, '')} |")
    lines.append("")
    RECORD_ID_MAP_OUT.write_text("\n".join(lines))
    print(f"[docs] wrote {RECORD_ID_MAP_OUT}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
