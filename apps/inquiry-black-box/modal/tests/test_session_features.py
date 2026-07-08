import json

import pytest

from inquiry_jobs import run_smoke_job
from model_env import resolve_model_environment
from models.calibration import train_toy_calibration
from models.session_features import RedactionViolation, extract_session_features


def redacted_session_export():
    return {
        "session_id": "session-modal-1",
        "exported_at": "2026-07-07T12:00:00Z",
        "events": [
            {
                "event_id": "event-1",
                "session_id": "session-modal-1",
                "event_type": "browser.typing_metrics",
                "monotonic_ms": 100,
                "privacy_class": "redacted-sync",
                "payload": {
                    "field_role": "search",
                    "burst_length": 7,
                    "pause_ms": 450,
                    "backspace_count": 1,
                    "edit_churn": 0.2,
                },
            },
            {
                "event_id": "event-2",
                "session_id": "session-modal-1",
                "event_type": "camera.feature_window",
                "monotonic_ms": 1100,
                "privacy_class": "redacted-sync",
                "payload": {
                    "window_ms": 1000,
                    "face_present_ratio": 1.0,
                    "gaze_away_ratio": 0.25,
                    "blink_proxy": 0.15,
                    "head_pose_variance": 0.4,
                    "motion_score": 0.3,
                },
            },
            {
                "event_id": "event-3",
                "session_id": "session-modal-1",
                "event_type": "label.added",
                "monotonic_ms": 1500,
                "privacy_class": "redacted-sync",
                "payload": {"label": "confused-good"},
            },
        ],
    }


def test_extracts_features_from_redacted_export():
    features = extract_session_features(redacted_session_export())

    assert features["session_id"] == "session-modal-1"
    assert features["event_count"] == 3
    assert features["event_type_counts"]["browser.typing_metrics"] == 1
    assert features["typing"]["total_burst_length"] == 7
    assert features["camera"]["avg_gaze_away_ratio"] == pytest.approx(0.25)
    assert features["labels"]["confused-good"] == 1
    assert features["provenance"]["input_event_ids"] == ["event-1", "event-2", "event-3"]


@pytest.mark.parametrize("field", ["rawFrame", "keyText", "documentText", "rawVideo"])
def test_rejects_sensitive_session_fields(field):
    export = redacted_session_export()
    export["events"][0]["payload"][field] = "sensitive"

    with pytest.raises(RedactionViolation):
        extract_session_features(export)


def test_trains_toy_calibration_model_card():
    features = extract_session_features(redacted_session_export())
    model_card = train_toy_calibration(
        [
            {"features": features, "outcome": "useful"},
            {"features": {**features, "event_count": 1, "labels": {}}, "outcome": "needs_repair"},
        ]
    )

    assert model_card["model_name"] == "toy_session_calibration"
    assert model_card["metrics"]["training_examples"] == 2
    assert "limitations" in model_card
    assert model_card["provenance"]["feature_version"] == "session_features@0.1.0"


def test_smoke_job_returns_report_and_model_card():
    report = run_smoke_job(redacted_session_export())

    assert report["report_type"] == "modal_smoke_report"
    assert report["session_id"] == "session-modal-1"
    assert report["feature_summary"]["event_count"] == 3
    assert report["model_card"]["model_name"] == "toy_session_calibration"
    assert report["provenance"]["input_privacy"] == "redacted"
    assert report["provenance"]["model_environment"]["version"] == "model_env@0.1.0"


def test_model_environment_reuses_canonical_provider_and_research_keys(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-secret-value")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-secret-value")
    monkeypatch.setenv("HF_TOKEN", "hf-secret-value")
    monkeypatch.setenv("MODEL_PROVIDER", "anthropic")
    monkeypatch.setenv("SESSION_SUMMARY_MODEL", "claude-session-model")
    monkeypatch.setenv("TRIBE_MODEL_ID", "facebook/tribev2")
    monkeypatch.setenv("BRAINDECODE_MODEL_ID", "braindecode/cbramod-pretrained")
    monkeypatch.setenv("MODAL_ENVIRONMENT", "main")

    summary = resolve_model_environment()
    serialized = json.dumps(summary)

    assert summary["routing"]["provider"] == "anthropic"
    assert summary["routing"]["session_summary_model"] == "claude-session-model"
    assert summary["providers"]["anthropic"]["configured"] is True
    assert summary["providers"]["anthropic"]["configured_secret_keys"] == ["ANTHROPIC_API_KEY"]
    assert summary["providers"]["openai"]["configured_secret_keys"] == ["OPENAI_API_KEY"]
    assert summary["providers"]["huggingface"]["configured_secret_keys"] == ["HF_TOKEN"]
    assert summary["research_models"]["tribe"]["model_id"] == "facebook/tribev2"
    assert summary["research_models"]["brain2qwerty"]["repo"] == "facebookresearch/brain2qwerty"
    assert summary["research_models"]["braindecode"]["model_id"] == "braindecode/cbramod-pretrained"
    assert "MODAL_ENVIRONMENT" in summary["deploy"]["modal"]["configured_keys"]
    assert "anthropic-secret-value" not in serialized
    assert "openai-secret-value" not in serialized
    assert "hf-secret-value" not in serialized
