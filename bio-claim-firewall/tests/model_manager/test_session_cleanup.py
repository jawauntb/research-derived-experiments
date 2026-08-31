"""`with manager.session(): ...` calls `cleanup()` on exit, even on
exception; `cleanup()` never raises even if a provider's own cleanup
does."""
from __future__ import annotations

import pytest

pytest.importorskip("yaml")


def test_session_calls_cleanup_on_normal_exit(manager_with_fake):
    manager, fake = manager_with_fake
    with manager.session() as mgr:
        assert mgr is manager
        assert "fake_provider" in mgr._providers
    assert fake.cleaned_up is True
    assert manager._providers == {}


def test_session_calls_cleanup_on_exception(manager_with_fake):
    manager, fake = manager_with_fake
    with pytest.raises(ValueError, match="boom"):
        with manager.session():
            raise ValueError("boom")
    assert fake.cleaned_up is True
    assert manager._providers == {}


def test_cleanup_direct(manager_with_fake):
    manager, fake = manager_with_fake
    manager.cleanup()
    assert fake.cleaned_up is True
    assert manager._providers == {}


def test_cleanup_survives_provider_cleanup_error(manager_with_fake, monkeypatch):
    manager, fake = manager_with_fake

    def _boom():
        raise Exception("cleanup failed")

    monkeypatch.setattr(fake, "cleanup", _boom)

    manager.cleanup()  # must not raise
    assert manager._providers == {}


def test_cleanup_is_idempotent(manager_with_fake):
    manager, fake = manager_with_fake
    manager.cleanup()
    manager.cleanup()  # second call: nothing left to clean, must not raise
    assert manager._providers == {}
