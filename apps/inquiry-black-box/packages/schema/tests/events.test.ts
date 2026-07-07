import { describe, expect, test } from "bun:test";
import {
  canExportPrivacyClass,
  canSyncPrivacyClass,
  createEvent,
  validateEvent,
  type BrowserTypingMetricsPayload,
  type CameraFeaturePayload,
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
});
