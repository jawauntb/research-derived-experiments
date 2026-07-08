export type RecordingIndicatorView = {
  state: "idle" | "recording" | "paused" | "stopped";
  label: string;
  tone: "neutral" | "active" | "paused" | "done";
};

export const designTokens = {
  surface: "#f3f1eb",
  surfaceRaised: "#fbfaf6",
  surfaceInset: "#e7e3da",
  ink: "#151515",
  muted: "#68645d",
  line: "#d6d0c4",
  teal: "#087d73",
  tealBright: "#0f6b55",
  tealSoft: "#dceee8",
  amber: "#8a5b00",
  amberSoft: "#fff3cf",
  rose: "#a83347",
  roseSoft: "#f9dfe5",
  blue: "#2d5d7c",
  blueSoft: "#dceaf7",
  shadowRaised: "14px 14px 30px rgba(124, 112, 96, 0.22), -14px -14px 30px rgba(255, 255, 255, 0.86)",
  shadowPressed: "inset 8px 8px 18px rgba(124, 112, 96, 0.18), inset -8px -8px 18px rgba(255, 255, 255, 0.78)",
  focusRing: "0 0 0 3px rgba(8, 125, 115, 0.24)",
} as const;

export type InquiryCssVariableName =
  | "--surface"
  | "--surface-raised"
  | "--surface-inset"
  | "--ink"
  | "--muted"
  | "--line"
  | "--teal"
  | "--green"
  | "--green-soft"
  | "--amber"
  | "--amber-soft"
  | "--rose"
  | "--rose-soft"
  | "--blue"
  | "--blue-soft"
  | "--shadow-raised"
  | "--shadow-pressed"
  | "--focus";

export function inquiryCssVariables(): Record<InquiryCssVariableName, string> {
  return {
    "--surface": designTokens.surface,
    "--surface-raised": designTokens.surfaceRaised,
    "--surface-inset": designTokens.surfaceInset,
    "--ink": designTokens.ink,
    "--muted": designTokens.muted,
    "--line": designTokens.line,
    "--teal": designTokens.teal,
    "--green": designTokens.tealBright,
    "--green-soft": designTokens.tealSoft,
    "--amber": designTokens.amber,
    "--amber-soft": designTokens.amberSoft,
    "--rose": designTokens.rose,
    "--rose-soft": designTokens.roseSoft,
    "--blue": designTokens.blue,
    "--blue-soft": designTokens.blueSoft,
    "--shadow-raised": designTokens.shadowRaised,
    "--shadow-pressed": designTokens.shadowPressed,
    "--focus": designTokens.focusRing,
  };
}

export function inquiryCssVariableBlock(selector = ":root"): string {
  const variables = Object.entries(inquiryCssVariables())
    .map(([name, value]) => `  ${name}: ${value};`)
    .join("\n");
  return `${selector} {\n${variables}\n}`;
}

export const READING_ENGAGEMENT_MAP_TITLE = "Reading engagement map";

const recordingLabels = {
  idle: "Ready",
  recording: "Recording",
  paused: "Paused",
  stopped: "Stopped",
} satisfies Record<RecordingIndicatorView["state"], string>;

const recordingTones = {
  idle: "neutral",
  recording: "active",
  paused: "paused",
  stopped: "done",
} satisfies Record<RecordingIndicatorView["state"], RecordingIndicatorView["tone"]>;

export function recordingIndicator(state: RecordingIndicatorView["state"]): RecordingIndicatorView {
  return { state, label: recordingLabels[state], tone: recordingTones[state] };
}

export type SelfLabelSlug =
  | "flow"
  | "overloaded"
  | "confused-good"
  | "confused-bad"
  | "avoiding"
  | "near-breakthrough"
  | "tired";

const selfLabelNames: Record<SelfLabelSlug, string> = {
  flow: "Flow",
  overloaded: "Overloaded",
  "confused-good": "Confused (productive)",
  "confused-bad": "Confused (stuck)",
  avoiding: "Avoiding",
  "near-breakthrough": "Near breakthrough",
  tired: "Tired",
};

export function selfLabelDisplayName(label: string): string {
  return selfLabelNames[label as SelfLabelSlug] ?? label.replace(/-/g, " ");
}

export type ConfidenceBand = {
  label: "Low" | "Medium" | "High";
  detail: string;
};

export function confidenceBand(value: number): ConfidenceBand {
  const percent = Math.round(value * 100);
  if (value < 0.45) {
    return { label: "Low", detail: `${percent}% confidence` };
  }
  if (value < 0.75) {
    return { label: "Medium", detail: `${percent}% confidence` };
  }
  return { label: "High", detail: `${percent}% confidence` };
}

export function maskPairingToken(token: string, revealed: boolean): string {
  if (revealed || token.length <= 8) {
    return token;
  }
  return `${token.slice(0, 4)}…${token.slice(-4)}`;
}

export type SessionTransportCommand = "record" | "pause" | "resume" | "stop";

export type SessionTransportButton = {
  command: SessionTransportCommand;
  label: string;
  enabled: boolean;
  active: boolean;
  tone: "primary" | "secondary" | "danger";
};

export function sessionTransportButtons(state: RecordingIndicatorView["state"]): SessionTransportButton[] {
  return [
    {
      command: "record",
      label: "Record",
      enabled: state === "idle" || state === "stopped",
      active: state === "recording",
      tone: "primary",
    },
    {
      command: "pause",
      label: "Pause",
      enabled: state === "recording",
      active: state === "paused",
      tone: "secondary",
    },
    {
      command: "resume",
      label: "Resume",
      enabled: state === "paused",
      active: false,
      tone: "secondary",
    },
    {
      command: "stop",
      label: "Stop",
      enabled: state === "recording" || state === "paused",
      active: false,
      tone: "danger",
    },
  ];
}

export type PrivacySignalKey =
  | "selectedText"
  | "desktopActivity"
  | "desktopWindowTitles"
  | "camera"
  | "browser";

export type PrivacyUpgradeHint = {
  signalKey: PrivacySignalKey;
  title: string;
  detail: string;
};

export function privacyUpgradeHintForText(limitation: string): PrivacyUpgradeHint | null {
  const lower = limitation.toLowerCase();
  if (
    lower.includes("selected") ||
    lower.includes("copied") ||
    lower.includes("passage") ||
    lower.includes("excerpt")
  ) {
    return {
      signalKey: "selectedText",
      title: "Enable selected-text excerpts",
      detail:
        "Allow bounded selected or copied text locally so replay can name the passage. Raw page capture stays off by default.",
    };
  }
  return null;
}

export function siteCaptureLabel(hostname: string, paused: boolean): string {
  return paused ? `Capture paused on ${hostname}` : `Pause capture on ${hostname}`;
}

export function defaultSessionTitle(context?: { hostname?: string; pageTitle?: string }): string {
  if (context?.pageTitle && context.pageTitle.trim().length > 0) {
    return context.pageTitle.trim().slice(0, 80);
  }
  if (context?.hostname) {
    return `Session on ${context.hostname}`;
  }
  const now = new Date();
  return `Session ${now.toLocaleDateString()} ${now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
}
