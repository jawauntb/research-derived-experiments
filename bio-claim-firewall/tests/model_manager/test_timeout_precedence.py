"""Timeout precedence: default < task config < call-site override."""
from __future__ import annotations

import pytest

pytest.importorskip("yaml")


def test_task_timeout_beats_default(manager_with_fake):
    manager, fake = manager_with_fake
    manager.call(task="proposer", messages_override=[{"role": "user", "content": "x"}])
    assert fake.requests[-1].params["timeout"] == 45  # from conftest's write_config
    assert manager.DEFAULT_TIMEOUT_S != 45


def test_default_used_when_no_task_timeout(make_manager):
    manager, fake = make_manager(
        extra_tasks="""
  repairer:
    provider: fake_provider
    prompt_ref: repairer/claim_repair@v1
"""
    )
    manager.call(task="repairer", messages_override=[{"role": "user", "content": "x"}])
    assert fake.requests[-1].params["timeout"] == manager.DEFAULT_TIMEOUT_S


def test_call_site_override_beats_task_timeout(manager_with_fake):
    manager, fake = manager_with_fake
    manager.call(
        task="proposer",
        messages_override=[{"role": "user", "content": "x"}],
        timeout=5,
    )
    assert fake.requests[-1].params["timeout"] == 5


def test_call_site_override_beats_default_too(make_manager):
    manager, fake = make_manager(
        extra_tasks="""
  repairer:
    provider: fake_provider
    prompt_ref: repairer/claim_repair@v1
"""
    )
    manager.call(
        task="repairer",
        messages_override=[{"role": "user", "content": "x"}],
        timeout=3,
    )
    assert fake.requests[-1].params["timeout"] == 3
