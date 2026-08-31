# Sourced from MIDAS with permission (see bio-claim-firewall/PROVENANCE.md).
"""Lifted from MIDAS src/models/providers/base.py. Adapted:

  - `ChatRequest` / `ModelResponse` moved to `../types.py` (see that
    module's docstring) and `ModelResponse` renamed `ChatResponse`;
    `base.py` now imports them rather than defining them, so this module
    has no pydantic/PIL dependency of its own beyond the abstract
    provider interface.
  - `images` handling dropped implicitly: `ChatRequest` no longer has an
    `images` field (bio-claim-firewall has no vision pipeline).
  - `ModelProvider` renamed `BaseProvider` per PHASE_4_PLAN.md naming.

This module is intentionally pure-stdlib so that `model_manager.providers`
can always be imported, even in an environment with none of the optional
provider SDKs (`ollama`, `openai`, `httpx`, `tenacity`, `truststore`,
`pydantic`) installed. See providers/__init__.py.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..types import ChatRequest, ChatResponse


class ModelError(RuntimeError):
    """Unified provider error base."""


class ModelTimeout(ModelError):
    """A provider call exceeded its timeout."""


class ModelRetryable(ModelError):
    """A transient provider error; safe to retry."""


class BaseProvider(ABC):
    @abstractmethod
    def chat(self, req: ChatRequest) -> ChatResponse:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> bool:
        raise NotImplementedError
