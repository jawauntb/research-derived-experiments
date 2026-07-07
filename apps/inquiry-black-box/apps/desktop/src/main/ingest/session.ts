import { createEvent, type EventEnvelope, type JsonObject, type SessionRecord } from "@inquiry/schema";
import type { InquiryDatabase } from "../db";

export type SessionClock = {
  nowIso: () => string;
  nowMs: () => number;
};

export type StartSessionInput = {
  title: string;
  active_task?: string;
  notes?: string;
  session_id?: string;
  monotonic_ms?: number;
};

export type SessionStateChangeInput = {
  reason?: string;
  monotonic_ms?: number;
};

export type SessionController = {
  startSession(input: StartSessionInput): SessionRecord;
  pauseSession(input?: SessionStateChangeInput): SessionRecord;
  resumeSession(input?: SessionStateChangeInput): SessionRecord;
  stopSession(input?: SessionStateChangeInput): SessionRecord;
  currentSession(): SessionRecord | null;
  canCapture(): boolean;
  appendActiveEvent(event: EventEnvelope): EventEnvelope;
};

const defaultClock: SessionClock = {
  nowIso: () => new Date().toISOString(),
  nowMs: () => Date.now(),
};

export function createSessionController(database: InquiryDatabase, clock: Partial<SessionClock> = {}): SessionController {
  const resolvedClock: SessionClock = { ...defaultClock, ...clock };
  let activeSessionId: string | null = null;

  function activeSession(): SessionRecord {
    if (!activeSessionId) {
      throw new Error("no active session");
    }

    const session = database.getSession(activeSessionId);
    if (!session) {
      activeSessionId = null;
      throw new Error("active session no longer exists");
    }

    return session;
  }

  function updateRecordingState(session: SessionRecord, state: SessionRecord["recording_state"]): SessionRecord {
    const updatedAt = resolvedClock.nowIso();
    database.db
      .query("UPDATE sessions SET recording_state = $state, updated_at = $updatedAt WHERE session_id = $sessionId")
      .run({ state, updatedAt, sessionId: session.session_id });

    return { ...session, recording_state: state, updated_at: updatedAt };
  }

  function appendSessionEvent(
    sessionId: string,
    eventType: "session.started" | "session.paused" | "session.resumed" | "session.stopped",
    input: SessionStateChangeInput | undefined,
    payload: JsonObject = {},
  ): EventEnvelope {
    const eventPayload: JsonObject = { ...payload };
    if (input?.reason !== undefined) {
      eventPayload.reason = input.reason;
    }

    return database.appendEvent(
      createEvent({
        session_id: sessionId,
        source: "desktop-system",
        source_version: "desktop@0.1.0",
        captured_at: resolvedClock.nowIso(),
        monotonic_ms: input?.monotonic_ms ?? resolvedClock.nowMs(),
        event_type: eventType,
        payload: eventPayload,
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );
  }

  return {
    startSession(input) {
      const current = activeSessionId ? database.getSession(activeSessionId) : null;
      if (current && current.recording_state !== "stopped") {
        throw new Error(`session already active: ${current.session_id}`);
      }

      const sessionInput: Parameters<InquiryDatabase["createSession"]>[0] = { title: input.title };
      if (input.active_task !== undefined) {
        sessionInput.active_task = input.active_task;
      }
      if (input.notes !== undefined) {
        sessionInput.notes = input.notes;
      }
      if (input.session_id !== undefined) {
        sessionInput.session_id = input.session_id;
      }

      const session = database.createSession(sessionInput);
      activeSessionId = session.session_id;
      appendSessionEvent(
        session.session_id,
        "session.started",
        { monotonic_ms: input.monotonic_ms ?? 0 },
        { title: session.title },
      );
      return session;
    },
    pauseSession(input = {}) {
      const session = activeSession();
      if (session.recording_state !== "recording") {
        throw new Error(`cannot pause session while ${session.recording_state}`);
      }

      const paused = updateRecordingState(session, "paused");
      appendSessionEvent(session.session_id, "session.paused", input);
      return paused;
    },
    resumeSession(input = {}) {
      const session = activeSession();
      if (session.recording_state !== "paused") {
        throw new Error(`cannot resume session while ${session.recording_state}`);
      }

      const resumed = updateRecordingState(session, "recording");
      appendSessionEvent(session.session_id, "session.resumed", input);
      return resumed;
    },
    stopSession(input = {}) {
      const session = activeSession();
      if (session.recording_state === "stopped") {
        throw new Error("session is already stopped");
      }

      appendSessionEvent(session.session_id, "session.stopped", input);
      const stopped = database.stopSession(session.session_id, resolvedClock.nowIso());
      activeSessionId = null;
      return stopped;
    },
    currentSession() {
      if (!activeSessionId) {
        return null;
      }

      return database.getSession(activeSessionId);
    },
    canCapture() {
      const current = activeSessionId ? database.getSession(activeSessionId) : null;
      return current?.recording_state === "recording";
    },
    appendActiveEvent(event) {
      const session = activeSession();
      if (session.recording_state !== "recording") {
        throw new Error(`cannot capture event while session is ${session.recording_state}`);
      }
      if (event.session_id !== session.session_id) {
        throw new Error("event session does not match active session");
      }

      return database.appendEvent(event);
    },
  };
}
