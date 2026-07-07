export type ProbePrompt = {
  probe_id: string;
  question: string;
  source_marker_id?: string;
};

export type ProbeAnswer = {
  probe_id: string;
  answer: string;
  confidence: number;
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
  prompt: ProbePrompt | null,
  onAnswer: (answer: ProbeAnswer) => void | Promise<void>,
): void {
  const section = document.createElement("section");
  section.className = "probe-panel";

  if (!prompt) {
    container.replaceChildren(section);
    return;
  }

  const question = document.createElement("h2");
  question.textContent = prompt.question;

  const textarea = document.createElement("textarea");
  textarea.rows = 4;

  const confidence = document.createElement("input");
  confidence.type = "range";
  confidence.min = "0";
  confidence.max = "1";
  confidence.step = "0.1";
  confidence.value = "0.5";

  const submit = document.createElement("button");
  submit.type = "button";
  submit.textContent = "Save";
  submit.addEventListener("click", () => {
    void onAnswer({
      probe_id: prompt.probe_id,
      answer: textarea.value,
      confidence: Number(confidence.value),
    });
  });

  section.append(question, textarea, confidence, submit);
  container.replaceChildren(section);
}
