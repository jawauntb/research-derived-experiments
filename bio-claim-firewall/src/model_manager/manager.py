# Sourced from MIDAS with permission (see bio-claim-firewall/PROVENANCE.md).
"""Adapted from MIDAS src/models/manager.py.

Adaptation notes (Phase 4a, bio-claim-firewall):

  - The Marker OCR/document-conversion branch is deleted outright: the
    `Service` enum, the `.marker` property, and the `MarkerService` import
    are all gone. bio-claim-firewall has no document-conversion pipeline
    (PHASE_4_PLAN.md "Skip: ... Marker OCR").
  - Task names renamed per the fault-split invariant: `reasoning` ->
    `proposer`, `verification` -> `checker`, `reasoning_repair` ->
    `repairer`. `checker` is deliberately NOT a model task in
    bio-claim-firewall — it is the deterministic rule engine that will
    live in `src/checker/` (Phase 4c+), not an LLM call. Calling
    `call(task="checker", ...)` refuses immediately with
    `ModelManagerError("checker_is_not_a_model_task", ...)` rather than
    dispatching to a provider, silently no-op'ing, or (worse) actually
    asking a model to "check" something.
  - Provider config shape changed: `providers.<name>.model` now lives on
    the *provider* entry (config.yaml pins one model per provider) instead
    of on the task, matching the config.yaml shape specified for Phase 4a.
    A task config carries `provider`, `prompt_ref`, generation params
    (`max_tokens`, `temperature`, ...), and `timeout_s`. `call()` still
    accepts a task-level `model` override for forward compatibility, but
    Phase 4a's config.yaml does not set one.
  - `Provider` enum gains `GROQ` (MIDAS's manager.py only had
    OLLAMA/OPENAI even though groq_provider.py already existed upstream).
    Enum values now match the `type:` strings used in Phase 4a's
    config.yaml (`"openai_sdk"`, not MIDAS's `"openai"`).
  - `images` parameter dropped from `call()` (see types.py — ChatRequest
    has no `images` field).
  - `ModelResponse` renamed `ChatResponse`; both dataclasses now live in
    `./types.py` and are imported from there instead of from
    `providers/base.py`.
  - `call()`'s signature changed from MIDAS's
    `call(task, prompt_ref, variables, ...)` to
    `call(task, variables=None, ...)`: `prompt_ref` is no longer a
    call-site argument because Phase 4a's config.yaml embeds `prompt_ref`
    directly on each task (see config.yaml). `messages_override` still
    lets a caller bypass prompt rendering entirely, exactly as upstream.

  # MODEL-MANAGER-DECISION: every third-party import (`yaml`, provider
  construction, `PromptManager` construction) is deferred into the
  method/property that actually needs it, rather than imported at module
  top as MIDAS's manager.py does. This sandbox has no single Python
  interpreter with jinja2 + pyyaml + pydantic all installed at once (see
  PROVENANCE.md / the Phase 4a task's Return notes) — deferring these
  imports lets `import model_manager` and `ModelManager(...)` construction
  succeed anywhere, and lets `call(..., messages_override=...)` work
  without jinja2 installed, while a real `.prompts.render(...)` call still
  requires jinja2, exactly as it would upstream. This changes *when* an
  ImportError can surface, never *whether* the dependency is required to
  do real work.
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, Union

from .errors import ModelManagerError
from .types import ChatRequest, ChatResponse

if TYPE_CHECKING:
    from pydantic import BaseModel
    from .prompts import PromptManager

logger = logging.getLogger(__name__)


class Provider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai_sdk"
    GROQ = "groq"


@dataclass(frozen=True)
class TaskConfig:
    provider: str
    prompt_ref: Optional[str]
    params: Dict[str, Any]
    timeout_s: Optional[float]


# Task-config keys that are routing/metadata, not generation params to hand
# the provider (e.g. `temperature`, `max_tokens`) verbatim.
_NON_PARAM_TASK_KEYS = {"provider", "prompt_ref", "timeout_s", "model", "description"}


class ModelManager:
    #: fallback timeout (seconds) applied when neither the task config nor
    #: a call-site override specifies one.
    DEFAULT_TIMEOUT_S: float = 60.0

    def __init__(self, config_path: Union[Path, str], prompts_dir: Optional[Path] = None):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._providers: Dict[str, Any] = {}
        self._stats: Dict[str, Dict[str, Any]] = {}

        if prompts_dir is not None:
            self._prompts_dir: Path = Path(prompts_dir)
        else:
            # src/model_manager/manager.py -> parents[1] == src -> ../prompts
            src_root = Path(__file__).parents[1]
            self._prompts_dir = src_root.parent / "prompts"
        self._prompts: Optional["PromptManager"] = None

    @property
    def prompts(self) -> "PromptManager":
        """Lazily-constructed PromptManager (see module docstring's
        MODEL-MANAGER-DECISION on deferred imports)."""
        if self._prompts is None:
            from .prompts import PromptManager

            self._prompts = PromptManager(self._prompts_dir)
        return self._prompts

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")

        import yaml

        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        if not config or "providers" not in config:
            raise ValueError("Config missing 'providers'")
        if "tasks" not in config:
            raise ValueError("Config missing 'tasks'")

        for provider_name, provider_cfg in config["providers"].items():
            if not isinstance(provider_cfg, dict) or "type" not in provider_cfg:
                raise ValueError(f"Provider '{provider_name}' missing type")

        for task_name, task_cfg in config["tasks"].items():
            if not isinstance(task_cfg, dict):
                raise ValueError(f"Task '{task_name}' has an invalid configuration")
            if "provider" not in task_cfg:
                raise ValueError(f"Task '{task_name}' missing provider")

            provider_name = task_cfg["provider"]
            if provider_name not in config["providers"]:
                raise ValueError(f"Task '{task_name}' references unknown provider '{provider_name}'")

        return config

    def _get_provider(self, provider_name: str):
        if provider_name in self._providers:
            return self._providers[provider_name]

        if provider_name not in self.config["providers"]:
            raise ValueError(f"Unknown provider: {provider_name}")

        provider_cfg = self.config["providers"][provider_name]
        provider_type = provider_cfg["type"]

        import os

        if provider_type == "ollama":
            from .providers import OllamaProvider

            if OllamaProvider is None:
                raise ModelManagerError(
                    "provider_dependency_missing",
                    provider=provider_name,
                    message="OllamaProvider requires the optional 'ollama' package, which is not installed.",
                )
            provider = OllamaProvider(
                host=provider_cfg.get("base_url", "http://localhost:11434"),
                request_timeout_s=provider_cfg.get("timeout_s", 300),
            )
        elif provider_type == "openai_sdk":
            from .providers import OpenAIProvider

            if OpenAIProvider is None:
                raise ModelManagerError(
                    "provider_dependency_missing",
                    provider=provider_name,
                    message=(
                        "OpenAIProvider requires the optional 'openai'/'httpx'/'tenacity'/"
                        "'truststore' packages, which are not all installed."
                    ),
                )
            api_key_env = provider_cfg.get("api_key_env")
            provider = OpenAIProvider(
                base_url=provider_cfg.get("base_url"),
                api_key=os.environ.get(api_key_env) if api_key_env else None,
                timeout=provider_cfg.get("timeout_s", 60.0),
            )
        elif provider_type == "groq":
            from .providers import GroqProvider

            if GroqProvider is None:
                raise ModelManagerError(
                    "provider_dependency_missing",
                    provider=provider_name,
                    message=(
                        "GroqProvider requires the optional 'openai'/'httpx'/'tenacity'/"
                        "'truststore' packages, which are not all installed."
                    ),
                )
            api_key_env = provider_cfg.get("api_key_env", "GROQ_API_KEY")
            provider = GroqProvider(api_key=os.environ.get(api_key_env))
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

        self._providers[provider_name] = provider
        logger.info(f"initialized provider: {provider_name}")
        return provider

    def call(
        self,
        task: str,
        variables: Optional[Dict[str, Any]] = None,
        schema: Optional[Type["BaseModel"]] = None,
        messages_override: Optional[List[Dict[str, str]]] = None,
        **params_override: Any,
    ) -> ChatResponse:
        start_time = time.perf_counter()

        if task == "checker":
            raise ModelManagerError(
                "checker_is_not_a_model_task",
                task=task,
                stage="dispatch",
                message=(
                    "'checker' is the deterministic rule engine (src/checker/), not a "
                    "model task. ModelManager refuses to dispatch it, per the "
                    "fault-split invariant (PHASE_4_PLAN.md)."
                ),
            )

        if task not in self.config["tasks"]:
            raise ValueError(f"Unknown task: {task}")

        task_cfg = self.config["tasks"][task]
        provider_name = task_cfg["provider"]
        provider_cfg = self.config["providers"].get(provider_name, {})
        model_name = task_cfg.get("model") or provider_cfg.get("model")
        if not model_name:
            raise ValueError(
                f"Task '{task}' has no model configured (checked task and provider '{provider_name}')"
            )

        prompt_ref = task_cfg.get("prompt_ref")

        if messages_override is not None:
            rendered = messages_override
        else:
            if prompt_ref is None:
                raise ValueError(f"Task '{task}' has no prompt_ref and no messages_override was given")
            rendered = self.prompts.render(prompt_ref, variables or {})

        params = {k: v for k, v in task_cfg.items() if k not in _NON_PARAM_TASK_KEYS}
        params = {**params, **params_override}
        params.setdefault("timeout", task_cfg.get("timeout_s", self.DEFAULT_TIMEOUT_S))

        request = ChatRequest(
            model=model_name,
            messages=rendered,
            params=params,
            schema=schema,
            extra_body=task_cfg.get("extra_body") or None,
        )

        provider = self._get_provider(provider_name)
        try:
            response = provider.chat(request)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            tokens = 0
            if isinstance(getattr(response, "meta", None), dict):
                usage = response.meta.get("usage") or {}
                tokens = usage.get("total_tokens", 0) or 0
            self._track_stats(task, elapsed_ms, success=True, tokens=tokens)

            prompt_version = prompt_ref.rsplit("@", 1)[1] if prompt_ref and "@" in prompt_ref else None
            return ChatResponse(
                content=response.content,
                raw=response.raw,
                meta=response.meta,
                parsed=response.parsed,
                prompt_ref=prompt_ref,
                prompt_version=prompt_version,
            )
        except Exception:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self._track_stats(task, elapsed_ms, success=False, tokens=0)
            raise

    def _track_stats(self, task: str, latency_ms: float, success: bool, tokens: int = 0) -> None:
        stats = self._stats.setdefault(
            task,
            {
                "total_calls": 0,
                "successful_calls": 0,
                "errors": 0,
                "total_latency_ms": 0.0,
                "total_tokens": 0,
            },
        )
        stats["total_calls"] += 1
        stats["total_latency_ms"] += latency_ms
        if success:
            stats["successful_calls"] += 1
            stats["total_tokens"] += tokens
        else:
            stats["errors"] += 1

    def get_stats(self, task: Optional[str] = None) -> Dict[str, Any]:
        if task:
            return self._stats.get(task, {})
        return self._stats

    def cleanup(self) -> None:
        for name, provider in self._providers.items():
            if hasattr(provider, "cleanup"):
                try:
                    provider.cleanup()
                    logger.info(f"Cleaned up provider: {name}")
                except Exception as e:
                    logger.error(f"Cleanup failed for {name}: {e}")

        self._providers.clear()

    @contextmanager
    def session(self):
        try:
            yield self
        finally:
            self.cleanup()
