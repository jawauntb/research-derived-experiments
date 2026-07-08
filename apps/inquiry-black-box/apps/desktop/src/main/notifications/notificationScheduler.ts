import { createEvent, type EventEnvelope } from "@inquiry/schema";
import type { DailyReview } from "@inquiry/signals";
import type { InquiryDatabase } from "../db";
import type { DesktopNotifier } from "./desktopNotifier";
import { type QuietHours } from "./notificationManager";

export type CheckupNotificationResult =
  | { delivered: true; event: EventEnvelope }
  | { delivered: false; suppression_reason: string };

export type RunCheckupNotificationInput = {
  database: InquiryDatabase;
  review: DailyReview;
  notifier: DesktopNotifier;
  now_ms?: number;
  quiet_hours?: QuietHours;
  cooldown_ms?: number;
};

export async function runDailyReviewCheckupNotification(
  input: RunCheckupNotificationInput,
): Promise<CheckupNotificationResult> {
  const settings = input.database.signalSettings();
  const nowMs = input.now_ms ?? Date.now();
  const cooldownMs = input.cooldown_ms ?? 12 * 60 * 60 * 1000;
  const anchorSessionId = input.review.suggestions[0]?.session_ids[0] ?? input.database.listSessions()[0]?.session_id;

  if (!anchorSessionId) {
    return { delivered: false, suppression_reason: "no-session" };
  }

  const candidate = {
    notification_id: `daily-review:${input.review.local_date}`,
    title: "Daily Inquiry review is ready",
    body: dailyReviewBody(input.review),
    local_date: input.review.local_date,
    report_id: input.review.report_id,
    suggestion_ids: input.review.suggestions.map((suggestion) => suggestion.suggestion_id),
  };
  input.database.appendEventIfNew(
    createEvent({
      event_id: `notification-candidate:${candidate.notification_id}`,
      session_id: anchorSessionId,
      source: "desktop-system",
      source_version: "desktop@0.1.0",
      monotonic_ms: lastMonotonicMs(input.database.listEvents(anchorSessionId)) + 1,
      event_type: "notification.candidate",
      payload: candidate,
      privacy_class: "local-derived",
      retention_policy: "local-default",
    }),
  );

  if (!settings.notifications) {
    return { delivered: false, suppression_reason: "notifications-disabled" };
  }
  if (input.review.suggestions.length === 0) {
    return { delivered: false, suppression_reason: "no-actionable-suggestions" };
  }
  if (input.quiet_hours && isWithinQuietHours(new Date(nowMs), input.quiet_hours)) {
    return { delivered: false, suppression_reason: "quiet-hours" };
  }

  const lastDeliveredMs = latestDailyDeliveredMs(input.database, input.review.local_date);
  if (lastDeliveredMs !== undefined && nowMs - lastDeliveredMs < cooldownMs) {
    return { delivered: false, suppression_reason: "cooldown" };
  }

  const shown = await input.notifier.show({ title: candidate.title, body: candidate.body });
  if (shown !== "shown") {
    return { delivered: false, suppression_reason: "notifier-failed" };
  }

  const event = createEvent({
    event_id: `notification-delivered:${candidate.notification_id}:${nowMs}`,
    session_id: anchorSessionId,
    source: "desktop-system",
    source_version: "desktop@0.1.0",
    captured_at: new Date(nowMs).toISOString(),
    monotonic_ms: lastMonotonicMs(input.database.listEvents(anchorSessionId)) + 2,
    event_type: "notification.delivered",
    payload: {
      ...candidate,
      delivered_at_ms: nowMs,
    },
    privacy_class: "local-derived",
    retention_policy: "local-default",
  });
  input.database.appendEventIfNew(event);
  return { delivered: true, event };
}

function dailyReviewBody(review: DailyReview): string {
  const top = review.suggestions[0];
  if (!top) {
    return "No suggestions yet. Open Inquiry to review the empty state.";
  }
  return top.action;
}

function latestDailyDeliveredMs(database: InquiryDatabase, localDate: string): number | undefined {
  const delivered = database
    .listSessions()
    .flatMap((session) => database.listEvents(session.session_id))
    .filter((event) => event.event_type === "notification.delivered" && event.payload.local_date === localDate)
    .map((event) => Number(event.payload.delivered_at_ms))
    .filter((value) => Number.isFinite(value));
  if (delivered.length === 0) {
    return undefined;
  }
  return Math.max(...delivered);
}

function lastMonotonicMs(events: EventEnvelope[]): number {
  return events.reduce((max, event) => Math.max(max, event.monotonic_ms), 0);
}

function isWithinQuietHours(date: Date, quietHours: QuietHours): boolean {
  const hour = date.getHours();
  if (quietHours.start_hour === quietHours.end_hour) {
    return false;
  }
  if (quietHours.start_hour < quietHours.end_hour) {
    return hour >= quietHours.start_hour && hour < quietHours.end_hour;
  }
  return hour >= quietHours.start_hour || hour < quietHours.end_hour;
}
