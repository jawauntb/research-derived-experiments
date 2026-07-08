import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import type { EventEnvelope } from "../packages/schema/src";
import { buildReplayMarkers } from "../packages/signals/src";

export type ValidationRowKind =
  | "label"
  | "probe"
  | "repair_outcome"
  | "stimulus_segment"
  | "behavior_marker"
  | "camera_quality_flag";

export type ValidationRow = {
  kind: ValidationRowKind;
  session_id: string;
  source_event_id: string;
  target_id: string;
  value: string;
  monotonic_ms: number;
  privacy_class: string;
  smoke: boolean;
  metrics?: Record<string, number | boolean>;
  quality_flags?: string[];
};

export type GateStatus = "smoke" | "insufficient-data";

export type ValidationReport = {
  artifact: "inquiry-validation-report/v1";
  run_id: string;
  generated_at: string;
  scope: {
    requirements: string[];
    acceptance_examples: string[];
    state_prediction_claims: "not-made";
  };
  validation_rows: ValidationRow[];
  gates: {
    g0: ReliabilityGate;
    g1: StimulusBaselineGate;
    g2: ResidualGate;
    g3: CameraResidualGate;
    g4: RepairUtilityGate;
  };
  privacy_checks: {
    uses_raw_camera_frames: false;
    uses_raw_typed_content: false;
    excluded_payload_fields: string[];
  };
  interpretation: {
    proven: string[];
    smoke: string[];
    insufficient_data: string[];
  };
};

export type ReliabilityGate = {
  status: GateStatus;
  repeated_target_count: number;
  agreement_mean: number | null;
  rows: Array<{
    kind: "label" | "probe" | "repair_outcome";
    target_id: string;
    observations: number;
    majority_value: string;
    agreement: number;
  }>;
  negative_controls: Array<{
    control: string;
    status: GateStatus;
    note: string;
  }>;
  decision: string;
};

export type StimulusBaselineGate = {
  status: GateStatus;
  baseline: {
    top_segment_id: string | null;
    target_segment_ids: string[];
    hit_at_1: boolean | null;
    segment_scores: Array<{
      segment_id: string;
      score: number;
      density: number;
      term_novelty: number;
      transition_count: number;
      quiz_checkpoint_candidate: boolean;
    }>;
  };
  negative_controls: Array<{
    control: "shuffled-segment-order" | "shifted-boundaries";
    top_segment_id: string | null;
    hit_at_1: boolean | null;
    note: string;
  }>;
  decision: string;
};

export type ResidualGate = {
  status: "insufficient-data";
  available_sessions: number;
  available_targets: number;
  browser_marker_counts: Record<string, number>;
  threshold: string;
  decision: string;
};

export type CameraResidualGate = ResidualGate & {
  camera_feature_windows: number;
  quality_flag_counts: Record<string, number>;
  uses_raw_camera_frames: false;
};

export type RepairUtilityGate = {
  status: "insufficient-data";
  repair_outcome_count: number;
  outcome_counts: Record<string, number>;
  threshold: string;
  decision: string;
};

type ValidationOptions = {
  run_id?: string;
  generated_at?: string;
};

type StimulusSegmentRow = ValidationRow & {
  kind: "stimulus_segment";
  segment_id: string;
  ordinal: number;
  start_ms: number;
  end_ms: number;
  density: number;
  term_novelty: number;
  transition_count: number;
  quiz_checkpoint_candidate: boolean;
};

const verifierKinds = new Set<ValidationRowKind>(["label", "probe", "repair_outcome"]);
const excludedPayloadFields = [
  "answer",
  "content",
  "copied_text",
  "frame",
  "highlight_text",
  "html",
  "key",
  "question",
  "rawFrame",
  "rawText",
  "selected_text",
  "text",
  "typed_text",
  "user_response",
  "video",
];

export function parseValidationJsonl(jsonl: string): EventEnvelope[] {
  return jsonl
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line) as unknown)
    .flatMap((line) => {
      if (isRecord(line) && isEventEnvelopeLike(line.event)) {
        return [line.event];
      }

      if (isEventEnvelopeLike(line)) {
        return [line];
      }

      return [];
    })
    .sort((a, b) => a.monotonic_ms - b.monotonic_ms || a.event_id.localeCompare(b.event_id));
}

