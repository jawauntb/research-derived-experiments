import type { EventEnvelope } from "@inquiry/schema";
import {
  buildSessionInterpretation,
  createReportGeneratedEvent,
  createSuggestionCandidateEvent,
  sessionInterpretationReportPayload,
  type SessionInterpretation,
} from "@inquiry/signals";
import type { InquiryDatabase } from "../db";
import { createSessionReplayReport } from "./sessionReplay";

export type SessionInterpretationReport = SessionInterpretation;

export function createSessionInterpretationReport(
  database: InquiryDatabase,
  sessionId: string,
): SessionInterpretationReport {
  const session = database.getSession(sessionId);
  if (!session) {
    throw new Error(`session not found: ${sessionId}`);
  }

  const events = database.listEvents(sessionId);
  const replay = createSessionReplayReport(events);
  const interpretation = buildSessionInterpretation({
    replay,
    events,
    session,
    generated_at: session.ended_at ?? new Date().toISOString(),
  });
  const reportEvent = createReportGeneratedEvent(
    sessionId,
    sessionInterpretationReportPayload(interpretation),
    {
      event_id: `report-generated:${interpretation.report_id}`,
      captured_at: interpretation.generated_at,
      monotonic_ms: lastMonotonicMs(events),
    },
  );
  database.appendEventIfNew(reportEvent);

  const suggestionEvents = interpretation.next_actions.map((suggestion, index) =>
    createSuggestionCandidateEvent(sessionId, suggestion, {
      event_id: `suggestion-candidate:${suggestion.suggestion_id}`,
      captured_at: interpretation.generated_at,
      monotonic_ms: lastMonotonicMs(events) + index + 1,
    }),
  );
  for (const event of suggestionEvents) {
    database.appendEventIfNew(event);
  }

  return interpretation;
}

function lastMonotonicMs(events: EventEnvelope[]): number {
  return events.reduce((max, event) => Math.max(max, event.monotonic_ms), 0);
}
