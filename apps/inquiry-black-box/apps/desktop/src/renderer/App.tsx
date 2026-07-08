import type { EventEnvelope, LabelPayload, SessionRecord, SuggestionResponse } from "@inquiry/schema";
import type { RepairCandidate } from "@inquiry/signals";
import { defaultSessionTitle, maskPairingToken } from "@inquiry/ui";
import type { DesktopShellStatus } from "../main/ipc";
import type { DailyReviewReport } from "../main/reports/dailyDigest";
import type { SessionHistoryEntry } from "../main/reports/sessionHistory";
import type { SessionInterpretationReport } from "../main/reports/sessionInterpretation";
import type { SessionReplayReport } from "../main/reports/sessionReplay";
import { renderCameraPanel, type CameraPermissionState } from "./camera/CameraPanel";
import type { CameraFeatureWindow } from "./camera/featureWorker";
import { renderDailyReviewPanel } from "./daily/DailyReviewPanel";
import { renderSessionInterpretationPanel } from "./interpretation/SessionInterpretationPanel";
import { renderProbePanel, type ProbeAnswer } from "./probes/ProbePanel";
import { renderReplayTimeline } from "./replay/ReplayTimeline";
import { renderSessionControls, type SelfLabel } from "./session/SessionControls";
import {
  defaultPrivacySettingsView,
  renderPrivacySettings,
  type PrivacySettingsView,
} from "./settings/PrivacySettings";

export type InquirySessionFacade = {
  currentSession: () => Promise<SessionRecord | null>;
  startSession: (input: { title: string; active_task?: string; notes?: string }) => Promise<SessionRecord>;
  pauseSession: () => Promise<SessionRecord>;
  resumeSession: () => Promise<SessionRecord>;
  stopSession: () => Promise<SessionRecord>;
  addLabel: (label: LabelPayload["label"], note?: string) => Promise<EventEnvelope<LabelPayload>>;
};

export type InquiryCameraFacade = {
  requestCamera: () => Promise<CameraPermissionState>;
  disableCamera: () => Promise<void>;
  appendFeatureWindow: (featureWindow: CameraFeatureWindow) => Promise<EventEnvelope>;
};

export type InquiryPrivacyFacade = {
  currentSettings: () => Promise<PrivacySettingsView>;
  setSignalEnabled: (key: keyof PrivacySettingsView["signals"], enabled: boolean) => Promise<PrivacySettingsView>;
  exportSession: () => Promise<unknown>;
  deleteSession: () => Promise<unknown>;
};

export type InquiryDesktopBridge = {
  status?: {
    current: () => Promise<DesktopShellStatus>;
  };
  session: InquirySessionFacade;
  camera: InquiryCameraFacade;
  privacy?: InquiryPrivacyFacade;
  replay?: {
    report: () => Promise<SessionReplayReport | null>;
    demo?: () => Promise<SessionReplayReport>;
  };
  sessions?: {
    listHistory: () => Promise<SessionHistoryEntry[]>;
    select: (session_id: string) => Promise<SessionRecord | null>;
  };
  interpretation?: {
    session: () => Promise<SessionInterpretationReport | null>;
    daily: () => Promise<DailyReviewReport>;
    refreshDaily: () => Promise<DailyReviewReport>;
    respondSuggestion: (input: {
      suggestion_id: string;
      response: SuggestionResponse;
      reason?: string;
      snoozed_until?: string;
      local_date?: string;
    }) => Promise<EventEnvelope>;
  };
  repair?: {
    accept: (repair_id: RepairCandidate["repair_id"]) => Promise<EventEnvelope>;
    answer: (input: ProbeAnswer) => Promise<EventEnvelope[]>;
    dismiss: (input: { repair_id: RepairCandidate["repair_id"]; reason?: string }) => Promise<EventEnvelope>;
  };
};

export type AppViewModel = {
  session: SessionRecord | null;
  status?: DesktopShellStatus;
  replay?: SessionReplayReport | null;
  interpretation?: SessionInterpretationReport | null;
  dailyReview?: DailyReviewReport | null;
  sessionHistory: SessionHistoryEntry[];
  repairCandidate?: RepairCandidate | null;
  pairingTokenRevealed: boolean;
  replayDemo: boolean;
  camera: {
    enabled: boolean;
    permission: CameraPermissionState;
    featureWindow?: CameraFeatureWindow;
  };
  privacy: PrivacySettingsView;
};

export function createInitialAppViewModel(session: SessionRecord | null = null): AppViewModel {
  return {
    session,
    sessionHistory: [],
    pairingTokenRevealed: false,
    replayDemo: false,
    camera: {
      enabled: false,
      permission: "prompt",
    },
    privacy: defaultPrivacySettingsView({
      browser: true,
      camera: false,
      desktopActivity: false,
      desktopWindowTitles: false,
      screenSnapshots: false,
      typingMetrics: true,
      notifications: false,
      cloudSync: false,
    }),
  };
}

