import {
  canRunModalJobPrivacyClass,
  findSensitiveFieldPaths,
  isPrivacyClass,
  normalizeSensitiveFieldName,
  rawTextPayloadFieldNames,
  selectedTextPayloadFieldNames,
  type JsonObject,
} from "@inquiry/schema";
import type { CloudStore, JobKind, JobStatus } from "../db/schema";
import { isJobKind, isJobStatus, isJsonObject } from "../db/schema";
import type { ModalClient } from "../lib/modalClient";
import { RouteError, authenticate, isRecord, jsonResponse, readJsonObject, stringField } from "./common";

export type JobsRouteContext = {
  store: CloudStore;
  modalClient: ModalClient;
};

export async function handleJobsRoute(request: Request, url: URL, context: JobsRouteContext): Promise<Response | undefined> {
  if (url.pathname === "/jobs" && request.method === "POST") {
    return submitJob(request, context);
  }

  const statusMatch = url.pathname.match(/^\/jobs\/([^/]+)\/status$/);
  if (statusMatch && request.method === "POST") {
    return updateJob(request, context, statusMatch[1] ?? "");
  }

  const jobMatch = url.pathname.match(/^\/jobs\/([^/]+)$/);
  if (jobMatch && request.method === "GET") {
    return getJob(request, context, jobMatch[1] ?? "");
  }

  return undefined;
}

async function submitJob(request: Request, context: JobsRouteContext): Promise<Response> {
  const user = authenticate(request);
  const body = await readJsonObject(request);
  const kind = parseJobKind(body.kind);
  const input = parseModalJobInput(body.input ?? {});
  const session_id = stringField(body, "session_id", false);
  const job = await context.store.createJob({
    user_id: user.user_id,
    kind,
    input,
    ...(session_id ? { session_id } : {}),
  });

  try {
    const modalSubmission = await context.modalClient.submitJob({
      job_id: job.job_id,
      user_id: user.user_id,
      kind,
      input,
      ...(session_id ? { session_id } : {}),
    });
    const updated = await context.store.updateJobStatus(user.user_id, job.job_id, {
      status: modalSubmission.status,
      modal_call_id: modalSubmission.modal_call_id,
    });
    return jsonResponse({ job: updated ?? job }, 202);
  } catch (error) {
    const updated = await context.store.updateJobStatus(user.user_id, job.job_id, {
      status: "failed",
      error: error instanceof Error ? error.message : "Modal submission failed",
    });
    return jsonResponse({ job: updated ?? job }, 502);
  }
}

async function getJob(request: Request, context: JobsRouteContext, job_id: string): Promise<Response> {
  const user = authenticate(request);
  const job = await context.store.getJob(user.user_id, job_id);
  if (!job) {
    throw new RouteError(404, "not_found", "job was not found");
  }

  return jsonResponse({ job });
}

async function updateJob(request: Request, context: JobsRouteContext, job_id: string): Promise<Response> {
  const user = authenticate(request);
  const existing = await context.store.getJob(user.user_id, job_id);
  if (!existing) {
    throw new RouteError(404, "not_found", "job was not found");
  }

  const body = await readJsonObject(request);
  const status = parseJobStatus(body.status);
  const parsedResult = body.result === undefined ? undefined : parseJsonObject(body.result, "result");
  const result = parsedResult ? sanitizeJobResult(existing.kind, parsedResult) : undefined;
  const error = stringField(body, "error", false);
  if (result) {
    rejectSensitiveFields(result, [...selectedTextPayloadFieldNames, ...rawTextPayloadFieldNames]);
  }

  let report_id: string | undefined = existing.report_id;
  if (status === "complete" && result && isRecord(result.report)) {
    if (!report_id) {
      const report = await createReportFromJobResult(context.store, existing, result.report);
      report_id = report.report_id;
    }
  }

  const updated = await context.store.updateJobStatus(user.user_id, job_id, {
    status,
    ...(report_id ? { report_id } : {}),
    ...(result ? { result } : {}),
    ...(error ? { error } : {}),
  });

  return jsonResponse({ job: updated });
}

