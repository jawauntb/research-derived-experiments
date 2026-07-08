import { describe, expect, test } from "bun:test";
import { createEvent, type EventEnvelope } from "@inquiry/schema";
import { ensureContentScriptRegistration, handleRuntimeMessage, retryBridgeQueue } from "../src/background/service-worker";
import {
  BRIDGE_STATE_KEY,
  DEFAULT_BRIDGE_ENDPOINT,
  DEFAULT_SESSION_ID,
  PairingRequiredError,
  PairingRejectedError,
  createMemoryEventQueue,
  defaultBridgeState,
  fetchSessionStatus,
  flushQueuedEvents,
  getBridgeState,
  isBridgeEventAllowed,
  postEventBatch,
  postSessionControl,
  requestBridgePairing,
  type BridgeState,
  type StorageAreaLike,
} from "../src/lib/localBridge";
import { CONTENT_SETTINGS_UPDATED_MESSAGE } from "../src/lib/messages";

describe("local bridge pairing and queue", () => {
  test("keeps events queued while desktop bridge is offline and retries later", async () => {
    const queue = createMemoryEventQueue();
    const event = browserScrollEvent("event-offline");
    const state = pairedState();
    await queue.enqueue([event]);

    const offline = await flushQueuedEvents(queue, state, {
      fetchImpl: async () => {
        throw new Error("desktop offline");
      },
    });

    expect(offline.posted).toBe(0);
    expect(offline.remaining).toBe(1);
    expect(await queue.size()).toBe(1);

    let postedBody = "";
    const retried = await flushQueuedEvents(queue, state, {
      fetchImpl: async (_url, init) => {
        postedBody = String(init?.body ?? "");
        return new Response(JSON.stringify({ accepted: 1 }), { status: 202 });
      },
    });

    expect(retried.posted).toBe(1);
    expect(retried.remaining).toBe(0);
    expect(await queue.size()).toBe(0);
    expect(postedBody).toContain("event-offline");
  });

  test("rejects bridge posts when the pairing token is absent", async () => {
    await expect(
      postEventBatch([browserScrollEvent("event-missing-token")], { ...pairedState(), pairingToken: undefined }),
    ).rejects.toBeInstanceOf(PairingRequiredError);
  });

  test("defaults to the desktop bridge port and blocks capture until paired and recording", () => {
    const state = defaultBridgeState(new Date("2026-07-07T00:00:00.000Z"));
    const event = browserScrollEvent("event-default-state");

    expect(state.endpoint).toBe(DEFAULT_BRIDGE_ENDPOINT);
    expect(state.recordingState).toBe("stopped");
    expect(state.privacyToggles.browser).toBe(false);
    expect(isBridgeEventAllowed(event, state)).toBe(false);
    expect(isBridgeEventAllowed(event, { ...pairedState(), recordingState: "paused", pausedUntilMs: 1_000 }, 1_001)).toBe(true);
  });

  test("sends the pairing token header and rejects stale tokens", async () => {
    let tokenHeader = "";
    const event = browserScrollEvent("event-paired");

    await postEventBatch([event], pairedState(), {
      fetchImpl: async (_url, init) => {
        tokenHeader = new Headers(init?.headers).get("x-inquiry-pairing-token") ?? "";
        return new Response(JSON.stringify({ accepted: 1 }), { status: 202 });
      },
    });

    expect(tokenHeader).toBe("paired-token");

    await expect(
      postEventBatch([event], pairedState(), {
        fetchImpl: async () => new Response("stale token", { status: 401 }),
      }),
    ).rejects.toBeInstanceOf(PairingRejectedError);
  });

  test("rejects bridge posts with stale event session ids before sending", async () => {
    let calls = 0;
    await expect(
      postEventBatch([{ ...browserScrollEvent("event-stale-session"), session_id: "stale-session" }], pairedState(), {
        fetchImpl: async () => {
          calls += 1;
          return new Response(JSON.stringify({ accepted: 1 }), { status: 202 });
        },
      }),
    ).rejects.toThrow("event session does not match bridge session");
    expect(calls).toBe(0);
  });

  test("posts session controls to the desktop session endpoint", async () => {
    let url = "";
    let tokenHeader = "";
    let postedBody: Record<string, unknown> = {};

    const result = await postSessionControl(
      pairedState(),
      { recordingState: "recording", title: "Research session", monotonicMs: 2_500 },
      {
        fetchImpl: async (nextUrl, init) => {
          url = nextUrl;
          tokenHeader = new Headers(init?.headers).get("x-inquiry-pairing-token") ?? "";
          postedBody = JSON.parse(String(init?.body ?? "{}")) as Record<string, unknown>;
          return new Response(JSON.stringify({ ok: true, recording_state: "recording", session_id: "desktop-session-1" }), {
            status: 200,
          });
        },
      },
    );

    expect(url).toBe("http://127.0.0.1:39170/v1/extension/session");
    expect(tokenHeader).toBe("paired-token");
    expect(postedBody).toMatchObject({
      recording_state: "recording",
      title: "Research session",
      monotonic_ms: 2_500,
    });
    expect(result).toEqual({ recordingState: "recording", sessionId: "desktop-session-1" });

    const paused = await postSessionControl(
      pairedState(),
      { recordingState: "paused", monotonicMs: 3_000 },
      {
        fetchImpl: async (nextUrl, init) => {
          url = nextUrl;
          tokenHeader = new Headers(init?.headers).get("x-inquiry-pairing-token") ?? "";
          postedBody = JSON.parse(String(init?.body ?? "{}")) as Record<string, unknown>;
          return new Response(JSON.stringify({ ok: true, recording_state: "paused", session_id: "desktop-session-1" }), {
            status: 200,
          });
        },
      },
    );

    expect(url).toBe("http://127.0.0.1:39170/v1/extension/session");
    expect(tokenHeader).toBe("paired-token");
    expect(postedBody).toMatchObject({
      recording_state: "paused",
      monotonic_ms: 3_000,
    });
    expect(paused).toEqual({ recordingState: "paused", sessionId: "desktop-session-1" });
  });

  test("fetches authoritative desktop session status", async () => {
    let url = "";
    let tokenHeader = "";

    const result = await fetchSessionStatus(pairedState(), {
      fetchImpl: async (nextUrl, init) => {
        url = nextUrl;
        tokenHeader = new Headers(init?.headers).get("x-inquiry-pairing-token") ?? "";
        return new Response(JSON.stringify({ ok: true, recording_state: "stopped", session_id: null, session: null }), {
          status: 200,
        });
      },
    });

    expect(url).toBe("http://127.0.0.1:39170/v1/extension/session");
    expect(tokenHeader).toBe("paired-token");
    expect(result).toEqual({ recordingState: "stopped", sessionId: null });
  });

  test("requests one-click pairing from the desktop pairing endpoint", async () => {
    let url = "";
    const result = await requestBridgePairing(DEFAULT_BRIDGE_ENDPOINT, {
      challenge: "pairing-challenge-fixture-123",
      fetchImpl: async (nextUrl, init) => {
        url = nextUrl;
        expect(init?.method).toBe("GET");
        return new Response(
          JSON.stringify({
            ok: true,
            endpoint: DEFAULT_BRIDGE_ENDPOINT,
            pairing_token: "auto-token",
            session_id: "desktop-session-1",
            recording_state: "paused",
          }),
          { status: 200 },
        );
      },
    });

    expect(url).toBe("http://127.0.0.1:39170/v1/extension/pairing?challenge=pairing-challenge-fixture-123");
    expect(result).toEqual({
      endpoint: DEFAULT_BRIDGE_ENDPOINT,
      pairingToken: "auto-token",
      sessionId: "desktop-session-1",
      recordingState: "paused",
    });
  });

  test("stores one-click desktop pairing responses", async () => {
    const storage = createMemoryStorage({ [BRIDGE_STATE_KEY]: defaultBridgeState() });
    const queue = createMemoryEventQueue();

    const response = await handleRuntimeMessage(
      { type: "inquiry:auto-pair", challenge: "pairing-challenge-fixture-123" },
      {},
      {
        storage,
        queue,
        now: () => 2_000,
        fetchImpl: async () =>
          new Response(
            JSON.stringify({
              ok: true,
              endpoint: DEFAULT_BRIDGE_ENDPOINT,
              pairing_token: "auto-paired-token",
              session_id: null,
              recording_state: "stopped",
            }),
            { status: 200 },
          ),
      },
    );

    expect(response).toMatchObject({
      ok: true,
      endpoint: DEFAULT_BRIDGE_ENDPOINT,
      pairingToken: "auto-paired-token",
      sessionId: DEFAULT_SESSION_ID,
      recordingState: "stopped",
    });
    expect(await getBridgeState(storage)).toMatchObject({ pairingToken: "auto-paired-token" });
  });

  test("rejects malformed one-click desktop pairing responses without changing stored state", async () => {
    await expect(
      requestBridgePairing(DEFAULT_BRIDGE_ENDPOINT, {
        challenge: "pairing-challenge-fixture-123",
        fetchImpl: async () => new Response("unauthorized", { status: 401 }),
      }),
    ).rejects.toThrow("desktop pairing failed with status 401");

    await expect(
      requestBridgePairing(DEFAULT_BRIDGE_ENDPOINT, {
        challenge: "pairing-challenge-fixture-123",
        fetchImpl: async () => new Response("not json", { status: 200 }),
      }),
    ).rejects.toThrow("desktop pairing returned invalid JSON");

    await expect(
      requestBridgePairing(DEFAULT_BRIDGE_ENDPOINT, {
        challenge: "pairing-challenge-fixture-123",
        fetchImpl: async () => new Response(JSON.stringify({ ok: true }), { status: 200 }),
      }),
    ).rejects.toThrow("desktop pairing did not return a token");

    const storage = createMemoryStorage({ [BRIDGE_STATE_KEY]: defaultBridgeState() });
    const queue = createMemoryEventQueue();
    const missingChallenge = await handleRuntimeMessage(
      { type: "inquiry:auto-pair" },
      {},
      {
        storage,
        queue,
        now: () => 2_000,
        fetchImpl: async () => new Response(JSON.stringify({ pairing_token: "should-not-store" }), { status: 200 }),
      },
    );
    expect(missingChallenge).toMatchObject({ ok: false, error: "pairing challenge is required" });
    expect((await getBridgeState(storage)).pairingToken).toBeUndefined();

    const failed = await handleRuntimeMessage(
      { type: "inquiry:auto-pair", challenge: "pairing-challenge-fixture-123" },
      {},
      {
        storage,
        queue,
        now: () => 2_100,
        fetchImpl: async () => new Response("unauthorized", { status: 401 }),
      },
    );
    expect(failed).toMatchObject({ ok: false, error: "desktop pairing failed with status 401" });
    expect((await getBridgeState(storage)).pairingToken).toBeUndefined();
  });

  test("blocks capture while paused, stopped, or disabled for the site", () => {
    const event = browserScrollEvent("event-gated");
    const state = pairedState();

    expect(isBridgeEventAllowed(event, state)).toBe(true);
    expect(isBridgeEventAllowed(event, { ...state, recordingState: "paused" })).toBe(false);
    expect(isBridgeEventAllowed(event, { ...state, recordingState: "stopped" })).toBe(false);
    expect(isBridgeEventAllowed(event, { ...state, disabledSiteHashes: ["host-abc"] })).toBe(false);
  });

  test("requires selected text opt-in for document-opt-in copy evidence", () => {
    const event = browserCopyTextEvent("event-selected-text");
    const alternateTextFieldEvent = browserCopyTextEvent("event-copied-text", { copied_text: "copied claim" });
    const camelTextFieldEvent = browserCopyTextEvent("event-selection-text", { selectionText: "selected claim" });
    const state = pairedState();

    expect(isBridgeEventAllowed(event, state)).toBe(false);
    expect(isBridgeEventAllowed(alternateTextFieldEvent, state)).toBe(false);
    expect(isBridgeEventAllowed(camelTextFieldEvent, state)).toBe(false);
    expect(
      isBridgeEventAllowed(event, {
        ...state,
        privacyToggles: {
          ...state.privacyToggles,
          selectedText: true,
        },
      }),
    ).toBe(true);
    expect(
      isBridgeEventAllowed(alternateTextFieldEvent, {
        ...state,
        privacyToggles: {
          ...state.privacyToggles,
          selectedText: true,
        },
      }),
    ).toBe(true);
    expect(
      isBridgeEventAllowed(camelTextFieldEvent, {
        ...state,
        privacyToggles: {
          ...state.privacyToggles,
          selectedText: true,
        },
      }),
    ).toBe(true);
  });

  test("broadcasts popup recording changes to loaded content scripts", async () => {
    const storage = createMemoryStorage({ [BRIDGE_STATE_KEY]: { ...pairedState(), recordingState: "stopped" } });
    const queue = createMemoryEventQueue();
    const sentMessages: Array<{ tabId: number; message: unknown }> = [];

    const response = await handleRuntimeMessage(
      { type: "inquiry:set-recording-state", recordingState: "recording" },
      {},
      {
        storage,
        queue,
        tabs: {
          query: (_query, callback) => callback([{ id: 1 }, {}, { id: 2 }]),
          sendMessage: (tabId, message) => {
            sentMessages.push({ tabId, message });
          },
        },
        now: () => 2_000,
        fetchImpl: async () =>
          new Response(JSON.stringify({ ok: true, recording_state: "recording", session_id: "desktop-session-1" }), {
            status: 200,
          }),
      },
    );

    expect(response).toMatchObject({ ok: true, recordingState: "recording", sessionId: "desktop-session-1" });
    expect(sentMessages).toEqual([
      {
        tabId: 1,
        message: {
          type: CONTENT_SETTINGS_UPDATED_MESSAGE,
          settings: expect.objectContaining({ recordingState: "recording", sessionId: "desktop-session-1" }),
        },
      },
      {
        tabId: 2,
        message: {
          type: CONTENT_SETTINGS_UPDATED_MESSAGE,
          settings: expect.objectContaining({ recordingState: "recording", sessionId: "desktop-session-1" }),
        },
      },
    ]);
  });

  test("keeps extension stopped when desktop record coordination fails", async () => {
    const storage = createMemoryStorage({ [BRIDGE_STATE_KEY]: { ...pairedState(), recordingState: "stopped" } });
    const queue = createMemoryEventQueue();

    const response = await handleRuntimeMessage(
      { type: "inquiry:set-recording-state", recordingState: "recording" },
      {},
      {
        storage,
        queue,
        now: () => 2_000,
        fetchImpl: async () => {
          throw new Error("desktop offline");
        },
      },
    );

    expect(response).toMatchObject({ ok: false, recordingState: "stopped", error: "desktop offline" });
    expect((await getBridgeState(storage)).recordingState).toBe("stopped");
  });

  test("pauses through the desktop session endpoint before changing local capture state", async () => {
    const storage = createMemoryStorage({ [BRIDGE_STATE_KEY]: pairedState() });
    const queue = createMemoryEventQueue();
    let postedBody: Record<string, unknown> = {};

    const response = await handleRuntimeMessage(
      { type: "inquiry:set-recording-state", recordingState: "paused" },
      {},
      {
        storage,
        queue,
        now: () => 2_500,
        fetchImpl: async (_url, init) => {
          postedBody = JSON.parse(String(init?.body ?? "{}")) as Record<string, unknown>;
          return new Response(JSON.stringify({ ok: true, recording_state: "paused", session_id: "session-bridge" }), {
            status: 200,
          });
        },
      },
    );

    expect(response).toMatchObject({ ok: true, recordingState: "paused", sessionId: "session-bridge" });
    expect(postedBody).toMatchObject({ recording_state: "paused", monotonic_ms: 2_500 });
    expect(await getBridgeState(storage)).toMatchObject({ recordingState: "paused", sessionId: "session-bridge" });
  });

  test("reconciles stale popup recording state against stopped desktop status", async () => {
    const storage = createMemoryStorage({ [BRIDGE_STATE_KEY]: { ...pairedState(), recordingState: "recording" } });
    const queue = createMemoryEventQueue();
    const sentMessages: unknown[] = [];

    const response = await handleRuntimeMessage(
      { type: "inquiry:get-popup-state" },
      {},
      {
        storage,
        queue,
        tabs: {
          query: (_query, callback) => callback([{ id: 1 }]),
          sendMessage: (_tabId, message) => {
            sentMessages.push(message);
          },
        },
        now: () => 2_000,
        fetchImpl: async () =>
          new Response(JSON.stringify({ ok: true, recording_state: "stopped", session_id: null, session: null }), {
            status: 200,
          }),
      },
    );

    expect(response).toMatchObject({
      ok: true,
      recordingState: "stopped",
      sessionId: DEFAULT_SESSION_ID,
      desktopRecordingState: "stopped",
    });
    expect(await getBridgeState(storage)).toMatchObject({ recordingState: "stopped", sessionId: DEFAULT_SESSION_ID });
    expect(sentMessages).toEqual([
      {
        type: CONTENT_SETTINGS_UPDATED_MESSAGE,
        settings: expect.objectContaining({ recordingState: "stopped", sessionId: DEFAULT_SESSION_ID }),
      },
    ]);
  });

  test("returns a desktop status warning without changing stored popup state", async () => {
    const storage = createMemoryStorage({ [BRIDGE_STATE_KEY]: { ...pairedState(), recordingState: "recording" } });
    const queue = createMemoryEventQueue();

    const response = await handleRuntimeMessage(
      { type: "inquiry:get-popup-state" },
      {},
      {
        storage,
        queue,
        now: () => 2_000,
        fetchImpl: async () => new Response("desktop failed", { status: 500 }),
      },
    );

    expect(response).toMatchObject({
      ok: true,
      recordingState: "recording",
      desktopStatusWarning: "desktop bridge post failed with status 500",
    });
    expect(await getBridgeState(storage)).toMatchObject({ recordingState: "recording", sessionId: "session-bridge" });

    const malformed = await handleRuntimeMessage(
      { type: "inquiry:get-popup-state" },
      {},
      {
        storage,
        queue,
        now: () => 2_100,
        fetchImpl: async () => new Response("not json", { status: 200 }),
      },
    );
    expect(malformed).toMatchObject({
      ok: true,
      recordingState: "recording",
      desktopStatusWarning: "desktop bridge returned invalid session status JSON",
    });
    expect(await getBridgeState(storage)).toMatchObject({ recordingState: "recording", sessionId: "session-bridge" });

    const missingState = await handleRuntimeMessage(
      { type: "inquiry:get-popup-state" },
      {},
      {
        storage,
        queue,
        now: () => 2_200,
        fetchImpl: async () => new Response(JSON.stringify({ ok: true, session_id: null }), { status: 200 }),
      },
    );
    expect(missingState).toMatchObject({
      ok: true,
      recordingState: "recording",
      desktopStatusWarning: "desktop bridge returned invalid session recording state",
    });
    expect(await getBridgeState(storage)).toMatchObject({ recordingState: "recording", sessionId: "session-bridge" });
  });

  test("retry alarm reconciliation clears stale queued events instead of rebinding them", async () => {
    const storage = createMemoryStorage({ [BRIDGE_STATE_KEY]: { ...pairedState(), recordingState: "recording" } });
    const queuedEvent = browserScrollEvent("event-retry-reconcile");
    const queue = createMemoryEventQueue([queuedEvent]);
    const calls: string[] = [];

    await retryBridgeQueue({
      storage,
      queue,
      tabs: {
        query: (_query, callback) => callback([{ id: 1 }]),
        sendMessage: (_tabId, message) => {
          calls.push(`broadcast:${JSON.stringify(message)}`);
        },
      },
      now: () => 2_000,
      fetchImpl: async (url) => {
        if (url.endsWith("/v1/extension/session")) {
          calls.push("status");
          return new Response(JSON.stringify({ ok: true, recording_state: "stopped", session_id: null, session: null }), {
            status: 200,
          });
        }
        calls.push("post-events");
        return new Response(JSON.stringify({ accepted: 1 }), { status: 202 });
      },
    });

    expect(await getBridgeState(storage)).toMatchObject({ recordingState: "stopped", sessionId: DEFAULT_SESSION_ID });
    expect(await queue.size()).toBe(0);
    expect(calls[0]).toBe("status");
    expect(calls[1]).toContain(CONTENT_SETTINGS_UPDATED_MESSAGE);
    expect(calls[1]).toContain(DEFAULT_SESSION_ID);
    expect(calls).not.toContain("post-events");
  });

  test("registers the content script as a service-worker fallback", async () => {
    const registrations: unknown[] = [];
    const unregistered: string[][] = [];

    const registered = await ensureContentScriptRegistration({
      unregisterContentScripts: (filter, callback) => {
        unregistered.push(filter.ids);
        callback?.();
      },
      registerContentScripts: (scripts, callback) => {
        registrations.push(...scripts);
        callback?.();
      },
    });

    expect(registered).toBe(true);
    expect(unregistered).toEqual([["inquiry-content-listener"]]);
    expect(registrations).toEqual([
      {
        id: "inquiry-content-listener",
        matches: ["http://*/*", "https://*/*"],
        js: ["dist/content/index.js"],
        runAt: "document_idle",
        persistAcrossSessions: true,
        world: "ISOLATED",
      },
    ]);
  });
});

