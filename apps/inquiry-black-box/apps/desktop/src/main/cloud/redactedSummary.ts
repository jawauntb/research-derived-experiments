import { execFileSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import { homedir } from "node:os";
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

export type RedactedSummarySubmissionStatus = "submitted" | "complete" | "blocked" | "unavailable" | "failed";

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
  geminiApiKey?: string;
  geminiApiBaseUrl?: string;
  disableDopplerGemini?: boolean;
  dopplerProject?: string;
  dopplerConfig?: string;
  dopplerCommand?: string;
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
  const providerPreference = options.provider ?? process.env.MODEL_PROVIDER;

  if (!settings.cloudSync) {
    return appendRun(database, {
      sessionId,
      runId,
      provider: providerPreference ?? "modal",
      model: options.model ?? process.env.SESSION_SUMMARY_MODEL ?? "redacted-session-summary",
      status: "unavailable",
      message: "Cloud sync is off. Enable Cloud sync before requesting a redacted LLM summary.",
      limitations: ["No cloud, Modal, or Gemini request was made.", "Local interpretation remains available."],
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
  const wantsGemini = isGeminiProvider(providerPreference) || (!cloudApiUrl || !bearerToken);
  const geminiApiKey = wantsGemini ? resolveGeminiApiKey(options) : undefined;

  if (wantsGemini && geminiApiKey) {
    const model = options.model ?? process.env.SESSION_SUMMARY_MODEL ?? process.env.GEMINI_MODEL_JUDGE ?? "gemini-2.0-flash";
    return requestGeminiSummary(database, {
      sessionId,
      runId,
      inputReportId: interpretation.report_id,
      input,
      apiKey: geminiApiKey,
      model,
      fetchImpl: options.fetchImpl ?? fetch,
      timeoutMs: options.timeoutMs ?? 10_000,
      ...(options.geminiApiBaseUrl ? { baseUrl: options.geminiApiBaseUrl } : {}),
    });
  }

  if (!cloudApiUrl || !bearerToken) {
    return appendRun(database, {
      sessionId,
      runId,
      provider: isGeminiProvider(providerPreference) ? "gemini" : providerPreference ?? "modal",
      model:
        isGeminiProvider(providerPreference)
          ? options.model ?? process.env.SESSION_SUMMARY_MODEL ?? process.env.GEMINI_MODEL_JUDGE ?? "gemini-2.0-flash"
          : options.model ?? process.env.SESSION_SUMMARY_MODEL ?? "redacted-session-summary",
      status: "unavailable",
      inputReportId: interpretation.report_id,
      message: isGeminiProvider(providerPreference)
        ? "Gemini API key is not configured."
        : "Cloud job endpoint/auth token or Gemini API key is not configured.",
      limitations: ["Generated the redacted job input locally.", "No cloud, Modal, or Gemini request was made."],
      submissionStatus: "unavailable",
    });
  }

  const provider = providerPreference ?? "modal";
  const model = options.model ?? process.env.SESSION_SUMMARY_MODEL ?? "redacted-session-summary";

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

async function requestGeminiSummary(
  database: InquiryDatabase,
  input: {
    sessionId: string;
    runId: string;
    inputReportId: string;
    input: JsonObject;
    apiKey: string;
    model: string;
    fetchImpl: FetchLike;
    baseUrl?: string;
    timeoutMs: number;
  },
): Promise<RedactedSummarySubmission> {
  try {
    const response = await fetchWithTimeout(
      input.fetchImpl,
      geminiGenerateContentUrl(input.model, input.baseUrl),
      {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-goog-api-key": input.apiKey,
        },
        body: JSON.stringify(geminiSummaryRequestBody(input.input)),
      },
      input.timeoutMs,
    );
    const body = (await response.json().catch(() => ({}))) as Record<string, unknown>;
    if (!response.ok) {
      return appendRun(database, {
        sessionId: input.sessionId,
        runId: input.runId,
        provider: "gemini",
        model: input.model,
        status: "failed",
        inputReportId: input.inputReportId,
        message: `Gemini summary request failed with status ${response.status}.`,
        limitations: [errorMessage(body), "The submitted payload was redacted-sync only."],
        submissionStatus: "failed",
      });
    }

    const text = geminiText(body);
    if (!text) {
      return appendRun(database, {
        sessionId: input.sessionId,
        runId: input.runId,
        provider: "gemini",
        model: input.model,
        status: "failed",
        inputReportId: input.inputReportId,
        message: "Gemini summary response did not include text.",
        limitations: ["The submitted payload was redacted-sync only."],
        submissionStatus: "failed",
      });
    }

    return appendRun(database, {
      sessionId: input.sessionId,
      runId: input.runId,
      provider: "gemini",
      model: input.model,
      status: "complete",
      inputReportId: input.inputReportId,
      message: text,
      limitations: ["Generated by Gemini from redacted session interpretation counts, themes, actions, and limitations only."],
      submissionStatus: "complete",
    });
  } catch (error) {
    return appendRun(database, {
      sessionId: input.sessionId,
      runId: input.runId,
      provider: "gemini",
      model: input.model,
      status: "failed",
      inputReportId: input.inputReportId,
      message: "Gemini summary request failed before completion.",
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

function resolveGeminiApiKey(options: RedactedSummaryOptions): string | undefined {
  const explicit = stringValue(options.geminiApiKey);
  if (explicit) {
    return explicit;
  }

  const envKey = stringValue(process.env.GEMINI_API_KEY) ?? stringValue(process.env.GOOGLE_API_KEY);
  if (envKey || options.disableDopplerGemini) {
    return envKey;
  }

  return resolveDopplerSecret("GEMINI_API_KEY", options) ?? resolveDopplerSecret("GOOGLE_API_KEY", options);
}

function resolveDopplerSecret(key: string, options: RedactedSummaryOptions): string | undefined {
  const project = options.dopplerProject ?? process.env.INQUIRY_DOPPLER_PROJECT ?? "cofounder";
  const config = options.dopplerConfig ?? process.env.INQUIRY_DOPPLER_CONFIG ?? "prd_superoptimizers";
  const commands = uniqueStrings([
    options.dopplerCommand,
    process.env.INQUIRY_DOPPLER_COMMAND,
    `${homedir()}/.local/bin/doppler`,
    "/opt/homebrew/bin/doppler",
    "/usr/local/bin/doppler",
    "doppler",
  ]);

  for (const command of commands) {
    try {
      const output = execFileSync(
        command,
        ["run", "--project", project, "--config", config, "--", "printenv", key],
        {
          encoding: "utf8",
          stdio: ["ignore", "pipe", "ignore"],
          timeout: 2_500,
        },
      ).trim();
      if (output.length > 0) {
        return output;
      }
    } catch {
      // Keep the summary path usable when Doppler is unavailable or unconfigured.
    }
  }

  return undefined;
}

function normalizeCloudApiUrl(value: string | undefined): string | undefined {
  if (!value) {
    return undefined;
  }
  return value.replace(/\/+$/, "");
}

function geminiGenerateContentUrl(model: string, baseUrl = "https://generativelanguage.googleapis.com/v1beta"): string {
  const normalizedBase = baseUrl.replace(/\/+$/, "");
  const normalizedModel = model.startsWith("models/") || model.startsWith("tunedModels/") ? model : `models/${model}`;
  return `${normalizedBase}/${normalizedModel}:generateContent`;
}

function geminiSummaryRequestBody(input: JsonObject): JsonObject {
  return {
    contents: [
      {
        role: "user",
        parts: [
          {
            text: [
              "Summarize this Inquiry Black Box session using only the redacted JSON below.",
              "Do not infer identities, diagnoses, hidden mental states, raw page text, typed text, or window titles.",
              "Return concise plain text: one evidence-grounded summary sentence and up to two next actions.",
              "",
              JSON.stringify({
                kind: "session_summary",
                privacy_class: "redacted-sync",
                input,
              }),
            ].join("\n"),
          },
        ],
      },
    ],
    generationConfig: {
      temperature: 0.2,
      maxOutputTokens: 384,
    },
  };
}

function geminiText(body: Record<string, unknown>): string | undefined {
  const candidates = Array.isArray(body.candidates) ? body.candidates : [];
  for (const candidate of candidates) {
    const content = isRecord(candidate) && isRecord(candidate.content) ? candidate.content : {};
    const parts = Array.isArray(content.parts) ? content.parts : [];
    const text = parts
      .map((part) => (isRecord(part) && typeof part.text === "string" ? part.text : ""))
      .join("")
      .trim();
    if (text.length > 0) {
      return text;
    }
  }

  return undefined;
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

function isGeminiProvider(value: unknown): boolean {
  return value === "gemini" || value === "google" || value === "google-gemini";
}

function uniqueStrings(values: Array<string | undefined>): string[] {
  return [...new Set(values.filter((value): value is string => typeof value === "string" && value.length > 0))];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
