import { createHmac, timingSafeEqual } from "node:crypto";
import type { AuthenticatedUser } from "../db/schema";

export class RouteError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly details?: unknown,
  ) {
    super(message);
  }
}

export function authenticate(request: Request): AuthenticatedUser {
  const authorization = request.headers.get("authorization");
  if (!authorization?.startsWith("Bearer ")) {
    throw new RouteError(401, "unauthorized", "authorization bearer token is required");
  }

  const token = authorization.slice("Bearer ".length).trim();
  if (token.length === 0) {
    throw new RouteError(401, "unauthorized", "authorization bearer token is required");
  }

  const user_id = verifyCloudBearerToken(token);
  if (!user_id) {
    throw new RouteError(401, "unauthorized", "authorization bearer token is invalid");
  }

  return { user_id, token };
}

export function createCloudBearerToken(userId: string, secret = cloudAuthSecret()): string {
  const encodedUserId = base64UrlEncode(userId);
  const signature = signTokenSubject(encodedUserId, secret);
  return `dev.${encodedUserId}.${signature}`;
}

export async function readJsonObject(request: Request): Promise<Record<string, unknown>> {
  let parsed: unknown;
  try {
    parsed = await request.json();
  } catch {
    throw new RouteError(400, "invalid_json", "request body must be valid JSON");
  }

  if (!isRecord(parsed)) {
    throw new RouteError(400, "invalid_json", "request body must be a JSON object");
  }

  return parsed;
}

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

export function routeErrorResponse(error: unknown): Response {
  if (error instanceof RouteError) {
    return jsonResponse(
      {
        error: {
          code: error.code,
          message: error.message,
          ...(error.details === undefined ? {} : { details: error.details }),
        },
      },
      error.status,
    );
  }

  const message = error instanceof Error ? error.message : "unknown cloud route error";
  return jsonResponse({ error: { code: "internal_error", message } }, 500);
}

export function stringField(body: Record<string, unknown>, key: string): string;
export function stringField(body: Record<string, unknown>, key: string, required: true): string;
export function stringField(body: Record<string, unknown>, key: string, required: false): string | undefined;
export function stringField(body: Record<string, unknown>, key: string, required = true): string | undefined {
  const value = body[key];
  if (typeof value === "string" && value.length > 0) {
    return value;
  }
  if (required) {
    throw new RouteError(400, "invalid_request", `${key} must be a non-empty string`);
  }
  return undefined;
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function verifyCloudBearerToken(token: string): string | null {
  const [scheme, encodedUserId, signature] = token.split(".");
  if (scheme !== "dev" || !encodedUserId || !signature) {
    return null;
  }

  const expected = signTokenSubject(encodedUserId, cloudAuthSecret());
  if (!constantTimeEqual(signature, expected)) {
    return null;
  }

  try {
    return base64UrlDecode(encodedUserId);
  } catch {
    return null;
  }
}

function signTokenSubject(subject: string, secret: string): string {
  return createHmac("sha256", secret).update(subject).digest("base64url");
}

function constantTimeEqual(left: string, right: string): boolean {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);
  return leftBuffer.length === rightBuffer.length && timingSafeEqual(leftBuffer, rightBuffer);
}

function cloudAuthSecret(): string {
  const configured = process.env.INQUIRY_CLOUD_AUTH_SECRET;
  if (configured && configured.length > 0) {
    return configured;
  }

  if (process.env.NODE_ENV === "production" || process.env.RAILWAY_ENVIRONMENT) {
    throw new RouteError(500, "auth_not_configured", "INQUIRY_CLOUD_AUTH_SECRET is required");
  }

  return "local-dev-inquiry-secret";
}

function base64UrlEncode(value: string): string {
  return Buffer.from(value, "utf8").toString("base64url");
}

function base64UrlDecode(value: string): string {
  return Buffer.from(value, "base64url").toString("utf8");
}
