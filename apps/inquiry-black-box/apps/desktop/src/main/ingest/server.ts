import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import {
  assertNoBlockedPayload,
  createEvent,
  isEventType,
  type EventEnvelope,
  type EventType,
  type JsonObject,
  type PrivacyClass,
  type RetentionPolicy,
  type SessionRecord,
} from "@inquiry/schema";
import type { InquiryDatabase } from "../db";
import { verifyPairingToken } from "../security/pairing";
import type { SessionController } from "./session";

export type IngestServerOptions = {
  allowedOrigins?: readonly string[];
  database: InquiryDatabase;
  pairingSecret: string;
  sessions: SessionController;
  nowMs?: () => number;
  sourceVersion?: string;
};

export type StartIngestServerOptions = IngestServerOptions & {
  hostname?: string;
  port?: number;
};

export type StartedIngestServer = {
  url: string;
  port: number;
  stop: () => void;
};

type IngestEventBody = {
  event_id?: unknown;
  session_id?: unknown;
  source?: unknown;
  source_version?: unknown;
  captured_at?: unknown;
  monotonic_ms?: unknown;
  timezone?: unknown;
  event_type?: unknown;
  payload?: unknown;
  privacy_class?: unknown;
  retention_policy?: unknown;
  confidence?: unknown;
  quality_flags?: unknown;
};

type SessionControlBody = {
  recording_state?: unknown;
  title?: unknown;
  monotonic_ms?: unknown;
};

const defaultAllowedOrigins = ["chrome-extension://*"] as const;
const ingestPaths = new Set(["/v1/events", "/v1/extension/events"]);
const sessionControlPaths = new Set(["/v1/extension/session"]);

export function createIngestRequestHandler(options: IngestServerOptions): (request: Request) => Promise<Response> {
  const allowedOrigins = options.allowedOrigins ?? defaultAllowedOrigins;
  const sourceVersion = options.sourceVersion ?? "extension@0.1.0";
  const nowMs = options.nowMs ?? (() => Date.now());

  return async function handleIngestRequest(request: Request): Promise<Response> {
    const origin = request.headers.get("origin");

    if (request.method === "OPTIONS") {
      return jsonResponse({ ok: true }, 204, origin);
    }

    const url = new URL(request.url);
    if (url.pathname === "/health") {
      return jsonResponse({ ok: true }, 200, origin);
    }

    const isIngestPath = ingestPaths.has(url.pathname);
    const isSessionControlPath = sessionControlPaths.has(url.pathname);
    if (!isIngestPath && !isSessionControlPath) {
      return jsonResponse({ error: "not found" }, 404, origin);
    }

    const canHandleMethod =
      (isIngestPath && request.method === "POST") ||
      (isSessionControlPath && (request.method === "POST" || request.method === "GET"));
    if (!canHandleMethod) {
      return jsonResponse({ error: "method not allowed" }, 405, origin);
    }

    if (!origin || !isAllowedOrigin(origin, allowedOrigins)) {
      return jsonResponse({ error: "origin not allowed" }, 403, origin);
    }

    const token = pairingTokenFromHeaders(request.headers);
    if (!token) {
      return jsonResponse({ error: "missing pairing token" }, 401, origin);
    }

    const tokenDecision = verifyPairingToken({
      secret: options.pairingSecret,
      token,
      nowMs: nowMs(),
    });
    if (!tokenDecision.valid) {
      return jsonResponse({ error: tokenDecision.reason }, 401, origin);
    }

    try {
      if (isSessionControlPath && request.method === "GET") {
        return jsonResponse(sessionStatusResponse(options.sessions.currentSession()), 200, origin);
      }

      let body: unknown;
      try {
        body = await request.json();
      } catch {
        return jsonResponse({ error: "request body must be JSON" }, 400, origin);
      }

      if (isSessionControlPath) {
        return jsonResponse(applySessionControl(body, options.sessions), 200, origin);
      }

      const events = normalizeExtensionBody(body, {
        sessions: options.sessions,
        sourceVersion,
      });
      let accepted = 0;
      let duplicates = 0;
      const eventIds: string[] = [];
      options.database.db.transaction(() => {
        for (const event of events) {
          const result = options.database.appendEventIfNew(event);
          if (result.inserted) {
            accepted += 1;
          } else {
            duplicates += 1;
          }
          eventIds.push(result.event.event_id);
        }
      })();
      return jsonResponse(
        {
          ok: true,
          accepted,
          duplicates,
          event_ids: eventIds,
        },
        202,
        origin,
      );
    } catch (error) {
      return jsonResponse({ error: error instanceof Error ? error.message : "invalid event" }, 400, origin);
    }
  };
}

