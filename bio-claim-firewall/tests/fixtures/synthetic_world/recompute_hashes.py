#!/usr/bin/env python3
"""Regenerate every derived hash, id, and manifest in the synthetic_world fixture pack.

Run this any time a fixture source file under `synthetic_world/` changes:

    python3 tests/fixtures/synthetic_world/recompute_hashes.py
    # or:
    uv run --no-sync python bio-claim-firewall/tests/fixtures/synthetic_world/recompute_hashes.py

What it does, in order:

1. For every `ontology_snapshots/<source>/` directory, computes
   `evidence.hashing.sha256_dir(<source>/)` -- the SAME function
   `evidence.loader._load_ontology_source` uses to verify a manifest --
   over every regular file directly inside that directory (`curies.txt`,
   and `labels.jsonl` / `aliases.jsonl` / `cell_ontology.jsonl` when
   present), and rewrites that source's manifest `sha256` + `row_count`
   (row_count = number of non-blank lines in `curies.txt`).

2. For `perturbseq_v_test`, rebuilds `evidence_records/perturbseq_v_test/
   records.jsonl` from `raw_source.jsonl`:

   - Every record's `snapshot_hash` is set to `sha256(raw_source.jsonl)`
     -- raw-file provenance. This is a *record-level* fact, independent of
     the manifest's own `sha256` (see below), and is never checked by
     `evidence/loader.py` (only `R-CITE-02` in `src/rules/` reads it).
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

   The `perturbseq_v_test` manifest's own `sha256` is then set to
   `evidence.hashing.sha256_file(records.jsonl)` -- the SAME function
   `evidence.loader._load_evidence_source` uses -- over the *built*
   `records.jsonl`, not `raw_source.jsonl`.

3. Rewrites every `manifests/<source>.yaml` in place (preserving every
   field except `sha256` and `row_count`, which are recomputed here) and
   emits a `manifests/<source>.json` sibling carrying the same fields, so
   `evidence/loader.py` can ingest a manifest even in an environment where
   `pyyaml` is not importable (it accepts both `.yaml`/`.yml` and `.json`;
   see `evidence/manifest.py`).

This script uses only the standard library plus `evidence.hashing` (the
real, authoritative hashing module -- imported, never reimplemented, so
there is no drift between what this script computes and what
`evidence/loader.py` verifies at load time) so it runs identically under a
plain `python3` and under `uv run --no-sync`, where third-party packages
such as PyYAML are not guaranteed importable.

Idempotent: running this script twice in a row with no source file changes
produces byte-identical output the second time.

# FIXTURE-CLEANUP-DECISION: a manifest's `sha256` now covers the SAME
# bytes `evidence/loader.py` actually hashes to verify that source --
# `sha256_dir` over the whole `ontology_snapshots/<source>/` directory for
# an ontology source, `sha256_file` over `records.jsonl` for the evidence
# source -- rather than a single hand-picked upstream `snapshot_file`
# (the old scheme, which `load_bundle` could never verify byte-for-byte;
# see the former `tests/rules/conftest.py` repair workaround this
# migration deletes). The `snapshot_file` manifest field is dropped
# entirely.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent  # .../tests/fixtures/synthetic_world
_BCF_ROOT = ROOT.parents[2]  # .../bio-claim-firewall
_SRC = _BCF_ROOT / "src"
for _p in (str(_BCF_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# The real, authoritative hashing functions -- imported, not reimplemented,
# so this script can never drift from what evidence/loader.py verifies.
from evidence.hashing import sha256_bytes, sha256_dir, sha256_file  # noqa: E402

MANIFESTS_DIR = ROOT / "manifests"
ONTOLOGY_DIR = ROOT / "ontology_snapshots"
PERTURBSEQ_DIR = ROOT / "evidence_records" / "perturbseq_v_test"
RAW_SOURCE = PERTURBSEQ_DIR / "raw_source.jsonl"
RECORDS_OUT = PERTURBSEQ_DIR / "records.jsonl"
RECORD_ID_MAP_OUT = PERTURBSEQ_DIR / "RECORD_ID_MAP.md"

MANIFEST_LINE_RE = re.compile(r'^([a-zA-Z0-9_]+):\s*(.*)$')

# Field order for the flat `.yaml` manifest (and the key order the `.json`
# sibling is written in). `snapshot_file` is deliberately absent -- see the
# FIXTURE-CLEANUP-DECISION above.
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


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _parse_flat_manifest(path: Path) -> dict[str, object]:
    """Parse this fixture pack's flat `key: value` manifest lines (no pyyaml)."""
    out: dict[str, object] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = MANIFEST_LINE_RE.match(line)
        if not m:
            raise SystemExit(f"{path}: could not parse manifest line: {line!r}")
        key, value = m.group(1), m.group(2).strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif key == "row_count":
            value = int(value)
        out[key] = value
    return out


