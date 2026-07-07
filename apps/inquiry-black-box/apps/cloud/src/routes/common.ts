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

  const user_id = request.headers.get("x-inquiry-user-id") ?? userIdFromToken(token);
  if (user_id.length === 0) {
    throw new RouteError(401, "unauthorized", "authenticated user id could not be resolved");
  }

  return { user_id, token };
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

function userIdFromToken(token: string): string {
  const delimiter = token.indexOf(".");
  return delimiter === -1 ? token : token.slice(0, delimiter);
}
