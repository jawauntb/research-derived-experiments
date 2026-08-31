"""conftest for bio-claim-firewall/tests/model_manager/.

`sys.path` for `src/` (so `from model_manager... import ...` works) is
already set up by the repo-root `bio-claim-firewall/conftest.py`.

Provides:
  - `FakeProvider`: a `BaseProvider` that returns a canned `ChatResponse`
    for any `.chat()` call and never touches the network or a real
    provider SDK. Tests inject it by pre-populating
    `ModelManager._providers[name] = FakeProvider(...)` before calling
    `manager.call(...)` — `_get_provider` checks that cache before doing
    any real provider construction, so no `ollama`/`openai` package or
    network access is ever required by these tests
    (see test_no_network.py).
  - `write_config` / `make_manager` / `manager_with_fake`: build a
    minimal, valid model_manager config.yaml wired to a `FakeProvider`.

Content here is new to bio-claim-firewall (not lifted from MIDAS), though
its shape mirrors what MIDAS's tests/manager/test_model_manager.py mocks
via `unittest.mock.patch` — pre-populating the provider cache is the
FakeProvider-based equivalent for Phase 4a.

# MODEL-MANAGER-DECISION: `pytest.importorskip("yaml")` is deliberately
# NOT called at this module's top level. pytest.importorskip raising
# `Skipped` during *conftest.py* collection aborts the whole session
# instead of degrading gracefully (unlike the same call inside a regular
# test module, which pytest skips cleanly — see test_prompts.py). None of
# `model_manager.manager` / `.providers.base` / `.types` need pyyaml just
# to *import* (see their own deferred-import decisions), so importing them
# here is safe; the guard is instead placed inside the fixtures that
# actually construct a `ModelManager` (which needs pyyaml only at
# `_load_config()` time), so only those specific tests skip when pyyaml
# is unavailable.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

from model_manager.manager import ModelManager
from model_manager.providers.base import BaseProvider
from model_manager.types import ChatRequest, ChatResponse


class FakeProvider(BaseProvider):
    """Canned-response provider. Records every request it receives so
    tests can assert on dispatch, params, and timeouts without a real
    provider package or network access."""

    def __init__(
        self,
        content: str = '{"ok": true}',
        meta: Optional[Dict[str, Any]] = None,
        raise_error: Optional[BaseException] = None,
    ) -> None:
        self.content = content
        self.meta = meta if meta is not None else {"usage": {"total_tokens": 7}}
        self.raise_error = raise_error
        self.requests: List[ChatRequest] = []
        self.cleaned_up = False

    def chat(self, req: ChatRequest) -> ChatResponse:
        self.requests.append(req)
        if self.raise_error is not None:
            raise self.raise_error
        return ChatResponse(content=self.content, raw={"fake": True}, meta=dict(self.meta))

    def health_check(self) -> bool:
        return True

    def cleanup(self) -> None:
        self.cleaned_up = True


def write_config(tmp_path: Path, extra_tasks: str = "") -> Path:
    """Write a minimal, valid config.yaml (one fake provider, one
    `proposer` task with a task-level timeout_s) and return its path.
    `extra_tasks` is raw YAML appended under `tasks:` for tests that need
    an additional task (e.g. one without its own timeout_s)."""
    config_text = f"""
providers:
  fake_provider:
    type: fake
    model: fake-model-v1
    base_url: http://example.invalid
    timeout_s: 20

tasks:
  proposer:
    provider: fake_provider
    prompt_ref: proposer/claim_bundle@v1
    max_tokens: 500
    temperature: 0.0
    timeout_s: 45
{extra_tasks}
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_text)
    return config_file


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    return write_config(tmp_path)


@pytest.fixture
def make_manager(tmp_path: Path):
    """Factory fixture: `make_manager(extra_tasks="...")` builds a fresh
    ModelManager + FakeProvider pair (independent tmp_path each call).
    `ModelManager(...)` needs pyyaml (see manager.py's `_load_config`), so
    the import-skip guard lives here rather than at module top."""
    pytest.importorskip("yaml")

    def _make(extra_tasks: str = "") -> Tuple[ModelManager, FakeProvider]:
        cfg = write_config(tmp_path, extra_tasks=extra_tasks)
        mgr = ModelManager(cfg)
        fake = FakeProvider()
        mgr._providers["fake_provider"] = fake
        return mgr, fake

    return _make


@pytest.fixture
def manager_with_fake(make_manager) -> Tuple[ModelManager, FakeProvider]:
    return make_manager()
