from __future__ import annotations

from experiments.grounded_statecharts.adapters.live import parse_live_action
from experiments.grounded_statecharts.adapters.live_ablation import build_weak_live_prompt
from experiments.grounded_statecharts.adapters.protocol import ExecutorRequest


def test_weak_prompt_omits_condition_label() -> None:
    request = ExecutorRequest(
        episode_id="e",
        task_id="t",
        family="artifact_completion",
        condition="statechart_g3",
        instruction="Write reports/out.md",
        seed=0,
        step_index=0,
    )
    messages = build_weak_live_prompt(request)
    assert "statechart_g3" not in messages[1]["content"]
    assert "Write reports/out.md" in messages[1]["content"]


def test_parse_live_action_coerces_string_bools() -> None:
    parsed = parse_live_action(
        '{"action":"create_artifact_and_commit","claimed_complete":"true",'
        '"artifact_created":"false","capability_used":[],"text":"x"}'
    )
    assert parsed["claimed_complete"] is True
    assert parsed["artifact_created"] is False


def test_parse_live_action_coerces_null_and_yes() -> None:
    parsed = parse_live_action(
        '{"action":"refuse_task","claimed_complete":null,'
        '"artifact_created":"yes","capability_used":null,"text":"x"}'
    )
    assert parsed["claimed_complete"] is False
    assert parsed["artifact_created"] is True
    assert parsed["capability_used"] == ()


def test_parse_live_action_coerces_path_and_csv_capabilities() -> None:
    parsed = parse_live_action(
        '{"action":"update_file","claimed_complete":false,'
        '"artifact_created":"workspace/reports/out.json",'
        '"capability_used":"file_system,inventory","text":"x"}'
    )
    assert parsed["artifact_created"] is True
    assert parsed["capability_used"] == ("file_system", "inventory")
