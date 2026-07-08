import type { CameraFeatureWindow } from "./featureWorker";

export type CameraPermissionState = "prompt" | "granted" | "denied" | "unavailable";

export type CameraPanelStatusTone = "good" | "warn" | "blocked" | "muted";

export type CameraPanelStatusLine = {
  label: string;
  detail: string;
  tone: CameraPanelStatusTone;
};

export type CameraPanelViewModel = {
  enabled: boolean;
  permission: CameraPermissionState;
  status: string;
  permissionStatus: CameraPanelStatusLine;
  enabledStatus: CameraPanelStatusLine;
  featureHeartbeat: CameraPanelStatusLine;
  qualityStatus: CameraPanelStatusLine;
  localOnlyStatus: CameraPanelStatusLine;
  privacyNote: string;
  qualityFlags: readonly string[];
  canRequestCamera: boolean;
  canDisableCamera: boolean;
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
  const featureHeartbeat = cameraFeatureHeartbeatStatus(input.enabled, input.featureWindow);
  const qualityStatus = cameraQualityStatus(input.enabled, input.featureWindow, qualityFlags);
  return {
    enabled: input.enabled,
    permission: input.permission,
    status: cameraStatus(input.permission, input.enabled, featureHeartbeat, qualityFlags),
    permissionStatus: cameraPermissionStatus(input.permission),
    enabledStatus: cameraEnabledStatus(input.permission, input.enabled),
    featureHeartbeat,
    qualityStatus,
    localOnlyStatus: {
      label: "Local only",
      detail: "Derived camera features stay on this device unless a later opt-in explicitly changes that.",
      tone: input.enabled ? "good" : "muted",
    },
    privacyNote: "No raw camera frames are stored or exported by default.",
    qualityFlags,
    canRequestCamera: input.permission === "prompt" || input.permission === "denied",
    canDisableCamera: input.enabled,
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

  const statusRows = document.createElement("dl");
  statusRows.className = "camera-status-list";
  appendStatusLine(statusRows, "Permission", view.permissionStatus);
  appendStatusLine(statusRows, "Enabled", view.enabledStatus);
  appendStatusLine(statusRows, "Feature heartbeat", view.featureHeartbeat);
  appendStatusLine(statusRows, "Quality", view.qualityStatus);
  appendStatusLine(statusRows, "Storage", view.localOnlyStatus);
  container.append(statusRows);

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
  disableButton.disabled = !view.canDisableCamera;
  disableButton.addEventListener("click", () => {
    void actions.disableCamera();
  });
  toolbar.append(disableButton);
  container.append(toolbar);

  const flags = document.createElement("ul");
  flags.className = "camera-quality-flags";
  for (const flag of view.qualityFlags) {
    const item = document.createElement("li");
    item.textContent = qualityFlagLabel(flag);
    flags.append(item);
  }
  container.append(flags);

  const privacyNote = document.createElement("p");
  privacyNote.className = "camera-privacy-note";
  privacyNote.textContent = view.privacyNote;
  container.append(privacyNote);

  root.replaceChildren(container);
}

function appendStatusLine(root: HTMLElement, termText: string, line: CameraPanelStatusLine): void {
  const term = document.createElement("dt");
  term.textContent = termText;

  const detail = document.createElement("dd");
  detail.className = `camera-status-line camera-status-line-${line.tone}`;

  const label = document.createElement("strong");
  label.textContent = line.label;
  const copy = document.createElement("span");
  copy.textContent = line.detail;
  detail.append(label, document.createTextNode(" "), copy);

  root.append(term, detail);
}

function cameraStatus(
  permission: CameraPermissionState,
  enabled: boolean,
  heartbeat: CameraPanelStatusLine,
  flags: readonly string[],
): string {
  if (permission === "unavailable") {
    return "Camera unavailable";
  }
  if (permission === "denied") {
    return "Camera blocked";
  }
  if (!enabled) {
    return "Camera off";
  }
  if (heartbeat.tone === "warn") {
    return "Camera features waiting";
  }
  if (flags.length > 0) {
    return "Camera features degraded";
  }
  return "Camera features active";
}

function cameraPermissionStatus(permission: CameraPermissionState): CameraPanelStatusLine {
  if (permission === "granted") {
    return {
      label: "Permission allowed",
      detail: "The operating system allowed camera access for local feature extraction.",
      tone: "good",
    };
  }
  if (permission === "denied") {
    return {
      label: "Permission blocked",
      detail: "Camera access was denied. Use system or browser permission settings to allow it.",
      tone: "blocked",
    };
  }
  if (permission === "unavailable") {
    return {
      label: "Permission unavailable",
      detail: "No camera permission API is available in this desktop shell.",
      tone: "blocked",
    };
  }

  return {
    label: "Permission not requested",
    detail: "Enable camera to request permission before collecting derived features.",
    tone: "muted",
  };
}

function cameraEnabledStatus(permission: CameraPermissionState, enabled: boolean): CameraPanelStatusLine {
  if (enabled && permission === "granted") {
    return {
      label: "Feature collection on",
      detail: "The camera lane is enabled and waiting for derived feature windows.",
      tone: "good",
    };
  }

  if (enabled) {
    return {
      label: "Feature collection blocked",
      detail: "The camera lane was enabled, but permission is not available for feature collection.",
      tone: "blocked",
    };
  }

  if (permission === "denied" || permission === "unavailable") {
    return {
      label: "Feature collection off",
      detail: "No camera-derived features can be collected in this permission state.",
      tone: "blocked",
    };
  }

  return {
    label: "Feature collection off",
    detail: "Camera-derived features are disabled.",
    tone: "muted",
  };
}

function cameraFeatureHeartbeatStatus(
  enabled: boolean,
  featureWindow: CameraFeatureWindow | undefined,
): CameraPanelStatusLine {
  if (featureWindow) {
    return {
      label: "Derived feature heartbeat received",
      detail: `Last local feature window ended ${formatSeconds(featureWindow.window_end_ms)} into the session.`,
      tone: "good",
    };
  }

  if (enabled) {
    return {
      label: "Waiting for derived feature heartbeat",
      detail: "Permission is allowed, but no camera feature window has been recorded yet.",
      tone: "warn",
    };
  }

  return {
    label: "No derived feature heartbeat yet",
    detail: "No camera feature window has been recorded in this session.",
    tone: "muted",
  };
}

function cameraQualityStatus(
  enabled: boolean,
  featureWindow: CameraFeatureWindow | undefined,
  qualityFlags: readonly string[],
): CameraPanelStatusLine {
  if (qualityFlags.length > 0) {
    return {
      label: "Feature quality degraded",
      detail: qualityFlags.map(qualityFlagLabel).join(", "),
      tone: "warn",
    };
  }

  if (featureWindow) {
    return {
      label: "Feature quality usable",
      detail: `${featureWindow.sample_count} frame summaries contributed to the last derived feature window.`,
      tone: "good",
    };
  }

  if (enabled) {
    return {
      label: "Degraded until features arrive",
      detail: "Quality cannot be assessed until the first derived feature heartbeat.",
      tone: "warn",
    };
  }

  return {
    label: "Quality unavailable",
    detail: "Quality flags appear here after local feature extraction runs.",
    tone: "muted",
  };
}

function qualityFlagLabel(flag: string): string {
  const labels: Record<string, string> = {
    "camera.low-sample-count": "Low sample count",
    "camera.face-missing": "Face not consistently visible",
    "camera.gaze-away": "Gaze away",
    "camera.blink-likely": "Blink likely",
    "camera.head-pose-unstable": "Head pose unstable",
    "camera.motion-high": "Motion high",
    "camera.low-light": "Low light",
    "camera.blurry": "Blurry feature signal",
  };

  return labels[flag] ?? flag;
}

function formatSeconds(ms: number): string {
  return `${(ms / 1_000).toFixed(1)}s`;
}
