import { describe, expect, test } from "bun:test";
import { createEvent } from "@inquiry/schema";
import { createInquiryDatabase } from "../src/main/db";
import { createDesktopIpcFacade } from "../src/main/ipc";
import { createDesktopRuntime } from "../src/main/main";
import { requestRedactedSessionSummary } from "../src/main/cloud/redactedSummary";
import type { DesktopActivityProvider } from "../src/main/activity/desktopActivity";

describe("desktop shell IPC facade", () => {
  test("exposes visible session controls, pairing, replay, export, and delete without filesystem escape hatches", async () => {
    const database = createInquiryDatabase();
    const runtime = createDesktopRuntime({
      database,
      pairingSecret: "desktop-shell-test-secret",
      startServer: false,
    });
    const facade = createDesktopIpcFacade(runtime);

    expect(Object.keys(facade)).not.toContain("readFile");
    expect((await facade.status()).pairingToken.split(".")).toHaveLength(3);

    const started = await facade.startSession({ title: "Shell fixture" });
    expect(started.recording_state).toBe("recording");

    database.appendEvent(
      createEvent({
        session_id: started.session_id,
        source: "browser",
        source_version: "extension@0.1.0",
        monotonic_ms: 1_000,
        event_type: "browser.scroll",
        payload: { url_hash: "url-shell", delta_y: 4_800, scroll_y: 4_800, viewport_h: 900 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );
    database.appendEvent(
      createEvent({
        session_id: started.session_id,
        source: "browser",
        source_version: "extension@0.1.0",
        monotonic_ms: 1_500,
        event_type: "browser.dwell",
        payload: { url_hash: "url-shell", dwell_ms: 200 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );

    expect((await facade.pauseSession()).recording_state).toBe("paused");
    expect((await facade.resumeSession()).recording_state).toBe("recording");
    await facade.addLabel({ label: "near-breakthrough", note: "spotted the key turn" });
    const stopped = await facade.stopSession();
    expect(stopped.recording_state).toBe("stopped");

    const replay = await facade.replayReport();
    expect(replay?.markers.some((marker) => marker.kind === "skim-risk")).toBe(true);
    const repair = replay?.repair_candidates[0];
    expect(repair?.action).toBe("recall-question");
    if (!repair) {
      throw new Error("expected repair candidate");
    }

    const requestedProbe = await facade.acceptRepair(repair.repair_id);
    expect(requestedProbe.event_type).toBe("probe.requested");
    const answerEvents = await facade.answerRepair({
      repair_id: repair.repair_id,
      answer: "The span should answer what claim the fast scroll skipped.",
      confidence: 0.7,
    });
    const dismissed = await facade.dismissRepair({ repair_id: repair.repair_id, reason: "handled in notes" });
    expect(answerEvents.map((event) => event.event_type)).toEqual(["probe.answered", "repair.outcome"]);
    expect(dismissed.event_type).toBe("repair.outcome");
    expect(database.listRepairEvents(started.session_id).map((event) => event.event_type)).toEqual(
      expect.arrayContaining(["repair.candidate", "probe.requested", "probe.answered", "repair.outcome"]),
    );

    const exported = await facade.exportSession();
    expect(exported.jsonl).toContain("Shell fixture");
    expect(exported.jsonl).toContain("near-breakthrough");
    expect(exported.jsonl).toContain("repair.outcome");

    const deleted = await facade.deleteSession();
    expect(deleted.deleted).toBe(true);
    expect(database.getSession(stopped.session_id)).toBeNull();
    expect(database.listSyncQueue()[0]?.payload).toMatchObject({
      action: "delete-cloud-aggregates",
      session_id: stopped.session_id,
    });

    runtime.stop();
  });

  test("stops active desktop activity before deleting the current session", async () => {
    let foregroundCalls = 0;
    const provider: DesktopActivityProvider = {
      permissionStatus: () => "granted",
      foregroundActivity: () => {
        foregroundCalls += 1;
        return {
          app_name: "Cursor",
          bundle_id: "com.todesktop.230313mzl4w4u92",
          permission_status: "granted",
        };
      },
    };
    const database = createInquiryDatabase();
    const runtime = createDesktopRuntime({
      database,
      pairingSecret: "desktop-shell-test-secret",
      startServer: false,
      desktopActivityProvider: provider,
      desktopActivityClock: {
        nowMs: () => 1_000,
        nowIso: () => "1970-01-01T00:00:01.000Z",
      },
      desktopActivityAutoPoll: false,
    });
    const facade = createDesktopIpcFacade(runtime);
    await facade.setSignalEnabled("desktopActivity", true);
    const session = await facade.startSession({ title: "Delete active desktop activity" });

    await runtime.desktopActivity.tick();
    const deleted = await facade.deleteSession();
    await runtime.desktopActivity.tick();

    expect(deleted).toEqual({ session_id: session.session_id, deleted: true });
    expect(database.getSession(session.session_id)).toBeNull();
    expect(foregroundCalls).toBe(1);
    expect((await facade.status()).desktopActivity.active).toBe(false);
    runtime.stop();
  });

  test("keeps privacy settings and camera feature appends behind typed IPC methods", async () => {
    const database = createInquiryDatabase();
    const runtime = createDesktopRuntime({
      database,
      pairingSecret: "desktop-shell-test-secret",
      startServer: false,
    });
    const facade = createDesktopIpcFacade(runtime);
    const session = await facade.startSession({ title: "Camera fixture" });

    const settings = await facade.setSignalEnabled("camera", true);
    expect(settings.signals.camera).toBe(true);
    expect(settings.cloud_sync_enabled).toBe(false);

    const cameraEvent = await facade.appendCameraFeatureWindow({
      window_start_ms: 0,
      window_end_ms: 1_000,
      sample_count: 3,
      confidence: 0.8,
      quality_flags: [],
      payload: {
        window_ms: 1_000,
        face_present_ratio: 1,
        gaze_away_ratio: 0.2,
        blink_proxy: 0,
        head_pose_variance: 0.1,
        motion_score: 0.1,
      },
    });

    expect(cameraEvent.event_type).toBe("camera.feature_window");
    expect(database.listEvents(session.session_id).map((event) => event.event_type)).toContain("camera.feature_window");
    const exported = await facade.exportSession();
    expect(exported.jsonl).toContain("camera.feature_window");
    expect(exported.jsonl).toContain("face_present_ratio");
    expect(exported.jsonl).not.toMatch(/rawFrame|frameImage|imageBlob|frameBlob|pixels|data:image|base64/);

    runtime.stop();
  });

  test("generates interpretation, daily review, feedback, and opted-in notification events", async () => {
    const database = createInquiryDatabase();
    const shown: Array<{ title: string; body: string }> = [];
    const runtime = createDesktopRuntime({
      database,
      pairingSecret: "desktop-shell-test-secret",
      startServer: false,
      notifier: {
        show: async (input) => {
          shown.push(input);
          return "shown";
        },
      },
    });
    const facade = createDesktopIpcFacade(runtime);
    await facade.setSignalEnabled("notifications", true);
    const session = await facade.startSession({ title: "Interpretation fixture" });

    database.appendEvent(
      createEvent({
        session_id: session.session_id,
        source: "browser",
        source_version: "extension@0.1.0",
        monotonic_ms: 1_000,
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
        monotonic_ms: 1_500,
        event_type: "browser.dwell",
        payload: { dwell_ms: 200 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );

    await facade.stopSession();
    const interpretation = await facade.sessionInterpretation();
    const review = await facade.refreshDailyReview();
    const suggestion = review.suggestions[0];
    if (!suggestion) {
      throw new Error("expected a daily suggestion");
    }
    const response = await facade.respondSuggestion({
      suggestion_id: suggestion.suggestion_id,
      response: "accepted",
      local_date: review.local_date,
    });

    expect(interpretation?.summary).toContain("Interpretation fixture");
    expect(review.sections.retry.length + review.sections.fragmented.length + review.sections.open_loops.length).toBeGreaterThan(0);
    expect(response.event_type).toBe("suggestion.responded");
    expect(shown.length).toBe(1);
    expect(database.listEvents(session.session_id).map((event) => event.event_type)).toEqual(
      expect.arrayContaining(["report.generated", "suggestion.candidate", "suggestion.responded", "notification.delivered"]),
    );
    runtime.stop();
  });

  test("submits optional redacted LLM summaries only after cloud sync opt-in", async () => {
    const database = createInquiryDatabase();
    const postedBodies: Record<string, unknown>[] = [];
    const authorizations: string[] = [];
    const runtime = createDesktopRuntime({
      database,
      pairingSecret: "desktop-shell-test-secret",
      startServer: false,
    });
    const facade = createDesktopIpcFacade(runtime, {
      redactedSummary: {
        cloudApiUrl: "https://cloud.example.test",
        bearerToken: "fixture-token",
        provider: "modal",
        nowMs: () => 10_000,
        fetchImpl: async (_url, init) => {
          authorizations.push(new Headers(init?.headers).get("authorization") ?? "");
          postedBodies.push(JSON.parse(String(init?.body ?? "{}")) as Record<string, unknown>);
          return new Response(
            JSON.stringify({
              job: {
                job_id: "job-redacted-1",
                status: "submitted",
                modal_call_id: "modal-call-1",
              },
            }),
            { status: 202 },
          );
        },
      },
    });
    try {
      const session = await facade.startSession({ title: "Redacted summary fixture" });
      appendDesktopActivityFixture(database, session.session_id);
      await facade.stopSession();

      const blocked = await facade.requestRedactedSummary();
      expect(blocked).toMatchObject({ status: "blocked" });
      expect(postedBodies).toHaveLength(0);

      await facade.setSignalEnabled("cloudSync", true);
      const submitted = await facade.requestRedactedSummary();
      expect(submitted).toMatchObject({
        status: "submitted",
        job_id: "job-redacted-1",
        modal_call_id: "modal-call-1",
      });
      expect(authorizations).toEqual(["Bearer fixture-token"]);
      expect(postedBodies).toHaveLength(1);
      expect(postedBodies[0]).toMatchObject({
        kind: "session_summary",
        session_id: session.session_id,
        input: {
          privacy_class: "redacted-sync",
        },
      });
      const serialized = JSON.stringify(postedBodies[0]);
      expect(serialized).not.toContain("Cursor");
      expect(serialized).not.toContain("com.todesktop.230313mzl4w4u92");
      expect(database.listEvents(session.session_id).map((event) => event.event_type)).toContain("model.run");
    } finally {
      runtime.stop();
    }
  });

  test("shows completed cloud redacted LLM summaries when Railway returns provider output", async () => {
    const database = createInquiryDatabase();
    const runtime = createDesktopRuntime({
      database,
      pairingSecret: "desktop-shell-test-secret",
      startServer: false,
    });
    const facade = createDesktopIpcFacade(runtime);
    const session = await facade.startSession({ title: "Cloud completed summary" });
    appendDesktopActivityFixture(database, session.session_id);
    await facade.stopSession();
    database.setSignalEnabled("cloudSync", true);

    const result = await requestRedactedSessionSummary(database, session.session_id, {
      cloudApiUrl: "https://cloud.example.test",
      bearerToken: "fixture-token",
      fetchImpl: async () =>
        new Response(
          JSON.stringify({
            job: {
              job_id: "job-openai-1",
              status: "complete",
              result: {
                report: {
                  payload: {
                    summary_text: "OpenAI says the copied evidence needs one follow-up note.",
                  },
                },
              },
            },
          }),
          { status: 202 },
        ),
    });

    expect(result).toMatchObject({
      status: "complete",
      message: "OpenAI says the copied evidence needs one follow-up note.",
      job_id: "job-openai-1",
    });
    expect(database.listEvents(session.session_id).find((event) => event.event_type === "model.run")?.payload).toMatchObject({
      status: "complete",
    });
    runtime.stop();
  });

  test("records redacted LLM summary unavailability without sending network requests", async () => {
    const database = createInquiryDatabase();
    const runtime = createDesktopRuntime({
      database,
      pairingSecret: "desktop-shell-test-secret",
      startServer: false,
    });
    const facade = createDesktopIpcFacade(runtime);
    const session = await facade.startSession({ title: "Missing cloud config" });
    appendDesktopActivityFixture(database, session.session_id);
    await facade.stopSession();
    database.setSignalEnabled("cloudSync", true);
    let fetchCalls = 0;

    const result = await requestRedactedSessionSummary(database, session.session_id, {
      cloudApiUrl: "",
      bearerToken: "",
      provider: "modal",
      disableDopplerOpenAI: true,
      disableDopplerGemini: true,
      fetchImpl: async () => {
        fetchCalls += 1;
        return new Response("should not be called", { status: 500 });
      },
    });

    expect(result).toMatchObject({
      status: "unavailable",
      message: "Cloud job endpoint/auth token or direct OpenAI/Gemini API key is not configured.",
    });
    expect(fetchCalls).toBe(0);
    expect(database.listEvents(session.session_id).filter((event) => event.event_type === "model.run")).toHaveLength(1);
    runtime.stop();
  });

  test("requests a direct OpenAI redacted summary when cloud job config is absent", async () => {
    const database = createInquiryDatabase();
    const runtime = createDesktopRuntime({
      database,
      pairingSecret: "desktop-shell-test-secret",
      startServer: false,
    });
    const facade = createDesktopIpcFacade(runtime);
    const session = await facade.startSession({ title: "OpenAI redacted summary" });
    appendDesktopActivityFixture(database, session.session_id);
    await facade.stopSession();
    database.setSignalEnabled("cloudSync", true);
    let requestedUrl = "";
    let authorization = "";
    let postedBody = "";

    const result = await requestRedactedSessionSummary(database, session.session_id, {
      cloudApiUrl: "",
      bearerToken: "",
      openAiApiKey: "fixture-openai-key",
      model: "gpt-test-summary",
      nowMs: () => 10_000,
      fetchImpl: async (url, init) => {
        requestedUrl = url;
        authorization = new Headers(init?.headers).get("authorization") ?? "";
        postedBody = String(init?.body ?? "");
        return new Response(JSON.stringify({ output_text: "OpenAI says copied evidence needs one follow-up note." }), {
          status: 200,
        });
      },
    });

    expect(result).toMatchObject({
      status: "complete",
      message: "OpenAI says copied evidence needs one follow-up note.",
    });
    expect(requestedUrl).toBe("https://api.openai.com/v1/responses");
    expect(authorization).toBe("Bearer fixture-openai-key");
    expect(postedBody).toContain("redacted-sync");
    expect(postedBody).toContain("Analyze this Inquiry Black Box session");
    expect(postedBody).toContain("follow-up questions or next actions");
    expect(postedBody).not.toContain("Summarize this Inquiry Black Box session");
    expect(JSON.parse(postedBody)).toMatchObject({ max_output_tokens: 2_000 });
    expect(postedBody).not.toContain("Cursor");
    expect(postedBody).not.toContain("com.todesktop.230313mzl4w4u92");
    expect(database.listEvents(session.session_id).find((event) => event.event_type === "model.run")?.payload).toMatchObject({
      provider: "openai",
      model: "gpt-test-summary",
      status: "complete",
      input_privacy_class: "redacted-sync",
    });
    runtime.stop();
  });

  test("requests a direct Gemini redacted summary when cloud job config is absent", async () => {
    const database = createInquiryDatabase();
    const runtime = createDesktopRuntime({
      database,
      pairingSecret: "desktop-shell-test-secret",
      startServer: false,
    });
    const facade = createDesktopIpcFacade(runtime);
    const session = await facade.startSession({ title: "Gemini redacted summary" });
    appendDesktopActivityFixture(database, session.session_id);
    await facade.stopSession();
    database.setSignalEnabled("cloudSync", true);
    const previousSessionSummaryModel = process.env.SESSION_SUMMARY_MODEL;
    process.env.SESSION_SUMMARY_MODEL = "redacted-session-summary";
    let requestedUrl = "";
    let apiKey = "";
    let postedBody = "";

    try {
      const result = await requestRedactedSessionSummary(database, session.session_id, {
        cloudApiUrl: "",
        bearerToken: "",
        provider: "gemini",
        geminiApiKey: "fixture-gemini-key",
        nowMs: () => 10_000,
        fetchImpl: async (url, init) => {
          requestedUrl = url;
          apiKey = new Headers(init?.headers).get("x-goog-api-key") ?? "";
          postedBody = String(init?.body ?? "");
          return new Response(
            JSON.stringify({
              candidates: [
                {
                  content: {
                    parts: [{ text: "Gemini says copied evidence needs one follow-up note." }],
                  },
                },
              ],
            }),
            { status: 200 },
          );
        },
      });

      expect(result).toMatchObject({
        status: "complete",
        message: "Gemini says copied evidence needs one follow-up note.",
      });
      expect(requestedUrl).toBe("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent");
      expect(apiKey).toBe("fixture-gemini-key");
      expect(postedBody).toContain("redacted-sync");
      expect(postedBody).toContain("Analyze this Inquiry Black Box session");
      expect(postedBody).toContain("follow-up questions or next actions");
      expect(postedBody).not.toContain("Summarize this Inquiry Black Box session");
      expect(JSON.parse(postedBody)).toMatchObject({ generationConfig: { maxOutputTokens: 2_000 } });
      expect(postedBody).not.toContain("Cursor");
      expect(postedBody).not.toContain("com.todesktop.230313mzl4w4u92");
      const modelRun = database.listEvents(session.session_id).find((event) => event.event_type === "model.run");
      expect(modelRun?.payload).toMatchObject({
        provider: "gemini",
        model: "gemini-2.5-flash",
        status: "complete",
        input_privacy_class: "redacted-sync",
      });
    } finally {
      if (previousSessionSummaryModel === undefined) {
        delete process.env.SESSION_SUMMARY_MODEL;
      } else {
        process.env.SESSION_SUMMARY_MODEL = previousSessionSummaryModel;
      }
      runtime.stop();
    }
  });

  test("records redacted LLM summary cloud rejection and timeout failures", async () => {
    const database = createInquiryDatabase();
    const runtime = createDesktopRuntime({
      database,
      pairingSecret: "desktop-shell-test-secret",
      startServer: false,
    });
    const facade = createDesktopIpcFacade(runtime);
    const session = await facade.startSession({ title: "Rejected cloud summary" });
    appendDesktopActivityFixture(database, session.session_id);
    await facade.stopSession();
    database.setSignalEnabled("cloudSync", true);

    const rejected = await requestRedactedSessionSummary(database, session.session_id, {
      cloudApiUrl: "https://cloud.example.test",
      bearerToken: "fixture-token",
      fetchImpl: async () =>
        new Response(JSON.stringify({ error: { message: "privacy rejected" } }), { status: 422 }),
    });
    expect(rejected).toMatchObject({
      status: "failed",
      limitations: expect.arrayContaining(["privacy rejected"]),
    });

    const timedOut = await requestRedactedSessionSummary(database, session.session_id, {
      cloudApiUrl: "https://cloud.example.test",
      bearerToken: "fixture-token",
      timeoutMs: 1,
      fetchImpl: async () => await new Promise<Response>(() => undefined),
    });
    expect(timedOut).toMatchObject({
      status: "failed",
      limitations: expect.arrayContaining(["cloud job request timed out after 1ms"]),
    });
    expect(database.listEvents(session.session_id).filter((event) => event.event_type === "model.run").length).toBeGreaterThanOrEqual(2);
    runtime.stop();
  });
});

function appendDesktopActivityFixture(database: ReturnType<typeof createInquiryDatabase>, sessionId: string): void {
  database.appendEvent(
    createEvent({
      session_id: sessionId,
      source: "desktop-activity",
      source_version: "desktop@0.1.0",
      monotonic_ms: 1_000,
      event_type: "desktop.app_focus",
      payload: {
        app_name: "Cursor",
        bundle_id: "com.todesktop.230313mzl4w4u92",
        focus_started_monotonic_ms: 1_000,
        focus_ended_monotonic_ms: 1_500,
        duration_ms: 500,
        permission_status: "granted",
      },
      privacy_class: "local-derived",
      retention_policy: "local-default",
    }),
  );
}
