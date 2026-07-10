import {
  defaultSessionTitle,
  recordingIndicator,
  selfLabelDisplayName,
  type RecordingIndicatorView,
} from "@inquiry/ui";
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
  titleDraft: string;
  canEditTitle: boolean;
};

export type SessionControlsActions = {
  startSession: (title: string) => void | Promise<void>;
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

export function sessionControlsViewModel(
  session: SessionRecord | null,
  titleDraft = "",
): SessionControlsViewModel {
  const state = session?.recording_state ?? "idle";
  return {
    indicator: recordingIndicator(state),
    buttons: [
      { command: "start", label: "Start recording", enabled: state === "idle" || state === "stopped", tone: "primary" },
      { command: "pause", label: "Pause", enabled: state === "recording", tone: "secondary" },
      { command: "resume", label: "Resume", enabled: state === "paused", tone: "secondary" },
      { command: "stop", label: "Stop", enabled: state === "recording" || state === "paused", tone: "danger" },
    ],
    labels: visibleSelfLabels,
    titleDraft: titleDraft || session?.title || defaultSessionTitle(),
    canEditTitle: state === "idle" || state === "stopped",
  };
}

export function renderSessionControls(
  root: HTMLElement,
  session: SessionRecord | null,
  actions: SessionControlsActions,
  titleDraft = "",
): void {
  const view = sessionControlsViewModel(session, titleDraft);
  const container = document.createElement("section");
  container.className = "session-controls";

  const headingRow = document.createElement("div");
  headingRow.className = "session-controls__header";
  const headingGroup = document.createElement("div");
  const eyebrow = document.createElement("span");
  eyebrow.className = "app-eyebrow";
  eyebrow.textContent = "Primary task";
  const heading = document.createElement("h2");
  heading.textContent = "Recording session";
  headingGroup.append(eyebrow, heading);
  const status = document.createElement("strong");
  status.className = `recording-state recording-state-${view.indicator.tone}`;
  status.textContent = view.indicator.label;
  status.setAttribute("aria-live", "polite");
  headingRow.append(headingGroup, status);
  container.append(headingRow);

  const helper = document.createElement("p");
  helper.className = "session-helper";
  helper.textContent = sessionHelper(view.indicator.state);
  container.append(helper);

  const titleField = document.createElement("label");
  titleField.className = "session-title-field";
  titleField.textContent = "Session title";
  const titleInput = document.createElement("input");
  titleInput.type = "text";
  titleInput.className = "session-title-input";
  titleInput.value = view.titleDraft;
  titleInput.disabled = !view.canEditTitle;
  titleInput.placeholder = defaultSessionTitle();
  titleInput.setAttribute("aria-label", "Session title");
  titleField.append(titleInput);
  container.append(titleField);

  const toolbar = document.createElement("div");
  toolbar.className = "session-toolbar";
  for (const button of view.buttons.filter((candidate) => candidate.enabled)) {
    const control = document.createElement("button");
    control.type = "button";
    control.textContent = button.label;
    control.className = `session-button session-button-${button.tone}`;
    control.addEventListener("click", () => {
      if (button.command === "start") {
        const nextTitle = titleInput.value.trim() || defaultSessionTitle();
        void actions.startSession(nextTitle);
        return;
      }
      void actionFor(button.command, actions)();
    });
    toolbar.append(control);
  }
  container.append(toolbar);

  if (view.indicator.state === "recording" || view.indicator.state === "paused") {
    const labelHeading = document.createElement("p");
    labelHeading.className = "session-labels__heading";
    labelHeading.textContent = "Mark this moment";
    container.append(labelHeading);

    const labels = document.createElement("div");
    labels.className = "session-labels";
    for (const label of view.labels) {
      const control = document.createElement("button");
      control.type = "button";
      control.textContent = selfLabelDisplayName(label);
      control.dataset.labelSlug = label;
      control.addEventListener("click", () => {
        void actions.addLabel(label);
      });
      labels.append(control);
    }
    container.append(labels);
  }

  root.replaceChildren(container);
}

function sessionHelper(state: RecordingIndicatorView["state"]): string {
  if (state === "recording") {
    return "Capture is active. Mark a moment when your understanding shifts.";
  }
  if (state === "paused") {
    return "Capture is paused. Resume when you are ready to continue.";
  }
  return "Name the inquiry, then start capturing private browser evidence.";
}

function actionFor(command: SessionCommand, actions: SessionControlsActions): () => void | Promise<void> {
  switch (command) {
    case "start":
      return () => actions.startSession(defaultSessionTitle());
    case "pause":
      return actions.pauseSession;
    case "resume":
      return actions.resumeSession;
    case "stop":
      return actions.stopSession;
  }
}