async function createReportFromJobResult(
  store: CloudStore,
  job: { user_id: string; kind: JobKind; session_id?: string },
  reportInput: Record<string, unknown>,
) {
  const title = modalReportTitle(job.kind);
  const summary = modalReportSummary();
  const payload = parseJsonObject(reportInput.payload ?? {}, "result.report.payload");
  const provenance = parseJsonObject(reportInput.provenance ?? {}, "result.report.provenance");

  return store.createReport({
    user_id: job.user_id,
    kind: job.kind,
    title,
    summary,
    payload,
    provenance,
    ...(job.session_id ? { session_id: job.session_id } : {}),
  });
}

function modalReportTitle(kind: JobKind): string {
  return `Modal ${kind.replaceAll("_", " ")} report`;
}

function modalReportSummary(): string {
  return "Modal report completed.";
}

function sanitizeJobResult(kind: JobKind, result: JsonObject): JsonObject {
  const sanitized: JsonObject = { ...result };
  if (typeof sanitized.title === "string") {
    sanitized.title = modalReportTitle(kind);
  }
  if (typeof sanitized.summary === "string") {
    sanitized.summary = modalReportSummary();
  }

  const report = result.report;
  if (!isRecord(report)) {
    return sanitized;
  }

  sanitized.report = {
    ...(report as JsonObject),
    title: modalReportTitle(kind),
    summary: modalReportSummary(),
  };
  return sanitized;
}

function parseJobKind(value: unknown): JobKind {
  if (!isJobKind(value)) {
    throw new RouteError(400, "invalid_request", "kind must be one of content_difficulty, embedding, session_summary, calibration");
  }
  return value;
}

function parseJobStatus(value: unknown): JobStatus {
  if (!isJobStatus(value)) {
    throw new RouteError(400, "invalid_request", "status must be one of submitted, running, complete, failed");
  }
  return value;
}

function parseJsonObject(value: unknown, field: string): JsonObject {
  if (!isJsonObject(value)) {
    throw new RouteError(400, "invalid_request", `${field} must be a JSON object`);
  }
  return value;
}

function parseModalJobInput(value: unknown): JsonObject {
  const input = parseJsonObject(value, "input");
  const privacyClass = input.privacy_class;
  if (!isPrivacyClass(privacyClass)) {
    throw new RouteError(400, "invalid_request", "input.privacy_class must be a supported privacy class");
  }

  const decision = canRunModalJobPrivacyClass(privacyClass);
  if (!decision.allowed) {
    throw new RouteError(422, "privacy_rejected", decision.reason);
  }

  const payload = parseJsonObject(input.payload ?? {}, "input.payload");
  rejectSensitiveFields(payload);
  const rawTextFields = privacyClass === "redacted-sync" ? findRawTextFieldPaths(payload) : [];
  if (rawTextFields.length > 0) {
    throw new RouteError(422, "privacy_rejected", "redacted-sync Modal jobs cannot include raw text/content fields", {
      fields: rawTextFields,
    });
  }

  return { ...input, payload };
}

const redactedModalRawTextFieldNames = [...rawTextPayloadFieldNames, "page_text"] as const;

function findRawTextFieldPaths(value: unknown): string[] {
  return findSensitiveFieldPaths(value, {
    extraFieldNames: redactedModalRawTextFieldNames,
    normalizeFieldName: normalizeSensitiveFieldName,
  });
}

function rejectSensitiveFields(value: unknown, extraFieldNames: Iterable<string> = []): void {
  const paths = findSensitiveFieldPaths(value, {
    extraFieldNames,
    normalizeFieldName: normalizeSensitiveFieldName,
  });
  if (paths.length > 0) {
    throw new RouteError(422, "privacy_rejected", "payload contains sensitive fields that cannot be sent to cloud analysis", {
      fields: paths,
    });
  }
}