function applySessionControl(value: unknown, sessions: SessionController): JsonObject {
  if (!isRecord(value)) {
    throw new Error("session control body must be an object");
  }

  const body = value as SessionControlBody;
  const monotonicMs = typeof body.monotonic_ms === "number" ? body.monotonic_ms : undefined;
  const current = sessions.currentSession();

  if (body.recording_state === "recording") {
    if (!current) {
      return sessionControlResponse(
        sessions.startSession({
          title: typeof body.title === "string" && body.title.length > 0 ? body.title : "Research session",
          ...(typeof monotonicMs === "number" ? { monotonic_ms: monotonicMs } : {}),
        }),
      );
    }

    if (current.recording_state === "paused") {
      return sessionControlResponse(
        sessions.resumeSession({
          reason: "extension-record",
          ...(typeof monotonicMs === "number" ? { monotonic_ms: monotonicMs } : {}),
        }),
      );
    }

    return sessionControlResponse(current);
  }

  if (body.recording_state === "paused") {
    if (!current) {
      throw new Error("no active session");
    }

    if (current.recording_state === "paused") {
      return sessionControlResponse(current);
    }

    return sessionControlResponse(
      sessions.pauseSession({
        reason: "extension-pause",
        ...(typeof monotonicMs === "number" ? { monotonic_ms: monotonicMs } : {}),
      }),
    );
  }

  if (body.recording_state === "stopped") {
    if (!current) {
      return {
        ok: true,
        recording_state: "stopped",
        session_id: null,
        session: null,
      };
    }

    return sessionControlResponse(
      sessions.stopSession({
        reason: "extension-stop",
        ...(typeof monotonicMs === "number" ? { monotonic_ms: monotonicMs } : {}),
      }),
    );
  }

  throw new Error("session control recording_state must be recording, paused, or stopped");
}

function sessionControlResponse(session: SessionRecord): JsonObject {
  return {
    ok: true,
    recording_state: session.recording_state,
    session_id: session.session_id,
    session: sessionRecordJson(session),
  };
}

function sessionStatusResponse(session: SessionRecord | null): JsonObject {
  if (!session) {
    return {
      ok: true,
      recording_state: "stopped",
      session_id: null,
      session: null,
    };
  }

  return sessionControlResponse(session);
}

function sessionRecordJson(session: SessionRecord): JsonObject {
  return {
    session_id: session.session_id,
    title: session.title,
    active_task: session.active_task ?? null,
    notes: session.notes ?? null,
    recording_state: session.recording_state,
    created_at: session.created_at,
    updated_at: session.updated_at,
    ended_at: session.ended_at ?? null,
  };
}

export function startIngestServer(options: StartIngestServerOptions): StartedIngestServer {
  const hostname = options.hostname ?? "127.0.0.1";
  const port = options.port ?? Number(process.env.INQUIRY_LOCAL_API_PORT ?? 39170);
  const handler = createIngestRequestHandler(options);
  if (isBunRuntime()) {
    const server = Bun.serve({
      hostname,
      port,
      fetch: handler,
    });

    return {
      url: `http://${hostname}:${server.port}`,
      port: server.port ?? port,
      stop: () => server.stop(true),
    };
  }

  const server = createServer((request, response) => {
    void handleNodeRequest(request, response, handler, hostname, port);
  });
  server.listen(port, hostname);

  return {
    url: `http://${hostname}:${port}`,
    port,
    stop: () => server.close(),
  };
}

async function handleNodeRequest(
  request: IncomingMessage,
  response: ServerResponse,
  handler: (request: Request) => Promise<Response>,
  hostname: string,
  port: number,
): Promise<void> {
  try {
    const webResponse = await handler(await toWebRequest(request, hostname, port));
    response.statusCode = webResponse.status;
    webResponse.headers.forEach((value, key) => {
      response.setHeader(key, value);
    });
    const body = Buffer.from(await webResponse.arrayBuffer());
    response.end(body);
  } catch (error) {
    response.statusCode = 500;
    response.setHeader("content-type", "application/json");
    response.end(JSON.stringify({ error: error instanceof Error ? error.message : "ingest server error" }));
  }
}

async function toWebRequest(request: IncomingMessage, hostname: string, port: number): Promise<Request> {
  const method = request.method ?? "GET";
  const headers = new Headers();
  for (const [key, value] of Object.entries(request.headers)) {
    if (Array.isArray(value)) {
      for (const item of value) {
        headers.append(key, item);
      }
    } else if (value !== undefined) {
      headers.set(key, value);
    }
  }

  const host = headers.get("host") ?? `${hostname}:${port}`;
  const url = `http://${host}${request.url ?? "/"}`;
  const init: RequestInit = { method, headers };
  if (method !== "GET" && method !== "HEAD") {
    init.body = Buffer.concat(await readRequestBody(request));
  }

  return new Request(url, init);
}

async function readRequestBody(request: IncomingMessage): Promise<Buffer[]> {
  const chunks: Buffer[] = [];
  for await (const chunk of request) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return chunks;
}

