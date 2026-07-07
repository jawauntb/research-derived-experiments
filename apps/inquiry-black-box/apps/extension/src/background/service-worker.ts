import { validateEvent, type EventEnvelope } from "@inquiry/schema";
import {
  BRIDGE_STATE_KEY,
  createStorageEventQueue,
  flushQueuedEvents,
  getBridgeState,
  isBridgeEventAllowed,
  normalizeBridgeState,
  saveBridgeState,
  type BridgeState,
  type EventQueue,
  type PrivacyToggles,
  type RecordingState,
  type StorageAreaLike,
} from "../lib/localBridge";
import {
  CONTENT_EVENTS_MESSAGE,
  CONTENT_SETTINGS_MESSAGE,
  CONTENT_SETTINGS_UPDATED_MESSAGE,
} from "../lib/messages";

const RETRY_ALARM_NAME = "inquiry-bridge-retry";
const RETRY_PERIOD_MINUTES = 0.25;
const REGISTERED_CONTENT_SCRIPT_ID = "inquiry-content-listener";

type RuntimeSender = {
  url?: string;
};

type RuntimeLike = {
  onMessage?: {
    addListener(
      listener: (message: unknown, sender: RuntimeSender, sendResponse: (response: unknown) => void) => true | void,
    ): void;
  };
};

type AlarmLike = {
  name: string;
};

type TabLike = {
  id?: number;
};

type TabsLike = {
  query(query: Record<string, unknown>, callback: (tabs: TabLike[]) => void): void;
  sendMessage?(tabId: number, message: unknown, callback?: (response: unknown) => void): Promise<unknown> | void;
};

type ChromeLike = {
  runtime?: RuntimeLike;
  storage?: {
    local?: StorageAreaLike;
  };
  tabs?: TabsLike;
  scripting?: ScriptingLike;
  alarms?: {
    create(name: string, info: { periodInMinutes: number }): void;
    onAlarm?: {
      addListener(listener: (alarm: AlarmLike) => void): void;
    };
  };
};

type ContentScriptRegistration = {
  id: string;
  matches: string[];
  js: string[];
  runAt: "document_idle";
  persistAcrossSessions: boolean;
  world: "ISOLATED";
};

type ScriptingLike = {
  registerContentScripts?(
    scripts: ContentScriptRegistration[],
    callback?: () => void,
  ): Promise<unknown> | void;
  unregisterContentScripts?(filter: { ids: string[] }, callback?: () => void): Promise<unknown> | void;
};

type BackgroundContext = {
  storage: StorageAreaLike;
  queue: EventQueue;
  tabs?: TabsLike;
  now: () => number;
};

export async function handleRuntimeMessage(
  message: unknown,
  sender: RuntimeSender,
  context: BackgroundContext,
): Promise<unknown> {
  if (!isRecord(message)) {
    return { ok: false, error: "unsupported message" };
  }

  const state = await getBridgeState(context.storage);
  switch (message.type) {
    case CONTENT_EVENTS_MESSAGE:
      return enqueueContentEvents(message, state, context);
    case CONTENT_SETTINGS_MESSAGE:
      return contentSettingsFor(state, message);
    case "inquiry:get-popup-state":
      return {
        ...state,
        queueSize: await context.queue.size(),
        senderUrl: sender.url,
      };
    case "inquiry:set-pairing-token":
      return updateState(context, state, {
        pairingToken: stringValue(message.token),
        endpoint: stringValue(message.endpoint) ?? state.endpoint,
        sessionId: stringValue(message.sessionId) ?? state.sessionId,
      });
    case "inquiry:set-recording-state":
      return updateRecordingState(context, state, recordingStateValue(message.recordingState), numberValue(message.pausedUntilMs));
    case "inquiry:set-site-disabled":
      return setSiteDisabled(context, state, stringValue(message.siteHash), Boolean(message.disabled));
    case "inquiry:set-privacy-toggles":
      return updateState(context, state, {
        privacyToggles: privacyTogglesValue(message.privacyToggles) ?? state.privacyToggles,
      });
    case "inquiry:flush-queue":
      return flushQueuedEvents(context.queue, state);
    default:
      return { ok: false, error: "unsupported message" };
  }
}

