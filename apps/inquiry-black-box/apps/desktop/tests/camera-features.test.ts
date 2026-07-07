import { describe, expect, test } from "bun:test";
import { createInquiryDatabase } from "../src/main/db";
import {
  createCameraFeatureEvent,
  summarizeCameraFeatureWindow,
  type CameraFrameSummary,
} from "../src/renderer/camera/featureWorker";

const goodFrame: CameraFrameSummary = {
  monotonic_ms: 0,
  face_present: true,
  gaze_x: 0.05,
  gaze_y: 0.05,
  eye_open_left: 0.9,
  eye_open_right: 0.88,
  head_yaw_deg: 2,
  head_pitch_deg: 1,
  head_roll_deg: 0,
  motion_score: 0.05,
  brightness: 0.8,
  sharpness: 0.85,
};

describe("camera feature worker", () => {
  test("emits face, gaze, blink, head-pose, and motion quality flags from frame summaries", () => {
    const featureWindow = summarizeCameraFeatureWindow(
      [
        { ...goodFrame, monotonic_ms: 0, face_present: false, brightness: 0.2, sharpness: 0.2 },
        {
          ...goodFrame,
          monotonic_ms: 100,
          gaze_x: 0.95,
          eye_open_left: 0.05,
          eye_open_right: 0.05,
          head_yaw_deg: 35,
          motion_score: 0.9,
        },
        {
          ...goodFrame,
          monotonic_ms: 200,
          gaze_y: -0.95,
          eye_open_left: 0.1,
          eye_open_right: 0.1,
          head_pitch_deg: -34,
          motion_score: 0.8,
        },
      ],
      { window_ms: 1_000, min_frames: 3 },
    );

    expect(featureWindow.payload.face_present_ratio).toBeCloseTo(2 / 3);
    expect(featureWindow.payload.gaze_away_ratio).toBeCloseTo(2 / 3);
    expect(featureWindow.payload.blink_proxy).toBeCloseTo(2 / 3);
    expect(featureWindow.quality_flags).toEqual(
      expect.arrayContaining([
        "camera.gaze-away",
        "camera.blink-likely",
        "camera.head-pose-unstable",
        "camera.motion-high",
        "camera.low-light",
        "camera.blurry",
      ]),
    );
  });

  test("persists camera features without image blobs or raw frame fields", () => {
    const featureWindow = summarizeCameraFeatureWindow(
      [
        goodFrame,
        { ...goodFrame, monotonic_ms: 100 },
        { ...goodFrame, monotonic_ms: 200 },
      ],
      { window_ms: 1_000 },
    );
    const event = createCameraFeatureEvent({
      session_id: "session-camera-1",
      featureWindow,
      monotonic_ms: 1_000,
    });
    const database = createInquiryDatabase();
    const session = database.createSession({ title: "Camera", session_id: "session-camera-1" });

    database.appendEvent(event);

    const persisted = database.listEvents(session.session_id)[0];
    expect(persisted?.event_type).toBe("camera.feature_window");
    expect(JSON.stringify(persisted?.payload)).not.toMatch(/rawFrame|frameImage|imageBlob|frameBlob|pixels/);
    expect(() =>
      summarizeCameraFeatureWindow(
        [
          {
            ...goodFrame,
            imageBlob: "base64-image",
          } as unknown as CameraFrameSummary,
        ],
        { window_ms: 1_000 },
      ),
    ).toThrow(/raw camera frame data/);
    database.close();
  });
});
