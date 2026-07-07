import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { createCloudHandler } from "../../apps/cloud/src/server";
import { createCloudBearerToken } from "../../apps/cloud/src/routes/common";
import { createInquiryDatabase } from "../../apps/desktop/src/main/db";
import { deleteLocalSession } from "../../apps/desktop/src/main/privacy/delete";
import { exportSession } from "../../apps/desktop/src/main/privacy/export";
import { createCameraFeatureEvent, summarizeCameraFeatureWindow } from "../../apps/desktop/src/renderer/camera/featureWorker";
import { createSessionReplayReport } from "../../apps/desktop/src/main/reports/sessionReplay";
import { createEvent, type EventEnvelope } from "../../packages/schema/src";

type FixtureLine = {
  type: "event";
  event: EventEnvelope;
};

describe("local session fixture loop", () => {
  test("runs the demo path from fixture capture through replay, export, and delete", async () => {
    const database = createInquiryDatabase();
    const session = database.createSession({
      title: "Synthetic research session",
      session_id: "fixture-local-session",
      active_task: "Read the local demo article",
    });
    const article = readDemoArticle();
    const stimulusAttached = createEvent({
      event_id: "fixture-stimulus-attached",
      session_id: session.session_id,
      source: "stimulus",
      source_version: "desktop@0.1.0",
      monotonic_ms: 0,
      event_type: "stimulus.attached",
      payload: {
        stimulus_id: "demo-article",
        source: "article",
        content_ref: "fixture:demo-article",
        document_opt_in: false,
        title: "Demo article",
        duration_ms: 120_000,
      },
      privacy_class: "local-derived",
      retention_policy: "local-default",
    });

    database.appendEvent(stimulusAttached);

    for (const line of readFixture()) {
      database.appendEvent(line.event);
    }

    const cameraWindow = summarizeCameraFeatureWindow(
      [
        {
          monotonic_ms: 6000,
          face_present: true,
          gaze_x: 0.1,
          gaze_y: 0.1,
          eye_open_left: 0.8,
          eye_open_right: 0.8,
          head_yaw_deg: 2,
          head_pitch_deg: 1,
          head_roll_deg: 0,
          motion_score: 0.1,
          brightness: 0.8,
          sharpness: 0.9,
        },
        {
          monotonic_ms: 6200,
          face_present: true,
          gaze_x: 0.85,
          gaze_y: 0.1,
          eye_open_left: 0.7,
          eye_open_right: 0.7,
          head_yaw_deg: 6,
          head_pitch_deg: 2,
          head_roll_deg: 1,
          motion_score: 0.2,
          brightness: 0.75,
          sharpness: 0.85,
        },
      ],
      { window_ms: 1000 },
    );
    database.appendEvent(createCameraFeatureEvent({ session_id: session.session_id, featureWindow: cameraWindow }));

    const events = database.listEvents(session.session_id);
    const replay = createSessionReplayReport(events, {
      stimulus_inputs: [
        {
          stimulus_id: "demo-article",
          source: "article",
          content_ref: "fixture:demo-article",
          evidence_event_ids: [stimulusAttached.event_id],
          duration_ms: 120_000,
          text: article,
        },
      ],
    });
    const exported = exportSession(database, session.session_id);
    const exportedLines = exported.jsonl
      .trim()
      .split("\n")
      .map((line) => JSON.parse(line) as { type: string; event?: EventEnvelope });
    const cloud = createCloudHandler();
    const rawCloudResponse = await cloud(
      new Request("http://cloud.test/sync/events", {
        method: "POST",
        headers: {
          authorization: `Bearer ${createCloudBearerToken("fixture-user")}`,
          "content-type": "application/json",
        },
        body: JSON.stringify({
          device_id: "fixture-device",
          token_id: "fixture-token",
          events: [
            {
              event_id: "raw-cloud-event",
              session_id: session.session_id,
              source: "browser",
              source_version: "extension@0.1.0",
              captured_at: "2026-07-07T14:00:07.000Z",
              monotonic_ms: 7000,
              timezone: "UTC",
              event_type: "browser.copy",
              confidence: 1,
              quality_flags: [],
              payload: { rawFrame: "blocked" },
              privacy_class: "redacted-sync",
              retention_policy: "cloud-redacted",
            },
          ],
        }),
      }),
    );
    const deleted = deleteLocalSession(database, session.session_id);
    const tombstone = database.listSyncQueue()[0]?.payload;

    expect(article).toContain("Stimulus Difficulty and Losing the Thread");
    expect(events.map((event) => event.event_type)).toContain("camera.feature_window");
    expect(events.map((event) => event.event_type)).toEqual(
      expect.arrayContaining([
        "browser.scroll",
        "browser.visibility",
        "browser.highlight",
        "browser.copy",
        "browser.media",
        "browser.tab",
        "label.added",
        "probe.requested",
        "probe.answered",
      ]),
    );
    expect(replay.markers.some((marker) => marker.kind === "skim-risk")).toBe(true);
    expect(replay.markers.some((marker) => marker.kind === "copied-passage")).toBe(true);
    expect(replay.markers.some((marker) => marker.kind === "rewind")).toBe(true);
    expect(replay.markers.some((marker) => marker.kind === "label")).toBe(true);
    expect(replay.markers.some((marker) => marker.kind === "probe")).toBe(true);
    expect(replay.markers.some((marker) => marker.kind === "tab-churn")).toBe(true);
    expect(replay.markers.every((marker) => marker.evidence_event_ids.length > 0)).toBe(true);
    expect(replay.heatmap.length).toBeGreaterThan(0);
    expect(replay.heatmap.every((segment) => segment.limitation.length > 0)).toBe(true);
    expect(replay.heatmap.some((segment) => segment.stimulus_evidence.length > 0)).toBe(true);
    expect(replay.heatmap.some((segment) => segment.evidence_event_ids.length > 0)).toBe(true);
    expect(replay.heatmap.some((segment) => segment.evidence_event_ids.includes(stimulusAttached.event_id))).toBe(true);
    expect(exportedLines.some((line) => line.event?.event_id === "fixture-scroll-1")).toBe(true);
    expect(JSON.stringify(replay)).not.toContain("Stimulus Difficulty and Losing the Thread");
    expect(exported.jsonl).not.toContain("rawFrame");
    expect(exported.jsonl).not.toContain("Stimulus Difficulty and Losing the Thread");
    expect(rawCloudResponse.status).toBe(422);
    expect(deleted).toEqual({ session_id: session.session_id, deleted: true });
    expect(database.getSession(session.session_id)).toBeNull();
    expect(database.listEvents(session.session_id)).toEqual([]);
    expect(tombstone).toMatchObject({
      action: "delete-cloud-aggregates",
      session_id: session.session_id,
    });
    database.close();
  });
});

function readFixture(): FixtureLine[] {
  const path = join(import.meta.dir, "..", "fixtures", "research-session.jsonl");
  return readFileSync(path, "utf8")
    .trim()
    .split("\n")
    .map((line) => JSON.parse(line) as FixtureLine);
}

function readDemoArticle(): string {
  return readFileSync(join(import.meta.dir, "..", "fixtures", "demo-article.html"), "utf8");
}