async function enqueueContentEvents(
  message: Record<string, unknown>,
  state: BridgeState,
  context: BackgroundContext,
): Promise<unknown> {
  const events = Array.isArray(message.events) ? message.events : [];
  const accepted: EventEnvelope[] = [];

  if (!state.pairingToken) {
    return {
      ok: true,
      accepted: 0,
      posted: 0,
      queued: await context.queue.size(),
      error: "extension is not paired with the local desktop bridge",
    };
  }

  for (const value of events) {
    const event = normalizeIncomingEvent(value, state);
    if (event && isBridgeEventAllowed(event, state, context.now())) {
      accepted.push(event);
    }
  }

  if (accepted.length > 0) {
    await context.queue.enqueue(accepted);
  }

  const flush = await flushQueuedEvents(context.queue, state);
  return {
    ok: true,
    accepted: accepted.length,
    posted: flush.posted,
    queued: flush.remaining,
    error: flush.error?.message,
  };
}

async function updateState(
  context: BackgroundContext,
  current: BridgeState,
  updates: Partial<BridgeState>,
): Promise<BridgeState & { ok: true }> {
  const next = normalizeBridgeState({
    ...current,
    ...updates,
    updatedAt: new Date(context.now()).toISOString(),
  });
  if (updates.recordingState && updates.recordingState !== "paused" && !("pausedUntilMs" in updates)) {
    delete next.pausedUntilMs;
  }
  await saveBridgeState(context.storage, next, BRIDGE_STATE_KEY);
  await broadcastContentSettings(context, next);
  return { ...next, ok: true };
}

async function updateRecordingState(
  context: BackgroundContext,
  state: BridgeState,
  recordingState: RecordingState | undefined,
  pausedUntilMs: number | undefined,
): Promise<BridgeState & { ok: true }> {
  const updates: Partial<BridgeState> = {
    recordingState: recordingState ?? state.recordingState,
  };

  if (typeof pausedUntilMs === "number") {
    updates.pausedUntilMs = pausedUntilMs;
  }

  return updateState(context, state, updates);
}

async function setSiteDisabled(
  context: BackgroundContext,
  state: BridgeState,
  siteHash: string | undefined,
  disabled: boolean,
): Promise<BridgeState & { ok: true }> {
  if (!siteHash) {
    return { ...(await getBridgeState(context.storage)), ok: true };
  }

  const disabledSiteHashes = new Set(state.disabledSiteHashes);
  if (disabled) {
    disabledSiteHashes.add(siteHash);
  } else {
    disabledSiteHashes.delete(siteHash);
  }

  return updateState(context, state, {
    disabledSiteHashes: [...disabledSiteHashes],
  });
}

function contentSettingsFor(state: BridgeState, request: Record<string, unknown>): {
  sessionId: string;
  recordingState: RecordingState;
  pausedUntilMs?: number;
  siteDisabled: boolean;
  privacyToggles: PrivacyToggles;
} {
  const hostnameHash = stringValue(request.hostnameHash);
  const urlHash = stringValue(request.urlHash);
  const settings = {
    sessionId: state.sessionId,
    recordingState: state.recordingState,
    siteDisabled:
      (hostnameHash ? state.disabledSiteHashes.includes(hostnameHash) : false) ||
      (urlHash ? state.disabledSiteHashes.includes(urlHash) : false),
    privacyToggles: state.privacyToggles,
  };

  if (typeof state.pausedUntilMs === "number") {
    return { ...settings, pausedUntilMs: state.pausedUntilMs };
  }

  return settings;
}

async function broadcastContentSettings(context: BackgroundContext, state: BridgeState): Promise<void> {
  const tabs = context.tabs;
  if (!tabs?.sendMessage) {
    return;
  }

  const settings = contentSettingsFor(state, {});
  const message = {
    type: CONTENT_SETTINGS_UPDATED_MESSAGE,
    settings,
  };
  const openTabs = await queryTabs(tabs);
  await Promise.all(
    openTabs
      .map((tab) => tab.id)
      .filter((tabId): tabId is number => typeof tabId === "number")
      .map((tabId) => sendTabMessage(tabs, tabId, message)),
  );
}

