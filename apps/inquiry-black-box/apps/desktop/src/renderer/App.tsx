import type { EventEnvelope, LabelPayload, SessionRecord } from "@inquiry/schema";
import { renderCameraPanel, type CameraPermissionState } from "./camera/CameraPanel";
import type { CameraFeatureWindow } from "./camera/featureWorker";
import { renderSessionControls, type SelfLabel } from "./session/SessionControls";

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

export type InquiryDesktopBridge = {
  session: InquirySessionFacade;
  camera: InquiryCameraFacade;
};

export type AppViewModel = {
  session: SessionRecord | null;
  camera: {
    enabled: boolean;
    permission: CameraPermissionState;
    featureWindow?: CameraFeatureWindow;
  };
};

export function createInitialAppViewModel(session: SessionRecord | null = null): AppViewModel {
  return {
    session,
    camera: {
      enabled: false,
      permission: "prompt",
    },
  };
}

export function renderApp(root: HTMLElement, bridge: InquiryDesktopBridge, initial: AppViewModel = createInitialAppViewModel()): void {
  let view = initial;
  const sessionRoot = document.createElement("div");
  const cameraRoot = document.createElement("div");
  root.replaceChildren(sessionRoot, cameraRoot);

  const refresh = async (): Promise<void> => {
    view = { ...view, session: await bridge.session.currentSession() };
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
  };

  render();
  void refresh();
}
