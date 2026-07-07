import { describe, expect, test } from "bun:test";
import { createEvent } from "@inquiry/schema";
import { createSessionReplayReport } from "../src/main/reports/sessionReplay";

describe("session replay report", () => {
  test("creates a replay report with limitations and next actions", () => {
    const events = [
      createEvent({
        session_id: "replay-session",
        source: "browser",
        source_version: "test@0.1.0",
        monotonic_ms: 1_000,
        event_type: "browser.scroll",
        payload: { delta_y: 4200 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
      createEvent({
        session_id: "replay-session",
        source: "browser",
        source_version: "test@0.1.0",
        monotonic_ms: 2_000,
        event_type: "browser.dwell",
        payload: { dwell_ms: 200 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ];

    const report = createSessionReplayReport(events);

    expect(report.markers.some((marker) => marker.kind === "skim-risk")).toBe(true);
    expect(report.next_actions.length).toBe(1);
    expect(report.limitations.join(" ")).toContain("not cognitive-state certainty");
  });
});
