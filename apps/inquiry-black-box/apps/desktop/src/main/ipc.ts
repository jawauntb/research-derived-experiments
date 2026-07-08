import type { EventEnvelope, LabelPayload, SessionRecord, SignalSettings } from "@inquiry/schema";
import {
  createRepairCandidateEvent,
  createRepairOutcomeEvent,
  createRepairProbeAnswerEvent,
  createRepairProbeEvent,
  type RepairCandidate,
} from "@inquiry/signals";
import type { CameraFeatureWindow } from "../renderer/camera/featureWorker";
import type { PrivacySettingsView } from "../renderer/settings/PrivacySettings";
import { deleteLocalSession } from "./privacy/delete";
import { exportSession, type SessionExport } from "./privacy/export";
import { createSessionReplayReport, type SessionReplayReport } from "./reports/sessionReplay";
import type { DesktopRuntime } from "./main";
import type { DesktopActivityStatus } from "./activity/desktopActivity";

export type DesktopShellStatus = {
  session: SessionRecord | null;
  recordingState: SessionRecord["recording_state"] | "idle";
  pairingToken: string;
  ingestUrl: string | null;
  desktopActivity: DesktopActivityStatus;
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
  acceptRepair: (repair_id: string) => Promise<EventEnvelope>;
  answerRepair: (input: { repair_id: string; answer: string; confidence: number }) => Promise<EventEnvelope[]>;
  dismissRepair: (input: { repair_id: string; reason?: string }) => Promise<EventEnvelope>;
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
        desktopActivity: runtime.bridge.desktopActivityStatus(),
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
      return privacyView(runtime.database.signalSettings(), runtime.bridge.desktopActivityStatus());
    },
    async setSignalEnabled(key, enabled) {
      runtime.database.setSignalEnabled(key, enabled);
      runtime.bridge.syncDesktopActivity();
      return privacyView(runtime.database.signalSettings(), runtime.bridge.desktopActivityStatus());
    },
    async exportSession() {
      return exportSession(runtime.database, requireRememberedSessionId());
    },
    async deleteSession() {
      const sessionId = requireRememberedSessionId();
      const active = runtime.sessions.currentSession();
      if (active?.session_id === sessionId && active.recording_state !== "stopped") {
        runtime.bridge.stopSession({ reason: "delete-session" });
      } else {
        runtime.desktopActivity.stop();
      }
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
    async acceptRepair(repair_id) {
      const candidate = repairCandidateById(repair_id);
      appendRepairCandidateIfNew(candidate);
      const probe = createRepairProbeEvent(candidate, {
        event_id: probeEventId(candidate),
        probe_id: probeId(candidate),
      });
      runtime.database.appendEventIfNew(probe);
      return probe;
    },
    async answerRepair(input) {
      const candidate = repairCandidateById(input.repair_id);
      appendRepairCandidateIfNew(candidate);
      const probe = createRepairProbeEvent(candidate, {
        event_id: probeEventId(candidate),
        probe_id: probeId(candidate),
      });
      runtime.database.appendEventIfNew(probe);
      const answer = runtime.database.appendEvent(
        createRepairProbeAnswerEvent(candidate, {
          probe_id: probeId(candidate),
          answer: input.answer,
          confidence: input.confidence,
        }),
      );
      const outcome = runtime.database.appendEvent(
        createRepairOutcomeEvent({
          candidate,
          outcome: "answered",
          probe_id: probeId(candidate),
          answer: input.answer,
          answer_confidence: input.confidence,
        }),
      );
      return [answer, outcome];
    },
    async dismissRepair(input) {
      const candidate = repairCandidateById(input.repair_id);
      appendRepairCandidateIfNew(candidate);
      return runtime.database.appendEvent(
        createRepairOutcomeEvent({
          candidate,
          outcome: "dismissed",
          ...(input.reason ? { reason: input.reason } : {}),
        }),
      );
    },
    async shutdown() {
      runtime.stop();
    },
  };

  function repairCandidateById(repair_id: string): RepairCandidate {
    const session = rememberedSession();
    if (!session) {
      throw new Error("no session available");
    }

    const report = createSessionReplayReport(runtime.database.listEvents(session.session_id));
    const candidate = report.repair_candidates.find((item) => item.repair_id === repair_id);
    if (!candidate) {
      throw new Error(`repair candidate not found: ${repair_id}`);
    }
    return candidate;
  }

  function appendRepairCandidateIfNew(candidate: RepairCandidate): void {
    runtime.database.appendEventIfNew(
      createRepairCandidateEvent(candidate, {
        event_id: `repair-candidate:${candidate.repair_id}`,
      }),
    );
  }
}

function probeId(candidate: RepairCandidate): string {
  return `${candidate.repair_id}:probe`;
}

function probeEventId(candidate: RepairCandidate): string {
  return `repair-probe:${candidate.repair_id}`;
}

function privacyView(signals: SignalSettings, desktopActivity?: DesktopActivityStatus): PrivacySettingsView {
  return {
    signals,
    retention_days: 30,
    recording_indicator_visible: true,
    cloud_sync_enabled: signals.cloudSync,
    export_available: true,
    delete_available: true,
    ...(desktopActivity ? { desktop_activity: desktopActivity } : {}),
  };
}
