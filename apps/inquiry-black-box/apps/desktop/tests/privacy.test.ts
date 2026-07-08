import { describe, expect, test } from "bun:test";
import { createEvent } from "@inquiry/schema";
import { createInquiryDatabase } from "../src/main/db";
import { deleteLocalSession } from "../src/main/privacy/delete";
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
    deleteLocalSession(database, session.session_id);

    expect(exported.jsonl).toContain("camera.feature_window");
    expect(exported.jsonl).not.toContain("debug-only");
    expect(database.getSession(session.session_id)).toBeNull();
    expect(database.listEvents(session.session_id)).toEqual([]);
    expect(database.listSyncQueue()).toHaveLength(1);
    const tombstone = database.listSyncQueue()[0]?.payload;
    expect(tombstone).toMatchObject({
      action: "delete-cloud-aggregates",
      session_id: session.session_id,
      privacy_class: "redacted-sync",
      retention_policy: "cloud-redacted",
    });
    expect(JSON.stringify(tombstone)).not.toContain("Privacy session");
    expect(JSON.stringify(tombstone)).not.toContain("camera.feature_window");
    database.close();
  });

  test("exports selected text only when the event is document-opt-in", () => {
    const database = createInquiryDatabase();
    const session = database.createSession({ title: "Selected text session", session_id: "session-privacy-2" });
    database.appendEvent(
      createEvent({
        event_id: "copy-derived",
        session_id: session.session_id,
        source: "browser",
        source_version: "extension@0.1.0",
        monotonic_ms: 10,
        event_type: "browser.copy",
        payload: {
          hostname_hash: "h_demo",
          url_hash: "h_page",
          selection_length: 21,
          selection_hash: "h_unopted_claim",
        },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );
    database.appendEvent(
      createEvent({
        event_id: "copy-document-opt-in",
        session_id: session.session_id,
        source: "browser",
        source_version: "extension@0.1.0",
        monotonic_ms: 11,
        event_type: "browser.copy",
        payload: {
          hostname_hash: "h_demo",
          url_hash: "h_page",
          selection_length: 18,
          selected_text: "opted excerpt",
        },
        privacy_class: "document-opt-in",
        retention_policy: "session-delete",
      }),
    );

    const exported = exportSession(database, session.session_id);
    const parsed = exported.jsonl
      .trim()
      .split("\n")
      .map((line) => JSON.parse(line) as { type: string; event?: { event_id: string; payload: Record<string, unknown> } });
    const exportedEvents = parsed.filter((line) => line.type === "event").map((line) => line.event);

    expect(exported.jsonl).toContain("selection_hash");
    expect(exported.jsonl).toContain("opted excerpt");
    expect(exportedEvents).toEqual([
      expect.objectContaining({
        event_id: "copy-derived",
        payload: expect.not.objectContaining({ selected_text: expect.any(String) }),
      }),
      expect.objectContaining({
        event_id: "copy-document-opt-in",
        payload: expect.objectContaining({ selected_text: "opted excerpt" }),
      }),
    ]);
    database.close();
  });
});
