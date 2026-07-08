import { createEvent, type EventEnvelope, type EventType, type JsonObject } from "@inquiry/schema";
import {
  DEFAULT_SESSION_ID,
  disabledPrivacyToggles,
  type PrivacyToggles,
  type RecordingState,
} from "../lib/localBridge";
import {
  CONTENT_EVENTS_MESSAGE,
  CONTENT_PING_MESSAGE,
  CONTENT_PONG_MESSAGE,
  CONTENT_SETTINGS_MESSAGE,
  CONTENT_SETTINGS_UPDATED_MESSAGE,
} from "../lib/messages";
import { hashForTelemetry } from "../lib/telemetry";

export const SOURCE_VERSION = "extension@0.1.0";

export type ContentEventMessage = {
  type: typeof CONTENT_EVENTS_MESSAGE;
  events: EventEnvelope[];
};

export type ContentSettings = {
  sessionId: string;
  recordingState: RecordingState;
  pausedUntilMs?: number;
  siteDisabled: boolean;
  privacyToggles: PrivacyToggles;
};

export type ContentTelemetryOptions = {
  sessionId?: string;
  now?: () => number;
  wallClockNow?: () => number;
  sendMessage: (message: ContentEventMessage) => void | Promise<void>;
  location?: Pick<Location, "href" | "hostname">;
  visibilityState?: () => "visible" | "hidden" | "prerender" | "unloaded";
  settings?: Partial<ContentSettings>;
};

export type ScrollSnapshot = {
  scrollX?: number;
  scrollY: number;
  viewportHeight: number;
  viewportWidth?: number;
  documentHeight?: number;
};

export type MediaAction = "play" | "pause" | "seeking" | "seeked";

export type MediaElementLike = {
  tagName?: string;
  currentTime?: number;
  duration?: number;
  paused?: boolean;
  playbackRate?: number;
};

export type SelectionKind = "selection" | "copy" | "highlight";

export type SelectionMetrics = {
  selectionLength: number;
  rangeCount?: number;
  selectedText?: string;
};

export type EditableElementLike = {
  tagName?: string;
  type?: string;
  value?: string;
  isContentEditable?: boolean;
  getAttribute?: (name: string) => string | null;
};

export type KeyboardInput = {
  key: string;
  target: EditableElementLike | null;
};

export type TypingInput = {
  target: EditableElementLike | null;
  inputType?: string;
};

const CONTENT_SCRIPT_INSTALLED_KEY = "__inquiryBlackBoxContentInstalled";

type EventCategory = "browser" | "typingMetrics" | "selection" | "media";
type EmitOptions = {
  privacyClass?: EventEnvelope["privacy_class"];
  retentionPolicy?: EventEnvelope["retention_policy"];
};

type TypingState = {
  burstLength: number;
  backspaceCount: number;
  pendingDeletes: number;
  firstInputAt: number | null;
  lastInputAt: number | null;
  lastKeyAt: number | null;
  lastLength: number | null;
  editDistance: number;
};

export function createContentTelemetry(options: ContentTelemetryOptions): ContentTelemetry {
  return new ContentTelemetry(options);
}

export class ContentTelemetry {
  private readonly now: () => number;
  private readonly wallClockNow: () => number;
  private readonly sendMessage: (message: ContentEventMessage) => void | Promise<void>;
  private readonly location: Pick<Location, "href" | "hostname">;
  private readonly visibilityState: () => "visible" | "hidden" | "prerender" | "unloaded";
  private readonly typingByElement = new WeakMap<object, TypingState>();
  private readonly mediaTimeByElement = new WeakMap<object, number>();
  private settings: ContentSettings;
  private visibleSinceMs: number;
  private lastScrollY: number | null = null;

  constructor(options: ContentTelemetryOptions) {
    this.now = options.now ?? (() => performance.now());
    this.wallClockNow = options.wallClockNow ?? (() => Date.now());
    this.sendMessage = options.sendMessage;
    this.location = options.location ?? globalThis.location;
    this.visibilityState = options.visibilityState ?? (() => readDocumentVisibility());
    const initialSettings: Partial<ContentSettings> = { ...options.settings };
    if (options.sessionId) {
      initialSettings.sessionId = options.sessionId;
    }
    this.settings = normalizeContentSettings(initialSettings);
    this.visibleSinceMs = this.now();
  }

