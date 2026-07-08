import type { EventEnvelope, JsonObject, ReportGeneratedPayload, SuggestionCandidatePayload } from "@inquiry/schema";
import type { RepairCandidate } from "./repairs";
import type { ReplayMarker, ReplayMemo } from "./heuristics";

export type SessionInterpretationTheme = JsonObject & {
  theme_id: string;
  title: string;
  detail: string;
  kind: "helped" | "fragmented" | "open-loop" | "retry" | "local-context";
  confidence: number;
  marker_ids: string[];
  evidence_event_ids: string[];
  limitation: string;
};

export type SessionOpenLoop = JsonObject & {
  loop_id: string;
  title: string;
  action: string;
  evidence_event_ids: string[];
  marker_ids: string[];
  confidence: number;
};

export type SessionInterpretation = JsonObject & {
  report_id: string;
  report_kind: "session_interpretation";
  session_id: string;
  generated_at: string;
  summary: string;
  confidence: number;
  themes: SessionInterpretationTheme[];
  next_actions: SuggestionCandidatePayload[];
  open_loops: SessionOpenLoop[];
  limitations: string[];
  evidence_event_ids: string[];
  source_report_ids: string[];
  provenance: JsonObject;
};

export type BuildSessionInterpretationInput = {
  replay: ReplayMemo & {
    report_id?: string;
    generated_at?: string;
    limitations?: string[];
    repair_candidates?: RepairCandidate[];
  };
  events?: EventEnvelope[];
  session?: {
    title?: string;
    active_task?: string;
    started_at?: string;
    ended_at?: string;
  };
  generated_at?: string;
};

const markerPriority: Record<ReplayMarker["kind"], number> = {
  "stuck-loop": 0,
  "copied-passage": 1,
  "tab-churn": 2,
  "app-churn": 3,
  "deep-work-span": 4,
  "off-browser-focus": 5,
  "skim-risk": 6,
  "high-load": 7,
  rewind: 8,
  label: 9,
  probe: 10,
};

export function buildSessionInterpretation(input: BuildSessionInterpretationInput): SessionInterpretation {
  const replay = input.replay;
  const generatedAt = input.generated_at ?? new Date().toISOString();
  const reportId = sessionInterpretationReportId(replay.session_id);
  const sortedMarkers = [...replay.markers].sort(
    (a, b) => markerPriority[a.kind] - markerPriority[b.kind] || b.confidence - a.confidence || a.start_ms - b.start_ms,
  );
  const events = input.events ?? [];
  const repairOutcomes = events.filter((event) => event.event_type === "repair.outcome");
  const acceptedRepairIds = new Set(
    repairOutcomes
      .filter((event) => event.payload.outcome === "accepted" || event.payload.outcome === "answered" || event.payload.outcome === "rated-useful")
      .map((event) => String(event.payload.repair_id ?? "")),
  );
  const dismissedRepairIds = new Set(
    repairOutcomes
      .filter((event) => event.payload.outcome === "dismissed" || event.payload.outcome === "rated-not-useful")
      .map((event) => String(event.payload.repair_id ?? "")),
  );

  const themes = sortedMarkers.slice(0, 5).map((marker) => themeForMarker(marker));
  themes.push(...repairOutcomeThemes(replay.repair_candidates ?? [], acceptedRepairIds, dismissedRepairIds));

  const evidenceEventIds = unique([
    ...themes.flatMap((theme) => theme.evidence_event_ids),
    ...sortedMarkers.flatMap((marker) => marker.evidence_event_ids),
  ]);
  const sourceReportIds = replay.report_id ? [replay.report_id] : [];
  const nextActions = buildInterpretationSuggestions({
    reportId,
    sessionId: replay.session_id,
    markers: sortedMarkers,
    themes,
  });
  const openLoops = buildOpenLoops(sortedMarkers);
  const limitations = unique([
    ...(replay.limitations ?? []),
    "Session interpretation is local deterministic guidance, not a diagnosis or hidden mental-state claim.",
    "Evidence uses marker kinds, timings, counts, labels, and outcomes; raw typed text, screenshots, OCR, and raw selected text are not required.",
    ...(hasDesktopMarkers(sortedMarkers)
      ? ["Desktop app context can appear locally when desktop activity is enabled, but it is marked local-only and excluded from redacted LLM payloads."]
      : []),
  ]);
  const confidence = sortedMarkers.length === 0 ? 0.25 : clamp(average(sortedMarkers.map((marker) => marker.confidence)), 0.35, 0.86);

  return {
    report_id: reportId,
    report_kind: "session_interpretation",
    session_id: replay.session_id,
    generated_at: generatedAt,
    summary: summaryFor({
      markers: sortedMarkers,
      openLoops,
      ...(input.session?.title ? { sessionTitle: input.session.title } : {}),
    }),
    confidence,
    themes,
    next_actions: nextActions,
    open_loops: openLoops,
    limitations,
    evidence_event_ids: evidenceEventIds,
    source_report_ids: sourceReportIds,
    provenance: {
      builder: "local-session-interpretation@0.1.0",
      replay_report_id: replay.report_id ?? null,
      marker_count: sortedMarkers.length,
      repair_outcome_count: repairOutcomes.length,
    },
  };
}

