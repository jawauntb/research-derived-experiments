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
            object(), "MED19 increases GYPB", _FakeManager(response)
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


def test_natural_language_does_not_fabricate_a_prompt_version_when_metadata_is_missing():
    manager = _FakeManager(
        json.dumps({"subject": "MED19", "object": "GYPB", "direction": "increases"}),
        prompt_ref=None,
    )

    _, interpretation = natural_language._parse_question(
        "Does MED19 increase GYPB?", manager
    )

    assert interpretation["prompt_ref"] == "unknown"
