import { describe, expect, test } from "bun:test";
import { createInquiryDatabase } from "../src/main/db";
import { createSessionController } from "../src/main/ingest/session";
import { createIdleIntegrityWatcher } from "../src/main/ingest/idleIntegrity";

describe("idle integrity watcher", () => {
  test("nudges once after sustained idle recording and respects cooldown", () => {
    let now = 0;
    const database = createInquiryDatabase();
    const sessions = createSessionController(database, {
      nowIso: () => new Date(now).toISOString(),
      nowMs: () => now,
    });
    const session = sessions.startSession({ title: "Idle fixture", monotonic_ms: 0 });
    const watcher = createIdleIntegrityWatcher({
      database,
      sessions,
      settings: { idle_threshold_ms: 1_000, cooldown_ms: 5_000, auto_pause: false },
      clock: { nowMs: () => now, nowIso: () => new Date(now).toISOString() },
    });

    watcher.recordActivity(0);
    now = 2_000;
    watcher.tick();
    watcher.tick();

    const events = database.listEvents(session.session_id);
    const nudge = events.find((event) => event.event_type === "notification.candidate");
    expect(nudge).toBeDefined();
    expect(nudge?.payload).toMatchObject({ kind: "idle-integrity", decision: "still-recording-prompt" });
    expect(sessions.currentSession()?.recording_state).toBe("recording");

    now = 3_000;
    watcher.tick();
    expect(database.listEvents(session.session_id).filter((event) => event.event_type === "notification.candidate")).toHaveLength(1);
    database.close();
  });

  test("auto-pauses recording when configured and idle threshold is exceeded", () => {
    let now = 0;
    const database = createInquiryDatabase();
    const sessions = createSessionController(database, {
      nowIso: () => new Date(now).toISOString(),
      nowMs: () => now,
    });
    const session = sessions.startSession({ title: "Auto pause fixture", monotonic_ms: 0 });
    const watcher = createIdleIntegrityWatcher({
      database,
      sessions,
      settings: { idle_threshold_ms: 500, cooldown_ms: 5_000, auto_pause: true },
      clock: { nowMs: () => now, nowIso: () => new Date(now).toISOString() },
    });

    watcher.recordActivity(0);
    now = 1_000;
    watcher.tick();

    expect(sessions.currentSession()?.recording_state).toBe("paused");
    expect(database.listEvents(session.session_id).some((event) => event.event_type === "session.paused")).toBe(true);
    database.close();
  });
});
