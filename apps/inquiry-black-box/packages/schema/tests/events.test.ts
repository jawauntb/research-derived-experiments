import { describe, expect, test } from "bun:test";
import {
  canExportPrivacyClass,
  canSyncPrivacyClass,
  createEvent,
  validateEvent,
  type BrowserTypingMetricsPayload,
  type CameraFeaturePayload,
  type RepairCandidatePayload,
  type RepairOutcomePayload,
  type StimulusAttachedPayload,
} from "../src";

describe("event schema", () => {
  test("creates and validates browser typing metrics without text content", () => {
    const payload: BrowserTypingMetricsPayload = {
      field_role: "search",
      burst_length: 8,
      pause_ms: 420,
      backspace_count: 2,
      edit_churn: 0.25,
    };

    const event = createEvent({
      session_id: "session-1",
      source: "browser",
      source_version: "extension@0.1.0",
      monotonic_ms: 10,
      event_type: "browser.typing_metrics",
      payload,
      privacy_class: "local-derived",
      retention_policy: "local-default",
    });

    expect(event.payload.field_role).toBe("search");
    expect(JSON.stringify(event.payload)).not.toContain("hello");
  });

  test("accepts camera features and rejects image payload fields", () => {
    const payload: CameraFeaturePayload = {
      window_ms: 1000,
      face_present_ratio: 1,
      gaze_away_ratio: 0.2,
      blink_proxy: 0.1,
      head_pose_variance: 0.3,
      motion_score: 0.4,
    };

    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "desktop-camera",
        source_version: "desktop@0.1.0",
        monotonic_ms: 20,
        event_type: "camera.feature_window",
        payload,
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).not.toThrow();

    expect(() =>
      validateEvent({
        event_id: "bad-camera",
        session_id: "session-1",
        source: "desktop-camera",
        source_version: "desktop@0.1.0",
        captured_at: new Date().toISOString(),
        monotonic_ms: 20,
        timezone: "UTC",
        event_type: "camera.feature_window",
        confidence: 1,
        quality_flags: [],
        payload: { rawFrame: "base64" },
        privacy_class: "debug-sensitive",
        retention_policy: "debug-ephemeral",
      }),
    ).toThrow(/blocked sensitive/);
  });

  test("makes privacy sync/export eligibility explicit", () => {
    expect(canSyncPrivacyClass("redacted-sync").allowed).toBe(true);
    expect(canSyncPrivacyClass("local-derived").allowed).toBe(false);
    expect(canExportPrivacyClass("local-derived").allowed).toBe(true);
    expect(canExportPrivacyClass("debug-sensitive").allowed).toBe(false);
  });

  test("allows stimulus references but requires document opt-in for raw text", () => {
    const payload: StimulusAttachedPayload = {
      stimulus_id: "article-1",
      source: "article",
      content_ref: "article:article-1:abc123#1",
      document_opt_in: false,
      title: "Demo article",
    };

    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "stimulus",
        source_version: "desktop@0.1.0",
        monotonic_ms: 30,
        event_type: "stimulus.attached",
        payload,
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).not.toThrow();

    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "stimulus",
        source_version: "desktop@0.1.0",
        monotonic_ms: 31,
        event_type: "stimulus.attached",
        payload: { ...payload, text: "raw article body" },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).toThrow(/document-opt-in/);
  });

  test("requires document opt-in for raw browser selected text", () => {
    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "browser",
        source_version: "extension@0.1.0",
        monotonic_ms: 35,
        event_type: "browser.copy",
        payload: {
          hostname_hash: "h_demo",
          url_hash: "h_page",
          selection_length: 13,
          selected_text: "copied claim",
        },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).toThrow(/document-opt-in/);

    const event = createEvent({
      session_id: "session-1",
      source: "browser",
      source_version: "extension@0.1.0",
      monotonic_ms: 36,
      event_type: "browser.copy",
      payload: {
        hostname_hash: "h_demo",
        url_hash: "h_page",
        selection_length: 13,
        selected_text: "copied claim",
      },
      privacy_class: "document-opt-in",
      retention_policy: "session-delete",
    });

    expect(event.privacy_class).toBe("document-opt-in");
    expect(canExportPrivacyClass(event.privacy_class).allowed).toBe(true);
    expect(canSyncPrivacyClass(event.privacy_class).allowed).toBe(false);
  });

  test("accepts local repair candidate and outcome events", () => {
    const candidatePayload: RepairCandidatePayload = {
      repair_id: "repair-1",
      heatmap_id: "heatmap-1",
      action: "missing-prerequisite",
      prompt: "What prerequisite was missing?",
      start_ms: 1000,
      end_ms: 2000,
      source_kind: "behavioral-loss-of-thread",
      source_marker_ids: ["marker-1"],
      evidence_event_ids: ["event-1"],
      limitation: "repair hypothesis",
    };
    const outcomePayload: RepairOutcomePayload = {
      repair_id: "repair-1",
      heatmap_id: "heatmap-1",
      action: "missing-prerequisite",
      outcome: "dismissed",
      reason: "already answered",
    };

    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "desktop-system",
        source_version: "desktop@0.1.0",
        monotonic_ms: 40,
        event_type: "repair.candidate",
        payload: candidatePayload,
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).not.toThrow();
    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "user",
        source_version: "desktop@0.1.0",
        monotonic_ms: 41,
        event_type: "repair.outcome",
        payload: outcomePayload,
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).not.toThrow();
  });
});
