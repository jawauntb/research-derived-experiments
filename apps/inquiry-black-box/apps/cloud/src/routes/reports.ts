import type { CloudStore } from "../db/schema";
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
    return jsonResponse({ user_id: user.user_id, reports: context.store.listReports(user.user_id) });
  }

  const reportMatch = url.pathname.match(/^\/reports\/([^/]+)$/);
  if (reportMatch && request.method === "GET") {
    const user = authenticate(request);
    const report = context.store.getReport(user.user_id, reportMatch[1] ?? "");
    if (!report) {
      throw new RouteError(404, "not_found", "report was not found");
    }
    return jsonResponse({ user_id: user.user_id, report });
  }

  return undefined;
}
