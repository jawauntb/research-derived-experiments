from __future__ import annotations

import json
from pathlib import Path

import pytest
from worlds.arc_vcc import (
    ArcVCCAdapter,
    ArcVCCIntegrityError,
    check_arc_vcc_claim,
    load_fixture,
    validate_fixture,
)

FIXTURE = Path(__file__).parents[1] / "fixtures" / "worlds" / "arc_vcc"


def claim(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "perturbed_gene": "STAT1",
        "response_gene": "TAGLN",
        "summary_statistic": "log2_fold_change_mean_raw_counts_pseudocount_1",
        "direction": "increases",
        "threshold": 0.25,
        "assay": "H1",
        "split": "locked_holdout",
    }
    value.update(changes)
    return value


@pytest.fixture()
def adapter() -> ArcVCCAdapter:
    return ArcVCCAdapter.from_path(FIXTURE)


def test_fixture_metadata_is_real_hash_bound_and_split_disjoint() -> None:
    report = validate_fixture(FIXTURE)
    assert report["license"] == "MIT"
    assert report["row_count"] == 6
    assert report["split_counts"] == {"development": 1, "locked_holdout": 5}
    assert report["raw_source_bytes"] == 4_991_092
    assert report["source_commit"] == "ddfc5df73c997b2f113a560bd863fb068f2b453a"
    fixture = load_fixture(FIXTURE)
    assert fixture.metadata.source_kind == "official_real_subset"


@pytest.mark.parametrize(
    ("changes", "outcome", "rule"),
    [
        ({}, "ACCEPTED", "ARC-H1-001"),
        ({"direction": "decreases"}, "REJECTED", "ARC-H1-002"),
        (
            {
                "perturbed_gene": "MED12",
                "response_gene": "PODXL",
                "direction": "decreases",
            },
            "ACCEPTED",
            "ARC-H1-001",
        ),
        (
            {"perturbed_gene": "STAT1", "response_gene": "HADHA", "direction": "null"},
            "ACCEPTED",
            "ARC-H1-001",
        ),
        (
            {
                "perturbed_gene": "STAT1",
                "response_gene": "HADHA",
                "direction": "increases",
            },
            "REJECTED",
            "ARC-H1-003",
        ),
    ],
)
def test_organic_direction_controls(
    adapter: ArcVCCAdapter, changes: dict[str, object], outcome: str, rule: str
) -> None:
    result = adapter.check(claim(**changes))
    assert result.outcome == outcome
    assert result.winning_rule and result.winning_rule["id"] == rule
    assert len(result.receipt["receipt_id"]) == 64


def test_receipt_is_stable_and_run_metadata_free(adapter: ArcVCCAdapter) -> None:
    first = adapter.check(claim()).as_dict()
    second = adapter.check(claim()).as_dict()
    assert first == second
    assert first["receipt"]["receipt_id"] == first["receipt"]["receipt_id"]
    assert "issued_at" not in first["receipt"]
    assert len(first["receipt"]["canonical_payload"]["world_digest"]) == 64
    assert (
        first["source_hashes"] == first["receipt"]["canonical_payload"]["source_hashes"]
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"assay": "H2"},
        {"summary_statistic": "median_log2_expression"},
        {"threshold": 0.5},
        {"split": "development"},
        {"perturbed_gene": "GENE_X"},
    ],
)
def test_scope_and_identity_mutations_do_not_accept(
    adapter: ArcVCCAdapter, changes: dict[str, object]
) -> None:
    result = adapter.check(claim(**changes))
    assert result.outcome in {"INCONCLUSIVE", "REJECTED"}
    assert result.outcome != "ACCEPTED"


def test_wrong_world_identity_fails_closed(adapter: ArcVCCAdapter) -> None:
    result = adapter.check(claim(world_id="open-targets"))
    assert result.outcome == "CHECKER_ERROR"
    assert "world identity" in result.reason


def test_corruption_fails_closed(tmp_path: Path) -> None:
    destination = tmp_path / "arc_vcc"
    destination.mkdir()
    for name in ("metadata.json", "measurements.jsonl"):
        (destination / name).write_bytes((FIXTURE / name).read_bytes())
    (destination / "measurements.jsonl").write_text(
        (destination / "measurements.jsonl")
        .read_text(encoding="utf-8")
        .replace("0.577988734679", "0.577988734680"),
        encoding="utf-8",
    )
    with pytest.raises(ArcVCCIntegrityError):
        load_fixture(destination)
    result = check_arc_vcc_claim(destination, claim())
    assert result.outcome == "CHECKER_ERROR"


def test_metadata_tamper_fails_registered_artifact_binding(tmp_path: Path) -> None:
    destination = tmp_path / "arc_vcc"
    destination.mkdir()
    for name in ("metadata.json", "measurements.jsonl"):
        (destination / name).write_bytes((FIXTURE / name).read_bytes())
    metadata = json.loads((destination / "metadata.json").read_text(encoding="utf-8"))
    metadata["retrieval_at"] = "2099-01-01T00:00:00Z"
    (destination / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ArcVCCIntegrityError, match="artifact hashes"):
        load_fixture(destination)


def test_split_leakage_fails_closed(tmp_path: Path) -> None:
    destination = tmp_path / "arc_vcc"
    destination.mkdir()
    for name in ("metadata.json", "measurements.jsonl"):
        (destination / name).write_bytes((FIXTURE / name).read_bytes())
    rows = [
        json.loads(line)
        for line in (destination / "measurements.jsonl").read_text().splitlines()
    ]
    rows.append({**rows[0], "measurement_id": "leak", "split": "locked_holdout"})
    payload = (
        "\n".join(
            json.dumps(row, separators=(",", ":"), sort_keys=True) for row in rows
        )
        + "\n"
    )
    (destination / "measurements.jsonl").write_text(payload, encoding="utf-8")
    metadata = json.loads((destination / "metadata.json").read_text())
    import hashlib

    metadata["measurement_sha256"] = hashlib.sha256(payload.encode()).hexdigest()
    metadata["row_count"] = 7
    (destination / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ArcVCCIntegrityError, match="split leakage"):
        load_fixture(destination)