  setSettings(settings: Partial<ContentSettings>): void {
    this.settings = normalizeContentSettings({
      ...this.settings,
      ...settings,
      privacyToggles: {
        ...this.settings.privacyToggles,
        ...settings.privacyToggles,
      },
    });
  }

  captureScroll(snapshot: ScrollSnapshot): EventEnvelope | null {
    const scrollY = finiteNumber(snapshot.scrollY);
    const deltaY = this.lastScrollY === null ? 0 : scrollY - this.lastScrollY;
    this.lastScrollY = scrollY;

    return this.emit("browser.scroll", "browser", {
      ...this.commonPayload(),
      scroll_y: scrollY,
      delta_y: finiteNumber(deltaY),
      scroll_x: finiteNumber(snapshot.scrollX ?? 0),
      viewport_h: finiteNumber(snapshot.viewportHeight),
      viewport_w: finiteNumber(snapshot.viewportWidth ?? 0),
      document_h: finiteNumber(snapshot.documentHeight ?? snapshot.viewportHeight),
      scroll_ratio: scrollRatio(snapshot),
    });
  }

  captureVisibility(visible = this.visibilityState() === "visible", lifecycle = "visibilitychange"): EventEnvelope | null {
    const now = this.now();
    const dwellMs = Math.max(0, now - this.visibleSinceMs);
    if (visible) {
      this.visibleSinceMs = now;
    }

    const state = lifecycle === "pageshow" ? "revisited" : visible ? "visible" : "hidden";
    return this.emit("browser.visibility", "browser", {
      ...this.commonPayload(),
      state,
      visible,
      dwell_ms: finiteNumber(dwellMs),
      lifecycle,
    });
  }

  captureMedia(action: MediaAction, media: MediaElementLike): EventEnvelope | null {
    const currentTimeS = finiteNumber(media.currentTime ?? 0);
    const previousTimeS = typeof media === "object" && media !== null ? this.mediaTimeByElement.get(media) : undefined;
    if (typeof media === "object" && media !== null) {
      this.mediaTimeByElement.set(media, currentTimeS);
    }

    return this.emit("browser.media", "media", {
      ...this.commonPayload(),
      action,
      media_kind: mediaKind(media),
      current_time_s: currentTimeS,
      delta_ms: finiteNumber(previousTimeS === undefined ? 0 : (currentTimeS - previousTimeS) * 1_000),
      duration_s: finiteNumber(media.duration ?? 0),
      paused: Boolean(media.paused),
      playback_rate: finiteNumber(media.playbackRate ?? 1),
    });
  }

  captureSelection(kind: SelectionKind, metrics: SelectionMetrics): EventEnvelope | null {
    if (metrics.selectionLength <= 0) {
      return null;
    }

    const eventType = selectionEventType(kind);
    const optedInText = selectedTextPayload(kind, metrics, this.settings.privacyToggles.selectedText);
    return this.emit(eventType, "selection", {
      ...this.commonPayload(),
      selection_length: finiteNumber(metrics.selectionLength),
      range_count: finiteNumber(metrics.rangeCount ?? 0),
      ...optedInText.payload,
    }, optedInText.enabled ? { privacyClass: "document-opt-in", retentionPolicy: "session-delete" } : {});
  }

  recordKeydown(input: KeyboardInput): void {
    const target = editableTarget(input.target);
    if (!target) {
      return;
    }

    const state = this.typingState(target);
    state.lastKeyAt = this.now();
    if (input.key === "Backspace" || input.key === "Delete") {
      state.pendingDeletes += 1;
    }
  }

  captureTypingInput(input: TypingInput): EventEnvelope | null {
    const target = editableTarget(input.target);
    if (!target) {
      return null;
    }

    const now = this.now();
    const state = this.typingState(target);
    const currentLength = editableLength(target);
    const previousLength = state.lastLength ?? currentLength;
    const pauseMs = state.lastInputAt === null ? Math.max(0, now - (state.lastKeyAt ?? now)) : now - state.lastInputAt;

    state.burstLength += 1;
    if (input.inputType?.startsWith("delete") && state.pendingDeletes === 0) {
      state.pendingDeletes += 1;
    }

    state.backspaceCount += state.pendingDeletes;
    state.pendingDeletes = 0;
    state.firstInputAt ??= now;
    state.editDistance += Math.abs(currentLength - previousLength);
    state.lastInputAt = now;
    state.lastLength = currentLength;

    return this.emit("browser.typing_metrics", "typingMetrics", {
      ...this.commonPayload(),
      field_role: fieldRole(target),
      burst_length: state.burstLength,
      pause_ms: finiteNumber(pauseMs),
      backspace_count: state.backspaceCount,
      edit_churn: churnRatio(state.editDistance, currentLength, previousLength),
      duration_ms: finiteNumber(now - state.firstInputAt),
      input_events: state.burstLength,
    });
  }

