import type { JsonObject } from "@inquiry/schema";
import type { InquiryDatabase } from "../db";

export function deleteLocalSession(db: InquiryDatabase, sessionId: string): { session_id: string; deleted: true } {
  queueCloudDeletion(db, sessionId);
  db.deleteSession(sessionId);
  return { session_id: sessionId, deleted: true };
}

export function queueCloudDeletion(db: InquiryDatabase, sessionId: string): void {
  const session = db.getSession(sessionId);
  if (!session) {
    return;
  }

  db.enqueueSyncPayload({
    session_id: null,
    payload: createCloudDeleteTombstone(sessionId),
    state: "queued",
  });
}

function createCloudDeleteTombstone(sessionId: string): JsonObject {
  return {
    action: "delete-cloud-aggregates",
    session_id: sessionId,
    privacy_class: "redacted-sync",
    retention_policy: "cloud-redacted",
  };
}
