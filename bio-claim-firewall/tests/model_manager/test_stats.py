"""Every call increments stats: total_calls, total_tokens, latency_ms
(as total_latency_ms), errors."""
from __future__ import annotations

import pytest

pytest.importorskip("yaml")


def test_successful_call_increments_stats(manager_with_fake):
    manager, fake = manager_with_fake
    manager.call(task="proposer", messages_override=[{"role": "user", "content": "x"}])
    stats = manager.get_stats("proposer")
    assert stats["total_calls"] == 1
    assert stats["successful_calls"] == 1
    assert stats["errors"] == 0
    assert stats["total_latency_ms"] > 0
    assert stats["total_tokens"] == 7  # FakeProvider's default meta.usage.total_tokens


def test_failed_call_increments_errors(make_manager):
    manager, fake = make_manager()
    fake.raise_error = RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        manager.call(task="proposer", messages_override=[{"role": "user", "content": "x"}])

    stats = manager.get_stats("proposer")
    assert stats["total_calls"] == 1
    assert stats["successful_calls"] == 0
    assert stats["errors"] == 1
    assert stats["total_latency_ms"] > 0
    assert stats["total_tokens"] == 0


def test_stats_accumulate_across_calls(manager_with_fake):
    manager, fake = manager_with_fake
    manager.call(task="proposer", messages_override=[{"role": "user", "content": "x"}])
    manager.call(task="proposer", messages_override=[{"role": "user", "content": "y"}])
    stats = manager.get_stats("proposer")
    assert stats["total_calls"] == 2
    assert stats["successful_calls"] == 2
    assert stats["total_tokens"] == 14


def test_get_stats_all_tasks(make_manager):
    manager, fake = make_manager(
        extra_tasks="""
  repairer:
    provider: fake_provider
    prompt_ref: repairer/claim_repair@v1
"""
    )
    manager.call(task="proposer", messages_override=[{"role": "user", "content": "x"}])
    manager.call(task="repairer", messages_override=[{"role": "user", "content": "y"}])

    all_stats = manager.get_stats()
    assert "proposer" in all_stats
    assert "repairer" in all_stats
    assert all_stats["proposer"]["total_calls"] == 1
    assert all_stats["repairer"]["total_calls"] == 1


def test_get_stats_unknown_task_returns_empty(manager_with_fake):
    manager, _fake = manager_with_fake
    assert manager.get_stats("never_called") == {}
