import { isPrivacyClass, validateEvent, type EventEnvelope, type JsonObject } from "@inquiry/schema";
import type { CloudStore, DeviceTokenRecord, JobKind, JobRecord, JobStatus, JobTransition, ReportRecord, SyncEventRecord } from "./schema";

export type PostgresSql = {
  unsafe(query: string, params?: unknown[]): Promise<Record<string, unknown>[]>;
};

export type PostgresCloudStoreOptions = {
  databaseUrl?: string;
  sql?: PostgresSql;
  now?: () => Date;
  autoMigrate?: boolean;
};

export const postgresSchemaStatements = [
  `CREATE TABLE IF NOT EXISTS inquiry_sync_events (
    user_id text NOT NULL,
    device_id text NOT NULL,
    event_id text NOT NULL,
    session_id text NOT NULL,
    event_type text NOT NULL,
    privacy_class text NOT NULL,
    payload jsonb NOT NULL,
    event jsonb NOT NULL,
    received_at text NOT NULL,
    PRIMARY KEY (user_id, event_id)
  )`,
  `CREATE INDEX IF NOT EXISTS inquiry_sync_events_user_session_idx
    ON inquiry_sync_events (user_id, session_id, received_at)`,
  `CREATE TABLE IF NOT EXISTS inquiry_device_tokens (
    user_id text NOT NULL,
    device_id text NOT NULL,
    token_id text NOT NULL,
    status text NOT NULL,
    revoked_at text NOT NULL,
    reason text,
    PRIMARY KEY (user_id, device_id, token_id)
  )`,
  `CREATE TABLE IF NOT EXISTS inquiry_jobs (
    user_id text NOT NULL,
    job_id text NOT NULL,
    kind text NOT NULL,
    status text NOT NULL,
    input jsonb NOT NULL,
    created_at text NOT NULL,
    updated_at text NOT NULL,
    transitions jsonb NOT NULL,
    session_id text,
    modal_call_id text,
    report_id text,
    result jsonb,
    error text,
    PRIMARY KEY (user_id, job_id)
  )`,
  `CREATE INDEX IF NOT EXISTS inquiry_jobs_user_session_idx
    ON inquiry_jobs (user_id, session_id, updated_at)`,
  `CREATE TABLE IF NOT EXISTS inquiry_reports (
    user_id text NOT NULL,
    report_id text NOT NULL,
    kind text NOT NULL,
    title text NOT NULL,
    summary text NOT NULL,
    payload jsonb NOT NULL,
    provenance jsonb NOT NULL,
    created_at text NOT NULL,
    session_id text,
    PRIMARY KEY (user_id, report_id)
  )`,
  `CREATE INDEX IF NOT EXISTS inquiry_reports_user_session_idx
    ON inquiry_reports (user_id, session_id, created_at)`,
] as const;

const validJobStatuses = new Set<JobStatus>(["submitted", "running", "complete", "failed"]);
const validJobKinds = new Set<JobKind>(["content_difficulty", "embedding", "session_summary", "calibration"]);

export function createPostgresCloudStore(options: PostgresCloudStoreOptions = {}): CloudStore {
  const databaseUrl = options.databaseUrl ?? process.env.DATABASE_URL;
  const sql = options.sql ?? createBunPostgresSql(databaseUrl);
  return new PostgresCloudStore(sql, options.now ?? (() => new Date()), options.autoMigrate ?? true);
}

export function createBunPostgresSql(databaseUrl: string | undefined): PostgresSql {
  if (!databaseUrl) {
    throw new Error("DATABASE_URL is required for the Postgres cloud store");
  }

  const SQL = (globalThis as { Bun?: { SQL?: new (url: string) => PostgresSql } }).Bun?.SQL;
  if (!SQL) {
    throw new Error("Bun.SQL is required for the Postgres cloud store");
  }

  return new SQL(databaseUrl);
}

class PostgresCloudStore implements CloudStore {
  readonly kind = "postgres";
  private ready: Promise<void> | undefined;

  constructor(
    private readonly sql: PostgresSql,
    private readonly now: () => Date,
    private readonly autoMigrate: boolean,
  ) {
    this.ready = autoMigrate ? undefined : Promise.resolve();
  }

  async initialize(): Promise<void> {
    await this.ensureReady();
  }

