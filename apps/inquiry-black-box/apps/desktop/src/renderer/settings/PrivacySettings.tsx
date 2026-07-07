import type { SignalSettings } from "@inquiry/schema";

export type PrivacySettingsView = {
  signals: SignalSettings;
  retention_days: number;
  recording_indicator_visible: boolean;
  cloud_sync_enabled: boolean;
  export_available: boolean;
  delete_available: boolean;
};

export type PrivacySettingsActions = {
  setSignalEnabled: (key: keyof SignalSettings, enabled: boolean) => void | Promise<void>;
  exportSession: () => void | Promise<void>;
  deleteSession: () => void | Promise<void>;
};

const signalLabels: Array<{ key: keyof SignalSettings; label: string }> = [
  { key: "browser", label: "Browser traces" },
  { key: "camera", label: "Camera features" },
  { key: "typingMetrics", label: "Typing rhythm" },
  { key: "notifications", label: "Notifications" },
  { key: "cloudSync", label: "Cloud sync" },
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
  const signals = { ...view.signals, [key]: enabled };
  return {
    ...view,
    signals,
    cloud_sync_enabled: signals.cloudSync,
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

  for (const signal of signalLabels) {
    const row = document.createElement("label");
    row.className = "privacy-settings__row";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = view.signals[signal.key];
    checkbox.addEventListener("change", () => {
      void actions.setSignalEnabled(signal.key, checkbox.checked);
    });

    const text = document.createElement("span");
    text.textContent = signal.label;
    row.append(checkbox, text);
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
