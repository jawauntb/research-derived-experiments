import {
  assertNoBlockedPayload,
  findSensitiveFieldPaths,
  isPrivacyClass,
  isRetentionPolicy,
  normalizeSensitiveFieldName,
  rawTextPayloadFieldNames,
  selectedTextPayloadFieldNames,
  type PrivacyClass,
  type RetentionPolicy,
} from "./privacy";

export const eventSources = [
  "browser",
  "desktop-camera",
  "desktop-activity",
  "desktop-hotkey",
  "desktop-system",
  "stimulus",
  "user",
  "cloud",
  "modal",
] as const;

export type EventSource = (typeof eventSources)[number];

export const eventTypes = [
  "browser.scroll",
  "browser.dwell",
  "browser.visibility",
  "browser.tab",
  "browser.media",
  "browser.selection",
  "browser.copy",
  "browser.highlight",
  "browser.typing_metrics",
  "camera.feature_window",
  "desktop.app_focus",
  "desktop.window_focus",
  "session.started",
  "session.paused",
  "session.resumed",
  "session.stopped",
  "label.added",
  "probe.requested",
  "probe.answered",
  "stimulus.attached",
  "stimulus.segmented",
  "repair.candidate",
  "repair.outcome",
  "notification.candidate",
  "notification.delivered",
  "notification.responded",
  "report.generated",
  "sync.queued",
  "model.run",
] as const;

export type EventType = (typeof eventTypes)[number];

export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };
export type JsonObject = { [key: string]: JsonValue };

export type EventEnvelope<TPayload extends JsonObject = JsonObject> = {
  event_id: string;
  session_id: string;
  source: EventSource;
  source_version: string;
  captured_at: string;
  monotonic_ms: number;
  timezone: string;
  event_type: EventType;
  confidence: number;
  quality_flags: string[];
  payload: TPayload;
  privacy_class: PrivacyClass;
  retention_policy: RetentionPolicy;
};

export type BrowserTypingMetricsPayload = JsonObject & {
  field_role: string;
  burst_length: number;
  pause_ms: number;
  backspace_count: number;
  edit_churn: number;
};

export type CameraFeaturePayload = JsonObject & {
  window_ms: number;
  face_present_ratio: number;
  gaze_away_ratio: number;
  blink_proxy: number;
  head_pose_variance: number;
  motion_score: number;
};

export const desktopPermissionStatuses = ["not_requested", "granted", "denied", "unavailable"] as const;

export type DesktopPermissionStatus = (typeof desktopPermissionStatuses)[number];

export type DesktopAppFocusPayload = JsonObject & {
  app_name: string;
  bundle_id?: string;
  pid_hash?: string;
  focus_started_monotonic_ms: number;
  focus_ended_monotonic_ms?: number;
  duration_ms?: number;
  permission_status: DesktopPermissionStatus;
};

export type DesktopWindowFocusPayload = DesktopAppFocusPayload & {
  window_id_hash?: string;
  window_title?: string;
  title_truncated?: boolean;
};

export type LabelPayload = JsonObject & {
  label:
    | "flow"
    | "overloaded"
    | "confused-good"
    | "confused-bad"
    | "avoiding"
    | "near-breakthrough"
    | "tired";
  note?: string;
};

export type StimulusSource = "article" | "transcript" | "manual" | "pdf-text" | "video-note";

export type StimulusAttachedPayload = JsonObject & {
  stimulus_id: string;
  source: StimulusSource;
  content_ref: string;
  document_opt_in: boolean;
  title?: string;
  duration_ms?: number;
};

export type StimulusSegmentedPayload = JsonObject & {
  stimulus_id: string;
  segment_ids: string[];
  segment_count: number;
  content_refs: string[];
};

export type RepairAction =
  | "restate-claim"
  | "missing-prerequisite"
  | "rewatch-span"
  | "recall-question"
  | "explain-copied-passage"
  | "follow-up-note";

export type RepairCandidatePayload = JsonObject & {
  repair_id: string;
  heatmap_id: string;
  action: RepairAction;
  prompt: string;
  start_ms: number;
  end_ms: number;
  source_kind: string;
  source_marker_ids: string[];
  evidence_event_ids: string[];
  limitation: string;
};

