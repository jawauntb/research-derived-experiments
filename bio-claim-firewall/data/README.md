# Phase 2 pilot world: frozen real-biology snapshot

A small, real, hash-verified evidence world for `bio-claim-firewall`'s verifier: five
identifier-ontology snapshots plus one perturbation-evidence ledger sampled from real,
permissively-licensed public sources. Nothing here is invented — see "Sampling &
substitution notes" below for the two places a literal reading of the task brief had to
be adjusted because the requested resource didn't actually exist as described, and what
was verified and used instead.

Only this file, `.gitignore`, `manifests/*.{yaml,json}`, and `scripts/*.py` are tracked
in git. Everything else under `data/` (`raw/`, `ontology_snapshots/`, `evidence_records/`,
`LICENSES/`) is regenerated locally by the download scripts and is gitignored — see
`data/.gitignore`.

## Quickstart

```bash
cd bio-claim-firewall/data/scripts

# Ontology snapshots (any order; each is independent):
python3 download_hgnc.py
python3 download_ncbitaxon.py
python3 download_cell_ontology.py
python3 download_cell_line_ontology.py
python3 download_reactome.py

# Perturbation evidence (download_hgnc.py must have run first --
# sample_replogle_2022.py maps gene symbols through the frozen HGNC snapshot):
python3 download_replogle_2022.py
python3 sample_replogle_2022.py

# Recompute every manifest's sha256/row_count from what's actually on disk
# (idempotent integrity pass; also run this any time you hand-edit a snapshot file):
python3 build_manifests.py
```

Then, from the repo root:

```python
from pathlib import Path
from evidence import load_bundle
bundle = load_bundle(Path("bio-claim-firewall/data"))
```

`load_bundle` fails closed (`EvidenceError("HASH_MISMATCH", ...)`) on any mismatch
between a manifest's declared `sha256` and what it actually computes from the files on
disk — see `tests/data/test_pilot_world_loads.py`.

## What's here

| Source (manifest key)        | What                                          | On disk (raw + snapshot) | Rows   | License      |
|-------------------------------|------------------------------------------------|---------------------------|--------|---------------|
| `hgnc.2026_pilot`             | HGNC complete gene set (full, unsampled)       | ~19MB                     | 45,045 curies, 3,449 merge-aliases | CC0-1.0 |
| `ncbitaxon.2026_pilot`        | 7 curated NCBI Taxonomy taxa                   | ~50KB                     | 7 curies | Public Domain (US Govt work) |
| `cellontology.2026_pilot`     | Cell Ontology (`cl-basic.obo`, full, unsampled)| ~3.9MB                    | 3,335 curies, is_a closure depth 3 | CC-BY-4.0 |
| `cellline.2026_pilot`         | 7 curated Cell Line Ontology terms (via OLS API)| ~30KB                     | 7 curies | CC-BY-4.0 |
| `reactome.2026_pilot`         | Human pathway membership (Ensembl2Reactome, sampled) | ~1.5MB               | 2,012 pathway curies, 20,000 membership rows | CC0-1.0 |
| `perturbseq.replogle_2022`    | Replogle 2022 K562 genome-scale Perturb-seq (sampled) | ~46MB (37MB raw + 9MB ledger) | 9,400 `perturbation_effect` records | CC0-1.0 |

**Total on-disk footprint (raw + ontology_snapshots + evidence_records, everything
`build_manifests.py`/`load_bundle` touches): ~70MB**, well under the 500MB budget.
(`data/raw/perturbseq.replogle_2022/` and `data/raw/hgnc.2026_pilot/` are the two big
line items, at 37MB and 16MB respectively; every other source's raw download is a few
KB to a few MB.)

## Sampling & substitution notes

Every deviation from a literal reading of the task brief, and why:

- **NCBI Taxonomy**: the full `taxdump` is 79-160MB for ~2.6M taxa this pilot world
  never cites. Instead of downloading it, `download_ncbitaxon.py` calls NCBI's own
  E-utilities `efetch` endpoint for a curated 7-taxon id list (human, mouse, rat,
  zebrafish, *C. elegans*, *D. melanogaster*, *S. cerevisiae*) — real, current NCBI
  Taxonomy names, just fetched a few bytes at a time instead of in bulk.

