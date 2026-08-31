#!/usr/bin/env python3
"""Download Reactome's Ensembl-gene-to-pathway mapping and extract a human pathway snapshot.

Source: `Ensembl2Reactome.txt` (all species, lowest-level pathway per gene),
https://reactome.org/download-data. License: CC0 1.0, per
https://reactome.org/license ("All data in the Reactome database and files
derived from that data are licensed under the Creative Commons Public
Domain Dedication (CC0)").

Sampling method: the raw file covers every species (~183MB, ~1.68M rows);
this pilot world is human-only (spec/inference_rules.md R-SCOPE-90), so we
filter to `species == "Homo sapiens"` while streaming, then cap the
per-gene-pathway membership rows at MAX_MEMBERSHIP_ROWS (in on-disk file
order, which is stable but not otherwise curated) to keep the snapshot
small. The raw multi-species download is NOT retained under data/raw/
(it would alone consume more than a third of the whole pilot world's 500MB
budget); only the filtered, capped human extraction is kept, and this
script's own preprocessing_cmd + manifest document exactly how it was
produced so it is reproducible from the same public URL.

Output: data/ontology_snapshots/reactome.2026_pilot/
  curies.txt              one `REACT:<id>` per line, for every pathway that
                           appears in the (capped) membership sample
  labels.jsonl             {"curie": "REACT:<id>", "label": "<pathway name>"}
  pathway_membership.jsonl {"gene": "ENSEMBL:<id>", "pathway": "REACT:<id>"}
                           one row per (gene, pathway) membership pair kept
                           in the sample (NOT read by evidence/loader.py --
                           it only recognizes curies.txt/labels.jsonl/
                           aliases.jsonl/cell_ontology.jsonl -- but it is
                           still hashed as part of sha256_dir and kept here
                           as auditable provenance for the pathway_membership
                           record_type described in spec/evidence.schema.json)
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from _common import (
    USER_AGENT,
    log,
    now_iso,
    write_license_text,
    write_ontology_manifest,
)

SOURCE = "reactome.2026_pilot"
ENSEMBL2REACTOME_URL = "https://reactome.org/download/current/Ensembl2Reactome.txt"
LICENSE_TAG = "CC0-1.0"
LICENSE_URL = "https://reactome.org/license"
MAX_MEMBERSHIP_ROWS = 20_000

OUT_DIR = Path(__file__).resolve().parent.parent / "ontology_snapshots" / SOURCE


def main() -> int:
    retrieved_at = now_iso()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    log(
        f"streaming {ENSEMBL2REACTOME_URL} (human rows only, cap={MAX_MEMBERSHIP_ROWS})"
    )
    req = urllib.request.Request(
        ENSEMBL2REACTOME_URL, headers={"User-Agent": USER_AGENT}
    )

    membership_rows: list[dict[str, str]] = []
    pathway_labels: dict[str, str] = {}
    total_lines = 0
    human_lines = 0

    with urllib.request.urlopen(req, timeout=180) as resp:  # noqa: S310
        for raw_line in resp:
            total_lines += 1
            line = raw_line.decode("utf-8", errors="replace").rstrip("\n")
            if not line:
                continue
            fields = line.split("\t")
            if len(fields) < 6:
                continue
            ensembl_id, reactome_id, _url, pathway_name, _evidence_code, species = (
                fields[:6]
            )
            if species != "Homo sapiens":
                continue
            human_lines += 1
            if len(membership_rows) >= MAX_MEMBERSHIP_ROWS:
                continue
            if not ensembl_id.startswith("ENSG"):
                continue
            pathway_curie = f"REACT:{reactome_id}"
            pathway_labels[pathway_curie] = pathway_name
            membership_rows.append(
                {"gene": f"ENSEMBL:{ensembl_id}", "pathway": pathway_curie}
            )

    if not membership_rows:
        raise SystemExit(
            "zero human Ensembl2Reactome rows parsed -- refusing to write an empty snapshot"
        )

    curies = sorted(pathway_labels)
    (OUT_DIR / "curies.txt").write_text("\n".join(curies) + "\n", encoding="utf-8")
    with (OUT_DIR / "labels.jsonl").open("w", encoding="utf-8") as f:
        for curie in curies:
            f.write(
                json.dumps(
                    {"curie": curie, "label": pathway_labels[curie]}, sort_keys=True
                )
            )
            f.write("\n")
    with (OUT_DIR / "pathway_membership.jsonl").open("w", encoding="utf-8") as f:
        for row in membership_rows:
            f.write(json.dumps(row, sort_keys=True))
            f.write("\n")

    log(
        f"{total_lines} total rows scanned, {human_lines} human rows matched, "
        f"kept {len(membership_rows)} membership rows across {len(curies)} distinct pathways"
    )

    write_license_text(
        SOURCE,
        "Reactome data license: Creative Commons Public Domain Dedication (CC0)",
        LICENSE_URL,
        "Per https://reactome.org/license: 'All data in the Reactome database and files "
        "derived from that data are licensed under the Creative Commons Public Domain "
        "Dedication (CC0). User may copy, modify, and distribute these data, even for "
        "commercial purposes, without asking for permission.' "
        "See data/LICENSES/CC0-1.0.txt for the full CC0 legal text.",
    )

    write_ontology_manifest(
        source=SOURCE,
        source_url=ENSEMBL2REACTOME_URL,
        retrieved_at=retrieved_at,
        license_tag=LICENSE_TAG,
        preprocessing_cmd=(
            "python3 data/scripts/download_reactome.py -- streams Ensembl2Reactome.txt "
            "(tab-separated: ensembl_gene_id, reactome_pathway_id, url, pathway_name, "
            "evidence_code, species), filters to species=='Homo sapiens', caps membership "
            f"rows at {MAX_MEMBERSHIP_ROWS} in on-disk file order (raw multi-species download "
            "not retained -- ~183MB, exceeds the per-source disk budget); writes curies.txt + "
            "labels.jsonl for every REACT pathway touched by the kept rows, plus "
            "pathway_membership.jsonl (gene, pathway) for the kept rows themselves."
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
