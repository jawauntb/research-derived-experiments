import { describe, expect, test } from "bun:test";
import { createEvent, type EventEnvelope } from "@inquiry/schema";
import { createCloudStore, createCloudStoreFromEnv, type CloudStore } from "../src/db/schema";
import { createCloudBearerToken } from "../src/routes/common";
import { createCloudHandler } from "../src/server";
import type { ModalClient } from "../src/lib/modalClient";
import type { SummaryClient } from "../src/lib/summaryClient";

const authHeaders = (userId = "user-a") => ({
  authorization: `Bearer ${createCloudBearerToken(userId)}`,
  "content-type": "application/json",
});

function redactedEvent(eventId: string): EventEnvelope {
  return createEvent({
    event_id: eventId,
    session_id: "session-cloud-1",
    source: "browser",
    source_version: "extension@0.1.0",
    captured_at: "2026-07-07T12:00:00.000Z",
    monotonic_ms: 120,
    timezone: "UTC",
    event_type: "browser.typing_metrics",
    confidence: 0.9,
    quality_flags: [],
    payload: {
      field_role: "search",
      burst_length: 5,
      pause_ms: 320,
      backspace_count: 1,
      edit_churn: 0.2,
    },
    privacy_class: "redacted-sync",
    retention_policy: "cloud-redacted",
  });
}

function redactedSessionSummaryJobInput() {
  return {
    privacy_class: "redacted-sync",
    payload: {
      report_id: "session-interpretation:session-cloud-1",
      report_kind: "session_interpretation",
      subject_session_id: "session-cloud-1",
      marker_count: 2,
      theme_count: 1,
      open_loop_count: 1,
      next_action_count: 1,
      summary: "Redacted local session summary with 1 theme, 1 open loop, and 1 next action.",
      themes: [
        {
          kind: "stuck-loop",
          title: "Repeated repair loop",
          confidence: 0.82,
          marker_count: 2,
          evidence_count: 2,
        },
      ],
      next_actions: [
        {
          suggestion_kind: "refocus",
          category: "retry",
          title: "Write the missing prerequisite",
          confidence: 0.78,
          evidence_count: 2,
        },
      ],
      limitations: ["No raw text, screenshots, app names, or window titles included."],
      provenance: {
        input_report_id: "session-interpretation:session-cloud-1",
        builder: "test-redacted-session-summary-input@0.1.0",
        excludes: ["raw typed text", "raw selected text", "raw page text", "app names", "window titles"],
      },
    },
  };
}

async function json(response: Response) {
  return response.json() as Promise<Record<string, unknown>>;
}