export function createValidationReport(events: EventEnvelope[], options: ValidationOptions = {}): ValidationReport {
  const sortedEvents = [...events].sort((a, b) => a.monotonic_ms - b.monotonic_ms || a.event_id.localeCompare(b.event_id));
  const stimulusSegments = stimulusSegmentRows(sortedEvents);
  const rows = [
    ...labelRows(sortedEvents, stimulusSegments),
    ...probeRows(sortedEvents, stimulusSegments),
    ...repairOutcomeRows(sortedEvents, stimulusSegments),
    ...stimulusSegments,
    ...behaviorMarkerRows(sortedEvents),
    ...cameraQualityRows(sortedEvents),
  ].sort((a, b) => a.monotonic_ms - b.monotonic_ms || a.kind.localeCompare(b.kind) || a.source_event_id.localeCompare(b.source_event_id));

  const sessions = unique(sortedEvents.map((event) => event.session_id));

  return {
    artifact: "inquiry-validation-report/v1",
    run_id: options.run_id ?? "fixture-smoke",
    generated_at: options.generated_at ?? latestCapturedAt(sortedEvents),
    scope: {
      requirements: ["R15"],
      acceptance_examples: ["AE7"],
      state_prediction_claims: "not-made",
    },
    validation_rows: rows,
    gates: {
      g0: reliabilityGate(rows),
      g1: stimulusBaselineGate(stimulusSegments, rows),
      g2: browserResidualGate(rows, sessions.length),
      g3: cameraResidualGate(sortedEvents, rows, sessions.length),
      g4: repairUtilityGate(rows),
    },
    privacy_checks: {
      uses_raw_camera_frames: false,
      uses_raw_typed_content: false,
      excluded_payload_fields: excludedPayloadFields,
    },
    interpretation: {
      proven: [
        "Fixture JSONL converts to validation rows without raw camera frames, raw typed content, or raw stimulus text.",
        "Stimulus-only G1 baseline and deterministic negative controls run from redacted segment features.",
      ],
      smoke: [
        "G0 agreement is fixture smoke over repeated labels, probes, and repair outcomes.",
        "G1 hit-at-1 is fixture smoke and is not evidence of personalized state prediction.",
      ],
      insufficient_data: [
        "G2 browser residual needs held-out sessions after G1.",
        "G3 camera residual needs quality-stratified held-out sessions and remains auxiliary only.",
        "G4 repair utility needs A/B or within-user repair comparisons.",
      ],
    },
  };
}

export function renderValidationMarkdown(report: ValidationReport): string {
  const rowCounts = countBy(report.validation_rows, (row) => row.kind);
  const rowTable = Object.entries(rowCounts)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([kind, count]) => `| ${kind} | ${count} |`)
    .join("\n");
  const g1Rows = report.gates.g1.baseline.segment_scores
    .map((row) => `| ${row.segment_id} | ${row.score.toFixed(2)} | ${row.density.toFixed(2)} | ${row.term_novelty.toFixed(2)} | ${row.transition_count} | ${row.quiz_checkpoint_candidate ? "yes" : "no"} |`)
    .join("\n");
  const controlRows = report.gates.g1.negative_controls
    .map((row) => `| ${row.control} | ${row.top_segment_id ?? "n/a"} | ${formatNullableBoolean(row.hit_at_1)} | ${row.note} |`)
    .join("\n");

  return [
    "# Inquiry Validation Smoke Report",
    "",
    `Run ID: \`${report.run_id}\``,
    `Generated from fixture timestamp: \`${report.generated_at}\``,
    "",
    "This artifact is a smoke validation report for R15 / AE7. It does not make state-prediction claims.",
    "",
    "## Export To Validation Rows",
    "",
    "| Row kind | Count |",
    "| --- | ---: |",
    rowTable,
    "",
    "## G0 Reliability Ceiling",
    "",
    `Status: \`${report.gates.g0.status}\``,
    `Repeated targets: ${report.gates.g0.repeated_target_count}`,
    `Mean agreement: ${report.gates.g0.agreement_mean === null ? "n/a" : report.gates.g0.agreement_mean.toFixed(2)}`,
    "",
    report.gates.g0.decision,
    "",
    "## G1 Stimulus-Only Baseline",
    "",
    `Status: \`${report.gates.g1.status}\``,
    `Top segment: \`${report.gates.g1.baseline.top_segment_id ?? "n/a"}\``,
    `Hit@1: ${formatNullableBoolean(report.gates.g1.baseline.hit_at_1)}`,
    "",
    "| Segment | Score | Density | Term novelty | Transitions | Quiz checkpoint |",
    "| --- | ---: | ---: | ---: | ---: | --- |",
    g1Rows,
    "",
    "| Negative control | Top segment | Hit@1 | Note |",
    "| --- | --- | --- | --- |",
    controlRows,
    "",
    "## G2-G4 Residual Gates",
    "",
    `G2 browser residual: \`${report.gates.g2.status}\` - ${report.gates.g2.decision}`,
    `G3 camera residual: \`${report.gates.g3.status}\` - ${report.gates.g3.decision}`,
    `G4 repair utility: \`${report.gates.g4.status}\` - ${report.gates.g4.decision}`,
    "",
    "## Privacy Checks",
    "",
    `Uses raw camera frames: ${report.privacy_checks.uses_raw_camera_frames}`,
    `Uses raw typed content: ${report.privacy_checks.uses_raw_typed_content}`,
    "",
  ].join("\n");
}

