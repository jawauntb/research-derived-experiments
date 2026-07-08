import { selectedTextPayloadFieldNames, validateEvent, type EventEnvelope } from "@inquiry/schema";

export const DEFAULT_BRIDGE_ENDPOINT = "http://127.0.0.1:39170/v1/extension/events";
export const BRIDGE_STATE_KEY = "inquiry.bridge.state";
export const BRIDGE_QUEUE_KEY = "inquiry.bridge.queue";
export const DEFAULT_SESSION_ID = "local-browser-session";
export const MAX_QUEUE_EVENTS = 500;

export type RecordingState = "recording" | "paused" | "stopped";

export type PrivacyToggles = {
  browser: boolean;
  typingMetrics: boolean;
  selection: boolean;
  selectedText: boolean;
  media: boolean;
};

export type BridgeState = {
  endpoint: string;
  pairingToken: string | undefined;
  sessionId: string;
  recordingState: RecordingState;
  pausedUntilMs?: number;
  disabledSiteHashes: string[];
  privacyToggles: PrivacyToggles;
  updatedAt: string;
};

export type FlushResult = {
  posted: number;
  remaining: number;
  error?: Error;
};

export type SessionControlResult = {
  recordingState: RecordingState;
  sessionId?: string;
};

export type SessionStatusResult = {
  recordingState: RecordingState;
  sessionId?: string | null;
};

export type AutoPairingResult = {
  endpoint: string;
  pairingToken: string;
  sessionId: string;
  recordingState: RecordingState;
};

export type FetchLike = (url: string, init?: RequestInit) => Promise<Response>;

export type EventQueue = {
  enqueue(events: EventEnvelope[]): Promise<void>;
  peek(limit: number): Promise<EventEnvelope[]>;
  remove(count: number): Promise<void>;
  size(): Promise<number>;
  clear(): Promise<void>;
};

export type StorageAreaLike = {
  get(
    key: string | string[] | Record<string, unknown>,
    callback?: (items: Record<string, unknown>) => void,
  ): Promise<Record<string, unknown>> | void;
  set(items: Record<string, unknown>, callback?: () => void): Promise<void> | void;
};

export class PairingRequiredError extends Error {
  constructor() {
    super("extension is not paired with the local desktop bridge");
    this.name = "PairingRequiredError";
  }
}

export class PairingRejectedError extends Error {
  constructor(status: number) {
    super(`desktop bridge rejected the pairing token with status ${status}`);
    this.name = "PairingRejectedError";
  }
}

export class BridgePostError extends Error {
  constructor(status: number) {
    super(`desktop bridge post failed with status ${status}`);
    this.name = "BridgePostError";
  }
}

export class BridgeStatusError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "BridgeStatusError";
  }
}

export class AutoPairingError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AutoPairingError";
  }
}

export const defaultPrivacyToggles: PrivacyToggles = {
  browser: true,
  typingMetrics: true,
  selection: true,
  selectedText: false,
  media: true,
};

export const disabledPrivacyToggles: PrivacyToggles = {
  browser: false,
  typingMetrics: false,
  selection: false,
  selectedText: false,
  media: false,
};

const rawSelectedTextPayloadKeys = selectedTextPayloadFieldNames;

export function createPairingChallenge(): string {
  return crypto.randomUUID();
}

export function defaultBridgeState(now = new Date()): BridgeState {
  return {
    endpoint: DEFAULT_BRIDGE_ENDPOINT,
    pairingToken: undefined,
    sessionId: DEFAULT_SESSION_ID,
    recordingState: "stopped",
    disabledSiteHashes: [],
    privacyToggles: { ...disabledPrivacyToggles },
    updatedAt: now.toISOString(),
  };
}

export async function postEventBatch(
  events: EventEnvelope[],
  state: BridgeState,
  options: { fetchImpl?: FetchLike; timeoutMs?: number } = {},
): Promise<{ accepted: number }> {
  if (!state.pairingToken) {
    throw new PairingRequiredError();
  }

  for (const event of events) {
    validateEvent(event);
    if (event.session_id !== state.sessionId) {
      throw new Error("event session does not match bridge session");
    }
  }

  const fetchImpl = options.fetchImpl ?? fetch;
  const response = await fetchWithTimeout(fetchImpl, state.endpoint, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-inquiry-pairing-token": state.pairingToken,
    },
    body: JSON.stringify({
      session_id: state.sessionId,
      source: "chrome-extension",
      events,
    }),
  }, options.timeoutMs ?? 3_000);

  if (response.status === 401 || response.status === 403) {
    throw new PairingRejectedError(response.status);
  }

  if (!response.ok) {
    throw new BridgePostError(response.status);
  }

  const responseBody = (await response.json().catch(() => ({}))) as Record<string, unknown>;
  return { accepted: typeof responseBody.accepted === "number" ? responseBody.accepted : events.length };
}

