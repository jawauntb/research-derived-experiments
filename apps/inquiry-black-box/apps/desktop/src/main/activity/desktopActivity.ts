import { createHash } from "node:crypto";
import {
  createEvent,
  type DesktopAppFocusPayload,
  type DesktopPermissionStatus,
  type DesktopWindowFocusPayload,
  type EventEnvelope,
} from "@inquiry/schema";

export type DesktopActivitySnapshot = {
  app_name: string;
  bundle_id?: string;
  process_id?: number;
  window_id?: string;
  window_title?: string;
  permission_status: DesktopPermissionStatus;
};

export type DesktopActivityProvider = {
  permissionStatus: () => Promise<DesktopPermissionStatus> | DesktopPermissionStatus;
  foregroundActivity: (input: {
    includeWindowTitle: boolean;
  }) => Promise<DesktopActivitySnapshot | null> | DesktopActivitySnapshot | null;
};

export type DesktopActivitySettings = {
  enabled: boolean;
  includeWindowTitles: boolean;
};

export type DesktopActivityStatus = {
  enabled: boolean;
  includeWindowTitles: boolean;
  active: boolean;
  permission_status: DesktopPermissionStatus;
  last_heartbeat_monotonic_ms?: number;
  last_app_name?: string;
  last_error?: string;
};

export type DesktopActivityClock = {
  nowMs: () => number;
  nowIso: () => string;
};

export type DesktopActivityCollectorOptions = {
  provider: DesktopActivityProvider;
  appendEvent: (event: EventEnvelope) => EventEnvelope;
  canCapture?: (session_id: string) => boolean;
  clock?: Partial<DesktopActivityClock>;
  pollIntervalMs?: number;
  autoPoll?: boolean;
};

export type DesktopActivityCollector = {
  configure: (settings: DesktopActivitySettings) => void;
  start: (input: { session_id: string }) => void;
  tick: () => Promise<EventEnvelope | null>;
  stop: () => EventEnvelope | null;
  status: () => DesktopActivityStatus;
};

type FocusSpan = {
  session_id: string;
  snapshot: DesktopActivitySnapshot;
  started_ms: number;
};

const defaultClock: DesktopActivityClock = {
  nowMs: () => Date.now(),
  nowIso: () => new Date().toISOString(),
};

export function createDesktopActivityCollector(options: DesktopActivityCollectorOptions): DesktopActivityCollector {
  const clock: DesktopActivityClock = { ...defaultClock, ...options.clock };
  const pollIntervalMs = options.pollIntervalMs ?? 1_500;
  const autoPoll = options.autoPoll ?? true;
  let settings: DesktopActivitySettings = { enabled: false, includeWindowTitles: false };
  let sessionId: string | null = null;
  let activeSpan: FocusSpan | null = null;
  let interval: ReturnType<typeof setInterval> | null = null;
  let permissionStatus: DesktopPermissionStatus = "not_requested";
  let lastHeartbeatMs: number | undefined;
  let lastAppName: string | undefined;
  let lastError: string | undefined;
  let tickInFlight: Promise<EventEnvelope | null> | null = null;
  let revision = 0;

  function status(): DesktopActivityStatus {
    return {
      enabled: settings.enabled,
      includeWindowTitles: settings.includeWindowTitles,
      active: sessionId !== null,
      permission_status: permissionStatus,
      ...(lastHeartbeatMs === undefined ? {} : { last_heartbeat_monotonic_ms: lastHeartbeatMs }),
      ...(lastAppName === undefined ? {} : { last_app_name: lastAppName }),
      ...(lastError === undefined ? {} : { last_error: lastError }),
    };
  }

  function canCapture(session_id: string): boolean {
    return options.canCapture ? options.canCapture(session_id) : true;
  }

  function clearLastCaptureStatus(): void {
    permissionStatus = "not_requested";
    lastHeartbeatMs = undefined;
    lastAppName = undefined;
    lastError = undefined;
  }

  function clearTimer(): void {
    if (interval) {
      clearInterval(interval);
      interval = null;
    }
  }

  function ensureTimer(): void {
    if (!autoPoll || !sessionId || interval) {
      return;
    }

    interval = setInterval(() => {
      void tick();
    }, pollIntervalMs);
  }

  async function tick(): Promise<EventEnvelope | null> {
    if (tickInFlight) {
      return tickInFlight;
    }

    tickInFlight = runTick()
      .catch((error: unknown) => {
        lastError = error instanceof Error ? error.message : "desktop activity polling failed";
        try {
          flush(clock.nowMs());
        } catch {
          // Status carries the polling failure; repeated append failures should not crash Electron main.
        }
        return null;
      })
      .finally(() => {
        tickInFlight = null;
      });

    return tickInFlight;
  }

  async function runTick(): Promise<EventEnvelope | null> {
    const startedSessionId = sessionId;
    const startedSettings = { ...settings };
    const startedRevision = revision;
    if (!startedSessionId || !startedSettings.enabled || !canCapture(startedSessionId)) {
      return null;
    }

    const snapshot = await options.provider.foregroundActivity({
      includeWindowTitle: startedSettings.includeWindowTitles,
    });
    if (!isCurrentTick(startedSessionId, startedRevision) || !canCapture(startedSessionId)) {
      return null;
    }

    const now = clock.nowMs();
    if (!snapshot) {
      permissionStatus = await options.provider.permissionStatus();
      if (!isCurrentTick(startedSessionId, startedRevision) || !canCapture(startedSessionId)) {
        return null;
      }
      const flushed = flush(now);
      lastHeartbeatMs = undefined;
      lastAppName = undefined;
      return null;
    }

    permissionStatus = snapshot.permission_status;
    if (permissionStatus !== "granted") {
      lastHeartbeatMs = undefined;
      lastAppName = undefined;
      return flush(now);
    }

    lastError = undefined;
    lastHeartbeatMs = now;
    lastAppName = snapshot.app_name;

    if (activeSpan && sameFocus(activeSpan.snapshot, snapshot, startedSettings.includeWindowTitles)) {
      return null;
    }

    const flushed = flush(now);
    activeSpan = {
      session_id: startedSessionId,
      snapshot: sanitizeSnapshot(snapshot, startedSettings.includeWindowTitles),
      started_ms: now,
    };
    return flushed;
  }

  function isCurrentTick(startedSessionId: string, startedRevision: number): boolean {
    return revision === startedRevision && sessionId === startedSessionId && settings.enabled;
  }

  function flush(endMs: number): EventEnvelope | null {
    if (!activeSpan) {
      return null;
    }

    const span = activeSpan;
    activeSpan = null;
    if (!canCapture(span.session_id)) {
      return null;
    }

    const durationMs = Math.max(0, endMs - span.started_ms);
    const payload = createFocusPayload(span.snapshot, span.started_ms, endMs, durationMs, settings.includeWindowTitles);
    const hasWindowTitle = "window_title" in payload && typeof payload.window_title === "string";
    const event = createEvent({
      session_id: span.session_id,
      source: "desktop-activity",
      source_version: "desktop@0.1.0",
      captured_at: clock.nowIso(),
      monotonic_ms: endMs,
      event_type: hasWindowTitle ? "desktop.window_focus" : "desktop.app_focus",
      payload,
      privacy_class: hasWindowTitle ? "document-opt-in" : "local-derived",
      retention_policy: hasWindowTitle ? "session-delete" : "local-default",
    });
    return options.appendEvent(event);
  }

  return {
    configure(nextSettings) {
      revision += 1;
      if (!nextSettings.enabled) {
        clearTimer();
        flush(clock.nowMs());
        sessionId = null;
        clearLastCaptureStatus();
      }
      settings = {
        enabled: nextSettings.enabled,
        includeWindowTitles: nextSettings.enabled && nextSettings.includeWindowTitles,
      };
    },
    start(input) {
      if (!settings.enabled) {
        return;
      }

      revision += 1;
      sessionId = input.session_id;
      ensureTimer();
    },
    tick,
    stop() {
      revision += 1;
      clearTimer();
      const event = flush(clock.nowMs());
      sessionId = null;
      clearLastCaptureStatus();
      return event;
    },
    status,
  };
}

