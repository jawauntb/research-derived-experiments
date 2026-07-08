import {
  canRunModalJobPrivacyClass,
  findDesktopWindowTitleFieldPaths,
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
import type { SessionSummaryResult, SummaryClient } from "../lib/summaryClient";
import { RouteError, authenticate, isRecord, jsonResponse, readJsonObject, stringField } from "./common";

export type JobsRouteContext = {
  store: CloudStore;
  modalClient: ModalClient;
  summaryClient?: SummaryClient;
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
  const input = parseModalJobInput(kind, body.input ?? {});
  const session_id = stringField(body, "session_id", false);
  const job = await context.store.createJob({
    user_id: user.user_id,
    kind,
    input,
    ...(session_id ? { session_id } : {}),
  });

  try {
    if (kind === "session_summary" && context.summaryClient) {
      const summary = await context.summaryClient.summarizeSession({
        job_id: job.job_id,
        user_id: user.user_id,
        input,
        ...(session_id ? { session_id } : {}),
      });
      const result = sessionSummaryJobResult(job.job_id, input, summary);
      const reportInput = isRecord(result.report) ? result.report : {};
      const report = await createCloudSummaryReport(context.store, { ...job, user_id: user.user_id }, reportInput);
      const updated = await context.store.updateJobStatus(user.user_id, job.job_id, {
        status: "complete",
        report_id: report.report_id,
        result,
        message: `Completed by ${summary.provider}.`,
      });
      return jsonResponse({ job: updated ?? job }, 202);
    }

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

async function createCloudSummaryReport(
  store: CloudStore,
  job: { user_id: string; kind: JobKind; session_id?: string },
  reportInput: Record<string, unknown>,
) {
  const payload = parseJsonObject(reportInput.payload ?? {}, "result.report.payload");
  const provenance = parseJsonObject(reportInput.provenance ?? {}, "result.report.provenance");

  return store.createReport({
    user_id: job.user_id,
    kind: job.kind,
    title: "Redacted LLM session analysis",
    summary: "Cloud LLM analysis completed.",
    payload,
    provenance,
    ...(job.session_id ? { session_id: job.session_id } : {}),
  });
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

function sessionSummaryJobResult(jobId: string, input: JsonObject, summary: SessionSummaryResult): JsonObject {
  const payload = parseJsonObject(input.payload ?? {}, "input.payload");
  const inputReportId = stringField(payload, "report_id", false);
  const subjectSessionId = stringField(payload, "subject_session_id", false);
  const reportPayload: JsonObject = {
    summary_text: summary.text,
    provider: summary.provider,
    model: summary.model,
    privacy_class: "redacted-sync",
    limitations: summary.limitations,
    ...(inputReportId ? { input_report_id: inputReportId } : {}),
    ...(subjectSessionId ? { subject_session_id: subjectSessionId } : {}),
  };
  const provenance: JsonObject = {
    job_id: jobId,
    provider: summary.provider,
    model: summary.model,
    input_privacy_class: "redacted-sync",
    ...(inputReportId ? { input_report_id: inputReportId } : {}),
  };
  return {
    title: "Redacted LLM session analysis",
    summary: "Cloud LLM analysis completed.",
    report: {
      title: "Redacted LLM session analysis",
      summary: "Cloud LLM analysis completed.",
      payload: reportPayload,
      provenance,
    },
  };
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

function parseModalJobInput(kind: JobKind, value: unknown): JsonObject {
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
  rejectDesktopActivityInput(input, payload);
  rejectSensitiveFields(payload);
  const rawTextFields = privacyClass === "redacted-sync" ? findRawTextFieldPaths(payload) : [];
  if (rawTextFields.length > 0) {
    throw new RouteError(422, "privacy_rejected", "redacted-sync Modal jobs cannot include raw text/content fields", {
      fields: rawTextFields,
    });
  }
  assertSessionSummaryRedactedInput(kind, privacyClass, payload);

  return { ...input, payload };
}

function assertSessionSummaryRedactedInput(kind: JobKind, privacyClass: string, payload: JsonObject): void {
  if (kind !== "session_summary") {
    return;
  }
  if (privacyClass !== "redacted-sync") {
    throw new RouteError(422, "privacy_rejected", "session_summary jobs require redacted-sync input");
  }

  const localIdentityFields = findSensitiveFieldPaths(payload, {
    extraFieldNames: ["app_name", "appName", "bundle_id", "bundleId", "window_title", "windowTitle"],
    normalizeFieldName: normalizeSensitiveFieldName,
  });
  if (localIdentityFields.length > 0) {
    throw new RouteError(422, "privacy_rejected", "session_summary redacted payload cannot include app names, bundle ids, or window titles", {
      fields: localIdentityFields,
    });
  }

  const requiredStrings = ["report_id", "report_kind", "summary"] as const;
  for (const key of requiredStrings) {
    if (typeof payload[key] !== "string" || String(payload[key]).length === 0) {
      throw new RouteError(400, "invalid_request", `session_summary payload.${key} must be a non-empty string`);
    }
  }
  if (payload.report_kind !== "session_interpretation") {
    throw new RouteError(400, "invalid_request", "session_summary payload.report_kind must be session_interpretation");
  }

  for (const key of ["marker_count", "theme_count", "open_loop_count", "next_action_count"] as const) {
    if (typeof payload[key] !== "number" || !Number.isFinite(payload[key])) {
      throw new RouteError(400, "invalid_request", `session_summary payload.${key} must be a number`);
    }
  }
  for (const key of ["themes", "next_actions", "limitations"] as const) {
    if (!Array.isArray(payload[key])) {
      throw new RouteError(400, "invalid_request", `session_summary payload.${key} must be an array`);
    }
  }
  if (!isRecord(payload.provenance)) {
    throw new RouteError(400, "invalid_request", "session_summary payload.provenance must be an object");
  }
}

function rejectDesktopActivityInput(input: JsonObject, payload: JsonObject): void {
  const titleFields = findDesktopWindowTitleFieldPaths(payload);
  const desktopPaths = findDesktopActivityPaths({ input, payload });
  if (desktopPaths.length > 0 || titleFields.length > 0) {
    throw new RouteError(422, "privacy_rejected", "desktop activity and window-title payloads are not eligible for Modal jobs", {
      ...(desktopPaths.length > 0 ? { desktop_fields: desktopPaths } : {}),
      ...(titleFields.length > 0 ? { fields: titleFields } : {}),
    });
  }
}

function findDesktopActivityPaths(value: unknown, path = "$"): string[] {
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => findDesktopActivityPaths(item, `${path}[${index}]`));
  }

  if (!isRecord(value)) {
    return [];
  }

  const paths: string[] = [];
  if (value.source === "desktop-activity") {
    paths.push(`${path}.source`);
  }
  if (typeof value.event_type === "string" && value.event_type.startsWith("desktop.")) {
    paths.push(`${path}.event_type`);
  }

  for (const [key, child] of Object.entries(value)) {
    paths.push(...findDesktopActivityPaths(child, `${path}.${key}`));
  }
  return paths;
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
