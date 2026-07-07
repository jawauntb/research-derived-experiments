import { canSyncPrivacyClass, findSensitiveFieldPaths, validateEvent, type EventEnvelope } from "@inquiry/schema";
import type { CloudStore } from "../db/schema";
import { RouteError, authenticate, isRecord, jsonResponse, readJsonObject, stringField } from "./common";

export type SyncRouteContext = {
  store: CloudStore;
};

export async function handleSyncRoute(request: Request, url: URL, context: SyncRouteContext): Promise<Response | undefined> {
  if (url.pathname === "/sync/events" && request.method === "POST") {
    return syncEvents(request, context);
  }

  if (url.pathname === "/sync/device/revoke" && request.method === "POST") {
    return revokeDeviceToken(request, context);
  }

  return undefined;
}

async function syncEvents(request: Request, context: SyncRouteContext): Promise<Response> {
  const user = authenticate(request);
  const body = await readJsonObject(request);
  const device_id = stringField(body, "device_id");
  const token_id = stringField(body, "token_id");
  const revoked = await context.store.getDeviceToken(user.user_id, device_id, token_id);
  if (revoked?.status === "revoked") {
    throw new RouteError(403, "device_revoked", "device token has been revoked");
  }
  const events = body.events;
  if (!Array.isArray(events)) {
    throw new RouteError(400, "invalid_request", "events must be an array");
  }

  const rejected: Array<{ index: number; event_id?: string; reason: string }> = [];
  const validEvents: EventEnvelope[] = [];

  for (const [index, candidate] of events.entries()) {
    try {
      validateEvent(candidate);
      const decision = canSyncPrivacyClass(candidate.privacy_class);
      if (!decision.allowed) {
        throw new Error(decision.reason);
      }
      const sensitivePaths = findSensitiveFieldPaths(candidate.payload);
      if (sensitivePaths.length > 0) {
        throw new Error(`payload contains sensitive field(s): ${sensitivePaths.join(", ")}`);
      }
      validEvents.push(candidate);
    } catch (error) {
      rejected.push({
        index,
        ...(isRecord(candidate) && typeof candidate.event_id === "string" ? { event_id: candidate.event_id } : {}),
        reason: error instanceof Error ? error.message : "event rejected",
      });
    }
  }

  if (rejected.length > 0) {
    throw new RouteError(422, "events_rejected", "one or more events were rejected", {
      accepted: 0,
      duplicates: 0,
      rejected,
    });
  }

  let accepted = 0;
  let duplicates = 0;
  const event_ids: string[] = [];
  for (const event of validEvents) {
    const result = await context.store.syncEvent(user.user_id, device_id, event);
    if (result.inserted) {
      accepted += 1;
    } else {
      duplicates += 1;
    }
    event_ids.push(result.record.event_id);
  }

  return jsonResponse({ accepted, duplicates, event_ids, rejected: [] }, 202);
}

async function revokeDeviceToken(request: Request, context: SyncRouteContext): Promise<Response> {
  const user = authenticate(request);
  const body = await readJsonObject(request);
  const device_id = stringField(body, "device_id");
  const token_id = stringField(body, "token_id");
  const reason = stringField(body, "reason", false);
  const revoked_at = stringField(body, "revoked_at", false);

  const record = await context.store.revokeDeviceToken({
    user_id: user.user_id,
    device_id,
    token_id,
    ...(reason ? { reason } : {}),
    ...(revoked_at ? { revoked_at } : {}),
  });

  return jsonResponse(record);
}
