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

    expect(status).toBe("attached");
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

    expect(status).toBe("attached");
    expect(pingCount).toBe(2);
    expect(injectedFile).toBe("dist/content/index.js");
  });

  test("marks browser-internal pages as unsupported", async () => {
    const status = await detectPageListener({}, { id: 9, url: "chrome://extensions" });

    expect(status).toBe("unsupported");
    expect(pageListenerLabel(status)).toBe("Unavailable on this page");
  });
});
