import type { RepairCandidate } from "@inquiry/signals";
import { confidenceBand } from "@inquiry/ui";

export type ProbePrompt = {
  probe_id: string;
  question: string;
  source_marker_id?: string;
};

export type ProbeAnswer = {
  repair_id: string;
  answer: string;
  confidence: number;
};

export type ProbePanelActions = {
  acceptRepair: (repair_id: RepairCandidate["repair_id"]) => void | Promise<void>;
  answerRepair: (answer: ProbeAnswer) => void | Promise<void>;
  dismissRepair: (repair_id: RepairCandidate["repair_id"]) => void | Promise<void>;
};

export function createRecallProbe(source_marker_id: string, question: string): ProbePrompt {
  return {
    probe_id: crypto.randomUUID(),
    source_marker_id,
    question,
  };
}

export function renderProbePanel(
  container: HTMLElement,
  prompt: RepairCandidate | null,
  actions: ProbePanelActions,
): void {
  const section = document.createElement("section");
  section.className = "probe-panel";

  if (!prompt) {
    const title = document.createElement("h2");
    title.textContent = "No repair prompt yet";
    const detail = document.createElement("p");
    detail.textContent = "Replay will suggest a repair prompt after enough evidence-backed markers appear.";
    section.append(title, detail);
    container.replaceChildren(section);
    return;
  }

  const question = document.createElement("h2");
  question.textContent = prompt.prompt;

  const details = document.createElement("p");
  const band = confidenceBand(prompt.confidence);
  details.textContent = `${prompt.action} (${band.label}; ${band.detail}). ${prompt.limitation}`;

  const answerLabel = document.createElement("label");
  answerLabel.className = "probe-field";
  answerLabel.htmlFor = "probe-answer";
  answerLabel.textContent = "Your answer";

  const textarea = document.createElement("textarea");
  textarea.id = "probe-answer";
  textarea.name = "probe-answer";
  textarea.rows = 4;
  textarea.setAttribute("aria-label", "Repair answer");

  const confidenceLabel = document.createElement("label");
  confidenceLabel.className = "probe-field";
  confidenceLabel.htmlFor = "probe-confidence";
  confidenceLabel.textContent = "Answer confidence";

  const confidence = document.createElement("input");
  confidence.id = "probe-confidence";
  confidence.type = "range";
  confidence.min = "0";
  confidence.max = "1";
  confidence.step = "0.1";
  confidence.value = "0.5";
  confidence.setAttribute("aria-label", "Answer confidence");

  const confidenceReadout = document.createElement("output");
  confidenceReadout.className = "probe-confidence-readout";
  confidenceReadout.setAttribute("for", "probe-confidence");
  const updateReadout = (): void => {
    const bandValue = confidenceBand(Number(confidence.value));
    confidenceReadout.textContent = `${bandValue.label} (${bandValue.detail})`;
  };
  confidence.addEventListener("input", updateReadout);
  updateReadout();

  const accept = document.createElement("button");
  accept.type = "button";
  accept.textContent = "Accept repair";
  accept.addEventListener("click", () => {
    void actions.acceptRepair(prompt.repair_id);
  });

  const submit = document.createElement("button");
  submit.type = "button";
  submit.textContent = "Save answer";
  submit.addEventListener("click", () => {
    void actions.answerRepair({
      repair_id: prompt.repair_id,
      answer: textarea.value,
      confidence: Number(confidence.value),
    });
  });

  const dismiss = document.createElement("button");
  dismiss.type = "button";
  dismiss.textContent = "Dismiss";
  dismiss.addEventListener("click", () => {
    void actions.dismissRepair(prompt.repair_id);
  });

  section.append(question, details, answerLabel, textarea, confidenceLabel, confidence, confidenceReadout, accept, submit, dismiss);
  container.replaceChildren(section);
}