export type RepairOutcomePayload = JsonObject & {
  repair_id: string;
  heatmap_id: string;
  outcome: "accepted" | "answered" | "dismissed" | "snoozed" | "rated-useful" | "rated-not-useful";
  action: RepairAction;
  probe_id?: string;
  answer?: string;
  answer_confidence?: number;
  reason?: string;
};

export function createEvent<TPayload extends JsonObject>(
  event: Omit<EventEnvelope<TPayload>, "event_id" | "captured_at" | "timezone" | "confidence" | "quality_flags"> &
    Partial<Pick<EventEnvelope<TPayload>, "event_id" | "captured_at" | "timezone" | "confidence" | "quality_flags">>,
): EventEnvelope<TPayload> {
  const envelope: EventEnvelope<TPayload> = {
    event_id: event.event_id ?? crypto.randomUUID(),
    session_id: event.session_id,
    source: event.source,
    source_version: event.source_version,
    captured_at: event.captured_at ?? new Date().toISOString(),
    monotonic_ms: event.monotonic_ms,
    timezone: event.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone,
    event_type: event.event_type,
    confidence: event.confidence ?? 1,
    quality_flags: event.quality_flags ?? [],
    payload: event.payload,
    privacy_class: event.privacy_class,
    retention_policy: event.retention_policy,
  };

  validateEvent(envelope);
  return envelope;
}

export function isEventSource(value: unknown): value is EventSource {
  return typeof value === "string" && eventSources.includes(value as EventSource);
}

export function isEventType(value: unknown): value is EventType {
  return typeof value === "string" && eventTypes.includes(value as EventType);
}

