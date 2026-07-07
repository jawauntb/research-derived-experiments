from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from models.calibration import train_toy_calibration
from models.session_features import extract_session_features

try:
    import modal as modal_module
except ImportError:  # pragma: no cover - exercised only when Modal is installed
    modal_module: Any | None = None


def synthetic_redacted_export() -> dict[str, Any]:
    return {
        "session_id": "synthetic-session",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "events": [
            {
                "event_id": "synthetic-typing",
                "session_id": "synthetic-session",
                "event_type": "browser.typing_metrics",
                "monotonic_ms": 100,
                "privacy_class": "redacted-sync",
                "payload": {
                    "field_role": "search",
                    "burst_length": 6,
                    "pause_ms": 380,
                    "backspace_count": 1,
                    "edit_churn": 0.2,
                },
            },
            {
                "event_id": "synthetic-camera",
                "session_id": "synthetic-session",
                "event_type": "camera.feature_window",
                "monotonic_ms": 900,
                "privacy_class": "redacted-sync",
                "payload": {
                    "window_ms": 1000,
                    "face_present_ratio": 1.0,
                    "gaze_away_ratio": 0.18,
                    "blink_proxy": 0.12,
                    "head_pose_variance": 0.25,
                    "motion_score": 0.2,
                },
            },
            {
                "event_id": "synthetic-label",
                "session_id": "synthetic-session",
                "event_type": "label.added",
                "monotonic_ms": 1200,
                "privacy_class": "redacted-sync",
                "payload": {"label": "confused-good"},
            },
        ],
    }


def run_smoke_job(session_export: dict[str, Any] | None = None) -> dict[str, Any]:
    export = session_export or synthetic_redacted_export()
    features = extract_session_features(export)
    model_card = train_toy_calibration(
        [
            {"features": features, "outcome": "useful"},
            {"features": {**features, "event_count": max(1, int(features["event_count"]) - 2), "labels": {}}, "outcome": "needs_repair"},
        ]
    )

    return {
        "report_type": "modal_smoke_report",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "session_id": features["session_id"],
        "summary": "Synthetic Modal analysis completed on redacted session features.",
        "feature_summary": {
            "event_count": features["event_count"],
            "duration_ms": features["duration_ms"],
            "event_type_counts": features["event_type_counts"],
            "labels": features["labels"],
        },
        "model_card": model_card,
        "provenance": {
            "input_privacy": "redacted",
            "feature_version": features["provenance"]["feature_version"],
            "limitations": features["provenance"]["limitations"],
        },
    }


def run_calibration_job(samples: list[dict[str, Any]]) -> dict[str, Any]:
    return train_toy_calibration(samples)


if modal_module:
    app = modal_module.App("inquiry-black-box")

    @app.function()
    def smoke_job(session_export: dict[str, Any] | None = None) -> dict[str, Any]:
        return run_smoke_job(session_export)

    @app.function()
    def calibration_job(samples: list[dict[str, Any]]) -> dict[str, Any]:
        return run_calibration_job(samples)

    @app.function()
    @modal_module.fastapi_endpoint(method="POST")
    def job_webhook(request: dict[str, Any]) -> dict[str, Any]:
        job_id = str(request.get("job_id", "unknown"))
        kind = str(request.get("kind", "session_summary"))
        return {
            "modal_call_id": f"modal-{kind}-{job_id}",
            "status": "submitted",
        }
else:
    app = None

    def smoke_job(session_export: dict[str, Any] | None = None) -> dict[str, Any]:
        return run_smoke_job(session_export)

    def calibration_job(samples: list[dict[str, Any]]) -> dict[str, Any]:
        return run_calibration_job(samples)

    def job_webhook(request: dict[str, Any]) -> dict[str, Any]:
        job_id = str(request.get("job_id", "unknown"))
        kind = str(request.get("kind", "session_summary"))
        return {
            "modal_call_id": f"local-modal-{kind}-{job_id}",
            "status": "submitted",
        }
