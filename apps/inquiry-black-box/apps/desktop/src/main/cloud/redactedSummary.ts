import { randomUUID } from "node:crypto";
import {
  assertNoBlockedPayload,
  type EventEnvelope,
  type JsonObject,
  type ModelRunPayload,
  type ModelRunStatus,
} from "@inquiry/schema";
import { createModelRunEvent, redactedSessionSummaryJobInput } from "@inquiry/signals";
import type { InquiryDatabase } from "../db";
import { createSessionInterpretationReport } from "../reports/sessionInterpretation";

export type RedactedSummarySubmissionStatus = "submitted" | "blocked" | "unavailable" | "failed";

export type RedactedSummarySubmission = {
  status: RedactedSummarySubmissionStatus;
  run_id: string;
  session_id: string;
  input_report_id?: string;
  job_id?: string;
  modal_call_id?: string;
  message: string;
  limitations: string[];
};

export type RedactedSummaryOptions = {
  cloudApiUrl?: string;
  bearerToken?: string;
  fetchImpl?: FetchLike;
  provider?: string;
  model?: string;
  nowMs?: () => number;
  timeoutMs?: number;
};

type FetchLike = (url: string, init?: RequestInit) => Promise<Response>;

export async function requestRedactedSessionSummary(
  database: InquiryDatabase,
  sessionId: string,
  options: RedactedSummaryOptions = {},
): Promise<RedactedSummarySubmission> {
  const settings = database.signalSettings();
  const nowMs = options.nowMs ?? (() => Date.now());
  const runId = `session-summary:${sessionId}:${nowMs()}:${randomUUID()}`;
  const provider = options.provider ?? process.env.MODEL_PROVIDER ?? "modal";
  const model = options.model ?? process.env.SESSION_SUMMARY_MODEL ?? "redacted-session-summary";

  if (!settings.cloudSync) {
    return appendRun(database, {
      sessionId,
      runId,
      provider,
      model,
      status: "unavailable",
      message: "Cloud sync is off. Enable Cloud sync before requesting a redacted LLM summary.",
      limitations: ["No cloud or Modal request was made.", "Local interpretation remains available."],
      submissionStatus: "blocked",
    });
  }

  const cloudApiUrl = normalizeCloudApiUrl(options.cloudApiUrl ?? process.env.INQUIRY_CLOUD_API_URL ?? process.env.RAILWAY_PUBLIC_API_URL);
  const bearerToken =
    options.bearerToken ??
    process.env.INQUIRY_CLOUD_BEARER_TOKEN ??
    process.env.INQUIRY_CLOUD_AUTH_TOKEN;
  const interpretation = createSessionInterpretationReport(database, sessionId);
  const input = redactedSessionSummaryJobInput(interpretation);
  assertRedactedInput(input);

  if (!cloudApiUrl || !bearerToken) {
    return appendRun(database, {
      sessionId,
      runId,
      provider,
      model,
      status: "unavailable",
      inputReportId: interpretation.report_id,
      message: "Cloud job endpoint or auth token is not configured.",
      limitations: ["Generated the redacted job input locally.", "No cloud or Modal request was made."],
      submissionStatus: "unavailable",
    });
  }

  try {
    const response = await fetchWithTimeout(
      options.fetchImpl ?? fetch,
      `${cloudApiUrl}/jobs`,
      {
        method: "POST",
        headers: {
          authorization: `Bearer ${bearerToken}`,
          "content-type": "application/json",
        },
        body: JSON.stringify({
          kind: "session_summary",
          session_id: sessionId,
          input,
        }),
      },
      options.timeoutMs ?? 10_000,
    );
    const body = (await response.json().catch(() => ({}))) as Record<string, unknown>;
    const job = isRecord(body.job) ? body.job : {};
    if (!response.ok) {
      return appendRun(database, {
        sessionId,
        runId,
        provider,
        model,
        status: "failed",
        inputReportId: interpretation.report_id,
        message: `Cloud job request failed with status ${response.status}.`,
        limitations: [errorMessage(body), "The submitted payload was redacted-sync only."],
        submissionStatus: "failed",
      });
    }

    const jobId = stringValue(job.job_id);
    const modalCallId = stringValue(job.modal_call_id);
    return appendRun(database, {
      sessionId,
      runId,
      provider,
      model,
      status: modelRunStatus(job.status),
      inputReportId: interpretation.report_id,
      message: "Redacted LLM summary job submitted.",
      limitations: ["Submitted only redacted session interpretation counts, themes, actions, and limitations."],
      submissionStatus: "submitted",
      ...(jobId ? { jobId } : {}),
      ...(modalCallId ? { modalCallId } : {}),
    });
  } catch (error) {
    return appendRun(database, {
      sessionId,
      runId,
      provider,
      model,
      status: "failed",
      inputReportId: interpretation.report_id,
      message: "Cloud job request failed before submission completed.",
      limitations: [error instanceof Error ? error.message : String(error)],
      submissionStatus: "failed",
    });
  }
}

