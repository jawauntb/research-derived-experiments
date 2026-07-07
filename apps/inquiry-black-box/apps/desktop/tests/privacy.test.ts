import { describe, expect, test } from "bun:test";
import { createEvent } from "@inquiry/schema";
import { createInquiryDatabase } from "../src/main/db";
import { queueCloudDeletion, deleteLocalSession } from "../src/main/privacy/delete";
import { exportSession } from "../src/main/privacy/export";
import { defaultPrivacySettingsView, updateSignalSetting } from "../src/renderer/settings/PrivacySettings";

describe("privacy controls", () => {
  test("privacy settings update per-signal toggles without enabling cloud by accident", () => {
    const view = defaultPrivacySettingsView({
      browser: true,
      camera: false,
      typingMetrics: true,
      notifications: false,
      cloudSync: false,
    });

    const cameraEnabled = updateSignalSetting(view, "camera", true);
    const cloudStillDisabled = updateSignalSetting(cameraEnabled, "notifications", true);

    expect(cameraEnabled.signals.camera).toBe(true);
    expect(cloudStillDisabled.signals.cloudSync).toBe(false);
    expect(cloudStillDisabled.cloud_sync_enabled).toBe(false);
  });

  test("export excludes debug-sensitive payloads and local delete preserves cloud deletion request", () => {
    const database = createInquiryDatabase();
    const session = database.createSession({ title: "Privacy session", session_id: "session-privacy-1" });
    database.appendEvent(
      createEvent({
        session_id: session.session_id,
        source: "desktop-camera",
        source_version: "desktop@0.1.0",
        monotonic_ms: 10,
        event_type: "camera.feature_window",
        payload: { window_ms: 1000, face_present_ratio: 1, gaze_away_ratio: 0, blink_proxy: 0, head_pose_variance: 0, motion_score: 0 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );
    database.appendEvent(
      createEvent({
        session_id: session.session_id,
        source: "desktop-system",
        source_version: "desktop@0.1.0",
        monotonic_ms: 11,
        event_type: "report.generated",
        payload: { debug_note: "debug-only" },
        privacy_class: "debug-sensitive",
        retention_policy: "debug-ephemeral",
      }),
    );

    const exported = exportSession(database, session.session_id);
    queueCloudDeletion(database, session.session_id);
    deleteLocalSession(database, session.session_id);

    expect(exported.jsonl).toContain("camera.feature_window");
    expect(exported.jsonl).not.toContain("debug-only");
    expect(database.getSession(session.session_id)).toBeNull();
    expect(database.listSyncQueue()).toHaveLength(1);
    expect(database.listSyncQueue()[0]?.payload).toMatchObject({
      action: "delete-cloud-aggregates",
      session_id: session.session_id,
    });
    database.close();
  });
});
