import { createEvent, type EventEnvelope, type LabelPayload } from "@inquiry/schema";

export type SelfLabel = LabelPayload["label"];

export type GlobalHotkeyEventInput = {
  [key: string]: unknown;
  session_id: string;
  action: string;
  monotonic_ms: number;
  label?: SelfLabel;
  note?: string;
};

export type GlobalHotkeyBinding = {
  accelerator: string;
  action: "pause" | "resume" | "label";
  label?: SelfLabel;
};

export const selfLabels = [
  "flow",
  "overloaded",
  "confused-good",
  "confused-bad",
  "avoiding",
  "near-breakthrough",
  "tired",
] as const satisfies readonly SelfLabel[];

export const defaultGlobalHotkeyBindings: readonly GlobalHotkeyBinding[] = [
  { accelerator: "CommandOrControl+Shift+Space", action: "pause" },
  { accelerator: "CommandOrControl+Shift+Enter", action: "resume" },
  { accelerator: "CommandOrControl+Shift+1", action: "label", label: "flow" },
  { accelerator: "CommandOrControl+Shift+2", action: "label", label: "overloaded" },
  { accelerator: "CommandOrControl+Shift+3", action: "label", label: "confused-good" },
  { accelerator: "CommandOrControl+Shift+4", action: "label", label: "confused-bad" },
  { accelerator: "CommandOrControl+Shift+5", action: "label", label: "near-breakthrough" },
];

const labelSet = new Set<SelfLabel>(selfLabels);

export function createGlobalHotkeyEvent(input: GlobalHotkeyEventInput): EventEnvelope {
  switch (input.action) {
    case "label":
      return createLabelEvent(input);
    case "pause":
      return createSessionEvent(input, "session.paused");
    case "resume":
      return createSessionEvent(input, "session.resumed");
    default:
      throw new Error(`unsupported global hotkey action: ${input.action}`);
  }
}

function createLabelEvent(input: GlobalHotkeyEventInput): EventEnvelope<LabelPayload> {
  if (!input.label || !labelSet.has(input.label)) {
    throw new Error("global hotkey label must be one of the supported self-labels");
  }

  const payload: LabelPayload = { label: input.label };
  if (input.note !== undefined) {
    payload.note = input.note;
  }

  return createEvent({
    session_id: input.session_id,
    source: "desktop-hotkey",
    source_version: "desktop@0.1.0",
    monotonic_ms: input.monotonic_ms,
    event_type: "label.added",
    payload,
    privacy_class: "local-derived",
    retention_policy: "local-default",
  });
}

function createSessionEvent(input: GlobalHotkeyEventInput, eventType: "session.paused" | "session.resumed"): EventEnvelope {
  return createEvent({
    session_id: input.session_id,
    source: "desktop-hotkey",
    source_version: "desktop@0.1.0",
    monotonic_ms: input.monotonic_ms,
    event_type: eventType,
    payload: { trigger: "global-hotkey" },
    privacy_class: "local-derived",
    retention_policy: "local-default",
  });
}
