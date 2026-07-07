import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { createCloudHandler } from "../../apps/cloud/src/server";
import { createInquiryDatabase } from "../../apps/desktop/src/main/db";
import { createCameraFeatureEvent, summarizeCameraFeatureWindow } from "../../apps/desktop/src/renderer/camera/featureWorker";
import { createSessionReplayReport } from "../../apps/desktop/src/main/reports/sessionReplay";
import { createEvent, type EventEnvelope } from "../../packages/schema/src";

type FixtureLine = {
  type: "event";
  event: EventEnvelope;
};

describe("local session fixture loop", () => {
  test("ingests fixture events, renders replay evidence, exports safely, and rejects raw cloud payloads", async () => {
    const database = createInquiryDatabase();
    const session = database.createSession({
      title: "Synthetic research session",
      session_id: "fixture-local-session",
    });

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
    const replay = createSessionReplayReport(events);
    const exported = database.exportSessionJsonl(session.session_id);
    const cloud = createCloudHandler();
    const rawCloudResponse = await cloud(
      new Request("http://cloud.test/sync/events", {
        method: "POST",
        headers: {
          authorization: "Bearer fixture-user.test-token",
          "content-type": "application/json",
        },
        body: JSON.stringify({
          device_id: "fixture-device",
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

    expect(events.map((event) => event.event_type)).toContain("camera.feature_window");
    expect(replay.markers.some((marker) => marker.kind === "skim-risk")).toBe(true);
    expect(replay.markers.every((marker) => marker.evidence_event_ids.length > 0)).toBe(true);
    expect(exported).toContain("fixture-scroll-1");
    expect(exported).not.toContain("rawFrame");
    expect(rawCloudResponse.status).toBe(422);
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
