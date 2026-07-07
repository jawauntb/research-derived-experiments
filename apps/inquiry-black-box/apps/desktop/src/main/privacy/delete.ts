import { createEvent } from "@inquiry/schema";
import type { InquiryDatabase } from "../db";

export function deleteLocalSession(db: InquiryDatabase, sessionId: string): { session_id: string; deleted: true } {
  db.deleteSession(sessionId);
  return { session_id: sessionId, deleted: true };
}

export function queueCloudDeletion(db: InquiryDatabase, sessionId: string): void {
  const session = db.getSession(sessionId);
  if (!session) {
    return;
  }

  db.appendEvent(
    createEvent({
      session_id: sessionId,
      source: "desktop-system",
      source_version: "desktop@0.1.0",
      monotonic_ms: 0,
      event_type: "sync.queued",
      payload: { action: "delete-cloud-aggregates", session_id: sessionId },
      privacy_class: "redacted-sync",
      retention_policy: "cloud-redacted",
    }),
  );
}
