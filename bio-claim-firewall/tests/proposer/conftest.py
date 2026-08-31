"""Shared fixtures for tests/proposer/: a `FakeModelManager` satisfying the
`ModelManager` interface from the task brief (`call(task, user_msg, *,
system_msg=None, ..., prompt_ref=None) -> ChatResponse`), returning canned
responses per `task` and recording every call for inspection. Constructed
without any real prompt/config file -- no network calls, no
`src/model_manager` import.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

import pytest


@dataclass(frozen=True)
class FakeChatResponse:
    content: str
    provider: str = "fake-provider"
    model: str = "fake-model-v0"
    prompt_ref: str = ""
    prompt_version: str = "v1"
    latency_ms: int = 7
    tokens_prompt: int = 42
    tokens_completion: int = 13


@dataclass
class FakeModelManager:
    """`responses[task]` is either a single content string (returned on
    every call for that task) or a list of content strings, consumed one
    per call (for tests that need the Nth call to return something
    different, e.g. a repair sequence).
    """

    responses: dict[str, Any] = field(default_factory=dict)
    calls: list[dict[str, Any]] = field(default_factory=list)

    def call(
        self,
        task: str,
        user_msg: str,
        *,
        system_msg: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        timeout_s: float | None = None,
        prompt_ref: str | None = None,
    ) -> FakeChatResponse:
        self.calls.append(
            {
                "task": task,
                "user_msg": user_msg,
                "system_msg": system_msg,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "timeout_s": timeout_s,
                "prompt_ref": prompt_ref,
            }
        )
        if task not in self.responses:
            raise AssertionError(f"FakeModelManager: no canned response registered for task={task!r}")
        queue = self.responses[task]
        if isinstance(queue, list):
            if not queue:
                raise AssertionError(f"FakeModelManager: response queue for task={task!r} is exhausted")
            content = queue.pop(0)
        else:
            content = queue
        return FakeChatResponse(content=content, prompt_ref=prompt_ref or f"{task}/fake@v1")


@pytest.fixture
def fake_mm_factory():
    return FakeModelManager


@pytest.fixture
def valid_claim() -> dict:
    """A schema-valid claim dict (mirrors
    tests/fixtures/claims/ACCEPTED_CONDITIONALLY__example.json) -- every
    top-level required field from spec/claim.schema.json present.
    """
    return {
        "schema_version": "0.1.0",
        "claim_id": "65543f5e-334a-4d45-869c-1b55085feb27",
        "subject": {"id": "HGNC:1097", "label": "BRCA1"},
        "relation": "increases",
        "object": {"id": "HGNC:6407", "label": "KRAS"},
        "polarity": "positive",
        "species": "NCBITaxon:9606",
        "cell_context": {"cell_type": "CL:0000988", "cell_line": "CLO:0009454", "state": "resting"},
        "assay_context": {"assay": "CRISPRi_screen", "perturbation": "CRISPRi:HGNC:1097"},
        "evidence_ids": ["perturbseq_v_test:fc1d7ea4dd7c21a7"],
        "confidence_language": "supported",
        "requested_status": "hypothesis",
    }


@pytest.fixture
def make_claim(valid_claim: dict):
    """Fixture factory: `make_claim(claim_id="...")` -> a fresh deep copy
    of `valid_claim` with overrides applied.
    """

    def _make(**overrides: Any) -> dict:
        claim = copy.deepcopy(valid_claim)
        claim.update(overrides)
        return claim

    return _make
