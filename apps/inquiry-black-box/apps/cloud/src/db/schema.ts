import type { EventEnvelope, JsonObject, JsonValue, PrivacyClass } from "@inquiry/schema";

export const jobStatuses = ["submitted", "running", "complete", "failed"] as const;
export type JobStatus = (typeof jobStatuses)[number];

export const jobKinds = ["content_difficulty", "embedding", "session_summary", "calibration"] as const;
export type JobKind = (typeof jobKinds)[number];

export type AuthenticatedUser = {
  user_id: string;
  token: string;
};

export type SyncEventRecord = {
  user_id: string;
  device_id: string;
  event_id: string;
  session_id: string;
  event_type: string;
  privacy_class: PrivacyClass;
  payload: JsonObject;
  received_at: string;
  event: EventEnvelope;
};

export type DeviceTokenRecord = {
  user_id: string;
  device_id: string;
  token_id: string;
  status: "revoked";
  revoked_at: string;
  reason?: string;
};

export type JobTransition = {
  status: JobStatus;
  at: string;
  message?: string;
};

export type JobRecord = {
  job_id: string;
  user_id: string;
  kind: JobKind;
  status: JobStatus;
  input: JsonObject;
  created_at: string;
  updated_at: string;
  transitions: JobTransition[];
  session_id?: string;
  modal_call_id?: string;
  report_id?: string;
  result?: JsonObject;
  error?: string;
};

export type ReportRecord = {
  report_id: string;
  user_id: string;
  kind: string;
  title: string;
  summary: string;
  payload: JsonObject;
  provenance: JsonObject;
  created_at: string;
  session_id?: string;
};

export type CloudStore = {
  syncEvent(user_id: string, device_id: string, event: EventEnvelope): { inserted: boolean; record: SyncEventRecord };
  listEvents(user_id: string): SyncEventRecord[];
  revokeDeviceToken(input: {
    user_id: string;
    device_id: string;
    token_id: string;
    revoked_at?: string;
    reason?: string;
  }): DeviceTokenRecord;
  getDeviceToken(user_id: string, device_id: string, token_id: string): DeviceTokenRecord | undefined;
  createJob(input: { user_id: string; kind: JobKind; input: JsonObject; session_id?: string }): JobRecord;
  getJob(user_id: string, job_id: string): JobRecord | undefined;
  updateJobStatus(
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
  ): JobRecord | undefined;
  createReport(input: {
    user_id: string;
    kind: string;
    title: string;
    summary: string;
    payload: JsonObject;
    provenance: JsonObject;
    session_id?: string;
  }): ReportRecord;
  listReports(user_id: string): ReportRecord[];
  getReport(user_id: string, report_id: string): ReportRecord | undefined;
};

export function isJobStatus(value: unknown): value is JobStatus {
  return typeof value === "string" && jobStatuses.includes(value as JobStatus);
}

export function isJobKind(value: unknown): value is JobKind {
  return typeof value === "string" && jobKinds.includes(value as JobKind);
}

export function isJsonObject(value: unknown): value is JsonObject {
  if (!isRecord(value)) {
    return false;
  }

  return Object.values(value).every(isJsonValue);
}

export function createCloudStore(now: () => Date = () => new Date()): CloudStore {
  return new InMemoryCloudStore(now);
}

class InMemoryCloudStore implements CloudStore {
  private readonly events = new Map<string, SyncEventRecord>();
  private readonly deviceTokens = new Map<string, DeviceTokenRecord>();
  private readonly jobs = new Map<string, JobRecord>();
  private readonly reports = new Map<string, ReportRecord>();

  constructor(private readonly now: () => Date) {}

  syncEvent(user_id: string, device_id: string, event: EventEnvelope): { inserted: boolean; record: SyncEventRecord } {
    const key = `${user_id}:${event.event_id}`;
    const existing = this.events.get(key);
    if (existing) {
      return { inserted: false, record: existing };
    }

    const record: SyncEventRecord = {
      user_id,
      device_id,
      event_id: event.event_id,
      session_id: event.session_id,
      event_type: event.event_type,
      privacy_class: event.privacy_class,
      payload: event.payload,
      received_at: this.timestamp(),
      event,
    };
    this.events.set(key, record);
    return { inserted: true, record };
  }