  async syncEvent(user_id: string, device_id: string, event: EventEnvelope): Promise<{ inserted: boolean; record: SyncEventRecord }> {
    await this.ensureReady();
    const received_at = this.timestamp();
    const rows = await this.sql.unsafe(
      `INSERT INTO inquiry_sync_events (
        user_id, device_id, event_id, session_id, event_type, privacy_class, payload, event, received_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, $9)
      ON CONFLICT (user_id, event_id) DO NOTHING
      RETURNING *`,
      [
        user_id,
        device_id,
        event.event_id,
        event.session_id,
        event.event_type,
        event.privacy_class,
        jsonParam(event.payload),
        jsonParam(event),
        received_at,
      ],
    );

    const inserted = first(rows);
    if (inserted) {
      return { inserted: true, record: syncEventRecord(inserted) };
    }

    const existing = await this.selectSyncEvent(user_id, event.event_id);
    if (!existing) {
      throw new Error(`event ${event.event_id} was not inserted or found`);
    }

    return { inserted: false, record: existing };
  }

  async listEvents(user_id: string): Promise<SyncEventRecord[]> {
    await this.ensureReady();
    const rows = await this.sql.unsafe(
      `SELECT * FROM inquiry_sync_events WHERE user_id = $1 ORDER BY received_at ASC, event_id ASC`,
      [user_id],
    );
    return rows.map(syncEventRecord);
  }

  async revokeDeviceToken(input: {
    user_id: string;
    device_id: string;
    token_id: string;
    revoked_at?: string;
    reason?: string;
  }): Promise<DeviceTokenRecord> {
    await this.ensureReady();
    const revoked_at = input.revoked_at ?? this.timestamp();
    const rows = await this.sql.unsafe(
      `INSERT INTO inquiry_device_tokens (
        user_id, device_id, token_id, status, revoked_at, reason
      ) VALUES ($1, $2, $3, 'revoked', $4, $5)
      ON CONFLICT (user_id, device_id, token_id) DO NOTHING
      RETURNING *`,
      [input.user_id, input.device_id, input.token_id, revoked_at, input.reason ?? null],
    );

    const inserted = first(rows);
    if (inserted) {
      return deviceTokenRecord(inserted);
    }

    const existing = await this.getDeviceToken(input.user_id, input.device_id, input.token_id);
    if (!existing) {
      throw new Error(`device token ${input.token_id} was not inserted or found`);
    }
    return existing;
  }

  async getDeviceToken(user_id: string, device_id: string, token_id: string): Promise<DeviceTokenRecord | undefined> {
    await this.ensureReady();
    const rows = await this.sql.unsafe(
      `SELECT * FROM inquiry_device_tokens WHERE user_id = $1 AND device_id = $2 AND token_id = $3`,
      [user_id, device_id, token_id],
    );
    const row = first(rows);
    return row ? deviceTokenRecord(row) : undefined;
  }

  async createJob(input: { user_id: string; kind: JobKind; input: JsonObject; session_id?: string }): Promise<JobRecord> {
    await this.ensureReady();
    const created_at = this.timestamp();
    const job_id = newId("job");
    const transitions: JobTransition[] = [{ status: "submitted", at: created_at }];
    const rows = await this.sql.unsafe(
      `INSERT INTO inquiry_jobs (
        user_id, job_id, kind, status, input, created_at, updated_at, transitions, session_id
      ) VALUES ($1, $2, $3, 'submitted', $4::jsonb, $5, $6, $7::jsonb, $8)
      RETURNING *`,
      [input.user_id, job_id, input.kind, jsonParam(input.input), created_at, created_at, jsonParam(transitions), input.session_id ?? null],
    );

    const row = first(rows);
    if (!row) {
      throw new Error(`job ${job_id} was not created`);
    }
    return jobRecord(row);
  }

  async getJob(user_id: string, job_id: string): Promise<JobRecord | undefined> {
    await this.ensureReady();
    return this.selectJob(user_id, job_id);
  }

  async updateJobStatus(
    user_id: string,
    job_id: string,
    update: {
      status: JobStatus;
      modal_call_id?: string;
      report_id?: string;
      result?: JsonObject;
      error?: string;
      message?: string;
    },
  ): Promise<JobRecord | undefined> {
    await this.ensureReady();
    const job = await this.selectJob(user_id, job_id);
    if (!job) {
      return undefined;
    }

    const updated_at = this.timestamp();
    const transitions = [...job.transitions];
    if (job.status !== update.status || update.message) {
      transitions.push({
        status: update.status,
        at: updated_at,
        ...(update.message ? { message: update.message } : {}),
      });
    }

    const result = update.result ?? job.result;
    const rows = await this.sql.unsafe(
      `UPDATE inquiry_jobs
      SET status = $3,
        updated_at = $4,
        transitions = $5::jsonb,
        modal_call_id = $6,
        report_id = $7,
        result = $8::jsonb,
        error = $9
      WHERE user_id = $1 AND job_id = $2
      RETURNING *`,
      [
        user_id,
        job_id,
        update.status,
        updated_at,
        jsonParam(transitions),
        update.modal_call_id ?? job.modal_call_id ?? null,
        update.report_id ?? job.report_id ?? null,
        result ? jsonParam(result) : null,
        update.error ?? job.error ?? null,
      ],
    );

    const row = first(rows);
    return row ? jobRecord(row) : undefined;
  }

