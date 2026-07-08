import { applySignalSettingChange, type SignalSettings } from "@inquiry/schema";

export type DesktopActivitySettingsStatus = {
  enabled: boolean;
  includeWindowTitles: boolean;
  active: boolean;
  permission_status: "not_requested" | "granted" | "denied" | "unavailable";
  last_heartbeat_monotonic_ms?: number;
  last_app_name?: string;
  last_error?: string;
};

export type PrivacySettingsView = {
  signals: SignalSettings;
  retention_days: number;
  recording_indicator_visible: boolean;
  cloud_sync_enabled: boolean;
  export_available: boolean;
  delete_available: boolean;
  desktop_activity?: DesktopActivitySettingsStatus;
};

export type PrivacySettingsActions = {
  setSignalEnabled: (key: keyof SignalSettings, enabled: boolean) => void | Promise<void>;
  exportSession: () => void | Promise<void>;
  deleteSession: () => void | Promise<void>;
};

export type PrivacySettingsTone = "good" | "warn" | "blocked" | "muted";

export type PrivacySignalRow = {
  key: keyof SignalSettings;
  label: string;
  detail: string;
  checked: boolean;
  disabled: boolean;
  status: string;
  tone: PrivacySettingsTone;
};

export type DesktopActivityPrivacyStatus = {
  label: string;
  detail: string;
  tone: PrivacySettingsTone;
};

const signalLabels: Array<{ key: keyof SignalSettings; label: string; detail: string }> = [
  { key: "browser", label: "Browser traces", detail: "Browser events from paired http and https pages." },
  { key: "camera", label: "Camera features", detail: "Derived camera windows without raw frames." },
  { key: "desktopActivity", label: "Desktop app context", detail: "Foreground app identity while recording." },
  { key: "desktopWindowTitles", label: "Window titles", detail: "Bounded focused-window titles." },
  { key: "typingMetrics", label: "Typing rhythm", detail: "Aggregate typing cadence without typed text." },
  { key: "notifications", label: "Notifications", detail: "Local notification candidates." },
  { key: "screenSnapshots", label: "Screen snapshots", detail: "Reserved for a later explicit screen-capture opt-in." },
  { key: "cloudSync", label: "Cloud sync", detail: "Only redacted-sync payloads are eligible." },
];

export function defaultPrivacySettingsView(signals: SignalSettings): PrivacySettingsView {
  return {
    signals,
    retention_days: 30,
    recording_indicator_visible: true,
    cloud_sync_enabled: signals.cloudSync,
    export_available: true,
    delete_available: true,
  };
}

export function updateSignalSetting(
  view: PrivacySettingsView,
  key: keyof SignalSettings,
  enabled: boolean,
): PrivacySettingsView {
  const signals = applySignalSettingChange(view.signals, key, enabled);

  return {
    ...view,
    signals,
    cloud_sync_enabled: signals.cloudSync,
  };
}

export function privacySignalRows(view: PrivacySettingsView): PrivacySignalRow[] {
  return signalLabels.map((signal) => {
    const disabled = signalDisabled(signal.key, view);
    return {
      key: signal.key,
      label: signal.label,
      detail: signal.detail,
      checked: view.signals[signal.key],
      disabled,
      status: signalStatus(signal.key, view, disabled),
      tone: signalTone(signal.key, view, disabled),
    };
  });
}

export function desktopActivityPrivacyStatus(view: PrivacySettingsView): DesktopActivityPrivacyStatus {
  const status = view.desktop_activity;
  if (!view.signals.desktopActivity) {
    return {
      label: "Desktop activity off",
      detail: "No cross-app metadata is collected.",
      tone: "muted",
    };
  }
  if (!status || status.permission_status === "not_requested") {
    return {
      label: "Permission not checked",
      detail: "Recording will check macOS foreground-app access before collecting metadata.",
      tone: "warn",
    };
  }
  if (status.permission_status === "denied") {
    return {
      label: "Permission blocked",
      detail: "macOS did not allow foreground app/window metadata.",
      tone: "blocked",
    };
  }
  if (status.permission_status === "unavailable") {
    return {
      label: "Permission unavailable",
      detail: "Desktop activity capture is only available in the macOS app.",
      tone: "blocked",
    };
  }
  if (status.active && status.last_heartbeat_monotonic_ms !== undefined) {
    return {
      label: "Desktop activity active",
      detail: `Last app: ${status.last_app_name ?? "unknown"} at ${formatSeconds(status.last_heartbeat_monotonic_ms)}.`,
      tone: "good",
    };
  }
  if (status.active) {
    return {
      label: "Desktop activity waiting",
      detail: "The collector is on and waiting for the first app-focus heartbeat.",
      tone: "warn",
    };
  }

  return {
    label: "Desktop activity ready",
    detail: "Metadata collection can start with the next recording session.",
    tone: "good",
  };
}

