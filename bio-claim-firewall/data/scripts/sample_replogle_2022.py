#!/usr/bin/env python3
"""Sample the downloaded Replogle 2022 z-normalized expression matrix into EvidenceRecords.

Input (from `download_replogle_2022.py`, under data/raw/perturbseq.replogle_2022/):
  clustered_mean_gene_expression_figs2-4.csv.gz  -- gene_transcript (measured
    gene) x perturbation matrix of gemgroup Z-normalized mean pseudobulk
    expression deviation from control. ~2322 measured genes x ~1973
    perturbations = ~4.6M possible (perturbation, gene) pairs -- far more
    than the 20,000-record pilot-world cap, so we sample exactly as the task
    brief's stated fallback describes: "sample 100 perturbations x top 100
    differentially-expressed targets = 10k records."
  annotated_embedding_coordinates.csv -- per-perturbation metadata,
    including the Anderson-Darling differential-expression gene count
    (`anderson-darling de genes`) used to rank perturbations by phenotype
    strength, and the clean HGNC-symbol `gene` column used to identify the
    perturbed gene without needing to regex-parse the matrix's composite
    column ids.

Sampling method (exactly, for the manifest and README):
  1. Rank all ~1973 perturbations by `anderson-darling de genes` (desc,
     ties broken by perturbation id asc for determinism); take the top
     N_PERTURBATIONS.
  2. For each of those perturbations' matrix column, rank its ~2322
     measured-gene z-score values by absolute magnitude (desc, ties broken
     by gene symbol asc); take the top N_GENES_PER_PERTURBATION.
  3. Drop any (perturbed gene, measured gene) pair where either gene symbol
     does not resolve against this repo's own frozen HGNC snapshot
     (data/ontology_snapshots/hgnc.2026_pilot/) -- never invents an HGNC id.

Every kept pair becomes one `record_type: perturbation_effect` EvidenceRecord
per spec/evidence.schema.json. Because this source is a Z-SCORE matrix, not a
log2 fold-change table, `effect.magnitude_scale` is honestly set to
`"zscore_mean_expression"` (see download_replogle_2022.py's docstring for why
no real log2FC table was substituted here). `effect.significance` and
`effect.n_replicates` are `null` -- the underlying Anderson-Darling p-value
table (488MB) was not downloaded (see task's size budget), and replicate
counts are not reported at this granularity in this export.

Context fields: species=NCBITaxon:9606 (human); the K562 genome-scale
screen -> cell_line=CLO:0007059 ("K-562 cell", the CLO term that actually
resolves to K562 -- see download_cell_line_ontology.py's docstring for why
the task brief's suggested CLO:0009454 is wrong); cell_type=CL:0000988
("hematopoietic cell", a correct if generic Cell Ontology ancestor for a
myeloid/erythroleukemia line -- the brief's suggested CL:0000094
("granulocyte") was verified wrong and not used); state="resting" (no
additional stimulus was applied in this screen, matching Replogle's
described baseline growth condition).
"""

from __future__ import annotations

import csv
import gzip
import json

from _common import (
    EVIDENCE_DIR,
    RAW_DIR,
    load_hgnc_symbol_map,
    log,
    record_hash16,
    sha256_file,
    write_evidence_manifest,
)

SOURCE = "perturbseq.replogle_2022"
RAW_IN = RAW_DIR / SOURCE
MATRIX_FILE = RAW_IN / "clustered_mean_gene_expression_figs2-4.csv.gz"
METADATA_FILE = RAW_IN / "annotated_embedding_coordinates.csv"
OUT_FILE = EVIDENCE_DIR / SOURCE / "records.jsonl"

N_PERTURBATIONS = 100
N_GENES_PER_PERTURBATION = 100
MAX_RECORDS = 20_000

SPECIES = "NCBITaxon:9606"
CELL_TYPE = "CL:0000988"  # "hematopoietic cell" -- verified real CL ancestor term
CELL_LINE = "CLO:0007059"  # "K-562 cell" -- verified real CLO term for K562
STATE = "resting"
LICENSE_TAG = "CC0-1.0"
STUDY_CITATION = (
    "Replogle, J.M. et al. Mapping information-rich genotype-phenotype landscapes with "
    "genome-scale Perturb-seq. Cell 185(14):2559-2575.e28 (2022). DOI: 10.1016/j.cell.2022.05.013"
)
FIGSHARE_URL = "https://ndownloader.figshare.com/files/38349305"  # clustered_mean_gene_expression_figs2-4.csv.gz
_SKIP_ROW_LABELS = {"cluster", "gene_name"}