  async createReport(input: {
    user_id: string;
    kind: string;
    title: string;
    summary: string;
    payload: JsonObject;
    provenance: JsonObject;
    session_id?: string;
  }): Promise<ReportRecord> {
    await this.ensureReady();
    const report_id = newId("report");
    const rows = await this.sql.unsafe(
      `INSERT INTO inquiry_reports (
        user_id, report_id, kind, title, summary, payload, provenance, created_at, session_id
      ) VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8, $9)
      RETURNING *`,
      [
        input.user_id,
        report_id,
        input.kind,
        input.title,
        input.summary,
        jsonParam(input.payload),
        jsonParam(input.provenance),
        this.timestamp(),
        input.session_id ?? null,
      ],
    );

    const row = first(rows);
    if (!row) {
      throw new Error(`report ${report_id} was not created`);
    }
    return reportRecord(row);
  }

  async listReports(user_id: string): Promise<ReportRecord[]> {
    await this.ensureReady();
    const rows = await this.sql.unsafe(
      `SELECT * FROM inquiry_reports WHERE user_id = $1 ORDER BY created_at DESC, report_id ASC`,
      [user_id],
    );
    return rows.map(reportRecord);
  }

  async getReport(user_id: string, report_id: string): Promise<ReportRecord | undefined> {
    await this.ensureReady();
    const rows = await this.sql.unsafe(
      `SELECT * FROM inquiry_reports WHERE user_id = $1 AND report_id = $2`,
      [user_id, report_id],
    );
    const row = first(rows);
    return row ? reportRecord(row) : undefined;
  }

  private async migrate(): Promise<void> {
    for (const statement of postgresSchemaStatements) {
      await this.sql.unsafe(statement);
    }
  }

  private async ensureReady(): Promise<void> {
    if (!this.ready) {
      this.ready = this.migrate();
    }
    await this.ready;
  }

  private async selectSyncEvent(user_id: string, event_id: string): Promise<SyncEventRecord | undefined> {
    const rows = await this.sql.unsafe(
      `SELECT * FROM inquiry_sync_events WHERE user_id = $1 AND event_id = $2`,
      [user_id, event_id],
    );
    const row = first(rows);
    return row ? syncEventRecord(row) : undefined;
  }

  private async selectJob(user_id: string, job_id: string): Promise<JobRecord | undefined> {
    const rows = await this.sql.unsafe(`SELECT * FROM inquiry_jobs WHERE user_id = $1 AND job_id = $2`, [user_id, job_id]);
    const row = first(rows);
    return row ? jobRecord(row) : undefined;
  }

  private timestamp(): string {
    return this.now().toISOString();
  }
}

function syncEventRecord(row: Record<string, unknown>): SyncEventRecord {
  const privacy_class = stringColumn(row, "privacy_class");
  if (!isPrivacyClass(privacy_class)) {
    throw new Error(`invalid privacy class in cloud store: ${privacy_class}`);
  }

  return {
    user_id: stringColumn(row, "user_id"),
    device_id: stringColumn(row, "device_id"),
    event_id: stringColumn(row, "event_id"),
    session_id: stringColumn(row, "session_id"),
    event_type: stringColumn(row, "event_type"),
    privacy_class,
    payload: jsonObjectColumn(row, "payload"),
    received_at: stringColumn(row, "received_at"),
    event: eventEnvelopeColumn(row, "event"),
  };
}

function deviceTokenRecord(row: Record<string, unknown>): DeviceTokenRecord {
  const status = stringColumn(row, "status");
  if (status !== "revoked") {
    throw new Error(`invalid device token status in cloud store: ${status}`);
  }
  const reason = optionalStringColumn(row, "reason");

  return {
    user_id: stringColumn(row, "user_id"),
    device_id: stringColumn(row, "device_id"),
    token_id: stringColumn(row, "token_id"),
    status,
    revoked_at: stringColumn(row, "revoked_at"),
    ...(reason ? { reason } : {}),
  };
}

