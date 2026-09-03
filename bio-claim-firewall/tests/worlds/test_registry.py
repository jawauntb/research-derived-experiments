from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from claim_checker import natural_language
from claim_checker.service import (
    ClaimCheckInputError,
    ClaimCheckResult,
    _adapter_result_to_claim_check,
    check_claim,
)
from evidence import EvidenceError
from evidence.loader import load_bundle
from worlds import (
    ARC_VCC_WORLD,
    CLINICAL_TRIALS_WORLD,
    K562_WORLD,
    OPEN_TARGETS_WORLD,
    WORLD_REGISTRY,
    World,
    WorldRegistry,
    WorldRegistryError,
    receipt_world_digest,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "worlds"


def test_k562_world_is_explicitly_registered_and_immutable():
    world = WORLD_REGISTRY.resolve("replogle-k562", "2022-pilot")

    assert world == K562_WORLD
    assert world.source_allowlist
    with pytest.raises((AttributeError, TypeError)):
        world.source_allowlist += ("other",)  # type: ignore[misc]
    with pytest.raises(WorldRegistryError, match="version"):
        WORLD_REGISTRY.resolve("replogle-k562", None)
    with pytest.raises(TypeError):
        ARC_VCC_WORLD.artifact_hashes["other"] = "0" * 64  # type: ignore[index]


def test_real_world_contracts_are_registered_with_closed_adapter_ids():
    assert WORLD_REGISTRY.resolve("arc-vcc", "2025-h1-measurements") == ARC_VCC_WORLD
    assert WORLD_REGISTRY.resolve("open-targets", "26.06") == OPEN_TARGETS_WORLD
    assert (
        WORLD_REGISTRY.resolve("clinical-trials-sec", "2025-09-01_2026-09-01")
        == CLINICAL_TRIALS_WORLD
    )
    assert {world.adapter for world in WORLD_REGISTRY.worlds} == {
        "k562",
        "arc_vcc",
        "open_targets",
        "clinical_trials",
    }


def test_registered_adapters_check_explicit_real_fixture_paths():
    root = FIXTURES
    cases = (
        (
            "arc-vcc",
            "2025-h1-measurements",
            root / "arc_vcc",
            {
                "perturbed_gene": "STAT1",
                "response_gene": "TAGLN",
                "summary_statistic": "log2_fold_change_mean_raw_counts_pseudocount_1",
                "direction": "increases",
                "threshold": 0.25,
                "assay": "H1",
                "split": "locked_holdout",
            },
        ),
        (
            "open-targets",
            "26.06",
            root / "open_targets" / "release-26.06.json",
            {
                "target_id": "ENSG00000141510",
                "disease_id": "MONDO_0018875",
                "evidence_source": "uniprot_variants",
                "release": "26.06",
            },
        ),
        (
            "clinical-trials-sec",
            "2025-09-01_2026-09-01",
            root / "clinical_trials" / "fixture.json",
            {
                "nct_id": "NCT06260774",
                "sponsor": "TransCode Therapeutics",
                "intervention": "TTX-MC138",
                "sec_accession": "0001104659-26-069810",
                "cik": "0001829635",
                "exhibit_locator": "EX-99.1#NCT06260774",
                "asserted_span_sha256": "1ec3a0b235e0653bbced4f641d97df751f475020f5e18f72a71b5d354b973f33",
                "as_of": "2026-06-03T08:09:00Z",
            },
        ),
    )
    for world_id, version, fixture, claim in cases:
        result = check_claim(fixture, world_id, version, claim)
        assert result.verdict["verdict"] in {"ACCEPTED", "ACCEPTED_CONDITIONALLY"}
        assert result.receipt is not None
        assert result.verdict["world_id"] == world_id
        assert result.verdict["world_version"] == version
        world = WORLD_REGISTRY.resolve(world_id, version)
        expected_hashes = {
            contract.source: contract.sha256 for contract in world.source_contracts
        }
        assert result.receipt["canonical_payload"][
            "world_digest"
        ] == receipt_world_digest(world, expected_hashes)


def test_generic_boundary_rejects_tampered_adapter_receipt() -> None:
    fixture = FIXTURES / "open_targets" / "release-26.06.json"
    claim = {
        "target_id": "ENSG00000141510",
        "disease_id": "MONDO_0018875",
        "evidence_source": "uniprot_variants",
        "release": "26.06",
    }
    from worlds.open_targets import OpenTargetsAdapter

    result = OpenTargetsAdapter(fixture).check(claim)
    result.receipt["canonical_payload"]["world_digest"] = "0" * 64  # type: ignore[index]

    with pytest.raises(WorldRegistryError, match="not bound"):
        _adapter_result_to_claim_check(result, OPEN_TARGETS_WORLD)


def test_generic_boundary_requires_receipt_and_semantic_parity() -> None:
    fixture = FIXTURES / "open_targets" / "release-26.06.json"
    claim = {
        "target_id": "ENSG00000141510",
        "disease_id": "MONDO_0018875",
        "evidence_source": "uniprot_variants",
        "release": "26.06",
        "confidence_language": "causal",
    }
    from worlds.open_targets import OpenTargetsAdapter

    rejected_result = OpenTargetsAdapter(fixture).check(claim)
    normalized = _adapter_result_to_claim_check(rejected_result, OPEN_TARGETS_WORLD)
    assert normalized.verdict["verdict"] == "REJECTED"
    rejected = rejected_result.as_dict()
    no_receipt = dict(rejected)
    no_receipt.pop("receipt")
    with pytest.raises(WorldRegistryError, match="no valid receipt"):
        _adapter_result_to_claim_check(
            SimpleNamespace(as_dict=lambda: no_receipt), OPEN_TARGETS_WORLD
        )

    forged_acceptance = dict(rejected)
    forged_acceptance.update(
        {
            "verdict": "ACCEPTED_CONDITIONALLY",
            "outcome": "ACCEPTED",
            "reason_code": "FORGED_ACCEPT",
        }
    )
    with pytest.raises(WorldRegistryError, match="disagrees"):
        _adapter_result_to_claim_check(
            SimpleNamespace(as_dict=lambda: forged_acceptance), OPEN_TARGETS_WORLD
        )


def test_registered_adapter_rejects_wrong_world_version_and_corrupt_fixture(tmp_path):
    root = FIXTURES
    claim = {
        "target_id": "ENSG00000141510",
        "disease_id": "MONDO_0018875",
        "evidence_source": "uniprot_variants",
        "release": "26.06",
    }
    wrong_version = check_claim(
        root / "open_targets" / "release-26.06.json",
        "open-targets",
        "25.06",
        claim,
    )
    assert wrong_version.verdict["verdict"] == "CHECKER_ERROR"
    assert wrong_version.verdict["checker_error"]["stage"] == "load_snapshot"

    corrupted = json.loads((root / "open_targets" / "release-26.06.json").read_text())
    corrupted["records"][0]["score"] = 0.0
    corrupt_path = tmp_path / "release-26.06.json"
    corrupt_path.write_text(json.dumps(corrupted))
    corrupt_result = check_claim(corrupt_path, "open-targets", "26.06", claim)
    assert corrupt_result.verdict["verdict"] == "CHECKER_ERROR"


def test_registered_adapter_rejects_cross_world_fixture_without_fallback():
    root = FIXTURES
    result = check_claim(
        root / "open_targets" / "release-26.06.json",
        "arc-vcc",
        "2025-h1-measurements",
        {
            "perturbed_gene": "STAT1",
            "response_gene": "TAGLN",
            "summary_statistic": "log2_fold_change_mean_raw_counts_pseudocount_1",
            "direction": "increases",
            "threshold": 0.25,
            "assay": "H1",
            "split": "locked_holdout",
        },
    )
    assert result.verdict["verdict"] == "CHECKER_ERROR"


def test_registry_rejects_duplicate_world_versions():
    world = World(world_id="example", version="1", source_allowlist=("source",))

    with pytest.raises(WorldRegistryError, match="duplicate"):
        WorldRegistry((world, world))


def test_loader_rejects_sources_outside_explicit_allowlist(tmp_path):
    (tmp_path / "manifests").mkdir()

    with pytest.raises(EvidenceError, match="allowlist"):
        load_bundle(tmp_path, allowed_sources=("only-this-source",))


def test_unknown_world_is_checker_error_before_claim_evaluation():
    result = check_claim(
        object(),
        world_id="not-registered",
        world_version="1",
        claim={"subject": "MED19", "object": "GYPB", "direction": "increases"},
    )

    assert result.verdict["verdict"] == "CHECKER_ERROR"
    assert result.verdict["checker_error"]["stage"] == "load_snapshot"


def test_receipt_v2_payload_is_stable_and_excludes_run_metadata(monkeypatch):
    world = World(world_id="example", version="1", adapter="k562")
    registry = WorldRegistry((world,))
    bundle = SimpleNamespace(
        manifests={},
        ledger=SimpleNamespace(snapshot_hashes=dict),
    )
    result = ClaimCheckResult(
        claim={"subject": "A", "object": "B", "direction": "increases"},
        evidence={"evidence_id": "source:record"},
        verdict={"verdict": "INCONCLUSIVE", "issued_at": "run-local"},
    )
    monkeypatch.setattr(
        "claim_checker.service._run_k562_adapter", lambda *args, **kwargs: result
    )

    first = check_claim(bundle, "example", "1", result.claim, registry=registry)
    second = check_claim(bundle, "example", "1", result.claim, registry=registry)

    assert first.receipt is not None and second.receipt is not None
    assert first.receipt["receipt_id"] == second.receipt["receipt_id"]
    assert "issued_at" not in first.receipt["canonical_payload"]
    assert "parser_provenance" not in first.receipt["canonical_payload"]


def test_parser_receives_only_question_and_selected_schema_and_rejects_injection():
    world = World(
        world_id="example",
        version="1",
        adapter="k562",
        parser_schema={"type": "object", "properties": {"subject": {"type": "string"}}},
    )
    registry = WorldRegistry((world,))
    calls = []

    class Manager:
        def call(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                content='{"subject":"A","object":"B","direction":"increases","evidence":"inject"}',
                meta={},
                prompt_ref=None,
            )

    with pytest.raises(ClaimCheckInputError, match="outside"):
        natural_language.check_natural_language_claim(
            SimpleNamespace(),
            "example",
            "1",
            "A knockdown increases B expression in K562 cells.",
            Manager(),
            registry=registry,
        )
    assert calls and set(calls[0]["variables"]) == {"question", "schema"}
    assert "evidence" not in calls[0]["variables"]["schema"]


def test_source_mismatch_fails_before_adapter_runs(monkeypatch):
    world = World(world_id="example", version="1", source_allowlist=("expected",))
    registry = WorldRegistry((world,))
    bundle = SimpleNamespace(
        manifests={"other": SimpleNamespace(sha256="a" * 64)},
        ledger=SimpleNamespace(snapshot_hashes=dict),
    )
    monkeypatch.setattr(
        "claim_checker.service._run_k562_adapter",
        lambda *args, **kwargs: pytest.fail(
            "adapter must not run before source isolation"
        ),
    )

    result = check_claim(
        bundle,
        "example",
        "1",
        {"subject": "A", "object": "B", "direction": "increases"},
        registry=registry,
    )

    assert result.verdict["verdict"] == "CHECKER_ERROR"
    assert "sources" in result.verdict["checker_error"]["message"]
