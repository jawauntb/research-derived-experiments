"""Tests for the untrusted natural-language boundary of the local checker."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from claim_checker import natural_language
from claim_checker.__main__ import format_natural_language_result
from claim_checker.service import ClaimCheckInputError, ClaimCheckResult


class _FakeManager:
    def __init__(
        self,
        content: str,
        *,
        prompt_ref: str | None = "claim_parser/k562_gene_effect@v1",
    ) -> None:
        self.content = content
        self.prompt_ref = prompt_ref
        self.calls: list[dict] = []

    def call(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            content=self.content,
            meta={"provider": "openai", "model": "gpt-4o-mini-2024-07-18"},
            prompt_ref=self.prompt_ref,
            prompt_version="v1",
        )


def test_natural_language_is_reduced_to_the_three_field_checker_contract(monkeypatch):
    captured: dict = {}

    def fake_check(bundle, subject, object_, direction, *, checker_version):
        captured.update(
            bundle=bundle,
            subject=subject,
            object=object_,
            direction=direction,
            checker_version=checker_version,
        )
        return ClaimCheckResult(
            claim={
                "subject": {"label": subject},
                "relation": direction,
                "object": {"label": object_},
            },
            evidence={
                "evidence_id": "replogle:test",
                "effect_sign": "positive",
                "magnitude": 1.0,
                "magnitude_scale": "zscore",
                "significance": None,
                "citation": None,
            },
            verdict={"verdict": "ACCEPTED_CONDITIONALLY"},
        )

    monkeypatch.setattr(natural_language, "check_k562_claim", fake_check)
    manager = _FakeManager(
        json.dumps({"subject": "MED19", "object": "GYPB", "direction": "increases"})
    )

    result = natural_language.check_natural_language_k562_claim(
        object(),
        "Does MED19 knockdown increase GYPB expression in K562?",
        manager,
        checker_version="0.1.0",
    )

    assert captured["bundle"] is not None
    assert captured["subject"] == "MED19"
    assert captured["object"] == "GYPB"
    assert captured["direction"] == "increases"
    assert captured["checker_version"] == "0.1.0"
    assert manager.calls == [
        {
            "task": "claim_parser",
            "variables": {
                "question": "Does MED19 knockdown increase GYPB expression in K562?"
            },
        }
    ]
    assert result.interpretation == {
        "mode": "untrusted_llm",
        "question": "Does MED19 knockdown increase GYPB expression in K562?",
        "subject": "MED19",
        "object": "GYPB",
        "direction": "increases",
        "provider": "openai",
        "model": "gpt-4o-mini-2024-07-18",
        "prompt_ref": "claim_parser/k562_gene_effect@v1",
    }
    assert result.as_dict()["verdict"] == {"verdict": "ACCEPTED_CONDITIONALLY"}
    assert (
        "Question (untrusted): 'Does MED19 knockdown increase GYPB expression in K562?'"
        in (format_natural_language_result(result))
    )


@pytest.mark.parametrize(
    "response",
    [
        "not json",
        json.dumps({"subject": "MED19", "object": "GYPB"}),
        json.dumps(
            {
                "subject": "MED19",
                "object": "GYPB",
                "direction": "increases",
                "citation": "invented",
            }
        ),
    ],
)
def test_natural_language_refuses_any_model_output_outside_its_tiny_contract(response):
    with pytest.raises(ClaimCheckInputError, match="subject, object, and direction"):
        natural_language.check_natural_language_k562_claim(
            object(),
            "MED19 knockdown increases GYPB expression in K562 cells.",
            _FakeManager(response),
        )


def test_natural_language_rejects_an_oversized_prompt_before_a_model_call():
    manager = _FakeManager(
        json.dumps({"subject": "MED19", "object": "GYPB", "direction": "increases"})
    )

    with pytest.raises(ClaimCheckInputError, match="2,000 character limit"):
        natural_language.check_natural_language_k562_claim(
            object(), "x" * 2_001, manager
        )

    assert manager.calls == []


@pytest.mark.parametrize(
    "question",
    [
        "MED19 knockdown increases GYPB and decreases RPS2 in K562 cells.",
        "MED19 knockdown increases GYPB while TAF1 knockdown increases RPS2.",
    ],
)
def test_natural_language_rejects_multiple_directional_claims_before_model_call(
    question,
):
    manager = _FakeManager(
        json.dumps({"subject": "MED19", "object": "GYPB", "direction": "increases"})
    )

    with pytest.raises(ClaimCheckInputError, match="exactly one directional claim"):
        natural_language.check_natural_language_k562_claim(object(), question, manager)

    assert manager.calls == []


@pytest.mark.parametrize(
    ("question", "direction"),
    [
        ("Does MED19 knockdown raise GYPB expression in K562?", "increases"),
        ("Does MED19 knockdown reduce GYPB expression in K562?", "decreases"),
        ("Does MED19 knockdown upregulate GYPB expression in K562?", "increases"),
        ("Does MED19 knockdown suppress GYPB expression in K562?", "decreases"),
    ],
)
def test_natural_language_accepts_directional_synonyms_when_parser_agrees(
    monkeypatch, question, direction
):
    monkeypatch.setattr(
        natural_language,
        "check_k562_claim",
        lambda *args, **kwargs: ClaimCheckResult(
            claim={}, evidence={}, verdict={"verdict": "REJECTED"}
        ),
    )
    manager = _FakeManager(
        json.dumps({"subject": "MED19", "object": "GYPB", "direction": direction})
    )

    result = natural_language.check_natural_language_k562_claim(
        object(), question, manager
    )

    assert result.interpretation["direction"] == direction
    assert len(manager.calls) == 1


@pytest.mark.parametrize(
    "parsed",
    [
        {"subject": "TAF1", "object": "GYPB", "direction": "increases"},
        {"subject": "MED19", "object": "RPS2", "direction": "increases"},
        {"subject": "MED19", "object": "GYPB", "direction": "decreases"},
    ],
)
def test_natural_language_rejects_parser_claim_detached_from_question(parsed):
    manager = _FakeManager(json.dumps(parsed))

    with pytest.raises(
        ClaimCheckInputError, match="does not match|exactly once|gene roles"
    ):
        natural_language.check_natural_language_k562_claim(
            object(),
            "Does MED19 knockdown increase GYPB expression in K562?",
            manager,
        )


def test_natural_language_rejects_swapped_parser_roles():
    manager = _FakeManager(
        json.dumps({"subject": "GYPB", "object": "MED19", "direction": "increases"})
    )

    with pytest.raises(ClaimCheckInputError, match="gene roles|subject/object roles"):
        natural_language.check_natural_language_k562_claim(
            object(),
            "Does MED19 knockdown increase GYPB expression in K562?",
            manager,
        )


@pytest.mark.parametrize(
    "question",
    [
        "Within K562 cells, MED19 knockdown does not increase GYPB expression.",
        "Within K562 and mouse cortical neurons, MED19 knockdown increases GYPB.",
        "Within K562 cells, MED19 knockout after knockdown increases GYPB.",
        "Within K562 cells, MED19 knockdown always causes GYPB to increase.",
        "Within K562 cells, MED19 increases GYPB expression.",
        "Within K562 and HEK293 cells, MED19 knockdown increases GYPB expression.",
        "Within K562 and HeLa cells, MED19 knockdown increases GYPB expression.",
        "Within K562 cells, MED19 knockdown causing increased GYPB expression.",
        "Within K562 cells, MED19 knockdown causally increases GYPB expression.",
        "Within K562 cells, MED19 knockdown drives increased GYPB expression.",
    ],
)
def test_natural_language_rejects_unsupported_k562_scope_before_model(question):
    manager = _FakeManager(
        json.dumps({"subject": "MED19", "object": "GYPB", "direction": "increases"})
    )

    with pytest.raises(ClaimCheckInputError):
        natural_language.check_natural_language_k562_claim(object(), question, manager)

    assert manager.calls == []


def test_natural_language_rejects_repeated_entities_before_model():
    bundle = SimpleNamespace(labels={"HGNC:1": "MED19", "HGNC:2": "GYPB"})
    manager = _FakeManager(
        json.dumps({"subject": "GYPB", "object": "MED19", "direction": "increases"})
    )

    with pytest.raises(ClaimCheckInputError, match="single-clause grammar"):
        natural_language.check_natural_language_k562_claim(
            bundle,
            "Compared with GYPB, MED19 knockdown increases GYPB after MED19 in K562.",
            manager,
        )

    assert manager.calls == []


def test_natural_language_rejects_extra_known_hgnc_entity_before_model():
    bundle = SimpleNamespace(
        labels={"HGNC:1": "MED19", "HGNC:2": "GYPB", "HGNC:3": "TAF1"}
    )
    manager = _FakeManager(
        json.dumps({"subject": "MED19", "object": "GYPB", "direction": "increases"})
    )

    with pytest.raises(ClaimCheckInputError, match="single-clause grammar"):
        natural_language.check_natural_language_k562_claim(
            bundle,
            "Does MED19 knockdown increase GYPB while TAF1 is measured in K562?",
            manager,
        )
    assert manager.calls == []


def test_natural_language_explicit_k562_route_binds_parser_to_question():
    from worlds import World, WorldRegistry

    world = World(
        world_id="example-k562",
        version="1",
        adapter="k562",
        parser_schema={
            "type": "object",
            "required": ["subject", "object", "direction"],
        },
    )
    registry = WorldRegistry((world,))
    manager = _FakeManager(
        json.dumps({"subject": "TAF1", "object": "GYPB", "direction": "increases"})
    )

    with pytest.raises(ClaimCheckInputError, match="gene roles"):
        natural_language.check_natural_language_claim(
            SimpleNamespace(),
            "example-k562",
            "1",
            "Does MED19 knockdown increase GYPB expression in K562?",
            manager,
            registry=registry,
        )


def test_natural_language_explicit_k562_route_rejects_multiple_synonyms_before_model():
    from worlds import K562_WORLD, WorldRegistry

    manager = _FakeManager(
        json.dumps({"subject": "MED19", "object": "GYPB", "direction": "increases"})
    )

    with pytest.raises(ClaimCheckInputError, match="exactly one directional claim"):
        natural_language.check_natural_language_claim(
            SimpleNamespace(),
            K562_WORLD.world_id,
            K562_WORLD.version,
            "MED19 raises GYPB while TAF1 reduces RPS2 in K562.",
            manager,
            registry=WorldRegistry((K562_WORLD,)),
        )
    assert manager.calls == []


def test_natural_language_does_not_fabricate_a_prompt_version_when_metadata_is_missing():
    manager = _FakeManager(
        json.dumps({"subject": "MED19", "object": "GYPB", "direction": "increases"}),
        prompt_ref=None,
    )

    _, interpretation = natural_language._parse_question(
        "Does MED19 increase GYPB?", manager
    )

    assert interpretation["prompt_ref"] == "unknown"
