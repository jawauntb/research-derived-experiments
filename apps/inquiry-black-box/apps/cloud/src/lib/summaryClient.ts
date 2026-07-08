import type { JsonObject, PrivacyClass } from "@inquiry/schema";

export type SessionSummaryRequest = {
  job_id: string;
  user_id: string;
  input: JsonObject;
  session_id?: string;
};

export type SessionSummaryProvider = "openai" | "gemini";

export type SessionSummaryResult = {
  provider: SessionSummaryProvider;
  model: string;
  text: string;
  limitations: string[];
};

export type SummaryClient = {
  summarizeSession(request: SessionSummaryRequest): Promise<SessionSummaryResult>;
};

export type SummaryClientOptions = {
  fetchImpl?: FetchLike;
  timeoutMs?: number;
};

type FetchLike = (url: string, init?: RequestInit) => Promise<Response>;

export function createSummaryClientFromEnv(
  env: Record<string, string | undefined> = process.env,
  options: SummaryClientOptions = {},
): SummaryClient | undefined {
  const fetchImpl = options.fetchImpl ?? fetch;
  const timeoutMs = options.timeoutMs ?? Number(env.SESSION_SUMMARY_TIMEOUT_MS ?? 10_000);
  const provider = normalizedProvider(env.MODEL_PROVIDER);
  const openAiKey = stringValue(env.OPENAI_API_KEY);
  const geminiKey = stringValue(env.GEMINI_API_KEY) ?? stringValue(env.GOOGLE_API_KEY);
  const openAiBaseUrl = env.OPENAI_API_BASE_URL ?? env.OPENAI_BASE_URL;
  const geminiBaseUrl = env.GEMINI_API_BASE_URL;

  if ((provider === "openai" || !provider) && openAiKey) {
    return new OpenAiSummaryClient({
      apiKey: openAiKey,
      model: openAiSessionSummaryModel(env),
      maxOutputTokens: openAiSessionSummaryMaxOutputTokens(env),
      fetchImpl,
      timeoutMs,
      ...(openAiBaseUrl ? { baseUrl: openAiBaseUrl } : {}),
    });
  }

  if ((provider === "gemini" || !provider) && geminiKey) {
    return new GeminiSummaryClient({
      apiKey: geminiKey,
      model: geminiSessionSummaryModel(env),
      maxOutputTokens: geminiSessionSummaryMaxOutputTokens(env),
      fetchImpl,
      timeoutMs,
      ...(geminiBaseUrl ? { baseUrl: geminiBaseUrl } : {}),
    });
  }

  return undefined;
}

type OpenAiSummaryClientOptions = {
  apiKey: string;
  model: string;
  maxOutputTokens: number;
  baseUrl?: string;
  fetchImpl: FetchLike;
  timeoutMs: number;
};

export class OpenAiSummaryClient implements SummaryClient {
  constructor(private readonly options: OpenAiSummaryClientOptions) {}

  async summarizeSession(request: SessionSummaryRequest): Promise<SessionSummaryResult> {
    const response = await fetchWithTimeout(
      this.options.fetchImpl,
      openAiResponsesUrl(this.options.baseUrl),
      {
        method: "POST",
        headers: {
          authorization: `Bearer ${this.options.apiKey}`,
          "content-type": "application/json",
        },
        body: JSON.stringify(openAiSessionSummaryBody(this.options.model, request.input, this.options.maxOutputTokens)),
      },
      this.options.timeoutMs,
    );
    const body = (await response.json().catch(() => ({}))) as Record<string, unknown>;
    if (!response.ok) {
      throw new Error(`OpenAI analysis request failed with status ${response.status}: ${providerErrorMessage(body)}`);
    }

    const text = openAiOutputText(body);
    if (!text) {
      throw new Error("OpenAI analysis response did not include text");
    }

    return {
      provider: "openai",
      model: this.options.model,
      text,
      limitations: [providerPayloadLimitation("OpenAI", sessionSummaryInputPrivacyClass(request.input))],
    };
  }
}

type GeminiSummaryClientOptions = {
  apiKey: string;
  model: string;
  maxOutputTokens: number;
  baseUrl?: string;
  fetchImpl: FetchLike;
  timeoutMs: number;
};

export class GeminiSummaryClient implements SummaryClient {
  constructor(private readonly options: GeminiSummaryClientOptions) {}

  async summarizeSession(request: SessionSummaryRequest): Promise<SessionSummaryResult> {
    const response = await fetchWithTimeout(
      this.options.fetchImpl,
      geminiGenerateContentUrl(this.options.model, this.options.baseUrl),
      {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-goog-api-key": this.options.apiKey,
        },
        body: JSON.stringify(geminiSessionSummaryBody(request.input, this.options.maxOutputTokens)),
      },
      this.options.timeoutMs,
    );
    const body = (await response.json().catch(() => ({}))) as Record<string, unknown>;
    if (!response.ok) {
      throw new Error(`Gemini analysis request failed with status ${response.status}: ${providerErrorMessage(body)}`);
    }

    const text = geminiOutputText(body);
    if (!text) {
      throw new Error("Gemini analysis response did not include text");
    }

    return {
      provider: "gemini",
      model: this.options.model,
      text,
      limitations: [providerPayloadLimitation("Gemini", sessionSummaryInputPrivacyClass(request.input))],
    };
  }
}

export function openAiSessionSummaryModel(env: Record<string, string | undefined> = process.env): string {
  return (
    stringValue(env.OPENAI_SESSION_SUMMARY_MODEL) ??
    stringValue(env.OPENAI_MODEL) ??
    openAiCompatibleSessionModel(env.SESSION_SUMMARY_MODEL) ??
    "gpt-5.5"
  );
}

