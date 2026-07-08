import {
  findSensitiveFieldPaths,
  normalizeSensitiveFieldName,
  rawTextPayloadFieldNames,
  selectedTextPayloadFieldNames,
  sensitivePayloadFieldNames,
  type JsonObject,
} from "@inquiry/schema";
import type { CloudStore } from "../db/schema";
import type { ReportRecord } from "../db/schema";
import { RouteError, authenticate, jsonResponse } from "./common";

export type ReportsRouteContext = {
  store: CloudStore;
};

export async function handleReportsRoute(
  request: Request,
  url: URL,
  context: ReportsRouteContext,
): Promise<Response | undefined> {
  if (url.pathname === "/reports" && request.method === "GET") {
    const user = authenticate(request);
    const reports = await context.store.listReports(user.user_id);
    return jsonResponse({ user_id: user.user_id, reports: reports.map(publicReport) });
  }

  const reportMatch = url.pathname.match(/^\/reports\/([^/]+)$/);
  if (reportMatch && request.method === "GET") {
    const user = authenticate(request);
    const report = await context.store.getReport(user.user_id, reportMatch[1] ?? "");
    if (!report) {
      throw new RouteError(404, "not_found", "report was not found");
    }
    return jsonResponse({ user_id: user.user_id, report: publicReport(report) });
  }

  return undefined;
}

function publicReport(report: ReportRecord): ReportRecord {
  return {
    ...report,
    payload: sanitizeReportObject(report.payload),
    provenance: sanitizeReportObject(report.provenance),
  };
}

function sanitizeReportObject(value: JsonObject): JsonObject {
  const sensitiveFields = findSensitiveFieldPaths(value, {
    extraFieldNames: [...selectedTextPayloadFieldNames, ...rawTextPayloadFieldNames],
    normalizeFieldName: normalizeSensitiveFieldName,
  });
  if (sensitiveFields.length === 0) {
    return value;
  }

  return {
    ...omitReportSensitiveFields(value),
    redacted: true,
    omitted_sensitive_fields: sensitiveFields,
  };
}

const reportSensitiveFields = new Set(
  [...sensitivePayloadFieldNames, ...selectedTextPayloadFieldNames, ...rawTextPayloadFieldNames].map(
    normalizeSensitiveFieldName,
  ),
);

function omitReportSensitiveFields(value: unknown): JsonObject {
  const redacted = omitSensitiveValue(value);
  return isJsonObject(redacted) ? redacted : {};
}

function isJsonObject(value: unknown): value is JsonObject {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return false;
  }

  return Object.values(value).every(isJsonValue);
}

function isJsonValue(value: unknown): value is JsonObject[keyof JsonObject] {
  if (value === null) {
    return true;
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return true;
  }
  if (Array.isArray(value)) {
    return value.every(isJsonValue);
  }
  return isJsonObject(value);
}

function omitSensitiveValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(omitSensitiveValue);
  }

  if (typeof value !== "object" || value === null) {
    return value;
  }

  return Object.fromEntries(
    Object.entries(value)
      .filter(([key]) => !reportSensitiveFields.has(normalizeSensitiveFieldName(key)))
      .map(([key, child]) => [key, omitSensitiveValue(child)]),
  );
}
