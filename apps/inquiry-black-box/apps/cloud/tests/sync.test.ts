import { describe, expect, test } from "bun:test";
import { createEvent, type EventEnvelope } from "@inquiry/schema";
import { createCloudStore, createCloudStoreFromEnv, type CloudStore } from "../src/db/schema";
import { createCloudBearerToken } from "../src/routes/common";
import { createCloudHandler } from "../src/server";
import type { ModalClient } from "../src/lib/modalClient";

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

  test("rejects privacy-ineligible and sensitive-field payloads", async () => {
    const handler = createCloudHandler({ store: createCloudStore() });
    const localOnly = { ...redactedEvent("event-local"), privacy_class: "local-derived" };
    const sensitive = {
      ...redactedEvent("event-sensitive"),
      payload: { nested: { keyContent: "raw typed content" }, rawVideo: "base64-video" },
    };

    for (const event of [localOnly, sensitive]) {
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
          input: { privacy_class: "redacted-sync", payload: { export_ref: "fixture" } },
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
            report: {
              title: "Smoke report",
              summary: "Synthetic analysis completed.",
              payload: { markers: 2 },
              provenance: { modal_call_id: `modal-${submitted.job.job_id}` },
            },
          },
        }),
      }),
    );
    const completed = (await json(complete)) as { job: { status: string; report_id: string } };

    expect(complete.status).toBe(200);
    expect(completed.job.status).toBe("complete");
    expect(completed.job.report_id.startsWith("report_")).toBe(true);

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
});
