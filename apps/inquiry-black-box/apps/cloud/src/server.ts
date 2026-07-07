import { createCloudStore, type CloudStore } from "./db/schema";
import { createModalClientFromEnv, type ModalClient } from "./lib/modalClient";
import { handleJobsRoute } from "./routes/jobs";
import { jsonResponse, routeErrorResponse } from "./routes/common";
import { handleReportsRoute } from "./routes/reports";
import { handleSyncRoute } from "./routes/sync";

export type CloudHandlerOptions = {
  store?: CloudStore;
  modalClient?: ModalClient;
};

export function createCloudHandler(options: CloudHandlerOptions = {}) {
  assertPersistenceIsIntentional(options);
  const store = options.store ?? createCloudStore();
  const modalClient = options.modalClient ?? createModalClientFromEnv();

  return async function handleCloudRequest(request: Request): Promise<Response> {
    const url = new URL(request.url);

    try {
      if (url.pathname === "/health" && request.method === "GET") {
        return jsonResponse({ status: "ok", service: "inquiry-black-box-cloud" });
      }

      const syncResponse = await handleSyncRoute(request, url, { store });
      if (syncResponse) {
        return syncResponse;
      }

      const jobsResponse = await handleJobsRoute(request, url, { store, modalClient });
      if (jobsResponse) {
        return jobsResponse;
      }

      const reportsResponse = await handleReportsRoute(request, url, { store });
      if (reportsResponse) {
        return reportsResponse;
      }

      return jsonResponse({ error: { code: "not_found", message: "cloud route was not found" } }, 404);
    } catch (error) {
      return routeErrorResponse(error);
    }
  };
}

if (import.meta.main) {
  const port = Number(process.env.PORT ?? process.env.INQUIRY_CLOUD_PORT ?? 3000);
  Bun.serve({
    port,
    fetch: createCloudHandler(),
  });
  console.log(`Inquiry Black Box cloud API listening on ${port}`);
}

function assertPersistenceIsIntentional(options: CloudHandlerOptions): void {
  if (options.store) {
    return;
  }

  const productionRuntime = process.env.NODE_ENV === "production" || Boolean(process.env.RAILWAY_ENVIRONMENT);
  const allowInMemory = process.env.INQUIRY_ALLOW_IN_MEMORY_CLOUD === "1";
  if (productionRuntime && !allowInMemory) {
    throw new Error("Railway/production cloud API requires durable persistence; set INQUIRY_ALLOW_IN_MEMORY_CLOUD=1 only for ephemeral smoke tests");
  }
}
