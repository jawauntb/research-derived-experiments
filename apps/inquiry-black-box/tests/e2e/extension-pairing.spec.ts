import { describe, expect, test } from "bun:test";
import { createDesktopRuntime } from "../../apps/desktop/src/main/main";
import { createIngestRequestHandler } from "../../apps/desktop/src/main/ingest/server";
import { createInquiryDatabase } from "../../apps/desktop/src/main/db";
import { createPairingToken } from "../../apps/desktop/src/main/security/pairing";
import { createContentTelemetry, type ContentEventMessage } from "../../apps/extension/src/content";
import { postEventBatch, type BridgeState, type FetchLike } from "../../apps/extension/src/lib/localBridge";

const origin = "chrome-extension://extension-pairing-smoke";
const pairingSecret = "extension-pairing-smoke-secret";
const issuedAtMs = 10_000;

describe("extension pairing smoke", () => {
  test("posts browser telemetry into desktop SQLite with a valid pairing token", async () => {
    const database = createInquiryDatabase();
    const runtime = createDesktopRuntime({
      allowedOrigins: [origin],
      database,
      pairingSecret,
      startServer: false,
    });
    const session = runtime.bridge.startSession({ title: "Extension pairing smoke" });
    const handler = createIngestRequestHandler({
      allowedOrigins: [origin],
      database,
      pairingSecret,
      sessions: runtime.sessions,
      nowMs: () => issuedAtMs,
    });
    const messages: ContentEventMessage[] = [];
    const telemetry = createContentTelemetry({
      now: () => 1_000,
      sessionId: "extension-session-before-rebind",
      settings: recordingSettings(),
      location: {
        href: "http://127.0.0.1:39210/demo-article.html",
        hostname: "127.0.0.1",
      },
      sendMessage: (message) => {
        messages.push(message);
      },
    });

    telemetry.captureScroll({ scrollY: 320, viewportHeight: 900, documentHeight: 2_400 });
    telemetry.captureSelection("highlight", { selectionLength: 28, rangeCount: 1 });
    telemetry.captureMedia("seeked", { tagName: "VIDEO", currentTime: 42, duration: 120, paused: false });

    const events = messages.flatMap((message) => message.events);
    const result = await postEventBatch(events, pairedState(session.session_id), {
      fetchImpl: handlerFetch(handler),
    });
    const stored = database.listEvents(session.session_id);

    expect(result.accepted).toBe(events.length);
    expect(stored.map((event) => event.event_type)).toEqual([
      "session.started",
      "browser.scroll",
      "browser.highlight",
      "browser.media",
    ]);
    expect(stored.filter((event) => event.source === "browser").every((event) => event.session_id === session.session_id)).toBe(true);
    expect(JSON.stringify(stored)).not.toContain("demo-article.html");

    runtime.stop();
  });
});

function pairedState(sessionId: string): BridgeState {
  return {
    endpoint: "http://127.0.0.1:39170/v1/extension/events",
    pairingToken: createPairingToken({ secret: pairingSecret, issuedAtMs, nonce: "smoke-nonce" }),
    sessionId,
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

function handlerFetch(handler: (request: Request) => Promise<Response>): FetchLike {
  return async (url, init) => {
    const headers = new Headers(init?.headers);
    headers.set("origin", origin);
    return await handler(
      new Request(url, {
        method: init?.method,
        headers,
        body: init?.body,
        signal: init?.signal,
      }),
    );
  };
}

function recordingSettings() {
  return {
    recordingState: "recording" as const,
    siteDisabled: false,
    privacyToggles: {
      browser: true,
      typingMetrics: true,
      selection: true,
      selectedText: false,
      media: true,
    },
  };
}
