import type { EventEnvelope, SuggestionCandidatePayload, SuggestionRespondedPayload } from "@inquiry/schema";
import {
  buildDailyReview,
  createReportGeneratedEvent,
  createSuggestionCandidateEvent,
  createSuggestionResponseEvent,
  dailyReviewReportPayload,
  localDateKey,
  type DailyReview,
  type SessionInterpretation,
} from "@inquiry/signals";
import type { InquiryDatabase } from "../db";
import { createSessionInterpretationReport } from "./sessionInterpretation";

export type DailyReviewReport = DailyReview;

export type SuggestionResponseInput = {
  suggestion_id: string;
  response: SuggestionRespondedPayload["response"];
  reason?: string;
  snoozed_until?: string;
  local_date?: string;
};

export function createDailyReviewReport(
  database: InquiryDatabase,
  options: { local_date?: string; timezone?: string; generated_at?: string } = {},
): DailyReviewReport {
  const generatedAt = options.generated_at ?? new Date().toISOString();
  const timezone = options.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone;
  const localDate = options.local_date ?? localDateKey(generatedAt, timezone);
  const sessions = database.listSessions().filter((session) =>
    [session.started_at, session.ended_at ?? session.updated_at].some((date) => localDateKey(date, timezone) === localDate),
  );
  const interpretations: SessionInterpretation[] = sessions.map((session) =>
    createSessionInterpretationReport(database, session.session_id),
  );
  const suggestionCandidates = listSuggestionCandidates(database);
  const suggestionResponses = listSuggestionResponses(database);
  const review = buildDailyReview({
    interpretations,
    suggestion_candidates: suggestionCandidates,
    suggestion_responses: suggestionResponses,
    local_date: localDate,
    timezone,
    generated_at: generatedAt,
  });
  const anchorSession = sessions[0] ?? null;
  if (!anchorSession) {
    return review;
  }

  const monotonicBase = lastMonotonicMs(database.listEvents(anchorSession.session_id)) + 10;
  const reportEvent = createReportGeneratedEvent(anchorSession.session_id, dailyReviewReportPayload(review), {
    event_id: `report-generated:${review.report_id}`,
    captured_at: review.generated_at,
    monotonic_ms: monotonicBase,
  });
  database.appendEventIfNew(reportEvent);

  const suggestionEvents = review.suggestions.map((suggestion, index) =>
    createSuggestionCandidateEvent(anchorSession.session_id, suggestion, {
      event_id: `suggestion-candidate:${suggestion.suggestion_id}`,
      captured_at: review.generated_at,
      monotonic_ms: monotonicBase + index + 1,
    }),
  );
  for (const event of suggestionEvents) {
    database.appendEventIfNew(event);
  }

  return review;
}

export function recordSuggestionResponse(
  database: InquiryDatabase,
  input: SuggestionResponseInput,
): EventEnvelope<SuggestionRespondedPayload> {
  const review = createDailyReviewReport(database, input.local_date ? { local_date: input.local_date } : {});
  const suggestion = review.suggestions.find((candidate) => candidate.suggestion_id === input.suggestion_id);
  if (!suggestion) {
    throw new Error(`suggestion not found: ${input.suggestion_id}`);
  }

  const sessionId = suggestion.session_ids[0] ?? database.listSessions()[0]?.session_id;
  if (!sessionId) {
    throw new Error("no session available for suggestion response");
  }

  const respondedAt = new Date().toISOString();
  const payload: SuggestionRespondedPayload = {
    suggestion_id: input.suggestion_id,
    response: input.response,
    responded_at: respondedAt,
    ...(review.report_id ? { source_report_id: review.report_id } : {}),
    ...(input.reason ? { reason: input.reason } : {}),
    ...(input.snoozed_until ? { snoozed_until: input.snoozed_until } : {}),
  };
  const event = createSuggestionResponseEvent(sessionId, payload, {
    captured_at: respondedAt,
    monotonic_ms: lastMonotonicMs(database.listEvents(sessionId)) + 1,
  });
  database.appendEvent(event);
  return event;
}

function listSuggestionCandidates(database: InquiryDatabase): SuggestionCandidatePayload[] {
  return database
    .listSessions()
    .flatMap((session) => database.listEvents(session.session_id))
    .filter((event): event is EventEnvelope<SuggestionCandidatePayload> => event.event_type === "suggestion.candidate")
    .map((event) => event.payload);
}

function listSuggestionResponses(database: InquiryDatabase): SuggestionRespondedPayload[] {
  return database
    .listSessions()
    .flatMap((session) => database.listEvents(session.session_id))
    .filter((event): event is EventEnvelope<SuggestionRespondedPayload> => event.event_type === "suggestion.responded")
    .map((event) => event.payload);
}

function lastMonotonicMs(events: EventEnvelope[]): number {
  return events.reduce((max, event) => Math.max(max, event.monotonic_ms), 0);
}
