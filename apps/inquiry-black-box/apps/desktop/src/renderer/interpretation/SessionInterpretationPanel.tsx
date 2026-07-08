import type { RedactedSummarySubmission } from "../../main/cloud/redactedSummary";
import type { SessionInterpretationReport } from "../../main/reports/sessionInterpretation";

export type SessionInterpretationActions = {
  cloudSyncEnabled: boolean;
  redactedSummary?: RedactedSummarySubmission | null;
  documentContextEnabled?: boolean;
  requestRedactedSummary?: (input?: { additionalContext?: string }) => void | Promise<void>;
};

export function renderSessionInterpretationPanel(
  container: HTMLElement,
  interpretation: SessionInterpretationReport | null | undefined,
  actions: SessionInterpretationActions = { cloudSyncEnabled: false },
): void {
  const section = document.createElement("section");
  section.className = "interpretation-panel";

  const title = document.createElement("h2");
  title.textContent = "Session Interpretation";
  section.append(title);

  if (!interpretation) {
    section.append(emptyState("No interpretation yet", "Stop or refresh a session to turn replay evidence into next actions."));
    container.replaceChildren(section);
    return;
  }

  const summary = document.createElement("p");
  summary.className = "interpretation-summary";
  summary.textContent = interpretation.summary;
  section.append(summary);

  section.append(redactedSummaryAction(actions));

  const themes = document.createElement("ol");
  themes.className = "interpretation-themes";
  for (const theme of interpretation.themes.slice(0, 5)) {
    const item = document.createElement("li");
    item.dataset.themeKind = theme.kind;

    const heading = document.createElement("strong");
    heading.textContent = `${theme.title} (${Math.round(theme.confidence * 100)}%)`;
    const detail = document.createElement("p");
    detail.textContent = theme.detail;
    const evidence = document.createElement("p");
    evidence.className = "evidence-ref";
    evidence.textContent = `Evidence events: ${theme.evidence_event_ids.join(", ") || "none"}.`;

    item.append(heading, detail, evidence);
    themes.append(item);
  }
  section.append(themes);

  if (interpretation.next_actions.length > 0) {
    const actions = document.createElement("ul");
    actions.className = "interpretation-actions";
    for (const action of interpretation.next_actions) {
      const item = document.createElement("li");
      item.textContent = action.action;
      actions.append(item);
    }
    section.append(actions);
  }

  const limitations = document.createElement("p");
  limitations.className = "interpretation-limitations";
  limitations.textContent = interpretation.limitations[0] ?? "Evidence-linked local interpretation only.";
  section.append(limitations);

  container.replaceChildren(section);
}

function redactedSummaryAction(actions: SessionInterpretationActions): HTMLElement {
  const panel = document.createElement("div");
  panel.className = "interpretation-llm";

  const button = document.createElement("button");
  button.type = "button";
  button.className = "interpretation-llm__button";
  button.textContent = "Analyze and ask about your data";
  button.disabled = !actions.cloudSyncEnabled || !actions.requestRedactedSummary;

  const contextInput = document.createElement("textarea");
  contextInput.className = "interpretation-llm__context";
  contextInput.rows = 3;
  contextInput.maxLength = 2_000;
  contextInput.placeholder = "Add context for this analysis...";
  contextInput.setAttribute("aria-label", "Additional analysis context");
  contextInput.disabled = !actions.cloudSyncEnabled || !actions.requestRedactedSummary;

  button.addEventListener("click", () => {
    const additionalContext = contextInput.value.trim();
    void actions.requestRedactedSummary?.(additionalContext ? { additionalContext } : undefined);
  });

  const status = document.createElement("p");
  status.className = "interpretation-llm__status";
  if (actions.redactedSummary) {
    status.textContent = actions.redactedSummary.message;
  } else if (!actions.cloudSyncEnabled) {
    status.textContent = "Cloud sync is off; no model request will be sent.";
  } else if (actions.documentContextEnabled) {
    status.textContent = "Opted-in page/selection text and your optional context can be submitted for analysis.";
  } else {
    status.textContent = "Only redacted counts, themes, actions, and limitations are submitted for analysis.";
  }

  panel.append(button, contextInput, status);
  return panel;
}

function emptyState(titleText: string, bodyText: string): HTMLElement {
  const state = document.createElement("div");
  state.className = "interpretation-empty";
  const title = document.createElement("strong");
  title.textContent = titleText;
  const body = document.createElement("p");
  body.textContent = bodyText;
  state.append(title, body);
  return state;
}
