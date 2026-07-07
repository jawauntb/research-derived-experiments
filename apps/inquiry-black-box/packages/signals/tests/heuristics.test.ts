import { describe, expect, test } from "bun:test";
import { createEvent, type EventEnvelope, type EventType, type JsonObject } from "@inquiry/schema";
import { buildReplayMemo, buildReplayMarkers } from "../src";

function event(event_type: EventType, monotonic_ms: number, payload: JsonObject, quality_flags: string[] = []): EventEnvelope {
  return createEvent({
    session_id: "fixture-session",
    source: event_type.startsWith("camera") ? "desktop-camera" : "browser",
    source_version: "test@0.1.0",
    monotonic_ms,
    event_type,
    payload,
    privacy_class: "local-derived",
    retention_policy: "local-default",
    quality_flags,
  });
}

describe("replay heuristics", () => {
  test("fixture session produces skim, stuck, copied, rewind, and tab markers", () => {
    const events = [
      event("browser.scroll", 1_000, { delta_y: 1800 }),
      event("browser.scroll", 2_000, { delta_y: 1400 }),
      event("browser.dwell", 3_000, { dwell_ms: 500 }),
      event("browser.visibility", 4_000, { state: "revisited" }),
      event("browser.visibility", 5_000, { state: "revisited" }),
      event("browser.media", 6_000, { action: "seeked", delta_ms: -15_000 }),
      event("browser.copy", 7_000, { selection_length: 120 }),
      event("browser.tab", 8_000, { action: "activated" }),
      event("browser.tab", 9_000, { action: "activated" }),
      event("browser.tab", 10_000, { action: "activated" }),
      event("browser.tab", 11_000, { action: "activated" }),
    ];

    const kinds = buildReplayMarkers(events, 30_000).map((marker) => marker.kind);

    expect(kinds).toContain("skim-risk");
    expect(kinds).toContain("stuck-loop");
    expect(kinds).toContain("copied-passage");
    expect(kinds).toContain("rewind");
    expect(kinds).toContain("tab-churn");
  });

  test("low camera quality suppresses high-load marker", () => {
    const events = [
      event("camera.feature_window", 1_000, { gaze_away_ratio: 0.9 }, ["face-missing"]),
      event("browser.typing_metrics", 2_000, { pause_ms: 3000 }),
    ];

    expect(buildReplayMarkers(events).some((marker) => marker.kind === "high-load")).toBe(false);
  });

  test("memo returns evidence-backed next actions", () => {
    const events = [
      event("camera.feature_window", 1_000, { gaze_away_ratio: 0.7 }),
      event("browser.typing_metrics", 2_000, { pause_ms: 2400 }),
      event("browser.scroll", 3_000, { delta_y: 4000 }),
      event("browser.dwell", 4_000, { dwell_ms: 300 }),
    ];

    const memo = buildReplayMemo(events);

    expect(memo.next_actions.length).toBeGreaterThanOrEqual(2);
    expect(memo.markers.every((marker) => marker.evidence_event_ids.length > 0)).toBe(true);
  });
});
