from __future__ import annotations

import pytest
from types import SimpleNamespace

from claim_checker.service import ClaimCheckInputError, ClaimCheckResult, check_claim
from claim_checker import natural_language
from evidence import EvidenceError
from evidence.loader import load_bundle
from worlds import K562_WORLD, WORLD_REGISTRY, World, WorldRegistry, WorldRegistryError


def test_k562_world_is_explicitly_registered_and_immutable():
    world = WORLD_REGISTRY.resolve("replogle-k562", "2022-pilot")

    assert world == K562_WORLD
    assert world.source_allowlist
    with pytest.raises((AttributeError, TypeError)):
        world.source_allowlist += ("other",)  # type: ignore[misc]
    with pytest.raises(WorldRegistryError, match="version"):
        WORLD_REGISTRY.resolve("replogle-k562", None)


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
        ledger=SimpleNamespace(snapshot_hashes=lambda: {}),
    )
    result = ClaimCheckResult(
        claim={"subject": "A", "object": "B", "direction": "increases"},
        evidence={"evidence_id": "source:record"},
        verdict={"verdict": "INCONCLUSIVE", "issued_at": "run-local"},
    )
    monkeypatch.setattr("claim_checker.service._run_k562_adapter", lambda *args, **kwargs: result)

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
            SimpleNamespace(), "example", "1", "A increases B", Manager(), registry=registry
        )
    assert calls and set(calls[0]["variables"]) == {"question", "schema"}
    assert "evidence" not in calls[0]["variables"]["schema"]


def test_source_mismatch_fails_before_adapter_runs(monkeypatch):
    world = World(world_id="example", version="1", source_allowlist=("expected",))
    registry = WorldRegistry((world,))
    bundle = SimpleNamespace(
        manifests={"other": SimpleNamespace(sha256="a" * 64)},
        ledger=SimpleNamespace(snapshot_hashes=lambda: {}),
    )
    monkeypatch.setattr(
        "claim_checker.service._run_k562_adapter",
        lambda *args, **kwargs: pytest.fail("adapter must not run before source isolation"),
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
