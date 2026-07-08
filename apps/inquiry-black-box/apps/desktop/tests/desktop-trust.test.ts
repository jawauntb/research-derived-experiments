import { describe, expect, test } from "bun:test";
import { maskPairingToken } from "@inquiry/ui";
import { createEvent } from "@inquiry/schema";
import { createInquiryDatabase } from "../src/main/db";
import { createDesktopIpcFacade } from "../src/main/ipc";
import { createDesktopRuntime } from "../src/main/main";
import { listSessionHistory } from "../src/main/reports/sessionHistory";
import { renderPrivacySettings } from "../src/renderer/settings/PrivacySettings";
import { renderApp, createInitialAppViewModel, type InquiryDesktopBridge } from "../src/renderer/App";
import type { DailyReviewReport } from "../src/main/reports/dailyDigest";
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

  test("shows native pairing notices from desktop deep links", async () => {
    const documentStub = new FakeDocument();
    const globalWithDocument = globalThis as unknown as { document?: unknown };
    const originalDocument = globalWithDocument.document;
    globalWithDocument.document = documentStub;
    let deepLinkHandler: Parameters<NonNullable<InquiryDesktopBridge["deepLinks"]>["onReceived"]>[0] | undefined;

    try {
      const root = documentStub.createElement("div");
      renderApp(root as unknown as HTMLElement, {
        ...shellBridge("header.secret.token"),
        deepLinks: {
          onReceived: (handler) => {
            deepLinkHandler = handler;
            return () => undefined;
          },
        },
      });
      deepLinkHandler?.({
        href: "inquiry-black-box://pair?source=chrome-extension&challenge=pairing-challenge-fixture-123",
        action: "pair",
        source: "chrome-extension",
        challenge: "pairing-challenge-fixture-123",
      });

      expect(root.textContent).toContain("Pairing request received. Return to the Chrome popup to finish one-click pairing.");
      await flushAsync();
    } finally {
      globalWithDocument.document = originalDocument;
    }
  });

  test("persists dark mode choices on the root theme attribute", async () => {
    const documentStub = new FakeDocument();
    const storage = createMemoryLocalStorage({ "inquiry.theme": "dark" });
    const globalWithDocument = globalThis as unknown as {
      document?: unknown;
      localStorage?: unknown;
    };
    const originalDocument = globalWithDocument.document;
    const originalLocalStorage = globalWithDocument.localStorage;
    globalWithDocument.document = documentStub;
    globalWithDocument.localStorage = storage;

    try {
      const root = documentStub.createElement("div");
      renderApp(root as unknown as HTMLElement, shellBridge("header.secret.token"));

      expect(documentStub.documentElement.dataset.theme).toBe("dark");
      root.findAllByTag("button").find((button) => button.textContent === "System")?.click();
      expect(storage.getItem("inquiry.theme")).toBe("system");
      expect(documentStub.documentElement.dataset.theme).toBeUndefined();

      root.findAllByTag("button").find((button) => button.textContent === "Light")?.click();
      expect(storage.getItem("inquiry.theme")).toBe("light");
      expect(documentStub.documentElement.dataset.theme).toBe("light");
      await flushAsync();
    } finally {
      globalWithDocument.document = originalDocument;
      if (originalLocalStorage === undefined) {
        delete globalWithDocument.localStorage;
      } else {
        globalWithDocument.localStorage = originalLocalStorage;
      }
    }
  });

  test("daily review refresh shows progress and completion even when content is unchanged", async () => {
    const documentStub = new FakeDocument();
    const globalWithDocument = globalThis as unknown as { document?: unknown };
    const originalDocument = globalWithDocument.document;
    globalWithDocument.document = documentStub;
    const review = dailyReviewFixture("Daily review built from one interpretation.");
    let resolveRefresh!: (review: DailyReviewReport) => void;
    const refreshPromise = new Promise<DailyReviewReport>((resolve) => {
      resolveRefresh = resolve;
    });

    try {
      const root = documentStub.createElement("div");
      renderApp(root as unknown as HTMLElement, dailyReviewBridge(review, () => refreshPromise), {
        ...createInitialAppViewModel(),
        dailyReview: review,
      });

      const refresh = root.findAllByTag("button").find((button) => button.textContent === "Refresh");
      refresh?.click();
      expect(root.textContent).toContain("Refreshing daily review...");
      expect(root.findAllByTag("button").find((button) => button.textContent === "Refreshing...")?.disabled).toBe(true);

      resolveRefresh(review);
      await flushAsync();
      await flushAsync();

      expect(root.textContent).toContain("Daily review refreshed.");
      await flushAsync();
    } finally {
      globalWithDocument.document = originalDocument;
    }
  });

  test("daily review refresh reports failures instead of failing silently", async () => {
    const documentStub = new FakeDocument();
    const globalWithDocument = globalThis as unknown as { document?: unknown };
    const originalDocument = globalWithDocument.document;
    globalWithDocument.document = documentStub;
    const review = dailyReviewFixture("Daily review built from one interpretation.");

    try {
      const root = documentStub.createElement("div");
      renderApp(root as unknown as HTMLElement, dailyReviewBridge(review, async () => {
        throw new Error("database is busy");
      }), {
        ...createInitialAppViewModel(),
        dailyReview: review,
      });

      root.findAllByTag("button").find((button) => button.textContent === "Refresh")?.click();
      await flushAsync();
      await flushAsync();

      expect(root.textContent).toContain("Daily review refresh failed: database is busy");
      await flushAsync();
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
        llmDocumentContext: false,
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
            llmDocumentContext: false,
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

  test("selects the latest stored session on launch so interpretation actions are reachable", async () => {
    const database = createInquiryDatabase();
    const session = database.createSession({ title: "Stored summary fixture", session_id: "stored-summary-session" });
    database.appendEvent(
      createEvent({
        session_id: session.session_id,
        source: "browser",
        source_version: "test@0.1.0",
        monotonic_ms: 1_000,
        event_type: "browser.scroll",
        payload: { delta_y: 400 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );
    database.stopSession(session.session_id);

    const runtime = createDesktopRuntime({ database, pairingSecret: "summary-launch-secret", startServer: false });
    const facade = createDesktopIpcFacade(runtime);

    expect((await facade.status()).session?.session_id).toBe(session.session_id);
    expect((await facade.sessionInterpretation())?.session_id).toBe(session.session_id);
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

function dailyReviewBridge(
  review: DailyReviewReport,
  refreshDaily: () => Promise<DailyReviewReport>,
): InquiryDesktopBridge {
  return {
    ...shellBridge("header.secret.token"),
    interpretation: {
      session: async () => null,
      requestRedactedSummary: async () => {
        throw new Error("not used");
      },
      daily: async () => review,
      refreshDaily,
      respondSuggestion: async () => {
        throw new Error("not used");
      },
    },
  };
}

function dailyReviewFixture(summary: string): DailyReviewReport {
  return {
    report_id: "daily-review:fixture",
    report_kind: "daily_review",
    local_date: "2026-07-08",
    generated_at: "2026-07-08T06:00:00.000Z",
    summary,
    sections: {
      helped: [],
      fragmented: [],
      retry: [],
      ignore: [],
      open_loops: [],
      care_candidates: [],
    },
    suggestions: [],
    limitations: ["Refresh status fixture."],
    evidence_event_ids: [],
    source_report_ids: [],
    provenance: {
      builder: "test",
    },
  };
}

class FakeDocument {
  readonly documentElement = new FakeElement("html");

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
  private attributes: Record<string, string> = {};
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
    this.attributes[name] = value;
    if (name === "data-theme") {
      this.dataset.theme = value;
    }
    if (name === "aria-live") {
      this.className += ` aria-${value}`;
    }
  }

  removeAttribute(name: string): void {
    delete this.attributes[name];
    if (name === "data-theme") {
      delete this.dataset.theme;
    }
  }

  getAttribute(name: string): string | null {
    return this.attributes[name] ?? null;
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

function createMemoryLocalStorage(initial: Record<string, string> = {}): Storage {
  const state = { ...initial };
  return {
    get length() {
      return Object.keys(state).length;
    },
    clear() {
      for (const key of Object.keys(state)) {
        delete state[key];
      }
    },
    getItem(key: string) {
      return state[key] ?? null;
    },
    key(index: number) {
      return Object.keys(state)[index] ?? null;
    },
    removeItem(key: string) {
      delete state[key];
    },
    setItem(key: string, value: string) {
      state[key] = value;
    },
  };
}

async function flushAsync(): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, 0));
}