export function renderApp(root: HTMLElement, bridge: InquiryDesktopBridge, initial: AppViewModel = createInitialAppViewModel()): void {
  let view = initial;
  const shell = document.createElement("div");
  shell.className = "app-shell";
  const rail = document.createElement("aside");
  rail.className = "app-rail";
  const canvas = document.createElement("main");
  canvas.className = "app-canvas";
  const headerRoot = document.createElement("div");
  const historyRoot = document.createElement("div");
  const sessionRoot = document.createElement("div");
  const cameraRoot = document.createElement("div");
  const privacyRoot = document.createElement("div");
  const dailyRoot = document.createElement("div");
  const replayRoot = document.createElement("div");
  const interpretationRoot = document.createElement("div");
  const probeRoot = document.createElement("div");
  rail.append(headerRoot, sessionRoot, historyRoot);
  canvas.append(dailyRoot, replayRoot, interpretationRoot, probeRoot, cameraRoot, privacyRoot);
  shell.append(rail, canvas);
  root.replaceChildren(shell);

  const refresh = async (): Promise<void> => {
    const status = bridge.status ? await bridge.status.current() : undefined;
    const session = status?.session ?? (await bridge.session.currentSession());
    const replay = view.replayDemo
      ? bridge.replay?.demo
        ? await bridge.replay.demo()
        : view.replay ?? null
      : bridge.replay
        ? await bridge.replay.report()
        : view.replay ?? null;
    const interpretation = bridge.interpretation ? await bridge.interpretation.session() : view.interpretation ?? null;
    const dailyReview = bridge.interpretation ? await bridge.interpretation.daily() : view.dailyReview ?? null;
    const sessionHistory = bridge.sessions ? await bridge.sessions.listHistory() : view.sessionHistory;
    view = {
      ...view,
      ...(status ? { status } : {}),
      session,
      privacy: bridge.privacy ? await bridge.privacy.currentSettings() : view.privacy,
      replay,
      interpretation,
      dailyReview,
      sessionHistory,
      repairCandidate: replay?.repair_candidates[0] ?? null,
    };
    render();
  };

  const render = (): void => {
    renderShellHeader(headerRoot, view.status, view.session, view.pairingTokenRevealed, {
      revealPairingToken: () => {
        view = { ...view, pairingTokenRevealed: true };
        render();
      },
      copyPairingToken: async () => {
        if (view.status?.pairingToken) {
          await navigator.clipboard.writeText(view.status.pairingToken);
        }
      },
    });
    renderSessionControls(sessionRoot, view.session, {
      startSession: async (title) => {
        view = { ...view, session: await bridge.session.startSession({ title: title || defaultSessionTitle() }), replayDemo: false };
        await refresh();
      },
      pauseSession: async () => {
        view = { ...view, session: await bridge.session.pauseSession() };
        await refresh();
      },
      resumeSession: async () => {
        view = { ...view, session: await bridge.session.resumeSession() };
        await refresh();
      },
      stopSession: async () => {
        view = { ...view, session: await bridge.session.stopSession(), replayDemo: false };
        await refresh();
      },
      addLabel: async (label: SelfLabel) => {
        await bridge.session.addLabel(label);
        await refresh();
      },
    });
    renderSessionHistory(historyRoot, view.sessionHistory, view.session?.session_id ?? null, {
      selectSession: async (session_id) => {
        if (bridge.sessions) {
          view = { ...view, replayDemo: false };
          await bridge.sessions.select(session_id);
          await refresh();
        }
      },
    });
    if (bridge.privacy) {
      renderPrivacySettings(privacyRoot, view.privacy, {
        setSignalEnabled: async (key, enabled) => {
          view = { ...view, privacy: await bridge.privacy!.setSignalEnabled(key, enabled) };
          render();
        },
        exportSession: async () => {
          await bridge.privacy!.exportSession();
          await refresh();
        },
        deleteSession: async () => {
          await bridge.privacy!.deleteSession();
          view = { ...view, replayDemo: false };
          await refresh();
        },
      });
    } else {
      privacyRoot.replaceChildren();
    }
    if (view.replay) {
      const replayOptions: { demo: boolean; onViewDemo?: () => Promise<void> } = { demo: view.replayDemo };
      if (bridge.replay?.demo) {
        replayOptions.onViewDemo = async () => {
          view = { ...view, replayDemo: true, replay: await bridge.replay!.demo!() };
          render();
        };
      }
      renderReplayTimeline(replayRoot, view.replay, replayOptions);
    } else {
      renderReplayTimeline(replayRoot, {
        session_id: "",
        markers: [],
        heatmap: [],
        episodes: [],
        next_actions: [],
      });
    }
    renderSessionInterpretationPanel(interpretationRoot, view.interpretation);
    if (bridge.interpretation) {
      renderDailyReviewPanel(dailyRoot, view.dailyReview, {
        refreshDailyReview: async () => {
          view = { ...view, dailyReview: await bridge.interpretation!.refreshDaily() };
          render();
        },
        respondSuggestion: async (input) => {
          await bridge.interpretation!.respondSuggestion({
            ...input,
            ...(view.dailyReview?.local_date ? { local_date: view.dailyReview.local_date } : {}),
          });
          view = { ...view, dailyReview: await bridge.interpretation!.refreshDaily() };
          render();
        },
      });
    } else {
      dailyRoot.replaceChildren();
    }
    if (bridge.repair) {
      renderProbePanel(probeRoot, view.repairCandidate ?? null, {
        acceptRepair: async (repair_id) => {
          await bridge.repair!.accept(repair_id);
          await refresh();
        },
        answerRepair: async (answer) => {
          await bridge.repair!.answer(answer);
          await refresh();
        },
        dismissRepair: async (repair_id) => {
          await bridge.repair!.dismiss({ repair_id });
          await refresh();
        },
      });
    } else {
      probeRoot.replaceChildren();
    }
    renderCameraPanel(cameraRoot, view.camera, {
      requestCamera: async () => {
        const permission = await bridge.camera.requestCamera();
        view = { ...view, camera: { ...view.camera, enabled: permission === "granted", permission } };
        render();
      },
      disableCamera: async () => {
        await bridge.camera.disableCamera();
        view = { ...view, camera: { ...view.camera, enabled: false } };
        render();
      },
    });
  };

  render();
  void refresh();
}