  private emit(eventType: EventType, category: EventCategory, payload: JsonObject, options: EmitOptions = {}): EventEnvelope | null {
    if (!this.canCapture(category)) {
      return null;
    }

    const event = createEvent({
      session_id: this.settings.sessionId,
      source: "browser",
      source_version: SOURCE_VERSION,
      monotonic_ms: Math.max(0, this.now()),
      event_type: eventType,
      payload,
      privacy_class: options.privacyClass ?? "local-derived",
      retention_policy: options.retentionPolicy ?? "local-default",
    });

    void this.sendMessage({ type: CONTENT_EVENTS_MESSAGE, events: [event] });
    return event;
  }

  private commonPayload(): JsonObject {
    return {
      url_hash: hashForTelemetry(this.location.href),
      hostname_hash: hashForTelemetry(this.location.hostname),
      visible: this.visibilityState() === "visible",
    };
  }

  private canCapture(category: EventCategory): boolean {
    const pausedExpired =
      this.settings.recordingState === "paused" &&
      typeof this.settings.pausedUntilMs === "number" &&
      this.settings.pausedUntilMs <= this.wallClockNow();
    const recording = this.settings.recordingState === "recording" || pausedExpired;
    if (!recording || this.settings.siteDisabled) {
      return false;
    }

    if (!this.settings.privacyToggles.browser) {
      return false;
    }

    if (category === "typingMetrics") {
      return this.settings.privacyToggles.typingMetrics;
    }

    if (category === "selection") {
      return this.settings.privacyToggles.selection;
    }

    if (category === "media") {
      return this.settings.privacyToggles.media;
    }

    return true;
  }

  private typingState(target: object): TypingState {
    const existing = this.typingByElement.get(target);
    if (existing) {
      return existing;
    }

    const state: TypingState = {
      burstLength: 0,
      backspaceCount: 0,
      pendingDeletes: 0,
      firstInputAt: null,
      lastInputAt: null,
      lastKeyAt: null,
      lastLength: editableLength(target as EditableElementLike),
      editDistance: 0,
    };
    this.typingByElement.set(target, state);
    return state;
  }
}

function normalizeContentSettings(input: Partial<ContentSettings>): ContentSettings {
  const toggles: Partial<PrivacyToggles> = input.privacyToggles ?? {};
  const settings: ContentSettings = {
    sessionId: input.sessionId && input.sessionId.length > 0 ? input.sessionId : DEFAULT_SESSION_ID,
    recordingState: input.recordingState ?? "stopped",
    siteDisabled: input.siteDisabled ?? false,
    privacyToggles: {
      browser: typeof toggles.browser === "boolean" ? toggles.browser : disabledPrivacyToggles.browser,
      typingMetrics:
        typeof toggles.typingMetrics === "boolean" ? toggles.typingMetrics : disabledPrivacyToggles.typingMetrics,
      selection: typeof toggles.selection === "boolean" ? toggles.selection : disabledPrivacyToggles.selection,
      selectedText:
        typeof toggles.selectedText === "boolean" ? toggles.selectedText : disabledPrivacyToggles.selectedText,
      media: typeof toggles.media === "boolean" ? toggles.media : disabledPrivacyToggles.media,
    },
  };

  if (typeof input.pausedUntilMs === "number" && Number.isFinite(input.pausedUntilMs)) {
    settings.pausedUntilMs = input.pausedUntilMs;
  }

  return settings;
}

function selectionEventType(kind: SelectionKind): EventType {
  if (kind === "copy") {
    return "browser.copy";
  }

  if (kind === "highlight") {
    return "browser.highlight";
  }

  return "browser.selection";
}

const MAX_SELECTED_TEXT_CHARS = 2_000;

