import { describe, expect, test } from "bun:test";
import { createEvent } from "@inquiry/schema";
import { createSessionReplayReport } from "../src/main/reports/sessionReplay";
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
    expect(report.heatmap.every((segment) => segment.evidence_event_ids.length > 0 || segment.stimulus_evidence.length > 0)).toBe(
      true,
    );
    expect(JSON.stringify(report)).not.toContain("This easy paragraph repeats");
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
  private ownText = "";
  private children: Array<FakeElement | FakeText> = [];

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
}

class FakeText {
  constructor(readonly textContent: string) {}
}
