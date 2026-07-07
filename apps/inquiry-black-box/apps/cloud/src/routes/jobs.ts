import type { CloudStore, JobKind, JobStatus } from "../db/schema";
import { findSensitiveFieldPaths, isJobKind, isJobStatus, isJsonObject } from "../db/schema";
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
  const input = parseJsonObject(body.input ?? {}, "input");
  rejectSensitiveFields(input);
  const session_id = stringField(body, "session_id", false);
  const job = context.store.createJob({
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
    const updated = context.store.updateJobStatus(user.user_id, job.job_id, {
      status: modalSubmission.status,
      modal_call_id: modalSubmission.modal_call_id,
    });
    return jsonResponse({ job: updated ?? job }, 202);
  } catch (error) {
    const updated = context.store.updateJobStatus(user.user_id, job.job_id, {
      status: "failed",
      error: error instanceof Error ? error.message : "Modal submission failed",
    });
    return jsonResponse({ job: updated ?? job }, 502);
  }
}

async function getJob(request: Request, context: JobsRouteContext, job_id: string): Promise<Response> {
  const user = authenticate(request);
  const job = context.store.getJob(user.user_id, job_id);
  if (!job) {
    throw new RouteError(404, "not_found", "job was not found");
  }

  return jsonResponse({ job });
}

async function updateJob(request: Request, context: JobsRouteContext, job_id: string): Promise<Response> {
  const user = authenticate(request);
  const existing = context.store.getJob(user.user_id, job_id);
  if (!existing) {
    throw new RouteError(404, "not_found", "job was not found");
  }

  const body = await readJsonObject(request);
  const status = parseJobStatus(body.status);
  const result = body.result === undefined ? undefined : parseJsonObject(body.result, "result");
  const error = stringField(body, "error", false);
  if (result) {
    rejectSensitiveFields(result);
  }

  let report_id: string | undefined;
  if (status === "complete" && result && isRecord(result.report)) {
    const report = createReportFromJobResult(context.store, existing, result.report);
    report_id = report.report_id;
  }

  const updated = context.store.updateJobStatus(user.user_id, job_id, {
    status,
    ...(report_id ? { report_id } : {}),
    ...(result ? { result } : {}),
    ...(error ? { error } : {}),
  });

  return jsonResponse({ job: updated });
}

function createReportFromJobResult(
  store: CloudStore,
  job: { user_id: string; kind: JobKind; session_id?: string },
  reportInput: Record<string, unknown>,
) {
  const title = typeof reportInput.title === "string" && reportInput.title.length > 0 ? reportInput.title : "Modal report";
  const summary = typeof reportInput.summary === "string" ? reportInput.summary : "";
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

function parseJsonObject(value: unknown, field: string) {
  if (!isJsonObject(value)) {
    throw new RouteError(400, "invalid_request", `${field} must be a JSON object`);
  }
  return value;
}

function rejectSensitiveFields(value: unknown): void {
  const paths = findSensitiveFieldPaths(value);
  if (paths.length > 0) {
    throw new RouteError(422, "privacy_rejected", "payload contains sensitive fields that cannot be sent to cloud analysis", {
      fields: paths,
    });
  }
}
