import type { ReplayMarker, ReplayMarkerKind } from "./heuristics";
import type { StimulusSegment } from "./stimulus";

export type ComprehensionHeatmapKind =
  | "intrinsic-difficulty"
  | "behavioral-loss-of-thread"
  | "mixed-load"
  | "behavior-only";

export type HeatmapStimulusEvidence = {
  segment_id: string;
  stimulus_id: string;
  content_ref: string;
  density: number;
  term_novelty: number;
  transition_count: number;
  quiz_checkpoint_candidate: boolean;
  evidence_event_ids: string[];
  evidence: string[];
  text?: string;
};

export type HeatmapBehaviorEvidence = {
  marker_id: string;
  kind: ReplayMarkerKind;
  confidence: number;
  evidence_event_ids: string[];
  evidence: string[];
};

export type ComprehensionHeatmapSegment = {
  heatmap_id: string;
  session_id: string;
  kind: ComprehensionHeatmapKind;
  start_ms: number;
  end_ms: number;
  confidence: number;
  stimulus_evidence: HeatmapStimulusEvidence[];
  behavior_evidence: HeatmapBehaviorEvidence[];
  evidence_event_ids: string[];
  limitation: string;
  suggested_repair: string;
};

export type BuildComprehensionHeatmapInput = {
  session_id: string;
  markers: ReplayMarker[];
  stimulus_segments?: StimulusSegment[];
  stimulusSegments?: StimulusSegment[];
};

const behaviorWeights: Record<ReplayMarkerKind, number> = {
  "skim-risk": 0.45,
  "stuck-loop": 0.9,
  "high-load": 0.75,
  "copied-passage": 0.35,
  rewind: 0.7,
  "tab-churn": 0.6,
  "app-churn": 0.55,
  "off-browser-focus": 0.4,
  "deep-work-span": 0.45,
  label: 0.2,
  probe: 0.15,
};

export function buildComprehensionHeatmap(input: BuildComprehensionHeatmapInput): ComprehensionHeatmapSegment[] {
  const stimulusSegments = input.stimulus_segments ?? input.stimulusSegments ?? [];
  if (stimulusSegments.length === 0) {
    return buildBehaviorOnlyHeatmap(input.session_id, input.markers);
  }

  const segments = stimulusSegments
    .flatMap((segment) => {
      const overlappingMarkers = input.markers.filter((marker) => overlaps(segment, marker));
      const difficulty = stimulusDifficulty(segment);
      const behavior = behaviorFriction(overlappingMarkers);
      const kind = classifySegment(difficulty, behavior);

      if (!kind) {
        return [];
      }

      return [
        heatmapSegment({
          session_id: input.session_id,
          kind,
          start_ms: segment.start_ms,
          end_ms: segment.end_ms,
          stimulus_evidence: [stimulusEvidence(segment)],
          behavior_evidence: overlappingMarkers.map(markerEvidence),
          confidence: confidenceFor(kind, difficulty, behavior),
        }),
      ];
    })
    .sort((a, b) => a.start_ms - b.start_ms || b.confidence - a.confidence);

  if (segments.length > 0) {
    return segments;
  }

  return buildBehaviorOnlyHeatmap(input.session_id, input.markers);
}

function buildBehaviorOnlyHeatmap(sessionId: string, markers: ReplayMarker[]): ComprehensionHeatmapSegment[] {
  return markers
    .filter((marker) => behaviorFriction([marker]) >= 0.2)
    .map((marker) =>
      heatmapSegment({
        session_id: sessionId,
        kind: "behavior-only",
        start_ms: marker.start_ms,
        end_ms: marker.end_ms,
        stimulus_evidence: [],
        behavior_evidence: [markerEvidence(marker)],
        confidence: clamp(0.42 + behaviorFriction([marker]) * 0.5),
      }),
    )
    .sort((a, b) => a.start_ms - b.start_ms || b.confidence - a.confidence);
}

function classifySegment(difficulty: number, behavior: number): ComprehensionHeatmapKind | null {
  const difficult = difficulty >= 0.56;
  const behavioral = behavior >= 0.25;

  if (difficult && behavioral) {
    return "mixed-load";
  }

  if (difficult) {
    return "intrinsic-difficulty";
  }

  if (behavioral) {
    return "behavioral-loss-of-thread";
  }

  return null;
}

function heatmapSegment(input: {
  session_id: string;
  kind: ComprehensionHeatmapKind;
  start_ms: number;
  end_ms: number;
  confidence: number;
  stimulus_evidence: HeatmapStimulusEvidence[];
  behavior_evidence: HeatmapBehaviorEvidence[];
}): ComprehensionHeatmapSegment {
  const evidenceEventIds = unique([
    ...input.stimulus_evidence.flatMap((evidence) => evidence.evidence_event_ids),
    ...input.behavior_evidence.flatMap((evidence) => evidence.evidence_event_ids),
  ]);
  const stimulusKey = input.stimulus_evidence.map((evidence) => evidence.segment_id).join("+") || "no-stimulus";
  const behaviorKey = input.behavior_evidence.map((evidence) => evidence.marker_id).join("+") || "no-marker";

  return {
    heatmap_id: `${input.kind}:${input.session_id}:${input.start_ms}:${stimulusKey}:${behaviorKey}`,
    session_id: input.session_id,
    kind: input.kind,
    start_ms: input.start_ms,
    end_ms: input.end_ms,
    confidence: round(input.confidence),
    stimulus_evidence: input.stimulus_evidence,
    behavior_evidence: input.behavior_evidence,
    evidence_event_ids: evidenceEventIds,
    limitation: limitationFor(input.kind),
    suggested_repair: repairFor(input.kind, input.behavior_evidence),
  };
}

