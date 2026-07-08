import { createEvent, type EventEnvelope, type JsonObject, type RepairCandidatePayload, type RepairOutcomePayload } from "@inquiry/schema";
import type { ComprehensionHeatmapSegment, HeatmapBehaviorEvidence } from "./heatmap";

export type RepairActionKind =
  | "restate-claim"
  | "missing-prerequisite"
  | "rewatch-span"
  | "recall-question"
  | "explain-copied-passage"
  | "follow-up-note";

export type RepairCandidate = {
  repair_id: string;
  session_id: string;
  heatmap_id: string;
  action: RepairActionKind;
  prompt: string;
  start_ms: number;
  end_ms: number;
  confidence: number;
  source_kind: ComprehensionHeatmapSegment["kind"];
  source_marker_ids: string[];
  evidence_event_ids: string[];
  limitation: string;
};

export type RepairCandidateOptions = {
  min_confidence?: number;
  max_candidates?: number;
};

export type RepairEventOptions = {
  event_id?: string;
  source_version?: string;
  monotonic_ms?: number;
  captured_at?: string;
};

export type RepairProbeEventOptions = RepairEventOptions & {
  probe_id?: string;
};

export type RepairOutcomeKind = "accepted" | "answered" | "dismissed" | "snoozed" | "rated-useful" | "rated-not-useful";

export type CreateRepairOutcomeInput = RepairEventOptions & {
  candidate: RepairCandidate;
  outcome: RepairOutcomeKind;
  probe_id?: string;
  answer?: string;
  answer_confidence?: number;
  reason?: string;
};

export function buildRepairCandidates(
  heatmap: ComprehensionHeatmapSegment[],
  options: RepairCandidateOptions = {},
): RepairCandidate[] {
  const minConfidence = options.min_confidence ?? 0.5;
  const maxCandidates = options.max_candidates ?? 3;

  return heatmap
    .filter((segment) => segment.confidence >= minConfidence)
    .filter((segment) => segment.evidence_event_ids.length > 0 || segment.stimulus_evidence.length > 0)
    .map(candidateForSegment)
    .sort((a, b) => b.confidence - a.confidence || a.start_ms - b.start_ms)
    .slice(0, maxCandidates);
}

export function createRepairCandidateEvent(
  candidate: RepairCandidate,
  options: RepairEventOptions = {},
): EventEnvelope<RepairCandidatePayload> {
  return createEvent({
    ...(options.event_id === undefined ? {} : { event_id: options.event_id }),
    session_id: candidate.session_id,
    source: "desktop-system",
    source_version: options.source_version ?? "desktop@0.1.0",
    ...(options.captured_at === undefined ? {} : { captured_at: options.captured_at }),
    monotonic_ms: options.monotonic_ms ?? candidate.start_ms,
    event_type: "repair.candidate",
    confidence: candidate.confidence,
    payload: {
      repair_id: candidate.repair_id,
      heatmap_id: candidate.heatmap_id,
      action: candidate.action,
      prompt: candidate.prompt,
      start_ms: candidate.start_ms,
      end_ms: candidate.end_ms,
      source_kind: candidate.source_kind,
      source_marker_ids: candidate.source_marker_ids,
      evidence_event_ids: candidate.evidence_event_ids,
      limitation: candidate.limitation,
    },
    privacy_class: "local-derived",
    retention_policy: "local-default",
  });
}

export function createRepairProbeEvent(
  candidate: RepairCandidate,
  options: RepairProbeEventOptions = {},
): EventEnvelope<JsonObject> {
  const probeId = options.probe_id ?? `${candidate.repair_id}:probe`;
  return createEvent({
    ...(options.event_id === undefined ? {} : { event_id: options.event_id }),
    session_id: candidate.session_id,
    source: "desktop-system",
    source_version: options.source_version ?? "desktop@0.1.0",
    ...(options.captured_at === undefined ? {} : { captured_at: options.captured_at }),
    monotonic_ms: options.monotonic_ms ?? candidate.start_ms,
    event_type: "probe.requested",
    confidence: candidate.confidence,
    payload: {
      probe_id: probeId,
      repair_id: candidate.repair_id,
      heatmap_id: candidate.heatmap_id,
      question: candidate.prompt,
      action: candidate.action,
      source_marker_ids: candidate.source_marker_ids,
      evidence_event_ids: candidate.evidence_event_ids,
    },
    privacy_class: "local-derived",
    retention_policy: "local-default",
  });
}

