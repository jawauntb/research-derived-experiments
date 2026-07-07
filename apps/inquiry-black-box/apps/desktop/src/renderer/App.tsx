import type { EventEnvelope, LabelPayload, SessionRecord } from "@inquiry/schema";
import { renderCameraPanel, type CameraPermissionState } from "./camera/CameraPanel";
import type { CameraFeatureWindow } from "./camera/featureWorker";
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
  exportSession: () => Promise<void>;
  deleteSession: () => Promise<void>;
};

export type InquiryDesktopBridge = {
  session: InquirySessionFacade;
  camera: InquiryCameraFacade;
  privacy?: InquiryPrivacyFacade;
};

export type AppViewModel = {
  session: SessionRecord | null;
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
  const sessionRoot = document.createElement("div");
  const cameraRoot = document.createElement("div");
  const privacyRoot = document.createElement("div");
  root.replaceChildren(sessionRoot, cameraRoot, privacyRoot);

  const refresh = async (): Promise<void> => {
    view = {
      ...view,
      session: await bridge.session.currentSession(),
      privacy: bridge.privacy ? await bridge.privacy.currentSettings() : view.privacy,
    };
    render();
  };

  const render = (): void => {
    renderSessionControls(sessionRoot, view.session, {
      startSession: async () => {
        view = { ...view, session: await bridge.session.startSession({ title: "Research session" }) };
        render();
      },
      pauseSession: async () => {
        view = { ...view, session: await bridge.session.pauseSession() };
        render();
      },
      resumeSession: async () => {
        view = { ...view, session: await bridge.session.resumeSession() };
        render();
      },
      stopSession: async () => {
        view = { ...view, session: await bridge.session.stopSession() };
        render();
      },
      addLabel: async (label: SelfLabel) => {
        await bridge.session.addLabel(label);
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
        exportSession: bridge.privacy.exportSession,
        deleteSession: bridge.privacy.deleteSession,
      });
    } else {
      privacyRoot.replaceChildren();
    }
  };

  render();
  void refresh();
}
