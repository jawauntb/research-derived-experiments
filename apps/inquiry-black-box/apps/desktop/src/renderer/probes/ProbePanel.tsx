import type { RepairCandidate } from "@inquiry/signals";

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
    container.replaceChildren(section);
    return;
  }

  const question = document.createElement("h2");
  question.textContent = prompt.prompt;

  const details = document.createElement("p");
  details.textContent = `${prompt.action} (${Math.round(prompt.confidence * 100)}%). ${prompt.limitation}`;

  const textarea = document.createElement("textarea");
  textarea.rows = 4;

  const confidence = document.createElement("input");
  confidence.type = "range";
  confidence.min = "0";
  confidence.max = "1";
  confidence.step = "0.1";
  confidence.value = "0.5";

  const accept = document.createElement("button");
  accept.type = "button";
  accept.textContent = "Start";
  accept.addEventListener("click", () => {
    void actions.acceptRepair(prompt.repair_id);
  });

  const submit = document.createElement("button");
  submit.type = "button";
  submit.textContent = "Save";
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

  section.append(question, details, textarea, confidence, accept, submit, dismiss);
  container.replaceChildren(section);
}
