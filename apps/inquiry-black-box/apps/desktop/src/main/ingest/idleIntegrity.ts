import type { SessionRecord } from "@inquiry/schema";
import type { InquiryDatabase } from "../db";
import type { SessionController } from "./session";

export type IdleIntegritySettings = {
  enabled: boolean;
  idle_threshold_ms: number;
  cooldown_ms: number;
  auto_pause: boolean;
};

export type IdleIntegrityClock = {
  nowMs: () => number;
  nowIso: () => string;
};

const defaultSettings: IdleIntegritySettings = {
  enabled: true,
  idle_threshold_ms: 15 * 60 * 1000,
  cooldown_ms: 10 * 60 * 1000,
  auto_pause: false,
};

const defaultClock: IdleIntegrityClock = {
  nowMs: () => Date.now(),
  nowIso: () => new Date().toISOString(),
};

export type IdleIntegrityWatcher = {
  recordActivity(monotonic_ms?: number): void;
  tick(): void;
  settings(): IdleIntegritySettings;
};

export function createIdleIntegrityWatcher(input: {
  database: InquiryDatabase;
  sessions: SessionController;
  settings?: Partial<IdleIntegritySettings>;
  clock?: Partial<IdleIntegrityClock>;
}): IdleIntegrityWatcher {
  const settings = { ...defaultSettings, ...input.settings };
  const clock = { ...defaultClock, ...input.clock };
  let lastActivityMs = clock.nowMs();
  let lastNudgeMs: number | undefined;

  function activeRecordingSession(): SessionRecord | null {
    const session = input.sessions.currentSession();
    return session?.recording_state === "recording" ? session : null;
  }

  return {
    recordActivity(monotonic_ms = clock.nowMs()) {
      lastActivityMs = monotonic_ms;
    },
    settings() {
      return settings;
    },
    tick() {
      if (!settings.enabled) {
        return;
      }

      const session = activeRecordingSession();
      if (!session) {
        return;
      }

      const now = clock.nowMs();
      const events = input.database.listEvents(session.session_id);
      const lastEventMs = events.length > 0 ? Math.max(...events.map((event) => event.monotonic_ms)) : lastActivityMs;
      const idleFor = now - Math.max(lastActivityMs, lastEventMs);
      if (idleFor < settings.idle_threshold_ms) {
        return;
      }
      if (lastNudgeMs !== undefined && now - lastNudgeMs < settings.cooldown_ms) {
        return;
      }

      lastNudgeMs = now;
      if (settings.auto_pause) {
        input.sessions.pauseSession({ reason: "idle-integrity", monotonic_ms: now });
        return;
      }

      input.database.appendSystemEvent({
        session_id: session.session_id,
        event_type: "notification.candidate",
        monotonic_ms: now,
        payload: {
          kind: "idle-integrity",
          idle_ms: idleFor,
          decision: "still-recording-prompt",
          title: "Still recording?",
          body: "No browser or desktop activity was detected. Pause if this span should not count.",
        },
      });
    },
  };
}
