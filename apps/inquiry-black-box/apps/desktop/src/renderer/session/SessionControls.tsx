import { recordingIndicator, type RecordingIndicatorView } from "@inquiry/ui";
import type { LabelPayload, SessionRecord } from "@inquiry/schema";

export type SessionCommand = "start" | "pause" | "resume" | "stop";
export type SelfLabel = LabelPayload["label"];

export type SessionButton = {
  command: SessionCommand;
  label: string;
  enabled: boolean;
  tone: "primary" | "secondary" | "danger";
};

export type SessionControlsViewModel = {
  indicator: RecordingIndicatorView;
  buttons: SessionButton[];
  labels: readonly SelfLabel[];
};

export type SessionControlsActions = {
  startSession: () => void | Promise<void>;
  pauseSession: () => void | Promise<void>;
  resumeSession: () => void | Promise<void>;
  stopSession: () => void | Promise<void>;
  addLabel: (label: SelfLabel) => void | Promise<void>;
};

export const visibleSelfLabels = [
  "flow",
  "overloaded",
  "confused-good",
  "confused-bad",
  "avoiding",
  "near-breakthrough",
  "tired",
] as const satisfies readonly SelfLabel[];

export function sessionControlsViewModel(session: SessionRecord | null): SessionControlsViewModel {
  const state = session?.recording_state ?? "idle";
  return {
    indicator: recordingIndicator(state),
    buttons: [
      { command: "start", label: "Start", enabled: state === "idle" || state === "stopped", tone: "primary" },
      { command: "pause", label: "Pause", enabled: state === "recording", tone: "secondary" },
      { command: "resume", label: "Resume", enabled: state === "paused", tone: "secondary" },
      { command: "stop", label: "Stop", enabled: state === "recording" || state === "paused", tone: "danger" },
    ],
    labels: visibleSelfLabels,
  };
}

export function renderSessionControls(
  root: HTMLElement,
  session: SessionRecord | null,
  actions: SessionControlsActions,
): void {
  const view = sessionControlsViewModel(session);
  const container = document.createElement("section");
  container.className = "session-controls";

  const status = document.createElement("strong");
  status.className = `recording-state recording-state-${view.indicator.tone}`;
  status.textContent = view.indicator.label;
  status.setAttribute("aria-live", "polite");
  container.append(status);

  const toolbar = document.createElement("div");
  toolbar.className = "session-toolbar";
  for (const button of view.buttons) {
    const control = document.createElement("button");
    control.type = "button";
    control.textContent = button.label;
    control.disabled = !button.enabled;
    control.className = `session-button session-button-${button.tone}`;
    control.addEventListener("click", () => {
      void actionFor(button.command, actions)();
    });
    toolbar.append(control);
  }
  container.append(toolbar);

  const labels = document.createElement("div");
  labels.className = "session-labels";
  for (const label of view.labels) {
    const control = document.createElement("button");
    control.type = "button";
    control.textContent = label;
    control.disabled = view.indicator.state !== "recording" && view.indicator.state !== "paused";
    control.addEventListener("click", () => {
      void actions.addLabel(label);
    });
    labels.append(control);
  }
  container.append(labels);

  root.replaceChildren(container);
}

function actionFor(command: SessionCommand, actions: SessionControlsActions): () => void | Promise<void> {
  switch (command) {
    case "start":
      return actions.startSession;
    case "pause":
      return actions.pauseSession;
    case "resume":
      return actions.resumeSession;
    case "stop":
      return actions.stopSession;
  }
}
