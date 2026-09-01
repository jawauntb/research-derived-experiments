"""Compatibility adapter for the Phase 4b proposer/repairer call shape.

Phase 4b was built against a small, message-oriented model-manager protocol.
Phase 4a's real :class:`ModelManager` instead owns task configuration,
versioned prompt rendering, and provider metadata.  This adapter accepts the
former protocol, renders the configured prompt through the latter, and returns
the provenance fields that the proposer and repairer record in their results.

It is deliberately a boundary object: model output remains text and parsed
JSON data, and the deterministic verifier remains outside the model path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from numbers import Real
from typing import Any, NoReturn

from .errors import ModelManagerError
from .manager import ModelManager


@dataclass(frozen=True, slots=True)
class AdapterChatResponse:
    """Phase 4b's provenance-shaped view of a real model response."""

    content: str
    provider: str
    model: str
    prompt_ref: str
    prompt_version: str
    latency_ms: int
    tokens_prompt: int
    tokens_completion: int


class ModelManagerAdapter:
    """Translate the Phase 4b call contract into the real manager contract."""

    def __init__(self, manager: ModelManager) -> None:
        self._manager = manager

    def call(
        self,
        task: str,
        user_msg: str,
        *,
        system_msg: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        timeout_s: float | None = None,
        prompt_ref: str | None = None,
    ) -> AdapterChatResponse:
        del system_msg  # The configured versioned prompt owns system content.

        task_cfg = self._task_config(task)
        configured_prompt_ref = task_cfg.get("prompt_ref")
        if prompt_ref is not None and prompt_ref != configured_prompt_ref:
            raise ModelManagerError(
                "adapter_prompt_ref_mismatch",
                task=task,
                stage="adapter",
                message=(
                    f"Task {task!r} is configured for prompt_ref {configured_prompt_ref!r}; "
                    f"the adapter cannot override it with {prompt_ref!r}."
                ),
            )

        params: dict[str, Any] = {}
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        if temperature is not None:
            params["temperature"] = temperature
        if timeout_s is not None:
            params["timeout"] = timeout_s

        response = self._manager.call(
            task=task,
            variables=self._variables_for_task(task, user_msg),
            **params,
        )
        return self._adapt_response(task, response)

    def _task_config(self, task: str) -> dict[str, Any]:
        if task == "checker":
            # Preserve ModelManager's fail-closed checker refusal.
            self._manager.call(task=task, variables={})

        task_cfg = self._manager.config["tasks"].get(task)
        if task_cfg is None:
            raise ValueError(f"Unknown task: {task}")
        return task_cfg

    def _variables_for_task(self, task: str, user_msg: str) -> dict[str, Any]:
        payload = self._load_payload(task, user_msg)
        if task == "proposer":
            self._require_keys(task, payload, "question", "evidence_records", "context_hints")
            return payload

        if task == "repairer":
            self._require_keys(task, payload, "failed_claim", "verdict", "evidence_records")
            verdict = payload["verdict"]
            if not isinstance(verdict, dict):
                self._invalid_request(task, "'verdict' must be a JSON object")
            reasons = verdict.get("reasons", [])
            if not isinstance(reasons, list):
                self._invalid_request(task, "'verdict.reasons' must be a JSON array")
            return {
                "failed_claim": payload["failed_claim"],
                "fault_code": verdict.get("fault_code", "UNKNOWN"),
                "reasons": [self._reason_text(reason) for reason in reasons],
                "evidence_records": payload["evidence_records"],
            }

        self._invalid_request(task, "only proposer and repairer are model tasks")

    @staticmethod
    def _reason_text(reason: Any) -> str:
        if isinstance(reason, dict) and isinstance(reason.get("message"), str):
            return reason["message"]
        return str(reason)

    def _load_payload(self, task: str, user_msg: str) -> dict[str, Any]:
        try:
            payload = json.loads(user_msg)
        except json.JSONDecodeError as exc:
            self._invalid_request(task, f"user_msg must be a JSON object: {exc}")
        if not isinstance(payload, dict):
            self._invalid_request(task, "user_msg must encode a JSON object")
        return payload

    def _require_keys(self, task: str, payload: dict[str, Any], *keys: str) -> None:
        missing = [key for key in keys if key not in payload]
        if missing:
            self._invalid_request(task, f"user_msg is missing required key(s): {', '.join(missing)}")

    def _invalid_request(self, task: str, message: str) -> NoReturn:
        raise ModelManagerError("adapter_invalid_request", task=task, stage="adapter", message=message)

    def _adapt_response(self, task: str, response: Any) -> AdapterChatResponse:
        task_cfg = self._manager.config["tasks"][task]
        provider_cfg = self._manager.config["providers"][task_cfg["provider"]]
        meta = response.meta if isinstance(getattr(response, "meta", None), dict) else {}
        usage_value = meta.get("usage")
        usage: dict[str, Any] = usage_value if isinstance(usage_value, dict) else {}
        prompt_ref = response.prompt_ref or task_cfg.get("prompt_ref") or ""
        prompt_version = response.prompt_version or _prompt_version(prompt_ref)

        return AdapterChatResponse(
            content=response.content,
            provider=str(meta.get("provider") or provider_cfg.get("type") or task_cfg["provider"]),
            model=str(meta.get("model") or task_cfg.get("model") or provider_cfg.get("model") or ""),
            prompt_ref=prompt_ref,
            prompt_version=prompt_version,
            latency_ms=_latency_ms(meta),
            tokens_prompt=_token_count(usage.get("prompt_tokens", meta.get("prompt_eval_count"))),
            tokens_completion=_token_count(
                usage.get("completion_tokens", meta.get("eval_count"))
            ),
        )


def adapt_model_manager(manager: Any) -> Any:
    """Wrap real managers while preserving the existing lightweight fakes.

    The structural check accepts either supported import spelling
    (``model_manager`` or ``src.model_manager``) without accidentally
    wrapping the Phase 4b test doubles.
    """

    if isinstance(manager, ModelManagerAdapter):
        return manager
    if hasattr(manager, "config") and hasattr(manager, "_providers") and callable(
        getattr(manager, "call", None)
    ):
        return ModelManagerAdapter(manager)
    return manager


def _prompt_version(prompt_ref: str) -> str:
    return prompt_ref.rsplit("@", 1)[1] if "@" in prompt_ref else ""


def _latency_ms(meta: dict[str, Any]) -> int:
    if isinstance(meta.get("latency_ms"), Real):
        return round(meta["latency_ms"])
    if isinstance(meta.get("latency"), Real):
        return round(meta["latency"] * 1000)
    return 0


def _token_count(value: Any) -> int:
    return int(value) if isinstance(value, Real) else 0
