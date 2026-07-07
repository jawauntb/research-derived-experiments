from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from models.session_features import FEATURE_VERSION


MODEL_VERSION = "toy_calibration@0.1.0"


def train_toy_calibration(samples: list[dict[str, Any]]) -> dict[str, Any]:
    if not samples:
        raise ValueError("at least one calibration sample is required")

    scored = [_score_sample(sample) for sample in samples]
    threshold = sum(score for score, _outcome in scored) / len(scored)
    correct = 0
    for score, outcome in scored:
        predicted = "useful" if score >= threshold else "needs_repair"
        if predicted == outcome:
            correct += 1

    return {
        "model_name": "toy_session_calibration",
        "model_version": MODEL_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "intended_use": "Smoke-test personalized calibration plumbing on redacted session features.",
        "features": ["event_count", "duration_ms", "labels", "typing.total_burst_length", "camera.avg_gaze_away_ratio"],
        "decision_rule": {
            "type": "mean_threshold",
            "threshold": threshold,
            "positive_label": "useful",
            "negative_label": "needs_repair",
        },
        "metrics": {
            "training_examples": len(samples),
            "training_accuracy": correct / len(samples),
        },
        "provenance": {
            "feature_version": FEATURE_VERSION,
            "model_version": MODEL_VERSION,
            "input_rows": len(samples),
        },
        "limitations": [
            "Toy calibration only; it is not a validated state classifier.",
            "Needs user-specific verifier outcomes before real personalization.",
            "Must not be used for medical, diagnostic, or surveillance decisions.",
        ],
    }


def _score_sample(sample: dict[str, Any]) -> tuple[float, str]:
    features = sample.get("features")
    if not isinstance(features, dict):
        raise ValueError("calibration sample must include feature dict")

    outcome = sample.get("outcome")
    if outcome not in {"useful", "needs_repair"}:
        raise ValueError("calibration sample outcome must be useful or needs_repair")

    labels = features.get("labels") if isinstance(features.get("labels"), dict) else {}
    typing = features.get("typing") if isinstance(features.get("typing"), dict) else {}
    camera = features.get("camera") if isinstance(features.get("camera"), dict) else {}

    score = float(features.get("event_count", 0))
    score += float(features.get("duration_ms", 0)) / 1000.0
    score += float(typing.get("total_burst_length", 0)) * 0.1
    score -= float(camera.get("avg_gaze_away_ratio", 0)) * 0.5
    score += float(labels.get("confused-good", 0)) * 1.5
    score -= float(labels.get("confused-bad", 0)) * 1.5

    return score, str(outcome)
