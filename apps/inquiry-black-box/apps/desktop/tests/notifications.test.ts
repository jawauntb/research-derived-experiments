import { describe, expect, test } from "bun:test";
import { decideNotification, recordNotificationOutcome } from "../src/main/notifications/notificationManager";

const marker = {
  marker_id: "stuck-loop:1",
  session_id: "session-notify",
  kind: "stuck-loop" as const,
  start_ms: 1,
  end_ms: 2,
  confidence: 0.8,
  evidence_event_ids: ["event-1"],
  evidence: ["fixture"],
  suggested_action: "Ask what prerequisite is missing.",
};

describe("notification manager", () => {
  test("suppresses notifications when disabled, quiet, or cooling down", () => {
    expect(decideNotification(marker, { enabled: false, cooldown_ms: 1, now_ms: 1 }).deliver).toBe(false);
    expect(
      decideNotification(marker, {
        enabled: true,
        quiet_hours: { start_hour: 0, end_hour: 23 },
        cooldown_ms: 1,
        now_ms: new Date("2026-07-07T12:00:00Z").getTime(),
      }),
    ).toEqual({ deliver: false, suppression_reason: "quiet-hours" });
    expect(decideNotification(marker, { enabled: true, cooldown_ms: 1000, now_ms: 1200, last_delivered_ms: 1000 })).toEqual({
      deliver: false,
      suppression_reason: "cooldown",
    });
  });

  test("delivers actionable markers and records outcomes", () => {
    const decision = decideNotification(marker, { enabled: true, cooldown_ms: 1, now_ms: 10_000 });

    expect(decision.deliver).toBe(true);
    expect(recordNotificationOutcome({ marker, response: "accepted", monotonic_ms: 11_000 }).payload.response).toBe("accepted");
  });
});