  listEvents(user_id: string): SyncEventRecord[] {
    return [...this.events.values()].filter((event) => event.user_id === user_id);
  }

  revokeDeviceToken(input: {
    user_id: string;
    device_id: string;
    token_id: string;
    revoked_at?: string;
    reason?: string;
  }): DeviceTokenRecord {
    const key = this.deviceTokenKey(input.user_id, input.device_id, input.token_id);
    const existing = this.deviceTokens.get(key);
    if (existing) {
      return existing;
    }

    const record: DeviceTokenRecord = {
      user_id: input.user_id,
      device_id: input.device_id,
      token_id: input.token_id,
      status: "revoked",
      revoked_at: input.revoked_at ?? this.timestamp(),
      ...(input.reason ? { reason: input.reason } : {}),
    };
    this.deviceTokens.set(key, record);
    return record;
  }

  getDeviceToken(user_id: string, device_id: string, token_id: string): DeviceTokenRecord | undefined {
    return this.deviceTokens.get(this.deviceTokenKey(user_id, device_id, token_id));
  }

  createJob(input: { user_id: string; kind: JobKind; input: JsonObject; session_id?: string }): JobRecord {
    const created_at = this.timestamp();
    const job: JobRecord = {
      job_id: newId("job"),
      user_id: input.user_id,
      kind: input.kind,
      status: "submitted",
      input: input.input,
      created_at,
      updated_at: created_at,
      transitions: [{ status: "submitted", at: created_at }],
      ...(input.session_id ? { session_id: input.session_id } : {}),
    };
    this.jobs.set(this.jobKey(input.user_id, job.job_id), job);
    return clone(job);
  }

  getJob(user_id: string, job_id: string): JobRecord | undefined {
    const job = this.jobs.get(this.jobKey(user_id, job_id));
    return job ? clone(job) : undefined;
  }

  updateJobStatus(
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
  ): JobRecord | undefined {
    const key = this.jobKey(user_id, job_id);
    const job = this.jobs.get(key);
    if (!job) {
      return undefined;
    }

    const updated_at = this.timestamp();
    const previousStatus = job.status;
    job.status = update.status;
    job.updated_at = updated_at;
    if (update.modal_call_id) {
      job.modal_call_id = update.modal_call_id;
    }
    if (update.report_id) {
      job.report_id = update.report_id;
    }
    if (update.result) {
      job.result = update.result;
    }
    if (update.error) {
      job.error = update.error;
    }
    if (previousStatus !== update.status || update.message) {
      job.transitions.push({
        status: update.status,
        at: updated_at,
        ...(update.message ? { message: update.message } : {}),
      });
    }

    return clone(job);
  }

  createReport(input: {
    user_id: string;
    kind: string;
    title: string;
    summary: string;
    payload: JsonObject;
    provenance: JsonObject;
    session_id?: string;
  }): ReportRecord {
    const report: ReportRecord = {
      report_id: newId("report"),
      user_id: input.user_id,
      kind: input.kind,
      title: input.title,
      summary: input.summary,
      payload: input.payload,
      provenance: input.provenance,
      created_at: this.timestamp(),
      ...(input.session_id ? { session_id: input.session_id } : {}),
    };
    this.reports.set(this.reportKey(input.user_id, report.report_id), report);
    return clone(report);
  }

  listReports(user_id: string): ReportRecord[] {
    return [...this.reports.values()].filter((report) => report.user_id === user_id).map((report) => clone(report));
  }

  getReport(user_id: string, report_id: string): ReportRecord | undefined {
    const report = this.reports.get(this.reportKey(user_id, report_id));
    return report ? clone(report) : undefined;
  }

  private timestamp(): string {
    return this.now().toISOString();
  }

  private deviceTokenKey(user_id: string, device_id: string, token_id: string): string {
    return `${user_id}:${device_id}:${token_id}`;
  }

  private jobKey(user_id: string, job_id: string): string {
    return `${user_id}:${job_id}`;
  }

  private reportKey(user_id: string, report_id: string): string {
    return `${user_id}:${report_id}`;
  }
}

function newId(prefix: string): string {
  return `${prefix}_${crypto.randomUUID()}`;
}

function clone<T>(value: T): T {
  return structuredClone(value);
}

function isJsonValue(value: unknown): value is JsonValue {
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
