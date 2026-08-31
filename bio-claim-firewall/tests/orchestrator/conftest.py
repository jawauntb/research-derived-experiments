"""Shared fixtures for tests/orchestrator/: a `FakeModelManager` (same
shape as `tests/proposer/conftest.py` -- duplicated for the same
cross-test-package-import reason `tests/repairer/conftest.py` documents),
plus a REAL hash-verified `SnapshotBundle` loaded from
`tests/fixtures/synthetic_world` and a real `VerifierConfig`, so these
tests exercise the actual deterministic checker (`verifier.verify`), not a
fake one -- only the two untrusted model calls (`proposer`/`repairer`
tasks) are faked.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from evidence import load_bundle
from evidence.snapshot import SnapshotBundle
from verifier import VerifierConfig

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SYNTH_SRC = FIXTURES / "synthetic_world"
SPEC_DIR = FIXTURES.parent.parent / "spec"


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
        self.calls.append({"task": task, "user_msg": user_msg, "prompt_ref": prompt_ref})
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
def snapshot() -> SnapshotBundle:
    """A hash-verified `SnapshotBundle` over `tests/fixtures/synthetic_world`
    -- the same fixture pack `tests/verifier/conftest.py` uses.
    """
    return load_bundle(SYNTH_SRC)


@pytest.fixture
def verifier_config() -> VerifierConfig:
    return VerifierConfig(checker_version="0.1.0", schema_dir=SPEC_DIR)


@pytest.fixture
def accepted_claim() -> dict:
    """Mirrors tests/fixtures/claims/ACCEPTED_CONDITIONALLY__example.json --
    BRCA1 `increases` KRAS, cited evidence is the real interventional
    CRISPRi record for that pair -> `ACCEPTED_CONDITIONALLY`.
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
def rejected_claim() -> dict:
    """Mirrors tests/fixtures/claims/BAD_CITATION__invalid.json -- same
    claim as `accepted_claim` but citing a well-formed, non-resolving
    evidence_id -> `REJECTED`/`BAD_CITATION` (R-CITE-*).
    """
    return {
        "schema_version": "0.1.0",
        "claim_id": "c4069faf-ce54-42ea-81e0-1591b74906be",
        "subject": {"id": "HGNC:1097", "label": "BRCA1"},
        "relation": "increases",
        "object": {"id": "HGNC:6407", "label": "KRAS"},
        "polarity": "positive",
        "species": "NCBITaxon:9606",
        "cell_context": {"cell_type": "CL:0000988", "cell_line": "CLO:0009454", "state": "resting"},
        "assay_context": {"assay": "CRISPRi_screen", "perturbation": "CRISPRi:HGNC:1097"},
        "evidence_ids": ["perturbseq_v_test:0000000000000000"],
        "confidence_language": "supported",
        "requested_status": "hypothesis",
    }


@pytest.fixture
def make_claim(accepted_claim: dict):
    def _make(**overrides: Any) -> dict:
        claim = copy.deepcopy(accepted_claim)
        claim.update(overrides)
        return claim

    return _make
