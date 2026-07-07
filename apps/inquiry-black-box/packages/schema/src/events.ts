import {
  assertNoBlockedPayload,
  isPrivacyClass,
  isRetentionPolicy,
  type PrivacyClass,
  type RetentionPolicy,
} from "./privacy";

export const eventSources = [
  "browser",
  "desktop-camera",
  "desktop-hotkey",
  "desktop-system",
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
  "session.started",
  "session.paused",
  "session.resumed",
  "session.stopped",
  "label.added",
  "probe.requested",
  "probe.answered",
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
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
