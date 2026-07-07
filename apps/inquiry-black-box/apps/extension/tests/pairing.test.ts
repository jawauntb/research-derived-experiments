import { describe, expect, test } from "bun:test";
import { createEvent, type EventEnvelope } from "@inquiry/schema";
import {
  DEFAULT_BRIDGE_ENDPOINT,
  PairingRequiredError,
  PairingRejectedError,
  createMemoryEventQueue,
  defaultBridgeState,
  flushQueuedEvents,
  isBridgeEventAllowed,
  postEventBatch,
  type BridgeState,
} from "../src/lib/localBridge";

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
