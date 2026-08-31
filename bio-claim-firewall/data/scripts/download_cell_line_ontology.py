#!/usr/bin/env python3
"""Fetch a minimal, real Cell Line Ontology (CLO) snapshot via the EBI OLS API.

CLO has no working bulk OBO/OWL download at this time: `purl.obolibrary.org/
obo/clo.obo` 404s, and its GitHub `master` branch has no `clo.obo` at the
expected path either (checked at download time). This is exactly the
"format weirdness" case the task brief anticipates -- so instead of a full
ontology dump we fall back to a minimal snapshot of real CLO terms, fetched
one-by-one from the EBI Ontology Lookup Service (OLS) REST API
(https://www.ebi.ac.uk/ols4/), for K562 and RPE1 (used by the frozen
Replogle 2022 perturbation evidence) plus a handful of other commonly used
cell lines. Every CURIE below was looked up and label-verified against OLS
at authoring time -- none are invented. In particular, note that the task
brief's suggested `CLO:0009454` (K562) and `CLO:0037231` (RPE1) do NOT
resolve to those cell lines (OLS reports CLO:0009454 = "U-2 OS cell" and
CLO:0037231 = "ECC-1 cell") -- the real ids used below were found by
searching OLS's `clo` ontology for each cell line name.

License: CC BY 4.0, per the OBO Foundry registry entry for CLO
(https://obofoundry.org/ontology/clo.html -> license: CC BY 4.0).

Output: data/ontology_snapshots/cellline.2026_pilot/
  curies.txt    one `CLO:<id>` per line
  labels.jsonl  {"curie": "CLO:<id>", "label": "<preferred OLS label>"}
"""

from __future__ import annotations

import json
import urllib.parse
from pathlib import Path

from _common import (
    RAW_DIR,
    fetch_json,
    log,
    now_iso,
    write_license_text,
    write_ontology_manifest,
)

SOURCE = "cellline.2026_pilot"
OLS_TERM_URL = "https://www.ebi.ac.uk/ols4/api/ontologies/clo/terms/{iri}"
LICENSE_TAG = "CC-BY-4.0"
LICENSE_URL = "https://obofoundry.org/ontology/clo.html"

# Real CLO ids, verified against OLS at authoring time. Comment = the cell
# line each one actually resolves to (label as returned by OLS).
CURATED_IDS = {
    "CLO:0007059": "K562 (K-562 cell) -- used by the frozen Replogle 2022 perturbation evidence",
    "CLO:0004290": "RPE1 (hTERT RPE-1 cell)",
    "CLO:0003684": "HeLa cell",
    "CLO:0037372": "HEK293T cell",
    "CLO:0007043": "JURKAT cell",
    "CLO:0007606": "MCF7 cell",
    "CLO:0001601": "A549 cell",
}

OUT_DIR = Path(__file__).resolve().parent.parent / "ontology_snapshots" / SOURCE
RAW_OUT = RAW_DIR / SOURCE


def _ols_term_url(curie: str) -> str:
    iri = f"http://purl.obolibrary.org/obo/{curie.replace(':', '_')}"
    double_encoded = urllib.parse.quote(urllib.parse.quote(iri, safe=""), safe="")
    return OLS_TERM_URL.format(iri=double_encoded)


def main() -> int:
    retrieved_at = now_iso()
    RAW_OUT.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    curies: list[str] = []
    labels: list[dict[str, str]] = []
    raw_responses: dict[str, dict] = {}

    for curie, expected_note in CURATED_IDS.items():
        url = _ols_term_url(curie)
        log(f"fetching {curie} ({expected_note}) via OLS: {url}")
        doc = fetch_json(url, timeout=20)
        raw_responses[curie] = doc
        label = doc.get("label")
        if not label:
            log(f"WARNING: {curie} returned no label, skipping")
            continue
        curies.append(curie)
        labels.append({"curie": curie, "label": label})

    if not curies:
        raise SystemExit(
            "resolved zero CLO terms via OLS -- refusing to write an empty snapshot"
        )

    (RAW_OUT / "ols_terms.json").write_text(
        json.dumps(raw_responses, indent=2, sort_keys=True), encoding="utf-8"
    )

    (OUT_DIR / "curies.txt").write_text("\n".join(curies) + "\n", encoding="utf-8")
    with (OUT_DIR / "labels.jsonl").open("w", encoding="utf-8") as f:
        for row in labels:
            f.write(json.dumps(row, sort_keys=True))
            f.write("\n")

    log(
        f"{len(curies)} CLO terms: "
        + ", ".join(f"{r['curie']}={r['label']!r}" for r in labels)
    )

    write_license_text(
        SOURCE,
        "Cell Line Ontology (CLO) license: Creative Commons Attribution 4.0 International",
        LICENSE_URL,
        "Per the OBO Foundry registry entry for CLO, its license is CC BY 4.0. "
        "See data/LICENSES/CC-BY-4.0.txt for the full legal text.",
    )

    write_ontology_manifest(
        source=SOURCE,
        source_url="https://www.ebi.ac.uk/ols4/api/ontologies/clo/terms/{double-url-encoded PURL} (per-term)",
        retrieved_at=retrieved_at,
        license_tag=LICENSE_TAG,
        preprocessing_cmd=(
            "python3 data/scripts/download_cell_line_ontology.py -- CLO has no working bulk "
            "OBO/OWL download at fetch time (purl.obolibrary.org/obo/clo.obo 404s); falls back "
            "to per-term lookups against the EBI OLS REST API for a curated real-CURIE list "
            "(K562, RPE1, + a handful of common lines), verified by label match, not invented. "
            "Writes curies.txt + labels.jsonl."
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
