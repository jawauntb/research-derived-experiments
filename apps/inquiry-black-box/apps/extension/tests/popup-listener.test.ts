import { describe, expect, test } from "bun:test";
import { CONTENT_PING_MESSAGE, CONTENT_PONG_MESSAGE } from "../src/lib/messages";
import { detectPageListener, pageListenerLabel } from "../src/popup/App";

describe("popup page listener status", () => {
  test("reports an attached content script without injecting again", async () => {
    let injected = false;
    const status = await detectPageListener({
      tabs: {
        query: (_query, callback) => callback([]),
        sendMessage: (_tabId, message, callback) => {
          expect(message).toEqual({ type: CONTENT_PING_MESSAGE });
          callback?.({ type: CONTENT_PONG_MESSAGE, ok: true });
        },
      },
      scripting: {
        executeScript: () => {
          injected = true;
        },
      },
    }, { id: 7, url: "http://127.0.0.1:4173/demo-article.html" });

    expect(status).toEqual({ status: "attached" });
    expect(injected).toBe(false);
  });

  test("injects the content script when the active tab does not answer the ping", async () => {
    let pingCount = 0;
    let injectedFile = "";

    const status = await detectPageListener({
      tabs: {
        query: (_query, callback) => callback([]),
        sendMessage: (_tabId, message, callback) => {
          expect(message).toEqual({ type: CONTENT_PING_MESSAGE });
          pingCount += 1;
          callback?.(pingCount === 1 ? undefined : { type: CONTENT_PONG_MESSAGE, ok: true });
        },
      },
      scripting: {
        executeScript: (details, callback) => {
          injectedFile = details.files[0] ?? "";
          callback?.();
        },
      },
    }, { id: 8, url: "https://example.test/article" });

    expect(status).toEqual({ status: "attached" });
    expect(pingCount).toBe(2);
    expect(injectedFile).toBe("dist/content/index.js");
  });

  test("marks browser-internal pages as unsupported", async () => {
    const status = await detectPageListener({}, { id: 9, url: "chrome://extensions" });

    expect(status).toEqual({ status: "unsupported", detail: "not an http tab" });
    expect(pageListenerLabel(status)).toBe("Unavailable - not an http tab");
  });

  test("surfaces the attach failure reason when script injection misses", async () => {
    const status = await detectPageListener({
      runtime: { sendMessage: () => undefined },
      tabs: {
        query: (_query, callback) => callback([]),
        sendMessage: (_tabId, _message, callback) => {
          callback?.(undefined);
        },
      },
      scripting: {
        executeScript: (_details, callback) => {
          callback?.();
        },
      },
    }, { id: 10, url: "http://127.0.0.1:4173/demo-article.html" });

    expect(status.status).toBe("missing");
    expect(pageListenerLabel({ status: "missing", detail: "tabs permission unavailable" })).toBe(
      "Missing - tabs permission unavailable",
    );
  });
});
