import type { LabelPayload } from "@inquiry/schema";

export const stateLabels: LabelPayload["label"][] = [
  "flow",
  "overloaded",
  "confused-good",
  "confused-bad",
  "avoiding",
  "near-breakthrough",
  "tired",
];

export function renderStateLabelBar(
  container: HTMLElement,
  onLabel: (label: LabelPayload["label"]) => void | Promise<void>,
): void {
  const nav = document.createElement("nav");
  nav.className = "state-label-bar";

  for (const label of stateLabels) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", () => void onLabel(label));
    nav.append(button);
  }

  container.replaceChildren(nav);
}