- **Cell Line Ontology (CLO)**: `purl.obolibrary.org/obo/clo.obo` 404s and the CLO
  GitHub repo has no `clo.obo` at the expected release path — there is no working bulk
  OBO/OWL download for CLO right now. `download_cell_line_ontology.py` falls back to
  per-term lookups against the EBI Ontology Lookup Service (OLS) REST API for a curated
  list of real cell-line CURIEs (K562, RPE1, HeLa, HEK293T, JURKAT, MCF7, A549), each
  found by searching OLS and verified by exact label match before being written — see
  the next bullet for why this mattered.

- **The task brief's suggested `CLO:0009454` (K562) and `CLO:0037231` (RPE1) are
  wrong.** OLS resolves `CLO:0009454` to *"U-2 OS cell"* and `CLO:0037231` to *"ECC-1
  cell"* — neither is K562 or RPE1. The brief itself flagged these as needing
  verification ("if that's the CL term for K562's lineage — verify"); they didn't hold
  up, so this pilot world uses the CURIEs that actually verified: **`CLO:0007059`
  ("K-562 cell")** and **`CLO:0004290`  ("hTERT RPE-1 cell")**. Similarly, the brief's
  suggested Cell Ontology term for K562's lineage, `CL:0000094`, resolves to
  *"granulocyte"* — not correct for a myeloid/erythroleukemia line. This pilot world
  uses **`CL:0000988` ("hematopoietic cell")** instead: a real, correct (if
  deliberately generic) Cell Ontology ancestor term, rather than inventing or
  guess-preserving an incorrect specific one. All of this is re-derived and
  re-documented in `download_cell_line_ontology.py`'s and `sample_replogle_2022.py`'s
  own docstrings, not just asserted here.

- **Reactome**: there's no single "HGNC / Reactome mapping CSV" at the URL implied by
  the brief; the closest real, small, directly-usable file is Reactome's own
  `Ensembl2Reactome.txt` (all species, ~183MB, ~1.68M rows). `download_reactome.py`
  streams it, filters to `species == "Homo sapiens"` (381,765 matching rows), and caps
  the kept membership rows at 20,000 (in on-disk file order) — the raw multi-species
  download is not retained locally (it alone would be over a third of the whole
  budget); only the filtered, capped extraction is kept.