describe("cloud sync route", () => {
  test("accepts redacted events idempotently by event_id", async () => {
    const store = createCloudStore();
    const handler = createCloudHandler({ store });
    const body = JSON.stringify({ device_id: "device-1", token_id: "token-1", events: [redactedEvent("event-1")] });

    const first = await handler(
      new Request("http://cloud.test/sync/events", {
        method: "POST",
        headers: authHeaders(),
        body,
      }),
    );
    const duplicate = await handler(
      new Request("http://cloud.test/sync/events", {
        method: "POST",
        headers: authHeaders(),
        body,
      }),
    );

    expect(first.status).toBe(202);
    expect(await json(first)).toMatchObject({ accepted: 1, duplicates: 0 });
    expect(duplicate.status).toBe(202);
    expect(await json(duplicate)).toMatchObject({ accepted: 0, duplicates: 1 });
    expect(await store.listEvents("user-a")).toHaveLength(1);
  });

  test("rejects privacy-ineligible sync classes", async () => {
    const handler = createCloudHandler({ store: createCloudStore() });
    const documentOptIn = createEvent({
      event_id: "event-document-opt-in",
      session_id: "session-cloud-1",
      source: "browser",
      source_version: "extension@0.1.0",
      captured_at: "2026-07-07T12:00:00.000Z",
      monotonic_ms: 121,
      timezone: "UTC",
      event_type: "browser.copy",
      confidence: 0.9,
      quality_flags: [],
      payload: {
        hostname_hash: "h_demo",
        url_hash: "h_page",
        selection_length: 12,
        selected_text: "copied claim",
      },
      privacy_class: "document-opt-in",
      retention_policy: "session-delete",
    });
    const events = [
      { ...redactedEvent("event-local"), privacy_class: "local-derived", retention_policy: "local-default" },
      documentOptIn,
      { ...redactedEvent("event-debug"), privacy_class: "debug-sensitive", retention_policy: "debug-ephemeral" },
      { ...redactedEvent("event-blocked"), privacy_class: "blocked-sensitive", retention_policy: "session-delete" },
    ];

    for (const event of events) {
      const response = await handler(
        new Request("http://cloud.test/sync/events", {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ device_id: "device-1", token_id: "token-1", events: [event] }),
        }),
      );
      const body = await json(response);

      expect(response.status).toBe(422);
      expect(body.error).toMatchObject({ code: "events_rejected" });
    }
  });

  test("rejects raw frame, raw key, typed text, selected text, and document text sync payloads", async () => {
    const handler = createCloudHandler({ store: createCloudStore() });
    const events: EventEnvelope[] = [
      { ...redactedEvent("event-raw-frame"), payload: { rawFrame: "base64-frame" } },
      { ...redactedEvent("event-raw-key"), payload: { nested: { rawKey: "A" } } },
      { ...redactedEvent("event-typed-text"), payload: { typedText: "typed search" } },
      { ...redactedEvent("event-generic-text"), event_type: "model.run", payload: { text: "raw model text" } },
      { ...redactedEvent("event-content"), event_type: "model.run", payload: { content: "raw article body" } },
      { ...redactedEvent("event-html"), event_type: "model.run", payload: { html: "<p>raw</p>" } },
      { ...redactedEvent("event-excerpt"), event_type: "model.run", payload: { excerpt: "raw excerpt" } },
      { ...redactedEvent("event-selected-text-camel"), event_type: "model.run", payload: { selectedText: "copied text" } },
      {
        ...redactedEvent("event-selected-text"),
        event_type: "browser.copy",
        payload: {
          hostname_hash: "h_demo",
          url_hash: "h_page",
          selection_length: 11,
          selected_text: "copied text",
        },
      },
      { ...redactedEvent("event-document-text"), payload: { page_text: "article text" } },
      { ...redactedEvent("event-document-text-camel"), payload: { documentText: "article text" } },
    ];

    for (const event of events) {
      const response = await handler(
        new Request("http://cloud.test/sync/events", {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ device_id: "device-1", token_id: "token-1", events: [event] }),
        }),
      );
      const body = await json(response);

      expect(response.status).toBe(422);
      expect(body.error).toMatchObject({ code: "events_rejected" });
    }
  });

  test("does not store rejected events and rejects revoked device tokens", async () => {
    const store = createCloudStore();
    const handler = createCloudHandler({ store });

    const rejected = await handler(
      new Request("http://cloud.test/sync/events", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          device_id: "device-1",
          token_id: "token-1",
          events: [{ ...redactedEvent("event-sensitive-nested"), payload: { nested: { keyContent: "secret" } } }],
        }),
      }),
    );
    expect(rejected.status).toBe(422);
    expect(await store.listEvents("user-a")).toHaveLength(0);

    await handler(
      new Request("http://cloud.test/sync/device/revoke", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ device_id: "device-1", token_id: "token-1", reason: "user-disabled-sync" }),
      }),
    );
    const revoked = await handler(
      new Request("http://cloud.test/sync/events", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ device_id: "device-1", token_id: "token-1", events: [redactedEvent("event-after-revoke")] }),
      }),
    );

    expect(revoked.status).toBe(403);
    expect(await json(revoked)).toMatchObject({ error: { code: "device_revoked" } });
  });

  test("records device token revocation shape", async () => {
    const store = createCloudStore();
    const handler = createCloudHandler({ store });

    const response = await handler(
      new Request("http://cloud.test/sync/device/revoke", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ device_id: "device-1", token_id: "token-1", reason: "user-disabled-sync" }),
      }),
    );
    const body = await json(response);

    expect(response.status).toBe(200);
    expect(body).toMatchObject({ device_id: "device-1", token_id: "token-1", status: "revoked" });
    expect((await store.getDeviceToken("user-a", "device-1", "token-1"))?.status).toBe("revoked");
  });
});

