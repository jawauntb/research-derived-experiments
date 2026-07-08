import type { EventEnvelope } from "@inquiry/schema";
import {
  buildRepairCandidates,
  buildReplayMemo,
  segmentStimulus,
  type RepairCandidate,
  type ReplayMemo,
  type StimulusInput,
  type StimulusSegment,
} from "@inquiry/signals";

export type SessionReplayReport = ReplayMemo & {
  report_id: string;
  generated_at: string;
  limitations: string[];
  repair_candidates: RepairCandidate[];
};

export type SessionReplayReportOptions = {
  window_ms?: number;
  stimulus_inputs?: StimulusInput[];
  stimulus_segments?: StimulusSegment[];
};

export function createSessionReplayReport(events: EventEnvelope[], options: SessionReplayReportOptions = {}): SessionReplayReport {
  const stimulusSegments = [
    ...(options.stimulus_segments ?? []),
    ...(options.stimulus_inputs ?? []).flatMap((input) => segmentStimulus(input)),
  ];
  const memo = buildReplayMemo(events, {
    stimulus_segments: stimulusSegments,
    ...(options.window_ms === undefined ? {} : { window_ms: options.window_ms }),
  });

  return {
    ...memo,
    report_id: crypto.randomUUID(),
    generated_at: new Date().toISOString(),
    repair_candidates: buildRepairCandidates(memo.heatmap),
    limitations: [
      "Markers are conservative heuristics, not cognitive-state certainty.",
      "Camera-derived markers require adequate quality flags and should be interpreted with surrounding evidence.",
      "Stimulus heatmap segments use local deterministic features and only include document text after explicit opt-in.",
      "Copied or selected page text is not stored by default; replay uses timing, counts, lengths, and hashed page refs.",
      "Desktop activity replay uses app/window metadata only; raw screenshots, OCR text, and screen recordings are not stored by default.",
    ],
  };
}