function labelRows(events: EventEnvelope[], segments: StimulusSegmentRow[]): ValidationRow[] {
  return events
    .filter((event) => event.event_type === "label.added")
    .map((event) => {
      const targetId = targetSegmentId(event, segments);
      return row(event, "label", targetId, safeString(event.payload.label, "unknown-label"));
    });
}

function probeRows(events: EventEnvelope[], segments: StimulusSegmentRow[]): ValidationRow[] {
  return events
    .filter((event) => event.event_type === "probe.answered")
    .map((event) => {
      const targetId = targetSegmentId(event, segments);
      return row(event, "probe", targetId, safeString(event.payload.answer_quality, "answered"));
    });
}

function repairOutcomeRows(events: EventEnvelope[], segments: StimulusSegmentRow[]): ValidationRow[] {
  return events
    .filter((event) => event.event_type === "repair.outcome")
    .map((event) => {
      const targetId = targetSegmentId(event, segments);
      return row(event, "repair_outcome", targetId, safeString(event.payload.outcome, "unknown-outcome"));
    });
}

function stimulusSegmentRows(events: EventEnvelope[]): StimulusSegmentRow[] {
  return events
    .filter((event) => event.event_type === "stimulus.segmented")
    .flatMap((event) => {
      const rawSegments: unknown[] = Array.isArray(event.payload.segments) ? event.payload.segments : [];
      const payloadSegments = rawSegments.filter(isRecord);
      return payloadSegments.map((segment, index): StimulusSegmentRow => {
        const segmentId = safeString(segment.segment_id, `${safeString(event.payload.stimulus_id, "stimulus")}:${index + 1}`);
        const ordinal = safeNumber(segment.ordinal, index + 1);
        const startMs = safeNumber(segment.start_ms, event.monotonic_ms);
        const endMs = safeNumber(segment.end_ms, startMs);
        const density = safeNumber(segment.density, 0);
        const termNovelty = safeNumber(segment.term_novelty, 0);
        const transitionCount = safeNumber(segment.transition_count, 0);
        const quizCheckpointCandidate = segment.quiz_checkpoint_candidate === true;

        return {
          kind: "stimulus_segment",
          session_id: event.session_id,
          source_event_id: event.event_id,
          target_id: segmentId,
          value: segmentId,
          privacy_class: event.privacy_class,
          smoke: true,
          segment_id: segmentId,
          ordinal,
          start_ms: startMs,
          end_ms: endMs,
          monotonic_ms: startMs,
          density,
          term_novelty: termNovelty,
          transition_count: transitionCount,
          quiz_checkpoint_candidate: quizCheckpointCandidate,
          metrics: {
            ordinal,
            start_ms: startMs,
            end_ms: endMs,
            density,
            term_novelty: termNovelty,
            transition_count: transitionCount,
            quiz_checkpoint_candidate: quizCheckpointCandidate,
          },
        };
      });
    })
    .sort((a, b) => a.ordinal - b.ordinal || a.segment_id.localeCompare(b.segment_id));
}

function behaviorMarkerRows(events: EventEnvelope[]): ValidationRow[] {
  return buildReplayMarkers(events).map((marker) => ({
    kind: "behavior_marker",
    session_id: marker.session_id,
    source_event_id: marker.marker_id,
    target_id: marker.marker_id,
    value: marker.kind,
    monotonic_ms: marker.start_ms,
    privacy_class: "local-derived",
    smoke: true,
    metrics: {
      confidence: marker.confidence,
      evidence_event_count: marker.evidence_event_ids.length,
    },
  }));
}

