import {
  createEvent,
  type EventEnvelope,
  type JsonObject,
  type ModelRunPayload,
  type ReportGeneratedPayload,
  type SuggestionCandidatePayload,
  type SuggestionRespondedPayload,
} from "@inquiry/schema";
import type { SessionInterpretation } from "./interpretation";

export type ArtifactEventOptions = {
  event_id?: string;
  source_version?: string;
  captured_at?: string;
  monotonic_ms?: number;
};

export function createReportGeneratedEvent(
  sessionId: string,
  payload: ReportGeneratedPayload,
  options: ArtifactEventOptions & { privacy_class?: "local-derived" | "redacted-sync"; source?: "desktop-system" | "cloud" | "modal" } = {},
): EventEnvelope<ReportGeneratedPayload> {
  return createEvent({
    event_id: options.event_id ?? `report-generated:${payload.report_id}`,
    session_id: sessionId,
    source: options.source ?? "desktop-system",
    source_version: options.source_version ?? "desktop@0.1.0",
    ...(options.captured_at === undefined ? {} : { captured_at: options.captured_at }),
    monotonic_ms: options.monotonic_ms ?? 0,
    event_type: "report.generated",
    payload,
    privacy_class: options.privacy_class ?? "local-derived",
    retention_policy: options.privacy_class === "redacted-sync" ? "cloud-redacted" : "local-default",
  });
}

export function createSuggestionCandidateEvent(
  sessionId: string,
  payload: SuggestionCandidatePayload,
  options: ArtifactEventOptions = {},
): EventEnvelope<SuggestionCandidatePayload> {
  return createEvent({
    event_id: options.event_id ?? `suggestion-candidate:${payload.suggestion_id}`,
    session_id: sessionId,
    source: "desktop-system",
    source_version: options.source_version ?? "desktop@0.1.0",
    ...(options.captured_at === undefined ? {} : { captured_at: options.captured_at }),
    monotonic_ms: options.monotonic_ms ?? 0,
    event_type: "suggestion.candidate",
    confidence: payload.confidence,
    payload,
    privacy_class: "local-derived",
    retention_policy: "local-default",
  });
}

export function createSuggestionResponseEvent(
  sessionId: string,
  payload: SuggestionRespondedPayload,
  options: ArtifactEventOptions = {},
): EventEnvelope<SuggestionRespondedPayload> {
  return createEvent({
    event_id: options.event_id ?? `suggestion-response:${payload.suggestion_id}:${payload.response}:${stableKey(payload.responded_at)}`,
    session_id: sessionId,
    source: "user",
    source_version: options.source_version ?? "desktop@0.1.0",
    ...(options.captured_at === undefined ? {} : { captured_at: options.captured_at }),
    monotonic_ms: options.monotonic_ms ?? Date.now(),
    event_type: "suggestion.responded",
    payload,
    privacy_class: "local-derived",
    retention_policy: "local-default",
  });
}

export function createModelRunEvent(
  sessionId: string,
  payload: ModelRunPayload,
  options: ArtifactEventOptions & { source?: "desktop-system" | "cloud" | "modal" } = {},
): EventEnvelope<ModelRunPayload> {
  return createEvent({
    event_id: options.event_id ?? `model-run:${payload.run_id}`,
    session_id: sessionId,
    source: options.source ?? "modal",
    source_version: options.source_version ?? "modal@0.1.0",
    ...(options.captured_at === undefined ? {} : { captured_at: options.captured_at }),
    monotonic_ms: options.monotonic_ms ?? 0,
    event_type: "model.run",
    payload,
    privacy_class: "redacted-sync",
    retention_policy: "cloud-redacted",
  });
}

export function redactedSessionSummaryJobInput(interpretation: SessionInterpretation): JsonObject {
  return {
    privacy_class: "redacted-sync",
    payload: {
      report_id: interpretation.report_id,
      report_kind: "session_interpretation",
      subject_session_id: interpretation.session_id,
      marker_count: Number(interpretation.provenance.marker_count ?? 0),
      theme_count: interpretation.themes.length,
      open_loop_count: interpretation.open_loops.length,
      next_action_count: interpretation.next_actions.length,
      summary: `Redacted local session summary with ${interpretation.themes.length} theme(s), ${interpretation.open_loops.length} open loop(s), and ${interpretation.next_actions.length} next action(s).`,
      themes: interpretation.themes.map((theme) => ({
        kind: theme.kind,
        title: theme.title,
        confidence: theme.confidence,
        marker_count: theme.marker_ids.length,
        evidence_count: theme.evidence_event_ids.length,
      })),
      next_actions: interpretation.next_actions.map((suggestion) => ({
        suggestion_kind: suggestion.suggestion_kind,
        category: suggestion.category,
        title: suggestion.title,
        confidence: suggestion.confidence,
        evidence_count: suggestion.evidence_event_ids.length,
      })),
      limitations: interpretation.limitations,
      provenance: {
        input_report_id: interpretation.report_id,
        builder: "redacted-session-summary-input@0.1.0",
        excludes: [
          "raw typed text",
          "raw selected text",
          "raw page text",
          "screenshots",
          "OCR text",
          "desktop event objects",
          "app names",
          "window titles",
        ],
      },
    },
  };
}

function stableKey(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 80);
}
