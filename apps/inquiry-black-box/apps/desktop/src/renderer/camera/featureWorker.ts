import { createEvent, type CameraFeaturePayload, type EventEnvelope } from "@inquiry/schema";

export type CameraFrameSummary = {
  monotonic_ms: number;
  face_present: boolean;
  gaze_x: number;
  gaze_y: number;
  eye_open_left: number;
  eye_open_right: number;
  head_yaw_deg: number;
  head_pitch_deg: number;
  head_roll_deg: number;
  motion_score: number;
  brightness: number;
  sharpness: number;
};

export type CameraFeatureOptions = {
  window_ms: number;
  min_frames?: number;
};

export type CameraFeatureWindow = {
  window_start_ms: number;
  window_end_ms: number;
  sample_count: number;
  confidence: number;
  quality_flags: string[];
  payload: CameraFeaturePayload;
};

const unsafeCameraKeys = new Set(["rawFrame", "frameImage", "imageBlob", "frameBlob", "pixels"]);

export function summarizeCameraFeatureWindow(
  frames: readonly CameraFrameSummary[],
  options: CameraFeatureOptions,
): CameraFeatureWindow {
  if (frames.length === 0) {
    throw new Error("camera feature window requires at least one frame summary");
  }

  for (const frame of frames) {
    assertNoRawCameraData(frame);
    validateFrame(frame);
  }

  const minFrames = options.min_frames ?? 2;
  const faceFrames = frames.filter((frame) => frame.face_present);
  const facePresentRatio = ratio(faceFrames.length, frames.length);
  const gazeAwayRatio = ratio(frames.filter((frame) => frame.face_present && isGazeAway(frame)).length, frames.length);
  const blinkProxy = ratio(frames.filter((frame) => frame.face_present && isBlinkProxy(frame)).length, frames.length);
  const headPoseVariance = clamp01(
    (standardDeviation(frames.map((frame) => frame.head_yaw_deg)) +
      standardDeviation(frames.map((frame) => frame.head_pitch_deg)) +
      standardDeviation(frames.map((frame) => frame.head_roll_deg))) /
      90,
  );
  const motionScore = clamp01(mean(frames.map((frame) => frame.motion_score)));
  const lowLightRatio = ratio(frames.filter((frame) => frame.brightness < 0.3).length, frames.length);
  const blurryRatio = ratio(frames.filter((frame) => frame.sharpness < 0.35).length, frames.length);

  const qualityFlags: string[] = [];
  if (frames.length < minFrames) {
    qualityFlags.push("camera.low-sample-count");
  }
  if (facePresentRatio < 0.6) {
    qualityFlags.push("camera.face-missing");
  }
  if (gazeAwayRatio > 0.4) {
    qualityFlags.push("camera.gaze-away");
  }
  if (blinkProxy > 0.4) {
    qualityFlags.push("camera.blink-likely");
  }
  if (headPoseVariance > 0.25) {
    qualityFlags.push("camera.head-pose-unstable");
  }
  if (motionScore >= 0.55) {
    qualityFlags.push("camera.motion-high");
  }
  if (lowLightRatio > 0.25) {
    qualityFlags.push("camera.low-light");
  }
  if (blurryRatio > 0.25) {
    qualityFlags.push("camera.blurry");
  }

  const windowStartMs = Math.min(...frames.map((frame) => frame.monotonic_ms));
  const confidence = clamp01(facePresentRatio * (1 - lowLightRatio * 0.3) * (1 - blurryRatio * 0.2));

  return {
    window_start_ms: windowStartMs,
    window_end_ms: windowStartMs + options.window_ms,
    sample_count: frames.length,
    confidence,
    quality_flags: qualityFlags,
    payload: {
      window_ms: options.window_ms,
      face_present_ratio: facePresentRatio,
      gaze_away_ratio: gazeAwayRatio,
      blink_proxy: blinkProxy,
      head_pose_variance: headPoseVariance,
      motion_score: motionScore,
    },
  };
}

export function createCameraFeatureEvent(input: {
  session_id: string;
  featureWindow: CameraFeatureWindow;
  monotonic_ms?: number;
}): EventEnvelope<CameraFeaturePayload> {
  return createEvent({
    session_id: input.session_id,
    source: "desktop-camera",
    source_version: "desktop@0.1.0",
    monotonic_ms: input.monotonic_ms ?? input.featureWindow.window_end_ms,
    event_type: "camera.feature_window",
    confidence: input.featureWindow.confidence,
    quality_flags: input.featureWindow.quality_flags,
    payload: input.featureWindow.payload,
    privacy_class: "local-derived",
    retention_policy: "local-default",
  });
}

function isGazeAway(frame: CameraFrameSummary): boolean {
  return Math.abs(frame.gaze_x) > 0.7 || Math.abs(frame.gaze_y) > 0.7;
}

function isBlinkProxy(frame: CameraFrameSummary): boolean {
  return (frame.eye_open_left + frame.eye_open_right) / 2 < 0.2;
}

function validateFrame(frame: CameraFrameSummary): void {
  const numericKeys = [
    "monotonic_ms",
    "gaze_x",
    "gaze_y",
    "eye_open_left",
    "eye_open_right",
    "head_yaw_deg",
    "head_pitch_deg",
    "head_roll_deg",
    "motion_score",
    "brightness",
    "sharpness",
  ] as const;

  if (typeof frame.face_present !== "boolean") {
    throw new Error("camera frame summary face_present must be boolean");
  }

  for (const key of numericKeys) {
    if (typeof frame[key] !== "number" || !Number.isFinite(frame[key])) {
      throw new Error(`camera frame summary ${key} must be a finite number`);
    }
  }
}

function assertNoRawCameraData(value: unknown): void {
  if (Array.isArray(value)) {
    for (const item of value) {
      assertNoRawCameraData(item);
    }
    return;
  }

  if (typeof value !== "object" || value === null) {
    return;
  }

  for (const [key, child] of Object.entries(value)) {
    if (unsafeCameraKeys.has(key)) {
      throw new Error(`camera frame summary contains raw camera frame data: ${key}`);
    }
    assertNoRawCameraData(child);
  }
}

function mean(values: readonly number[]): number {
  if (values.length === 0) {
    return 0;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function standardDeviation(values: readonly number[]): number {
  if (values.length <= 1) {
    return 0;
  }

  const center = mean(values);
  const variance = mean(values.map((value) => (value - center) ** 2));
  return Math.sqrt(variance);
}

function ratio(count: number, total: number): number {
  return total <= 0 ? 0 : count / total;
}

function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value));
}
