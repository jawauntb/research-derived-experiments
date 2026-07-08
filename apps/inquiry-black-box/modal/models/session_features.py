from __future__ import annotations

from collections import Counter
from typing import Any


FEATURE_VERSION = "session_features@0.1.0"
ALLOWED_PRIVACY_CLASSES = {"public", "redacted-sync", "document-opt-in"}
SENSITIVE_FIELD_NAMES = {
    "rawFrame",
    "frameImage",
    "keyText",
    "documentText",
    "rawVideo",
    "videoBytes",
    "keyContent",
    "app_name",
    "appName",
    "bundle_id",
    "bundleId",
    "window_title",
    "windowTitle",
}


class RedactionViolation(ValueError):
    """Raised when a Modal payload contains fields outside the redacted contract."""


def extract_session_features(session_export: dict[str, Any]) -> dict[str, Any]:
    assert_redacted_payload(session_export)
    events = _events_from_export(session_export)
    if not events:
        raise ValueError("session export must contain at least one event")

    session_id = str(session_export.get("session_id") or events[0].get("session_id") or "unknown-session")
    _assert_allowed_privacy(events)

    event_type_counts = Counter(str(event.get("event_type", "unknown")) for event in events)
    privacy_classes = sorted({str(event.get("privacy_class", "unknown")) for event in events})
    monotonic_values = [event.get("monotonic_ms") for event in events if isinstance(event.get("monotonic_ms"), (int, float))]
    duration_ms = int(max(monotonic_values) - min(monotonic_values)) if len(monotonic_values) >= 2 else 0

    typing = _typing_features(events)
    camera = _camera_features(events)
    labels = Counter(
        str(event.get("payload", {}).get("label"))
        for event in events
        if isinstance(event.get("payload"), dict) and event.get("payload", {}).get("label")
    )

    return {
        "session_id": session_id,
        "event_count": len(events),
        "duration_ms": duration_ms,
        "event_type_counts": dict(event_type_counts),
        "privacy_classes": privacy_classes,
        "typing": typing,
        "camera": camera,
        "labels": dict(labels),
        "provenance": {
            "feature_version": FEATURE_VERSION,
            "input_event_ids": [str(event.get("event_id", "unknown")) for event in events],
            "limitations": [
                "Synthetic foundation features only.",
                "No diagnostic or workplace-surveillance inference.",
                "Requires user-specific outcomes before personalization is meaningful.",
            ],
        },
    }


def assert_redacted_payload(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in SENSITIVE_FIELD_NAMES:
                raise RedactionViolation(f"{child_path} is not allowed in Modal redacted jobs")
            assert_redacted_payload(child, child_path)
        return

    if isinstance(value, list):
        for index, child in enumerate(value):
            assert_redacted_payload(child, f"{path}[{index}]")


def _events_from_export(session_export: dict[str, Any]) -> list[dict[str, Any]]:
    events = session_export.get("events")
    if not isinstance(events, list) or not all(isinstance(event, dict) for event in events):
        raise ValueError("session export must include an events list")
    return events


def _assert_allowed_privacy(events: list[dict[str, Any]]) -> None:
    rejected = [
        str(event.get("event_id", "unknown"))
        for event in events
        if event.get("privacy_class") not in ALLOWED_PRIVACY_CLASSES
    ]
    if rejected:
        raise RedactionViolation(f"events are not eligible for Modal analysis: {', '.join(rejected)}")


def _typing_features(events: list[dict[str, Any]]) -> dict[str, Any]:
    payloads = [
        event.get("payload", {})
        for event in events
        if event.get("event_type") == "browser.typing_metrics" and isinstance(event.get("payload"), dict)
    ]
    return {
        "windows": len(payloads),
        "total_burst_length": int(sum(_number(payload.get("burst_length")) for payload in payloads)),
        "total_backspace_count": int(sum(_number(payload.get("backspace_count")) for payload in payloads)),
        "avg_pause_ms": _average(_number(payload.get("pause_ms")) for payload in payloads),
        "avg_edit_churn": _average(_number(payload.get("edit_churn")) for payload in payloads),
    }


def _camera_features(events: list[dict[str, Any]]) -> dict[str, Any]:
    payloads = [
        event.get("payload", {})
        for event in events
        if event.get("event_type") == "camera.feature_window" and isinstance(event.get("payload"), dict)
    ]
    return {
        "windows": len(payloads),
        "avg_face_present_ratio": _average(_number(payload.get("face_present_ratio")) for payload in payloads),
        "avg_gaze_away_ratio": _average(_number(payload.get("gaze_away_ratio")) for payload in payloads),
        "avg_blink_proxy": _average(_number(payload.get("blink_proxy")) for payload in payloads),
        "avg_head_pose_variance": _average(_number(payload.get("head_pose_variance")) for payload in payloads),
        "avg_motion_score": _average(_number(payload.get("motion_score")) for payload in payloads),
    }


def _number(value: Any) -> float:
    return float(value) if isinstance(value, (int, float)) else 0.0


def _average(values: Any) -> float:
    numbers = list(values)
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