export function createRepairProbeAnswerEvent(
  candidate: RepairCandidate,
  input: RepairEventOptions & { probe_id: string; answer: string; confidence: number },
): EventEnvelope<JsonObject> {
  return createEvent({
    ...(input.event_id === undefined ? {} : { event_id: input.event_id }),
    session_id: candidate.session_id,
    source: "user",
    source_version: input.source_version ?? "desktop@0.1.0",
    ...(input.captured_at === undefined ? {} : { captured_at: input.captured_at }),
    monotonic_ms: input.monotonic_ms ?? candidate.end_ms,
    event_type: "probe.answered",
    confidence: input.confidence,
    payload: {
      probe_id: input.probe_id,
      repair_id: candidate.repair_id,
      heatmap_id: candidate.heatmap_id,
      answer: input.answer,
      source_marker_ids: candidate.source_marker_ids,
      evidence_event_ids: candidate.evidence_event_ids,
    },
    privacy_class: "local-derived",
    retention_policy: "local-default",
  });
}

export function createRepairOutcomeEvent(input: CreateRepairOutcomeInput): EventEnvelope<RepairOutcomePayload> {
  return createEvent({
    ...(input.event_id === undefined ? {} : { event_id: input.event_id }),
    session_id: input.candidate.session_id,
    source: "user",
    source_version: input.source_version ?? "desktop@0.1.0",
    ...(input.captured_at === undefined ? {} : { captured_at: input.captured_at }),
    monotonic_ms: input.monotonic_ms ?? input.candidate.end_ms,
    event_type: "repair.outcome",
    confidence: input.answer_confidence ?? input.candidate.confidence,
    payload: {
      repair_id: input.candidate.repair_id,
      heatmap_id: input.candidate.heatmap_id,
      outcome: input.outcome,
      action: input.candidate.action,
      ...(input.probe_id ? { probe_id: input.probe_id } : {}),
      ...(input.answer ? { answer: input.answer } : {}),
      ...(input.answer_confidence === undefined ? {} : { answer_confidence: input.answer_confidence }),
      ...(input.reason ? { reason: input.reason } : {}),
    },
    privacy_class: "local-derived",
    retention_policy: "local-default",
  });
}

function candidateForSegment(segment: ComprehensionHeatmapSegment): RepairCandidate {
  const action = actionForSegment(segment);
  return {
    repair_id: `repair:${segment.heatmap_id}:${action}`,
    session_id: segment.session_id,
    heatmap_id: segment.heatmap_id,
    action,
    prompt: promptForAction(action, segment),
    start_ms: segment.start_ms,
    end_ms: segment.end_ms,
    confidence: segment.confidence,
    source_kind: segment.kind,
    source_marker_ids: segment.behavior_evidence.map((evidence) => evidence.marker_id),
    evidence_event_ids: segment.evidence_event_ids,
    limitation: segment.limitation,
  };
}

function actionForSegment(segment: ComprehensionHeatmapSegment): RepairActionKind {
  const behaviorKinds = new Set(segment.behavior_evidence.map((evidence) => evidence.kind));

  if (behaviorKinds.has("stuck-loop")) {
    return "missing-prerequisite";
  }

  if (behaviorKinds.has("rewind")) {
    return "rewatch-span";
  }

  if (behaviorKinds.has("skim-risk")) {
    return "recall-question";
  }

  if (behaviorKinds.has("copied-passage")) {
    return "explain-copied-passage";
  }

  if (behaviorKinds.has("tab-churn")) {
    return "follow-up-note";
  }

  if (segment.kind === "intrinsic-difficulty") {
    return "restate-claim";
  }

  return "missing-prerequisite";
}

function promptForAction(action: RepairActionKind, segment: ComprehensionHeatmapSegment): string {
  const span = `${Math.round(segment.start_ms / 1000)}s-${Math.round(segment.end_ms / 1000)}s`;

  if (action === "missing-prerequisite") {
    return `What prerequisite, definition, or example was missing around ${span}?`;
  }

  if (action === "rewatch-span") {
    return `Rewatch or reread ${span}. What changed after the replay?`;
  }

  if (action === "recall-question") {
    return `What is one recall question this fast-scrolled span should answer?`;
  }

  if (action === "explain-copied-passage") {
    const evidenceSummary = copiedEvidenceSummary(segment);
    if (evidenceSummary) {
      return `Around ${span}, ${evidenceSummary} What were you trying to preserve, compare, or question?`;
    }

    return `Around ${span}, what were you trying to preserve, compare, or question with the selected or copied evidence?`;
  }

  if (action === "follow-up-note") {
    return `Which open branch should become a follow-up note, and which can be closed?`;
  }

  return `State the main claim from ${span} in one sentence.`;
}

function copiedEvidenceSummary(segment: ComprehensionHeatmapSegment): string | null {
  const copiedEvidence = segment.behavior_evidence.find((evidence) => evidence.kind === "copied-passage");
  const summary = copiedEvidence?.evidence[0];
  if (!summary) {
    return null;
  }

  return `${summary.charAt(0).toLowerCase()}${summary.slice(1)}`;
}
