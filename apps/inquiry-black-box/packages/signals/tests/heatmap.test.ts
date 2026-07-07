import { describe, expect, test } from "bun:test";
import { createEvent, type EventEnvelope, type EventType, type JsonObject } from "@inquiry/schema";
import { buildComprehensionHeatmap, buildReplayMemo, segmentStimulus } from "../src";

function event(event_type: EventType, monotonic_ms: number, payload: JsonObject): EventEnvelope {
  return createEvent({
    session_id: "heatmap-session",
    source: event_type.startsWith("camera") ? "desktop-camera" : "browser",
    source_version: "test@0.1.0",
    monotonic_ms,
    event_type,
    payload,
    privacy_class: "local-derived",
    retention_policy: "local-default",
  });
}

describe("comprehension heatmap", () => {
  test("flags dense local stimulus with low friction as intrinsic difficulty", () => {
    const segments = segmentStimulus({
      stimulus_id: "dense-article",
      source: "article",
      duration_ms: 60_000,
      text:
        "Neurophenomenology triangulates first-person report, behavioral residue, and stimulus structure. " +
        "Counterfactual baselines, residualization, and concept-transition density determine whether a claim is explanatory.",
    });

    const heatmap = buildComprehensionHeatmap({
      session_id: "heatmap-session",
      markers: [],
      stimulus_segments: segments,
    });

    expect(heatmap.some((segment) => segment.kind === "intrinsic-difficulty")).toBe(true);
    expect(heatmap[0]?.stimulus_evidence[0]?.segment_id).toStartWith("dense-article:");
    expect(JSON.stringify(heatmap)).not.toContain("Neurophenomenology triangulates");
  });

  test("separates behavioral loss of thread from low-density stimulus", () => {
    const segments = segmentStimulus({
      stimulus_id: "plain-video-note",
      source: "transcript",
      duration_ms: 45_000,
      text: "The speaker names the result. Then they repeat the result. The example stays simple.",
    });
    const memo = buildReplayMemo([
      event("browser.visibility", 10_000, { state: "revisited" }),
      event("browser.visibility", 12_000, { state: "revisited" }),
      event("browser.media", 14_000, { action: "seeked", delta_ms: -12_000 }),
    ], { stimulus_segments: segments });

    const segment = memo.heatmap.find((candidate) => candidate.kind === "behavioral-loss-of-thread");

    expect(segment).toBeDefined();
    expect(segment?.behavior_evidence.map((evidence) => evidence.kind)).toContain("stuck-loop");
    expect(segment?.evidence_event_ids.length).toBeGreaterThan(0);
    expect(segment?.limitation).toContain("behavior");
  });

  test("falls back to behavior-only heatmap when stimulus is missing", () => {
    const memo = buildReplayMemo([
      event("browser.scroll", 1_000, { delta_y: 4200 }),
      event("browser.dwell", 2_000, { dwell_ms: 200 }),
    ]);

    expect(memo.heatmap.some((segment) => segment.kind === "behavior-only")).toBe(true);
    expect(memo.heatmap[0]?.stimulus_evidence).toEqual([]);
    expect(memo.heatmap[0]?.limitation).toContain("No local stimulus");
  });

  test("includes stimulus text only with explicit document opt-in", () => {
    const redacted = segmentStimulus({
      stimulus_id: "redacted-doc",
      source: "manual",
      text: "This sensitive paragraph should stay local and unexported.",
    });
    const optedIn = segmentStimulus({
      stimulus_id: "opt-in-doc",
      source: "manual",
      document_opt_in: true,
      text: "This paragraph was explicitly attached for document-level analysis.",
    });

    expect(redacted[0]?.text).toBeUndefined();
    expect(optedIn[0]?.text).toContain("explicitly attached");
  });
});
