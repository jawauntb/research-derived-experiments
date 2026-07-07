import { describe, expect, test } from "bun:test";
import { createEvent, type EventEnvelope } from "@inquiry/schema";
import { createPostgresCloudStore, postgresSchemaStatements, type PostgresSql } from "../src/db/postgres";

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

describe("Postgres cloud store", () => {
  test("migrates and preserves cloud behavior contracts", async () => {
    const sql = new MemoryPostgresSql();
    const store = createPostgresCloudStore({
      sql,
      now: () => new Date("2026-07-07T12:00:00.000Z"),
    });

    const first = await store.syncEvent("user-a", "device-1", redactedEvent("event-1"));
    const duplicate = await store.syncEvent("user-a", "device-1", redactedEvent("event-1"));

    expect(store.kind).toBe("postgres");
    expect(sql.migrations).toBe(postgresSchemaStatements.length);
    expect(first.inserted).toBe(true);
    expect(duplicate.inserted).toBe(false);
    expect(await store.listEvents("user-a")).toHaveLength(1);

    await store.revokeDeviceToken({
      user_id: "user-a",
      device_id: "device-1",
      token_id: "token-1",
      reason: "user-disabled-sync",
    });
    expect((await store.getDeviceToken("user-a", "device-1", "token-1"))?.status).toBe("revoked");

    const job = await store.createJob({
      user_id: "user-a",
      kind: "session_summary",
      input: { privacy_class: "redacted-sync", payload: { export_ref: "fixture" } },
      session_id: "session-cloud-1",
    });
    const running = await store.updateJobStatus("user-a", job.job_id, {
      status: "running",
      modal_call_id: "modal-job-1",
      message: "submitted to Modal",
    });
    expect(running?.transitions.map((transition) => transition.status)).toEqual(["submitted", "running"]);

    await store.createReport({
      user_id: "user-a",
      session_id: "session-cloud-1",
      kind: "session_summary",
      title: "A report",
      summary: "Visible to user A.",
      payload: { score: 1 },
      provenance: { source: "test" },
    });
    await store.createReport({
      user_id: "user-b",
      session_id: "session-cloud-2",
      kind: "session_summary",
      title: "B report",
      summary: "Hidden from user A.",
      payload: { score: 2 },
      provenance: { source: "test" },
    });
    expect((await store.listReports("user-a")).map((report) => report.title)).toEqual(["A report"]);
  });
});

class MemoryPostgresSql implements PostgresSql {
  migrations = 0;
  private readonly syncEvents = new Map<string, Record<string, unknown>>();
  private readonly deviceTokens = new Map<string, Record<string, unknown>>();
  private readonly jobs = new Map<string, Record<string, unknown>>();
  private readonly reports = new Map<string, Record<string, unknown>>();