export async function postSessionControl(
  state: BridgeState,
  input: { recordingState: RecordingState; title?: string; monotonicMs?: number },
  options: { fetchImpl?: FetchLike; timeoutMs?: number } = {},
): Promise<SessionControlResult> {
  if (!state.pairingToken) {
    throw new PairingRequiredError();
  }

  const body: Record<string, unknown> = {
    recording_state: input.recordingState,
  };
  if (input.title) {
    body.title = input.title;
  }
  if (typeof input.monotonicMs === "number") {
    body.monotonic_ms = input.monotonicMs;
  }

  const fetchImpl = options.fetchImpl ?? fetch;
  const response = await fetchWithTimeout(
    fetchImpl,
    sessionControlEndpoint(state.endpoint),
    {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-inquiry-pairing-token": state.pairingToken,
      },
      body: JSON.stringify(body),
    },
    options.timeoutMs ?? 3_000,
  );

  if (response.status === 401 || response.status === 403) {
    throw new PairingRejectedError(response.status);
  }

  if (!response.ok) {
    throw new BridgePostError(response.status);
  }

  const responseBody = (await response.json().catch(() => ({}))) as Record<string, unknown>;
  const recordingState = isRecordingState(responseBody.recording_state)
    ? responseBody.recording_state
    : input.recordingState;
  return {
    recordingState,
    ...(typeof responseBody.session_id === "string" ? { sessionId: responseBody.session_id } : {}),
  };
}

export async function fetchSessionStatus(
  state: BridgeState,
  options: { fetchImpl?: FetchLike; timeoutMs?: number } = {},
): Promise<SessionStatusResult> {
  if (!state.pairingToken) {
    throw new PairingRequiredError();
  }

  const fetchImpl = options.fetchImpl ?? fetch;
  const response = await fetchWithTimeout(
    fetchImpl,
    sessionControlEndpoint(state.endpoint),
    {
      method: "GET",
      headers: {
        "x-inquiry-pairing-token": state.pairingToken,
      },
    },
    options.timeoutMs ?? 3_000,
  );

  if (response.status === 401 || response.status === 403) {
    throw new PairingRejectedError(response.status);
  }

  if (!response.ok) {
    throw new BridgePostError(response.status);
  }

  let responseBody: Record<string, unknown>;
  try {
    responseBody = (await response.json()) as Record<string, unknown>;
  } catch {
    throw new BridgeStatusError("desktop bridge returned invalid session status JSON");
  }
  if (!isRecordingState(responseBody.recording_state)) {
    throw new BridgeStatusError("desktop bridge returned invalid session recording state");
  }
  return {
    recordingState: responseBody.recording_state,
    ...(typeof responseBody.session_id === "string" || responseBody.session_id === null
      ? { sessionId: responseBody.session_id }
      : {}),
  };
}

export async function requestBridgePairing(
  eventsEndpoint = DEFAULT_BRIDGE_ENDPOINT,
  options: { challenge: string; fetchImpl?: FetchLike; timeoutMs?: number },
): Promise<AutoPairingResult> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const response = await fetchWithTimeout(
    fetchImpl,
    pairingEndpoint(eventsEndpoint, options.challenge),
    {
      method: "GET",
      cache: "no-store",
    },
    options.timeoutMs ?? 3_000,
  );

  if (!response.ok) {
    throw new AutoPairingError(`desktop pairing failed with status ${response.status}`);
  }

  let body: Record<string, unknown>;
  try {
    body = (await response.json()) as Record<string, unknown>;
  } catch {
    throw new AutoPairingError("desktop pairing returned invalid JSON");
  }

  const endpoint = typeof body.endpoint === "string" && body.endpoint.length > 0 ? body.endpoint : eventsEndpoint;
  const pairingToken = typeof body.pairing_token === "string" ? body.pairing_token : undefined;
  if (!pairingToken) {
    throw new AutoPairingError("desktop pairing did not return a token");
  }

  return {
    endpoint,
    pairingToken,
    sessionId: typeof body.session_id === "string" && body.session_id.length > 0 ? body.session_id : DEFAULT_SESSION_ID,
    recordingState: isRecordingState(body.recording_state) ? body.recording_state : "stopped",
  };
}

