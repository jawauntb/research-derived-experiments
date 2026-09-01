"""Regression checks for the local product against the downloaded pilot world."""

from __future__ import annotations

from pathlib import Path

import pytest

from claim_checker import check_k562_claim
from evidence import load_bundle


DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_REQUIRED_SOURCES = (
    "hgnc.2026_pilot",
    "ncbitaxon.2026_pilot",
    "cellontology.2026_pilot",
    "cellline.2026_pilot",
    "reactome.2026_pilot",
    "perturbseq.replogle_2022",
)


def _skip_if_pilot_world_is_absent() -> None:
    missing = [
        source
        for source in _REQUIRED_SOURCES
        if not (
            (DATA_ROOT / "ontology_snapshots" / source).is_dir()
            or (DATA_ROOT / "evidence_records" / source / "records.jsonl").is_file()
        )
    ]
    if missing:
        pytest.skip(
            "run data download scripts first (missing: " + ", ".join(missing) + ")"
        )


@pytest.fixture(scope="module")
def real_bundle():
    _skip_if_pilot_world_is_absent()
    return load_bundle(DATA_ROOT)


def test_k562_checker_accepts_a_known_frozen_replogle_record(real_bundle):
    result = check_k562_claim(real_bundle, "MED19", "GYPB", "increases")

    assert result.verdict["verdict"] == "ACCEPTED_CONDITIONALLY"
    assert result.evidence is not None
    assert result.evidence["source"] == "perturbseq.replogle_2022"
    assert result.evidence["citation"].startswith("Replogle, J.M. et al.")
    assert result.verdict["derivation"]["applied_rules"][-1] == "R-EDGE-02"


def test_k562_checker_rejects_the_reversed_direction_for_that_same_record(real_bundle):
    result = check_k562_claim(real_bundle, "MED19", "GYPB", "decreases")

    assert result.verdict["verdict"] == "REJECTED"
    assert result.verdict["fault_code"] == "SIGN_MISMATCH"
