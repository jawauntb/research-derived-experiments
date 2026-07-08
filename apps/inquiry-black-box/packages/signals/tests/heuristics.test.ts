import { describe, expect, test } from "bun:test";
import { createEvent, type EventEnvelope, type EventType, type JsonObject } from "@inquiry/schema";
import { buildRepairCandidates, buildReplayMemo, buildReplayMarkers } from "../src";

function event(event_type: EventType, monotonic_ms: number, payload: JsonObject, quality_flags: string[] = []): EventEnvelope {
  return createEvent({
    session_id: "fixture-session",
    source: sourceForEventType(event_type),
    source_version: "test@0.1.0",
    monotonic_ms,
    event_type,
    payload,
    privacy_class: "local-derived",
    retention_policy: "local-default",
    quality_flags,
  });
}

function sourceForEventType(eventType: EventType): EventEnvelope["source"] {
  if (eventType.startsWith("camera")) {
    return "desktop-camera";
  }
  if (eventType.startsWith("desktop.")) {
    return "desktop-activity";
  }

  return "browser";
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

  test("marks frequent foreground app switching as app churn with event evidence", () => {
    const events = [
      event("desktop.app_focus", 1_000, { app_name: "Cursor", focus_started_monotonic_ms: 0, focus_ended_monotonic_ms: 1_000, duration_ms: 1_000, permission_status: "granted" }),
      event("desktop.app_focus", 3_000, { app_name: "Terminal", focus_started_monotonic_ms: 1_000, focus_ended_monotonic_ms: 3_000, duration_ms: 2_000, permission_status: "granted" }),
      event("desktop.app_focus", 5_000, { app_name: "Google Chrome", focus_started_monotonic_ms: 3_000, focus_ended_monotonic_ms: 5_000, duration_ms: 2_000, permission_status: "granted" }),
      event("desktop.app_focus", 8_000, { app_name: "Slack", focus_started_monotonic_ms: 5_000, focus_ended_monotonic_ms: 8_000, duration_ms: 3_000, permission_status: "granted" }),
    ];

    const marker = buildReplayMarkers(events, 30_000).find((item) => item.kind === "app-churn");

    expect(marker).toBeDefined();
    expect(marker?.evidence_event_ids).toHaveLength(4);
    expect(marker?.evidence.join(" ")).toContain("Cursor, Terminal, Google Chrome, Slack");
    expect(marker?.suggested_action).toContain("follow-up note");
  });

  test("marks long non-browser focus after browser research as a deep-work span", () => {
    const events = [
      event("browser.scroll", 1_000, { delta_y: 700 }),
      event("desktop.app_focus", 905_000, {
        app_name: "Cursor",
        bundle_id: "com.todesktop.230313mzl4w4u92",
        focus_started_monotonic_ms: 5_000,
        focus_ended_monotonic_ms: 905_000,
        duration_ms: 900_000,
        permission_status: "granted",
      }),
    ];

    const memo = buildReplayMemo(events);
    const marker = memo.markers.find((item) => item.kind === "deep-work-span");
    const repair = buildRepairCandidates(memo.heatmap).find((candidate) => candidate.action === "follow-up-note");

    expect(marker).toBeDefined();
    if (!marker) {
      throw new Error("expected deep-work marker");
    }

    expect(marker.evidence_event_ids).toHaveLength(2);
    expect(marker.evidence.join(" ")).toContain("Cursor held foreground");
    expect(marker.evidence.join(" ")).not.toMatch(/distract/i);
    expect(memo.markers.some((item) => item.kind === "off-browser-focus")).toBe(false);
    expect(memo.next_actions).toContain(marker.suggested_action);
    expect(repair?.evidence_event_ids).toEqual(expect.arrayContaining(marker.evidence_event_ids));
    expect(repair?.prompt).toContain("non-browser work block");
  });

  test("marks long app focus without a window title using app-level evidence", () => {
    const events = [
      event("desktop.app_focus", 360_000, {
        app_name: "Preview",
        bundle_id: "com.apple.Preview",
        focus_started_monotonic_ms: 60_000,
        focus_ended_monotonic_ms: 360_000,
        duration_ms: 300_000,
        permission_status: "granted",
      }),
    ];

    const marker = buildReplayMarkers(events).find((item) => item.kind === "off-browser-focus");

    expect(marker).toBeDefined();
    expect(marker?.evidence.join(" ")).toContain("Preview held foreground");
    expect(marker?.evidence.join(" ")).not.toContain("window_title");
  });

  test("coalesces noisy selection, highlight, and copy bursts into one copied-passage marker", () => {
    const events = [
      event("browser.selection", 7_000, {
        hostname_hash: "h_demo",
        url_hash: "h_page",
        selection_length: 120,
        range_count: 1,
      }),
      event("browser.highlight", 7_400, {
        hostname_hash: "h_demo",
        url_hash: "h_page",
        selection_length: 140,
        range_count: 1,
      }),
      event("browser.selection", 8_000, {
        hostname_hash: "h_demo",
        url_hash: "h_page",
        selection_length: 180,
        range_count: 1,
      }),
      event("browser.highlight", 8_300, {
        hostname_hash: "h_demo",
        url_hash: "h_page",
        selection_length: 180,
        range_count: 1,
      }),
      event("browser.copy", 9_000, {
        hostname_hash: "h_demo",
        url_hash: "h_page",
        selection_length: 180,
        range_count: 1,
      }),
    ];

    const markers = buildReplayMarkers(events);
    const copiedMarkers = markers.filter((marker) => marker.kind === "copied-passage");
    const memo = buildReplayMemo(events);
    const firstCopiedMarker = copiedMarkers[0];
    if (!firstCopiedMarker) {
      throw new Error("expected one copied marker");
    }

    expect(copiedMarkers).toHaveLength(1);
    expect(firstCopiedMarker.evidence.join(" ")).toContain("2 selection changes, 2 highlights, and 1 copy action");
    expect(firstCopiedMarker.evidence.join(" ")).toContain("Selection length ranged 120-180 characters");
    expect(memo.episodes).toHaveLength(1);
    expect(memo.episodes[0]?.marker_ids).toEqual([firstCopiedMarker.marker_id]);
    expect(memo.episodes[0]?.privacy_note).toContain("Raw selected or copied text was not stored");
  });

  test("keeps distant copied-passage bursts separate", () => {
    const events = [
      event("browser.copy", 1_000, {
        hostname_hash: "h_demo",
        url_hash: "h_page",
        selection_length: 80,
        range_count: 1,
      }),
      event("browser.copy", 20_000, {
        hostname_hash: "h_demo",
        url_hash: "h_page",
        selection_length: 90,
        range_count: 1,
      }),
    ];

    expect(buildReplayMarkers(events).filter((marker) => marker.kind === "copied-passage")).toHaveLength(2);
  });

  test("evidence episodes include snippets only for document opt-in selected text", () => {
    const events = [
      createEvent({
        session_id: "fixture-session",
        source: "browser",
        source_version: "test@0.1.0",
        monotonic_ms: 7_000,
        event_type: "browser.copy",
        payload: {
          hostname_hash: "h_demo",
          url_hash: "h_page",
          selection_length: 36,
          range_count: 1,
          selected_text: "a copied claim about residual evidence",
        },
        privacy_class: "document-opt-in",
        retention_policy: "session-delete",
      }),
    ];

    const memo = buildReplayMemo(events);

    expect(memo.episodes).toHaveLength(1);
    expect(memo.episodes[0]?.snippets).toEqual(["a copied claim about residual evidence"]);
    expect(memo.episodes[0]?.details.join(" ")).toContain('Opt-in excerpt: "a copied claim about residual evidence"');
    expect(memo.episodes[0]?.privacy_note).toContain("opt-in was enabled");
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