export function validateEvent(value: unknown): asserts value is EventEnvelope {
  if (!isRecord(value)) {
    throw new Error("event must be an object");
  }

  const requiredStrings = ["event_id", "session_id", "source_version", "captured_at", "timezone"] as const;
  for (const key of requiredStrings) {
    if (typeof value[key] !== "string" || value[key].length === 0) {
      throw new Error(`event.${key} must be a non-empty string`);
    }
  }

  if (!isEventSource(value.source)) {
    throw new Error("event.source is unsupported");
  }

  if (!isEventType(value.event_type)) {
    throw new Error("event.event_type is unsupported");
  }

  if (typeof value.monotonic_ms !== "number" || !Number.isFinite(value.monotonic_ms) || value.monotonic_ms < 0) {
    throw new Error("event.monotonic_ms must be a non-negative number");
  }

  if (typeof value.confidence !== "number" || value.confidence < 0 || value.confidence > 1) {
    throw new Error("event.confidence must be between 0 and 1");
  }

  if (!Array.isArray(value.quality_flags) || !value.quality_flags.every((flag) => typeof flag === "string")) {
    throw new Error("event.quality_flags must be a string array");
  }

  if (!isRecord(value.payload)) {
    throw new Error("event.payload must be an object");
  }

  if (!isPrivacyClass(value.privacy_class)) {
    throw new Error("event.privacy_class is unsupported");
  }

  if (!isRetentionPolicy(value.retention_policy)) {
    throw new Error("event.retention_policy is unsupported");
  }

  assertNoBlockedPayload(value.payload);
  assertStimulusTextOptIn(value as EventEnvelope);
  assertBrowserSelectedTextOptIn(value as EventEnvelope);
  assertDesktopWindowTitleOptIn(value as EventEnvelope);
  assertDesktopActivityPayloadShape(value as EventEnvelope);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

const desktopWindowTitleFieldNames = ["window_title", "windowTitle", "window-title"] as const;
const desktopActivityAllowedPayloadKeys: ReadonlySet<string> = new Set([
  "app_name",
  "bundle_id",
  "pid_hash",
  "focus_started_monotonic_ms",
  "focus_ended_monotonic_ms",
  "duration_ms",
  "permission_status",
  "window_id_hash",
  "window_title",
  "title_truncated",
]);

function assertStimulusTextOptIn(event: EventEnvelope): void {
  if (!event.event_type.startsWith("stimulus.") || event.privacy_class === "document-opt-in") {
    return;
  }

  const present = findSensitiveFieldPaths(event.payload, {
    extraFieldNames: rawTextPayloadFieldNames,
    normalizeFieldName: normalizeSensitiveFieldName,
  });
  if (present.length > 0) {
    throw new Error(`stimulus text requires document-opt-in: ${present.join(", ")}`);
  }
}

function assertBrowserSelectedTextOptIn(event: EventEnvelope): void {
  if (!isBrowserSelectionTextEvent(event.event_type) || event.privacy_class === "document-opt-in") {
    return;
  }

  const present = findSensitiveFieldPaths(event.payload, {
    extraFieldNames: selectedTextPayloadFieldNames,
    normalizeFieldName: normalizeSensitiveFieldName,
  });
  if (present.length > 0) {
    throw new Error(`browser selected text requires document-opt-in: ${present.join(", ")}`);
  }
}

function isBrowserSelectionTextEvent(eventType: EventType): boolean {
  return eventType === "browser.selection" || eventType === "browser.copy" || eventType === "browser.highlight";
}

function assertDesktopWindowTitleOptIn(event: EventEnvelope): void {
  if (event.event_type !== "desktop.window_focus" || event.privacy_class === "document-opt-in") {
    return;
  }

  const present = findDesktopWindowTitleFieldPaths(event.payload);
  if (present.length > 0) {
    throw new Error(`desktop window titles require document-opt-in: ${present.join(", ")}`);
  }
}

export function findDesktopWindowTitleFieldPaths(value: unknown): string[] {
  return findSensitiveFieldPaths(value, {
    extraFieldNames: desktopWindowTitleFieldNames,
    normalizeFieldName: normalizeSensitiveFieldName,
  });
}

function assertDesktopActivityPayloadShape(event: EventEnvelope): void {
  if (event.event_type !== "desktop.app_focus" && event.event_type !== "desktop.window_focus") {
    return;
  }

  if (event.source !== "desktop-activity") {
    throw new Error("desktop activity events must use desktop-activity source");
  }

  const payload = event.payload;
  for (const key of Object.keys(payload)) {
    if (!desktopActivityAllowedPayloadKeys.has(key)) {
      throw new Error(`desktop activity payload contains unsupported field: ${key}`);
    }
  }

  if (typeof payload.app_name !== "string" || payload.app_name.length === 0) {
    throw new Error("desktop activity payload.app_name must be a non-empty string");
  }

  if (!desktopPermissionStatuses.includes(payload.permission_status as DesktopPermissionStatus)) {
    throw new Error("desktop activity payload.permission_status is unsupported");
  }

  assertFiniteNonNegative(payload.focus_started_monotonic_ms, "desktop activity payload.focus_started_monotonic_ms");
  assertFiniteNonNegative(payload.focus_ended_monotonic_ms, "desktop activity payload.focus_ended_monotonic_ms");
  assertFiniteNonNegative(payload.duration_ms, "desktop activity payload.duration_ms");

  const startedMs = payload.focus_started_monotonic_ms as number;
  const endedMs = payload.focus_ended_monotonic_ms as number;
  const durationMs = payload.duration_ms as number;
  if (endedMs < startedMs) {
    throw new Error("desktop activity payload.focus_ended_monotonic_ms must be at or after focus_started_monotonic_ms");
  }
  if (durationMs !== endedMs - startedMs) {
    throw new Error("desktop activity payload.duration_ms must match focus span length");
  }

  for (const key of ["bundle_id", "pid_hash", "window_id_hash"] as const) {
    if (payload[key] !== undefined && (typeof payload[key] !== "string" || payload[key].length === 0)) {
      throw new Error(`desktop activity payload.${key} must be a non-empty string when present`);
    }
  }

  const titlePaths = findDesktopWindowTitleFieldPaths(payload);
  if (event.event_type === "desktop.app_focus" && titlePaths.length > 0) {
    throw new Error(`desktop.app_focus must not include window title fields: ${titlePaths.join(", ")}`);
  }

  if (payload.window_title !== undefined) {
    if (event.event_type !== "desktop.window_focus") {
      throw new Error("desktop window title payloads must use desktop.window_focus");
    }
    if (typeof payload.window_title !== "string" || payload.window_title.length === 0 || payload.window_title.length > 120) {
      throw new Error("desktop activity payload.window_title must be a 1-120 character string");
    }
  }

  if (payload.title_truncated !== undefined && typeof payload.title_truncated !== "boolean") {
    throw new Error("desktop activity payload.title_truncated must be a boolean when present");
  }
}

function assertFiniteNonNegative(value: unknown, field: string): asserts value is number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    throw new Error(`${field} must be a non-negative number`);
  }
}
