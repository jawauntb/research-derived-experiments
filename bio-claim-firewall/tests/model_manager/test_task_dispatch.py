"""Task -> provider dispatch, and the `checker` refusal (the checker is a
deterministic rule engine, not a model task — see PHASE_4_PLAN.md's
fault-split invariant and manager.py's module docstring)."""
from __future__ import annotations

import pytest

pytest.importorskip("yaml")

from model_manager.errors import ModelManagerError


def test_call_routes_to_configured_provider(manager_with_fake):
    manager, fake = manager_with_fake
    response = manager.call(
        task="proposer",
        variables={},
        messages_override=[{"role": "user", "content": "hi"}],
    )
    assert response.content == fake.content
    assert len(fake.requests) == 1
    assert fake.requests[0].model == "fake-model-v1"
    assert fake.requests[0].messages == [{"role": "user", "content": "hi"}]


def test_call_records_prompt_ref_and_version(manager_with_fake):
    manager, fake = manager_with_fake
    response = manager.call(
        task="proposer",
        messages_override=[{"role": "user", "content": "hi"}],
    )
    assert response.prompt_ref == "proposer/claim_bundle@v1"
    assert response.prompt_version == "v1"


def test_call_unknown_task_raises(manager_with_fake):
    manager, _fake = manager_with_fake
    with pytest.raises(ValueError, match="Unknown task: not_a_real_task"):
        manager.call(task="not_a_real_task", messages_override=[{"role": "user", "content": "x"}])


def test_call_checker_task_refuses(manager_with_fake):
    manager, fake = manager_with_fake
    with pytest.raises(ModelManagerError) as exc_info:
        manager.call(task="checker", messages_override=[{"role": "user", "content": "x"}])

    err = exc_info.value
    assert err.code == "checker_is_not_a_model_task"
    assert err.task == "checker"
    assert fake.requests == []  # never dispatched to any provider


def test_call_checker_refuses_even_if_present_in_config(make_manager):
    """Even if a config file were to define a `checker` task entry (ours
    doesn't — it's documented as a comment only), the manager must still
    refuse rather than dispatch it."""
    manager, fake = make_manager(
        extra_tasks="""
  checker:
    provider: fake_provider
    prompt_ref: checker/anything@v1
"""
    )
    with pytest.raises(ModelManagerError) as exc_info:
        manager.call(task="checker", messages_override=[{"role": "user", "content": "x"}])
    assert exc_info.value.code == "checker_is_not_a_model_task"
    assert fake.requests == []


def test_call_with_schema_and_params_override(manager_with_fake):
    manager, fake = manager_with_fake
    manager.call(
        task="proposer",
        messages_override=[{"role": "user", "content": "x"}],
        temperature=0.9,
        max_tokens=42,
    )
    req = fake.requests[-1]
    assert req.params["temperature"] == 0.9
    assert req.params["max_tokens"] == 42
