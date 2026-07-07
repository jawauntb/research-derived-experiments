export type TimeWindow = {
  session_id: string;
  start_ms: number;
  end_ms: number;
  event_ids: string[];
};

export function windowDurationMs(window: TimeWindow): number {
  return Math.max(0, window.end_ms - window.start_ms);
}
