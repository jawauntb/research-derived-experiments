# Sourced from MIDAS with permission (see bio-claim-firewall/PROVENANCE.md).
"""Adapted from MIDAS src/models/providers/base.py.

The `ChatRequest` / `ModelResponse` dataclasses are split out of
`providers/base.py` into their own module so they can be imported without
pulling in the provider ABC or provider-transport errors, and are
renamed/extended for bio-claim-firewall:

  - `ModelResponse` -> `ChatResponse` (Phase 4a naming).
  - `images` field dropped entirely (MIDAS coupling to the vision/Marker
    pipeline; out of scope per PHASE_4_PLAN.md "Skip: vision pipeline").
  - `prompt_ref` / `prompt_version` added to `ChatResponse` so every model
    call can be traced back to the exact prompt template + version that
    produced it, for the trajectory logger (Phase 4b).

# MODEL-MANAGER-DECISION: `BaseModel` is imported only under
# `TYPE_CHECKING` (with `from __future__ import annotations` making every
# annotation a string), so this module has **zero** runtime third-party
# dependencies — not even pydantic. This sandbox has no single Python
# interpreter with jinja2 + pyyaml + pydantic + httpx/tenacity installed
# together (see PROVENANCE.md and the Phase 4a task's Return section), so
# every module in this package that can plausibly avoid a hard runtime
# import of an optional third-party package does so, deferring the actual
# import to the point where the corresponding functionality is really
# used. Dataclass field annotations are never evaluated at runtime unless
# something calls `typing.get_type_hints()`, so this costs nothing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Type

if TYPE_CHECKING:
    from pydantic import BaseModel


@dataclass(frozen=True)
class Message:
    role: Literal["system", "user", "assistant"]
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class ChatRequest:
    model: str
    messages: List[Dict[str, Any]]
    params: Optional[Dict[str, Any]] = None
    schema: Optional[Type[BaseModel]] = None  # pydantic model -> json schema
    extra_body: Optional[Dict[str, Any]] = None  # extra body for openai-compatible endpoints


@dataclass(frozen=True)
class ChatResponse:
    content: str
    raw: Any  # provider-native response obj/dict
    meta: Dict[str, Any]  # timings, token counts, model, created_at, etc.
    parsed: Optional[BaseModel] = None  # populated if schema was provided
    prompt_ref: Optional[str] = None  # e.g. "proposer/claim_bundle@v1"
    prompt_version: Optional[str] = None  # e.g. "v1", parsed from prompt_ref
