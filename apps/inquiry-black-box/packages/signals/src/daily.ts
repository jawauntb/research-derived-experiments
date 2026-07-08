import type {
  JsonObject,
  ReportGeneratedPayload,
  SuggestionCandidatePayload,
  SuggestionRespondedPayload,
} from "@inquiry/schema";
import type { SessionInterpretation } from "./interpretation";

export type DailyReviewSections = JsonObject & {
  helped: SuggestionCandidatePayload[];
  fragmented: SuggestionCandidatePayload[];
  retry: SuggestionCandidatePayload[];
  ignore: SuggestionCandidatePayload[];
  open_loops: SuggestionCandidatePayload[];
  care_candidates: SuggestionCandidatePayload[];
};

export type DailyReview = JsonObject & {
  report_id: string;
  report_kind: "daily_review";
  local_date: string;
  generated_at: string;
  summary: string;
  sections: DailyReviewSections;
  suggestions: SuggestionCandidatePayload[];
  limitations: string[];
  evidence_event_ids: string[];
  source_report_ids: string[];
  provenance: JsonObject;
};

export type BuildDailyReviewInput = {
  interpretations: SessionInterpretation[];
  suggestion_candidates?: SuggestionCandidatePayload[];
  suggestion_responses?: SuggestionRespondedPayload[];
  local_date?: string;
  timezone?: string;
  generated_at?: string;
};

type ResponseStats = {
  accepted: number;
  useful: number;
  dismissed: number;
  notUseful: number;
  snoozed: number;
  confirmedCare: number;
  rejectedCare: number;
};

const emptyStats: ResponseStats = {
  accepted: 0,
  useful: 0,
  dismissed: 0,
  notUseful: 0,
  snoozed: 0,
  confirmedCare: 0,
  rejectedCare: 0,
};

const dailyReviewSectionKeys = ["helped", "fragmented", "retry", "ignore", "open_loops", "care_candidates"] as const;

export function buildDailyReview(input: BuildDailyReviewInput): DailyReview {
  const generatedAt = input.generated_at ?? new Date().toISOString();
  const timezone = input.timezone ?? "UTC";
  const localDate = input.local_date ?? localDateKey(generatedAt, timezone);
  const interpretations = input.interpretations.filter(
    (interpretation) => localDateKey(interpretation.generated_at, timezone) === localDate,
  );
  const priorSuggestions = input.suggestion_candidates ?? [];
  const responses = input.suggestion_responses ?? [];
  const reportId = dailyReviewReportId(localDate);

  if (interpretations.length === 0) {
    return {
      report_id: reportId,
      report_kind: "daily_review",
      local_date: localDate,
      generated_at: generatedAt,
      summary: "No explicit Inquiry sessions were available for this local day.",
      sections: emptySections(),
      suggestions: [],
      limitations: ["Daily review needs at least one session interpretation before it can suggest useful next actions."],
      evidence_event_ids: [],
      source_report_ids: [],
      provenance: {
        builder: "local-daily-review@0.1.0",
        timezone,
        interpretation_count: 0,
        response_count: responses.length,
      },
    };
  }

  const baseSuggestions = interpretations.flatMap((interpretation) =>
    interpretation.next_actions.map((suggestion) => ({
      ...suggestion,
      local_date: localDate,
      report_ids: unique([...suggestion.report_ids, interpretation.report_id]),
      session_ids: unique([...suggestion.session_ids, interpretation.session_id]),
    })),
  );
  const currentSessionIds = new Set(interpretations.map((interpretation) => interpretation.session_id));
  const currentPatternKeys = new Set(baseSuggestions.map(patternKey));
  const currentPriorSuggestions = priorSuggestions.filter(
    (suggestion) =>
      suggestion.local_date === localDate ||
      suggestion.session_ids.some((sessionId) => currentSessionIds.has(sessionId)) ||
      currentPatternKeys.has(patternKey(suggestion)),
  );
  const candidates = dedupeByPattern([...baseSuggestions, ...currentPriorSuggestions]);
  const statsByPattern = responseStatsByPattern([...baseSuggestions, ...priorSuggestions], responses);
  const ranked = candidates
    .map((candidate) => applyFeedback(candidate, statsByPattern.get(patternKey(candidate)) ?? emptyStats, localDate))
    .sort((a, b) => b.confidence - a.confidence || a.title.localeCompare(b.title));
  const sections = emptySections();

  for (const suggestion of ranked) {
    sections[suggestion.category].push(suggestion);
  }

  addCareCandidates(sections, ranked, statsByPattern, localDate, reportId);

  for (const key of dailyReviewSectionKeys) {
    sections[key] = sections[key].slice(0, 4);
  }

  const suggestions = [
    ...sections.helped,
    ...sections.fragmented,
    ...sections.retry,
    ...sections.ignore,
    ...sections.open_loops,
    ...sections.care_candidates,
  ];

  return {
    report_id: reportId,
    report_kind: "daily_review",
    local_date: localDate,
    generated_at: generatedAt,
    summary: summaryFor(sections, interpretations.length),
    sections,
    suggestions,
    limitations: [
      "Daily suggestions are deterministic local summaries of session evidence and explicit feedback.",
      "Care candidates require confirmation before they are treated as durable preferences.",
      "Dismissed or rated-not-useful suggestions are deprioritized, not silently deleted.",
    ],
    evidence_event_ids: unique(suggestions.flatMap((suggestion) => suggestion.evidence_event_ids)),
    source_report_ids: unique([
      ...interpretations.map((interpretation) => interpretation.report_id),
      ...suggestions.flatMap((suggestion) => suggestion.report_ids),
    ]),
    provenance: {
      builder: "local-daily-review@0.1.0",
      timezone,
      interpretation_count: interpretations.length,
      response_count: responses.length,
      suggestion_count: suggestions.length,
    },
  };
}

