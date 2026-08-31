"""`evidence.load_bundle` succeeds, hash-verified, against the real Phase 2 pilot world.

Skips (rather than fails) if the downloads have not been run locally --
`data/` under version control ships only manifests/scripts/README/.gitignore,
never the raw or processed snapshot files themselves (see data/.gitignore).
Run `python3 data/scripts/download_*.py` (in any order; `sample_replogle_2022.py`
needs `download_hgnc.py` and `download_replogle_2022.py` to have run first)
to populate the tree this test loads.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from evidence import load_bundle
from evidence.errors import EvidenceError

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"

# One manifest source per data/scripts/download_*.py script. If any is
# missing, the pilot world has not been (fully) downloaded locally.
EXPECTED_SOURCES = (
    "hgnc.2026_pilot",
    "ncbitaxon.2026_pilot",
    "cellontology.2026_pilot",
    "cellline.2026_pilot",
    "reactome.2026_pilot",
    "perturbseq.replogle_2022",
)


def _missing_sources() -> list[str]:
    manifests_dir = DATA_ROOT / "manifests"
    missing = []
    for source in EXPECTED_SOURCES:
        has_manifest = (manifests_dir / f"{source}.yaml").is_file() or (
            manifests_dir / f"{source}.json"
        ).is_file()
        has_data = (DATA_ROOT / "ontology_snapshots" / source).is_dir() or (
            DATA_ROOT / "evidence_records" / source / "records.jsonl"
        ).is_file()
        if not (has_manifest and has_data):
            missing.append(source)
    return missing


def _skip_if_not_downloaded() -> None:
    missing = _missing_sources()
    if missing:
        pytest.skip(
            "run scripts/download_*.py first (missing locally: "
            + ", ".join(missing)
            + ")"
        )


def test_load_bundle_succeeds_without_hash_mismatch():
    _skip_if_not_downloaded()

    try:
        bundle = load_bundle(DATA_ROOT)
    except EvidenceError as exc:
        pytest.fail(f"load_bundle raised EvidenceError({exc.fault_code!r}): {exc}")

    assert set(bundle.manifests.keys()) == set(EXPECTED_SOURCES)
    # 5 ontology sources contribute curies; 1 evidence source contributes ledger records.
    assert len(bundle.curies) > 0
    assert bundle.ledger.count() > 0
    # Every manifest's declared sha256 must equal what load_bundle actually verified.
    hashes = bundle.ledger.snapshot_hashes()
    assert hashes, "expected at least the evidence source's hash in snapshot_hashes()"
    for source, digest in hashes.items():
        assert bundle.manifests[source].sha256 == digest


def test_expected_curie_prefixes_present():
    _skip_if_not_downloaded()
    bundle = load_bundle(DATA_ROOT)

    prefixes = {curie.split(":", 1)[0] for curie in bundle.curies}
    # hgnc, ncbitaxon, cellontology (CL), cellline (CLO), reactome (REACT)
    assert {"HGNC", "NCBITaxon", "CL", "CLO", "REACT"} <= prefixes


def test_replogle_evidence_records_are_perturbation_effect_human_k562():
    _skip_if_not_downloaded()
    bundle = load_bundle(DATA_ROOT)

    sample_ids = list(
        bundle.ledger.list_by(subject_id="HGNC:4170", object_id="HGNC:2528")
    )
    assert sample_ids, (
        "expected the hand-verified GATA1 -> CTSC record to be loadable by ledger.list_by"
    )
    record = sample_ids[0]
    assert record["record_type"] == "perturbation_effect"
    assert record["species"] == "NCBITaxon:9606"
    assert record["cell_context"]["cell_line"] == "CLO:0007059"
    assert record["observation_type"] == "interventional"


def test_all_sources_missing_reports_every_source():
    """`_missing_sources()` itself is exercised even in environments where the
    pilot world IS present, by checking it against an empty scratch root."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        empty_root = Path(tmp)
        manifests_dir = empty_root / "manifests"
        missing = []
        for source in EXPECTED_SOURCES:
            has_manifest = (manifests_dir / f"{source}.yaml").is_file() or (
                manifests_dir / f"{source}.json"
            ).is_file()
            if not has_manifest:
                missing.append(source)
        assert missing == list(EXPECTED_SOURCES)
