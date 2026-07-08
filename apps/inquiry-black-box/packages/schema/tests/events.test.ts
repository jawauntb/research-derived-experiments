import { describe, expect, test } from "bun:test";
import {
  canExportSelectedTextPrivacyClass,
  canExportPrivacyClass,
  canQueueDeleteTombstonePrivacyClass,
  canRunModalJobPrivacyClass,
  canSyncPrivacyClass,
  createEvent,
  findSensitiveFieldPaths,
  normalizeSensitiveFieldName,
  privacyClassMatrix,
  privacyClasses,
  validateEvent,
  type BrowserTypingMetricsPayload,
  type CameraFeaturePayload,
  type DesktopAppFocusPayload,
  type DesktopWindowFocusPayload,
  type JsonObject,
  type PrivacyClass,
  type RepairCandidatePayload,
  type RepairOutcomePayload,
  type StimulusAttachedPayload,
} from "../src";

describe("event schema", () => {
  test("creates and validates browser typing metrics without text content", () => {
    const payload: BrowserTypingMetricsPayload = {
      field_role: "search",
      burst_length: 8,
      pause_ms: 420,
      backspace_count: 2,
      edit_churn: 0.25,
    };

    const event = createEvent({
      session_id: "session-1",
      source: "browser",
      source_version: "extension@0.1.0",
      monotonic_ms: 10,
      event_type: "browser.typing_metrics",
      payload,
      privacy_class: "local-derived",
      retention_policy: "local-default",
    });

    expect(event.payload.field_role).toBe("search");
    expect(JSON.stringify(event.payload)).not.toContain("hello");
  });

  test("accepts camera features and rejects image payload fields", () => {
    const payload: CameraFeaturePayload = {
      window_ms: 1000,
      face_present_ratio: 1,
      gaze_away_ratio: 0.2,
      blink_proxy: 0.1,
      head_pose_variance: 0.3,
      motion_score: 0.4,
    };

    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "desktop-camera",
        source_version: "desktop@0.1.0",
        monotonic_ms: 20,
        event_type: "camera.feature_window",
        payload,
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).not.toThrow();

    expect(() =>
      validateEvent({
        event_id: "bad-camera",
        session_id: "session-1",
        source: "desktop-camera",
        source_version: "desktop@0.1.0",
        captured_at: new Date().toISOString(),
        monotonic_ms: 20,
        timezone: "UTC",
        event_type: "camera.feature_window",
        confidence: 1,
        quality_flags: [],
        payload: { rawFrame: "base64" },
        privacy_class: "debug-sensitive",
        retention_policy: "debug-ephemeral",
      }),
    ).toThrow(/blocked sensitive/);
  });

  test("accepts local desktop app focus metadata while keeping it cloud-ineligible", () => {
    const payload: DesktopAppFocusPayload = {
      app_name: "Cursor",
      bundle_id: "com.todesktop.230313mzl4w4u92",
      pid_hash: "pid_a1b2",
      focus_started_monotonic_ms: 1_000,
      focus_ended_monotonic_ms: 8_000,
      duration_ms: 7_000,
      permission_status: "granted",
    };

    const event = createEvent({
      session_id: "session-1",
      source: "desktop-activity",
      source_version: "desktop@0.1.0",
      monotonic_ms: 8_000,
      event_type: "desktop.app_focus",
      payload,
      privacy_class: "local-derived",
      retention_policy: "local-default",
    });

    expect(event.payload.app_name).toBe("Cursor");
    expect(canExportPrivacyClass(event.privacy_class).allowed).toBe(true);
    expect(canSyncPrivacyClass(event.privacy_class).allowed).toBe(false);
    expect(canRunModalJobPrivacyClass(event.privacy_class).allowed).toBe(false);
  });

  test("gates desktop window titles separately from app focus metadata", () => {
    const metadataOnlyPayload: DesktopWindowFocusPayload = {
      app_name: "Terminal",
      bundle_id: "com.apple.Terminal",
      focus_started_monotonic_ms: 2_000,
      focus_ended_monotonic_ms: 4_000,
      duration_ms: 2_000,
      permission_status: "granted",
      window_id_hash: "window_hash_1",
    };

    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "desktop-activity",
        source_version: "desktop@0.1.0",
        monotonic_ms: 4_000,
        event_type: "desktop.window_focus",
        payload: metadataOnlyPayload,
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).not.toThrow();

    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "desktop-activity",
        source_version: "desktop@0.1.0",
        monotonic_ms: 4_000,
        event_type: "desktop.window_focus",
        payload: {
          ...metadataOnlyPayload,
          window_title: "private-notes.md",
        },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).toThrow(/window titles require document-opt-in/);

    const titledEvent = createEvent({
      session_id: "session-1",
      source: "desktop-activity",
      source_version: "desktop@0.1.0",
      monotonic_ms: 4_000,
      event_type: "desktop.window_focus",
      payload: {
        ...metadataOnlyPayload,
        window_title: "private-notes.md",
        title_truncated: false,
      },
      privacy_class: "document-opt-in",
      retention_policy: "session-delete",
    });

    expect(titledEvent.payload.window_title).toBe("private-notes.md");
    expect(canExportPrivacyClass(titledEvent.privacy_class).allowed).toBe(true);
    expect(canSyncPrivacyClass(titledEvent.privacy_class).allowed).toBe(false);
  });

  test("rejects malformed desktop activity payloads", () => {
    const validPayload: DesktopAppFocusPayload = {
      app_name: "Cursor",
      focus_started_monotonic_ms: 1_000,
      focus_ended_monotonic_ms: 2_000,
      duration_ms: 1_000,
      permission_status: "granted",
    };
    const invalidPayloads: Array<{ payload: JsonObject; pattern: RegExp; event_type?: "desktop.app_focus" | "desktop.window_focus" }> = [
      { payload: {}, pattern: /app_name/ },
      { payload: { ...validPayload, permission_status: "maybe" }, pattern: /permission_status/ },
      { payload: { ...validPayload, focus_started_monotonic_ms: "1" }, pattern: /focus_started/ },
      { payload: { ...validPayload, focus_started_monotonic_ms: 2_000, focus_ended_monotonic_ms: 1_000 }, pattern: /at or after/ },
      { payload: { ...validPayload, duration_ms: 999 }, pattern: /duration_ms/ },
      { payload: { ...validPayload, pid_hash: "" }, pattern: /pid_hash/ },
      { payload: { ...validPayload, "window-title": "private.md" }, pattern: /unsupported field: window-title/ },
      { payload: { ...validPayload, screenData: "base64-png" }, pattern: /unsupported field: screenData/ },
      { payload: { ...validPayload, bitmap: "base64-png" }, pattern: /unsupported field: bitmap/ },
      { payload: { ...validPayload, imageData: "base64-png" }, pattern: /unsupported field: imageData/ },
      { payload: { ...validPayload, displayFrame: "base64-png" }, pattern: /unsupported field: displayFrame/ },
      { payload: { ...validPayload, base64Png: "base64-png" }, pattern: /unsupported field: base64Png/ },
      {
        payload: { ...validPayload, window_title: "x".repeat(121) },
        event_type: "desktop.window_focus",
        pattern: /1-120/,
      },
      {
        payload: { ...validPayload, title_truncated: "yes" },
        event_type: "desktop.window_focus",
        pattern: /title_truncated/,
      },
    ];

    for (const item of invalidPayloads) {
      expect(() =>
        createEvent({
          session_id: "session-1",
          source: "desktop-activity",
          source_version: "desktop@0.1.0",
          monotonic_ms: 2_000,
          event_type: item.event_type ?? "desktop.app_focus",
          payload: item.payload,
          privacy_class: "document-opt-in",
          retention_policy: "session-delete",
        }),
      ).toThrow(item.pattern);
    }

    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "desktop-system",
        source_version: "desktop@0.1.0",
        monotonic_ms: 2_000,
        event_type: "desktop.app_focus",
        payload: validPayload,
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).toThrow(/desktop-activity source/);
  });

  test("rejects raw screen image and OCR aliases for desktop activity", () => {
    const blockedPayloads: JsonObject[] = [
      { screenshot: "base64-screen" },
      { nested: { screen_image: "base64-screen" } },
      { nested: { "screen-image": "base64-screen" } },
      { screenRecording: "movie-bytes" },
      { screen_recording: "movie-bytes" },
      { ocr_text: "raw screen words" },
      { OCRText: "raw screen words" },
      { rawScreenText: "visible document body" },
      { "raw-screen-text": "visible document body" },
    ];

    for (const payload of blockedPayloads) {
      expect(() =>
        createEvent({
          session_id: "session-1",
          source: "desktop-activity",
          source_version: "desktop@0.1.0",
          monotonic_ms: 32,
          event_type: "desktop.app_focus",
          payload,
          privacy_class: "blocked-sensitive",
          retention_policy: "debug-ephemeral",
        }),
      ).toThrow(/blocked sensitive/);
    }
  });

  test("makes privacy sync/export/job/delete eligibility explicit", () => {
    expect(canSyncPrivacyClass("redacted-sync").allowed).toBe(true);
    expect(canSyncPrivacyClass("local-derived").allowed).toBe(false);
    expect(canExportPrivacyClass("local-derived").allowed).toBe(true);
    expect(canExportPrivacyClass("debug-sensitive").allowed).toBe(false);
    expect(canExportSelectedTextPrivacyClass("document-opt-in").allowed).toBe(true);
    expect(canExportSelectedTextPrivacyClass("local-derived").allowed).toBe(false);
    expect(canRunModalJobPrivacyClass("redacted-sync").allowed).toBe(true);
    expect(canRunModalJobPrivacyClass("document-opt-in").allowed).toBe(true);
    expect(canRunModalJobPrivacyClass("debug-sensitive").allowed).toBe(false);
    expect(canQueueDeleteTombstonePrivacyClass("redacted-sync").allowed).toBe(true);
    expect(canQueueDeleteTombstonePrivacyClass("document-opt-in").allowed).toBe(false);
  });

  test("publishes the privacy-class matrix for product data paths", () => {
    const expected: Record<
      PrivacyClass,
      {
        defaultExport: boolean;
        selectedTextOptInExport: boolean;
        cloudSync: boolean;
        modalJob: boolean;
        deleteTombstone: boolean;
      }
    > = {
      public: {
        defaultExport: true,
        selectedTextOptInExport: false,
        cloudSync: true,
        modalJob: false,
        deleteTombstone: false,
      },
      "local-derived": {
        defaultExport: true,
        selectedTextOptInExport: false,
        cloudSync: false,
        modalJob: false,
        deleteTombstone: false,
      },
      "redacted-sync": {
        defaultExport: true,
        selectedTextOptInExport: false,
        cloudSync: true,
        modalJob: true,
        deleteTombstone: true,
      },
      "document-opt-in": {
        defaultExport: true,
        selectedTextOptInExport: true,
        cloudSync: false,
        modalJob: true,
        deleteTombstone: false,
      },
      "debug-sensitive": {
        defaultExport: false,
        selectedTextOptInExport: false,
        cloudSync: false,
        modalJob: false,
        deleteTombstone: false,
      },
      "blocked-sensitive": {
        defaultExport: false,
        selectedTextOptInExport: false,
        cloudSync: false,
        modalJob: false,
        deleteTombstone: false,
      },
    };

    expect(Object.keys(privacyClassMatrix).sort()).toEqual([...privacyClasses].sort());
    for (const privacyClass of privacyClasses) {
      expect(privacyClassMatrix[privacyClass]["default-export"].allowed).toBe(expected[privacyClass].defaultExport);
      expect(privacyClassMatrix[privacyClass]["selected-text-opt-in-export"].allowed).toBe(
        expected[privacyClass].selectedTextOptInExport,
      );
      expect(privacyClassMatrix[privacyClass]["cloud-sync"].allowed).toBe(expected[privacyClass].cloudSync);
      expect(privacyClassMatrix[privacyClass]["modal-job"].allowed).toBe(expected[privacyClass].modalJob);
      expect(privacyClassMatrix[privacyClass]["delete-tombstone"].allowed).toBe(expected[privacyClass].deleteTombstone);
    }
  });

  test("rejects raw frame, raw key, typed text, and document text aliases", () => {
    const blockedPayloads: JsonObject[] = [
      { rawFrame: "base64-frame" },
      { nested: { rawKey: "A" } },
      { typedText: "search terms" },
      { page_text: "visible article body" },
    ];

    for (const payload of blockedPayloads) {
      expect(() =>
        createEvent({
          session_id: "session-1",
          source: "browser",
          source_version: "extension@0.1.0",
          monotonic_ms: 32,
          event_type: "browser.typing_metrics",
          payload,
          privacy_class: "redacted-sync",
          retention_policy: "cloud-redacted",
        }),
      ).toThrow(/blocked sensitive/);
    }
  });

  test("finds sensitive fields with route-specific normalized aliases", () => {
    const paths = findSensitiveFieldPaths(
      {
        safe: 1,
        selectedText: "selected claim",
        nested: [{ copied_text: "copied claim" }, { content: "raw article body" }],
      },
      {
        extraFieldNames: ["selected_text", "copied_text", "content"],
        normalizeFieldName: normalizeSensitiveFieldName,
      },
    );

    expect(paths).toEqual(["$.selectedText", "$.nested[0].copied_text", "$.nested[1].content"]);
  });

  test("allows stimulus references but requires document opt-in for raw text", () => {
    const payload: StimulusAttachedPayload = {
      stimulus_id: "article-1",
      source: "article",
      content_ref: "article:article-1:abc123#1",
      document_opt_in: false,
      title: "Demo article",
    };

    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "stimulus",
        source_version: "desktop@0.1.0",
        monotonic_ms: 30,
        event_type: "stimulus.attached",
        payload,
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).not.toThrow();

    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "stimulus",
        source_version: "desktop@0.1.0",
        monotonic_ms: 31,
        event_type: "stimulus.attached",
        payload: { ...payload, text: "raw article body" },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).toThrow(/document-opt-in/);
  });

  test("requires document opt-in for raw browser selected text", () => {
    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "browser",
        source_version: "extension@0.1.0",
        monotonic_ms: 35,
        event_type: "browser.copy",
        payload: {
          hostname_hash: "h_demo",
          url_hash: "h_page",
          selection_length: 13,
          selected_text: "copied claim",
        },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).toThrow(/document-opt-in/);

    const event = createEvent({
      session_id: "session-1",
      source: "browser",
      source_version: "extension@0.1.0",
      monotonic_ms: 36,
      event_type: "browser.copy",
      payload: {
        hostname_hash: "h_demo",
        url_hash: "h_page",
        selection_length: 13,
        selected_text: "copied claim",
      },
      privacy_class: "document-opt-in",
      retention_policy: "session-delete",
    });

    expect(event.privacy_class).toBe("document-opt-in");
    expect(canExportPrivacyClass(event.privacy_class).allowed).toBe(true);
    expect(canSyncPrivacyClass(event.privacy_class).allowed).toBe(false);

    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "browser",
        source_version: "extension@0.1.0",
        monotonic_ms: 37,
        event_type: "browser.selection",
        payload: {
          hostname_hash: "h_demo",
          url_hash: "h_page",
          selection_length: 13,
          selectedText: "selected claim",
        },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).toThrow(/document-opt-in/);
  });

  test("accepts local repair candidate and outcome events", () => {
    const candidatePayload: RepairCandidatePayload = {
      repair_id: "repair-1",
      heatmap_id: "heatmap-1",
      action: "missing-prerequisite",
      prompt: "What prerequisite was missing?",
      start_ms: 1000,
      end_ms: 2000,
      source_kind: "behavioral-loss-of-thread",
      source_marker_ids: ["marker-1"],
      evidence_event_ids: ["event-1"],
      limitation: "repair hypothesis",
    };
    const outcomePayload: RepairOutcomePayload = {
      repair_id: "repair-1",
      heatmap_id: "heatmap-1",
      action: "missing-prerequisite",
      outcome: "dismissed",
      reason: "already answered",
    };

    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "desktop-system",
        source_version: "desktop@0.1.0",
        monotonic_ms: 40,
        event_type: "repair.candidate",
        payload: candidatePayload,
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).not.toThrow();
    expect(() =>
      createEvent({
        session_id: "session-1",
        source: "user",
        source_version: "desktop@0.1.0",
        monotonic_ms: 41,
        event_type: "repair.outcome",
        payload: outcomePayload,
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    ).not.toThrow();
  });
});
