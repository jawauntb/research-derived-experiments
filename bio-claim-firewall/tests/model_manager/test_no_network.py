"""Verify tests never touch the real providers: importing the provider
modules (even the optional ollama/openai ones, when their packages happen
to be installed) never attempts a network connection, and every dispatch
in this test suite goes through FakeProvider, never a real provider
class."""
from __future__ import annotations

import importlib
import socket

import pytest

pytest.importorskip("yaml")


def _blocked_socket(*args, **kwargs):
    raise AssertionError("Tests must never open a real network socket")


def test_importing_providers_package_opens_no_socket(monkeypatch):
    monkeypatch.setattr(socket, "socket", _blocked_socket)

    import model_manager.providers as providers_pkg

    importlib.reload(providers_pkg)

    # Either the optional package (ollama/openai/httpx/tenacity/truststore)
    # is installed and the class is real, or it's absent and
    # providers/__init__.py leaves the symbol as None — both are
    # acceptable outcomes of *importing*. What's unacceptable is a socket
    # ever being opened while doing so, which `_blocked_socket` would have
    # caught above.
    assert providers_pkg.BaseProvider is not None
    assert hasattr(providers_pkg, "OllamaProvider")
    assert hasattr(providers_pkg, "OpenAIProvider")
    assert hasattr(providers_pkg, "GroqProvider")


def test_dispatch_never_touches_real_provider(manager_with_fake, monkeypatch):
    monkeypatch.setattr(socket, "socket", _blocked_socket)

    manager, fake = manager_with_fake
    response = manager.call(task="proposer", messages_override=[{"role": "user", "content": "x"}])

    assert response.content == fake.content
    assert len(fake.requests) == 1
    # The only object ever constructed for provider_name "fake_provider"
    # is the FakeProvider that the test injected directly.
    assert manager._providers["fake_provider"] is fake


def test_unrecognized_provider_type_never_reaches_real_construction(make_manager, monkeypatch):
    """'fake' is not a provider `type` the manager knows how to construct
    for real (only 'ollama' / 'openai_sdk' / 'groq' are). If the
    FakeProvider injection in conftest were ever bypassed, calling would
    raise ValueError("Unknown provider type: fake") rather than silently
    falling through to a real provider — this test locks that in."""
    monkeypatch.setattr(socket, "socket", _blocked_socket)

    manager, _fake = make_manager()
    manager._providers.clear()  # remove the FakeProvider injection

    with pytest.raises(ValueError, match="Unknown provider type: fake"):
        manager.call(task="proposer", messages_override=[{"role": "user", "content": "x"}])
