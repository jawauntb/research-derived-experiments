import type { EventEnvelope } from "@inquiry/schema";
import { buildEventWindows, numericPayload, stringPayload, type EventWindow } from "./windows";

export type ReplayMarkerKind =
  | "skim-risk"
  | "stuck-loop"
  | "high-load"
  | "copied-passage"
  | "rewind"
  | "tab-churn"
  | "label"
  | "probe";

export type ReplayMarker = {
  marker_id: string;
  session_id: string;
  kind: ReplayMarkerKind;
  start_ms: number;
  end_ms: number;
  confidence: number;
  evidence_event_ids: string[];
  evidence: string[];
  suggested_action: string;
};

export type ReplayMemo = {
  session_id: string;
  markers: ReplayMarker[];
  next_actions: string[];
};

export function buildReplayMarkers(events: EventEnvelope[], windowMs = 30_000): ReplayMarker[] {
  const windows = buildEventWindows(events, windowMs);
  const markers = [
    ...windows.flatMap(markSkimRisk),
    ...windows.flatMap(markHighLoad),
    ...windows.flatMap(markTabChurn),
    ...markStuckLoops(windows),
    ...markCopiedPassages(events),
    ...markRewinds(events),
    ...markLabels(events),
    ...markProbes(events),
  ];

  return markers
    .filter((marker) => marker.evidence_event_ids.length > 0)
    .sort((a, b) => a.start_ms - b.start_ms || b.confidence - a.confidence);
}

export function buildReplayMemo(events: EventEnvelope[], windowMs = 30_000): ReplayMemo {
  const sessionId = events[0]?.session_id ?? "unknown-session";
  const markers = buildReplayMarkers(events, windowMs);
  const nextActions = [
    markers.find((marker) => marker.kind === "stuck-loop")?.suggested_action,
    markers.find((marker) => marker.kind === "high-load")?.suggested_action,
    markers.find((marker) => marker.kind === "skim-risk")?.suggested_action,
  ].filter((value): value is string => typeof value === "string");

  return {
    session_id: sessionId,
    markers,
    next_actions: nextActions.slice(0, 3),
  };
}

function markSkimRisk(window: EventWindow): ReplayMarker[] {
  const scrollEvents = window.events.filter((event) => event.event_type === "browser.scroll");
  const dwellEvents = window.events.filter((event) => event.event_type === "browser.dwell");
  const scrollDistance = sum(scrollEvents.map((event) => Math.abs(numericPayload(event, "delta_y") ?? 0)));
  const dwellMs = sum(dwellEvents.map((event) => numericPayload(event, "dwell_ms") ?? 0));

  if (scrollDistance < 2400 || dwellMs > 6000) {
    return [];
  }

  return [
    marker(window, "skim-risk", 0.72, [...scrollEvents, ...dwellEvents], [
      `High scroll distance (${Math.round(scrollDistance)}px) with low dwell (${Math.round(dwellMs)}ms).`,
    ], "Return to the fastest-scrolled section and write one recall question."),
  ];
}

function markHighLoad(window: EventWindow): ReplayMarker[] {
  const cameraEvents = window.events.filter((event) => event.event_type === "camera.feature_window");
  const typingEvents = window.events.filter((event) => event.event_type === "browser.typing_metrics");
  const gazeAway = average(cameraEvents.map((event) => numericPayload(event, "gaze_away_ratio")).filter(isNumber));
  const pauseMs = average(typingEvents.map((event) => numericPayload(event, "pause_ms")).filter(isNumber));
  const qualityOk = cameraEvents.every((event) => !event.quality_flags.includes("low-light") && !event.quality_flags.includes("face-missing"));

  if (!qualityOk || (gazeAway < 0.45 && pauseMs < 1800)) {
    return [];
  }

  return [
    marker(window, "high-load", 0.68, [...cameraEvents, ...typingEvents], [
      `Gaze-away ratio ${gazeAway.toFixed(2)} and typing pause average ${Math.round(pauseMs)}ms.`,
    ], "Pause and restate the current claim in one sentence before continuing."),
  ];
}