function cameraQualityRows(events: EventEnvelope[]): ValidationRow[] {
  return events
    .filter((event) => event.event_type === "camera.feature_window")
    .flatMap((event) => {
      const flags = event.quality_flags.length > 0 ? event.quality_flags : ["quality-ok"];
      return flags.map((flag) => row(event, "camera_quality_flag", event.event_id, flag, { quality_flags: event.quality_flags }));
    });
}

function reliabilityGate(rows: ValidationRow[]): ReliabilityGate {
  const verifierRows = rows.filter((row) => verifierKinds.has(row.kind));
  const groups = groupBy(verifierRows, (row) => `${row.kind}:${row.target_id}`);
  const repeated = [...groups.values()]
    .filter((group) => group.length >= 2)
    .map((group) => {
      const counts = countBy(group, (row) => row.value);
      const [majorityValue, majorityCount] = maxEntry(counts);
      return {
        kind: group[0]!.kind as "label" | "probe" | "repair_outcome",
        target_id: group[0]!.target_id,
        observations: group.length,
        majority_value: majorityValue,
        agreement: round(majorityCount / group.length),
      };
    });
  const agreementMean = repeated.length > 0 ? round(average(repeated.map((group) => group.agreement))) : null;

  return {
    status: repeated.length > 0 ? "smoke" : "insufficient-data",
    repeated_target_count: repeated.length,
    agreement_mean: agreementMean,
    rows: repeated,
    negative_controls: [
      {
        control: "randomly-paired-labels",
        status: "insufficient-data",
        note: "Needs multiple sessions before random-pair reliability is meaningful.",
      },
      {
        control: "duplicate-session-disagreement-audit",
        status: "insufficient-data",
        note: "Needs repeated exported sessions, not a single fixture.",
      },
    ],
    decision:
      repeated.length > 0
        ? "Fixture repeats are internally consistent, but this is only a smoke ceiling; collect real repeated labels, probes, and outcomes before modeling."
        : "No repeated verifier targets exist yet; revise prompts and collect repeated verifier events before modeling.",
  };
}

function stimulusBaselineGate(segments: StimulusSegmentRow[], rows: ValidationRow[]): StimulusBaselineGate {
  const scored = segments
    .map((segment) => ({
      segment_id: segment.segment_id,
      score: stimulusScore(segment),
      density: segment.density,
      term_novelty: segment.term_novelty,
      transition_count: segment.transition_count,
      quiz_checkpoint_candidate: segment.quiz_checkpoint_candidate,
    }))
    .sort((a, b) => b.score - a.score || a.segment_id.localeCompare(b.segment_id));
  const targetIds = targetSegmentIds(rows, new Set(segments.map((segment) => segment.segment_id)));
  const topSegmentId = scored[0]?.segment_id ?? null;
  const hitAt1 = topSegmentId === null || targetIds.length === 0 ? null : targetIds.includes(topSegmentId);
  const shuffled = shuffledSegmentScores(segments);
  const shiftedTargetIds = shiftedBoundaryTargetIds(segments, rows);
  const shiftedHitAt1 = topSegmentId === null || shiftedTargetIds.length === 0 ? null : shiftedTargetIds.includes(topSegmentId);

  return {
    status: segments.length > 0 ? "smoke" : "insufficient-data",
    baseline: {
      top_segment_id: topSegmentId,
      target_segment_ids: targetIds,
      hit_at_1: hitAt1,
      segment_scores: scored,
    },
    negative_controls: [
      {
        control: "shuffled-segment-order",
        top_segment_id: shuffled[0]?.segment_id ?? null,
        hit_at_1: shuffled[0] === undefined || targetIds.length === 0 ? null : targetIds.includes(shuffled[0].segment_id),
        note: "Deterministic one-step rotation assigns feature scores to the wrong segment IDs.",
      },
      {
        control: "shifted-boundaries",
        top_segment_id: topSegmentId,
        hit_at_1: shiftedHitAt1,
        note: "Targets are re-associated after shifting segment windows by half a segment.",
      },
    ],
    decision:
      segments.length > 0
        ? "Stimulus-only smoke baseline is available; product models must beat it on held-out sessions before any user-specific claim."
        : "No redacted stimulus segment features exist yet; attach stimulus.segmented metadata before G1.",
  };
}

