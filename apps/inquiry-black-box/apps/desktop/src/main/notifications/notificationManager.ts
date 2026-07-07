import type { ReplayMarker } from "@inquiry/signals";

export type QuietHours = {
  start_hour: number;
  end_hour: number;
};

export type NotificationSettings = {
  enabled: boolean;
  quiet_hours?: QuietHours;
  cooldown_ms: number;
  snoozed_until_ms?: number;
  now_ms: number;
  last_delivered_ms?: number;
};

export type NotificationCandidate = {
  marker: ReplayMarker;
  title: string;
  body: string;
};

export type NotificationDecision =
  | { deliver: true; candidate: NotificationCandidate }
  | { deliver: false; suppression_reason: string };

const allowedKinds = new Set<ReplayMarker["kind"]>(["stuck-loop", "skim-risk", "high-load"]);

export function notificationCandidate(marker: ReplayMarker): NotificationCandidate | null {
  if (!allowedKinds.has(marker.kind) || marker.confidence < 0.65) {
    return null;
  }

  return {
    marker,
    title: titleFor(marker.kind),
    body: marker.suggested_action,
  };
}

export function decideNotification(marker: ReplayMarker, settings: NotificationSettings): NotificationDecision {
  const candidate = notificationCandidate(marker);
  if (!candidate) {
    return { deliver: false, suppression_reason: "marker-not-actionable" };
  }

  if (!settings.enabled) {
    return { deliver: false, suppression_reason: "notifications-disabled" };
  }

  if (settings.snoozed_until_ms !== undefined && settings.now_ms < settings.snoozed_until_ms) {
    return { deliver: false, suppression_reason: "snoozed" };
  }

  if (settings.last_delivered_ms !== undefined && settings.now_ms - settings.last_delivered_ms < settings.cooldown_ms) {
    return { deliver: false, suppression_reason: "cooldown" };
  }

  if (settings.quiet_hours && isWithinQuietHours(new Date(settings.now_ms), settings.quiet_hours)) {
    return { deliver: false, suppression_reason: "quiet-hours" };
  }

  return { deliver: true, candidate };
}

export function recordNotificationOutcome(input: {
  marker: ReplayMarker;
  response: "accepted" | "snoozed" | "dismissed" | "ignored";
  monotonic_ms: number;
}): {
  session_id: string;
  event_type: "notification.responded";
  monotonic_ms: number;
  payload: { marker_id: string; response: "accepted" | "snoozed" | "dismissed" | "ignored" };
} {
  return {
    session_id: input.marker.session_id,
    event_type: "notification.responded",
    monotonic_ms: input.monotonic_ms,
    payload: {
      marker_id: input.marker.marker_id,
      response: input.response,
    },
  };
}

function titleFor(kind: ReplayMarker["kind"]): string {
  switch (kind) {
    case "stuck-loop":
      return "Possible stuck loop";
    case "skim-risk":
      return "Fast skim detected";
    case "high-load":
      return "High-load moment";
    default:
      return "Research cue";
  }
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
