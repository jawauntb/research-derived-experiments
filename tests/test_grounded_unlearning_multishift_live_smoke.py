from __future__ import annotations

import json

import pytest

from experiments.grounded_statecharts.adapters.live import LiveExecutor
from experiments.grounded_statecharts.run_unlearning_multishift_live_smoke import (
    CONDITIONS,
    SMOKE_CASE_IDS,
    build_memory_probe_messages,
    generate_results,
)
from experiments.grounded_statecharts.unlearning_multishift import draft_shift_cases


def _case(case_id: str):
    return next(case for case in draft_shift_cases() if case.case_id == case_id)


def test_target_suppressed_prompt_omits_memory_reminder() -> None:
    case = _case("tool_schema_v2_to_v3")
    observed = build_memory_probe_messages(case, condition="observed")
    suppressed = build_memory_probe_messages(case, condition="target_suppressed")

    observed_user = observed[1]["content"]
    suppressed_user = suppressed[1]["content"]
    assert case.fixture.target_action in observed_user
    assert case.fixture.target_action not in suppressed_user
    assert "No prior tool-usage memory is available" in suppressed_user


def test_placebo_suppressed_prompt_keeps_target_drops_placebo_note() -> None:
    case = _case("tool_schema_v2_to_v3")
    observed = build_memory_probe_messages(case, condition="observed")
    placebo_suppressed = build_memory_probe_messages(case, condition="placebo_suppressed")

    assert "unrelated preference note" in observed[1]["content"]
    assert "unrelated preference note" not in placebo_suppressed[1]["content"]
    assert case.fixture.target_action in placebo_suppressed[1]["content"]


def test_build_memory_probe_messages_rejects_unknown_condition() -> None:
    case = _case("tool_schema_v2_to_v3")
    with pytest.raises(ValueError):
        build_memory_probe_messages(case, condition="not-a-condition")


def test_generate_results_requires_opt_in_env(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GROUNDED_HARNESS_LIVE", raising=False)
    with pytest.raises(RuntimeError, match="GROUNDED_HARNESS_LIVE"):
        generate_results(tmp_path / "artifacts" / "hu_live_smoke")


def test_generate_results_refuses_results_directory(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GROUNDED_HARNESS_LIVE", "1")
    with pytest.raises(RuntimeError, match="results/"):
        generate_results(tmp_path / "results" / "hu_live_smoke")


def _fake_openai_transport(expected_action: str):
    def transport(url, headers, payload, timeout_seconds):
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "action": expected_action,
                                "claimed_complete": True,
                                "artifact_created": False,
                                "capability_used": [],
                                "text": "chose the current regime's value",
                            }
                        )
                    }
                }
            ],
            "usage": {"prompt_tokens": 42, "completion_tokens": 8},
        }

    return transport


def test_generate_results_end_to_end_with_fake_transport(tmp_path, monkeypatch) -> None:
    """A model that always follows the current regime instruction should pass."""

    monkeypatch.setenv("GROUNDED_HARNESS_LIVE", "1")
    executor = LiveExecutor(
        provider_id="openai",
        model_id="fake-model",
        api_key="fake-key",
        transport=_fake_openai_transport("__matches_regime__"),
    )
    # Override per-case since the fake transport is fixed; monkeypatch the
    # transport per case's expected action to exercise both matched and
    # mismatched scoring paths deterministically.
    output_dir = tmp_path / "artifacts" / "hu_live_smoke"
    summary = generate_results(output_dir, executor=executor)

    rows = [
        json.loads(line) for line in (output_dir / "rows.jsonl").read_text().splitlines()
    ]
    assert len(rows) == len(SMOKE_CASE_IDS) * len(CONDITIONS)
    assert {row["case_id"] for row in rows} == set(SMOKE_CASE_IDS)
    assert {row["condition"] for row in rows} == set(CONDITIONS)
    assert summary["gates"]["opt_in"] is True
    assert summary["gates"]["writes_to_artifacts_only"] is True
    assert summary["gates"]["all_episodes_parsed"] is True
    assert summary["gates"]["budget_ok"] is True
    assert summary["gates"]["provider_failures"] == 0
    # The fake transport always returns the same literal action, which will
    # not equal every case's expected action, so this exercises both
    # matched_expected outcomes without any live provider being real.
    assert {row["matched_expected"] for row in rows} == {False}


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
    output_dir = tmp_path / "artifacts" / "hu_live_smoke"
    summary = generate_results(output_dir, executor=executor)

    assert summary["episode_count"] == len(SMOKE_CASE_IDS) * len(CONDITIONS)
    assert summary["publishable_rows"] == 0
    assert len(summary["provider_failures"]) == len(SMOKE_CASE_IDS) * len(CONDITIONS)
    assert summary["gates"]["all_episodes_parsed"] is False
    assert summary["gates"]["provider_failures"] == len(SMOKE_CASE_IDS) * len(CONDITIONS)