export function dailyReviewReportId(localDate: string): string {
  return `daily-review:${localDate}`;
}

export function dailyReviewReportPayload(review: DailyReview): ReportGeneratedPayload {
  return {
    report_id: review.report_id,
    report_kind: "daily_review",
    local_date: review.local_date,
    summary: review.summary,
    generated_at: review.generated_at,
    evidence_event_ids: review.evidence_event_ids,
    source_report_ids: review.source_report_ids,
    suggestion_ids: review.suggestions.map((suggestion) => suggestion.suggestion_id),
    limitations: review.limitations,
    provenance: review.provenance,
  };
}

export function localDateKey(isoDate: string, timezone = "UTC"): string {
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  return formatter.format(new Date(isoDate));
}

function emptySections(): DailyReviewSections {
  return {
    helped: [],
    fragmented: [],
    retry: [],
    ignore: [],
    open_loops: [],
    care_candidates: [],
  };
}

function applyFeedback(
  candidate: SuggestionCandidatePayload,
  stats: ResponseStats,
  localDate: string,
): SuggestionCandidatePayload {
  const negativeCount = stats.dismissed + stats.notUseful + stats.rejectedCare;
  const positiveCount = stats.accepted + stats.useful + stats.confirmedCare;
  if (negativeCount >= 2) {
    return {
      ...candidate,
      suggestion_id: dailySuggestionId(localDate, candidate, "ignore"),
      suggestion_kind: "ignore",
      category: "ignore",
      confidence: Math.max(0.35, candidate.confidence - 0.22),
      rationale: `${candidate.rationale} Prior feedback dismissed or rated this pattern not useful ${negativeCount} time(s).`,
      limitation: "Ignored patterns can return only when new evidence recurs or the user changes feedback.",
    };
  }

  if (positiveCount > 0) {
    return {
      ...candidate,
      suggestion_id: dailySuggestionId(localDate, candidate, candidate.category),
      confidence: Math.min(0.92, candidate.confidence + Math.min(0.16, positiveCount * 0.08)),
      rationale: `${candidate.rationale} Prior feedback marked a similar suggestion useful ${positiveCount} time(s).`,
    };
  }

  return {
    ...candidate,
    suggestion_id: dailySuggestionId(localDate, candidate, candidate.category),
  };
}

