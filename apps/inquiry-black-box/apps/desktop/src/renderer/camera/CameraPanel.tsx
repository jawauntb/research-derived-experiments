import type { CameraFeatureWindow } from "./featureWorker";

export type CameraPermissionState = "prompt" | "granted" | "denied" | "unavailable";

export type CameraPanelViewModel = {
  enabled: boolean;
  permission: CameraPermissionState;
  status: string;
  qualityFlags: readonly string[];
  canRequestCamera: boolean;
};

export type CameraPanelActions = {
  requestCamera: () => void | Promise<void>;
  disableCamera: () => void | Promise<void>;
};

export function cameraPanelViewModel(input: {
  enabled: boolean;
  permission: CameraPermissionState;
  featureWindow?: CameraFeatureWindow;
}): CameraPanelViewModel {
  const qualityFlags = input.featureWindow?.quality_flags ?? [];
  return {
    enabled: input.enabled,
    permission: input.permission,
    status: cameraStatus(input.permission, input.enabled, qualityFlags),
    qualityFlags,
    canRequestCamera: input.permission === "prompt" || input.permission === "denied",
  };
}

export function renderCameraPanel(
  root: HTMLElement,
  input: { enabled: boolean; permission: CameraPermissionState; featureWindow?: CameraFeatureWindow },
  actions: CameraPanelActions,
): void {
  const view = cameraPanelViewModel(input);
  const container = document.createElement("section");
  container.className = "camera-panel";

  const status = document.createElement("strong");
  status.textContent = view.status;
  status.setAttribute("aria-live", "polite");
  container.append(status);

  const toolbar = document.createElement("div");
  toolbar.className = "camera-toolbar";
  const requestButton = document.createElement("button");
  requestButton.type = "button";
  requestButton.textContent = "Enable camera";
  requestButton.disabled = !view.canRequestCamera || view.enabled;
  requestButton.addEventListener("click", () => {
    void actions.requestCamera();
  });
  toolbar.append(requestButton);

  const disableButton = document.createElement("button");
  disableButton.type = "button";
  disableButton.textContent = "Disable camera";
  disableButton.disabled = !view.enabled;
  disableButton.addEventListener("click", () => {
    void actions.disableCamera();
  });
  toolbar.append(disableButton);
  container.append(toolbar);

  const flags = document.createElement("ul");
  flags.className = "camera-quality-flags";
  for (const flag of view.qualityFlags) {
    const item = document.createElement("li");
    item.textContent = flag;
    flags.append(item);
  }
  container.append(flags);

  root.replaceChildren(container);
}

function cameraStatus(permission: CameraPermissionState, enabled: boolean, flags: readonly string[]): string {
  if (permission === "unavailable") {
    return "Camera unavailable";
  }
  if (permission === "denied") {
    return "Camera blocked";
  }
  if (!enabled) {
    return "Camera off";
  }
  if (flags.length > 0) {
    return "Camera features degraded";
  }
  return "Camera features active";
}
