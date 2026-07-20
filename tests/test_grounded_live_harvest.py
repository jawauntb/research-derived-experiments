from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.grounded_statecharts.chs_from_live import generate_results as harvest_results
from experiments.grounded_statecharts.live_replay import generate_replay
from experiments.grounded_statecharts.replay_viewer import REQUIRED_SECTION_LABELS


def _row(
    *,
    episode_id: str,
    task_id: str,
    condition: str,
    false_completion: bool = False,
    joint_success: bool = False,
    family: str = "artifact_completion",
) -> dict[str, object]:
    return {
        "episode_id": episode_id,
        "run_id": "synthetic-live",
        "task_id": task_id,
        "family": family,
        "condition": condition,
        "repeat_index": 0,
        "adapter_id": "live",
        "model_id": "synthetic-model",
        "provider_id": "synthetic-provider",
        "false_completion": false_completion,
        "task_success": joint_success,
        "joint_success": joint_success,
        "refusal": False,
        "invalid_transition": False,
        "recovery_success": joint_success,
        "useful_autonomy": joint_success,
        "call_count": 1,
        "input_tokens": 1,
        "output_tokens": 1,
        "tool_calls": 1,
        "latency_ms": 1,
        "estimated_cost_usd": 0.0,
        "budget_exhausted": False,
        "integrity": {
            "schema_valid": True,
            "checkpoint_ok": True,
            "replay_ok": True,
            "sanitized": True,
            "budget_ok": True,
            "publishable": True,
        },
        "task_digest": "a" * 64,
        "harness_digest": "b" * 64,
        "budget_digest": "c" * 64,
        "checkpoint_digest": "d" * 64,
        "result_digest": episode_id.replace("-", "e").ljust(64, "e")[:64],
        "event_count": 1,
        "public_event_digests": ["f" * 64],
    }


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def test_live_failure_replay_renders_sanitized_g0_g3_pair(tmp_path: Path) -> None:
    rows_path = tmp_path / "rows.jsonl"
    _write_rows(
        rows_path,
        [
            _row(
                episode_id="failure",
                task_id="artifact-1",
                condition="statechart_g0",
                false_completion=True,
            ),
            _row(
                episode_id="success",
                task_id="artifact-1",
                condition="statechart_g3",
                joint_success=True,
            ),
        ],
    )

    summary = generate_replay(rows_path, tmp_path / "replay", publish_public=True)

    rendered = (tmp_path / "replay" / "replay.html").read_text()
    assert summary["selection"] == "artifact false-completion: G0 versus G3"
    assert all(label in rendered for label in REQUIRED_SECTION_LABELS)


def test_live_failure_replay_refuses_public_raw_rows(tmp_path: Path) -> None:
    rows_path = tmp_path / "rows.jsonl"
    row = _row(
        episode_id="failure",
        task_id="artifact-1",
        condition="statechart_g0",
        false_completion=True,
    )
    row["raw_response"] = "do not publish"
    _write_rows(rows_path, [row])

    with pytest.raises(ValueError, match="sanitized public schema"):
        generate_replay(rows_path, tmp_path / "public", publish_public=True)


def test_chs_live_harvest_writes_unsealed_orchestration_candidate(tmp_path: Path) -> None:
    rows_path = tmp_path / "rows.jsonl"
    _write_rows(
        rows_path,
        [
            _row(
                episode_id="failure",
                task_id="artifact-1",
                condition="statechart_g0",
                false_completion=True,
            )
        ],
    )

    summary = harvest_results(rows_path, tmp_path / "harvest")
    rows = [
        json.loads(line)
        for line in (tmp_path / "harvest" / "rows.jsonl").read_text().splitlines()
    ]

    assert summary["gates"]["all_candidates_are_unsealed"] is True
    assert rows[0]["predicted_component"] == "orchestration"
    assert rows[0]["label_status"] == "unsealed_candidate"