function createFocusPayload(
  snapshot: DesktopActivitySnapshot,
  startedMs: number,
  endedMs: number,
  durationMs: number,
  includeWindowTitle: boolean,
): DesktopAppFocusPayload | DesktopWindowFocusPayload {
  const base: DesktopAppFocusPayload = {
    app_name: snapshot.app_name,
    focus_started_monotonic_ms: startedMs,
    focus_ended_monotonic_ms: endedMs,
    duration_ms: durationMs,
    permission_status: snapshot.permission_status,
  };
  if (snapshot.bundle_id) {
    base.bundle_id = snapshot.bundle_id;
  }
  if (snapshot.process_id !== undefined) {
    base.pid_hash = hashIdentifier("pid", String(snapshot.process_id));
  }

  if (!includeWindowTitle || !snapshot.window_title) {
    return base;
  }

  const boundedTitle = boundWindowTitle(snapshot.window_title);
  return {
    ...base,
    ...(snapshot.window_id ? { window_id_hash: hashIdentifier("window", snapshot.window_id) } : {}),
    window_title: boundedTitle.title,
    title_truncated: boundedTitle.truncated,
  };
}

function sanitizeSnapshot(snapshot: DesktopActivitySnapshot, includeWindowTitle: boolean): DesktopActivitySnapshot {
  return {
    app_name: snapshot.app_name,
    ...(snapshot.bundle_id ? { bundle_id: snapshot.bundle_id } : {}),
    ...(snapshot.process_id === undefined ? {} : { process_id: snapshot.process_id }),
    ...(includeWindowTitle && snapshot.window_id ? { window_id: snapshot.window_id } : {}),
    ...(includeWindowTitle && snapshot.window_title ? { window_title: snapshot.window_title } : {}),
    permission_status: snapshot.permission_status,
  };
}

function sameFocus(a: DesktopActivitySnapshot, b: DesktopActivitySnapshot, includeWindowTitle: boolean): boolean {
  if (a.app_name !== b.app_name || a.bundle_id !== b.bundle_id || a.process_id !== b.process_id) {
    return false;
  }

  if (!includeWindowTitle) {
    return true;
  }

  return a.window_id === b.window_id && a.window_title === b.window_title;
}

function boundWindowTitle(title: string): { title: string; truncated: boolean } {
  const maxLength = 120;
  if (title.length <= maxLength) {
    return { title, truncated: false };
  }

  return { title: title.slice(0, maxLength), truncated: true };
}

function hashIdentifier(prefix: string, value: string): string {
  return `${prefix}_${createHash("sha256").update(value).digest("hex").slice(0, 16)}`;
}
