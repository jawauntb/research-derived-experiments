import type { EventEnvelope } from "@inquiry/schema";
import { numericPayload, stringPayload } from "./windows";

export type EvidenceEpisodeKind = "copied-selection";

export type EvidenceEpisode = {
  episode_id: string;
  session_id: string;
  kind: EvidenceEpisodeKind;
  start_ms: number;
  end_ms: number;
  confidence: number;
  marker_ids: string[];
  evidence_event_ids: string[];
  source_refs: string[];
  summary: string;
  details: string[];
  privacy_note: string;
};

type EpisodeMarker = {
  marker_id: string;
  kind: string;
  evidence_event_ids: string[];
};

type CopyGroup = {
  session_id: string;
  page_key: string;
  source_refs: string[];
  events: EventEnvelope[];
};

const COPY_EPISODE_GAP_MS = 12_000;
const copiedEventTypes = new Set(["browser.selection", "browser.highlight", "browser.copy"]);

export function buildEvidenceEpisodes(events: EventEnvelope[], markers: EpisodeMarker[] = []): EvidenceEpisode[] {
  return buildCopiedSelectionEpisodes(events).map((episode) => ({
    ...episode,
    marker_ids: markers
      .filter((marker) => marker.kind === "copied-passage" && overlapsEvidence(marker.evidence_event_ids, episode.evidence_event_ids))
      .map((marker) => marker.marker_id),
  }));
}

export function buildCopiedSelectionEpisodes(events: EventEnvelope[]): EvidenceEpisode[] {
  const ordered = events
    .filter((event) => copiedEventTypes.has(event.event_type))
    .sort((a, b) => a.session_id.localeCompare(b.session_id) || a.monotonic_ms - b.monotonic_ms);

  const groups: CopyGroup[] = [];
  for (const event of ordered) {
    const pageKey = pageKeyFor(event);
    const previous = groups[groups.length - 1];
    const previousEvent = previous?.events[previous.events.length - 1];
    const sameGroup =
      previous &&
      previous.session_id === event.session_id &&
      previous.page_key === pageKey &&
      previousEvent &&
      event.monotonic_ms - previousEvent.monotonic_ms <= COPY_EPISODE_GAP_MS;

    if (sameGroup) {
      previous.events.push(event);
      continue;
    }

    groups.push({
      session_id: event.session_id,
      page_key: pageKey,
      source_refs: sourceRefsFor(event),
      events: [event],
    });
  }

  return groups.map(groupToEpisode);
}

function groupToEpisode(group: CopyGroup): EvidenceEpisode {
  const first = group.events[0];
  const last = group.events[group.events.length - 1] ?? first;
  if (!first || !last) {
    throw new Error("copy episode group must contain at least one event");
  }

  const counts = eventCounts(group.events);
  const lengths = group.events.map((event) => numericPayload(event, "selection_length")).filter(isNumber);
  const rangeCounts = group.events.map((event) => numericPayload(event, "range_count")).filter(isNumber);
  const eventIds = group.events.map((event) => event.event_id);
  const spanMs = Math.max(0, last.monotonic_ms - first.monotonic_ms);
  const actionSummary = compactList([
    countPhrase(counts.selection, "selection change"),
    countPhrase(counts.highlight, "highlight"),
    countPhrase(counts.copy, "copy action"),
  ]);
  const sourceSummary = group.source_refs.join(", ");
  const selectionRange = numberRange(lengths);
  const rangeCount = numberRange(rangeCounts);

  return {
    episode_id: `copied-selection:${group.session_id}:${Math.round(first.monotonic_ms)}:${stableHash(eventIds.join("|"))}`,
    session_id: group.session_id,
    kind: "copied-selection",
    start_ms: first.monotonic_ms,
    end_ms: last.monotonic_ms,
    confidence: counts.copy > 0 ? 0.86 : 0.74,
    marker_ids: [],
    evidence_event_ids: eventIds,
    source_refs: group.source_refs,
    summary: `${capitalize(actionSummary)} on ${sourceSummary} over ${formatDuration(spanMs)}.`,
    details: [
      selectionRange ? `Selection length ranged ${selectionRange} characters.` : "Selection length was not available.",
      rangeCount ? `DOM range count ranged ${rangeCount}.` : "DOM range count was not available.",
      `${group.events.length} evidence event${group.events.length === 1 ? "" : "s"} contributed to this episode.`,
    ],
    privacy_note: "Raw selected or copied text was not stored; this episode uses timing, counts, lengths, and hashed page refs.",
  };
}

function eventCounts(events: EventEnvelope[]): { selection: number; highlight: number; copy: number } {
  return {
    selection: events.filter((event) => event.event_type === "browser.selection").length,
    highlight: events.filter((event) => event.event_type === "browser.highlight").length,
    copy: events.filter((event) => event.event_type === "browser.copy").length,
  };
}

function sourceRefsFor(event: EventEnvelope): string[] {
  const hostnameHash = stringPayload(event, "hostname_hash");
  const urlHash = stringPayload(event, "url_hash");
  const refs = [
    hostnameHash ? `host ${hostnameHash}` : null,
    urlHash ? `page ${urlHash}` : null,
  ].filter((value): value is string => typeof value === "string");

  return refs.length > 0 ? refs : ["unknown page"];
}

function pageKeyFor(event: EventEnvelope): string {
  return `${stringPayload(event, "hostname_hash") ?? "unknown-host"}:${stringPayload(event, "url_hash") ?? "unknown-url"}`;
}

function overlapsEvidence(left: string[], right: string[]): boolean {
  const rightSet = new Set(right);
  return left.some((eventId) => rightSet.has(eventId));
}

function countPhrase(count: number, label: string): string | null {
  if (count === 0) {
    return null;
  }

  return `${count} ${label}${count === 1 ? "" : "s"}`;
}

function compactList(values: Array<string | null>): string {
  const present = values.filter((value): value is string => typeof value === "string");
  if (present.length === 0) {
    return "browser evidence";
  }

  if (present.length === 1) {
    return present[0] ?? "browser evidence";
  }

  if (present.length === 2) {
    return `${present[0] ?? "browser evidence"} and ${present[1] ?? "browser evidence"}`;
  }

  return `${present.slice(0, -1).join(", ")}, and ${present[present.length - 1] ?? "browser evidence"}`;
}

function numberRange(values: number[]): string | null {
  if (values.length === 0) {
    return null;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  return min === max ? `${Math.round(min)}` : `${Math.round(min)}-${Math.round(max)}`;
}

function formatDuration(durationMs: number): string {
  if (durationMs < 1000) {
    return "one moment";
  }

  return `${Math.round(durationMs / 1000)}s`;
}

function capitalize(value: string): string {
  return value.length === 0 ? value : `${value.charAt(0).toUpperCase()}${value.slice(1)}`;
}

function stableHash(value: string): string {
  let hash = 0x811c9dc5;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function isNumber(value: number | null): value is number {
  return typeof value === "number";
}
