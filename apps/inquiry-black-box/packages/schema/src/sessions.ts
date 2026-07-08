export const recordingStates = ["idle", "recording", "paused", "stopped"] as const;
export type RecordingState = (typeof recordingStates)[number];

export type SessionRecord = {
  session_id: string;
  title: string;
  active_task?: string;
  notes?: string;
  started_at: string;
  ended_at?: string;
  recording_state: RecordingState;
  created_at: string;
  updated_at: string;
};

export type SignalSettings = {
  browser: boolean;
  camera: boolean;
  desktopActivity: boolean;
  desktopWindowTitles: boolean;
  llmDocumentContext: boolean;
  screenSnapshots: boolean;
  typingMetrics: boolean;
  notifications: boolean;
  cloudSync: boolean;
};

export const signalSettingKeys = [
  "browser",
  "camera",
  "desktopActivity",
  "desktopWindowTitles",
  "llmDocumentContext",
  "screenSnapshots",
  "typingMetrics",
  "notifications",
  "cloudSync",
] as const satisfies ReadonlyArray<keyof SignalSettings>;

export function defaultSignalSettings(): SignalSettings {
  return {
    browser: true,
    camera: false,
    desktopActivity: false,
    desktopWindowTitles: false,
    llmDocumentContext: false,
    screenSnapshots: false,
    typingMetrics: true,
    notifications: false,
    cloudSync: false,
  };
}

export function isSignalSettingKey(value: unknown): value is keyof SignalSettings {
  return typeof value === "string" && signalSettingKeys.includes(value as keyof SignalSettings);
}

export function normalizeSignalSettings(settings: SignalSettings): SignalSettings {
  return {
    ...settings,
    desktopWindowTitles: settings.desktopActivity && settings.desktopWindowTitles,
    screenSnapshots: false,
  };
}

export function applySignalSettingChange(
  current: SignalSettings,
  key: keyof SignalSettings,
  enabled: boolean,
): SignalSettings {
  if (!isSignalSettingKey(key)) {
    throw new Error(`unsupported signal setting: ${String(key)}`);
  }

  return normalizeSignalSettings({
    ...current,
    [key]: key === "screenSnapshots" ? false : enabled,
  });
}

export function createSessionRecord(input: {
  title: string;
  active_task?: string;
  notes?: string;
  session_id?: string;
  started_at?: string;
}): SessionRecord {
  const now = new Date().toISOString();
  const record: SessionRecord = {
    session_id: input.session_id ?? crypto.randomUUID(),
    title: input.title,
    started_at: input.started_at ?? now,
    recording_state: "recording",
    created_at: now,
    updated_at: now,
  };

  if (input.active_task !== undefined) {
    record.active_task = input.active_task;
  }

  if (input.notes !== undefined) {
    record.notes = input.notes;
  }

  return record;
}

export function isRecordingState(value: unknown): value is RecordingState {
  return typeof value === "string" && recordingStates.includes(value as RecordingState);
}
