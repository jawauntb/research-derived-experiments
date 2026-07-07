import type { ReplayMarker, ReplayMemo } from "@inquiry/signals";

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