describe("cloud reports and jobs routes", () => {
  test("returns only reports for the authenticated user", async () => {
    const store = createCloudStore();
    await store.createReport({
      user_id: "user-a",
      session_id: "session-a",
      kind: "session_summary",
      title: "A report",
      summary: "Visible to user A.",
      payload: { score: 1 },
      provenance: { source: "test" },
    });
    await store.createReport({
      user_id: "user-b",
      session_id: "session-b",
      kind: "session_summary",
      title: "B report",
      summary: "Hidden from user A.",
      payload: { score: 2 },
      provenance: { source: "test" },
    });

    const handler = createCloudHandler({ store });
    const response = await handler(new Request("http://cloud.test/reports", { headers: authHeaders("user-a") }));
    const body = await json(response);

    expect(response.status).toBe(200);
    expect(body.user_id).toBe("user-a");
    expect(Array.isArray(body.reports)).toBe(true);
    expect((body.reports as Array<{ title: string }>)).toHaveLength(1);
    expect((body.reports as Array<{ title: string }>)[0]?.title).toBe("A report");
  });

  test("redacts sensitive report payloads before hosted review responses", async () => {
    const store = createCloudStore();
    const report = await store.createReport({
      user_id: "user-a",
      session_id: "session-sensitive",
      kind: "session_summary",
      title: "Sensitive report",
      summary: "Hosted review should stay redacted.",
      payload: {
        score: 1,
        selectedText: "local selected text",
        nested: [{ copied_text: "copied text" }, { content: "article body" }],
      },
      provenance: { modal_call_id: "modal-sensitive", rawText: "raw page text" },
    });
    const handler = createCloudHandler({ store });

    const response = await handler(new Request(`http://cloud.test/reports/${report.report_id}`, { headers: authHeaders("user-a") }));
    const body = await json(response);

    expect(response.status).toBe(200);
    expect(JSON.stringify(body)).not.toContain("local selected text");
    expect(JSON.stringify(body)).not.toContain("copied text");
    expect(JSON.stringify(body)).not.toContain("article body");
    expect(JSON.stringify(body)).not.toContain("raw page text");
    expect(body.report).toMatchObject({
      report_id: report.report_id,
      user_id: "user-a",
      payload: {
        score: 1,
        redacted: true,
        omitted_sensitive_fields: ["$.selectedText", "$.nested[0].copied_text", "$.nested[1].content"],
      },
      provenance: {
        modal_call_id: "modal-sensitive",
        redacted: true,
        omitted_sensitive_fields: ["$.rawText"],
      },
    });

    const listResponse = await handler(new Request("http://cloud.test/reports", { headers: authHeaders("user-a") }));
    const listBody = await json(listResponse);

    expect(listResponse.status).toBe(200);
    expect(JSON.stringify(listBody)).not.toContain("local selected text");
    expect(JSON.stringify(listBody)).not.toContain("copied text");
    expect(JSON.stringify(listBody)).not.toContain("article body");
    expect(JSON.stringify(listBody)).not.toContain("raw page text");
    expect((listBody.reports as Array<Record<string, unknown>>)[0]).toMatchObject({
      report_id: report.report_id,
      user_id: "user-a",
      payload: {
        score: 1,
        redacted: true,
        omitted_sensitive_fields: ["$.selectedText", "$.nested[0].copied_text", "$.nested[1].content"],
      },
      provenance: {
        modal_call_id: "modal-sensitive",
        redacted: true,
        omitted_sensitive_fields: ["$.rawText"],
      },
    });
  });

  test("records submitted, running, complete, and failed job states through a Modal client", async () => {
    const store = createCloudStore();
    const modalClient: ModalClient = {
      submitJob: async ({ job_id }) => ({ modal_call_id: `modal-${job_id}`, status: "running" }),
    };
    const handler = createCloudHandler({ store, modalClient });

    const submit = await handler(
      new Request("http://cloud.test/jobs", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          kind: "session_summary",
          session_id: "session-cloud-1",
          input: redactedSessionSummaryJobInput(),
        }),
      }),
    );
    const submitted = (await json(submit)) as { job: { job_id: string; status: string; transitions: Array<{ status: string }> } };

    expect(submit.status).toBe(202);
    expect(submitted.job.status).toBe("running");
    expect(submitted.job.transitions.map((transition) => transition.status)).toEqual(["submitted", "running"]);

    const complete = await handler(
      new Request(`http://cloud.test/jobs/${submitted.job.job_id}/status`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          status: "complete",
          result: {
            title: "Top-level Modal title with private prompt",
            summary: "Top-level Modal summary with raw page notes.",
            report: {
              title: "Raw Modal title with copied claim",
              summary: "Raw Modal summary with selected task text.",
              payload: { markers: 2 },
              provenance: { modal_call_id: `modal-${submitted.job.job_id}` },
            },
          },
        }),
      }),
    );
    const completed = (await json(complete)) as { job: { status: string; report_id: string; result: Record<string, unknown> } };

    expect(complete.status).toBe(200);
    expect(completed.job.status).toBe("complete");
    expect(completed.job.report_id.startsWith("report_")).toBe(true);
    expect(JSON.stringify(completed)).not.toContain("copied claim");
    expect(JSON.stringify(completed)).not.toContain("selected task text");
    expect(JSON.stringify(completed)).not.toContain("private prompt");
    expect(JSON.stringify(completed)).not.toContain("raw page notes");
    expect(completed.job.result).toMatchObject({
      title: "Modal session summary report",
      summary: "Modal report completed.",
    });
    expect(completed.job.result.report).toMatchObject({
      title: "Modal session summary report",
      summary: "Modal report completed.",
    });

    const reportResponse = await handler(
      new Request(`http://cloud.test/reports/${completed.job.report_id}`, { headers: authHeaders() }),
    );
    const reportBody = await json(reportResponse);
    expect(reportResponse.status).toBe(200);
    expect(JSON.stringify(reportBody)).not.toContain("copied claim");
    expect(JSON.stringify(reportBody)).not.toContain("selected task text");
    expect(reportBody.report).toMatchObject({
      title: "Modal session summary report",
      summary: "Modal report completed.",
      payload: { markers: 2 },
    });

    const repeatedComplete = await handler(
      new Request(`http://cloud.test/jobs/${submitted.job.job_id}/status`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          status: "complete",
          result: {
            report: {
              title: "Second Modal title",
              summary: "Second Modal summary.",
              payload: { markers: 3 },
              provenance: { modal_call_id: `modal-${submitted.job.job_id}-again` },
            },
          },
        }),
      }),
    );
    const repeated = (await json(repeatedComplete)) as { job: { report_id: string } };
    expect(repeatedComplete.status).toBe(200);
    expect(repeated.job.report_id).toBe(completed.job.report_id);
    expect(await store.listReports("user-a")).toHaveLength(1);

    const failedSubmit = await handler(
      new Request("http://cloud.test/jobs", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ kind: "calibration", input: { privacy_class: "redacted-sync", payload: { export_ref: "fixture" } } }),
      }),
    );
    const failedJob = (await json(failedSubmit)) as { job: { job_id: string } };
    const fail = await handler(
      new Request(`http://cloud.test/jobs/${failedJob.job.job_id}/status`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ status: "failed", error: "synthetic failure" }),
      }),
    );

    expect(fail.status).toBe(200);
    expect(((await json(fail)) as { job: { status: string; error: string } }).job).toMatchObject({
      status: "failed",
      error: "synthetic failure",
    });
  });

  test("completes redacted session summary jobs through a cloud summary provider before Modal", async () => {
    const store = createCloudStore();
    let modalCalls = 0;
    let summaryInput = "";
    const modalClient: ModalClient = {
      submitJob: async () => {
        modalCalls += 1;
        throw new Error("Modal should not be called when cloud summary provider is configured");
      },
    };
    const summaryClient: SummaryClient = {
      summarizeSession: async ({ input }) => {
        summaryInput = JSON.stringify(input);
        return {
          provider: "openai",
          model: "gpt-test-summary",
          text: "OpenAI says the copied evidence needs one follow-up note.",
          limitations: ["fixture limitation"],
        };
      },
    };
    const handler = createCloudHandler({ store, modalClient, summaryClient });

    const response = await handler(
      new Request("http://cloud.test/jobs", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          kind: "session_summary",
          session_id: "session-cloud-1",
          input: redactedSessionSummaryJobInput(),
        }),
      }),
    );
    const body = (await json(response)) as { job: { status: string; report_id: string; result: Record<string, unknown> } };

    expect(response.status).toBe(202);
    expect(body.job.status).toBe("complete");
    expect(body.job.report_id.startsWith("report_")).toBe(true);
    expect(body.job.result).toMatchObject({
      report: {
        payload: {
          summary_text: "OpenAI says the copied evidence needs one follow-up note.",
          provider: "openai",
          model: "gpt-test-summary",
          privacy_class: "redacted-sync",
          limitations: ["fixture limitation"],
        },
        provenance: {
          provider: "openai",
          model: "gpt-test-summary",
          input_privacy_class: "redacted-sync",
        },
      },
    });
    expect(summaryInput).toContain("redacted-sync");
    expect(summaryInput).not.toContain("Cursor");
    expect(summaryInput).not.toContain("com.todesktop.230313mzl4w4u92");
    expect(modalCalls).toBe(0);

    const reportResponse = await handler(new Request(`http://cloud.test/reports/${body.job.report_id}`, { headers: authHeaders() }));
    const reportBody = await json(reportResponse);
    expect(reportResponse.status).toBe(200);
    expect(reportBody.report).toMatchObject({
      title: "Redacted LLM session summary",
      summary: "Cloud LLM report completed.",
      payload: {
        summary_text: "OpenAI says the copied evidence needs one follow-up note.",
        provider: "openai",
      },
    });
  });

  test("rejects raw text in Modal job results before report creation", async () => {
    const store = createCloudStore();
    const modalClient: ModalClient = {
      submitJob: async ({ job_id }) => ({ modal_call_id: `modal-${job_id}`, status: "running" }),
    };
    const handler = createCloudHandler({ store, modalClient });

    const submittedResponse = await handler(
      new Request("http://cloud.test/jobs", {
        method: "POST",
        headers: authHeaders("user-a"),
        body: JSON.stringify({
          kind: "session_summary",
          input: redactedSessionSummaryJobInput(),
        }),
      }),
    );
    const submitted = (await json(submittedResponse)) as { job: { job_id: string } };

    const response = await handler(
      new Request(`http://cloud.test/jobs/${submitted.job.job_id}/status`, {
        method: "POST",
        headers: authHeaders("user-a"),
        body: JSON.stringify({
          status: "complete",
          result: {
            report: {
              title: "Sensitive result",
              payload: { score: 1, content: "raw article body" },
              provenance: { selectedText: "copied claim" },
            },
          },
        }),
      }),
    );
    const body = await json(response);

    expect(response.status).toBe(422);
    expect(body.error).toMatchObject({
      code: "privacy_rejected",
      details: {
        fields: ["$.report.payload.content", "$.report.provenance.selectedText"],
      },
    });
  });

  test("rejects sensitive job input before calling Modal", async () => {
    const modalClient: ModalClient = {
      submitJob: async () => {
        throw new Error("Modal should not be called for sensitive input");
      },
    };
    const handler = createCloudHandler({ store: createCloudStore(), modalClient });

    const response = await handler(
      new Request("http://cloud.test/jobs", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          kind: "session_summary",
          input: { privacy_class: "redacted-sync", payload: { keyText: "typed content" } },
        }),
      }),
    );
    const body = await json(response);

    expect(response.status).toBe(422);
    expect(body.error).toMatchObject({ code: "privacy_rejected" });
  });

  test("requires redacted session summary inputs to be structured and identity-free", async () => {
    let calls = 0;
    const modalClient: ModalClient = {
      submitJob: async () => {
        calls += 1;
        throw new Error("Modal should not be called for malformed session summary input");
      },
    };
    const handler = createCloudHandler({ store: createCloudStore(), modalClient });
    const malformed = await handler(
      new Request("http://cloud.test/jobs", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          kind: "session_summary",
          input: { privacy_class: "redacted-sync", payload: { report_id: "missing-shape" } },
        }),
      }),
    );
    const identityPayload = redactedSessionSummaryJobInput();
    (identityPayload.payload as Record<string, unknown>).window_title = "private-notes.md";
    const identity = await handler(
      new Request("http://cloud.test/jobs", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          kind: "session_summary",
          input: identityPayload,
        }),
      }),
    );

    expect(malformed.status).toBe(400);
    expect((await json(malformed)).error).toMatchObject({ code: "invalid_request" });
    expect(identity.status).toBe(422);
    expect((await json(identity)).error).toMatchObject({ code: "privacy_rejected" });
    expect(calls).toBe(0);
  });

  test("rejects raw frame, raw key, typed text, and document text Modal job inputs", async () => {
    let calls = 0;
    const modalClient: ModalClient = {
      submitJob: async () => {
        calls += 1;
        throw new Error("Modal should not be called for sensitive input");
      },
    };
    const handler = createCloudHandler({ store: createCloudStore(), modalClient });
    const payloads = [
      { rawFrame: "base64-frame" },
      { nested: { rawKey: "A" } },
      { typedText: "typed search" },
      { content: "article body" },
      { page_text: "article body" },
      { documentText: "article body" },
    ];

    for (const payload of payloads) {
      const response = await handler(
        new Request("http://cloud.test/jobs", {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({
            kind: "session_summary",
            input: { privacy_class: "redacted-sync", payload },
          }),
        }),
      );
      const body = await json(response);

      expect(response.status).toBe(422);
      expect(body.error).toMatchObject({ code: "privacy_rejected" });
    }
    expect(calls).toBe(0);
  });

  test("rejects desktop activity and window-title Modal job inputs", async () => {
    let calls = 0;
    const modalClient: ModalClient = {
      submitJob: async () => {
        calls += 1;
        throw new Error("Modal should not be called for desktop activity input");
      },
    };
    const handler = createCloudHandler({ store: createCloudStore(), modalClient });
    const inputs = [
      {
        privacy_class: "document-opt-in",
        source: "desktop-activity",
        event_type: "desktop.window_focus",
        payload: {
          app_name: "Cursor",
          window_title: "private-notes.md",
          focus_started_monotonic_ms: 1_000,
          focus_ended_monotonic_ms: 2_000,
          duration_ms: 1_000,
          permission_status: "granted",
        },
      },
      {
        privacy_class: "document-opt-in",
        payload: { window_title: "private-notes.md" },
      },
      {
        privacy_class: "document-opt-in",
        payload: {
          events: [
            {
              source: "desktop-activity",
              event_type: "desktop.app_focus",
              payload: {
                app_name: "Cursor",
                bundle_id: "com.todesktop.230313mzl4w4u92",
              },
            },
          ],
        },
      },
      {
        privacy_class: "document-opt-in",
        payload: {
          events: [
            {
              source: "desktop-activity",
              event_type: "desktop.window_focus",
              payload: {
                app_name: "Cursor",
                bundle_id: "com.todesktop.230313mzl4w4u92",
              },
            },
          ],
        },
      },
    ];

    for (const input of inputs) {
      const response = await handler(
        new Request("http://cloud.test/jobs", {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({
            kind: "session_summary",
            input,
          }),
        }),
      );
      const body = await json(response);

      expect(response.status).toBe(422);
      expect(body.error).toMatchObject({ code: "privacy_rejected" });
    }
    expect(calls).toBe(0);
  });
});

