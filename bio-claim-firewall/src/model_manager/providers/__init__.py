# Sourced from MIDAS with permission (see bio-claim-firewall/PROVENANCE.md), adapted for
# bio-claim-firewall — this guarded re-export pattern does not exist upstream.
"""Re-exports the provider ABC and concrete provider implementations.

Each concrete provider's third-party dependency (`ollama` for
OllamaProvider; `openai` + `httpx` + `tenacity` + `truststore` for
OpenAIProvider and GroqProvider) is optional at the bio-claim-firewall
project level — see PHASE_4_PLAN.md's dependency list and the Phase 4a
task instructions ("treat them as optional deps ... do not silently add
packages"). # MODEL-MANAGER-DECISION: import failures here are caught so
that `import model_manager.providers` always succeeds — even in an
environment with none of those packages installed — and the affected
provider class is left as `None` rather than breaking the whole package.
Callers (ModelManager._get_provider) raise a clear ModelManagerError if a
caller actually tries to construct a provider whose class is `None`.
Tests import-skip (`pytest.importorskip("ollama")` etc.) around anything
that needs a *real* concrete provider; FakeProvider-based tests never hit
this at all.
"""
from __future__ import annotations

from .base import BaseProvider, ModelError, ModelRetryable, ModelTimeout

# "Provider type" per the Phase 4a task's export list for this module —
# an alias for the ABC, distinct from the `Provider` *enum* (task/provider
# routing ids) exported from `model_manager.manager` / the top-level
# `model_manager` package. Two different concepts happen to share the
# name "Provider"; keeping them in separate namespaces (`model_manager.Provider`
# vs `model_manager.providers.Provider`) avoids a collision.
# # MODEL-MANAGER-DECISION
Provider = BaseProvider

try:
    from .ollama import OllamaProvider
except ImportError:  # pragma: no cover - depends on optional 'ollama' package
    OllamaProvider = None

try:
    from .openai_sdk import OpenAIProvider
except ImportError:  # pragma: no cover - depends on optional openai/httpx/tenacity/truststore
    OpenAIProvider = None

try:
    from .groq_provider import GroqProvider
except ImportError:  # pragma: no cover - depends on OpenAIProvider's optional deps
    GroqProvider = None

__all__ = [
    "Provider",
    "BaseProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "GroqProvider",
    "ModelError",
    "ModelRetryable",
    "ModelTimeout",
]
