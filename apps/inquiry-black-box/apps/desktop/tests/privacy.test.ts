import { describe, expect, test } from "bun:test";
import { createEvent } from "@inquiry/schema";
import { createInquiryDatabase } from "../src/main/db";
import { deleteLocalSession } from "../src/main/privacy/delete";
import { exportSession } from "../src/main/privacy/export";
import { createSessionInterpretationReport } from "../src/main/reports/sessionInterpretation";
import {
  defaultPrivacySettingsView,
  desktopActivityPrivacyStatus,
  privacySignalRows,
  updateSignalSetting,
} from "../src/renderer/settings/PrivacySettings";

describe("privacy controls", () => {
  test("privacy settings update per-signal toggles without enabling cloud by accident", () => {
    const view = defaultPrivacySettingsView({
      browser: true,
      camera: false,
      desktopActivity: false,
      desktopWindowTitles: false,
      screenSnapshots: false,
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

  test("desktop privacy settings default to metadata off with screen snapshots deferred", () => {
    const view = defaultPrivacySettingsView({
      browser: true,
      camera: false,
      desktopActivity: false,
      desktopWindowTitles: false,
      screenSnapshots: false,
      typingMetrics: true,
      notifications: false,
      cloudSync: false,
    });
    const rows = privacySignalRows(view);

    expect(rows.find((row) => row.key === "desktopActivity")).toMatchObject({
      checked: false,
      disabled: false,
      status: "Off",
    });
    expect(rows.find((row) => row.key === "desktopWindowTitles")).toMatchObject({
      checked: false,
      disabled: true,
      status: "Needs app context",
    });
    expect(rows.find((row) => row.key === "screenSnapshots")).toMatchObject({
      checked: false,
      disabled: true,
      status: "Deferred",
    });
    expect(desktopActivityPrivacyStatus(view)).toMatchObject({
      label: "Desktop activity off",
      tone: "muted",
    });
  });

  test("desktop app context does not enable window titles or screen snapshots by accident", () => {
    const view = defaultPrivacySettingsView({
      browser: true,
      camera: false,
      desktopActivity: false,
      desktopWindowTitles: false,
      screenSnapshots: false,
      typingMetrics: true,
      notifications: false,
      cloudSync: false,
    });

    const desktopEnabled = updateSignalSetting(view, "desktopActivity", true);
    const titleEnabled = updateSignalSetting(desktopEnabled, "desktopWindowTitles", true);
    const snapshotsStillDeferred = updateSignalSetting(titleEnabled, "screenSnapshots", true);
    const desktopDisabled = updateSignalSetting(snapshotsStillDeferred, "desktopActivity", false);

    expect(desktopEnabled.signals.desktopActivity).toBe(true);
    expect(desktopEnabled.signals.desktopWindowTitles).toBe(false);
    expect(titleEnabled.signals.desktopWindowTitles).toBe(true);
    expect(snapshotsStillDeferred.signals.screenSnapshots).toBe(false);
    expect(desktopDisabled.signals.desktopActivity).toBe(false);
    expect(desktopDisabled.signals.desktopWindowTitles).toBe(false);
  });

  test("desktop permission status surfaces blocked and active collector states", () => {
    const blocked = defaultPrivacySettingsView({
      browser: true,
      camera: false,
      desktopActivity: true,
      desktopWindowTitles: false,
      screenSnapshots: false,
      typingMetrics: true,
      notifications: false,
      cloudSync: false,
    });
    blocked.desktop_activity = {
      enabled: true,
      includeWindowTitles: false,
      active: false,
      permission_status: "denied",
    };

    const active = {
      ...blocked,
      desktop_activity: {
        enabled: true,
        includeWindowTitles: false,
        active: true,
        permission_status: "granted" as const,
        last_heartbeat_monotonic_ms: 2_500,
        last_app_name: "Cursor",
      },
    };

    expect(desktopActivityPrivacyStatus(blocked)).toMatchObject({
      label: "Permission blocked",
      tone: "blocked",
    });
    expect(desktopActivityPrivacyStatus(active)).toMatchObject({
      label: "Desktop activity active",
      tone: "good",
    });
    expect(desktopActivityPrivacyStatus(active).detail).toContain("Cursor");
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
        event_type: "sync.queued",
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

  test("exports and deletes desktop activity metadata without making it cloud eligible", () => {
    const database = createInquiryDatabase();
    const session = database.createSession({ title: "Desktop activity session", session_id: "session-privacy-3" });
    database.appendEvent(
      createEvent({
        event_id: "desktop-app-focus-1",
        session_id: session.session_id,
        source: "desktop-activity",
        source_version: "desktop@0.1.0",
        monotonic_ms: 10,
        event_type: "desktop.app_focus",
        payload: {
          app_name: "Cursor",
          bundle_id: "com.todesktop.230313mzl4w4u92",
          pid_hash: "pid_hash_1",
          focus_started_monotonic_ms: 1_000,
          focus_ended_monotonic_ms: 3_000,
          duration_ms: 2_000,
          permission_status: "granted",
        },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );
    database.appendEvent(
      createEvent({
        event_id: "desktop-window-focus-1",
        session_id: session.session_id,
        source: "desktop-activity",
        source_version: "desktop@0.1.0",
        monotonic_ms: 11,
        event_type: "desktop.window_focus",
        payload: {
          app_name: "Cursor",
          bundle_id: "com.todesktop.230313mzl4w4u92",
          window_id_hash: "window_hash_1",
          focus_started_monotonic_ms: 3_000,
          focus_ended_monotonic_ms: 4_000,
          duration_ms: 1_000,
          permission_status: "granted",
        },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );

    const exported = exportSession(database, session.session_id);
    deleteLocalSession(database, session.session_id);

    expect(exported.jsonl).toContain("desktop.app_focus");
    expect(exported.jsonl).toContain("desktop.window_focus");
    expect(exported.jsonl).toContain("com.todesktop.230313mzl4w4u92");
    expect(exported.jsonl).not.toContain("screenshot");
    expect(database.getSession(session.session_id)).toBeNull();
    expect(database.listEvents(session.session_id)).toEqual([]);
    expect(database.listSyncQueue()).toHaveLength(1);
    expect(database.listSyncQueue()[0]?.payload).toMatchObject({
      action: "delete-cloud-aggregates",
      session_id: session.session_id,
      privacy_class: "redacted-sync",
    });
    database.close();
  });

  test("exports and deletes local interpretation artifacts with the session", () => {
    const database = createInquiryDatabase();
    const session = database.createSession({ title: "Artifact privacy", session_id: "session-privacy-artifacts" });
    database.appendEvent(
      createEvent({
        session_id: session.session_id,
        source: "browser",
        source_version: "extension@0.1.0",
        monotonic_ms: 10,
        event_type: "browser.scroll",
        payload: { delta_y: 4_800, scroll_y: 4_800, viewport_h: 900 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );
    database.appendEvent(
      createEvent({
        session_id: session.session_id,
        source: "browser",
        source_version: "extension@0.1.0",
        monotonic_ms: 11,
        event_type: "browser.dwell",
        payload: { dwell_ms: 200 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );
    createSessionInterpretationReport(database, session.session_id);

    const exported = exportSession(database, session.session_id);
    deleteLocalSession(database, session.session_id);

    expect(exported.jsonl).toContain("session_interpretation");
    expect(exported.jsonl).toContain("suggestion.candidate");
    expect(database.getSession(session.session_id)).toBeNull();
    expect(database.listEvents(session.session_id)).toEqual([]);
    database.close();
  });
});