function normalizeExtensionBody(
  value: unknown,
  options: { sessions: SessionController; sourceVersion: string },
): EventEnvelope[] {
  if (!isRecord(value)) {
    throw new Error("event body must be an object");
  }

  if (Array.isArray(value.events)) {
    if (value.events.length === 0) {
      throw new Error("events batch must not be empty");
    }

    if (value.session_id !== undefined && typeof value.session_id !== "string") {
      throw new Error("batch session_id must be a string");
    }

    const batchSessionId = typeof value.session_id === "string" ? value.session_id : undefined;

    return value.events.map((event) => {
      const eventRecord = isRecord(event) ? event : {};
      if (eventRecord.session_id !== undefined && typeof eventRecord.session_id !== "string") {
        throw new Error("event session_id must be a string");
      }
      if (batchSessionId && typeof eventRecord.session_id === "string" && eventRecord.session_id !== batchSessionId) {
        throw new Error("event session does not match batch session");
      }

      return normalizeExtensionEvent({
        ...eventRecord,
        session_id: typeof eventRecord.session_id === "string" ? eventRecord.session_id : batchSessionId,
      }, options);
    });
  }

  return [normalizeExtensionEvent(value, options)];
}

function normalizeExtensionEvent(
  value: unknown,
  options: { sessions: SessionController; sourceVersion: string },
): EventEnvelope {
  if (!isRecord(value)) {
    throw new Error("event body must be an object");
  }

  const body = value as IngestEventBody;
  const active = options.sessions.currentSession();
  if (!active) {
    throw new Error("no active session");
  }
  if (active.recording_state !== "recording") {
    throw new Error(`session is ${active.recording_state}`);
  }

  if (body.session_id !== undefined && body.session_id !== active.session_id) {
    throw new Error("event session does not match active session");
  }

  if (body.source !== undefined && body.source !== "browser") {
    throw new Error("extension ingest accepts browser events only");
  }

  if (typeof body.event_type !== "string" || !isEventType(body.event_type) || !body.event_type.startsWith("browser.")) {
    throw new Error("extension ingest accepts browser event types only");
  }

  if (typeof body.monotonic_ms !== "number") {
    throw new Error("event.monotonic_ms must be a number");
  }

  if (!isRecord(body.payload)) {
    throw new Error("event.payload must be an object");
  }
  assertNoUnsafePayload(body.payload);

  const qualityFlags = body.quality_flags === undefined ? [] : body.quality_flags;
  if (!Array.isArray(qualityFlags) || !qualityFlags.every((flag) => typeof flag === "string")) {
    throw new Error("event.quality_flags must be a string array");
  }

  return createEvent({
    ...(typeof body.event_id === "string" ? { event_id: body.event_id } : {}),
    ...(typeof body.captured_at === "string" ? { captured_at: body.captured_at } : {}),
    ...(typeof body.timezone === "string" ? { timezone: body.timezone } : {}),
    session_id: active.session_id,
    source: "browser",
    source_version: typeof body.source_version === "string" ? body.source_version : options.sourceVersion,
    monotonic_ms: body.monotonic_ms,
    event_type: body.event_type as EventType,
    confidence: typeof body.confidence === "number" ? body.confidence : 1,
    quality_flags: qualityFlags,
    payload: body.payload as JsonObject,
    privacy_class: privacyClass(body.privacy_class),
    retention_policy: retentionPolicy(body.retention_policy),
  });
}

function pairingTokenFromHeaders(headers: Headers): string | null {
  const explicit = headers.get("x-inquiry-pairing-token");
  if (explicit) {
    return explicit;
  }

  const authorization = headers.get("authorization");
  if (!authorization) {
    return null;
  }

  const [scheme, token] = authorization.split(" ");
  if (scheme?.toLowerCase() !== "bearer" || !token) {
    return null;
  }

  return token;
}

function isAllowedOrigin(origin: string, allowedOrigins: readonly string[]): boolean {
  return allowedOrigins.some((allowed) => {
    if (allowed === origin) {
      return true;
    }
    if (allowed === "chrome-extension://*") {
      return origin.startsWith("chrome-extension://");
    }
    return false;
  });
}

function privacyClass(value: unknown): PrivacyClass {
  if (value === undefined) {
    return "local-derived";
  }
  if (value === "public" || value === "local-derived" || value === "redacted-sync" || value === "document-opt-in") {
    return value;
  }
  throw new Error("event.privacy_class is not allowed for extension ingest");
}

function retentionPolicy(value: unknown): RetentionPolicy {
  if (value === undefined) {
    return "local-default";
  }
  if (value === "session-delete" || value === "local-default" || value === "expire-30d" || value === "cloud-redacted") {
    return value;
  }
  throw new Error("event.retention_policy is not allowed for extension ingest");
}

function assertNoUnsafePayload(value: unknown, path = "payload"): void {
  if (!isRecord(value)) {
    throw new Error(`${path} must be an object`);
  }
  assertNoBlockedPayload(value);
}

function jsonResponse(body: JsonObject, status: number, origin: string | null): Response {
  const headers = new Headers({
    "content-type": "application/json",
  });
  if (origin) {
    headers.set("access-control-allow-origin", origin);
    headers.set("access-control-allow-headers", "authorization, content-type, x-inquiry-pairing-token");
    headers.set("access-control-allow-methods", "GET, POST, OPTIONS");
  }

  if (status === 204) {
    return new Response(null, { status, headers });
  }

  return new Response(JSON.stringify(body), { status, headers });
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isBunRuntime(): boolean {
  return typeof (globalThis as { Bun?: unknown }).Bun === "object";
}
