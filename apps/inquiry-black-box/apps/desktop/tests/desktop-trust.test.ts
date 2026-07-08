import { describe, expect, test } from "bun:test";
import { maskPairingToken } from "@inquiry/ui";
import { createEvent } from "@inquiry/schema";
import { createInquiryDatabase } from "../src/main/db";
import { createDesktopIpcFacade } from "../src/main/ipc";
import { createDesktopRuntime } from "../src/main/main";
import { listSessionHistory } from "../src/main/reports/sessionHistory";
import { renderPrivacySettings } from "../src/renderer/settings/PrivacySettings";
import { renderApp, createInitialAppViewModel, type InquiryDesktopBridge } from "../src/renderer/App";
import { defaultPrivacySettingsView } from "../src/renderer/settings/PrivacySettings";

describe("desktop shell trust surfaces", () => {
  test("masks pairing token by default in the shell header", async () => {
    const documentStub = new FakeDocument();
    const globalWithDocument = globalThis as unknown as { document?: unknown };
    const originalDocument = globalWithDocument.document;
    globalWithDocument.document = documentStub;

    try {
      const root = documentStub.createElement("div");
      const token = "header.secret.token";
      const status = shellStatus(token);
      renderApp(root as unknown as HTMLElement, shellBridge(token), {
        ...createInitialAppViewModel(),
        status,
      });
      await flushAsync();

      expect(root.textContent).not.toContain(token);
      expect(root.textContent).toContain(maskPairingToken(token, false));
      expect(root.textContent).toContain("Reveal");
    } finally {
      globalWithDocument.document = originalDocument;
    }
  });

  test("requires delete confirmation before calling privacy delete", async () => {
    await flushAsync();
    const documentStub = new FakeDocument();
    const globalWithDocument = globalThis as unknown as { document?: unknown; confirm?: (message?: string) => boolean };
    const originalDocument = globalWithDocument.document;
    const originalConfirm = globalWithDocument.confirm;
    globalWithDocument.document = documentStub;
    let confirmed = false;
    let deleteCalls = 0;
    globalWithDocument.confirm = () => confirmed;

    try {
      const root = documentStub.createElement("div");
      renderPrivacySettings(root as unknown as HTMLElement, defaultPrivacySettingsView({
        browser: true,
        camera: false,
        desktopActivity: false,
        desktopWindowTitles: false,
        screenSnapshots: false,
        typingMetrics: true,
        notifications: false,
        cloudSync: false,
      }), {
        setSignalEnabled: async () => {
          void defaultPrivacySettingsView({
            browser: true,
            camera: false,
            desktopActivity: false,
            desktopWindowTitles: false,
            screenSnapshots: false,
            typingMetrics: true,
            notifications: false,
            cloudSync: false,
          });
        },
        exportSession: async () => undefined,
        deleteSession: async () => {
          deleteCalls += 1;
        },
      });

      const deleteButton = root.findAllByTag("button").find((button) => button.textContent === "Delete session");
      expect(deleteButton?.className).toContain("privacy-delete-button");
      deleteButton!.click();
      expect(deleteCalls).toBe(0);

      confirmed = true;
      deleteButton!.click();
      expect(deleteCalls).toBe(1);
    } finally {
      globalWithDocument.document = originalDocument;
      if (originalConfirm === undefined) {
        delete globalWithDocument.confirm;
      } else {
        globalWithDocument.confirm = originalConfirm;
      }
    }
  });

  test("lists recent sessions with derived verdict metadata", async () => {
    const database = createInquiryDatabase();
    const first = database.createSession({ title: "Earlier session", session_id: "session-history-1" });
    const second = database.createSession({ title: "Later session", session_id: "session-history-2" });
    database.appendEvent(
      createEvent({
        session_id: second.session_id,
        source: "browser",
        source_version: "test@0.1.0",
        monotonic_ms: 1_000,
        event_type: "browser.scroll",
        payload: { delta_y: 4_200 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );
    database.stopSession(second.session_id);

    const history = listSessionHistory(database);
    expect(history[0]?.session_id).toBe(second.session_id);
    expect(history[1]?.session_id).toBe(first.session_id);
    expect(history[0]?.title).toBe("Later session");
    database.close();
  });

  test("exposes session history and demo replay through IPC", async () => {
    const database = createInquiryDatabase();
    const runtime = createDesktopRuntime({ database, pairingSecret: "history-test-secret", startServer: false });
    const facade = createDesktopIpcFacade(runtime);
    const session = await facade.startSession({ title: "History IPC fixture" });
    await facade.stopSession();

    const history = await facade.listSessionHistory();
    expect(history.some((entry) => entry.session_id === session.session_id)).toBe(true);

    const demo = await facade.demoReplayReport();
    expect(demo.markers.length + demo.heatmap.length).toBeGreaterThan(0);
    runtime.stop();
  });
});

function shellStatus(token: string) {
  return {
    session: null,
    recordingState: "idle" as const,
    pairingToken: token,
    ingestUrl: "http://127.0.0.1:39170",
    desktopActivity: {
      enabled: false,
      includeWindowTitles: false,
      active: false,
      permission_status: "not_requested" as const,
    },
  };
}

function shellBridge(token: string): InquiryDesktopBridge {
  const status = shellStatus(token);
  return {
    status: {
      current: async () => status,
    },
    session: {
      currentSession: async () => null,
      startSession: async () => {
        throw new Error("not used");
      },
      pauseSession: async () => {
        throw new Error("not used");
      },
      resumeSession: async () => {
        throw new Error("not used");
      },
      stopSession: async () => {
        throw new Error("not used");
      },
      addLabel: async () => {
        throw new Error("not used");
      },
    },
    camera: {
      requestCamera: async () => "denied",
      disableCamera: async () => undefined,
      appendFeatureWindow: async () => {
        throw new Error("not used");
      },
    },
    sessions: {
      listHistory: async () => [],
      select: async () => null,
    },
  };
}

class FakeDocument {
  createElement(tagName: string): FakeElement {
    return new FakeElement(tagName);
  }

  createTextNode(text: string): FakeText {
    return new FakeText(text);
  }
}

class FakeElement {
  readonly tagName: string;
  className = "";
  dataset: Record<string, string> = {};
  type = "";
  disabled = false;
  value = "";
  placeholder = "";
  private ownText = "";
  private children: Array<FakeElement | FakeText> = [];
  private clickListeners: Array<() => void> = [];

  constructor(tagName: string) {
    this.tagName = tagName;
  }

  get textContent(): string {
    return this.ownText + this.children.map((child) => child.textContent).join("");
  }

  set textContent(value: string) {
    this.ownText = value;
    this.children = [];
  }

  append(...nodes: Array<FakeElement | FakeText>): void {
    this.children.push(...nodes);
  }

  replaceChildren(...nodes: Array<FakeElement | FakeText>): void {
    this.ownText = "";
    this.children = [...nodes];
  }

  addEventListener(type: string, listener: () => void): void {
    if (type === "click") {
      this.clickListeners.push(listener);
    }
  }

  setAttribute(name: string, value: string): void {
    if (name === "aria-live") {
      this.className += ` aria-${value}`;
    }
  }

  click(): void {
    for (const listener of this.clickListeners) {
      listener();
    }
  }

  findAllByTag(tagName: string): FakeElement[] {
    const matches: FakeElement[] = [];
    if (this.tagName === tagName) {
      matches.push(this);
    }
    for (const child of this.children) {
      if (child instanceof FakeElement) {
        matches.push(...child.findAllByTag(tagName));
      }
    }
    return matches;
  }
}

class FakeText {
  constructor(readonly textContent: string) {}
}

async function flushAsync(): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, 0));
}