def _write_manifest_pair(source: str, fields: dict[str, object]) -> None:
    """Write `manifests/<source>.yaml` (flat key: value) and `<source>.json`."""
    lines = []
    for key in _MANIFEST_FIELD_ORDER:
        if key not in fields or fields[key] is None:
            continue
        value = fields[key]
        if isinstance(value, str):
            lines.append(f'{key}: "{value}"')
        else:
            lines.append(f"{key}: {value}")
    yaml_path = MANIFESTS_DIR / f"{source}.yaml"
    yaml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    json_fields = {k: fields[k] for k in _MANIFEST_FIELD_ORDER if k in fields and fields[k] is not None}
    json_path = MANIFESTS_DIR / f"{source}.json"
    json_path.write_text(json.dumps(json_fields, indent=2) + "\n", encoding="utf-8")


def update_ontology_manifest(source: str) -> str:
    """Recompute `sha256_dir` for one ontology source; rewrite its manifest pair.

    Returns the recomputed sha256.
    """
    onto_dir = ONTOLOGY_DIR / source
    manifest_path = MANIFESTS_DIR / f"{source}.yaml"
    fields = _parse_flat_manifest(manifest_path)

    digest = sha256_dir(onto_dir)
    curies_path = onto_dir / "curies.txt"
    row_count = len([ln for ln in curies_path.read_text().splitlines() if ln.strip()])

    fields["sha256"] = digest
    fields["row_count"] = row_count
    _write_manifest_pair(source, fields)
    print(f"[manifest] {source}: sha256_dir(ontology_snapshots/{source}) = {digest}")
    return digest


def build_perturbseq_records(raw_sha256: str) -> list[tuple[str, dict]]:
    raw_rows = []
    with RAW_SOURCE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw_rows.append(json.loads(line))

    id_by_label: dict[str, str] = {}
    built_records: list[tuple[str, dict]] = []

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
        record_hash = sha256_bytes(canonical_json(row).encode("utf-8"))[:16]
        evidence_id = f"{source}:{record_hash}"

        final_record = {"evidence_id": evidence_id, **row}
        id_by_label[row_label] = evidence_id
        built_records.append((row_label, final_record))

    return built_records


def update_perturbseq_manifest() -> None:
    raw_sha256 = sha256_file(RAW_SOURCE)
    built = build_perturbseq_records(raw_sha256)

    with RECORDS_OUT.open("w") as f:
        for _label, record in built:
            f.write(canonical_json(record))
            f.write("\n")
    print(f"[records] wrote {len(built)} records to {RECORDS_OUT}")

    records_sha256 = sha256_file(RECORDS_OUT)

    manifest_path = MANIFESTS_DIR / "perturbseq_v_test.yaml"
    fields = _parse_flat_manifest(manifest_path)
    fields["sha256"] = records_sha256
    fields["row_count"] = len(built)
    _write_manifest_pair("perturbseq_v_test", fields)
    print(f"[manifest] perturbseq_v_test: sha256_file(records.jsonl) = {records_sha256}")

    lines = [
        "# Perturb-seq fixture record id map",
        "",
        "Auto-generated by `recompute_hashes.py`. Do not hand-edit.",
        "",
        f"Raw source: `raw_source.jsonl`, sha256 = `{raw_sha256}`",
        "(this is also `snapshot_hash` on every record below; it is NOT the manifest's own "
        "`sha256`, which instead covers the built `records.jsonl` -- see `manifests/perturbseq_v_test.yaml`).",
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


def main() -> int:
    onto_sources = sorted(p.name for p in ONTOLOGY_DIR.iterdir() if p.is_dir())
    if not onto_sources:
        raise SystemExit(f"no ontology sources found under {ONTOLOGY_DIR}")
    for source in onto_sources:
        update_ontology_manifest(source)

    update_perturbseq_manifest()
    return 0


if __name__ == "__main__":
    sys.exit(main())
