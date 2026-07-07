import { describe, expect, test } from "bun:test";
import { createEvent } from "@inquiry/schema";
import { createInquiryDatabase } from "../src/main/db";
import { exportSession } from "../src/main/privacy/export";

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
        event_type: "report.generated",
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
});