function appendRun(
  database: InquiryDatabase,
  input: {
    sessionId: string;
    runId: string;
    provider: string;
    model: string;
    status: ModelRunStatus;
    inputReportId?: string;
    jobId?: string;
    modalCallId?: string;
    message: string;
    limitations: string[];
    submissionStatus: RedactedSummarySubmissionStatus;
  },
): RedactedSummarySubmission {
  const payload: ModelRunPayload = {
    run_id: input.runId,
    job_kind: "session_summary",
    provider: input.provider,
    model: input.model,
    status: input.status,
    input_privacy_class: "redacted-sync",
    limitations: input.limitations,
    ...(input.inputReportId ? { input_report_id: input.inputReportId } : {}),
  };
  const event: EventEnvelope<ModelRunPayload> = createModelRunEvent(input.sessionId, payload, {
    event_id: `model-run:${input.runId}`,
    source: "desktop-system",
    source_version: "desktop@0.1.0",
    monotonic_ms: Date.now(),
  });
  database.appendEventIfNew(event);

  return {
    status: input.submissionStatus,
    run_id: input.runId,
    session_id: input.sessionId,
    message: input.message,
    limitations: input.limitations,
    ...(input.inputReportId ? { input_report_id: input.inputReportId } : {}),
    ...(input.jobId ? { job_id: input.jobId } : {}),
    ...(input.modalCallId ? { modal_call_id: input.modalCallId } : {}),
  };
}

function assertRedactedInput(input: JsonObject): void {
  if (input.privacy_class !== "redacted-sync") {
    throw new Error("redacted summary input must use redacted-sync privacy class");
  }
  const payload = isRecord(input.payload) ? input.payload : {};
  assertNoBlockedPayload(payload);
  const serialized = JSON.stringify(payload);
  for (const blocked of ["app_name", "bundle_id", "window_title", "selected_text", "typed_text", "page_text"]) {
    if (serialized.includes(blocked)) {
      throw new Error(`redacted summary input contains blocked field: ${blocked}`);
    }
  }
}

function normalizeCloudApiUrl(value: string | undefined): string | undefined {
  if (!value) {
    return undefined;
  }
  return value.replace(/\/+$/, "");
}

async function fetchWithTimeout(fetchImpl: FetchLike, url: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  let timeout: ReturnType<typeof setTimeout> | undefined;
  const timeoutPromise = new Promise<Response>((_resolve, reject) => {
    timeout = setTimeout(() => {
      controller.abort();
      reject(new Error(`cloud job request timed out after ${timeoutMs}ms`));
    }, timeoutMs);
  });

  try {
    return await Promise.race([fetchImpl(url, { ...init, signal: controller.signal }), timeoutPromise]);
  } finally {
    if (timeout) {
      clearTimeout(timeout);
    }
  }
}

function modelRunStatus(value: unknown): ModelRunStatus {
  return value === "running" || value === "complete" || value === "failed" ? value : "submitted";
}

function errorMessage(value: Record<string, unknown>): string {
  const error = isRecord(value.error) ? value.error : {};
  return typeof error.message === "string" ? error.message : "Cloud rejected the job request.";
}

function stringValue(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
