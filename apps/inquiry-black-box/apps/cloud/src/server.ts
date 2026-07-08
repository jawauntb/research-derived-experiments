import { createCloudStoreFromEnv, type CloudStore } from "./db/schema";
import { createModalClientFromEnv, type ModalClient } from "./lib/modalClient";
import { createSummaryClientFromEnv, type SummaryClient } from "./lib/summaryClient";
import { handleJobsRoute } from "./routes/jobs";
import { jsonResponse, routeErrorResponse } from "./routes/common";
import { handleReportsRoute } from "./routes/reports";
import { handleSyncRoute } from "./routes/sync";

export type CloudHandlerOptions = {
  store?: CloudStore;
  modalClient?: ModalClient;
  summaryClient?: SummaryClient;
  env?: Record<string, string | undefined>;
};

export function createCloudHandler(options: CloudHandlerOptions = {}) {
  const env = options.env ?? process.env;
  const store = options.store ?? createCloudStoreFromEnv(env);
  assertCloudConfiguration({ env, store, storeWasProvided: Boolean(options.store) });
  const modalClient = options.modalClient ?? createModalClientFromEnv(env);
  const summaryClient = options.summaryClient ?? createSummaryClientFromEnv(env);

  return async function handleCloudRequest(request: Request): Promise<Response> {
    const url = new URL(request.url);

    try {
      if (url.pathname === "/health" && request.method === "GET") {
        await store.initialize?.();
        return jsonResponse({ status: "ok", service: "inquiry-black-box-cloud", storage: store.kind });
      }

      if (url.pathname === "/ready" && request.method === "GET") {
        await store.initialize?.();
        const durable = store.kind === "postgres";
        return jsonResponse(
          {
            status: durable ? "ready" : "not_ready",
            service: "inquiry-black-box-cloud",
            storage: store.kind,
            durable,
          },
          durable ? 200 : 503,
        );
      }

      const syncResponse = await handleSyncRoute(request, url, { store });
      if (syncResponse) {
        return syncResponse;
      }

      const jobsResponse = await handleJobsRoute(request, url, {
        store,
        modalClient,
        ...(summaryClient ? { summaryClient } : {}),
      });
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

function assertCloudConfiguration(input: {
  env: Record<string, string | undefined>;
  store: CloudStore;
  storeWasProvided: boolean;
}): void {
  const productionRuntime = input.env.NODE_ENV === "production" || Boolean(input.env.RAILWAY_ENVIRONMENT);
  if (productionRuntime && !input.env.INQUIRY_CLOUD_AUTH_SECRET) {
    throw new Error("INQUIRY_CLOUD_AUTH_SECRET is required for Railway/production cloud API startup");
  }

  if (input.storeWasProvided || input.store.kind === "postgres") {
    return;
  }

  const allowInMemory = input.env.INQUIRY_ALLOW_IN_MEMORY_CLOUD === "1";
  if (productionRuntime && !allowInMemory) {
    throw new Error("Railway/production cloud API requires durable persistence; set INQUIRY_ALLOW_IN_MEMORY_CLOUD=1 only for ephemeral smoke tests");
  }
}
