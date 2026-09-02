from __future__ import annotations

import hashlib
import json
from pathlib import Path

from worlds.open_targets import (
    OpenTargetsAdapter,
    OpenTargetsClaim,
    OutcomeKind,
    check_open_targets_claim,
)

FIXTURE = (
    Path(__file__).parents[1]
    / "fixtures"
    / "worlds"
    / "open_targets"
    / "release-26.06.json"
)


def _claim(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "target_id": "ENSG00000141510",
        "disease_id": "MONDO_0018875",
        "evidence_source": "uniprot_variants",
        "release": "26.06",
    }
    value.update(changes)
    return value


def test_exact_source_specific_release_row_is_accepted_and_stable() -> None:
    adapter = OpenTargetsAdapter(FIXTURE)
    first = adapter.check(_claim())
    second = adapter.check(_claim())
    assert first.verdict is OutcomeKind.ACCEPTED_CONDITIONALLY
    assert first.outcome == "ACCEPTED"
    assert first.evidence is not None and first.evidence["score"] == 0.9919541334408821
    assert first.receipt == second.receipt


def test_release_source_score_and_scope_mutations_never_upgrade() -> None:
    adapter = OpenTargetsAdapter(FIXTURE)
    assert adapter.check(_claim(release="25.06")).reason_code == "WRONG_RELEASE"
    assert adapter.check(_claim(score=0.82)).reason_code == "SCORE_MISMATCH"
    assert (
        adapter.check(_claim(score_threshold=0.8)).reason_code
        == "UNSUPPORTED_SCORE_THRESHOLD"
    )
    assert (
        adapter.check(_claim(confidence_language="causal efficacy")).reason_code
        == "UNSUPPORTED_CLAIM_SCOPE"
    )


def test_tuple_missing_from_compact_projection_is_inconclusive() -> None:
    result = OpenTargetsAdapter(FIXTURE).check(_claim(evidence_source="missing_source"))

    assert result.verdict is OutcomeKind.INCONCLUSIVE
    assert result.reason_code == "ASSOCIATION_NOT_IN_PROJECTION"


def test_foreign_world_and_corrupt_fixture_fail_closed(tmp_path: Path) -> None:
    adapter = OpenTargetsAdapter(FIXTURE)
    foreign = _claim(
        world_id="clinical-trials-sec", world_version="2025-09-01_2026-09-01"
    )
    assert adapter.check(foreign).verdict is OutcomeKind.CHECKER_ERROR
    foreign_wrong_release = _claim(
        release="25.06",
        world_id="clinical-trials-sec",
        world_version="2025-09-01_2026-09-01",
    )
    assert adapter.check(foreign_wrong_release).verdict is OutcomeKind.CHECKER_ERROR
    corrupted = json.loads(FIXTURE.read_text(encoding="utf-8"))
    corrupted["records"][0]["score"] = 0.83
    path = tmp_path / "release-26.06.json"
    path.write_text(json.dumps(corrupted), encoding="utf-8")
    assert check_open_targets_claim(_claim(), path).verdict is OutcomeKind.CHECKER_ERROR

    typed_foreign = OpenTargetsClaim(
        target_id="ENSG00000141510",
        disease_id="MONDO_0018875",
        evidence_source="uniprot_variants",
        release="26.06",
        world_id="clinical-trials-sec",
        world_version="2025-09-01_2026-09-01",
    )
    assert adapter.check(typed_foreign).verdict is OutcomeKind.CHECKER_ERROR


def test_hash_consistent_forged_source_is_rejected_by_registry_binding(
    tmp_path: Path,
) -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    fixture["source_hashes"]["open-targets-graphql-26-06"] = "f" * 64
    payload = {
        key: fixture[key]
        for key in ("schema_version", "world_id", "version", "source_hashes", "records")
    }
    fixture["integrity_sha256"] = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    path = tmp_path / "release-26.06.json"
    path.write_text(json.dumps(fixture), encoding="utf-8")

    assert check_open_targets_claim(_claim(), path).verdict is OutcomeKind.CHECKER_ERROR


def test_self_consistent_forged_projection_is_rejected_by_artifact_binding(
    tmp_path: Path,
) -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    fixture["records"][0]["score"] = 0.123456
    payload = {
        key: fixture[key]
        for key in ("schema_version", "world_id", "version", "source_hashes", "records")
    }
    fixture["integrity_sha256"] = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    path = tmp_path / "release-26.06.json"
    path.write_text(json.dumps(fixture), encoding="utf-8")

    assert (
        check_open_targets_claim(_claim(score=0.123456), path).verdict
        is OutcomeKind.CHECKER_ERROR
    )
