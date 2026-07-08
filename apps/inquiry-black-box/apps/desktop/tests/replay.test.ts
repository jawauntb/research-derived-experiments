import { describe, expect, test } from "bun:test";
import { createEvent, type SessionRecord } from "@inquiry/schema";
import type { RepairCandidate } from "@inquiry/signals";
import type { DailyReviewReport } from "../src/main/reports/dailyDigest";
import type { SessionInterpretationReport } from "../src/main/reports/sessionInterpretation";
import { createSessionReplayReport } from "../src/main/reports/sessionReplay";
import { createInitialAppViewModel, renderApp, type InquiryDesktopBridge } from "../src/renderer/App";
import { renderDailyReviewPanel } from "../src/renderer/daily/DailyReviewPanel";
import { renderSessionInterpretationPanel } from "../src/renderer/interpretation/SessionInterpretationPanel";
import { renderProbePanel } from "../src/renderer/probes/ProbePanel";
import { renderReplayTimeline } from "../src/renderer/replay/ReplayTimeline";

describe("session replay report", () => {
  test("creates a replay report with limitations and next actions", () => {
    const events = [
      createEvent({
        session_id: "replay-session",
        source: "browser",
        source_version: "test@0.1.0",
        monotonic_ms: 1_000,
        event_type: "browser.scroll",
        payload: { delta_y: 4200 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
      createEvent({
        session_id: "replay-session",
        source: "browser",
        source_version: "test@0.1.0",
        monotonic_ms: 2_000,
        event_type: "browser.dwell",
        payload: { dwell_ms: 200 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ];

    const report = createSessionReplayReport(events);

    expect(report.markers.some((marker) => marker.kind === "skim-risk")).toBe(true);
    expect(report.heatmap.some((segment) => segment.kind === "behavior-only")).toBe(true);
    expect(report.repair_candidates.some((candidate) => candidate.action === "recall-question")).toBe(true);
    expect(report.next_actions.length).toBe(1);
    expect(report.limitations.join(" ")).toContain("not cognitive-state certainty");
  });

  test("adds local stimulus heatmap without raw document text by default", () => {
    const events = [
      createEvent({
        session_id: "replay-session",
        source: "browser",
        source_version: "test@0.1.0",
        monotonic_ms: 12_000,
        event_type: "browser.visibility",
        payload: { state: "revisited" },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
      createEvent({
        session_id: "replay-session",
        source: "browser",
        source_version: "test@0.1.0",
        monotonic_ms: 13_000,
        event_type: "browser.visibility",
        payload: { state: "revisited" },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
      createEvent({
        session_id: "replay-session",
        source: "browser",
        source_version: "test@0.1.0",
        monotonic_ms: 14_000,
        event_type: "browser.media",
        payload: { action: "seeked", delta_ms: -9000 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ];

    const report = createSessionReplayReport(events, {
      stimulus_inputs: [
        {
          stimulus_id: "demo-article",
          source: "article",
          duration_ms: 60_000,
          text: "This easy paragraph repeats the result. Then it repeats the result again.",
        },
      ],
    });

    expect(report.heatmap.some((segment) => segment.kind === "behavioral-loss-of-thread")).toBe(true);
    expect(report.repair_candidates.some((candidate) => candidate.action === "missing-prerequisite")).toBe(true);
    expect(report.heatmap.every((segment) => segment.evidence_event_ids.length > 0 || segment.stimulus_evidence.length > 0)).toBe(
      true,
    );
    expect(JSON.stringify(report)).not.toContain("This easy paragraph repeats");
  });

  test("creates privacy-aware evidence episodes for copied browser bursts", () => {
    const report = createSessionReplayReport([
      createEvent({
        session_id: "replay-session",
        source: "browser",
        source_version: "test@0.1.0",
        monotonic_ms: 21_000,
        event_type: "browser.selection",
        payload: { hostname_hash: "h_demo", url_hash: "h_page", selection_length: 807, range_count: 1 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
      createEvent({
        session_id: "replay-session",
        source: "browser",
        source_version: "test@0.1.0",
        monotonic_ms: 22_000,
        event_type: "browser.highlight",
        payload: { hostname_hash: "h_demo", url_hash: "h_page", selection_length: 820, range_count: 1 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
      createEvent({
        session_id: "replay-session",
        source: "browser",
        source_version: "test@0.1.0",
        monotonic_ms: 23_000,
        event_type: "browser.copy",
        payload: { hostname_hash: "h_demo", url_hash: "h_page", selection_length: 832, range_count: 1 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ]);

    expect(report.episodes).toHaveLength(1);
    expect(report.markers.filter((marker) => marker.kind === "copied-passage")).toHaveLength(1);
    expect(report.episodes[0]?.summary).toContain("1 selection change, 1 highlight, and 1 copy action");
    expect(report.episodes[0]?.details.join(" ")).toContain("Selection length ranged 807-832 characters");
    expect(report.episodes[0]?.privacy_note).toContain("Raw selected or copied text was not stored");
    expect(report.limitations.join(" ")).toContain("Copied or selected page text is not stored");
  });

  test("shows opted-in selected text snippets in replay evidence episodes", () => {
    const report = createSessionReplayReport([
      createEvent({
        session_id: "replay-session",
        source: "browser",
        source_version: "test@0.1.0",
        monotonic_ms: 23_000,
        event_type: "browser.copy",
        payload: {
          hostname_hash: "h_demo",
          url_hash: "h_page",
          selection_length: 41,
          range_count: 1,
          selected_text: "repair should be evidence-backed and answerable",
        },
        privacy_class: "document-opt-in",
        retention_policy: "session-delete",
      }),
    ]);

    expect(report.episodes).toHaveLength(1);
    expect(report.episodes[0]?.details.join(" ")).toContain(
      'Opt-in excerpt: "repair should be evidence-backed and answerable"',
    );
    expect(report.episodes[0]?.privacy_note).toContain("Selected text was stored");
  });

  test("renders heatmap bands with confidence, evidence, and limitation text", () => {
    const documentStub = new FakeDocument();
    const globalWithDocument = globalThis as unknown as { document?: unknown };
    const originalDocument = globalWithDocument.document;
    globalWithDocument.document = documentStub;

    try {
      const report = createSessionReplayReport(
        [
          createEvent({
            session_id: "replay-session",
            source: "browser",
            source_version: "test@0.1.0",
            monotonic_ms: 1_000,
            event_type: "browser.scroll",
            payload: { delta_y: 4200 },
            privacy_class: "local-derived",
            retention_policy: "local-default",
          }),
          createEvent({
            session_id: "replay-session",
            source: "browser",
            source_version: "test@0.1.0",
            monotonic_ms: 2_000,
            event_type: "browser.dwell",
            payload: { dwell_ms: 200 },
            privacy_class: "local-derived",
            retention_policy: "local-default",
          }),
        ],
        {
          stimulus_inputs: [
            {
              stimulus_id: "dense-article",
              source: "article",
              duration_ms: 30_000,
              text: "Counterfactual baselines and residual stimulus transitions determine explanatory load.",
            },
          ],
        },
      );
      const firstHeatmapSegment = report.heatmap[0];
      expect(firstHeatmapSegment).toBeDefined();
      if (!firstHeatmapSegment) {
        throw new Error("expected at least one heatmap segment");
      }

      const root = documentStub.createElement("div");

      renderReplayTimeline(root as unknown as HTMLElement, report);

      expect(root.textContent).toContain("Reading engagement map");
      expect(root.textContent).toContain("Evidence events:");
      expect(root.textContent).toContain(firstHeatmapSegment.limitation);
      expect(root.findByDataset("heatmapKind", firstHeatmapSegment.kind)).toBeDefined();
    } finally {
      globalWithDocument.document = originalDocument;
    }
  });

  test("renders evidence episodes before low-level replay markers", () => {
    const documentStub = new FakeDocument();
    const globalWithDocument = globalThis as unknown as { document?: unknown };
    const originalDocument = globalWithDocument.document;
    globalWithDocument.document = documentStub;

    try {
      const report = createSessionReplayReport([
        createEvent({
          session_id: "replay-session",
          source: "browser",
          source_version: "test@0.1.0",
          monotonic_ms: 21_000,
          event_type: "browser.selection",
          payload: { hostname_hash: "h_demo", url_hash: "h_page", selection_length: 807, range_count: 1 },
          privacy_class: "local-derived",
          retention_policy: "local-default",
        }),
        createEvent({
          session_id: "replay-session",
          source: "browser",
          source_version: "test@0.1.0",
          monotonic_ms: 22_000,
          event_type: "browser.highlight",
          payload: { hostname_hash: "h_demo", url_hash: "h_page", selection_length: 832, range_count: 1 },
          privacy_class: "local-derived",
          retention_policy: "local-default",
        }),
      ]);
      const root = documentStub.createElement("div");

      renderReplayTimeline(root as unknown as HTMLElement, report);

      expect(root.textContent).toContain("Evidence");
      expect(root.textContent).toContain("Selection length ranged 807-832 characters");
      expect(root.textContent).toContain("Raw selected or copied text was not stored");
      expect(root.findByDataset("episodeKind", "copied-selection")).toBeDefined();
    } finally {
      globalWithDocument.document = originalDocument;
    }
  });

  test("renders an explicit no-event replay state", () => {
    const documentStub = new FakeDocument();
    const globalWithDocument = globalThis as unknown as { document?: unknown };
    const originalDocument = globalWithDocument.document;
    globalWithDocument.document = documentStub;

    try {
      const root = documentStub.createElement("div");
      const report = createSessionReplayReport([]);

      renderReplayTimeline(root as unknown as HTMLElement, report);

      expect(root.textContent).toContain("No replay evidence yet");
      expect(root.textContent).toContain("Stop a session after browser, camera, label, or probe events arrive");
    } finally {
      globalWithDocument.document = originalDocument;
    }
  });

  test("renders desktop app context without requiring window titles", () => {
    const documentStub = new FakeDocument();
    const globalWithDocument = globalThis as unknown as { document?: unknown };
    const originalDocument = globalWithDocument.document;
    globalWithDocument.document = documentStub;

    try {
      const root = documentStub.createElement("div");
      const report = createSessionReplayReport([
        createEvent({
          session_id: "replay-session",
          source: "desktop-activity",
          source_version: "test@0.1.0",
          monotonic_ms: 360_000,
          event_type: "desktop.app_focus",
          payload: {
            app_name: "Preview",
            bundle_id: "com.apple.Preview",
            focus_started_monotonic_ms: 60_000,
            focus_ended_monotonic_ms: 360_000,
            duration_ms: 300_000,
            permission_status: "granted",
          },
          privacy_class: "local-derived",
          retention_policy: "local-default",
        }),
      ]);

      renderReplayTimeline(root as unknown as HTMLElement, report);

      expect(root.textContent).toContain("Preview held foreground");
      expect(root.textContent).toContain("off-browser-focus");
      expect(root.textContent).not.toContain("window_title");
      expect(report.limitations.join(" ")).toContain("raw screenshots");
    } finally {
      globalWithDocument.document = originalDocument;
    }
  });

  test("renders session interpretation and daily suggestion feedback controls", () => {
    const documentStub = new FakeDocument();
    const globalWithDocument = globalThis as unknown as { document?: unknown };
    const originalDocument = globalWithDocument.document;
    globalWithDocument.document = documentStub;

    try {
      const interpretationRoot = documentStub.createElement("div");
      const dailyRoot = documentStub.createElement("div");
      const responses: string[] = [];
      const analysisContexts: string[] = [];

      renderSessionInterpretationPanel(interpretationRoot as unknown as HTMLElement, interpretationFixture(), {
        cloudSyncEnabled: true,
        documentContextEnabled: true,
        requestRedactedSummary: (input) => {
          analysisContexts.push(input?.additionalContext ?? "");
        },
      });
      renderDailyReviewPanel(dailyRoot as unknown as HTMLElement, dailyReviewFixture(), {
        refreshDailyReview: () => {
          responses.push("refresh");
        },
        respondSuggestion: (input) => {
          responses.push(`${input.suggestion_id}:${input.response}`);
        },
      });

      expect(interpretationRoot.textContent).toContain("Session Interpretation");
      expect(interpretationRoot.textContent).toContain("Repeated skim risk");
      expect(interpretationRoot.textContent).toContain("Analyze and ask about your data");
      expect(interpretationRoot.textContent).toContain("Opted-in page/selection text");
      expect(interpretationRoot.textContent).not.toContain("Request redacted LLM summary");
      expect(interpretationRoot.findByDataset("themeKind", "retry")).toBeDefined();
      const analysisTextarea = interpretationRoot.findByTag("textarea");
      const analysisButton = interpretationRoot.findByTag("button");
      expect(analysisTextarea?.attributes["aria-label"]).toBe("Additional analysis context");
      analysisTextarea!.value = "I was trying to compare two definitions.";
      analysisButton!.click();
      expect(analysisContexts).toEqual(["I was trying to compare two definitions."]);
      expect(dailyRoot.textContent).toContain("Daily Review");
      expect(dailyRoot.textContent).toContain("What to retry");
      expect(dailyRoot.findByDataset("suggestionId", "suggestion-render-1")).toBeDefined();

      const buttons = dailyRoot.findAllByTag("button");
      expect(buttons.map((button) => button.textContent)).toEqual(["Refresh", "Accept", "Snooze", "Dismiss", "Useful", "Not useful"]);
      buttons[0]!.click();
      buttons[1]!.click();
      buttons[5]!.click();

      expect(responses[0]).toBe("refresh");
      expect(responses).toContain("suggestion-render-1:accepted");
      expect(responses).toContain("suggestion-render-1:rated-not-useful");
    } finally {
      globalWithDocument.document = originalDocument;
    }
  });

  test("refreshes replay after stop and repair answers", async () => {
    const documentStub = new FakeDocument();
    const globalWithDocument = globalThis as unknown as { document?: unknown };
    const originalDocument = globalWithDocument.document;
    globalWithDocument.document = documentStub;

    try {
      const root = documentStub.createElement("div");
      const session = sessionFixture("recording");
      const stopped = { ...session, recording_state: "stopped" as const, ended_at: "2026-07-07T12:01:00.000Z" };
      let replayCalls = 0;
      let stoppedSession = false;
      let answeredRepair = false;
      const bridge: InquiryDesktopBridge = {
        status: {
          current: async () => ({
            session: stoppedSession ? stopped : session,
            recordingState: stoppedSession ? "stopped" : "recording",
            ingestUrl: "http://127.0.0.1:39170",
            pairingToken: "pairing-token",
            desktopActivity: {
              enabled: false,
              includeWindowTitles: false,
              active: false,
              permission_status: "not_requested",
            },
          }),
        },
        session: {
          currentSession: async () => (stoppedSession ? stopped : session),
          startSession: async () => session,
          pauseSession: async () => ({ ...session, recording_state: "paused" }),
          resumeSession: async () => session,
          stopSession: async () => {
            stoppedSession = true;
            return stopped;
          },
          addLabel: async () =>
            createEvent({
              session_id: session.session_id,
              source: "desktop-system",
              source_version: "test@0.1.0",
              monotonic_ms: 1,
              event_type: "label.added",
              payload: { label: "flow" },
              privacy_class: "local-derived",
              retention_policy: "local-default",
            }),
        },
        camera: {
          requestCamera: async () => "granted",
          disableCamera: async () => undefined,
          appendFeatureWindow: async () =>
            createEvent({
              session_id: session.session_id,
              source: "desktop-camera",
              source_version: "test@0.1.0",
              monotonic_ms: 1,
              event_type: "camera.feature_window",
              payload: { window_ms: 1000 },
              privacy_class: "local-derived",
              retention_policy: "local-default",
            }),
        },
        replay: {
          report: async () => {
            replayCalls += 1;
            return stoppedSession
              ? createSessionReplayReport([
                  createEvent({
                    session_id: session.session_id,
                    source: "browser",
                    source_version: "test@0.1.0",
                    monotonic_ms: 500,
                    event_type: "browser.scroll",
                    payload: { delta_y: 4_800, scroll_y: 4_800, viewport_h: 900 },
                    privacy_class: "local-derived",
                    retention_policy: "local-default",
                  }),
                  createEvent({
                    session_id: session.session_id,
                    source: "browser",
                    source_version: "test@0.1.0",
                    monotonic_ms: 900,
                    event_type: "browser.dwell",
                    payload: { dwell_ms: 200 },
                    privacy_class: "local-derived",
                    retention_policy: "local-default",
                  }),
                  createEvent({
                    session_id: session.session_id,
                    source: "browser",
                    source_version: "test@0.1.0",
                    monotonic_ms: 1_000,
                    event_type: "browser.copy",
                    payload: { hostname_hash: "host", url_hash: "page", selection_length: 20, range_count: 1 },
                    privacy_class: "local-derived",
                    retention_policy: "local-default",
                  }),
                  ...(answeredRepair
                    ? [
                        createEvent({
                          session_id: session.session_id,
                          source: "desktop-system",
                          source_version: "test@0.1.0",
                          monotonic_ms: 2_000,
                          event_type: "repair.outcome",
                          payload: { repair_id: "repair-render-1", outcome: "answered" },
                          privacy_class: "local-derived",
                          retention_policy: "local-default",
                        }),
                      ]
                    : []),
                ])
              : null;
          },
        },
        repair: {
          accept: async () =>
            createEvent({
              session_id: session.session_id,
              source: "desktop-system",
              source_version: "test@0.1.0",
              monotonic_ms: 1,
              event_type: "probe.requested",
              payload: { repair_id: "repair-render-1" },
              privacy_class: "local-derived",
              retention_policy: "local-default",
            }),
          answer: async () => {
            answeredRepair = true;
            return [];
          },
          dismiss: async () =>
            createEvent({
              session_id: session.session_id,
              source: "desktop-system",
              source_version: "test@0.1.0",
              monotonic_ms: 1,
              event_type: "repair.outcome",
              payload: { repair_id: "repair-render-1", outcome: "dismissed" },
              privacy_class: "local-derived",
              retention_policy: "local-default",
            }),
        },
      };

      renderApp(root as unknown as HTMLElement, bridge, {
        ...createInitialAppViewModel(session),
        replay: null,
      });
      await flushAsync();

      const stopButton = root.findAllByTag("button").find((button) => button.textContent === "Stop");
      expect(stopButton).toBeDefined();
      stopButton!.click();
      await flushAsync();

      expect(root.textContent).toContain("Evidence");
      expect(root.textContent).toContain("Raw selected or copied text was not stored");
      expect(replayCalls).toBeGreaterThanOrEqual(2);

      const textarea = root.findByTag("textarea");
      const saveButton = root.findAllByTag("button").find((button) => button.textContent === "Save answer");
      expect(textarea).toBeDefined();
      expect(saveButton).toBeDefined();
      textarea!.value = "The copied claim needed a concrete check.";
      saveButton!.click();
      await flushAsync();

      expect(answeredRepair).toBe(true);
      expect(replayCalls).toBeGreaterThanOrEqual(3);
    } finally {
      globalWithDocument.document = originalDocument;
    }
  });

  test("renders repair probe actions for start, answer, and dismiss", () => {
    const documentStub = new FakeDocument();
    const globalWithDocument = globalThis as unknown as { document?: unknown };
    const originalDocument = globalWithDocument.document;
    globalWithDocument.document = documentStub;

    try {
      const root = documentStub.createElement("div");
      const accepted: string[] = [];
      const answered: Array<{ repair_id: string; answer: string; confidence: number }> = [];
      const dismissed: string[] = [];

      renderProbePanel(root as unknown as HTMLElement, repairCandidateFixture(), {
        acceptRepair: (repair_id) => {
          accepted.push(repair_id);
        },
        answerRepair: (answer) => {
          answered.push(answer);
        },
        dismissRepair: (repair_id) => {
          dismissed.push(repair_id);
        },
      });

      const textarea = root.findByTag("textarea");
      const confidence = root.findByTag("input");
      const buttons = root.findAllByTag("button");
      expect(textarea).toBeDefined();
      expect(confidence).toBeDefined();
      expect(buttons).toHaveLength(3);
      textarea!.value = "The missing piece was the baseline.";
      confidence!.value = "0.8";

      buttons[0]!.click();
      buttons[1]!.click();
      buttons[2]!.click();

      expect(accepted).toEqual(["repair-render-1"]);
      expect(answered).toEqual([
        {
          repair_id: "repair-render-1",
          answer: "The missing piece was the baseline.",
          confidence: 0.8,
        },
      ]);
      expect(dismissed).toEqual(["repair-render-1"]);
    } finally {
      globalWithDocument.document = originalDocument;
    }
  });
});

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
  rows = 0;
  type = "";
  min = "";
  max = "";
  step = "";
  value = "";
  checked = false;
  disabled = false;
  attributes: Record<string, string> = {};
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
  }

  click(): void {
    for (const listener of this.clickListeners) {
      listener();
    }
  }

  findByDataset(key: string, value: string): FakeElement | undefined {
    if (this.dataset[key] === value) {
      return this;
    }

    for (const child of this.children) {
      if (child instanceof FakeElement) {
        const match = child.findByDataset(key, value);
        if (match) {
          return match;
        }
      }
    }

    return undefined;
  }

  findByTag(tagName: string): FakeElement | undefined {
    return this.findAllByTag(tagName)[0];
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

function sessionFixture(recordingState: SessionRecord["recording_state"]): SessionRecord {
  return {
    session_id: "replay-render-session",
    title: "Replay renderer session",
    started_at: "2026-07-07T12:00:00.000Z",
    recording_state: recordingState,
    created_at: "2026-07-07T12:00:00.000Z",
    updated_at: "2026-07-07T12:00:00.000Z",
  };
}

async function flushAsync(): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, 0));
}

function repairCandidateFixture(): RepairCandidate {
  return {
    repair_id: "repair-render-1",
    session_id: "replay-session",
    heatmap_id: "heatmap-render-1",
    action: "missing-prerequisite",
    prompt: "What prerequisite was missing?",
    start_ms: 1000,
    end_ms: 2000,
    confidence: 0.75,
    source_kind: "behavioral-loss-of-thread",
    source_marker_ids: ["marker-render-1"],
    evidence_event_ids: ["event-render-1"],
    limitation: "repair hypothesis",
  };
}

function interpretationFixture(): SessionInterpretationReport {
  return {
    report_id: "session-interpretation:render",
    report_kind: "session_interpretation",
    session_id: "replay-render-session",
    generated_at: "2026-07-07T12:10:00.000Z",
    summary: "Replay evidence suggests one retry theme and one concrete next action.",
    confidence: 0.78,
    themes: [
      {
        theme_id: "theme-render-1",
        title: "Repeated skim risk",
        detail: "Fast movement followed by short dwell suggests this passage should be revisited.",
        kind: "retry",
        confidence: 0.78,
        marker_ids: ["marker-render-1"],
        evidence_event_ids: ["event-render-1"],
        limitation: "Local marker evidence only.",
      },
    ],
    next_actions: [
      {
        suggestion_id: "suggestion-render-1",
        suggestion_kind: "retry",
        category: "retry",
        title: "Retry the skipped span",
        action: "Write one question the skipped span should answer.",
        rationale: "Fast scroll plus short dwell.",
        confidence: 0.78,
        evidence_event_ids: ["event-render-1"],
        report_ids: ["session-interpretation:render"],
        session_ids: ["replay-render-session"],
        limitation: "Needs user feedback.",
        pattern_key: "skim-risk:retry",
      },
    ],
    open_loops: [],
    limitations: ["Local deterministic guidance only."],
    evidence_event_ids: ["event-render-1"],
    source_report_ids: ["replay:render"],
    provenance: { builder: "test" },
  };
}

function dailyReviewFixture(): DailyReviewReport {
  const suggestion = interpretationFixture().next_actions[0]!;
  return {
    report_id: "daily-review:2026-07-07",
    report_kind: "daily_review",
    local_date: "2026-07-07",
    generated_at: "2026-07-07T22:00:00.000Z",
    summary: "One retry pattern stood out today.",
    sections: {
      helped: [],
      fragmented: [],
      retry: [suggestion],
      ignore: [],
      open_loops: [],
      care_candidates: [],
    },
    suggestions: [suggestion],
    limitations: ["Suggestions are local deterministic summaries."],
    evidence_event_ids: ["event-render-1"],
    source_report_ids: ["session-interpretation:render"],
    provenance: { builder: "test" },
  };
}
