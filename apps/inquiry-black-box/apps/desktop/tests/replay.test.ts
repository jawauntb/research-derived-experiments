import { describe, expect, test } from "bun:test";
import { createEvent } from "@inquiry/schema";
import type { RepairCandidate } from "@inquiry/signals";
import { createSessionReplayReport } from "../src/main/reports/sessionReplay";
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

      expect(root.textContent).toContain("Comprehension Heatmap");
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
