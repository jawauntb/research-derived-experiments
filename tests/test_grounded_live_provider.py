from __future__ import annotations

import json

import pytest

from experiments.grounded_statecharts.adapters.live import (
    LIVE_OPT_IN_ENV,
    LiveExecutor,
    build_live_prompt,
    parse_live_action,
)
from experiments.grounded_statecharts.adapters.protocol import ExecutorRequest
from experiments.grounded_statecharts.evaluation import (
    LiveEpisode,
    harness_digest_for,
    run_episode,
    smoke_tasks,
)
from experiments.grounded_statecharts.budgets import DEFAULT_PILOT_BUDGET
from experiments.grounded_statecharts.sanitization import sanitize_public_row


def _request() -> ExecutorRequest:
    return ExecutorRequest(
        episode_id="ep",
        task_id="t",
        family="artifact_completion",
        condition="statechart_g3",
        instruction="create the artifact",
        seed=1,
        step_index=0,
    )


def test_parse_live_action_accepts_json_object() -> None:
    parsed = parse_live_action(
        json.dumps(
            {
                "action": "create_artifact_and_commit",
                "claimed_complete": True,
                "artifact_created": True,
                "capability_used": ["write_artifact"],
                "text": "created",
            }
        )
    )
    assert parsed["action"] == "create_artifact_and_commit"
    assert parsed["artifact_created"] is True


def test_live_executor_uses_injectible_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(LIVE_OPT_IN_ENV, "1")
    monkeypatch.setenv("GROUNDED_HARNESS_PROVIDER", "openai")
    monkeypatch.setenv("GROUNDED_HARNESS_MODEL", "gpt-test")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_transport(url, headers, payload, timeout_seconds):
        assert "chat/completions" in url
        assert headers["Authorization"] == "Bearer test-key"
        assert payload["model"] == "gpt-test"
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "action": "create_artifact_and_commit",
                                "claimed_complete": True,
                                "artifact_created": True,
                                "capability_used": ["write_artifact"],
                                "text": "ok",
                            }
                        )
                    }
                }
            ],
            "usage": {"prompt_tokens": 11, "completion_tokens": 7},
        }

    executor = LiveExecutor.from_env(transport=fake_transport)
    response = executor.complete(_request())
    assert response.action == "create_artifact_and_commit"
    assert response.usage.input_tokens == 11
    assert response.raw is not None


def test_live_episode_public_row_excludes_raw(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(LIVE_OPT_IN_ENV, "1")
    monkeypatch.setenv("GROUNDED_HARNESS_PROVIDER", "openai")
    monkeypatch.setenv("GROUNDED_HARNESS_MODEL", "gpt-test")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_transport(url, headers, payload, timeout_seconds):
        del url, headers, payload, timeout_seconds
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "action": "create_artifact_and_commit",
                                "claimed_complete": True,
                                "artifact_created": True,
                                "capability_used": ["write_artifact"],
                                "text": "ok",
                            }
                        )
                    }
                }
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3},
        }

    executor = LiveExecutor.from_env(transport=fake_transport)
    episode = LiveEpisode(
        episode_id="live-ep",
        run_id="live-run",
        task=smoke_tasks()[0],
        condition="statechart_g3",
        repeat_index=0,
        model_id=executor.model_id,
        provider_id=executor.provider_id,
        adapter_id="live",
        harness_digest=harness_digest_for("statechart_g3"),
        budget=DEFAULT_PILOT_BUDGET,
        seed=2,
    )
    result = run_episode(episode, executor=executor)
    assert result.integrity.publishable
    assert "raw" not in result.public_row
    assert sanitize_public_row({**result.public_row, "raw": {"x": 1}}).ok is False


def test_build_live_prompt_mentions_condition() -> None:
    messages = build_live_prompt(_request())
    assert messages[0]["role"] == "system"
    assert "statechart_g3" in messages[1]["content"]
