import { describe, expect, test } from "bun:test";
import { createEvent } from "@inquiry/schema";
import { createRepairCandidateEvent, createRepairOutcomeEvent, type RepairCandidate } from "@inquiry/signals";
import { createInquiryDatabase } from "../src/main/db";
import { exportSession } from "../src/main/privacy/export";
import { createSessionInterpretationReport } from "../src/main/reports/sessionInterpretation";

describe("local inquiry database", () => {
  test("persists validated events and exports readable JSONL", () => {
    const database = createInquiryDatabase();
    const session = database.createSession({ title: "Reading session", session_id: "session-db-1" });

    database.appendEvent(
      createEvent({
        session_id: session.session_id,
        source: "browser",
        source_version: "extension@0.1.0",
        monotonic_ms: 100,
        event_type: "browser.scroll",
        payload: { url_hash: "url-1", scroll_y: 320, viewport_h: 900 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );

    const events = database.listEvents(session.session_id);
    expect(events).toHaveLength(1);
    expect(events[0]?.event_type).toBe("browser.scroll");

    const exported = exportSession(database, session.session_id);
    expect(exported.jsonl).toContain('"type":"session"');
    expect(exported.jsonl).toContain('"browser.scroll"');
    const parsed = exported.jsonl
      .trim()
      .split("\n")
      .map((line) => JSON.parse(line) as { type: string; event?: { event_type: string } });
    expect(parsed).toEqual([
      expect.objectContaining({ type: "session" }),
      expect.objectContaining({ type: "event", event: expect.objectContaining({ event_type: "browser.scroll" }) }),
    ]);
    database.close();
  });

  test("omits debug-sensitive events from default exports", () => {
    const database = createInquiryDatabase();
    const session = database.createSession({ title: "Debug session", session_id: "session-db-2" });

    database.appendEvent(
      createEvent({
        session_id: session.session_id,
        source: "desktop-system",
        source_version: "desktop@0.1.0",
        monotonic_ms: 0,
        event_type: "sync.queued",
        payload: { debug_summary: "local only" },
        privacy_class: "debug-sensitive",
        retention_policy: "debug-ephemeral",
      }),
    );

    expect(database.exportSessionJsonl(session.session_id)).not.toContain("debug_summary");
    database.close();
  });

  test("deleting a session removes dependent events", () => {
    const database = createInquiryDatabase();
    const session = database.createSession({ title: "Delete session", session_id: "session-db-3" });
    database.appendSystemEvent({ session_id: session.session_id, event_type: "session.started" });

    database.deleteSession(session.session_id);

    expect(database.getSession(session.session_id)).toBeNull();
    expect(database.listEvents(session.session_id)).toEqual([]);
    database.close();
  });

  test("persists repair candidates and outcomes as exportable events", () => {
    const database = createInquiryDatabase();
    const session = database.createSession({ title: "Repair session", session_id: "session-db-4" });
    const candidate: RepairCandidate = {
      repair_id: "repair-db-1",
      session_id: session.session_id,
      heatmap_id: "heatmap-db-1",
      action: "missing-prerequisite",
      prompt: "What prerequisite was missing?",
      start_ms: 1000,
      end_ms: 2000,
      confidence: 0.8,
      source_kind: "behavioral-loss-of-thread",
      source_marker_ids: ["marker-db-1"],
      evidence_event_ids: ["event-db-1"],
      limitation: "repair hypothesis",
    };

    database.appendEvent(createRepairCandidateEvent(candidate, { event_id: "repair-candidate-db-1" }));
    database.appendEvent(
      createRepairOutcomeEvent({
        candidate,
        event_id: "repair-outcome-db-1",
        outcome: "dismissed",
        reason: "already fixed",
      }),
    );

    expect(database.listRepairEvents(session.session_id).map((event) => event.event_type)).toEqual([
      "repair.candidate",
      "repair.outcome",
    ]);
    expect(database.exportSessionJsonl(session.session_id)).toContain("repair-outcome-db-1");
    database.close();
  });

  test("lists sessions and exports generated reports plus suggestions", () => {
    const database = createInquiryDatabase();
    const older = database.createSession({ title: "Older", session_id: "session-db-older" });
    const session = database.createSession({ title: "Generated artifacts", session_id: "session-db-generated" });

    database.appendEvent(
      createEvent({
        session_id: session.session_id,
        source: "browser",
        source_version: "extension@0.1.0",
        monotonic_ms: 1_000,
        event_type: "browser.scroll",
        payload: { delta_y: 4_800, scroll_y: 4_800, viewport_h: 900 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );
    database.appendEvent(
      createEvent({
        session_id: session.session_id,
        source: "browser",
        source_version: "extension@0.1.0",
        monotonic_ms: 1_500,
        event_type: "browser.dwell",
        payload: { dwell_ms: 200 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );
    database.stopSession(session.session_id, "2026-07-07T12:10:00.000Z");

    const report = createSessionInterpretationReport(database, session.session_id);
    const exported = exportSession(database, session.session_id);

    expect(database.listSessions().map((record) => record.session_id)).toEqual(expect.arrayContaining([older.session_id, session.session_id]));
    expect(report.next_actions.length).toBeGreaterThan(0);
    expect(database.listEvents(session.session_id).map((event) => event.event_type)).toEqual(
      expect.arrayContaining(["report.generated", "suggestion.candidate"]),
    );
    expect(exported.jsonl).toContain("session_interpretation");
    expect(exported.jsonl).toContain("suggestion.candidate");
    database.close();
  });
});
