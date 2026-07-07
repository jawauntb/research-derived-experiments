import type { InquiryDatabase } from "../db";

export type SessionExport = {
  session_id: string;
  jsonl: string;
  exported_at: string;
  omitted_policy: string;
};

export function exportSession(db: InquiryDatabase, sessionId: string): SessionExport {
  return {
    session_id: sessionId,
    jsonl: db.exportSessionJsonl(sessionId),
    exported_at: new Date().toISOString(),
    omitted_policy: "debug-sensitive and blocked-sensitive events are omitted by default",
  };
}
