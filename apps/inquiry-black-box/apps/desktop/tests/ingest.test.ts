import { describe, expect, test } from "bun:test";
import { createEvent } from "@inquiry/schema";
import { createInquiryDatabase } from "../src/main/db";
import { createSessionController } from "../src/main/ingest/session";
import { createIngestRequestHandler } from "../src/main/ingest/server";
import { createGlobalHotkeyEvent } from "../src/main/security/hotkeys";
import { createPairingToken } from "../src/main/security/pairing";

const origin = "chrome-extension://extension-fixture";
const secret = "fixture-pairing-secret";
const issuedAtMs = 1_000;

function token(): string {
  return createPairingToken({ secret, issuedAtMs, nonce: "fixture-nonce" });
}

function eventRequest(body: unknown, overrides: { origin?: string; token?: string } = {}): Request {
  return new Request("http://127.0.0.1:39170/v1/events", {
    method: "POST",
    headers: {
      authorization: `Bearer ${overrides.token ?? token()}`,
      "content-type": "application/json",
      origin: overrides.origin ?? origin,
    },
    body: JSON.stringify(body),
  });
}

function extensionBatchRequest(body: unknown, overrides: { origin?: string; token?: string } = {}): Request {
  return new Request("http://127.0.0.1:39170/v1/extension/events", {
    method: "POST",
    headers: {
      "x-inquiry-pairing-token": overrides.token ?? token(),
      "content-type": "application/json",
      origin: overrides.origin ?? origin,
    },
    body: JSON.stringify(body),
  });
}

describe("desktop extension ingest", () => {
  test("accepts valid extension events and rejects invalid token or origin", async () => {
    const database = createInquiryDatabase();
    const sessions = createSessionController(database, {
      nowIso: () => "2026-07-07T12:00:00.000Z",
      nowMs: () => issuedAtMs,
    });
    const session = sessions.startSession({ title: "Fixture session", session_id: "session-ingest-1" });
    const handler = createIngestRequestHandler({
      allowedOrigins: [origin],
      database,
      pairingSecret: secret,
      sessions,
      nowMs: () => issuedAtMs,
    });

    const valid = await handler(
      eventRequest({
        event_type: "browser.scroll",
        monotonic_ms: 42,
        payload: { url_hash: "hash-1", scroll_y: 320, viewport_h: 900 },
      }),
    );

    expect(valid.status).toBe(202);
    expect(database.listEvents(session.session_id).map((event) => event.event_type)).toContain("browser.scroll");

    const invalidToken = await handler(
      eventRequest(
        {
          event_type: "browser.scroll",
          monotonic_ms: 43,
          payload: { url_hash: "hash-2", scroll_y: 500, viewport_h: 900 },
        },
        { token: "bad-token" },
      ),
    );
    const invalidOrigin = await handler(
      eventRequest(
        {
          event_type: "browser.scroll",
          monotonic_ms: 44,
          payload: { url_hash: "hash-3", scroll_y: 700, viewport_h: 900 },
        },
        { origin: "https://attacker.example" },
      ),
    );

    expect(invalidToken.status).toBe(401);
    expect(invalidOrigin.status).toBe(403);
    expect(database.listEvents(session.session_id).filter((event) => event.event_type === "browser.scroll")).toHaveLength(1);
    database.close();
  });

  test("accepts the extension bridge batch shape", async () => {
    const database = createInquiryDatabase();
    const sessions = createSessionController(database, {
      nowIso: () => "2026-07-07T12:05:00.000Z",
      nowMs: () => issuedAtMs,
    });
    const session = sessions.startSession({ title: "Batch fixture", session_id: "session-ingest-batch" });
    const handler = createIngestRequestHandler({
      allowedOrigins: [origin],
      database,
      pairingSecret: secret,
      sessions,
      nowMs: () => issuedAtMs,
    });
    const event = createEvent({
      event_id: "extension-event-1",
      captured_at: "2026-07-07T12:05:01.000Z",
      timezone: "UTC",
      session_id: session.session_id,
      source: "browser",
      source_version: "extension@0.1.0",
      monotonic_ms: 55,
      event_type: "browser.typing_metrics",
      payload: {
        field_role: "search",
        burst_length: 3,
        pause_ms: 180,
        backspace_count: 0,
        edit_churn: 0,
      },
      privacy_class: "local-derived",
      retention_policy: "local-default",
    });

    const response = await handler(
      extensionBatchRequest({
        session_id: session.session_id,
        source: "chrome-extension",
        events: [event],
      }),
    );
    const body = await response.json();

    expect(response.status).toBe(202);
    expect(body).toMatchObject({ accepted: 1, event_ids: ["extension-event-1"] });
    expect(database.listEvents(session.session_id).map((stored) => stored.event_id)).toContain("extension-event-1");
    database.close();
  });

  test("session controller starts, pauses, resumes, and stops visibly", () => {
    const database = createInquiryDatabase();
    const sessions = createSessionController(database, {
      nowIso: () => "2026-07-07T12:30:00.000Z",
      nowMs: () => 5_000,
    });

    const started = sessions.startSession({ title: "Lifecycle", session_id: "session-life-1" });
    expect(started.recording_state).toBe("recording");

    const paused = sessions.pauseSession({ reason: "break", monotonic_ms: 5_500 });
    expect(paused.recording_state).toBe("paused");
    expect(database.getSession(started.session_id)?.recording_state).toBe("paused");

    const resumed = sessions.resumeSession({ monotonic_ms: 6_000 });
    expect(resumed.recording_state).toBe("recording");

    const stopped = sessions.stopSession({ monotonic_ms: 7_000 });
    expect(stopped.recording_state).toBe("stopped");
    expect(stopped.ended_at).toBe("2026-07-07T12:30:00.000Z");
    expect(database.listEvents(started.session_id).map((event) => event.event_type)).toEqual([
      "session.started",
      "session.paused",
      "session.resumed",
      "session.stopped",
    ]);
    database.close();
  });

  test("global hotkey helper emits only label and pause style events", () => {
    const labelEvent = createGlobalHotkeyEvent({
      session_id: "session-hotkey-1",
      action: "label",
      label: "near-breakthrough",
      monotonic_ms: 80,
    });
    const pauseEvent = createGlobalHotkeyEvent({
      session_id: "session-hotkey-1",
      action: "pause",
      monotonic_ms: 81,
    });

    expect(labelEvent).toMatchObject({
      source: "desktop-hotkey",
      event_type: "label.added",
      payload: { label: "near-breakthrough" },
    });
    expect(pauseEvent.event_type).toBe("session.paused");
    expect(() =>
      createGlobalHotkeyEvent({
        session_id: "session-hotkey-1",
        action: "capture-key",
        key: "A",
        monotonic_ms: 82,
      }),
    ).toThrow(/unsupported global hotkey action/);
  });
});
