import type { EventEnvelope, LabelPayload, SessionRecord, SignalSettings } from "@inquiry/schema";
import type { CameraFeatureWindow } from "../renderer/camera/featureWorker";
import type { PrivacySettingsView } from "../renderer/settings/PrivacySettings";
import { deleteLocalSession } from "./privacy/delete";
import { exportSession, type SessionExport } from "./privacy/export";
import { createSessionReplayReport, type SessionReplayReport } from "./reports/sessionReplay";
import type { DesktopRuntime } from "./main";

export type DesktopShellStatus = {
  session: SessionRecord | null;
  recordingState: SessionRecord["recording_state"] | "idle";
  pairingToken: string;
  ingestUrl: string | null;
};

export type DesktopIpcFacade = {
  status: () => Promise<DesktopShellStatus>;
  currentSession: () => Promise<SessionRecord | null>;
  startSession: (input: { title: string; active_task?: string; notes?: string }) => Promise<SessionRecord>;
  pauseSession: () => Promise<SessionRecord>;
  resumeSession: () => Promise<SessionRecord>;
  stopSession: () => Promise<SessionRecord>;
  addLabel: (input: { label: LabelPayload["label"]; note?: string; monotonic_ms?: number }) => Promise<EventEnvelope<LabelPayload>>;
  appendCameraFeatureWindow: (featureWindow: CameraFeatureWindow) => Promise<EventEnvelope>;
  currentSettings: () => Promise<PrivacySettingsView>;
  setSignalEnabled: (key: keyof SignalSettings, enabled: boolean) => Promise<PrivacySettingsView>;
  exportSession: () => Promise<SessionExport>;
  deleteSession: () => Promise<{ session_id: string; deleted: true }>;
  replayReport: () => Promise<SessionReplayReport | null>;
  shutdown: () => Promise<void>;
};

export function createDesktopIpcFacade(runtime: DesktopRuntime): DesktopIpcFacade {
  let lastSessionId = runtime.sessions.currentSession()?.session_id ?? null;

  function remember(session: SessionRecord): SessionRecord {
    lastSessionId = session.session_id;
    return session;
  }

  function rememberedSession(): SessionRecord | null {
    const active = runtime.sessions.currentSession();
    if (active) {
      lastSessionId = active.session_id;
      return active;
    }

    return lastSessionId ? runtime.database.getSession(lastSessionId) : null;
  }

  function requireRememberedSessionId(): string {
    const session = rememberedSession();
    if (!session) {
      throw new Error("no session available");
    }
    return session.session_id;
  }

  return {
    async status() {
      const session = rememberedSession();
      return {
        session,
        recordingState: session?.recording_state ?? "idle",
        pairingToken: runtime.pairingToken(),
        ingestUrl: runtime.ingest?.url ?? null,
      };
    },
    async currentSession() {
      return runtime.bridge.currentSession();
    },
    async startSession(input) {
      return remember(runtime.bridge.startSession(input));
    },
    async pauseSession() {
      return remember(runtime.bridge.pauseSession());
    },
    async resumeSession() {
      return remember(runtime.bridge.resumeSession());
    },
    async stopSession() {
      return remember(runtime.bridge.stopSession());
    },
    async addLabel(input) {
      return runtime.bridge.addLabel(input);
    },
    async appendCameraFeatureWindow(featureWindow) {
      return runtime.bridge.appendCameraFeatureWindow(featureWindow);
    },
    async currentSettings() {
      return privacyView(runtime.database.signalSettings());
    },
    async setSignalEnabled(key, enabled) {
      runtime.database.setSignalEnabled(key, enabled);
      return privacyView(runtime.database.signalSettings());
    },
    async exportSession() {
      return exportSession(runtime.database, requireRememberedSessionId());
    },
    async deleteSession() {
      const sessionId = requireRememberedSessionId();
      const result = deleteLocalSession(runtime.database, sessionId);
      if (lastSessionId === sessionId) {
        lastSessionId = null;
      }
      return result;
    },
    async replayReport() {
      const session = rememberedSession();
      if (!session) {
        return null;
      }

      return createSessionReplayReport(runtime.database.listEvents(session.session_id));
    },
    async shutdown() {
      runtime.stop();
    },
  };
}

function privacyView(signals: SignalSettings): PrivacySettingsView {
  return {
    signals,
    retention_days: 30,
    recording_indicator_visible: true,
    cloud_sync_enabled: signals.cloudSync,
    export_available: true,
    delete_available: true,
  };
}
