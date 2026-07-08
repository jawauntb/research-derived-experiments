import { describe, expect, test } from "bun:test";
import { createEvent } from "@inquiry/schema";
import { createInquiryDatabase } from "../src/main/db";
import { runDailyReviewCheckupNotification } from "../src/main/notifications/notificationScheduler";
import { createDailyReviewReport } from "../src/main/reports/dailyDigest";
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

  test("daily review checkups are opt-in, quiet-hour aware, and cooled down", async () => {
    const database = createInquiryDatabase();
    const session = database.createSession({ title: "Notification fixture", session_id: "session-notify-daily" });
    database.appendEvent(
      createEvent({
        session_id: session.session_id,
        source: "browser",
        source_version: "extension@0.1.0",
        monotonic_ms: 1_000,
        event_type: "browser.scroll",
        payload: { delta_y: 4_800, scroll_y: 4_800, viewport_h: 900 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );
    database.appendEvent(
      createEvent({
        session_id: session.session_id,
        source: "browser",
        source_version: "extension@0.1.0",
        monotonic_ms: 1_500,
        event_type: "browser.dwell",
        payload: { dwell_ms: 200 },
        privacy_class: "local-derived",
        retention_policy: "local-default",
      }),
    );
    const localDate = session.started_at.slice(0, 10);
    const review = createDailyReviewReport(database, {
      local_date: localDate,
      timezone: "UTC",
      generated_at: `${localDate}T22:00:00.000Z`,
    });
    const shown: Array<{ title: string; body: string }> = [];
    const notifier = {
      show: async (input: { title: string; body: string }) => {
        shown.push(input);
        return "shown" as const;
      },
    };

    expect((await runDailyReviewCheckupNotification({ database, review, notifier, now_ms: Date.parse(`${localDate}T22:00:00Z`) }))).toEqual(
      { delivered: false, suppression_reason: "notifications-disabled" },
    );
    expect(database.listEvents(session.session_id).map((event) => event.event_type)).toContain("notification.candidate");

    database.setSignalEnabled("notifications", true);
    const delivered = await runDailyReviewCheckupNotification({
      database,
      review,
      notifier,
      now_ms: Date.parse(`${localDate}T22:05:00Z`),
    });
    const cooledDown = await runDailyReviewCheckupNotification({
      database,
      review,
      notifier,
      now_ms: Date.parse(`${localDate}T22:06:00Z`),
      cooldown_ms: 60 * 60 * 1000,
    });
    const nextLocalDate = new Date(Date.parse(`${localDate}T00:00:00Z`) + 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
    const quiet = await runDailyReviewCheckupNotification({
      database,
      review: { ...review, local_date: nextLocalDate, report_id: `daily-review:${nextLocalDate}` },
      notifier,
      now_ms: Date.parse(`${nextLocalDate}T22:05:00Z`),
      quiet_hours: { start_hour: 21, end_hour: 23 },
    });
    const afterCooldown = await runDailyReviewCheckupNotification({
      database,
      review,
      notifier,
      now_ms: Date.parse(`${localDate}T23:10:00Z`),
      cooldown_ms: 60 * 60 * 1000,
    });

    expect(delivered.delivered).toBe(true);
    expect(cooledDown).toEqual({ delivered: false, suppression_reason: "cooldown" });
    expect(quiet).toEqual({ delivered: false, suppression_reason: "quiet-hours" });
    expect(afterCooldown.delivered).toBe(true);
    expect(shown).toHaveLength(2);
    expect(database.listEvents(session.session_id).filter((event) => event.event_type === "notification.delivered")).toHaveLength(2);
    database.close();
  });
});
