from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from model_env import resolve_model_environment
from models.session_features import assert_redacted_payload


SUMMARY_VERSION = "redacted_session_summary@0.1.0"


def summarize_redacted_session(job_input: dict[str, Any], env: dict[str, str | None] | None = None) -> dict[str, Any]:
    assert_redacted_payload(job_input)
    payload = _payload_from_input(job_input)
    _validate_payload(payload)

    model_environment = resolve_model_environment(env)
    routing = model_environment.get("routing", {})
    provider = str(routing.get("provider") or "auto")
    model = routing.get("session_summary_model")
    suggestions = _suggestions(payload)
    themes = _themes(payload)
    open_loop_count = _int(payload.get("open_loop_count"))
    summary = _summary_text(payload, themes, suggestions, open_loop_count)

    return {
        "report": {
            "title": "Modal session summary report",
            "summary": "Modal report completed.",
            "payload": {
                "summary_version": SUMMARY_VERSION,
                "input_report_id": payload["report_id"],
                "subject_session_id": payload.get("subject_session_id"),
                "executive_summary": summary,
                "top_theme_titles": [_title(theme, "Untitled theme") for theme in themes[:3]],
                "suggestion_titles": [_title(suggestion, "Untitled suggestion") for suggestion in suggestions[:3]],
                "counts": {
                    "markers": _int(payload.get("marker_count")),
                    "themes": _int(payload.get("theme_count")),
                    "open_loops": open_loop_count,
                    "next_actions": _int(payload.get("next_action_count")),
                },
                "llm": {
                    "status": "model-ready" if model else "not_configured",
                    "provider": provider,
                    "model": model,
                    "input_contract": "redacted local interpretation only",
                },
                "limitations": _list(payload.get("limitations")),
            },
            "provenance": {
                "summary_version": SUMMARY_VERSION,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "input_privacy": job_input.get("privacy_class"),
                "source_report_id": payload["report_id"],
                "input_provenance": payload.get("provenance", {}),
                "model_environment": model_environment,
                "excluded_fields": [
                    "raw typed text",
                    "raw selected text",
                    "raw page text",
                    "screenshots",
                    "OCR text",
                    "desktop event objects",
                    "app names",
                    "window titles",
                ],
            },
        }
    }


def _payload_from_input(job_input: dict[str, Any]) -> dict[str, Any]:
    if job_input.get("privacy_class") != "redacted-sync":
        raise ValueError("session summary jobs require redacted-sync input")
    payload = job_input.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("session summary input must include a payload object")
    return payload


def _validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("report_kind") != "session_interpretation":
        raise ValueError("session summary payload must be a session_interpretation report")
    for key in ("report_id", "summary"):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise ValueError(f"session summary payload.{key} must be a non-empty string")
    for key in ("marker_count", "theme_count", "open_loop_count", "next_action_count"):
        if not isinstance(payload.get(key), (int, float)):
            raise ValueError(f"session summary payload.{key} must be numeric")
    for key in ("themes", "next_actions", "limitations"):
        if not isinstance(payload.get(key), list):
            raise ValueError(f"session summary payload.{key} must be a list")
    if not isinstance(payload.get("provenance"), dict):
        raise ValueError("session summary payload.provenance must be an object")


def _summary_text(
    payload: dict[str, Any],
    themes: list[dict[str, Any]],
    suggestions: list[dict[str, Any]],
    open_loop_count: int,
) -> str:
    lead = str(payload["summary"])
    theme_title = _title(themes[0], "No dominant theme") if themes else "No dominant theme"
    suggestion_title = _title(suggestions[0], "No next action") if suggestions else "No next action"
    return f"{lead} Top theme: {theme_title}. Next action: {suggestion_title}. Open loops: {open_loop_count}."


def _themes(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in _list(payload.get("themes")) if isinstance(item, dict)]


def _suggestions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in _list(payload.get("next_actions")) if isinstance(item, dict)]


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    return 0


def _title(item: dict[str, Any], fallback: str) -> str:
    title = item.get("title")
    return title.strip() if isinstance(title, str) and title.strip() else fallback