describe("cloud runtime configuration", () => {
  test("health waits for configured store initialization", async () => {
    let initialized = false;
    const store = createCloudStore() as CloudStore & { initialize: () => Promise<void> };
    store.initialize = async () => {
      initialized = true;
    };
    const handler = createCloudHandler({ store });

    const response = await handler(new Request("http://cloud.test/health"));
    const body = await json(response);

    expect(response.status).toBe(200);
    expect(initialized).toBe(true);
    expect(body).toMatchObject({ status: "ok", storage: "memory" });
  });

  test("selects Postgres storage when DATABASE_URL is configured", () => {
    let selectedUrl: string | undefined;
    const selected = createCloudStoreFromEnv(
      { DATABASE_URL: "postgres://railway.example/inquiry" },
      {
        postgresFactory: (databaseUrl) => {
          selectedUrl = databaseUrl;
          const store = createCloudStore() as CloudStore & { kind: "postgres" };
          store.kind = "postgres";
          return store;
        },
      },
    );

    expect(selected.kind).toBe("postgres");
    expect(selectedUrl).toBe("postgres://railway.example/inquiry");
  });

  test("fails production startup without auth secret or durable storage", () => {
    expect(() => createCloudHandler({ env: { NODE_ENV: "production" } })).toThrow("INQUIRY_CLOUD_AUTH_SECRET");
    expect(() =>
      createCloudHandler({
        env: {
          NODE_ENV: "production",
          INQUIRY_CLOUD_AUTH_SECRET: "secret",
        },
      }),
    ).toThrow("requires durable persistence");
  });

  test("keeps explicit in-memory smoke mode available for Railway checks", () => {
    expect(() =>
      createCloudHandler({
        env: {
          NODE_ENV: "production",
          INQUIRY_CLOUD_AUTH_SECRET: "secret",
          INQUIRY_ALLOW_IN_MEMORY_CLOUD: "1",
        },
      }),
    ).not.toThrow();
  });

  test("readiness distinguishes durable Postgres from local memory storage", async () => {
    const memory = createCloudHandler({ store: createCloudStore() });
    const memoryReady = await memory(new Request("http://cloud.test/ready"));
    const memoryBody = await json(memoryReady);
    const postgresStore = createCloudStore() as CloudStore & { kind: "postgres"; initialize: () => Promise<void> };
    postgresStore.kind = "postgres";
    let initialized = false;
    postgresStore.initialize = async () => {
      initialized = true;
    };
    const postgres = createCloudHandler({ store: postgresStore });
    const postgresReady = await postgres(new Request("http://cloud.test/ready"));
    const postgresBody = await json(postgresReady);

    expect(memoryReady.status).toBe(503);
    expect(memoryBody).toMatchObject({ status: "not_ready", storage: "memory", durable: false });
    expect(postgresReady.status).toBe(200);
    expect(initialized).toBe(true);
    expect(postgresBody).toMatchObject({ status: "ready", storage: "postgres", durable: true });
  });
});