export function sessionInterpretationReportId(sessionId: string): string {
  return `session-interpretation:${sessionId}`;
}

export function sessionInterpretationReportPayload(interpretation: SessionInterpretation): ReportGeneratedPayload {
  return {
    report_id: interpretation.report_id,
    report_kind: "session_interpretation",
    subject_session_id: interpretation.session_id,
    summary: interpretation.summary,
    generated_at: interpretation.generated_at,
    evidence_event_ids: interpretation.evidence_event_ids,
    source_report_ids: interpretation.source_report_ids,
    suggestion_ids: interpretation.next_actions.map((suggestion) => suggestion.suggestion_id),
    limitations: interpretation.limitations,
    provenance: interpretation.provenance,
  };
}

function buildInterpretationSuggestions(input: {
  reportId: string;
  sessionId: string;
  markers: ReplayMarker[];
  themes: SessionInterpretationTheme[];
}): SuggestionCandidatePayload[] {
  const candidates = input.markers
    .filter((marker) => marker.confidence >= 0.55)
    .map((marker) => suggestionForMarker(marker, input.reportId, input.sessionId));
  if (candidates.length > 0) {
    return dedupeSuggestions(candidates).slice(0, 3);
  }

  return [
    {
      suggestion_id: `suggestion:${input.sessionId}:collect-more-evidence`,
      suggestion_kind: "daily-checkup",
      category: "retry",
      title: "Collect more session evidence",
      action: "Run one explicit session with a clear title, then stop and review the replay.",
      rationale: "This session did not yet have enough evidence-linked markers to recommend a stronger action.",
      confidence: 0.35,
      evidence_event_ids: [],
      report_ids: [input.reportId],
      session_ids: [input.sessionId],
      limitation: "Low-confidence reminder; it should be confirmed by future session evidence.",
      pattern_key: "collect-more-evidence",
    },
  ];
}

function suggestionForMarker(marker: ReplayMarker, reportId: string, sessionId: string): SuggestionCandidatePayload {
  const category = categoryForMarker(marker);
  const suggestionKind = suggestionKindForMarker(marker);
  return {
    suggestion_id: `suggestion:${sessionId}:${stableKey(marker.kind)}:${stableKey(marker.marker_id)}`,
    suggestion_kind: suggestionKind,
    category,
    title: titleForMarker(marker),
    action: marker.suggested_action,
    rationale: marker.evidence.join(" "),
    confidence: marker.confidence,
    evidence_event_ids: marker.evidence_event_ids,
    report_ids: [reportId],
    session_ids: [sessionId],
    limitation: "This suggestion is derived from local replay markers and needs user feedback before it becomes a preference.",
    pattern_key: `${marker.kind}:${stableKey(marker.suggested_action)}`,
  };
}

function buildOpenLoops(markers: ReplayMarker[]): SessionOpenLoop[] {
  return markers
    .filter((marker) => marker.kind === "copied-passage" || marker.kind === "tab-churn" || marker.kind === "app-churn" || marker.kind === "off-browser-focus")
    .slice(0, 4)
    .map((marker) => ({
      loop_id: `open-loop:${stableKey(marker.marker_id)}`,
      title: titleForMarker(marker),
      action: marker.suggested_action,
      evidence_event_ids: marker.evidence_event_ids,
      marker_ids: [marker.marker_id],
      confidence: marker.confidence,
    }));
}

function themeForMarker(marker: ReplayMarker): SessionInterpretationTheme {
  return {
    theme_id: `theme:${stableKey(marker.marker_id)}`,
    title: titleForMarker(marker),
    detail: detailForMarker(marker),
    kind: themeKindForMarker(marker),
    confidence: marker.confidence,
    marker_ids: [marker.marker_id],
    evidence_event_ids: marker.evidence_event_ids,
    limitation: "A theme summarizes local marker evidence; it is not a settled claim about attention or intent.",
  };
}

