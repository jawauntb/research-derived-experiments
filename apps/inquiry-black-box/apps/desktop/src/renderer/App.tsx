import type { EventEnvelope, LabelPayload, SessionRecord } from "@inquiry/schema";
import type { DesktopShellStatus } from "../main/ipc";
import type { SessionReplayReport } from "../main/reports/sessionReplay";
import { renderCameraPanel, type CameraPermissionState } from "./camera/CameraPanel";
import type { CameraFeatureWindow } from "./camera/featureWorker";
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
  };
};

export type AppViewModel = {
  session: SessionRecord | null;
  status?: DesktopShellStatus;
  replay?: SessionReplayReport | null;
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
    camera: {
      enabled: false,
      permission: "prompt",
    },
    privacy: defaultPrivacySettingsView({
      browser: true,
      camera: false,
      typingMetrics: true,
      notifications: false,
      cloudSync: false,
    }),
  };
}

export function renderApp(root: HTMLElement, bridge: InquiryDesktopBridge, initial: AppViewModel = createInitialAppViewModel()): void {
  let view = initial;
  const headerRoot = document.createElement("div");
  const sessionRoot = document.createElement("div");
  const cameraRoot = document.createElement("div");
  const privacyRoot = document.createElement("div");
  const replayRoot = document.createElement("div");
  root.replaceChildren(headerRoot, sessionRoot, cameraRoot, privacyRoot, replayRoot);

  const refresh = async (): Promise<void> => {
    const status = bridge.status ? await bridge.status.current() : undefined;
    const session = status?.session ?? (await bridge.session.currentSession());
    const replay = bridge.replay ? await bridge.replay.report() : view.replay ?? null;
    view = {
      ...view,
      ...(status ? { status } : {}),
      session,
      privacy: bridge.privacy ? await bridge.privacy.currentSettings() : view.privacy,
      replay,
    };
    render();
  };

  const render = (): void => {
    renderShellHeader(headerRoot, view.status, view.session);
    renderSessionControls(sessionRoot, view.session, {
      startSession: async () => {
        view = { ...view, session: await bridge.session.startSession({ title: "Research session" }) };
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
        view = { ...view, session: await bridge.session.stopSession() };
        await refresh();
      },
      addLabel: async (label: SelfLabel) => {
        await bridge.session.addLabel(label);
        await refresh();
      },
    });
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
          await refresh();
        },
      });
    } else {
      privacyRoot.replaceChildren();
    }
    if (view.replay) {
      renderReplayTimeline(replayRoot, view.replay);
    } else {
      replayRoot.replaceChildren();
    }
  };

  render();
  void refresh();
}

function renderShellHeader(
  root: HTMLElement,
  status: DesktopShellStatus | undefined,
  session: SessionRecord | null,
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
    statusItem("Pairing Token", status?.pairingToken ?? "Starting", "pairing-token"),
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