function browserResidualGate(rows: ValidationRow[], sessionCount: number): ResidualGate {
  const browserMarkers = rows.filter((row) => row.kind === "behavior_marker");
  const targets = targetSegmentIds(rows, new Set(rows.filter((row) => row.kind === "stimulus_segment").map((row) => row.target_id)));

  return {
    status: "insufficient-data",
    available_sessions: sessionCount,
    available_targets: targets.length,
    browser_marker_counts: countBy(browserMarkers, (row) => row.value),
    threshold: "At least 5 real sessions with held-out evaluation after the G1 stimulus-only baseline.",
    decision: "Do not claim browser-behavior residual value from fixture smoke; collect held-out sessions and compare against G1.",
  };
}

function cameraResidualGate(events: EventEnvelope[], rows: ValidationRow[], sessionCount: number): CameraResidualGate {
  const cameraEvents = events.filter((event) => event.event_type === "camera.feature_window");
  const targets = targetSegmentIds(rows, new Set(rows.filter((row) => row.kind === "stimulus_segment").map((row) => row.target_id)));

  return {
    status: "insufficient-data",
    available_sessions: sessionCount,
    available_targets: targets.length,
    browser_marker_counts: countBy(rows.filter((row) => row.kind === "behavior_marker"), (row) => row.value),
    camera_feature_windows: cameraEvents.length,
    quality_flag_counts: countBy(rows.filter((row) => row.kind === "camera_quality_flag"), (row) => row.value),
    uses_raw_camera_frames: false,
    threshold: "At least 5 real sessions with quality-stratified held-out residual lift after G1 and G2.",
    decision: "Camera features remain weak auxiliary metadata; fixture smoke only proves quality flags can be tabulated.",
  };
}

function repairUtilityGate(rows: ValidationRow[]): RepairUtilityGate {
  const repairRows = rows.filter((row) => row.kind === "repair_outcome");

  return {
    status: "insufficient-data",
    repair_outcome_count: repairRows.length,
    outcome_counts: countBy(repairRows, (row) => row.value),
    threshold: "A/B or within-user comparison of heatmap repair prompts versus no, generic, random, or stale prompts.",
    decision: "Repair outcomes are present as smoke rows, but utility needs a comparison group before keep/drop decisions.",
  };
}

function targetSegmentIds(rows: ValidationRow[], segmentIds: Set<string>): string[] {
  return unique(
    rows
      .filter((row) => verifierKinds.has(row.kind))
      .filter((row) => segmentIds.has(row.target_id))
      .filter(isDifficultyVerifier)
      .map((row) => row.target_id),
  ).sort();
}

function isDifficultyVerifier(row: ValidationRow): boolean {
  if (row.kind === "label") {
    return ["avoiding", "confused-bad", "confused-good", "overloaded", "tired"].includes(row.value);
  }

  if (row.kind === "probe") {
    return ["incorrect", "missed", "partial"].includes(row.value);
  }

  return ["answered", "rated-useful", "rated-not-useful"].includes(row.value);
}

function shuffledSegmentScores(segments: StimulusSegmentRow[]): Array<{ segment_id: string; score: number }> {
  return segments
    .map((segment, index) => {
      const source = segments[(index + segments.length - 1) % segments.length] ?? segment;
      return {
        segment_id: segment.segment_id,
        score: stimulusScore(source),
      };
    })
    .sort((a, b) => b.score - a.score || a.segment_id.localeCompare(b.segment_id));
}

function shiftedBoundaryTargetIds(segments: StimulusSegmentRow[], rows: ValidationRow[]): string[] {
  if (segments.length === 0) {
    return [];
  }

  const averageDuration = average(segments.map((segment) => Math.max(1, segment.end_ms - segment.start_ms)));
  const shifted = segments.map((segment) => ({
    segment_id: segment.segment_id,
    start_ms: segment.start_ms + averageDuration / 2,
    end_ms: segment.end_ms + averageDuration / 2,
  }));

  return unique(
    rows
      .filter((row) => verifierKinds.has(row.kind))
      .filter(isDifficultyVerifier)
      .flatMap((row) => shifted.find((segment) => row.monotonic_ms >= segment.start_ms && row.monotonic_ms < segment.end_ms)?.segment_id ?? []),
  ).sort();
}

