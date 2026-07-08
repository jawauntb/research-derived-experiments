import type { ComprehensionHeatmapSegment, EvidenceEpisode, ReplayMarker, ReplayMemo } from "@inquiry/signals";
import { confidenceBand, privacyUpgradeHintForText, READING_ENGAGEMENT_MAP_TITLE } from "@inquiry/ui";

type ReplayTimelineMemo = ReplayMemo & {
  limitations?: string[];
};

export type ReplayRenderOptions = {
  demo?: boolean;
  onViewDemo?: () => void | Promise<void>;
};

export function renderReplayTimeline(
  container: HTMLElement,
  memo: ReplayTimelineMemo,
  options: ReplayRenderOptions = {},
): void {
  const section = document.createElement("section");
  section.className = "replay-timeline";
  if (options.demo) {
    section.dataset.demo = "true";
  }

  const title = document.createElement("h2");
  title.textContent = options.demo ? "Sample replay preview" : "Replay";
  section.append(title);

  if (options.demo) {
    section.append(
      renderReplayState(
        "Fixture-backed preview",
        "This sample shows what replay markers, evidence, and limitations look like. It is not live session data.",
      ),
    );
  }

  if (memo.episodes.length === 0 && memo.markers.length === 0 && memo.heatmap.length === 0) {
    section.append(
      renderReplayState(
        "No replay evidence yet",
        "Stop a session after browser, camera, label, or probe events arrive, or open the sample preview to see expected value.",
      ),
      renderDemoAction(options.onViewDemo),
    );
    container.replaceChildren(section);
    return;
  }

  if (memo.episodes.length > 0) {
    section.append(renderEpisodes(memo.episodes));
  } else {
    section.append(
      renderReplayState(
        "No evidence episodes yet",
        "Copy, highlight, selected-text opt-in, labels, probes, or camera feature windows will appear here when available.",
      ),
    );
  }

  const list = document.createElement("ol");
  list.className = "replay-marker-list";
  for (const marker of memo.markers) {
    list.append(renderMarker(marker));
  }
  if (memo.markers.length > 0) {
    section.append(list);
  }

  if (memo.heatmap.length > 0) {
    section.append(renderHeatmap(memo.heatmap));
  }

  const actions = document.createElement("ul");
  actions.className = "replay-timeline__actions";
  const nextActions =
    memo.next_actions.length > 0
      ? memo.next_actions
      : ["No repair prompt yet; collect more browser, stimulus, camera, label, or probe evidence before acting."];
  for (const action of nextActions) {
    const item = document.createElement("li");
    item.textContent = action;
    actions.append(item);
  }
  section.append(actions);

  if (memo.limitations && memo.limitations.length > 0) {
    const limitations = document.createElement("section");
    limitations.className = "replay-limitations";
    const heading = document.createElement("h3");
    heading.textContent = "Limitations";
    limitations.append(heading);
    const limitationList = document.createElement("ul");
    for (const limitation of memo.limitations) {
      const item = document.createElement("li");
      item.textContent = limitation;
      const hint = privacyUpgradeHintForText(limitation);
      if (hint) {
        const upgrade = document.createElement("p");
        upgrade.className = "privacy-upgrade-hint";
        upgrade.textContent = `${hint.title}: ${hint.detail}`;
        item.append(upgrade);
      }
      limitationList.append(item);
    }
    limitations.append(limitationList);
    section.append(limitations);
  }

  container.replaceChildren(section);
}

function renderDemoAction(onViewDemo?: () => void | Promise<void>): HTMLElement {
  const action = document.createElement("button");
  action.type = "button";
  action.className = "replay-demo-button";
  action.textContent = "View sample replay";
  if (onViewDemo) {
    action.addEventListener("click", () => void onViewDemo());
  }
  return action;
}

function renderReplayState(titleText: string, detailText: string): HTMLElement {
  const state = document.createElement("section");
  state.className = "replay-state";

  const title = document.createElement("h3");
  title.textContent = titleText;
  const detail = document.createElement("p");
  detail.textContent = detailText;

  state.append(title, detail);
  return state;
}

function renderEpisodes(episodes: EvidenceEpisode[]): HTMLElement {
  const evidence = document.createElement("section");
  evidence.className = "replay-evidence";

  const title = document.createElement("h3");
  title.textContent = "Evidence";
  evidence.append(title);

  const list = document.createElement("ol");
  for (const episode of episodes) {
    list.append(renderEpisode(episode));
  }
  evidence.append(list);

  return evidence;
}

function renderEpisode(episode: EvidenceEpisode): HTMLLIElement {
  const item = document.createElement("li");
  item.dataset.episodeKind = episode.kind;
  item.dataset.episodeId = episode.episode_id;
  item.dataset.confidence = String(episode.confidence);

  const title = document.createElement("strong");
  title.textContent = episode.summary;

  const range = document.createElement("span");
  range.textContent = ` ${formatMs(episode.start_ms)}-${formatMs(episode.end_ms)}`;

  const details = document.createElement("p");
  details.textContent = episode.details.join(" ");

  const source = document.createElement("p");
  source.textContent = `Source refs: ${episode.source_refs.join(", ")}. Evidence events: ${
    episode.evidence_event_ids.length > 0 ? episode.evidence_event_ids.join(", ") : "none"
  }.`;

  const privacy = document.createElement("p");
  privacy.textContent = episode.privacy_note;
  const hint = privacyUpgradeHintForText(episode.privacy_note);
  if (hint) {
    const upgrade = document.createElement("p");
    upgrade.className = "privacy-upgrade-hint";
    upgrade.textContent = `${hint.title}: ${hint.detail}`;
    item.append(upgrade);
  }

  item.append(title, range, details, source, privacy);
  return item;
}

function renderHeatmap(segments: ComprehensionHeatmapSegment[]): HTMLElement {
  const heatmap = document.createElement("section");
  heatmap.className = "replay-heatmap";

  const title = document.createElement("h3");
  title.textContent = READING_ENGAGEMENT_MAP_TITLE;
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

  const band = confidenceBand(segment.confidence);
  const title = document.createElement("strong");
  title.textContent = `${segment.kind} (${band.label}; ${band.detail})`;

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
  const hint = privacyUpgradeHintForText(segment.limitation);
  if (hint) {
    const upgrade = document.createElement("p");
    upgrade.className = "privacy-upgrade-hint";
    upgrade.textContent = `${hint.title}: ${hint.detail}`;
    item.append(upgrade);
  }

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
    .map((evidence) => {
      const band = confidenceBand(evidence.confidence);
      return `${evidence.kind} ${band.label}`;
    })
    .join(", ")}.`;
}

function formatMs(ms: number): string {
  return `${(ms / 1000).toFixed(1)}s`;
}
