import { describe, expect, test } from "bun:test";
import { createDesktopRuntime } from "../../apps/desktop/src/main/main";
import { createIngestRequestHandler } from "../../apps/desktop/src/main/ingest/server";
import { createInquiryDatabase } from "../../apps/desktop/src/main/db";
import { createPairingToken } from "../../apps/desktop/src/main/security/pairing";
import { createContentTelemetry, type ContentEventMessage } from "../../apps/extension/src/content";
import { postEventBatch, postSessionControl, type BridgeState, type FetchLike } from "../../apps/extension/src/lib/localBridge";

const origin = "chrome-extension://extension-pairing-smoke";
const fixturePairingCredential = "extension-pairing-smoke-secret";
const issuedAtMs = 10_000;

describe("extension pairing smoke", () => {
  test("posts browser telemetry into desktop SQLite with a valid pairing token", async () => {
    const database = createInquiryDatabase();
    const runtime = createDesktopRuntime({
      allowedOrigins: [origin],
      database,
      pairingSecret: fixturePairingCredential,
      startServer: false,
    });
    const handler = createIngestRequestHandler({
      allowedOrigins: [origin],
      database,
      pairingSecret: fixturePairingCredential,
      sessions: runtime.sessions,
      nowMs: () => issuedAtMs,
    });
    const fetchImpl = handlerFetch(handler);
    const initialBridgeState = pairedState("local-browser-session");
    const control = await postSessionControl(
      initialBridgeState,
      { recordingState: "recording", title: "Extension pairing smoke" },
      { fetchImpl },
    );
    const sessionId = control.sessionId ?? "";
    const firstTabMessages: ContentEventMessage[] = [];
    const firstTabTelemetry = createContentTelemetry({
      now: () => 1_000,
      sessionId: "extension-session-before-rebind",
      settings: recordingSettings(),
      location: {
        href: "http://127.0.0.1:39210/demo-article.html",
        hostname: "127.0.0.1",
      },
      sendMessage: (message) => {
        firstTabMessages.push(message);
      },
    });
    const secondTabMessages: ContentEventMessage[] = [];
    const secondTabTelemetry = createContentTelemetry({
      now: () => 2_000,
      sessionId: "second-tab-before-rebind",
      settings: recordingSettings(),
      location: {
        href: "https://example.test/reference-note",
        hostname: "example.test",
      },
      sendMessage: (message) => {
        secondTabMessages.push(message);
      },
    });

    firstTabTelemetry.captureScroll({ scrollY: 320, viewportHeight: 900, documentHeight: 2_400 });
    firstTabTelemetry.captureSelection("highlight", { selectionLength: 28, rangeCount: 1 });
    firstTabTelemetry.captureMedia("seeked", { tagName: "VIDEO", currentTime: 42, duration: 120, paused: false });
    secondTabTelemetry.captureVisibility(false);
    secondTabTelemetry.captureSelection("copy", { selectionLength: 19, rangeCount: 1 });

    const events = [...firstTabMessages, ...secondTabMessages]
      .flatMap((message) => message.events)
      .map((event) => ({ ...event, session_id: sessionId }));
    const result = await postEventBatch(events, { ...initialBridgeState, sessionId }, {
      fetchImpl,
    });
    const stored = database.listEvents(sessionId);
    const browserEvents = stored.filter((event) => event.source === "browser");
    const hostHashes = new Set(browserEvents.map((event) => event.payload.hostname_hash));

    expect(control).toMatchObject({ recordingState: "recording" });
    expect(sessionId).not.toBe("local-browser-session");
    expect(result.accepted).toBe(events.length);
    expect(stored.map((event) => event.event_type)).toEqual([
      "session.started",
      "browser.scroll",
      "browser.highlight",
      "browser.media",
      "browser.visibility",
      "browser.copy",
    ]);
    expect(browserEvents.every((event) => event.session_id === sessionId)).toBe(true);
    expect(hostHashes.size).toBe(2);
    expect(JSON.stringify(stored)).not.toContain("demo-article.html");
    expect(JSON.stringify(stored)).not.toContain("example.test");

    runtime.stop();
  });
});

function pairedState(sessionId: string): BridgeState {
  return {
    endpoint: "http://127.0.0.1:39170/v1/extension/events",
    pairingToken: createPairingToken({ secret: fixturePairingCredential, issuedAtMs, nonce: "smoke-nonce" }),
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