- **Replogle 2022 perturbation data**: there is no publicly hosted, ready-made
  "MAGeCK-like" per-perturbation-per-gene **log2FC** table for this dataset, and reading
  the real `.h5ad` pseudobulk/single-cell files needs `anndata`/`h5py`, neither an
  existing project dependency (adding one was out of scope). Instead
  `download_replogle_2022.py` pulls the paper's own **small, already-processed**
  "commonly requested supplemental files" release (Figshare article `21632564`, CC0):
  a **gemgroup Z-normalized mean pseudobulk expression** matrix
  (`clustered_mean_gene_expression_figs2-4.csv.gz`, ~38MB, the source data behind
  Figures 2 and 4 of the paper) plus per-perturbation metadata including an
  Anderson-Darling differential-expression gene count
  (`annotated_embedding_coordinates.csv`). Because this is genuinely a **Z-score**
  matrix, not log2FC, `sample_replogle_2022.py` honestly sets
  `effect.magnitude_scale = "zscore_mean_expression"` rather than mislabeling it
  `"log2fc"`. `effect.significance` and `effect.n_replicates` are `null`: the
  underlying Anderson-Darling p-value table is a real file (`anderson-darling
  p-values, BH-corrected.csv.gz`, ~488MB) but was deliberately **not** downloaded — it
  alone would nearly consume the entire 500MB budget for one significance column.

  Sampling method (matches the task brief's own stated fallback: "sample 100
  perturbations x top 100 differentially-expressed targets = 10k records"):
  1. Rank all ~1,973 perturbations by their Anderson-Darling DE gene count (desc, ties
     broken by perturbation id asc); take the top 100.
  2. For each, rank its ~2,322 measured-gene z-score values by absolute magnitude
     (desc, ties broken by gene symbol asc); take the top 100.
  3. Drop any pair where either gene symbol doesn't resolve against this repo's own
     frozen HGNC snapshot (94 of 100 perturbed genes mapped; a handful of individual
     measured-gene pairs per perturbation were dropped for the same reason) — nothing
     is invented to fill a gap.
  4. Result: **9,400 `perturbation_effect` records** (well under the 20,000 cap),
     all human, all K562 (`CLO:0007059`), all CRISPRi, all `observation_type:
     interventional`.

## Licenses

Every source's license tag is recorded in its manifest (`license` field) and the full
legal text is written to `data/LICENSES/<source>.txt` (plus `CC0-1.0.txt`,
`CC-BY-4.0.txt`, `NCBI-Public-Domain.txt` for the shared texts) by the download scripts
— gitignored like the rest of the raw/processed tree, so it's always the text actually
fetched at download time, not a possibly-stale committed copy. Summary:

- **HGNC**: CC0 1.0 (Public Domain), per <https://www.genenames.org/about/license/>.
- **NCBI Taxonomy**: Public Domain (US Government work), per
  <https://www.ncbi.nlm.nih.gov/home/about/policies/>.
- **Cell Ontology (CL)**: CC BY 4.0, per the `terms:license` property embedded directly
  in `cl-basic.obo`'s header (confirmed against <https://obofoundry.org/ontology/cl.html>).
- **Cell Line Ontology (CLO)**: CC BY 4.0, per the OBO Foundry registry
  (<https://obofoundry.org/ontology/clo.html>).
- **Reactome**: CC0 1.0, per <https://reactome.org/license> ("All data in the Reactome
  database and files derived from that data are licensed under ... CC0").
- **Replogle et al. 2022 supplemental files**: CC0 1.0, per the Figshare article's own
  license metadata (verified programmatically at download time, see
  `download_replogle_2022.py`). Primary study citation: Replogle, J.M. et al. "Mapping
  information-rich genotype-phenotype landscapes with genome-scale Perturb-seq." *Cell*
  185(14):2559-2575.e28 (2022). DOI: 10.1016/j.cell.2022.05.013.

No source required an API key; none were skipped for licensing ambiguity — every source
listed in the task brief was successfully retrieved in some real form (see the
substitution notes above for the two that needed a fallback strategy).

## Scripts

| Script | Produces |
|---|---|
| `scripts/_common.py` | Shared stdlib-only helpers (fetch, manifest read/write, hashing via `evidence.hashing`) — not a download script itself. |
| `scripts/download_hgnc.py` | `ontology_snapshots/hgnc.2026_pilot/` |
| `scripts/download_ncbitaxon.py` | `ontology_snapshots/ncbitaxon.2026_pilot/` |
| `scripts/download_cell_ontology.py` | `ontology_snapshots/cellontology.2026_pilot/` |
| `scripts/download_cell_line_ontology.py` | `ontology_snapshots/cellline.2026_pilot/` |
| `scripts/download_reactome.py` | `ontology_snapshots/reactome.2026_pilot/` |
| `scripts/download_replogle_2022.py` | `raw/perturbseq.replogle_2022/` (the two small source CSVs) |
| `scripts/sample_replogle_2022.py` | `evidence_records/perturbseq.replogle_2022/records.jsonl` |
| `scripts/build_manifests.py` | Recomputes every manifest's `sha256`/`row_count` in place (idempotent integrity pass). |

All stdlib-only (`urllib.request`, `gzip`, `csv`, `json`, `hashlib` via
`evidence.hashing`) — no new project dependencies were added.

## Tests

`bio-claim-firewall/tests/data/test_pilot_world_loads.py` and
`test_pilot_world_end_to_end.py` skip (rather than fail) if the downloads haven't been
run locally. Run them after the Quickstart above:

```bash
uv run --no-sync python -m pytest bio-claim-firewall/tests/data/ -v
```