function selectedTextPayload(
  kind: SelectionKind,
  metrics: SelectionMetrics,
  enabled: boolean,
): { enabled: boolean; payload: JsonObject } {
  if (!enabled || kind === "selection" || typeof metrics.selectedText !== "string") {
    return { enabled: false, payload: {} };
  }

  const normalized = normalizeSelectedText(metrics.selectedText);
  if (normalized.length === 0) {
    return { enabled: false, payload: {} };
  }

  const selectedText = normalized.slice(0, MAX_SELECTED_TEXT_CHARS);
  return {
    enabled: true,
    payload: {
      selected_text: selectedText,
      selected_text_char_count: normalized.length,
      selected_text_truncated: normalized.length > selectedText.length,
      document_opt_in: true,
    },
  };
}

function normalizeSelectedText(value: string): string {
  return value.replace(/\u0000/g, "").replace(/\r\n?/g, "\n").trim();
}

function mediaKind(media: MediaElementLike): "audio" | "video" {
  return media.tagName?.toUpperCase() === "AUDIO" ? "audio" : "video";
}

function fieldRole(target: EditableElementLike): string {
  const tagName = target.tagName?.toUpperCase();
  if (target.isContentEditable) {
    return "contenteditable";
  }

  if (tagName === "TEXTAREA") {
    return "textarea";
  }

  const type = target.type?.toLowerCase() ?? target.getAttribute?.("type")?.toLowerCase() ?? "text";
  if (type === "search" || type === "email" || type === "url" || type === "password" || type === "number") {
    return type;
  }

  return "text";
}

function editableTarget(target: EditableElementLike | null): EditableElementLike | null {
  if (!target) {
    return null;
  }

  const tagName = target.tagName?.toUpperCase();
  if (target.isContentEditable || tagName === "INPUT" || tagName === "TEXTAREA") {
    return target;
  }

  return null;
}

function editableLength(target: EditableElementLike): number {
  if (typeof target.value === "string") {
    return target.value.length;
  }

  return 0;
}

function scrollRatio(snapshot: ScrollSnapshot): number {
  const viewportHeight = finiteNumber(snapshot.viewportHeight);
  const documentHeight = finiteNumber(snapshot.documentHeight ?? viewportHeight);
  const scrollable = Math.max(1, documentHeight - viewportHeight);
  return Math.min(1, Math.max(0, finiteNumber(snapshot.scrollY) / scrollable));
}

function churnRatio(editDistance: number, currentLength: number, previousLength: number): number {
  const denominator = Math.max(1, currentLength, previousLength);
  return Math.round((editDistance / denominator) * 1_000) / 1_000;
}

function finiteNumber(value: number): number {
  return Number.isFinite(value) ? value : 0;
}

function readDocumentVisibility(): "visible" | "hidden" | "prerender" | "unloaded" {
  if (typeof document === "undefined") {
    return "visible";
  }

  return document.visibilityState;
}

function installContentScript(): void {
  if (typeof document === "undefined" || typeof window === "undefined") {
    return;
  }

  const globalState = globalThis as Record<string, unknown>;
  if (globalState[CONTENT_SCRIPT_INSTALLED_KEY]) {
    return;
  }

  const runtime = readRuntime();
  if (!runtime) {
    return;
  }
  globalState[CONTENT_SCRIPT_INSTALLED_KEY] = true;

  const telemetry = createContentTelemetry({
    sendMessage: (message) => {
      void sendRuntimeMessage(runtime, message);
    },
    location: window.location,
    now: () => performance.now(),
  });

  void sendRuntimeMessage(runtime, {
    type: CONTENT_SETTINGS_MESSAGE,
    hostnameHash: hashForTelemetry(window.location.hostname),
    urlHash: hashForTelemetry(window.location.href),
  }).then((response) => {
    if (isContentSettings(response)) {
      telemetry.setSettings(response);
    }
  });

  runtime.onMessage?.addListener((message, _sender, sendResponse) => {
    if (isSettingsUpdate(message)) {
      telemetry.setSettings(message.settings);
      return;
    }

    if (isContentPing(message)) {
      sendResponse?.({ type: CONTENT_PONG_MESSAGE, ok: true });
    }
  });

  window.addEventListener(
    "scroll",
    () => {
      telemetry.captureScroll(readScrollSnapshot());
    },
    { passive: true },
  );
  window.addEventListener("pagehide", () => telemetry.captureVisibility(false, "pagehide"));
  window.addEventListener("pageshow", () => telemetry.captureVisibility(true, "pageshow"));
  document.addEventListener("visibilitychange", () => telemetry.captureVisibility(), true);
  document.addEventListener("play", (event) => captureMediaEvent(telemetry, "play", event), true);
  document.addEventListener("pause", (event) => captureMediaEvent(telemetry, "pause", event), true);
  document.addEventListener("seeking", (event) => captureMediaEvent(telemetry, "seeking", event), true);
  document.addEventListener("seeked", (event) => captureMediaEvent(telemetry, "seeked", event), true);
  document.addEventListener("selectionchange", () => telemetry.captureSelection("selection", readSelectionMetrics()), true);
  document.addEventListener("copy", () => telemetry.captureSelection("copy", readSelectionMetrics()), true);
  document.addEventListener("mouseup", () => telemetry.captureSelection("highlight", readSelectionMetrics()), true);
  document.addEventListener("keyup", () => telemetry.captureSelection("highlight", readSelectionMetrics()), true);
  document.addEventListener("keydown", (event) => telemetry.recordKeydown(readKeyboardInput(event)), true);
  document.addEventListener("input", (event) => telemetry.captureTypingInput(readTypingInput(event)), true);
}