def _load_perturbation_metadata() -> dict[str, dict[str, object]]:
    """{perturbation_id -> {gene_symbol, de_gene_count}} from annotated_embedding_coordinates.csv."""
    out: dict[str, dict[str, object]] = {}
    with METADATA_FILE.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pert_id = row.get("gene_transcript", "").strip()
            gene_symbol = row.get("gene", "").strip()
            de_raw = (row.get("anderson-darling de genes") or "").strip()
            if not pert_id or not gene_symbol or not de_raw:
                continue
            try:
                de_count = int(de_raw)
            except ValueError:
                continue
            out[pert_id] = {"gene_symbol": gene_symbol, "de_gene_count": de_count}
    return out


def _select_top_perturbations(meta: dict[str, dict[str, object]]) -> list[str]:
    ranked = sorted(meta.items(), key=lambda kv: (-kv[1]["de_gene_count"], kv[0]))
    return [pert_id for pert_id, _info in ranked[:N_PERTURBATIONS]]


def _read_matrix_rows(
    wanted_columns: dict[int, str],
) -> dict[str, list[tuple[str, float]]]:
    """{perturbation_id -> [(measured_gene_symbol, value), ...]} for the wanted columns only."""
    per_pert: dict[str, list[tuple[str, float]]] = {
        pid: [] for pid in wanted_columns.values()
    }
    with gzip.open(MATRIX_FILE, "rt", encoding="utf-8", newline="") as raw:
        reader = csv.reader(raw)
        header = next(reader)
        assert header[0] == "gene_transcript", (
            f"unexpected matrix header: {header[:3]!r}"
        )
        for row in reader:
            if not row or row[0] in _SKIP_ROW_LABELS:
                continue
            gene_symbol = row[0].strip()
            if not gene_symbol:
                continue
            for col_idx, pert_id in wanted_columns.items():
                if col_idx >= len(row):
                    continue
                cell = row[col_idx].strip()
                if not cell:
                    continue
                try:
                    value = float(cell)
                except ValueError:
                    continue
                per_pert[pert_id].append((gene_symbol, value))
    return per_pert


