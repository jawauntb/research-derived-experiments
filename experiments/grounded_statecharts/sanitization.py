"""Fail-closed public-row sanitization for grounded live evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

BLOCKED_PUBLIC_FIELDS = frozenset(
    {
        "raw",
        "raw_response",
        "raw_request",
        "provider_payload",
        "transcript",
        "messages",
        "prompt",
        "system_prompt",
        "hidden_cot",
        "chain_of_thought",
        "api_key",
        "authorization",
        "secret",
        "token",
        "password",
        "cookie",
    }
)

REQUIRED_PUBLIC_FIELDS = frozenset(
    {
        "episode_id",
        "run_id",
        "task_id",
        "family",
        "condition",
        "repeat_index",
        "adapter_id",
        "model_id",
        "provider_id",
        "false_completion",
        "task_success",
        "joint_success",
        "refusal",
        "invalid_transition",
        "recovery_success",
        "useful_autonomy",
        "call_count",
        "input_tokens",
        "output_tokens",
        "tool_calls",
        "latency_ms",
        "estimated_cost_usd",
        "budget_exhausted",
        "integrity",
        "task_digest",
        "harness_digest",
        "budget_digest",
        "checkpoint_digest",
        "result_digest",
        "event_count",
        "public_event_digests",
    }
)


@dataclass(frozen=True)
class SanitizationReceipt:
    sanitized: bool
    blocked_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    public_row: dict[str, object]

    @property
    def ok(self) -> bool:
        return self.sanitized and not self.blocked_fields and not self.missing_fields

    def to_dict(self) -> dict[str, object]:
        return {
            "sanitized": self.sanitized,
            "blocked_fields": list(self.blocked_fields),
            "missing_fields": list(self.missing_fields),
            "ok": self.ok,
        }


def _blocked_keys(payload: Mapping[str, Any], *, prefix: str = "") -> list[str]:
    blocked: list[str] = []
    for key, value in payload.items():
        path = f"{prefix}{key}"
        lowered = key.lower()
        if lowered in BLOCKED_PUBLIC_FIELDS or any(
            token in lowered for token in ("api_key", "secret", "password", "authorization")
        ):
            blocked.append(path)
            continue
        if isinstance(value, Mapping):
            blocked.extend(_blocked_keys(value, prefix=f"{path}."))
    return blocked


def sanitize_public_row(row: Mapping[str, Any]) -> SanitizationReceipt:
    """Project a candidate row to the public contract or refuse publication."""

    blocked = tuple(sorted(_blocked_keys(row)))
    missing = tuple(sorted(REQUIRED_PUBLIC_FIELDS - set(row)))
    if blocked or missing:
        return SanitizationReceipt(
            sanitized=False,
            blocked_fields=blocked,
            missing_fields=missing,
            public_row={},
        )

    public_row = {key: row[key] for key in sorted(REQUIRED_PUBLIC_FIELDS)}
    # Reject unexpected fields rather than silently dropping them.
    extras = sorted(set(row) - REQUIRED_PUBLIC_FIELDS)
    if extras:
        return SanitizationReceipt(
            sanitized=False,
            blocked_fields=tuple(extras),
            missing_fields=(),
            public_row={},
        )
    return SanitizationReceipt(
        sanitized=True,
        blocked_fields=(),
        missing_fields=(),
        public_row=public_row,
    )