function markTabChurn(window: EventWindow): ReplayMarker[] {
  const tabEvents = window.events.filter((event) => event.event_type === "browser.tab");
  if (tabEvents.length < 4) {
    return [];
  }

  return [
    marker(window, "tab-churn", 0.7, tabEvents, [`${tabEvents.length} tab changes in this window.`], "Pick one branch to either close or promote to a follow-up note."),
  ];
}

function markStuckLoops(windows: EventWindow[]): ReplayMarker[] {
  const markers: ReplayMarker[] = [];
  for (const window of windows) {
    const revisitEvents = window.events.filter((event) => event.event_type === "browser.visibility" && stringPayload(event, "state") === "revisited");
    const seekEvents = window.events.filter((event) => event.event_type === "browser.media" && stringPayload(event, "action") === "seeked");
    if (revisitEvents.length + seekEvents.length < 3) {
      continue;
    }

    markers.push(
      marker(window, "stuck-loop", 0.76, [...revisitEvents, ...seekEvents], [
        `${revisitEvents.length} revisits and ${seekEvents.length} media seeks in one window.`,
      ], "Mark the confusing span and ask what prerequisite is missing."),
    );
  }
  return markers;
}

function markCopiedPassages(events: EventEnvelope[]): ReplayMarker[] {
  return events
    .filter((event) => event.event_type === "browser.copy" || event.event_type === "browser.highlight")
    .map((event) => eventMarker(event, "copied-passage", 0.82, "Copied or highlighted passage.", "Attach a note explaining why this passage mattered."));
}

function markRewinds(events: EventEnvelope[]): ReplayMarker[] {
  return events
    .filter((event) => event.event_type === "browser.media" && stringPayload(event, "action") === "seeked" && (numericPayload(event, "delta_ms") ?? 0) < 0)
    .map((event) => eventMarker(event, "rewind", 0.74, "Media rewind detected.", "Replay this segment and answer a recall check."));
}

function markLabels(events: EventEnvelope[]): ReplayMarker[] {
  return events
    .filter((event) => event.event_type === "label.added")
    .map((event) => eventMarker(event, "label", event.confidence, `User label: ${stringPayload(event, "label") ?? "unknown"}.`, "Compare this label with the surrounding evidence."));
}

function markProbes(events: EventEnvelope[]): ReplayMarker[] {
  return events
    .filter((event) => event.event_type === "probe.answered")
    .map((event) => eventMarker(event, "probe", event.confidence, "Recall probe answered.", "Use this answer as verifier evidence for the segment."));
}

function marker(
  window: EventWindow,
  kind: ReplayMarkerKind,
  confidence: number,
  evidenceEvents: EventEnvelope[],
  evidence: string[],
  suggestedAction: string,
): ReplayMarker {
  return {
    marker_id: `${kind}:${window.session_id}:${window.start_ms}`,
    session_id: window.session_id,
    kind,
    start_ms: window.start_ms,
    end_ms: window.end_ms,
    confidence,
    evidence_event_ids: evidenceEvents.map((event) => event.event_id),
    evidence,
    suggested_action: suggestedAction,
  };
}

function eventMarker(
  event: EventEnvelope,
  kind: ReplayMarkerKind,
  confidence: number,
  evidence: string,
  suggestedAction: string,
): ReplayMarker {
  return {
    marker_id: `${kind}:${event.event_id}`,
    session_id: event.session_id,
    kind,
    start_ms: event.monotonic_ms,
    end_ms: event.monotonic_ms,
    confidence,
    evidence_event_ids: [event.event_id],
    evidence: [evidence],
    suggested_action: suggestedAction,
  };
}

function sum(values: number[]): number {
  return values.reduce((total, value) => total + value, 0);
}

function average(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }

  return sum(values) / values.length;
}

function isNumber(value: number | null): value is number {
  return typeof value === "number";
}
