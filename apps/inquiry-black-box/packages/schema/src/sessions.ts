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
  typingMetrics: boolean;
  notifications: boolean;
  cloudSync: boolean;
};

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