export function openAiSessionSummaryMaxOutputTokens(env: Record<string, string | undefined> = process.env): number {
  return summaryMaxOutputTokens(env.OPENAI_SESSION_SUMMARY_MAX_OUTPUT_TOKENS ?? env.SESSION_SUMMARY_MAX_OUTPUT_TOKENS);
}

export function geminiSessionSummaryModel(env: Record<string, string | undefined> = process.env): string {
  return (
    stringValue(env.GEMINI_SESSION_SUMMARY_MODEL) ??
    stringValue(env.GEMINI_MODEL_JUDGE) ??
    geminiCompatibleSessionModel(env.SESSION_SUMMARY_MODEL) ??
    "gemini-2.5-flash"
  );
}

export function geminiSessionSummaryMaxOutputTokens(env: Record<string, string | undefined> = process.env): number {
  return summaryMaxOutputTokens(env.GEMINI_SESSION_SUMMARY_MAX_OUTPUT_TOKENS ?? env.SESSION_SUMMARY_MAX_OUTPUT_TOKENS);
}

function openAiCompatibleSessionModel(value: string | undefined): string | undefined {
  return value && /^gpt-|^o[0-9]/.test(value) ? value : undefined;
}

function geminiCompatibleSessionModel(value: string | undefined): string | undefined {
  return value && /^gemini[-/]/.test(value) ? value : undefined;
}

function openAiResponsesUrl(baseUrl = "https://api.openai.com/v1"): string {
  return `${baseUrl.replace(/\/+$/, "")}/responses`;
}

function openAiSessionSummaryBody(model: string, input: JsonObject, maxOutputTokens: number): JsonObject {
  return {
    model,
    instructions: sessionSummaryInstructions(sessionSummaryInputPrivacyClass(input)),
    input: sessionSummaryPromptInput(input),
    max_output_tokens: maxOutputTokens,
  };
}

function geminiGenerateContentUrl(model: string, baseUrl = "https://generativelanguage.googleapis.com/v1beta"): string {
  const normalizedBase = baseUrl.replace(/\/+$/, "");
  const normalizedModel = model.startsWith("models/") || model.startsWith("tunedModels/") ? model : `models/${model}`;
  return `${normalizedBase}/${normalizedModel}:generateContent`;
}

function geminiSessionSummaryBody(input: JsonObject, maxOutputTokens: number): JsonObject {
  return {
    contents: [
      {
        role: "user",
        parts: [{ text: `${sessionSummaryInstructions(sessionSummaryInputPrivacyClass(input))}\n\n${sessionSummaryPromptInput(input)}` }],
      },
    ],
    generationConfig: {
      maxOutputTokens,
    },
  };
}

function sessionSummaryInstructions(privacyClass: PrivacyClass): string {
  if (privacyClass === "document-opt-in") {
    return [
      "Analyze this Inquiry Black Box session using the document-opt-in JSON below.",
      "You may use bounded reading/selected text snippets and the user's additional context when present.",
      "Do not infer identities, diagnoses, hidden mental states, typed text, app identities, or window titles.",
      "Return concise plain text: one evidence-grounded analysis sentence and up to two follow-up questions or next actions the user can answer from their data.",
    ].join("\n");
  }

  return [
    "Analyze this Inquiry Black Box session using only the redacted JSON below.",
    "Do not infer identities, diagnoses, hidden mental states, raw page text, typed text, selected text, app identities, or window titles.",
    "Return concise plain text: one evidence-grounded analysis sentence and up to two follow-up questions or next actions the user can answer from their data.",
  ].join("\n");
}

function sessionSummaryPromptInput(input: JsonObject): string {
  const privacyClass = sessionSummaryInputPrivacyClass(input);
  return JSON.stringify({
    kind: "session_summary",
    privacy_class: privacyClass,
    input,
  });
}

function sessionSummaryInputPrivacyClass(input: JsonObject): PrivacyClass {
  return input.privacy_class === "document-opt-in" ? "document-opt-in" : "redacted-sync";
}

function providerPayloadLimitation(provider: "OpenAI" | "Gemini", privacyClass: PrivacyClass): string {
  if (privacyClass === "document-opt-in") {
    return `Generated by ${provider} from document-opt-in session interpretation plus bounded reading/selection snippets and optional user context.`;
  }

  return `Generated by ${provider} from redacted session interpretation counts, themes, actions, and limitations only.`;
}

function openAiOutputText(body: Record<string, unknown>): string | undefined {
  const shortcut = stringValue(body.output_text);
  if (shortcut) {
    return shortcut.trim();
  }

  const output = Array.isArray(body.output) ? body.output : [];
  const text = output
    .flatMap((item) => (isRecord(item) && Array.isArray(item.content) ? item.content : []))
    .map((part) => (isRecord(part) && typeof part.text === "string" ? part.text : ""))
    .join("")
    .trim();
  return text.length > 0 ? text : undefined;
}

function geminiOutputText(body: Record<string, unknown>): string | undefined {
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
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetchImpl(url, { ...init, signal: controller.signal });
  } catch (error) {
    if (controller.signal.aborted) {
      throw new Error(`summary request timed out after ${timeoutMs}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

function providerErrorMessage(value: Record<string, unknown>): string {
  const error = isRecord(value.error) ? value.error : {};
  return typeof error.message === "string" ? error.message : "provider rejected the summary request";
}

function normalizedProvider(value: string | undefined): SessionSummaryProvider | undefined {
  if (value === "openai") {
    return "openai";
  }
  if (value === "gemini" || value === "google" || value === "google-gemini") {
    return "gemini";
  }
  return undefined;
}

function summaryMaxOutputTokens(value: string | undefined): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : 2_000;
}

function stringValue(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
