import type { EventEnvelope } from "@inquiry/schema";
import { buildCopiedSelectionEpisodes, buildEvidenceEpisodes, type EvidenceEpisode } from "./episodes";
import { buildComprehensionHeatmap, type ComprehensionHeatmapSegment } from "./heatmap";
import type { StimulusSegment } from "./stimulus";
import { buildEventWindows, numericPayload, stringPayload, type EventWindow } from "./windows";

export type ReplayMarkerKind =
  | "skim-risk"
  | "stuck-loop"
  | "high-load"
  | "copied-passage"
  | "rewind"
  | "tab-churn"
  | "app-churn"
  | "off-browser-focus"
  | "deep-work-span"
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
  episodes: EvidenceEpisode[];
  heatmap: ComprehensionHeatmapSegment[];
  next_actions: string[];
};

export type ReplayMemoOptions = {
  window_ms?: number;
  stimulus_segments?: StimulusSegment[];
  stimulusSegments?: StimulusSegment[];
};

export function buildReplayMarkers(events: EventEnvelope[], windowMs = 30_000): ReplayMarker[] {
  const windows = buildEventWindows(events, windowMs);
  const markers = [
    ...windows.flatMap(markSkimRisk),
    ...windows.flatMap(markHighLoad),
    ...windows.flatMap(markTabChurn),
    ...windows.flatMap(markAppChurn),
    ...markStuckLoops(windows),
    ...markDesktopFocus(events),
    ...markCopiedPassages(events),
    ...markRewinds(events),
    ...markLabels(events),
    ...markProbes(events),
  ];

  return markers
    .filter((marker) => marker.evidence_event_ids.length > 0)
    .sort((a, b) => a.start_ms - b.start_ms || b.confidence - a.confidence);
}

export function buildReplayMemo(events: EventEnvelope[], options: number | ReplayMemoOptions = {}): ReplayMemo {
  const windowMs = typeof options === "number" ? options : options.window_ms ?? 30_000;
  const stimulusSegments = typeof options === "number" ? [] : options.stimulus_segments ?? options.stimulusSegments ?? [];
  const sessionId = events[0]?.session_id ?? "unknown-session";
  const markers = buildReplayMarkers(events, windowMs);
  const episodes = buildEvidenceEpisodes(events, markers);
  const heatmap = buildComprehensionHeatmap({
    session_id: sessionId,
    markers,
    stimulus_segments: stimulusSegments,
  });
  const nextActions = [
    markers.find((marker) => marker.kind === "stuck-loop")?.suggested_action,
    markers.find((marker) => marker.kind === "high-load")?.suggested_action,
    markers.find((marker) => marker.kind === "app-churn")?.suggested_action,
    markers.find((marker) => marker.kind === "deep-work-span")?.suggested_action,
    markers.find((marker) => marker.kind === "off-browser-focus")?.suggested_action,
    heatmap.find((segment) => segment.kind === "mixed-load" || segment.kind === "intrinsic-difficulty")?.suggested_repair,
    markers.find((marker) => marker.kind === "skim-risk")?.suggested_action,
  ].filter((value): value is string => typeof value === "string");

  return {
    session_id: sessionId,
    markers,
    episodes,
    heatmap,
    next_actions: nextActions.slice(0, 3),
  };
}

