import { describe, expect, test } from "bun:test";
import {
  buildRepairCandidates,
  createRepairCandidateEvent,
  createRepairOutcomeEvent,
  createRepairProbeEvent,
  type ComprehensionHeatmapSegment,
} from "../src";

function heatmapSegment(
  kind: ComprehensionHeatmapSegment["kind"],
  behaviorKind: string,
  confidence = 0.82,
): ComprehensionHeatmapSegment {
  return {
    heatmap_id: `heatmap-${kind}-${behaviorKind}`,
    session_id: "repair-session",
    kind,
    start_ms: 10_000,
    end_ms: 20_000,
    confidence,
    stimulus_evidence: [
      {
        segment_id: "stimulus:1",
        stimulus_id: "stimulus",
        content_ref: "fixture:stimulus#1",
        density: 0.2,
        term_novelty: 0.1,
        transition_count: 0,
        quiz_checkpoint_candidate: false,
        evidence_event_ids: ["stimulus-attached"],
        evidence: ["density 0.20"],
      },
    ],
    behavior_evidence:
      behaviorKind === "none"
        ? []
        : [
            {
              marker_id: `${behaviorKind}:event-1`,
              kind: behaviorKind as ComprehensionHeatmapSegment["behavior_evidence"][number]["kind"],
              confidence,
              evidence_event_ids: [`${behaviorKind}-event`],
              evidence: [`${behaviorKind} evidence`],
            },
          ],
    evidence_event_ids: behaviorKind === "none" ? ["stimulus-attached"] : ["stimulus-attached", `${behaviorKind}-event`],
    limitation: "fixture limitation",
    suggested_repair: "fixture repair",
  };
}

describe("repair candidates", () => {
  test("stuck-loop segments generate prerequisite questions", () => {
    const [candidate] = buildRepairCandidates([heatmapSegment("behavioral-loss-of-thread", "stuck-loop")]);

    expect(candidate?.action).toBe("missing-prerequisite");
    expect(candidate?.prompt).toContain("prerequisite");
    expect(candidate?.source_marker_ids).toContain("stuck-loop:event-1");
  });

  test("skim-risk segments generate recall prompts", () => {
    const [candidate] = buildRepairCandidates([heatmapSegment("behavior-only", "skim-risk")]);

    expect(candidate?.action).toBe("recall-question");
    expect(candidate?.prompt).toContain("recall question");
  });

  test("copied-passage segments ask why the passage mattered", () => {
    const [candidate] = buildRepairCandidates([heatmapSegment("behavior-only", "copied-passage")]);

    expect(candidate?.action).toBe("explain-copied-passage");
    expect(candidate?.prompt).toContain("Why did this copied passage matter");
  });

  test("low confidence segments without evidence do not emit candidates", () => {
    const segment = {
      ...heatmapSegment("behavior-only", "none", 0.2),
      stimulus_evidence: [],
      evidence_event_ids: [],
    };

    expect(buildRepairCandidates([segment])).toEqual([]);
  });

  test("candidate, accepted probe, and dismissed outcome events are local-derived", () => {
    const [candidate] = buildRepairCandidates([heatmapSegment("mixed-load", "rewind")]);
    expect(candidate).toBeDefined();
    if (!candidate) {
      throw new Error("expected repair candidate");
    }

    const candidateEvent = createRepairCandidateEvent(candidate);
    const probeEvent = createRepairProbeEvent(candidate, { probe_id: "probe-1" });
    const outcomeEvent = createRepairOutcomeEvent({ candidate, outcome: "dismissed", reason: "already understood" });

    expect(candidateEvent.event_type).toBe("repair.candidate");
    expect(probeEvent.event_type).toBe("probe.requested");
    expect(outcomeEvent.event_type).toBe("repair.outcome");
    expect(candidateEvent.payload.evidence_event_ids).toContain("rewind-event");
    expect(probeEvent.payload.repair_id).toBe(candidate.repair_id);
    expect(outcomeEvent.payload.outcome).toBe("dismissed");
    expect(outcomeEvent.privacy_class).toBe("local-derived");
  });
});
