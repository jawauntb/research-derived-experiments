import type { EventEnvelope } from "@inquiry/schema";
import { buildReplayMemo, type ReplayMemo } from "@inquiry/signals";

export type SessionReplayReport = ReplayMemo & {
  report_id: string;
  generated_at: string;
  limitations: string[];
};

export function createSessionReplayReport(events: EventEnvelope[]): SessionReplayReport {
  const memo = buildReplayMemo(events);

  return {
    ...memo,
    report_id: crypto.randomUUID(),
    generated_at: new Date().toISOString(),
    limitations: [
      "Markers are conservative heuristics, not cognitive-state certainty.",
      "Camera-derived markers require adequate quality flags and should be interpreted with surrounding evidence.",
    ],
  };
}
