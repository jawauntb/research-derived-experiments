import type { JsonObject } from "@inquiry/schema";
import type { JobKind, JobStatus } from "../db/schema";
import { isJobStatus } from "../db/schema";

export type ModalJobRequest = {
  job_id: string;
  user_id: string;
  kind: JobKind;
  input: JsonObject;
  session_id?: string;
};

export type ModalJobSubmission = {
  modal_call_id: string;
  status: JobStatus;
};

export type ModalClient = {
  submitJob(request: ModalJobRequest): Promise<ModalJobSubmission>;
};

export class LocalModalClient implements ModalClient {
  async submitJob(request: ModalJobRequest): Promise<ModalJobSubmission> {
    return {
      modal_call_id: `local-modal-${request.job_id}`,
      status: "submitted",
    };
  }
}

export class HttpModalClient implements ModalClient {
  constructor(
    private readonly endpoint: string,
    private readonly bearerToken?: string,
    private readonly timeoutMs = 10_000,
  ) {}

  async submitJob(request: ModalJobRequest): Promise<ModalJobSubmission> {
    const headers = new Headers({ "content-type": "application/json" });
    if (this.bearerToken) {
      headers.set("authorization", `Bearer ${this.bearerToken}`);
    }

    const response = await fetchWithTimeout(
      this.endpoint,
      {
        method: "POST",
        headers,
        body: JSON.stringify(request),
      },
      this.timeoutMs,
    );
    if (!response.ok) {
      throw new Error(`Modal job submission failed with HTTP ${response.status}`);
    }

    const body = (await response.json()) as Record<string, unknown>;
    return {
      modal_call_id: typeof body.modal_call_id === "string" ? body.modal_call_id : `modal-${request.job_id}`,
      status: isJobStatus(body.status) ? body.status : "submitted",
    };
  }
}

export function createModalClientFromEnv(env: Record<string, string | undefined> = process.env): ModalClient {
  const endpoint = env.MODAL_JOB_WEBHOOK_URL ?? env.MODAL_WEBHOOK_URL;
  if (endpoint) {
    return new HttpModalClient(
      endpoint,
      env.MODAL_JOB_WEBHOOK_TOKEN ?? env.MODAL_WEBHOOK_TOKEN,
      Number(env.MODAL_JOB_TIMEOUT_MS ?? 10_000),
    );
  }

  return new LocalModalClient();
}

async function fetchWithTimeout(url: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}