function pairedState(): BridgeState {
  return {
    endpoint: "http://127.0.0.1:39170/v1/extension/events",
    pairingToken: "paired-token",
    sessionId: "session-bridge",
    recordingState: "recording",
    disabledSiteHashes: [],
    privacyToggles: {
      browser: true,
      typingMetrics: true,
      selection: true,
      selectedText: false,
      media: true,
    },
    updatedAt: "2026-07-07T00:00:00.000Z",
  };
}

function browserCopyTextEvent(eventId: string, textPayload: Record<string, string> = { selected_text: "copied claim" }): EventEnvelope {
  return createEvent({
    event_id: eventId,
    captured_at: "2026-07-07T00:00:00.000Z",
    timezone: "UTC",
    session_id: "session-bridge",
    source: "browser",
    source_version: "extension@0.1.0",
    monotonic_ms: 2,
    event_type: "browser.copy",
    payload: {
      url_hash: "url-abc",
      hostname_hash: "host-abc",
      selection_length: 12,
      range_count: 1,
      ...textPayload,
    },
    privacy_class: "document-opt-in",
    retention_policy: "session-delete",
  });
}

function createMemoryStorage(initial: Record<string, unknown> = {}): StorageAreaLike {
  const state = { ...initial };
  return {
    get(key, callback) {
      const keys = Array.isArray(key) ? key : [key];
      const result: Record<string, unknown> = {};
      for (const item of keys) {
        if (typeof item === "string" && item in state) {
          result[item] = state[item];
        }
      }
      callback?.(result);
      return Promise.resolve(result);
    },
    set(items, callback) {
      Object.assign(state, items);
      callback?.();
      return Promise.resolve();
    },
  };
}

function browserScrollEvent(eventId: string): EventEnvelope {
  return createEvent({
    event_id: eventId,
    captured_at: "2026-07-07T00:00:00.000Z",
    timezone: "UTC",
    session_id: "session-bridge",
    source: "browser",
    source_version: "extension@0.1.0",
    monotonic_ms: 1,
    event_type: "browser.scroll",
    payload: {
      url_hash: "url-abc",
      hostname_hash: "host-abc",
      scroll_y: 120,
      viewport_h: 900,
    },
    privacy_class: "local-derived",
    retention_policy: "local-default",
  });
}
