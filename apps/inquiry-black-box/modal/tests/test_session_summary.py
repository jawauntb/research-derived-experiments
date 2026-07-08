import json

import pytest

from inquiry_jobs import run_session_summary_job
from models.session_features import RedactionViolation
from models.session_summary import summarize_redacted_session


def redacted_summary_input():
    return {
        "privacy_class": "redacted-sync",
        "payload": {
            "report_id": "session-interpretation:session-modal-1",
            "report_kind": "session_interpretation",
            "subject_session_id": "session-modal-1",
            "marker_count": 3,
            "theme_count": 1,
            "open_loop_count": 1,
            "next_action_count": 1,
            "summary": "Redacted local session summary with 1 theme, 1 open loop, and 1 next action.",
            "themes": [
                {
                    "kind": "open-loop",
                    "title": "Copied passage needs follow-up",
                    "confidence": 0.82,
                    "marker_count": 1,
                    "evidence_count": 2,
                }
            ],
            "next_actions": [
                {
                    "suggestion_kind": "refocus",
                    "category": "open_loops",
                    "title": "Turn the copied claim into a question",
                    "confidence": 0.79,
                    "evidence_count": 2,
                }
            ],
            "limitations": ["No raw text, screenshots, app names, or window titles included."],
            "provenance": {
                "input_report_id": "session-interpretation:session-modal-1",
                "builder": "test-redacted-session-summary-input@0.1.0",
                "excludes": ["raw selected text", "app names", "window titles"],
            },
        },
    }


def test_session_summary_job_returns_redacted_model_ready_report(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "anthropic")
    monkeypatch.setenv("SESSION_SUMMARY_MODEL", "claude-session-model")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret-value")

    report = run_session_summary_job(redacted_summary_input())
    serialized = json.dumps(report)

    assert report["report"]["payload"]["input_report_id"] == "session-interpretation:session-modal-1"
    assert report["report"]["payload"]["llm"] == {
        "status": "model-ready",
        "provider": "anthropic",
        "model": "claude-session-model",
        "input_contract": "redacted local interpretation only",
    }
    assert "Copied passage needs follow-up" in report["report"]["payload"]["executive_summary"]
    assert "secret-value" not in serialized
    assert "raw selected text" in serialized


@pytest.mark.parametrize("field", ["app_name", "bundle_id", "window_title", "rawFrame", "documentText"])
def test_session_summary_rejects_local_identity_and_raw_fields(field):
    job_input = redacted_summary_input()
    job_input["payload"][field] = "private"

    with pytest.raises(RedactionViolation):
        summarize_redacted_session(job_input)


def test_session_summary_requires_interpretation_payload_shape():
    job_input = redacted_summary_input()
    job_input["payload"]["report_kind"] = "daily_review"

    with pytest.raises(ValueError, match="session_interpretation"):
        summarize_redacted_session(job_input)


def test_session_summary_tolerates_missing_item_titles():
    job_input = redacted_summary_input()
    job_input["payload"]["themes"] = [{"kind": "retry"}]
    job_input["payload"]["next_actions"] = [{"suggestion_kind": "retry"}]

    report = summarize_redacted_session(job_input)

    assert report["report"]["payload"]["top_theme_titles"] == ["Untitled theme"]
    assert report["report"]["payload"]["suggestion_titles"] == ["Untitled suggestion"]
