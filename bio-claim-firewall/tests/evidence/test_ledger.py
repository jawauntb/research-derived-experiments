from __future__ import annotations

import pytest

from src.evidence.errors import EvidenceError
from src.evidence.hashing import sha256_file
from src.evidence.loader import load_bundle

from conftest import (
    CELL_TYPE_CHILD,
    EVIDENCE_SOURCE,
    GENE_1,
    GENE_2,
    GENE_3,
    INTERVENTIONAL_EVIDENCE_ID,
    OBSERVATIONAL_EVIDENCE_ID,
)


def test_get_missing_evidence_id_raises_bad_citation(data_root):
    bundle = load_bundle(data_root)

    with pytest.raises(EvidenceError) as exc_info:
        bundle.ledger.get(f"{EVIDENCE_SOURCE}:0000000000000000")

    assert exc_info.value.fault_code == "BAD_CITATION"
    assert exc_info.value.details["evidence_id"] == f"{EVIDENCE_SOURCE}:0000000000000000"


def test_get_returns_the_record_for_a_known_id(data_root):
    bundle = load_bundle(data_root)

    record = bundle.ledger.get(INTERVENTIONAL_EVIDENCE_ID)

    assert record["evidence_id"] == INTERVENTIONAL_EVIDENCE_ID
    assert record["subject"]["id"] == GENE_1
    assert record["object"]["id"] == GENE_2
    assert record["observation_type"] == "interventional"


def test_list_by_matches_exact_subject_object_pair(data_root):
    bundle = load_bundle(data_root)

    hits = bundle.ledger.list_by(GENE_1, GENE_2)
    assert [r["evidence_id"] for r in hits] == [INTERVENTIONAL_EVIDENCE_ID]

    hits = bundle.ledger.list_by(GENE_1, GENE_3)
    assert [r["evidence_id"] for r in hits] == [OBSERVATIONAL_EVIDENCE_ID]

    # Reversed pair should not match -- list_by is directional.
    assert bundle.ledger.list_by(GENE_2, GENE_1) == []
    # Unrelated pair.
    assert bundle.ledger.list_by(GENE_2, GENE_3) == []


def test_list_by_filters_on_cell_type_and_assay(data_root):
    bundle = load_bundle(data_root)

    matched = bundle.ledger.list_by(GENE_1, GENE_2, cell_type=CELL_TYPE_CHILD, assay="CRISPRi_screen")
    assert [r["evidence_id"] for r in matched] == [INTERVENTIONAL_EVIDENCE_ID]

    unmatched_assay = bundle.ledger.list_by(GENE_1, GENE_2, assay="bulk-RNA-seq")
    assert unmatched_assay == []

    unmatched_cell_type = bundle.ledger.list_by(GENE_1, GENE_2, cell_type="CL:0000999")
    assert unmatched_cell_type == []


def test_list_by_filters_on_cell_line_and_state(data_root):
    bundle = load_bundle(data_root)

    # Interventional record has cell_line CLO:0009454, state None.
    assert len(bundle.ledger.list_by(GENE_1, GENE_2, cell_line="CLO:0009454")) == 1
    assert bundle.ledger.list_by(GENE_1, GENE_2, cell_line="CLO:9999999") == []
    assert len(bundle.ledger.list_by(GENE_1, GENE_2, state=None)) == 1  # None means "don't filter"


def test_count_reflects_total_loaded_records(data_root):
    bundle = load_bundle(data_root)
    assert bundle.ledger.count() == 2


def test_snapshot_hashes_maps_source_to_records_file_sha256(data_root):
    bundle = load_bundle(data_root)

    hashes = bundle.ledger.snapshot_hashes()

    assert set(hashes) == {EVIDENCE_SOURCE}
    records_path = data_root / "evidence_records" / EVIDENCE_SOURCE / "records.jsonl"
    assert hashes[EVIDENCE_SOURCE] == sha256_file(records_path)