function stimulusScore(segment: Pick<StimulusSegmentRow, "density" | "term_novelty" | "transition_count">): number {
  return round(segment.density * 0.66 + segment.term_novelty * 0.22 + Math.min(segment.transition_count, 4) * 0.03);
}

function targetSegmentId(event: EventEnvelope, segments: StimulusSegmentRow[]): string {
  const explicit = safeString(event.payload.target_segment_id, "");
  if (explicit.length > 0) {
    return explicit;
  }

  const segment = segments.find(
    (candidate) =>
      candidate.session_id === event.session_id &&
      event.monotonic_ms >= candidate.start_ms &&
      event.monotonic_ms < candidate.end_ms,
  );
  return segment?.segment_id ?? event.event_id;
}

function row(
  event: EventEnvelope,
  kind: ValidationRowKind,
  targetId: string,
  value: string,
  extras: Pick<ValidationRow, "metrics" | "quality_flags"> = {},
): ValidationRow {
  return {
    kind,
    session_id: event.session_id,
    source_event_id: event.event_id,
    target_id: targetId,
    value,
    monotonic_ms: event.monotonic_ms,
    privacy_class: event.privacy_class,
    smoke: true,
    ...extras,
  };
}

function countBy<T>(values: T[], key: (value: T) => string): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const value of values) {
    const countKey = key(value);
    counts[countKey] = (counts[countKey] ?? 0) + 1;
  }
  return counts;
}

function groupBy<T>(values: T[], key: (value: T) => string): Map<string, T[]> {
  const groups = new Map<string, T[]>();
  for (const value of values) {
    const groupKey = key(value);
    groups.set(groupKey, [...(groups.get(groupKey) ?? []), value]);
  }
  return groups;
}

function maxEntry(counts: Record<string, number>): [string, number] {
  const entries = Object.entries(counts).sort(([leftKey, leftValue], [rightKey, rightValue]) => rightValue - leftValue || leftKey.localeCompare(rightKey));
  return entries[0] ?? ["none", 0];
}

function latestCapturedAt(events: EventEnvelope[]): string {
  return events.reduce((latest, event) => (event.captured_at > latest ? event.captured_at : latest), "") || "unknown";
}

function formatNullableBoolean(value: boolean | null): string {
  if (value === null) {
    return "n/a";
  }

  return value ? "yes" : "no";
}

function average(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }

  return values.reduce((total, value) => total + value, 0) / values.length;
}

function round(value: number): number {
  return Math.round(value * 100) / 100;
}

function unique(values: string[]): string[] {
  return [...new Set(values)];
}

function safeString(value: unknown, fallback: string): string {
  return typeof value === "string" && value.length > 0 ? value : fallback;
}

function safeNumber(value: unknown, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function isEventEnvelopeLike(value: unknown): value is EventEnvelope {
  return (
    isRecord(value) &&
    typeof value.event_id === "string" &&
    typeof value.session_id === "string" &&
    typeof value.event_type === "string" &&
    typeof value.monotonic_ms === "number" &&
    isRecord(value.payload)
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseArgs(args: string[]): { input: string; output: string; markdown: string; run_id: string } {
  const parsed = {
    input: "tests/fixtures/research-session.jsonl",
    output: "research/validation-smoke-report.json",
    markdown: "research/validation-smoke-report.md",
    run_id: "fixture-smoke",
  };

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    const next = args[index + 1];
    if (arg === "--input" && next) {
      parsed.input = next;
      index += 1;
    } else if (arg === "--output" && next) {
      parsed.output = next;
      index += 1;
    } else if (arg === "--markdown" && next) {
      parsed.markdown = next;
      index += 1;
    } else if (arg === "--run-id" && next) {
      parsed.run_id = next;
      index += 1;
    }
  }

  return parsed;
}

if (import.meta.main) {
  const args = parseArgs(Bun.argv.slice(2));
  const input = resolve(args.input);
  const output = resolve(args.output);
  const markdown = resolve(args.markdown);
  const events = parseValidationJsonl(readFileSync(input, "utf8"));
  const report = createValidationReport(events, { run_id: args.run_id });

  mkdirSync(dirname(output), { recursive: true });
  mkdirSync(dirname(markdown), { recursive: true });
  writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`);
  writeFileSync(markdown, renderValidationMarkdown(report));
  console.log(`wrote ${output}`);
  console.log(`wrote ${markdown}`);
}