export function renderPrivacySettings(
  container: HTMLElement,
  view: PrivacySettingsView,
  actions: PrivacySettingsActions,
): void {
  const section = document.createElement("section");
  section.className = "privacy-settings";

  const title = document.createElement("h2");
  title.textContent = "Privacy";
  section.append(title);

  const desktopStatus = desktopActivityPrivacyStatus(view);
  const desktopStatusRow = document.createElement("div");
  desktopStatusRow.className = `privacy-settings__status privacy-settings__status-${desktopStatus.tone}`;
  const desktopStatusLabel = document.createElement("strong");
  desktopStatusLabel.textContent = desktopStatus.label;
  const desktopStatusDetail = document.createElement("span");
  desktopStatusDetail.textContent = desktopStatus.detail;
  desktopStatusRow.append(desktopStatusLabel, desktopStatusDetail);
  section.append(desktopStatusRow);

  for (const signal of privacySignalRows(view)) {
    const row = document.createElement("label");
    row.className = "privacy-settings__row";
    if (signal.disabled) {
      row.className += " privacy-settings__row-disabled";
    }

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = signal.checked;
    checkbox.disabled = signal.disabled;
    checkbox.addEventListener("change", () => {
      void actions.setSignalEnabled(signal.key, checkbox.checked);
    });

    const text = document.createElement("span");
    text.className = "privacy-settings__text";
    const label = document.createElement("strong");
    label.textContent = signal.label;
    const detail = document.createElement("span");
    detail.textContent = signal.detail;
    text.append(label, detail);

    const status = document.createElement("span");
    status.className = `privacy-settings__badge privacy-settings__badge-${signal.tone}`;
    status.textContent = signal.status;

    row.append(checkbox, text, status);
    section.append(row);
  }

  const exportButton = document.createElement("button");
  exportButton.type = "button";
  exportButton.disabled = !view.export_available;
  exportButton.textContent = "Export";
  exportButton.addEventListener("click", () => void actions.exportSession());

  const deleteButton = document.createElement("button");
  deleteButton.type = "button";
  deleteButton.disabled = !view.delete_available;
  deleteButton.textContent = "Delete";
  deleteButton.addEventListener("click", () => void actions.deleteSession());

  section.append(exportButton, deleteButton);
  container.replaceChildren(section);
}

function signalDisabled(key: keyof SignalSettings, view: PrivacySettingsView): boolean {
  if (key === "desktopWindowTitles") {
    return !view.signals.desktopActivity;
  }

  return key === "screenSnapshots";
}

function signalStatus(key: keyof SignalSettings, view: PrivacySettingsView, disabled: boolean): string {
  if (key === "screenSnapshots") {
    return "Deferred";
  }
  if (key === "desktopWindowTitles" && disabled) {
    return "Needs app context";
  }

  return view.signals[key] ? "On" : "Off";
}

function signalTone(key: keyof SignalSettings, view: PrivacySettingsView, disabled: boolean): PrivacySettingsTone {
  if (key === "screenSnapshots") {
    return "muted";
  }
  if (key === "desktopWindowTitles" && disabled) {
    return "muted";
  }
  if (key === "cloudSync" && view.signals.cloudSync) {
    return "warn";
  }

  return view.signals[key] ? "good" : "muted";
}

function formatSeconds(monotonicMs: number): string {
  return `${(monotonicMs / 1000).toFixed(1)}s`;
}
