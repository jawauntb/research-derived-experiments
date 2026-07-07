import { describe, expect, test } from "bun:test";
import { createEvent, type EventEnvelope } from "@inquiry/schema";
import { ensureContentScriptRegistration, handleRuntimeMessage } from "../src/background/service-worker";
import {
  BRIDGE_STATE_KEY,
  DEFAULT_BRIDGE_ENDPOINT,
  PairingRequiredError,
  PairingRejectedError,
  createMemoryEventQueue,
  defaultBridgeState,
  flushQueuedEvents,
  isBridgeEventAllowed,
  postEventBatch,
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

  test("blocks capture while paused, stopped, or disabled for the site", () => {
    const event = browserScrollEvent("event-gated");
    const state = pairedState();

    expect(isBridgeEventAllowed(event, state)).toBe(true);
    expect(isBridgeEventAllowed(event, { ...state, recordingState: "paused" })).toBe(false);
    expect(isBridgeEventAllowed(event, { ...state, recordingState: "stopped" })).toBe(false);
    expect(isBridgeEventAllowed(event, { ...state, disabledSiteHashes: ["host-abc"] })).toBe(false);
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
      },
    );

    expect(response).toMatchObject({ ok: true, recordingState: "recording" });
    expect(sentMessages).toEqual([
      {
        tabId: 1,
        message: {
          type: CONTENT_SETTINGS_UPDATED_MESSAGE,
          settings: expect.objectContaining({ recordingState: "recording" }),
        },
      },
      {
        tabId: 2,
        message: {
          type: CONTENT_SETTINGS_UPDATED_MESSAGE,
          settings: expect.objectContaining({ recordingState: "recording" }),
        },
      },
    ]);
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
      media: true,
    },
    updatedAt: "2026-07-07T00:00:00.000Z",
  };
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
