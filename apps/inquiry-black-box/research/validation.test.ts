import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { createValidationReport, parseValidationJsonl } from "./validation";

const fixturePath = join(import.meta.dir, "..", "tests", "fixtures", "research-session.jsonl");

describe("research validation artifacts", () => {
  test("converts the fixture export into validation rows for G0-G4 inputs", () => {
    const events = parseValidationJsonl(readFileSync(fixturePath, "utf8"));
    const report = createValidationReport(events, { run_id: "fixture-smoke" });
    const rowKinds = new Set(report.validation_rows.map((row) => row.kind));

    expect(rowKinds).toEqual(
      new Set(["label", "probe", "repair_outcome", "stimulus_segment", "behavior_marker", "camera_quality_flag"]),
    );
    expect(report.gates.g0.status).toBe("smoke");
    expect(report.gates.g1.status).toBe("smoke");
    expect(report.gates.g1.negative_controls.map((control) => control.control)).toEqual([
      "shuffled-segment-order",
      "shifted-boundaries",
    ]);
    expect(report.gates.g2.status).toBe("insufficient-data");
    expect(report.gates.g3.status).toBe("insufficient-data");
    expect(report.gates.g4.status).toBe("insufficient-data");
  });

  test("stimulus-only baseline and negative controls are deterministic", () => {
    const events = parseValidationJsonl(readFileSync(fixturePath, "utf8"));
    const first = createValidationReport(events, { run_id: "fixture-smoke" });
    const second = createValidationReport(events, { run_id: "fixture-smoke" });

    expect(first.gates.g1).toEqual(second.gates.g1);
    expect(first.gates.g1.baseline.top_segment_id).toBe("demo-article:2");
    expect(first.gates.g1.negative_controls[0]?.top_segment_id).not.toBe(first.gates.g1.baseline.top_segment_id);
  });

  test("time fallback targets only stimulus segments from the same session", () => {
    const events = parseValidationJsonl(
      [
        JSON.stringify({
          event_id: "session-a-segments",
          session_id: "session-a",
          source: "stimulus",
          source_version: "desktop@0.1.0",
          captured_at: "2026-07-07T14:00:00.000Z",
          monotonic_ms: 0,
          timezone: "UTC",
          event_type: "stimulus.segmented",
          confidence: 1,
          quality_flags: [],
          payload: {
            stimulus_id: "article-a",
            segment_count: 1,
            segment_ids: ["article-a:1"],
            content_refs: ["fixture:article-a#1"],
            segments: [
              {
                segment_id: "article-a:1",
                ordinal: 1,
                start_ms: 0,
                end_ms: 10_000,
                density: 0.2,
                term_novelty: 0.2,
                transition_count: 1,
                quiz_checkpoint_candidate: false,
              },
            ],
          },
          privacy_class: "local-derived",
          retention_policy: "local-default",
        }),
        JSON.stringify({
          event_id: "session-b-segments",
          session_id: "session-b",
          source: "stimulus",
          source_version: "desktop@0.1.0",
          captured_at: "2026-07-07T14:00:00.000Z",
          monotonic_ms: 0,
          timezone: "UTC",
          event_type: "stimulus.segmented",
          confidence: 1,
          quality_flags: [],
          payload: {
            stimulus_id: "article-b",
            segment_count: 1,
            segment_ids: ["article-b:1"],
            content_refs: ["fixture:article-b#1"],
            segments: [
              {
                segment_id: "article-b:1",
                ordinal: 1,
                start_ms: 0,
                end_ms: 10_000,
                density: 0.8,
                term_novelty: 0.8,
                transition_count: 3,
                quiz_checkpoint_candidate: true,
              },
            ],
          },
          privacy_class: "local-derived",
          retention_policy: "local-default",
        }),
        JSON.stringify({
          event_id: "session-b-label",
          session_id: "session-b",
          source: "user",
          source_version: "desktop@0.1.0",
          captured_at: "2026-07-07T14:00:05.000Z",
          monotonic_ms: 5_000,
          timezone: "UTC",
          event_type: "label.added",
          confidence: 1,
          quality_flags: [],
          payload: { label: "confused-good" },
          privacy_class: "local-derived",
          retention_policy: "local-default",
        }),
      ].join("\n"),
    );

    const report = createValidationReport(events, { run_id: "multi-session" });
    const label = report.validation_rows.find((row) => row.source_event_id === "session-b-label");

    expect(label?.target_id).toBe("article-b:1");
  });

  test("does not require raw camera frames or raw typed content", () => {
    const events = parseValidationJsonl(readFileSync(fixturePath, "utf8"));
    events.push({
      ...events[0]!,
      event_id: "fixture-sensitive-sentinel",
      event_type: "probe.answered",
      monotonic_ms: 9_000,
      payload: {
        probe_id: "probe-sensitive",
        target_segment_id: "demo-article:2",
        answer_quality: "partial",
        answer: "SECRET typed answer must not enter validation artifacts",
        rawFrame: "SECRET camera frame must not enter validation artifacts",
      },
    });

    const serialized = JSON.stringify(createValidationReport(events, { run_id: "fixture-smoke" }));

    expect(serialized).not.toContain("SECRET typed answer");
    expect(serialized).not.toContain("SECRET camera frame");
  });
});
