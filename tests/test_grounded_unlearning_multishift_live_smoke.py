from __future__ import annotations

import json

import pytest

from experiments.grounded_statecharts.adapters.live import LiveExecutor
from experiments.grounded_statecharts.run_unlearning_multishift_live_smoke import (
    CONDITIONS,
    SMOKE_CASE_IDS,
    build_memory_probe_messages,
    evaluate_kill_criteria,
    generate_results,
)
from experiments.grounded_statecharts.unlearning_multishift import draft_shift_cases


def _case(case_id: str):
    return next(case for case in draft_shift_cases() if case.case_id == case_id)


def _selected_cases_for_test():
    by_id = {case.case_id: case for case in draft_shift_cases()}
    return tuple(by_id[case_id] for case_id in SMOKE_CASE_IDS)


def _row(case_id: str, condition: str, *, matched: bool) -> dict:
    return {"case_id": case_id, "condition": condition, "matched_expected": matched}


def test_build_memory_probe_messages_never_leaks_condition_or_case_labels() -> None:
    """The live prompt must stay name-free: no condition name, case id, or
    shift-family label may appear, or the model could infer its arm from a
    label instead of the memory content itself."""

    case = _case("tool_schema_v2_to_v3")
    leak_free_labels = (*CONDITIONS, case.case_id, case.shift_family)
    for condition in CONDITIONS:
        messages = build_memory_probe_messages(case, condition=condition)
        full_text = " ".join(message["content"] for message in messages)
        for label in leak_free_labels:
            assert label not in full_text


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


def test_kill_criterion_fires_when_identical_semantics_case_looks_quarantine_worthy() -> None:
    """If the model/version-identical-semantics negative control shows the
    target-specific pattern (removing target helps, removing placebo does
    not), that is a false-forgetting risk signature and must trigger the
    kill criterion, not be read as a useful signal."""

    rows = [
        _row("model_version_identical_model_alias", "observed", matched=False),
        _row("model_version_identical_model_alias", "target_suppressed", matched=True),
        _row("model_version_identical_model_alias", "placebo_suppressed", matched=False),
    ]
    result = evaluate_kill_criteria(rows, _selected_cases_for_test())

    assert result["kill_triggered"] is True
    assert result["identical_semantics_violations"] == [
        "model_version_identical_model_alias"
    ]
    assert result["target_specificity_violations"] == []


def test_kill_criterion_does_not_fire_for_a_clean_semantic_shift_pattern() -> None:
    """A changed-semantics case showing the causal-use-shaped pattern
    (target-specific recovery, placebo unaffected) is exactly what the probe
    is meant to detect and must not trip either kill criterion."""

    rows = [
        _row("tool_schema_v2_to_v3", "observed", matched=False),
        _row("tool_schema_v2_to_v3", "target_suppressed", matched=True),
        _row("tool_schema_v2_to_v3", "placebo_suppressed", matched=False),
    ]
    result = evaluate_kill_criteria(rows, _selected_cases_for_test())

    assert result["kill_triggered"] is False
    assert result["identical_semantics_violations"] == []
    assert result["target_specificity_violations"] == []
    assert result["per_case"]["tool_schema_v2_to_v3"]["quarantine_signal"] is True


def test_quarantine_signal_requires_placebo_specificity_even_with_target_effect() -> None:
    """A generic 'any suppression helps' effect (placebo also recovers the
    correct action) must never be read as quarantine-worthy on its own, even
    when the target suppression also helped."""

    rows = [
        _row("tool_schema_v2_to_v3", "observed", matched=False),
        _row("tool_schema_v2_to_v3", "target_suppressed", matched=True),
        _row("tool_schema_v2_to_v3", "placebo_suppressed", matched=True),
    ]
    result = evaluate_kill_criteria(rows, _selected_cases_for_test())

    assert result["per_case"]["tool_schema_v2_to_v3"]["quarantine_signal"] is False
    assert result["target_specificity_violations"] == []
    assert result["kill_triggered"] is False


def test_kill_criteria_marks_incomplete_cases_as_insufficient_data() -> None:
    """A case missing a condition (e.g. a provider failure) must be excluded
    from the gate rather than silently defaulting to a pass or a kill."""

    rows = [
        _row("tool_schema_v2_to_v3", "observed", matched=False),
        _row("tool_schema_v2_to_v3", "target_suppressed", matched=True),
        # placebo_suppressed missing for this case.
    ]
    result = evaluate_kill_criteria(rows, _selected_cases_for_test())

    assert "tool_schema_v2_to_v3" not in result["per_case"]
    assert set(result["insufficient_data_cases"]) == set(SMOKE_CASE_IDS)
    assert result["kill_triggered"] is False


def test_generate_results_end_to_end_reports_kill_criteria_gate(tmp_path, monkeypatch) -> None:
    """The end-to-end summary must surface the kill-criteria gate alongside
    the existing mechanics gates."""

    monkeypatch.setenv("GROUNDED_HARNESS_LIVE", "1")
    executor = LiveExecutor(
        provider_id="openai",
        model_id="fake-model",
        api_key="fake-key",
        transport=_fake_openai_transport("__matches_regime__"),
    )
    output_dir = tmp_path / "artifacts" / "hu_live_smoke"
    summary = generate_results(output_dir, executor=executor)

    assert "kill_criteria" in summary
    assert "kill_triggered" in summary["gates"]
    assert isinstance(summary["kill_criteria"]["kill_triggered"], bool)


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
