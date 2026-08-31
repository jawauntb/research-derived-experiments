"""Shared fixtures: a tiny synthetic frozen data root for src/evidence tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# EVIDENCE-DECISION: bio-claim-firewall has no pyproject.toml / pytest.ini
# of its own yet (the monorepo root's pyproject.toml is out of scope to
# edit for this task), so nothing puts bio-claim-firewall/ on sys.path for
# `import src.evidence...` when tests run via
# `python -m pytest bio-claim-firewall/tests/evidence/` from the monorepo
# root. Do it here, in this directory's own conftest.py (in-scope), rather
# than touching any file outside src/evidence/ or tests/evidence/.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.evidence.hashing import sha256_dir, sha256_file  # noqa: E402

SPECIES_ID = "NCBITaxon:9606"
GENE_1 = "HGNC:1097"
GENE_2 = "HGNC:1098"
GENE_3 = "HGNC:1099"
GENE_1_DEPRECATED = "HGNC:OLD1"
CELL_TYPE_CHILD = "CL:0000236"  # e.g. "B cell"
CELL_TYPE_OTHER = "CL:0000542"  # e.g. "lymphocyte" -- second cell type, same ancestors
CELL_TYPE_PARENT = "CL:0000738"  # e.g. "leukocyte"
CELL_TYPE_ROOT = "CL:0000000"  # e.g. "cell"

EVIDENCE_SOURCE = "perturbseq.test_2026"
INTERVENTIONAL_EVIDENCE_ID = f"{EVIDENCE_SOURCE}:aaaaaaaaaaaaaaaa"
OBSERVATIONAL_EVIDENCE_ID = f"{EVIDENCE_SOURCE}:bbbbbbbbbbbbbbbb"


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _write_manifest(path: Path, **fields: object) -> None:
    path.write_text(json.dumps(fields, indent=2), encoding="utf-8")


def _build_hgnc_source(data_root: Path) -> None:
    """3 genes, 1 alias -- HGNC:OLD1 (deprecated) -> HGNC:1097 (canonical)."""
    source = "hgnc.test"
    onto_dir = data_root / "ontology_snapshots" / source
    onto_dir.mkdir(parents=True)
    (onto_dir / "curies.txt").write_text(f"{GENE_1}\n{GENE_2}\n{GENE_3}\n", encoding="utf-8")
    _write_jsonl(onto_dir / "aliases.jsonl", [{"deprecated": GENE_1_DEPRECATED, "canonical": GENE_1}])

    _write_manifest(
        data_root / "manifests" / f"{source}.json",
        source=source,
        source_url="https://example.invalid/hgnc",
        retrieved_at="2026-01-01T00:00:00Z",
        license="CC0",
        sha256=sha256_dir(onto_dir),
        row_count=3,
        preprocessing_cmd=None,
        schema_version="0.1.0",
    )


def _build_ncbitaxon_source(data_root: Path) -> None:
    """1 species -- NCBITaxon:9606 (human)."""
    source = "ncbitaxon.test"
    onto_dir = data_root / "ontology_snapshots" / source
    onto_dir.mkdir(parents=True)
    (onto_dir / "curies.txt").write_text(f"{SPECIES_ID}\n", encoding="utf-8")

    _write_manifest(
        data_root / "manifests" / f"{source}.json",
        source=source,
        source_url="https://example.invalid/ncbitaxon",
        retrieved_at="2026-01-01T00:00:00Z",
        license="CC0",
        sha256=sha256_dir(onto_dir),
        row_count=1,
        preprocessing_cmd=None,
        schema_version="0.1.0",
    )


def _build_cellontology_source(data_root: Path) -> None:
    """2 cell types (CELL_TYPE_CHILD, CELL_TYPE_OTHER), each with a recorded
    ancestor closure [CELL_TYPE_PARENT, CELL_TYPE_ROOT].
    """
    source = "cellontology.test"
    onto_dir = data_root / "ontology_snapshots" / source
    onto_dir.mkdir(parents=True)
    (onto_dir / "curies.txt").write_text(
        f"{CELL_TYPE_CHILD}\n{CELL_TYPE_OTHER}\n{CELL_TYPE_PARENT}\n{CELL_TYPE_ROOT}\n", encoding="utf-8"
    )
    _write_jsonl(
        onto_dir / "cell_ontology.jsonl",
        [
            {"curie": CELL_TYPE_CHILD, "ancestors": [CELL_TYPE_PARENT, CELL_TYPE_ROOT]},
            {"curie": CELL_TYPE_OTHER, "ancestors": [CELL_TYPE_PARENT, CELL_TYPE_ROOT]},
        ],
    )

    _write_manifest(
        data_root / "manifests" / f"{source}.json",
        source=source,
        source_url="https://example.invalid/cellontology",
        retrieved_at="2026-01-01T00:00:00Z",
        license="CC0",
        sha256=sha256_dir(onto_dir),
        row_count=4,
        preprocessing_cmd=None,
        schema_version="0.1.0",
    )


def _build_evidence_source(data_root: Path) -> None:
    """2 evidence records: one interventional CRISPRi perturbation_effect,
    one observational co-expression (expression_observation).
    """
    evidence_source_dir = data_root / "evidence_records" / EVIDENCE_SOURCE
    evidence_source_dir.mkdir(parents=True)
    records_path = evidence_source_dir / "records.jsonl"

    # EVIDENCE-DECISION: each record's own `snapshot_hash` field (per
    # evidence.schema.json) attests to the sha256 of the raw upstream
    # source file it was extracted from -- a fact about provenance that
    # this fixture doesn't have a real upstream file for. Using a fixed
    # placeholder here is deliberate: this loader module never reads or
    # checks a record's `snapshot_hash` field (that is R-CITE-02, a
    # rules-module concern using `EvidenceLedger.snapshot_hashes()`), so the
    # placeholder never participates in this module's own hash-verification
    # path -- only the manifest's `sha256` (checked against the actual
    # records.jsonl file below) does.
    placeholder_snapshot_hash = "0" * 64

    interventional = {
        "schema_version": "0.1.0",
        "evidence_id": INTERVENTIONAL_EVIDENCE_ID,
        "source": EVIDENCE_SOURCE,
        "snapshot_hash": placeholder_snapshot_hash,
        "record_type": "perturbation_effect",
        "subject": {"id": GENE_1, "label": "GENE1"},
        "object": {"id": GENE_2, "label": "GENE2"},
        "species": SPECIES_ID,
        "cell_context": {"cell_type": CELL_TYPE_CHILD, "cell_line": "CLO:0009454", "state": None},
        "assay_context": {"assay": "CRISPRi_screen", "perturbation": f"CRISPRi:{GENE_1}"},
        "observation_type": "interventional",
        "effect": {
            "sign": "negative",
            "magnitude": -1.5,
            "magnitude_scale": "log2fc",
            "significance": 0.001,
            "n_replicates": 3,
        },
        "contradicts": [],
        "retrieved_at": "2026-01-01T00:00:00Z",
        "license": "CC0",
        "source_citation": None,
    }
    observational = {
        "schema_version": "0.1.0",
        "evidence_id": OBSERVATIONAL_EVIDENCE_ID,
        "source": EVIDENCE_SOURCE,
        "snapshot_hash": placeholder_snapshot_hash,
        "record_type": "expression_observation",
        "subject": {"id": GENE_1, "label": "GENE1"},
        "object": {"id": GENE_3, "label": "GENE3"},
        "species": SPECIES_ID,
        "cell_context": {"cell_type": CELL_TYPE_CHILD, "cell_line": None, "state": None},
        "assay_context": {"assay": "bulk-RNA-seq", "perturbation": None},
        "observation_type": "observational",
        "effect": {
            "sign": "positive",
            "magnitude": 0.6,
            "magnitude_scale": "pearson_r",
            "significance": 0.01,
            "n_replicates": None,
        },
        "contradicts": [],
        "retrieved_at": "2026-01-02T00:00:00Z",
        "license": "CC0",
        "source_citation": None,
    }
    _write_jsonl(records_path, [interventional, observational])

    _write_manifest(
        data_root / "manifests" / f"{EVIDENCE_SOURCE}.json",
        source=EVIDENCE_SOURCE,
        source_url="https://example.invalid/perturbseq",
        retrieved_at="2026-01-03T00:00:00Z",
        license="CC0",
        sha256=sha256_file(records_path),
        row_count=2,
        preprocessing_cmd="scripts/build_perturbseq.py",
        schema_version="0.1.0",
    )


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    """A tiny synthetic frozen data root: 3 genes, 1 species, 2 cell types
    (each with a recorded ancestor closure), 1 alias, 2 evidence records
    (one interventional CRISPRi perturbation_effect, one observational
    co-expression) -- all covered by manifests whose ``sha256`` matches the
    files actually on disk.
    """
    (tmp_path / "manifests").mkdir(parents=True)
    _build_hgnc_source(tmp_path)
    _build_ncbitaxon_source(tmp_path)
    _build_cellontology_source(tmp_path)
    _build_evidence_source(tmp_path)
    return tmp_path