export async function flushQueuedEvents(
  queue: EventQueue,
  state: BridgeState,
  options: { batchSize?: number; fetchImpl?: FetchLike } = {},
): Promise<FlushResult> {
  const pending = await queue.peek(options.batchSize ?? 50);
  if (pending.length === 0) {
    return { posted: 0, remaining: 0 };
  }

  try {
    const postOptions = options.fetchImpl ? { fetchImpl: options.fetchImpl } : {};
    await postEventBatch(pending, state, postOptions);
    await queue.remove(pending.length);
    return {
      posted: pending.length,
      remaining: await queue.size(),
    };
  } catch (error) {
    return {
      posted: 0,
      remaining: await queue.size(),
      error: normalizeError(error),
    };
  }
}

export function createMemoryEventQueue(initialEvents: EventEnvelope[] = []): EventQueue {
  const events = [...initialEvents];

  return {
    async enqueue(nextEvents) {
      events.push(...nextEvents);
      if (events.length > MAX_QUEUE_EVENTS) {
        events.splice(0, events.length - MAX_QUEUE_EVENTS);
      }
    },
    async peek(limit) {
      return events.slice(0, limit);
    },
    async remove(count) {
      events.splice(0, count);
    },
    async size() {
      return events.length;
    },
    async clear() {
      events.length = 0;
    },
  };
}

export function createStorageEventQueue(storage: StorageAreaLike, key = BRIDGE_QUEUE_KEY): EventQueue {
  let mutation = Promise.resolve();

  async function exclusive<T>(task: () => Promise<T>): Promise<T> {
    const previous = mutation;
    let release!: () => void;
    mutation = new Promise<void>((resolve) => {
      release = resolve;
    });
    await previous;
    try {
      return await task();
    } finally {
      release();
    }
  }

  async function readEvents(): Promise<EventEnvelope[]> {
    const value = (await readStorageValue(storage, key)) as unknown;
    if (!Array.isArray(value)) {
      return [];
    }

    return value.filter(isEventEnvelope);
  }

  async function writeEvents(events: EventEnvelope[]): Promise<void> {
    await writeStorageValue(storage, key, events.slice(-MAX_QUEUE_EVENTS));
  }

  return {
    async enqueue(nextEvents) {
      await exclusive(async () => {
        const events = await readEvents();
        events.push(...nextEvents);
        await writeEvents(events);
      });
    },
    async peek(limit) {
      return (await readEvents()).slice(0, limit);
    },
    async remove(count) {
      await exclusive(async () => {
        const events = await readEvents();
        events.splice(0, count);
        await writeEvents(events);
      });
    },
    async size() {
      return (await readEvents()).length;
    },
    async clear() {
      await exclusive(async () => writeEvents([]));
    },
  };
}

export async function getBridgeState(storage: StorageAreaLike, key = BRIDGE_STATE_KEY): Promise<BridgeState> {
  return normalizeBridgeState((await readStorageValue(storage, key)) as Partial<BridgeState> | undefined);
}

export async function saveBridgeState(
  storage: StorageAreaLike,
  state: BridgeState,
  key = BRIDGE_STATE_KEY,
): Promise<BridgeState> {
  const normalized = normalizeBridgeState(state);
  await writeStorageValue(storage, key, normalized);
  return normalized;
}

export function normalizeBridgeState(input?: Partial<BridgeState>): BridgeState {
  const fallback = defaultBridgeState();
  const toggles: Partial<PrivacyToggles> = input?.privacyToggles ?? {};
  const state: BridgeState = {
    endpoint: typeof input?.endpoint === "string" && input.endpoint.length > 0 ? input.endpoint : fallback.endpoint,
    pairingToken:
      typeof input?.pairingToken === "string" && input.pairingToken.length > 0 ? input.pairingToken : undefined,
    sessionId:
      typeof input?.sessionId === "string" && input.sessionId.length > 0 ? input.sessionId : fallback.sessionId,
    recordingState: isRecordingState(input?.recordingState) ? input.recordingState : fallback.recordingState,
    disabledSiteHashes: Array.isArray(input?.disabledSiteHashes)
      ? input.disabledSiteHashes.filter((hash): hash is string => typeof hash === "string")
      : [],
    privacyToggles: {
      browser: typeof toggles.browser === "boolean" ? toggles.browser : fallback.privacyToggles.browser,
      typingMetrics:
        typeof toggles.typingMetrics === "boolean" ? toggles.typingMetrics : fallback.privacyToggles.typingMetrics,
      selection: typeof toggles.selection === "boolean" ? toggles.selection : fallback.privacyToggles.selection,
      selectedText:
        typeof toggles.selectedText === "boolean" ? toggles.selectedText : fallback.privacyToggles.selectedText,
      media: typeof toggles.media === "boolean" ? toggles.media : fallback.privacyToggles.media,
    },
    updatedAt: typeof input?.updatedAt === "string" ? input.updatedAt : fallback.updatedAt,
  };

  if (typeof input?.pausedUntilMs === "number" && Number.isFinite(input.pausedUntilMs)) {
    state.pausedUntilMs = input.pausedUntilMs;
  }

  return state;
}