function stimulusEvidence(segment: StimulusSegment): HeatmapStimulusEvidence {
  return {
    segment_id: segment.segment_id,
    stimulus_id: segment.stimulus_id,
    content_ref: segment.content_ref,
    density: round(segment.features.density),
    term_novelty: round(segment.features.term_novelty),
    transition_count: segment.features.transition_count,
    quiz_checkpoint_candidate: segment.features.quiz_checkpoint_candidate,
    evidence_event_ids: segment.evidence_event_ids,
    evidence: segment.evidence,
    ...(segment.text ? { text: segment.text } : {}),
  };
}

function markerEvidence(marker: ReplayMarker): HeatmapBehaviorEvidence {
  return {
    marker_id: marker.marker_id,
    kind: marker.kind,
    confidence: round(marker.confidence),
    evidence_event_ids: marker.evidence_event_ids,
    evidence: marker.evidence,
  };
}

function stimulusDifficulty(segment: StimulusSegment): number {
  const features = segment.features;
  return clamp(features.density * 0.66 + features.term_novelty * 0.22 + Math.min(features.transition_count, 4) * 0.03);
}

function behaviorFriction(markers: ReplayMarker[]): number {
  const weighted = markers.reduce((total, marker) => total + behaviorWeights[marker.kind] * marker.confidence, 0);
  return clamp(weighted / 1.25);
}

function overlaps(segment: StimulusSegment, marker: ReplayMarker): boolean {
  if (marker.start_ms === marker.end_ms) {
    return marker.start_ms >= segment.start_ms && marker.start_ms <= segment.end_ms;
  }

  return marker.start_ms < segment.end_ms && marker.end_ms > segment.start_ms;
}

function confidenceFor(kind: ComprehensionHeatmapKind, difficulty: number, behavior: number): number {
  if (kind === "mixed-load") {
    return clamp(0.52 + difficulty * 0.24 + behavior * 0.24);
  }

  if (kind === "intrinsic-difficulty") {
    return clamp(0.48 + difficulty * 0.38);
  }

  if (kind === "behavioral-loss-of-thread") {
    return clamp(0.46 + behavior * 0.42);
  }

  return clamp(0.42 + behavior * 0.5);
}

function limitationFor(kind: ComprehensionHeatmapKind): string {
  if (kind === "intrinsic-difficulty") {
    return "Stimulus features suggest density; this does not prove confusion without user behavior evidence.";
  }

  if (kind === "behavioral-loss-of-thread") {
    return "behavior evidence suggests loss of thread; stimulus may be simple or missing nuance not captured by local features.";
  }

  if (kind === "mixed-load") {
    return "Stimulus and behavior evidence both point to load, but the segment remains a repair hypothesis.";
  }

  return "No local stimulus was attached, so this segment uses behavior evidence only.";
}

function repairFor(kind: ComprehensionHeatmapKind, behaviorEvidence: HeatmapBehaviorEvidence[]): string {
  const behaviorKinds = new Set(behaviorEvidence.map((evidence) => evidence.kind));

  if (kind === "intrinsic-difficulty") {
    return "Slow down here and state the section's claim in one sentence.";
  }

  if (kind === "mixed-load") {
    return "Reread this span, identify the missing prerequisite, then answer one recall check.";
  }

  if (behaviorKinds.has("rewind") || behaviorKinds.has("stuck-loop")) {
    return "Rewatch or reread this span and write the confusing prerequisite.";
  }

  if (behaviorKinds.has("skim-risk")) {
    return "Return to the fast-scrolled span and write one recall question.";
  }

  if (behaviorKinds.has("tab-churn")) {
    return "Choose one branch to keep and turn the rest into follow-up notes.";
  }

  if (behaviorKinds.has("app-churn")) {
    return "Choose which app/task branch should become a follow-up note.";
  }

  if (behaviorKinds.has("deep-work-span")) {
    return "Summarize what the non-browser work block produced.";
  }

  if (behaviorKinds.has("off-browser-focus")) {
    return "Name what happened in this app block and whether it should become a note.";
  }

  return "Review this span against the source and mark whether the thread recovered.";
}

function unique(values: string[]): string[] {
  return [...new Set(values)];
}

function round(value: number): number {
  return Math.round(value * 100) / 100;
}

function clamp(value: number): number {
  return Math.max(0, Math.min(1, value));
}