function renderSessionHistory(
  root: HTMLElement,
  history: SessionHistoryEntry[],
  activeSessionId: string | null,
  actions: { selectSession: (session_id: string) => void | Promise<void> },
): void {
  const section = document.createElement("section");
  section.className = "session-history";

  const title = document.createElement("h2");
  title.textContent = "Recent sessions";
  section.append(title);

  if (history.length === 0) {
    const empty = document.createElement("p");
    empty.className = "session-history__empty";
    empty.textContent = "Start a titled session to build history here.";
    section.append(empty);
    root.replaceChildren(section);
    return;
  }

  const list = document.createElement("ol");
  list.className = "session-history__list";
  for (const entry of history) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "session-history__item";
    if (entry.session_id === activeSessionId) {
      button.classList.add("session-history__item-active");
    }
    button.addEventListener("click", () => void actions.selectSession(entry.session_id));

    const heading = document.createElement("strong");
    heading.textContent = entry.title;
    const meta = document.createElement("span");
    meta.className = "session-history__meta";
    meta.textContent = [
      entry.recording_state,
      entry.duration_ms ? formatDuration(entry.duration_ms) : "duration pending",
      entry.top_markers.length > 0 ? entry.top_markers.join(", ") : "no markers yet",
    ].join(" · ");
    const verdict = document.createElement("span");
    verdict.className = "session-history__verdict";
    verdict.textContent = entry.verdict;

    button.append(heading, meta, verdict);
    item.append(button);
    list.append(item);
  }
  section.append(list);
  root.replaceChildren(section);
}

function renderShellHeader(
  root: HTMLElement,
  status: DesktopShellStatus | undefined,
  session: SessionRecord | null,
  pairingTokenRevealed: boolean,
  actions: { revealPairingToken: () => void; copyPairingToken: () => void | Promise<void> },
): void {
  const header = document.createElement("header");
  header.className = "app-header";

  const title = document.createElement("h1");
  title.textContent = "Inquiry Black Box";
  header.append(title);

  const grid = document.createElement("div");
  grid.className = "app-status-grid";
  grid.append(
    statusItem("Session", session?.title ?? "No session"),
    statusItem("Ingest", status?.ingestUrl ?? "Not listening"),
    pairingTokenItem(status?.pairingToken ?? "Starting", pairingTokenRevealed, actions),
  );
  header.append(grid);

  root.replaceChildren(header);
}

function statusItem(labelText: string, valueText: string, valueClassName = ""): HTMLElement {
  const item = document.createElement("div");
  item.className = "app-status-item";

  const label = document.createElement("span");
  label.className = "app-status-label";
  label.textContent = labelText;

  const value = document.createElement("strong");
  value.className = `app-status-value ${valueClassName}`.trim();
  value.textContent = valueText;

  item.append(label, value);
  return item;
}

function pairingTokenItem(
  token: string,
  revealed: boolean,
  actions: { revealPairingToken: () => void; copyPairingToken: () => void | Promise<void> },
): HTMLElement {
  const item = document.createElement("div");
  item.className = "app-status-item pairing-token-item";

  const label = document.createElement("span");
  label.className = "app-status-label";
  label.textContent = "Pairing token";

  const value = document.createElement("strong");
  value.className = "app-status-value pairing-token";
  value.textContent = maskPairingToken(token, revealed);

  const controls = document.createElement("div");
  controls.className = "pairing-token-controls";
  const reveal = document.createElement("button");
  reveal.type = "button";
  reveal.textContent = revealed ? "Hide" : "Reveal";
  reveal.addEventListener("click", () => actions.revealPairingToken());
  const copy = document.createElement("button");
  copy.type = "button";
  copy.textContent = "Copy";
  copy.addEventListener("click", () => void actions.copyPairingToken());
  controls.append(reveal, copy);

  item.append(label, value, controls);
  return item;
}

function formatDuration(durationMs: number): string {
  const minutes = Math.floor(durationMs / 60_000);
  const seconds = Math.round((durationMs % 60_000) / 1000);
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  }
  return `${seconds}s`;
}
