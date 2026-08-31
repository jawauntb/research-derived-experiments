#!/usr/bin/env python3
"""Fetch a small, real NCBI Taxonomy snapshot: human + mouse + a few reference taxa.

Sampling method: the full NCBI taxdump (`new_taxdump.zip`, ~160MB, or the
classic `taxdump.tar.gz`, ~79MB) covers all ~2.6M taxa. The pilot world only
needs the taxon actually used by the frozen evidence (human, NCBITaxon:9606)
plus mouse and a small set of common model organisms for future headroom, so
instead of downloading the full dump we query NCBI's own E-utilities
`efetch` endpoint (https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi)
for exactly those taxon ids. This returns real, current NCBI Taxonomy
scientific names -- not invented -- for a curated id list, at a cost of a
few KB instead of ~80-160MB.

License: NCBI/NLM data is a US Government work; per
https://www.ncbi.nlm.nih.gov/home/about/policies/ it is in the public domain
(see data/LICENSES/NCBI-Public-Domain.txt).

Output: data/ontology_snapshots/ncbitaxon.2026_pilot/
  curies.txt    one `NCBITaxon:<id>` per line
  labels.jsonl  {"curie": "NCBITaxon:<id>", "label": "<scientific name>"}
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from _common import (
    RAW_DIR,
    fetch_bytes,
    log,
    now_iso,
    write_license_text,
    write_ontology_manifest,
)

SOURCE = "ncbitaxon.2026_pilot"
TAXON_IDS = ["9606", "10090", "10116", "7955", "6239", "7227", "4932"]
EFETCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    f"?db=taxonomy&id={','.join(TAXON_IDS)}&retmode=xml"
)
LICENSE_TAG = "Public-Domain"
LICENSE_URL = "https://www.ncbi.nlm.nih.gov/home/about/policies/"

OUT_DIR = Path(__file__).resolve().parent.parent / "ontology_snapshots" / SOURCE
RAW_OUT = RAW_DIR / SOURCE


def main() -> int:
    retrieved_at = now_iso()
    RAW_OUT.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    log(f"fetching {EFETCH_URL}")
    xml_bytes = fetch_bytes(EFETCH_URL, timeout=30)
    (RAW_OUT / "efetch_taxonomy.xml").write_bytes(xml_bytes)

    root = ET.fromstring(xml_bytes)
    curies: list[str] = []
    labels: list[dict[str, str]] = []
    for taxon in root.findall("Taxon"):
        tax_id = taxon.findtext("TaxId")
        name = taxon.findtext("ScientificName")
        if not tax_id or not name:
            continue
        curie = f"NCBITaxon:{tax_id}"
        curies.append(curie)
        labels.append({"curie": curie, "label": name})

    if not curies:
        raise SystemExit(
            "no taxa parsed from efetch response -- refusing to write an empty snapshot"
        )

    (OUT_DIR / "curies.txt").write_text("\n".join(curies) + "\n", encoding="utf-8")
    with (OUT_DIR / "labels.jsonl").open("w", encoding="utf-8") as f:
        for row in labels:
            f.write(json.dumps(row, sort_keys=True))
            f.write("\n")

    log(
        f"{len(curies)} taxa: "
        + ", ".join(f"{r['curie']}={r['label']}" for r in labels)
    )

    write_license_text(
        SOURCE,
        "NCBI Taxonomy data license: Public Domain (US Government work)",
        LICENSE_URL,
        "NCBI Taxonomy records are produced by NLM/NCBI, a US Government agency, and are in "
        "the public domain. See data/LICENSES/NCBI-Public-Domain.txt for NCBI's own policy text.",
    )

    write_ontology_manifest(
        source=SOURCE,
        source_url=EFETCH_URL,
        retrieved_at=retrieved_at,
        license_tag=LICENSE_TAG,
        preprocessing_cmd=(
            "python3 data/scripts/download_ncbitaxon.py -- fetches NCBI E-utilities efetch "
            "(db=taxonomy, retmode=xml) for a curated small taxon-id list "
            f"({', '.join(TAXON_IDS)}) instead of the full ~80-160MB taxdump, since the pilot "
            "world only cites NCBITaxon:9606 (human); parses TaxId/ScientificName into "
            "curies.txt + labels.jsonl."
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
