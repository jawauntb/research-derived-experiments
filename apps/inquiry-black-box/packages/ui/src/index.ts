export type RecordingIndicatorView = {
  state: "idle" | "recording" | "paused" | "stopped";
  label: string;
  tone: "neutral" | "active" | "paused" | "done";
};

export function recordingIndicator(state: RecordingIndicatorView["state"]): RecordingIndicatorView {
  const labels = {
    idle: "Ready",
    recording: "Recording",
    paused: "Paused",
    stopped: "Stopped",
  } satisfies Record<RecordingIndicatorView["state"], string>;

  const tones = {
    idle: "neutral",
    recording: "active",
    paused: "paused",
    stopped: "done",
  } satisfies Record<RecordingIndicatorView["state"], RecordingIndicatorView["tone"]>;

  return { state, label: labels[state], tone: tones[state] };
}
