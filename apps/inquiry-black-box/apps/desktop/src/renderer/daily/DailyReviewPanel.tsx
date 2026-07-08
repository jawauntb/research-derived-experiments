import type { SuggestionResponse } from "@inquiry/schema";
import type { DailyReviewReport } from "../../main/reports/dailyDigest";

export type DailyReviewActions = {
  refreshDailyReview: () => void | Promise<void>;
  respondSuggestion: (input: { suggestion_id: string; response: SuggestionResponse; reason?: string; snoozed_until?: string }) => void | Promise<void>;
};

type DailyReviewSectionKey = "helped" | "fragmented" | "retry" | "ignore" | "open_loops" | "care_candidates";

export function renderDailyReviewPanel(
  container: HTMLElement,
  review: DailyReviewReport | null | undefined,
  actions: DailyReviewActions,
): void {
  const section = document.createElement("section");
  section.className = "daily-review-panel";

  const header = document.createElement("div");
  header.className = "daily-review-header";
  const title = document.createElement("h2");
  title.textContent = "Daily Review";
  const refresh = document.createElement("button");
  refresh.type = "button";
  refresh.textContent = "Refresh";
  refresh.addEventListener("click", () => void actions.refreshDailyReview());
  header.append(title, refresh);
  section.append(header);

  if (!review || (review.suggestions.length === 0 && review.limitations.length === 0)) {
    section.append(emptyState("No daily suggestions yet", "Run and stop an explicit session, then refresh today's review."));
    container.replaceChildren(section);
    return;
  }

  const summary = document.createElement("p");
  summary.className = "daily-review-summary";
  summary.textContent = review.summary;
  section.append(summary);

  const categories: Array<[DailyReviewSectionKey, string]> = [
    ["helped", "What helped"],
    ["fragmented", "What fragmented"],
    ["retry", "What to retry"],
    ["open_loops", "Open loops"],
    ["care_candidates", "What to confirm"],
    ["ignore", "What to ignore"],
  ];

  for (const [key, label] of categories) {
    const items = review.sections[key];
    if (items.length === 0) {
      continue;
    }

    const group = document.createElement("section");
    group.className = "daily-review-group";
    const heading = document.createElement("h3");
    heading.textContent = label;
    group.append(heading);

    const list = document.createElement("ol");
    for (const suggestion of items) {
      const item = document.createElement("li");
      item.dataset.suggestionId = suggestion.suggestion_id;
      item.dataset.suggestionKind = suggestion.suggestion_kind;

      const title = document.createElement("strong");
      title.textContent = suggestion.title;
      const action = document.createElement("p");
      action.textContent = suggestion.action;
      const rationale = document.createElement("p");
      rationale.textContent = suggestion.rationale;
      const evidence = document.createElement("p");
      evidence.className = "evidence-ref";
      evidence.textContent = `Evidence: ${suggestion.evidence_event_ids.join(", ") || suggestion.report_ids.join(", ")}.`;
      const controls = suggestionControls(suggestion.suggestion_id, actions);

      item.append(title, action, rationale, evidence, controls);
      list.append(item);
    }
    group.append(list);
    section.append(group);
  }

  if (review.limitations.length > 0) {
    const limitations = document.createElement("section");
    limitations.className = "daily-review-group daily-review-limitations";
    const heading = document.createElement("h3");
    heading.textContent = "Limitations";
    limitations.append(heading);
    const list = document.createElement("ul");
    for (const limitation of review.limitations) {
      const item = document.createElement("li");
      item.textContent = limitation;
      list.append(item);
    }
    limitations.append(list);
    section.append(limitations);
  }

  container.replaceChildren(section);
}

function suggestionControls(suggestion_id: string, actions: DailyReviewActions): HTMLElement {
  const controls = document.createElement("div");
  controls.className = "suggestion-controls";
  controls.append(
    button("Accept", () => actions.respondSuggestion({ suggestion_id, response: "accepted" })),
    button("Snooze", () =>
      actions.respondSuggestion({
        suggestion_id,
        response: "snoozed",
        snoozed_until: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      }),
    ),
    button("Dismiss", () => actions.respondSuggestion({ suggestion_id, response: "dismissed" })),
    button("Useful", () => actions.respondSuggestion({ suggestion_id, response: "rated-useful" })),
    button("Not useful", () => actions.respondSuggestion({ suggestion_id, response: "rated-not-useful" })),
  );
  return controls;
}

function button(label: string, onClick: () => void | Promise<void>): HTMLButtonElement {
  const control = document.createElement("button");
  control.type = "button";
  control.textContent = label;
  control.addEventListener("click", () => void onClick());
  return control;
}

function emptyState(titleText: string, bodyText: string): HTMLElement {
  const state = document.createElement("div");
  state.className = "daily-review-empty";
  const title = document.createElement("strong");
  title.textContent = titleText;
  const body = document.createElement("p");
  body.textContent = bodyText;
  state.append(title, body);
  return state;
}
