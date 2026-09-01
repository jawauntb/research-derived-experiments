"""Real ModelManager coverage for the Phase 4b compatibility adapter."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("jinja2")
pytest.importorskip("yaml")

from model_manager import ModelManagerAdapter, ModelManagerError
from proposer import Proposer
from repairer import Repairer


def _claim() -> dict:
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


def test_adapter_renders_proposer_prompt_and_maps_response_metadata(manager_with_fake):
    manager, fake = manager_with_fake
    fake.meta = {
        "provider": "recorded-provider",
        "model": "recorded-model",
        "latency_ms": 42.4,
        "usage": {"prompt_tokens": 17, "completion_tokens": 23, "total_tokens": 40},
    }
    adapter = ModelManagerAdapter(manager)

    response = adapter.call(
        task="proposer",
        user_msg=json.dumps(
            {
                "question": "Does BRCA1 increase KRAS?",
                "evidence_records": [{"id": "perturbseq_v_test:fc1d7ea4dd7c21a7"}],
                "context_hints": {"scope": "synthetic"},
            }
        ),
        system_msg="legacy system message is intentionally ignored",
        max_tokens=321,
        temperature=0.25,
        timeout_s=12,
        prompt_ref="proposer/claim_bundle@v1",
    )

    request = fake.requests[-1]
    assert "untrusted proposer" in request.messages[0]["content"]
    assert "Does BRCA1 increase KRAS?" in request.messages[1]["content"]
    assert request.params["max_tokens"] == 321
    assert request.params["temperature"] == 0.25
    assert request.params["timeout"] == 12
    assert response.provider == "recorded-provider"
    assert response.model == "recorded-model"
    assert response.prompt_ref == "proposer/claim_bundle@v1"
    assert response.prompt_version == "v1"
    assert response.latency_ms == 42
    assert response.tokens_prompt == 17
    assert response.tokens_completion == 23


def test_adapter_rejects_unconfigured_prompt_ref_before_dispatch(manager_with_fake):
    manager, fake = manager_with_fake
    adapter = ModelManagerAdapter(manager)

    with pytest.raises(ModelManagerError) as error:
        adapter.call(
            task="proposer",
            user_msg=json.dumps(
                {"question": "Does BRCA1 increase KRAS?", "evidence_records": [], "context_hints": {}}
            ),
            prompt_ref="proposer/claim_bundle@v999",
        )

    assert error.value.code == "adapter_prompt_ref_mismatch"
    assert fake.requests == []


def test_adapter_preserves_checker_refusal_before_dispatch(manager_with_fake):
    manager, fake = manager_with_fake
    adapter = ModelManagerAdapter(manager)

    with pytest.raises(ModelManagerError) as error:
        adapter.call(task="checker", user_msg="{}")

    assert error.value.code == "checker_is_not_a_model_task"
    assert fake.requests == []


@pytest.mark.parametrize(
    "user_msg",
    [
        "not json",
        json.dumps([]),
        json.dumps({"question": "Does BRCA1 increase KRAS?"}),
    ],
)
def test_adapter_rejects_malformed_proposer_envelopes_before_dispatch(manager_with_fake, user_msg):
    manager, fake = manager_with_fake
    adapter = ModelManagerAdapter(manager)

    with pytest.raises(ModelManagerError) as error:
        adapter.call(task="proposer", user_msg=user_msg)

    assert error.value.code == "adapter_invalid_request"
    assert fake.requests == []


def test_proposer_wraps_real_manager_and_uses_versioned_prompt(manager_with_fake):
    manager, fake = manager_with_fake
    fake.content = json.dumps([_claim()])

    bundle = Proposer(manager).propose("Does BRCA1 increase KRAS?", [])

    assert bundle.claims == (_claim(),)
    assert bundle.provider == "fake"
    assert bundle.model == "fake-model-v1"
    assert "untrusted proposer" in fake.requests[-1].messages[0]["content"]


def test_repairer_wraps_real_manager_and_aligns_repair_prompt(make_manager):
    manager, fake = make_manager(
        extra_tasks="""
  repairer:
    provider: fake_provider
    prompt_ref: repairer/claim_repair@v2
    timeout_s: 20
"""
    )
    repaired = _claim()
    fake.content = json.dumps({"repaired_claim": repaired, "reason": "fixed citation"})
    rejected = {
        "fault_code": "BAD_CITATION",
        "reasons": [{"message": "evidence id does not resolve"}],
    }

    result = Repairer(manager).repair(_claim(), rejected, [{"id": repaired["evidence_ids"][0]}])

    assert result.claim == repaired
    assert result.provider == "fake"
    assert "BAD_CITATION" in fake.requests[-1].messages[1]["content"]
    assert "evidence id does not resolve" in fake.requests[-1].messages[1]["content"]


@pytest.mark.parametrize(
    "verdict",
    [
        ["BAD_CITATION"],
        {"fault_code": "BAD_CITATION", "reasons": "not an array"},
    ],
)
def test_repairer_fails_closed_on_invalid_verdict_envelope(make_manager, verdict):
    manager, fake = make_manager(
        extra_tasks="""
  repairer:
    provider: fake_provider
    prompt_ref: repairer/claim_repair@v2
    timeout_s: 20
"""
    )

    with pytest.raises(ModelManagerError) as error:
        Repairer(manager).repair(_claim(), verdict, [])

    assert error.value.code == "adapter_invalid_request"
    assert fake.requests == []


def test_src_import_style_wraps_a_real_manager_with_only_firewall_root_on_pythonpath(tmp_path):
    firewall_root = Path(__file__).resolve().parents[2]
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
providers:
  fake_provider:
    type: fake
    model: fake-model-v1

tasks:
  proposer:
    provider: fake_provider
    prompt_ref: proposer/claim_bundle@v1
  repairer:
    provider: fake_provider
    prompt_ref: repairer/claim_repair@v2
"""
    )
    responses = json.dumps([json.dumps([_claim()]), json.dumps({"abstain": True, "reason": "no repair"})])
    script = """
import json
import os

from src.model_manager import ModelManager
from src.model_manager.providers.base import BaseProvider
from src.model_manager.types import ChatResponse
from src.proposer import Proposer
from src.repairer import Repairer


class FakeProvider(BaseProvider):
    def __init__(self):
        self._responses = json.loads(os.environ["ADAPTER_RESPONSES"])

    def chat(self, request):
        return ChatResponse(content=self._responses.pop(0), raw={}, meta={})

    def health_check(self):
        return True


manager = ModelManager(os.environ["ADAPTER_CONFIG"])
manager._providers["fake_provider"] = FakeProvider()
bundle = Proposer(manager).propose("Does BRCA1 increase KRAS?", [])
assert bundle.claims[0]["subject"]["id"] == "HGNC:1097"
assert bundle.provider == "fake"
assert bundle.model == "fake-model-v1"
repair = Repairer(manager).repair(bundle.claims[0], {"fault_code": "BAD_CITATION", "reasons": []}, [])
assert repair.abstained is True
assert repair.provider == "fake"
assert repair.model == "fake-model-v1"
print("src import adapter ok")
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "PYTHONPATH": str(firewall_root),
            "ADAPTER_CONFIG": str(config_path),
            "ADAPTER_RESPONSES": responses,
        },
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[-1] == "src import adapter ok"