function repairOutcomeThemes(
  candidates: RepairCandidate[],
  acceptedRepairIds: Set<string>,
  dismissedRepairIds: Set<string>,
): SessionInterpretationTheme[] {
  const themes: SessionInterpretationTheme[] = [];
  for (const candidate of candidates) {
    if (acceptedRepairIds.has(candidate.repair_id)) {
      themes.push({
        theme_id: `theme:repair-helped:${stableKey(candidate.repair_id)}`,
        title: "Repair action helped",
        detail: `A ${candidate.action} repair was accepted or answered, so similar evidence can be retried when it recurs.`,
        kind: "helped",
        confidence: candidate.confidence,
        marker_ids: candidate.source_marker_ids,
        evidence_event_ids: candidate.evidence_event_ids,
        limitation: candidate.limitation,
      });
    }
    if (dismissedRepairIds.has(candidate.repair_id)) {
      themes.push({
        theme_id: `theme:repair-dismissed:${stableKey(candidate.repair_id)}`,
        title: "Dismissed repair should be deprioritized",
        detail: `A ${candidate.action} repair was dismissed or rated not useful, so the next review should avoid repeating it without new evidence.`,
        kind: "retry",
        confidence: Math.max(0.4, candidate.confidence - 0.15),
        marker_ids: candidate.source_marker_ids,
        evidence_event_ids: candidate.evidence_event_ids,
        limitation: candidate.limitation,
      });
    }
  }
  return themes;
}

function summaryFor(input: { markers: ReplayMarker[]; sessionTitle?: string; openLoops: SessionOpenLoop[] }): string {
  if (input.markers.length === 0) {
    return "Evidence is still sparse. Run an explicit session and review again before treating any suggestion as useful.";
  }

  const title = input.sessionTitle ? `${input.sessionTitle}: ` : "";
  const kinds = unique(input.markers.slice(0, 3).map((marker) => marker.kind.replaceAll("-", " ")));
  const openLoopCopy = input.openLoops.length > 0 ? ` ${input.openLoops.length} open loop candidate(s) need confirmation.` : "";
  return `${title}Evidence suggests ${kinds.join(", ")} shaped this session.${openLoopCopy}`;
}

function titleForMarker(marker: ReplayMarker): string {
  switch (marker.kind) {
    case "copied-passage":
      return "Copied evidence needs an explanation";
    case "skim-risk":
      return "Fast skim risk";
    case "stuck-loop":
      return "Possible stuck loop";
    case "high-load":
      return "High-load moment";
    case "tab-churn":
      return "Tab branch fragmentation";
    case "app-churn":
      return "App branch fragmentation";
    case "deep-work-span":
      return "Deep work block";
    case "off-browser-focus":
      return "Desktop branch to name";
    case "rewind":
      return "Replay or reread cue";
    case "label":
      return "Self-label evidence";
    case "probe":
      return "Recall probe evidence";
  }
}

function detailForMarker(marker: ReplayMarker): string {
  return `${marker.evidence.join(" ")} Try next: ${marker.suggested_action}`;
}

function themeKindForMarker(marker: ReplayMarker): SessionInterpretationTheme["kind"] {
  if (marker.kind === "deep-work-span" || marker.kind === "probe" || marker.kind === "label") {
    return "helped";
  }
  if (marker.kind === "copied-passage" || marker.kind === "tab-churn" || marker.kind === "app-churn" || marker.kind === "off-browser-focus") {
    return "open-loop";
  }
  if (marker.kind === "skim-risk" || marker.kind === "stuck-loop" || marker.kind === "high-load") {
    return "retry";
  }
  return "fragmented";
}

function categoryForMarker(marker: ReplayMarker): SuggestionCandidatePayload["category"] {
  if (marker.kind === "deep-work-span" || marker.kind === "probe" || marker.kind === "label") {
    return "helped";
  }
  if (marker.kind === "copied-passage" || marker.kind === "off-browser-focus") {
    return "open_loops";
  }
  if (marker.kind === "tab-churn" || marker.kind === "app-churn") {
    return "fragmented";
  }
  return "retry";
}

function suggestionKindForMarker(marker: ReplayMarker): SuggestionCandidatePayload["suggestion_kind"] {
  if (marker.kind === "copied-passage" || marker.kind === "off-browser-focus" || marker.kind === "tab-churn" || marker.kind === "app-churn") {
    return "open-loop";
  }
  if (marker.kind === "deep-work-span" || marker.kind === "label" || marker.kind === "probe") {
    return "care-candidate";
  }
  return "retry";
}

function hasDesktopMarkers(markers: ReplayMarker[]): boolean {
  return markers.some((marker) => marker.kind === "app-churn" || marker.kind === "deep-work-span" || marker.kind === "off-browser-focus");
}

function dedupeSuggestions(suggestions: SuggestionCandidatePayload[]): SuggestionCandidatePayload[] {
  const seen = new Set<string>();
  const deduped: SuggestionCandidatePayload[] = [];
  for (const suggestion of suggestions) {
    const key = suggestion.pattern_key ?? suggestion.suggestion_id;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    deduped.push(suggestion);
  }
  return deduped;
}

function stableKey(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 80);
}

function unique(values: string[]): string[] {
  return [...new Set(values.filter((value) => value.length > 0))];
}

function average(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}
