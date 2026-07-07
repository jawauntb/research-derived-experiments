import type { PrivacyToggles } from "../lib/localBridge";

export type PrivacyToggleChange = (toggles: PrivacyToggles) => void | Promise<void>;

const toggleLabels: Array<{ key: keyof PrivacyToggles; label: string }> = [
  { key: "browser", label: "Browser events" },
  { key: "typingMetrics", label: "Typing rhythm" },
  { key: "selection", label: "Selection metrics" },
  { key: "media", label: "Media events" },
];

export function renderPrivacyToggles(
  container: HTMLElement,
  toggles: PrivacyToggles,
  onChange: PrivacyToggleChange,
): void {
  const fieldset = document.createElement("fieldset");
  fieldset.className = "privacy-toggles";

  const legend = document.createElement("legend");
  legend.textContent = "Privacy";
  fieldset.append(legend);

  for (const toggle of toggleLabels) {
    const label = document.createElement("label");
    label.className = "toggle-row";

    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = toggles[toggle.key];
    input.addEventListener("change", () => {
      void onChange({
        ...toggles,
        [toggle.key]: input.checked,
      });
    });

    const text = document.createElement("span");
    text.textContent = toggle.label;

    label.append(input, text);
    fieldset.append(label);
  }

  container.replaceChildren(fieldset);
}
