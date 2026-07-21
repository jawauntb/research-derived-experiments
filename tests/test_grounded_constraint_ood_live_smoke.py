from __future__ import annotations

import json

import pytest

from experiments.grounded_statecharts.adapters.live import LiveExecutor
from experiments.grounded_statecharts.constraint_ood import OOD_KILL_THRESHOLD
from experiments.grounded_statecharts.run_constraint_ood_live_smoke import generate_results


def test_generate_results_requires_opt_in_env(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GROUNDED_HARNESS_LIVE", raising=False)
    with pytest.raises(RuntimeError, match="GROUNDED_HARNESS_LIVE"):
        generate_results(tmp_path / "artifacts" / "ct_ood_live")


def test_generate_results_rejects_labeled_prompt_mode(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GROUNDED_HARNESS_LIVE", "1")
    monkeypatch.setenv("GROUNDED_HARNESS_LABELED_PROMPT", "1")
    with pytest.raises(RuntimeError, match="name-free"):
        generate_results(tmp_path / "artifacts" / "ct_ood_live")


def test_generate_results_refuses_results_directory(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GROUNDED_HARNESS_LIVE", "1")
    with pytest.raises(RuntimeError, match="results/"):
        generate_results(tmp_path / "results" / "ct_ood_live")


def _transport_returning(action: str, capability_used: list[str]):
    def transport(url, headers, payload, timeout_seconds):
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "action": action,
                                "claimed_complete": True,
                                "artifact_created": False,
                                "capability_used": capability_used,
                                "text": "held-out paraphrase response",
                            }
                        )
                    }
                }
            ],
            "usage": {"prompt_tokens": 40, "completion_tokens": 10},
        }

    return transport


def test_generate_results_recovers_effect_when_guards_repair_violations(
    tmp_path, monkeypatch
) -> None:
    """A model that widens capabilities produces the harness-enforced effect.

    envelope_only leaves the widened capability as a violation;
    envelope_external_guards is enforced by `condition_policy.py` regardless
    of the model's chosen action, so joint_success should recover under the
    treatment condition even though the fake transport ignores wording.
    """

    monkeypatch.setenv("GROUNDED_HARNESS_LIVE", "1")
    executor = LiveExecutor(
        provider_id="openai",
        model_id="fake-model",
        api_key="fake-key",
        transport=_transport_returning(
            "delegate_with_widened_capability", ["delegate", "network"]
        ),
    )
    output_dir = tmp_path / "artifacts" / "ct_ood_live"
    summary = generate_results(output_dir, executor=executor)

    rows = [json.loads(line) for line in (output_dir / "rows.jsonl").read_text().splitlines()]
    assert len(rows) == 8
    assert summary["joint_success_effect"]["point_estimate"] == pytest.approx(1.0)
    assert summary["kill_triggered"] is False


def test_generate_results_records_kill_when_conditions_do_not_differ(
    tmp_path, monkeypatch
) -> None:
    """A model that never violates constraints even without guards collapses the effect."""

    monkeypatch.setenv("GROUNDED_HARNESS_LIVE", "1")
    executor = LiveExecutor(
        provider_id="openai",
        model_id="fake-model",
        api_key="fake-key",
        transport=_transport_returning("delegate_with_envelope", ["delegate"]),
    )
    output_dir = tmp_path / "artifacts" / "ct_ood_live"
    summary = generate_results(output_dir, executor=executor)

    assert summary["joint_success_effect"]["point_estimate"] == pytest.approx(0.0)
    assert summary["joint_success_effect"]["point_estimate"] < OOD_KILL_THRESHOLD
    assert summary["kill_triggered"] is True
    assert summary["allowed_claim"].startswith("KILL:")


def test_generate_results_records_provider_failures(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GROUNDED_HARNESS_LIVE", "1")

    def broken_transport(url, headers, payload, timeout_seconds):
        raise RuntimeError("simulated provider outage")

    executor = LiveExecutor(
        provider_id="openai",
        model_id="fake-model",
        api_key="fake-key",
        transport=broken_transport,
    )
    output_dir = tmp_path / "artifacts" / "ct_ood_live"
    summary = generate_results(output_dir, executor=executor)

    assert summary["publishable_rows"] == 0
    assert len(summary["provider_failures"]) == 8
    assert summary["joint_success_effect"]["point_estimate"] is None
    assert summary["kill_triggered"] is True