  async unsafe(query: string, params: unknown[] = []): Promise<Record<string, unknown>[]> {
    const normalized = query.replace(/\s+/g, " ").trim();
    if (normalized.startsWith("CREATE ")) {
      this.migrations += 1;
      return [];
    }

    if (normalized.startsWith("INSERT INTO inquiry_sync_events")) {
      const row = {
        user_id: stringParam(params[0]),
        device_id: stringParam(params[1]),
        event_id: stringParam(params[2]),
        session_id: stringParam(params[3]),
        event_type: stringParam(params[4]),
        privacy_class: stringParam(params[5]),
        payload: jsonParam(params[6]),
        event: jsonParam(params[7]),
        received_at: stringParam(params[8]),
      };
      const key = `${row.user_id}:${row.event_id}`;
      if (this.syncEvents.has(key)) {
        return [];
      }
      this.syncEvents.set(key, row);
      return cloneRows([row]);
    }
    if (normalized.includes("FROM inquiry_sync_events") && normalized.includes("event_id = $2")) {
      return cloneRows(mapGet(this.syncEvents, `${stringParam(params[0])}:${stringParam(params[1])}`));
    }
    if (normalized.includes("FROM inquiry_sync_events")) {
      return cloneRows([...this.syncEvents.values()].filter((row) => row.user_id === params[0]));
    }

    if (normalized.startsWith("INSERT INTO inquiry_device_tokens")) {
      const row = {
        user_id: stringParam(params[0]),
        device_id: stringParam(params[1]),
        token_id: stringParam(params[2]),
        status: "revoked",
        revoked_at: stringParam(params[3]),
        reason: nullableStringParam(params[4]),
      };
      const key = `${row.user_id}:${row.device_id}:${row.token_id}`;
      if (this.deviceTokens.has(key)) {
        return [];
      }
      this.deviceTokens.set(key, row);
      return cloneRows([row]);
    }
    if (normalized.includes("FROM inquiry_device_tokens")) {
      return cloneRows(mapGet(this.deviceTokens, `${stringParam(params[0])}:${stringParam(params[1])}:${stringParam(params[2])}`));
    }

    if (normalized.startsWith("INSERT INTO inquiry_jobs")) {
      const row = {
        user_id: stringParam(params[0]),
        job_id: stringParam(params[1]),
        kind: stringParam(params[2]),
        status: "submitted",
        input: jsonParam(params[3]),
        created_at: stringParam(params[4]),
        updated_at: stringParam(params[5]),
        transitions: jsonParam(params[6]),
        session_id: nullableStringParam(params[7]),
        modal_call_id: null,
        report_id: null,
        result: null,
        error: null,
      };
      this.jobs.set(`${row.user_id}:${row.job_id}`, row);
      return cloneRows([row]);
    }
    if (normalized.startsWith("UPDATE inquiry_jobs")) {
      const key = `${stringParam(params[0])}:${stringParam(params[1])}`;
      const existing = this.jobs.get(key);
      if (!existing) {
        return [];
      }
      const row = {
        ...existing,
        status: stringParam(params[2]),
        updated_at: stringParam(params[3]),
        transitions: jsonParam(params[4]),
        modal_call_id: nullableStringParam(params[5]),
        report_id: nullableStringParam(params[6]),
        result: nullableJsonParam(params[7]),
        error: nullableStringParam(params[8]),
      };
      this.jobs.set(key, row);
      return cloneRows([row]);
    }
    if (normalized.includes("FROM inquiry_jobs")) {
      return cloneRows(mapGet(this.jobs, `${stringParam(params[0])}:${stringParam(params[1])}`));
    }

    if (normalized.startsWith("INSERT INTO inquiry_reports")) {
      const row = {
        user_id: stringParam(params[0]),
        report_id: stringParam(params[1]),
        kind: stringParam(params[2]),
        title: stringParam(params[3]),
        summary: stringParam(params[4]),
        payload: jsonParam(params[5]),
        provenance: jsonParam(params[6]),
        created_at: stringParam(params[7]),
        session_id: nullableStringParam(params[8]),
      };
      this.reports.set(`${row.user_id}:${row.report_id}`, row);
      return cloneRows([row]);
    }
    if (normalized.includes("FROM inquiry_reports") && normalized.includes("report_id = $2")) {
      return cloneRows(mapGet(this.reports, `${stringParam(params[0])}:${stringParam(params[1])}`));
    }
    if (normalized.includes("FROM inquiry_reports")) {
      return cloneRows([...this.reports.values()].filter((row) => row.user_id === params[0]));
    }

    throw new Error(`unsupported fake SQL query: ${normalized}`);
  }
}

function mapGet(map: Map<string, Record<string, unknown>>, key: string): Record<string, unknown>[] {
  const value = map.get(key);
  return value ? [value] : [];
}

function stringParam(value: unknown): string {
  if (typeof value !== "string") {
    throw new Error("expected string SQL parameter");
  }
  return value;
}

function nullableStringParam(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function jsonParam(value: unknown): unknown {
  return typeof value === "string" ? JSON.parse(value) : value;
}

function nullableJsonParam(value: unknown): unknown {
  return value === null || value === undefined ? null : jsonParam(value);
}

function cloneRows(rows: Record<string, unknown>[]): Record<string, unknown>[] {
  return structuredClone(rows);
}