function addCareCandidates(
  sections: DailyReviewSections,
  ranked: SuggestionCandidatePayload[],
  statsByPattern: Map<string, ResponseStats>,
  localDate: string,
  reportId: string,
): void {
  const recurring = ranked.filter((suggestion) => {
    const stats = statsByPattern.get(patternKey(suggestion)) ?? emptyStats;
    return (
      suggestion.suggestion_kind === "care-candidate" ||
      stats.accepted + stats.useful + stats.confirmedCare > 0 ||
      suggestion.session_ids.length > 1
    );
  });

  for (const suggestion of recurring.slice(0, 3)) {
    const careCandidate: SuggestionCandidatePayload = {
      ...suggestion,
      suggestion_id: dailySuggestionId(localDate, suggestion, "care_candidates"),
      suggestion_kind: "care-candidate",
      category: "care_candidates",
      title: `Confirm care candidate: ${suggestion.title}`,
      action: "Confirm whether this pattern matters before Inquiry treats it as a preference.",
      rationale: `${suggestion.rationale} This is a candidate because it recurred or received useful feedback.`,
      report_ids: unique([...suggestion.report_ids, reportId]),
      limitation: "This is not a settled claim about what you care about; it needs explicit confirmation.",
    };
    sections.care_candidates.push(careCandidate);
  }
}

function responseStatsByPattern(
  suggestions: SuggestionCandidatePayload[],
  responses: SuggestionRespondedPayload[],
): Map<string, ResponseStats> {
  const suggestionToPattern = new Map(suggestions.map((suggestion) => [suggestion.suggestion_id, patternKey(suggestion)]));
  const map = new Map<string, ResponseStats>();
  for (const response of responses) {
    const pattern = suggestionToPattern.get(response.suggestion_id);
    if (!pattern) {
      continue;
    }
    const current = { ...(map.get(pattern) ?? emptyStats) };
    if (response.response === "accepted") current.accepted += 1;
    if (response.response === "rated-useful") current.useful += 1;
    if (response.response === "dismissed") current.dismissed += 1;
    if (response.response === "rated-not-useful") current.notUseful += 1;
    if (response.response === "snoozed") current.snoozed += 1;
    if (response.response === "confirmed-care") current.confirmedCare += 1;
    if (response.response === "rejected-care") current.rejectedCare += 1;
    map.set(pattern, current);
  }
  return map;
}

function dedupeByPattern(suggestions: SuggestionCandidatePayload[]): SuggestionCandidatePayload[] {
  const merged = new Map<string, SuggestionCandidatePayload>();
  for (const suggestion of suggestions) {
    const key = patternKey(suggestion);
    const existing = merged.get(key);
    if (!existing) {
      merged.set(key, suggestion);
      continue;
    }
    merged.set(key, {
      ...existing,
      confidence: Math.max(existing.confidence, suggestion.confidence),
      evidence_event_ids: unique([...existing.evidence_event_ids, ...suggestion.evidence_event_ids]),
      report_ids: unique([...existing.report_ids, ...suggestion.report_ids]),
      session_ids: unique([...existing.session_ids, ...suggestion.session_ids]),
    });
  }
  return [...merged.values()];
}

function dailySuggestionId(localDate: string, suggestion: SuggestionCandidatePayload, category: string): string {
  return `daily-suggestion:${localDate}:${category}:${stableKey(patternKey(suggestion))}`;
}

function patternKey(suggestion: SuggestionCandidatePayload): string {
  return suggestion.pattern_key ?? `${suggestion.suggestion_kind}:${stableKey(suggestion.title)}:${stableKey(suggestion.action)}`;
}

function summaryFor(sections: DailyReviewSections, interpretationCount: number): string {
  const counts = [
    `${interpretationCount} session interpretation(s)`,
    `${sections.retry.length} retry`,
    `${sections.open_loops.length} open loop`,
    `${sections.ignore.length} ignored pattern`,
    `${sections.care_candidates.length} care candidate`,
  ];
  return `Daily review built from ${counts.join(", ")}.`;
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
