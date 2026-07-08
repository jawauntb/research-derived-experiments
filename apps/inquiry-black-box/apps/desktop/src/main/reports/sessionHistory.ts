import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { EventEnvelope } from "@inquiry/schema";
import type { SessionRecord } from "@inquiry/schema";
import { createSessionReplayReport, type SessionReplayReport } from "./sessionReplay";
import { createSessionInterpretationReport } from "./sessionInterpretation";
import type { InquiryDatabase } from "../db";

export type SessionHistoryEntry = {
  session_id: string;
  title: string;
  started_at: string;
  ended_at: string | null;
  recording_state: SessionRecord["recording_state"];
  duration_ms: number | null;
  top_markers: string[];
  verdict: string;
};

export function buildSessionHistoryEntry(database: InquiryDatabase, session: SessionRecord): SessionHistoryEntry {
  const events = database.listEvents(session.session_id);
  const replay = events.length > 0 ? createSessionReplayReport(events) : null;
  const interpretation =
    session.recording_state === "stopped" ? createSessionInterpretationReport(database, session.session_id) : null;

  const topMarkers = replay?.markers.slice(0, 3).map((marker) => marker.kind) ?? [];
  const verdict =
    interpretation?.summary ??
    replay?.next_actions[0] ??
    (session.recording_state === "stopped" ? "Stopped without replay evidence" : "Recording in progress");

  return {
    session_id: session.session_id,
    title: session.title,
    started_at: session.started_at,
    ended_at: session.ended_at ?? null,
    recording_state: session.recording_state,
    duration_ms: sessionDurationMs(session, events),
    top_markers: topMarkers,
    verdict,
  };
}

export function listSessionHistory(database: InquiryDatabase, limit = 12): SessionHistoryEntry[] {
  return database
    .listSessions()
    .slice()
    .reverse()
    .slice(0, limit)
    .map((session) => buildSessionHistoryEntry(database, session));
}

export function loadDemoReplayReport(): SessionReplayReport {
  const fixturePath = join(
    dirname(fileURLToPath(import.meta.url)),
    "../../../../../tests/fixtures/research-session.jsonl",
  );
  const lines = readFileSync(fixturePath, "utf8")
    .trim()
    .split("\n")
    .map((line) => JSON.parse(line) as { type: string; event?: EventEnvelope });
  const events = lines
    .filter((line) => line.type === "event" && line.event)
    .map((line) => line.event!);
  return createSessionReplayReport(events);
}

function sessionDurationMs(session: SessionRecord, events: { monotonic_ms: number }[]): number | null {
  if (events.length === 0) {
    if (session.ended_at) {
      return Math.max(0, Date.parse(session.ended_at) - Date.parse(session.started_at));
    }
    return null;
  }

  const span = Math.max(...events.map((event) => event.monotonic_ms)) - Math.min(...events.map((event) => event.monotonic_ms));
  return span > 0 ? span : null;
}