function jobRecord(row: Record<string, unknown>): JobRecord {
  const status = jobStatusColumn(row, "status");
  const session_id = optionalStringColumn(row, "session_id");
  const modal_call_id = optionalStringColumn(row, "modal_call_id");
  const report_id = optionalStringColumn(row, "report_id");
  const result = optionalJsonObjectColumn(row, "result");
  const error = optionalStringColumn(row, "error");

  return {
    user_id: stringColumn(row, "user_id"),
    job_id: stringColumn(row, "job_id"),
    kind: jobKindColumn(row, "kind"),
    status,
    input: jsonObjectColumn(row, "input"),
    created_at: stringColumn(row, "created_at"),
    updated_at: stringColumn(row, "updated_at"),
    transitions: jobTransitionsColumn(row, "transitions"),
    ...(session_id ? { session_id } : {}),
    ...(modal_call_id ? { modal_call_id } : {}),
    ...(report_id ? { report_id } : {}),
    ...(result ? { result } : {}),
    ...(error ? { error } : {}),
  };
}

function reportRecord(row: Record<string, unknown>): ReportRecord {
  const session_id = optionalStringColumn(row, "session_id");

  return {
    user_id: stringColumn(row, "user_id"),
    report_id: stringColumn(row, "report_id"),
    kind: stringColumn(row, "kind"),
    title: stringColumn(row, "title"),
    summary: stringColumn(row, "summary"),
    payload: jsonObjectColumn(row, "payload"),
    provenance: jsonObjectColumn(row, "provenance"),
    created_at: stringColumn(row, "created_at"),
    ...(session_id ? { session_id } : {}),
  };
}

function eventEnvelopeColumn(row: Record<string, unknown>, key: string): EventEnvelope {
  const value = parseJsonColumn(row[key]);
  validateEvent(value);
  return value as EventEnvelope;
}

function jobTransitionsColumn(row: Record<string, unknown>, key: string): JobTransition[] {
  const value = parseJsonColumn(row[key]);
  if (!Array.isArray(value)) {
    throw new Error(`${key} must be a JSON array`);
  }
  return value.map((transition) => {
    if (!isRecord(transition)) {
      throw new Error(`${key} entries must be JSON objects`);
    }
    const message = optionalStringColumn(transition, "message");
    return {
      status: jobStatusColumn(transition, "status"),
      at: stringColumn(transition, "at"),
      ...(message ? { message } : {}),
    };
  });
}

function jobStatusColumn(row: Record<string, unknown>, key: string): JobStatus {
  const value = stringColumn(row, key);
  if (!validJobStatuses.has(value as JobStatus)) {
    throw new Error(`${key} must be a valid job status`);
  }
  return value as JobStatus;
}

function jobKindColumn(row: Record<string, unknown>, key: string): JobKind {
  const value = stringColumn(row, key);
  if (!validJobKinds.has(value as JobKind)) {
    throw new Error(`${key} must be a valid job kind`);
  }
  return value as JobKind;
}

function jsonObjectColumn(row: Record<string, unknown>, key: string): JsonObject {
  const value = parseJsonColumn(row[key]);
  if (!isJsonObject(value)) {
    throw new Error(`${key} must be a JSON object`);
  }
  return value;
}

function optionalJsonObjectColumn(row: Record<string, unknown>, key: string): JsonObject | undefined {
  const value = row[key];
  if (value === null || value === undefined) {
    return undefined;
  }
  return jsonObjectColumn(row, key);
}

function stringColumn(row: Record<string, unknown>, key: string): string {
  const value = row[key];
  if (typeof value !== "string") {
    throw new Error(`${key} must be a string`);
  }
  return value;
}

function optionalStringColumn(row: Record<string, unknown>, key: string): string | undefined {
  const value = row[key];
  if (value === null || value === undefined) {
    return undefined;
  }
  if (typeof value !== "string") {
    throw new Error(`${key} must be a string`);
  }
  return value;
}

function parseJsonColumn(value: unknown): unknown {
  if (typeof value === "string") {
    return JSON.parse(value);
  }
  return value;
}

function jsonParam(value: unknown): string {
  return JSON.stringify(value);
}

function first<T>(values: T[]): T | undefined {
  return values[0];
}

function newId(prefix: string): string {
  return `${prefix}_${crypto.randomUUID()}`;
}

function isJsonObject(value: unknown): value is JsonObject {
  if (!isRecord(value)) {
    return false;
  }
  return Object.values(value).every(isJsonValue);
}

function isJsonValue(value: unknown): boolean {
  if (value === null || typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return true;
  }
  if (Array.isArray(value)) {
    return value.every(isJsonValue);
  }
  if (isRecord(value)) {
    return Object.values(value).every(isJsonValue);
  }
  return false;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
