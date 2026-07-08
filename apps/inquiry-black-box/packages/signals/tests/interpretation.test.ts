import { describe, expect, test } from "bun:test";
import { createEvent, type JsonObject } from "@inquiry/schema";
import {
  buildReplayMemo,
  buildSessionInterpretation,
  redactedSessionSummaryJobInput,
  sessionInterpretationReportPayload,
  type ReplayMemo,
} from "../src";

describe("session interpretation", () => {
  test("summarizes web search churn and copied evidence with evidence-linked next actions", () => {
    const events = [
      event("browser.typing_metrics", 100, { field_role: "search", burst_length: 8, pause_ms: 2200, backspace_count: 1, edit_churn: 0.2 }),
      event("browser.tab", 200, { action: "activated", url_hash: "url-a", hostname_hash: "host-a" }),
      event("browser.tab", 300, { action: "activated", url_hash: "url-b", hostname_hash: "host-b" }),
      event("browser.tab", 400, { action: "activated", url_hash: "url-a", hostname_hash: "host-a" }),
      event("browser.tab", 500, { action: "activated", url_hash: "url-c", hostname_hash: "host-c" }),
      event("browser.copy", 800, { url_hash: "url-c", hostname_hash: "host-c", selection_length: 180, range_count: 1 }),
      event("browser.highlight", 900, { url_hash: "url-c", hostname_hash: "host-c", selection_length: 180, range_count: 1 }),
    ];
    const replay = { ...buildReplayMemo(events, 30_000), report_id: "replay-search-1", limitations: ["Replay limitation."] };

    const interpretation = buildSessionInterpretation({
      replay,
      events,
      session: { title: "Web search session" },
      generated_at: "2026-07-08T12:00:00.000Z",
    });

    expect(interpretation.summary).toContain("Web search session");
    expect(interpretation.themes.map((theme) => theme.title)).toContain("Tab branch fragmentation");
    expect(interpretation.next_actions.length).toBeGreaterThan(0);
    expect(interpretation.next_actions[0]?.evidence_event_ids.length).toBeGreaterThan(0);
    expect(interpretation.open_loops.length).toBeGreaterThan(0);
    expect(interpretation.limitations.join(" ")).toContain("raw selected text");
    expect(sessionInterpretationReportPayload(interpretation).suggestion_ids).toEqual(
      interpretation.next_actions.map((suggestion) => suggestion.suggestion_id),
    );
  });

  test("keeps mixed desktop/browser context local and redacts LLM job input", () => {
    const events = [
      event("browser.tab", 100, { action: "activated", url_hash: "url-paper", hostname_hash: "host-paper" }),
      createEvent({
        event_id: "desktop-focus-1",
        session_id: "session-interpret",
        source: "desktop-activity",
        source_version: "desktop@0.1.0",
        captured_at: "2026-07-08T12:00:00.000Z",
        monotonic_ms: 650_000,
        timezone: "UTC",
        event_type: "desktop.app_focus",
        confidence: 0.9,
        quality_flags: [],
        payload: {
          app_name: "Cursor",
          bundle_id: "com.todesktop.cursor",
          focus_started_monotonic_ms: 10_000,
          focus_ended_monotonic_ms: 650_000,
          duration_ms: 640_000,
          permission_status: "granted",
        },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ];
    const interpretation = buildSessionInterpretation({
      replay: { ...buildReplayMemo(events, 30_000), report_id: "replay-desktop-1" },
      events,
      generated_at: "2026-07-08T12:30:00.000Z",
    });
    const redacted = redactedSessionSummaryJobInput(interpretation);

    expect(interpretation.themes.some((theme) => theme.title === "Deep work block")).toBe(true);
    expect(interpretation.limitations.join(" ")).toContain("Desktop app context");
    expect(JSON.stringify(redacted)).not.toContain("Cursor");
    expect(JSON.stringify(redacted)).not.toContain("com.todesktop.cursor");
    expect(JSON.stringify(redacted)).not.toContain("desktop.app_focus");
    expect(redacted.privacy_class).toBe("redacted-sync");
  });

  test("returns a low-confidence interpretation for sparse sessions", () => {
    const replay: ReplayMemo & { report_id: string; limitations: string[] } = {
      session_id: "empty-session",
      report_id: "replay-empty",
      markers: [],
      episodes: [],
      heatmap: [],
      next_actions: [],
      limitations: ["No markers."],
    };

    const interpretation = buildSessionInterpretation({
      replay,
      generated_at: "2026-07-08T12:00:00.000Z",
    });

    expect(interpretation.confidence).toBeLessThan(0.4);
    expect(interpretation.summary).toContain("sparse");
    expect(interpretation.next_actions[0]?.suggestion_kind).toBe("daily-checkup");
  });
});

function event(event_type: Parameters<typeof createEvent>[0]["event_type"], monotonic_ms: number, payload: JsonObject) {
  return createEvent({
    event_id: `${event_type}-${monotonic_ms}`,
    session_id: "session-interpret",
    source: "browser",
    source_version: "extension@0.1.0",
    captured_at: "2026-07-08T12:00:00.000Z",
    monotonic_ms,
    timezone: "UTC",
    event_type,
    payload,
    privacy_class: "local-derived",
    retention_policy: "local-default",
  });
}