export function isBridgeEventAllowed(event: EventEnvelope, state: BridgeState, nowMs = Date.now()): boolean {
  if (!state.pairingToken) {
    return false;
  }

  const effectiveRecording =
    state.recordingState === "recording" ||
    (state.recordingState === "paused" && typeof state.pausedUntilMs === "number" && state.pausedUntilMs <= nowMs);
  if (!effectiveRecording) {
    return false;
  }

  if (!state.privacyToggles.browser) {
    return false;
  }

  const hostnameHash = event.payload.hostname_hash;
  const urlHash = event.payload.url_hash;
  if (
    (typeof hostnameHash === "string" && state.disabledSiteHashes.includes(hostnameHash)) ||
    (typeof urlHash === "string" && state.disabledSiteHashes.includes(urlHash))
  ) {
    return false;
  }

  if (event.event_type === "browser.typing_metrics") {
    return state.privacyToggles.typingMetrics;
  }

  if (
    event.event_type === "browser.selection" ||
    event.event_type === "browser.copy" ||
    event.event_type === "browser.highlight"
  ) {
    if (event.privacy_class === "document-opt-in" && hasSelectedText(event)) {
      return state.privacyToggles.selection && state.privacyToggles.selectedText;
    }

    return state.privacyToggles.selection;
  }

  if (event.event_type === "browser.media") {
    return state.privacyToggles.media;
  }

  return true;
}

function hasSelectedText(event: EventEnvelope): boolean {
  return rawSelectedTextPayloadKeys.some((key) => typeof event.payload[key] === "string" && event.payload[key].length > 0);
}

function sessionControlEndpoint(eventsEndpoint: string): string {
  return extensionEndpoint(eventsEndpoint, "session");
}

function pairingEndpoint(eventsEndpoint: string, challenge: string): string {
  return extensionEndpoint(eventsEndpoint, "pairing", challenge);
}

function extensionEndpoint(eventsEndpoint: string, target: "pairing" | "session", challenge?: string): string {
  const url = new URL(eventsEndpoint);
  if (url.pathname.endsWith("/extension/events")) {
    url.pathname = url.pathname.replace(/\/extension\/events$/, `/extension/${target}`);
  } else if (url.pathname.endsWith("/events")) {
    url.pathname = url.pathname.replace(/\/events$/, `/extension/${target}`);
  } else {
    url.pathname = `/v1/extension/${target}`;
  }
  if (challenge) {
    url.searchParams.set("challenge", challenge);
  }
  return url.toString();
}

async function fetchWithTimeout(fetchImpl: FetchLike, url: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetchImpl(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

async function readStorageValue(storage: StorageAreaLike, key: string): Promise<unknown> {
  const items = await new Promise<Record<string, unknown>>((resolve, reject) => {
    try {
      const maybePromise = storage.get(key, (result) => resolve(result ?? {}));
      if (isPromiseLike(maybePromise)) {
        maybePromise.then((result) => resolve(result ?? {}), reject);
      }
    } catch (error) {
      reject(error);
    }
  });

  return items[key];
}

async function writeStorageValue(storage: StorageAreaLike, key: string, value: unknown): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    try {
      const maybePromise = storage.set({ [key]: value }, () => resolve());
      if (isPromiseLike(maybePromise)) {
        maybePromise.then(() => resolve(), reject);
      }
    } catch (error) {
      reject(error);
    }
  });
}

function isEventEnvelope(value: unknown): value is EventEnvelope {
  try {
    validateEvent(value);
    return true;
  } catch {
    return false;
  }
}

export function isRecordingState(value: unknown): value is RecordingState {
  return value === "recording" || value === "paused" || value === "stopped";
}

function isPromiseLike<T>(value: unknown): value is Promise<T> {
  return typeof value === "object" && value !== null && "then" in value;
}

function normalizeError(error: unknown): Error {
  return error instanceof Error ? error : new Error(String(error));
}