function readScrollSnapshot(): ScrollSnapshot {
  const documentElement = document.documentElement;
  return {
    scrollX: window.scrollX,
    scrollY: window.scrollY,
    viewportHeight: window.innerHeight,
    viewportWidth: window.innerWidth,
    documentHeight: Math.max(documentElement.scrollHeight, document.body?.scrollHeight ?? 0),
  };
}

function captureMediaEvent(telemetry: ContentTelemetry, action: MediaAction, event: Event): void {
  const target = event.target;
  if (isMediaElement(target)) {
    telemetry.captureMedia(action, target);
  }
}

function readSelectionMetrics(): SelectionMetrics {
  const selection = document.getSelection();
  const selectedText = selection?.toString() ?? "";
  return {
    selectionLength: selectedText.length,
    rangeCount: selection?.rangeCount ?? 0,
    selectedText,
  };
}

function readKeyboardInput(event: Event): KeyboardInput {
  const keyboardEvent = event as KeyboardEvent;
  return {
    key: keyboardEvent.key,
    target: keyboardEvent.target as EditableElementLike | null,
  };
}

function readTypingInput(event: Event): TypingInput {
  const inputEvent = event as InputEvent;
  return {
    inputType: inputEvent.inputType,
    target: inputEvent.target as EditableElementLike | null,
  };
}

function isMediaElement(target: EventTarget | null): target is HTMLMediaElement {
  return target instanceof HTMLMediaElement;
}

type RuntimeLike = {
  sendMessage(message: unknown, callback?: (response: unknown) => void): Promise<unknown> | void;
  onMessage?: {
    addListener(listener: (message: unknown, sender?: unknown, sendResponse?: (response: unknown) => void) => void): void;
  };
};

function readRuntime(): RuntimeLike | null {
  return (globalThis as { chrome?: { runtime?: RuntimeLike } }).chrome?.runtime ?? null;
}

async function sendRuntimeMessage(runtime: RuntimeLike, message: unknown): Promise<unknown> {
  return await new Promise((resolve, reject) => {
    try {
      const result = runtime.sendMessage(message, (response) => resolve(response));
      if (isPromiseLike(result)) {
        result.then(resolve, reject);
      }
    } catch (error) {
      reject(error);
    }
  });
}

function isSettingsUpdate(value: unknown): value is { type: typeof CONTENT_SETTINGS_UPDATED_MESSAGE; settings: Partial<ContentSettings> } {
  return (
    typeof value === "object" &&
    value !== null &&
    (value as { type?: unknown }).type === CONTENT_SETTINGS_UPDATED_MESSAGE &&
    typeof (value as { settings?: unknown }).settings === "object"
  );
}

function isContentPing(value: unknown): value is { type: typeof CONTENT_PING_MESSAGE } {
  return typeof value === "object" && value !== null && (value as { type?: unknown }).type === CONTENT_PING_MESSAGE;
}

function isContentSettings(value: unknown): value is ContentSettings {
  return typeof value === "object" && value !== null && "privacyToggles" in value;
}

function isPromiseLike<T>(value: unknown): value is Promise<T> {
  return typeof value === "object" && value !== null && "then" in value;
}

installContentScript();
