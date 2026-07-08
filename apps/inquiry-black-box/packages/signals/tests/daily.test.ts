import { describe, expect, test } from "bun:test";
import {
  buildDailyReview,
  dailyReviewReportPayload,
  type SessionInterpretation,
} from "../src";

describe("daily review", () => {
  test("aggregates session interpretations into the six daily sections", () => {
    const first = interpretation("session-a", "2026-07-08T14:00:00.000Z", "retry", "skim-risk:recall");
    const second = interpretation("session-b", "2026-07-08T20:00:00.000Z", "open_loops", "copied-passage:explain");

    const review = buildDailyReview({
      interpretations: [first, second],
      local_date: "2026-07-08",
      timezone: "UTC",
      generated_at: "2026-07-08T23:00:00.000Z",
    });

    expect(review.sections.retry).toHaveLength(1);
    expect(review.sections.open_loops).toHaveLength(1);
    expect(review.sections.care_candidates.length).toBeGreaterThanOrEqual(0);
    expect(review.source_report_ids).toContain(first.report_id);
    expect(dailyReviewReportPayload(review).local_date).toBe("2026-07-08");
  });

  test("moves repeatedly dismissed suggestions into what to ignore", () => {
    const item = interpretation("session-a", "2026-07-08T14:00:00.000Z", "retry", "skim-risk:recall");
    const suggestion = item.next_actions[0]!;

    const review = buildDailyReview({
      interpretations: [item],
      suggestion_candidates: [suggestion],
      suggestion_responses: [
        { suggestion_id: suggestion.suggestion_id, response: "dismissed", responded_at: "2026-07-08T15:00:00.000Z" },
        { suggestion_id: suggestion.suggestion_id, response: "rated-not-useful", responded_at: "2026-07-08T16:00:00.000Z" },
      ],
      local_date: "2026-07-08",
      timezone: "UTC",
      generated_at: "2026-07-08T23:00:00.000Z",
    });

    expect(review.sections.ignore).toHaveLength(1);
    expect(review.sections.ignore[0]?.rationale).toContain("not useful");
    expect(review.sections.retry).toHaveLength(0);
  });

  test("keeps local day boundaries separate across midnight", () => {
    const late = interpretation("session-late", "2026-07-08T23:30:00.000Z", "retry", "late");
    const next = interpretation("session-next", "2026-07-09T00:30:00.000Z", "retry", "next");

    const review = buildDailyReview({
      interpretations: [late, next],
      local_date: "2026-07-08",
      timezone: "UTC",
      generated_at: "2026-07-08T23:59:00.000Z",
    });

    expect(review.suggestions.map((suggestion) => suggestion.session_ids[0])).toEqual(["session-late"]);
  });

  test("does not leak unrelated prior-day suggestion candidates into the current day", () => {
    const current = interpretation("session-current", "2026-07-08T14:00:00.000Z", "retry", "current-pattern");
    const old = interpretation("session-old", "2026-07-07T14:00:00.000Z", "open_loops", "old-open-loop");

    const review = buildDailyReview({
      interpretations: [current],
      suggestion_candidates: [{ ...old.next_actions[0]!, local_date: "2026-07-07" }],
      suggestion_responses: [
        { suggestion_id: old.next_actions[0]!.suggestion_id, response: "accepted", responded_at: "2026-07-07T15:00:00.000Z" },
      ],
      local_date: "2026-07-08",
      timezone: "UTC",
      generated_at: "2026-07-08T23:00:00.000Z",
    });

    expect(review.suggestions.map((suggestion) => suggestion.pattern_key)).toContain("current-pattern");
    expect(review.suggestions.map((suggestion) => suggestion.pattern_key)).not.toContain("old-open-loop");
  });

  test("keeps prior feedback for a pattern that recurs today", () => {
    const current = interpretation("session-current", "2026-07-08T14:00:00.000Z", "retry", "recurring-pattern");
    const old = interpretation("session-old", "2026-07-07T14:00:00.000Z", "retry", "recurring-pattern");

    const review = buildDailyReview({
      interpretations: [current],
      suggestion_candidates: [{ ...old.next_actions[0]!, local_date: "2026-07-07" }],
      suggestion_responses: [
        { suggestion_id: old.next_actions[0]!.suggestion_id, response: "rated-useful", responded_at: "2026-07-07T15:00:00.000Z" },
      ],
      local_date: "2026-07-08",
      timezone: "UTC",
      generated_at: "2026-07-08T23:00:00.000Z",
    });

    expect(review.sections.retry[0]?.rationale).toContain("Prior feedback marked a similar suggestion useful");
  });

  test("returns an empty state for days without sessions", () => {
    const review = buildDailyReview({
      interpretations: [],
      local_date: "2026-07-08",
      generated_at: "2026-07-08T23:00:00.000Z",
    });

    expect(review.suggestions).toEqual([]);
    expect(review.summary).toContain("No explicit Inquiry sessions");
  });
});

function interpretation(
  sessionId: string,
  generatedAt: string,
  category: "helped" | "fragmented" | "retry" | "ignore" | "open_loops" | "care_candidates",
  patternKey: string,
): SessionInterpretation {
  return {
    report_id: `session-interpretation:${sessionId}`,
    report_kind: "session_interpretation",
    session_id: sessionId,
    generated_at: generatedAt,
    summary: "Evidence suggests one actionable pattern.",
    confidence: 0.7,
    themes: [],
    open_loops: [],
    limitations: ["Fixture."],
    evidence_event_ids: [`event-${sessionId}`],
    source_report_ids: [`replay-${sessionId}`],
    provenance: { builder: "fixture" },
    next_actions: [
      {
        suggestion_id: `suggestion:${sessionId}:${patternKey}`,
        suggestion_kind: category === "open_loops" ? "open-loop" : "retry",
        category,
        title: `Suggestion ${patternKey}`,
        action: "Try one bounded next action.",
        rationale: "Fixture evidence.",
        confidence: 0.7,
        evidence_event_ids: [`event-${sessionId}`],
        report_ids: [`session-interpretation:${sessionId}`],
        session_ids: [sessionId],
        limitation: "Needs feedback.",
        pattern_key: patternKey,
      },
    ],
  };
}