function markSkimRisk(window: EventWindow): ReplayMarker[] {
  const scrollEvents = window.events.filter((event) => event.event_type === "browser.scroll");
  const dwellEvents = window.events.filter(
    (event) => event.event_type === "browser.dwell" || event.event_type === "browser.visibility",
  );
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

function markAppChurn(window: EventWindow): ReplayMarker[] {
  const desktopEvents = window.events.filter(isDesktopFocusEvent);
  const appNames = desktopEvents.map((event) => stringPayload(event, "app_name")).filter(isString);
  const uniqueApps = unique(appNames);
  const adjacentChanges = appNames.filter((appName, index) => index > 0 && appName !== appNames[index - 1]).length;
  if (desktopEvents.length < 4 || uniqueApps.length < 3 || adjacentChanges < 3) {
    return [];
  }

  return [
    marker(
      window,
      "app-churn",
      0.66,
      desktopEvents,
      [`Foreground app context changed ${adjacentChanges} times across ${uniqueApps.slice(0, 4).join(", ")}.`],
      "Choose which app/task branch should become a follow-up note, and close the rest.",
    ),
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

function markDesktopFocus(events: EventEnvelope[]): ReplayMarker[] {
  const ordered = [...events].sort((a, b) => a.monotonic_ms - b.monotonic_ms);
  const browserEvents = ordered.filter((event) => event.source === "browser");
  const focusEvents = ordered.filter(isDesktopFocusEvent);
  const deepWorkEventIds = new Set<string>();
  const markers: ReplayMarker[] = [];

  for (const event of focusEvents) {
    const appName = stringPayload(event, "app_name");
    const durationMs = numericPayload(event, "duration_ms") ?? 0;
    if (!appName || isBrowserAppName(appName) || durationMs < 180_000) {
      continue;
    }

    const startedAt = numericPayload(event, "focus_started_monotonic_ms") ?? event.monotonic_ms;
    const endedAt = numericPayload(event, "focus_ended_monotonic_ms") ?? event.monotonic_ms;
    const recentBrowserEvent = lastEventAtOrBefore(browserEvents, startedAt);
    const hasRecentBrowserContext = recentBrowserEvent !== undefined && startedAt - recentBrowserEvent.monotonic_ms <= 10 * 60_000;
    if (durationMs >= 600_000 && (isDeepWorkAppName(appName) || hasRecentBrowserContext)) {
      const evidenceEvents = recentBrowserEvent ? [recentBrowserEvent, event] : [event];
      markers.push(
        spanMarker({
          event,
          kind: "deep-work-span",
          confidence: 0.64,
          start_ms: startedAt,
          end_ms: endedAt,
          evidenceEvents,
          evidence: [`${appName} held foreground for ${formatMinutes(durationMs)} after browser-context evidence.`],
          suggestedAction: "Summarize what the non-browser work block produced, then decide what should return to notes or browser research.",
        }),
      );
      deepWorkEventIds.add(event.event_id);
    }
  }

  for (const event of focusEvents) {
    if (deepWorkEventIds.has(event.event_id)) {
      continue;
    }

    const appName = stringPayload(event, "app_name");
    const durationMs = numericPayload(event, "duration_ms") ?? 0;
    if (!appName || isBrowserAppName(appName) || durationMs < 180_000) {
      continue;
    }

    markers.push(
      spanMarker({
        event,
        kind: "off-browser-focus",
        confidence: 0.58,
        start_ms: numericPayload(event, "focus_started_monotonic_ms") ?? event.monotonic_ms,
        end_ms: numericPayload(event, "focus_ended_monotonic_ms") ?? event.monotonic_ms,
        evidenceEvents: [event],
        evidence: [`${appName} held foreground outside the browser for ${formatMinutes(durationMs)}.`],
        suggestedAction: "Name what happened in this app block and whether it should become a follow-up note.",
      }),
    );
  }

  return markers;
}

function markCopiedPassages(events: EventEnvelope[]): ReplayMarker[] {
  return buildCopiedSelectionEpisodes(events).map((episode) => ({
    marker_id: `copied-passage:${episode.episode_id}`,
    session_id: episode.session_id,
    kind: "copied-passage",
    start_ms: episode.start_ms,
    end_ms: episode.end_ms,
    confidence: episode.confidence,
    evidence_event_ids: episode.evidence_event_ids,
    evidence: [episode.summary, ...episode.details, episode.privacy_note],
    suggested_action: "Explain what this selected or copied evidence was preserving.",
  }));
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

function spanMarker(input: {
  event: EventEnvelope;
  kind: ReplayMarkerKind;
  confidence: number;
  start_ms: number;
  end_ms: number;
  evidenceEvents: EventEnvelope[];
  evidence: string[];
  suggestedAction: string;
}): ReplayMarker {
  return {
    marker_id: `${input.kind}:${input.event.event_id}`,
    session_id: input.event.session_id,
    kind: input.kind,
    start_ms: input.start_ms,
    end_ms: input.end_ms,
    confidence: input.confidence,
    evidence_event_ids: input.evidenceEvents.map((event) => event.event_id),
    evidence: input.evidence,
    suggested_action: input.suggestedAction,
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

function isString(value: string | null): value is string {
  return typeof value === "string" && value.length > 0;
}

function isDesktopFocusEvent(event: EventEnvelope): boolean {
  return event.event_type === "desktop.app_focus" || event.event_type === "desktop.window_focus";
}

function isBrowserAppName(appName: string): boolean {
  return /chrome|safari|firefox|edge|brave|arc/i.test(appName);
}

function isDeepWorkAppName(appName: string): boolean {
  return /cursor|terminal|iterm|visual studio code|xcode|preview|figma|obsidian|notes/i.test(appName);
}

function unique(values: string[]): string[] {
  return [...new Set(values)];
}

function formatMinutes(durationMs: number): string {
  const minutes = durationMs / 60_000;
  return `${minutes.toFixed(minutes >= 10 ? 0 : 1)}m`;
}

function lastEventAtOrBefore(events: EventEnvelope[], monotonicMs: number): EventEnvelope | undefined {
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const event = events[index];
    if (event && event.monotonic_ms <= monotonicMs) {
      return event;
    }
  }

  return undefined;
}