async function queryTabs(tabs: TabsLike): Promise<TabLike[]> {
  return await new Promise((resolve) => {
    tabs.query({}, (openTabs) => resolve(openTabs));
  });
}

async function sendTabMessage(tabs: TabsLike, tabId: number, message: unknown): Promise<void> {
  await new Promise<void>((resolve) => {
    try {
      const result = tabs.sendMessage?.(tabId, message, () => resolve());
      if (isPromiseLike(result)) {
        result.then(() => resolve(), () => resolve());
      } else if (result === undefined) {
        resolve();
      }
    } catch {
      resolve();
    }
  });
}

function normalizeIncomingEvent(value: unknown, state: BridgeState): EventEnvelope | null {
  try {
    validateEvent(value);
    const event = value.session_id === state.sessionId ? value : { ...value, session_id: state.sessionId };
    validateEvent(event);
    return event;
  } catch {
    return null;
  }
}

function installServiceWorker(): void {
  const chromeApi = readChrome();
  const storage = chromeApi?.storage?.local;
  if (!chromeApi?.runtime?.onMessage || !storage) {
    return;
  }

  const queue = createStorageEventQueue(storage);
  const context: BackgroundContext = {
    storage,
    queue,
    ...(chromeApi.tabs ? { tabs: chromeApi.tabs } : {}),
    now: () => Date.now(),
  };

  chromeApi.runtime.onMessage.addListener((message, sender, sendResponse) => {
    void handleRuntimeMessage(message, sender, context).then(sendResponse, (error) =>
      sendResponse({ ok: false, error: error instanceof Error ? error.message : String(error) }),
    );
    return true;
  });

  void ensureContentScriptRegistration(chromeApi.scripting);

  chromeApi.alarms?.create(RETRY_ALARM_NAME, { periodInMinutes: RETRY_PERIOD_MINUTES });
  chromeApi.alarms?.onAlarm?.addListener((alarm) => {
    if (alarm.name !== RETRY_ALARM_NAME) {
      return;
    }

    void getBridgeState(storage).then((state) => flushQueuedEvents(queue, state));
  });
}

export async function ensureContentScriptRegistration(scripting: ScriptingLike | undefined): Promise<boolean> {
  if (!scripting?.registerContentScripts) {
    return false;
  }

  await callScriptingApi((callback) => scripting.unregisterContentScripts?.({ ids: [REGISTERED_CONTENT_SCRIPT_ID] }, callback));
  return await callScriptingApi((callback) =>
    scripting.registerContentScripts?.(
      [
        {
          id: REGISTERED_CONTENT_SCRIPT_ID,
          matches: ["http://*/*", "https://*/*"],
          js: ["dist/content/index.js"],
          runAt: "document_idle",
          persistAcrossSessions: true,
          world: "ISOLATED",
        },
      ],
      callback,
    ),
  );
}

async function callScriptingApi(task: (callback: () => void) => Promise<unknown> | void | undefined): Promise<boolean> {
  return await new Promise((resolve) => {
    try {
      const result = task(() => resolve(true));
      if (isPromiseLike(result)) {
        result.then(() => resolve(true), () => resolve(false));
      } else if (result === undefined) {
        resolve(true);
      }
    } catch {
      resolve(false);
    }
  });
}

function readChrome(): ChromeLike | null {
  return (globalThis as { chrome?: ChromeLike }).chrome ?? null;
}

function stringValue(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

function numberValue(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function recordingStateValue(value: unknown): RecordingState | undefined {
  return value === "recording" || value === "paused" || value === "stopped" ? value : undefined;
}

function privacyTogglesValue(value: unknown): PrivacyToggles | undefined {
  if (!isRecord(value)) {
    return undefined;
  }

  return {
    browser: booleanValue(value.browser, true),
    typingMetrics: booleanValue(value.typingMetrics, true),
    selection: booleanValue(value.selection, true),
    media: booleanValue(value.media, true),
  };
}

function booleanValue(value: unknown, fallback: boolean): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isPromiseLike<T>(value: unknown): value is Promise<T> {
  return typeof value === "object" && value !== null && "then" in value;
}

installServiceWorker();