def main() -> int:
    if not MATRIX_FILE.is_file() or not METADATA_FILE.is_file():
        raise SystemExit(
            f"run download_replogle_2022.py first (missing {MATRIX_FILE} or {METADATA_FILE})"
        )

    hgnc_map = load_hgnc_symbol_map()
    if not hgnc_map:
        raise SystemExit(
            "run download_hgnc.py first -- sample_replogle_2022.py maps symbols via the HGNC snapshot"
        )
    log(f"loaded {len(hgnc_map)} HGNC symbol->curie mappings")

    meta = _load_perturbation_metadata()
    log(f"{len(meta)} perturbations described in {METADATA_FILE.name}")
    top_perturbations = _select_top_perturbations(meta)
    log(
        f"selected top {len(top_perturbations)} perturbations by Anderson-Darling DE gene count"
    )

    with gzip.open(MATRIX_FILE, "rt", encoding="utf-8", newline="") as raw:
        header = next(csv.reader(raw))
    header_index = {pert_id: idx for idx, pert_id in enumerate(header) if idx >= 2}
    wanted_columns = {
        header_index[pid]: pid for pid in top_perturbations if pid in header_index
    }
    missing_from_matrix = set(top_perturbations) - set(wanted_columns.values())
    if missing_from_matrix:
        log(
            f"WARNING: {len(missing_from_matrix)} selected perturbation ids not found as matrix columns"
        )

    per_pert_values = _read_matrix_rows(wanted_columns)

    # `retrieved_at` must come from when the RAW source was actually fetched
    # (download_replogle_2022.py's own provenance sidecar), not from
    # `now_iso()` at sampling time: it feeds every record's canonical-json
    # hash, so a wall-clock `retrieved_at` would make evidence_id (and this
    # source's manifest sha256) change on every rerun of this script even
    # when the underlying source data hasn't -- non-reproducible ids the
    # ledger and any claim citing them would silently drift under.
    provenance_path = RAW_IN / "_provenance.json"
    if not provenance_path.is_file():
        raise SystemExit(f"missing {provenance_path} -- run download_replogle_2022.py first")
    retrieved_at = json.loads(provenance_path.read_text(encoding="utf-8"))["retrieved_at"]
    raw_snapshot_hash = sha256_file(MATRIX_FILE)

    records: list[dict] = []
    seen_ids: set[str] = set()
    n_skipped_unmapped_perturbed = 0
    n_skipped_unmapped_measured = 0

    for pert_id in top_perturbations:
        if pert_id not in per_pert_values:
            continue
        perturbed_symbol = meta[pert_id]["gene_symbol"]
        perturbed_curie = hgnc_map.get(perturbed_symbol)
        if perturbed_curie is None:
            n_skipped_unmapped_perturbed += 1
            continue

        ranked_genes = sorted(
            per_pert_values[pert_id], key=lambda t: (-abs(t[1]), t[0])
        )
        kept = 0
        for measured_symbol, value in ranked_genes:
            if kept >= N_GENES_PER_PERTURBATION:
                break
            measured_curie = hgnc_map.get(measured_symbol)
            if measured_curie is None:
                n_skipped_unmapped_measured += 1
                continue
            kept += 1

            if value > 0:
                sign = "positive"
            elif value < 0:
                sign = "negative"
            else:
                sign = "null"

            record_without_id = {
                "source": SOURCE,
                "snapshot_hash": raw_snapshot_hash,
                "record_type": "perturbation_effect",
                "subject": {"id": perturbed_curie, "label": perturbed_symbol},
                "object": {"id": measured_curie, "label": measured_symbol},
                "species": SPECIES,
                "cell_context": {
                    "cell_type": CELL_TYPE,
                    "cell_line": CELL_LINE,
                    "state": STATE,
                },
                "assay_context": {
                    "assay": "CRISPRi_screen",
                    "perturbation": f"CRISPRi:{perturbed_curie}",
                },
                "observation_type": "interventional",
                "effect": {
                    "sign": sign,
                    "magnitude": round(value, 6),
                    "magnitude_scale": "zscore_mean_expression",
                    "significance": None,
                    "n_replicates": None,
                },
                "contradicts": [],
                "retrieved_at": retrieved_at,
                "license": LICENSE_TAG,
                "schema_version": "0.1.0",
                "source_citation": STUDY_CITATION,
            }
            evidence_id = f"{SOURCE}:{record_hash16(record_without_id)}"
            if evidence_id in seen_ids:
                continue
            seen_ids.add(evidence_id)
            records.append({"evidence_id": evidence_id, **record_without_id})

            if len(records) >= MAX_RECORDS:
                break
        if len(records) >= MAX_RECORDS:
            break

    if not records:
        raise SystemExit(
            "sampled zero evidence records -- refusing to write an empty ledger"
        )

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, sort_keys=True))
            f.write("\n")

    log(
        f"wrote {len(records)} perturbation_effect records "
        f"({n_skipped_unmapped_perturbed} perturbations skipped for unmapped symbol, "
        f"{n_skipped_unmapped_measured} measured-gene pairs skipped for unmapped symbol)"
    )

    write_evidence_manifest(
        source=SOURCE,
        source_url=FIGSHARE_URL,
        retrieved_at=retrieved_at,
        license_tag=LICENSE_TAG,
        preprocessing_cmd=(
            "python3 data/scripts/sample_replogle_2022.py -- ranks perturbations by "
            "annotated_embedding_coordinates.csv's Anderson-Darling DE gene count (desc), "
            f"takes the top {N_PERTURBATIONS}; for each, ranks measured genes in "
            "clustered_mean_gene_expression_figs2-4.csv.gz by |z-score| (desc), takes the top "
            f"{N_GENES_PER_PERTURBATION}; maps both perturbed- and measured-gene symbols through "
            "this repo's own frozen HGNC snapshot (unmapped symbols dropped, never invented); "
            f"writes one perturbation_effect EvidenceRecord per kept pair (cap {MAX_RECORDS})."
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
