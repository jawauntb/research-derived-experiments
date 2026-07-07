import type { EventEnvelope, JsonValue } from "@inquiry/schema";

export type EventWindow = {
  session_id: string;
  start_ms: number;
  end_ms: number;
  event_ids: string[];
  events: EventEnvelope[];
};

export function buildEventWindows(events: EventEnvelope[], windowMs: number): EventWindow[] {
  if (windowMs <= 0) {
    throw new Error("windowMs must be greater than zero");
  }

  const ordered = [...events].sort((a, b) => a.monotonic_ms - b.monotonic_ms);
  const windows = new Map<string, EventWindow>();

  for (const event of ordered) {
    const bucketStart = Math.floor(event.monotonic_ms / windowMs) * windowMs;
    const key = `${event.session_id}:${bucketStart}`;
    const existing =
      windows.get(key) ??
      ({
        session_id: event.session_id,
        start_ms: bucketStart,
        end_ms: bucketStart + windowMs,
        event_ids: [],
        events: [],
      } satisfies EventWindow);

    existing.event_ids.push(event.event_id);
    existing.events.push(event);
    windows.set(key, existing);
  }

  return [...windows.values()].sort((a, b) => a.start_ms - b.start_ms);
}

export function numericPayload(event: EventEnvelope, key: string): number | null {
  const value: JsonValue | undefined = event.payload[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function stringPayload(event: EventEnvelope, key: string): string | null {
  const value: JsonValue | undefined = event.payload[key];
  return typeof value === "string" ? value : null;
}
