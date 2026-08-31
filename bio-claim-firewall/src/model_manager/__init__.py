# Sourced from MIDAS with permission (see bio-claim-firewall/PROVENANCE.md), adapted for
# bio-claim-firewall.
"""bio-claim-firewall model_manager package.

Lifted/adapted from MIDAS's `src/models/` + `src/config/profiles.py` (see
bio-claim-firewall/PROVENANCE.md): provider->model routing, versioned
Jinja2 prompts, and task-based dispatch for the untrusted `proposer` and
`repairer` tasks. `checker` (the deterministic rule engine) is
deliberately NOT dispatchable through this package — see manager.py.
"""
from __future__ import annotations

from .errors import ModelManagerError
from .manager import ModelManager, Provider
from .types import ChatRequest, ChatResponse

__all__ = [
    "ModelManager",
    "Provider",
    "PromptManager",
    "ChatRequest",
    "ChatResponse",
    "ProfileConfig",
    "ModelManagerError",
]


def __getattr__(name: str):
    """PEP 562 lazy attribute access for `PromptManager` / `ProfileConfig`.

    `prompts.py` imports jinja2 + pyyaml unconditionally at module top, and
    `profiles.py` imports pyyaml unconditionally — both lifted ~verbatim
    from MIDAS (see their own headers). Importing either eagerly here
    would mean `import model_manager` itself required those packages.
    # MODEL-MANAGER-DECISION: deferring via module `__getattr__` means
    `model_manager.PromptManager` / `model_manager.ProfileConfig` resolve
    on first access instead, matching the deferred-import strategy used
    throughout this package (see manager.py's module docstring for the
    full rationale — this sandbox has no interpreter with jinja2 + pyyaml
    + pydantic installed together).
    """
    if name == "PromptManager":
        from .prompts import PromptManager

        return PromptManager
    if name == "ProfileConfig":
        from .profiles import ProfileConfig

        return ProfileConfig
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
