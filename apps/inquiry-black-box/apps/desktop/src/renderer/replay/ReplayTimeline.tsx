import type { ComprehensionHeatmapSegment, ReplayMarker, ReplayMemo } from "@inquiry/signals";

export function renderReplayTimeline(container: HTMLElement, memo: ReplayMemo): void {
  const section = document.createElement("section");
  section.className = "replay-timeline";

  const title = document.createElement("h2");
  title.textContent = "Replay";
  section.append(title);

  const list = document.createElement("ol");
  for (const marker of memo.markers) {
    list.append(renderMarker(marker));
  }
  section.append(list);

  if (memo.heatmap.length > 0) {
    section.append(renderHeatmap(memo.heatmap));
  }

  const actions = document.createElement("ul");
  actions.className = "replay-timeline__actions";
  for (const action of memo.next_actions) {
    const item = document.createElement("li");
    item.textContent = action;
    actions.append(item);
  }
  section.append(actions);

  container.replaceChildren(section);
}

function renderHeatmap(segments: ComprehensionHeatmapSegment[]): HTMLElement {
  const heatmap = document.createElement("section");
  heatmap.className = "replay-heatmap";

  const title = document.createElement("h3");
  title.textContent = "Comprehension Heatmap";
  heatmap.append(title);

  const list = document.createElement("ol");
  for (const segment of segments) {
    list.append(renderHeatmapSegment(segment));
  }
  heatmap.append(list);

  return heatmap;
}

function renderHeatmapSegment(segment: ComprehensionHeatmapSegment): HTMLLIElement {
  const item = document.createElement("li");
  item.dataset.heatmapKind = segment.kind;
  item.dataset.heatmapId = segment.heatmap_id;
  item.dataset.confidence = String(segment.confidence);

  const title = document.createElement("strong");
  title.textContent = `${segment.kind} (${Math.round(segment.confidence * 100)}%)`;

  const range = document.createElement("span");
  range.textContent = ` ${formatMs(segment.start_ms)}-${formatMs(segment.end_ms)}`;

  const evidence = document.createElement("p");
  evidence.textContent = [
    stimulusSummary(segment),
    behaviorSummary(segment),
    `Evidence events: ${segment.evidence_event_ids.length > 0 ? segment.evidence_event_ids.join(", ") : "none"}.`,
  ].join(" ");

  const repair = document.createElement("p");
  repair.textContent = segment.suggested_repair;

  const limitation = document.createElement("p");
  limitation.textContent = segment.limitation;

  item.append(title, range, evidence, repair, limitation);
  return item;
}

function renderMarker(marker: ReplayMarker): HTMLLIElement {
  const item = document.createElement("li");
  item.dataset.markerKind = marker.kind;
  item.dataset.markerId = marker.marker_id;

  const label = document.createElement("strong");
  label.textContent = marker.kind;

  const evidence = document.createElement("span");
  evidence.textContent = marker.evidence.join(" ");

  item.append(label, document.createTextNode(" "), evidence);
  return item;
}

function stimulusSummary(segment: ComprehensionHeatmapSegment): string {
  if (segment.stimulus_evidence.length === 0) {
    return "Stimulus evidence: none.";
  }

  return `Stimulus evidence: ${segment.stimulus_evidence
    .map(
      (evidence) =>
        `${evidence.segment_id} density ${evidence.density.toFixed(2)}, novelty ${evidence.term_novelty.toFixed(2)}, transitions ${evidence.transition_count}`,
    )
    .join("; ")}.`;
}

function behaviorSummary(segment: ComprehensionHeatmapSegment): string {
  if (segment.behavior_evidence.length === 0) {
    return "Behavior evidence: none.";
  }

  return `Behavior evidence: ${segment.behavior_evidence
    .map((evidence) => `${evidence.kind} ${Math.round(evidence.confidence * 100)}%`)
    .join(", ")}.`;
}

function formatMs(value: number): string {
  return `${Math.round(value / 1000)}s`;
}
