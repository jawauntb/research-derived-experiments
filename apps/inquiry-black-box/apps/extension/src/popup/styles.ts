import { inquiryCssVariableBlock, inquiryDarkCssVariableBlock } from "@inquiry/ui";

export function installPopupStyles(): void {
  if (document.getElementById("inquiry-popup-styles")) {
    return;
  }

  const style = document.createElement("style");
  style.id = "inquiry-popup-styles";
  style.textContent = `
    ${inquiryCssVariableBlock(":root")}
    ${inquiryDarkCssVariableBlock(":root[data-theme='dark']")}

    :root {
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    @media (prefers-color-scheme: dark) {
      ${inquiryDarkCssVariableBlock(":root")}

      :root {
        color-scheme: dark;
      }
    }

    body {
      margin: 0;
      min-width: 360px;
      width: 360px;
      background: var(--surface);
      color: var(--ink);
    }

    .popup {
      display: grid;
      gap: 12px;
      padding: 16px;
    }

    .popup-header {
      align-items: center;
      display: flex;
      justify-content: space-between;
      gap: 12px;
    }

    .popup-brand {
      display: grid;
      gap: 3px;
    }

    .popup-eyebrow {
      color: var(--teal);
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0.11em;
      line-height: 1.2;
      text-transform: uppercase;
    }

    h1 {
      font-size: 24px;
      letter-spacing: -0.03em;
      line-height: 1.2;
      margin: 0;
    }

    h2 {
      font-size: 14px;
      line-height: 1.25;
      margin: 0;
    }

    .status {
      border-radius: 999px;
      color: #fff;
      font-size: 12px;
      font-weight: 700;
      min-width: 92px;
      padding: 7px 10px;
      text-align: center;
    }

    .status-setup {
      background: var(--blue-soft);
      color: var(--blue);
    }

    .status-recording {
      background: var(--green);
    }

    .status-paused {
      background: var(--amber);
    }

    .status-stopped {
      background: #68737c;
    }

    .queue-row {
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
      margin-top: 2px;
      padding-top: 10px;
    }

    .popup-notice {
      background: var(--amber-soft);
      border: 1px solid var(--line);
      border-radius: 10px;
      color: var(--amber);
      font-size: 12px;
      line-height: 1.4;
      padding: 10px;
    }

    .popup-notice[hidden] {
      display: none;
    }

    .health-row {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
    }

    .transport-active {
      box-shadow: var(--shadow-pressed);
      outline: 2px solid var(--green);
    }

    details summary {
      box-sizing: border-box;
      cursor: pointer;
      font-size: 12px;
      font-weight: 700;
      margin: 0;
      min-height: 40px;
      padding: 10px 0;
    }

    details[open] > summary {
      margin-bottom: 10px;
    }

    .privacy-disclosure,
    .diagnostics-disclosure,
    .pairing-disclosure,
    .pairing-panel,
    .session-panel,
    .site-panel {
      background: var(--surface-raised);
      border: 1px solid var(--line);
      border-radius: 12px;
      box-shadow: var(--shadow-raised);
      padding: 12px;
    }

    .session-panel,
    .site-panel {
      display: grid;
      gap: 12px;
    }

    .section-heading {
      display: grid;
      gap: 4px;
    }

    .section-heading p {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
      margin: 0;
    }

    .pairing-panel {
      display: grid;
      gap: 12px;
      border-color: color-mix(in srgb, var(--teal) 48%, var(--line));
    }

    .pairing-actions {
      display: grid;
      gap: 8px;
      grid-template-columns: minmax(0, 1.65fr) minmax(0, 1fr);
    }

    .pairing-auto-button {
      background: var(--green);
      border-color: var(--green);
      color: #fff;
    }

    .pairing-open-desktop-button {
      background: var(--blue-soft);
      border-color: var(--blue-soft);
      color: var(--blue);
    }

    .pairing-summary {
      background: var(--surface-raised);
      border: 1px solid var(--line);
      border-radius: 10px;
      box-shadow: none;
      display: grid;
      gap: 6px;
      padding: 10px;
    }

    .pairing-summary__row {
      display: grid;
      gap: 4px;
      grid-template-columns: 76px minmax(0, 1fr);
      min-width: 0;
    }

    .pairing-summary__row span {
      color: var(--muted);
      font-size: 12px;
    }

    .pairing-summary__row strong {
      font-size: 12px;
      overflow-wrap: anywhere;
    }

    .button-row {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    button {
      background: var(--surface-raised);
      border: 1px solid var(--line);
      border-radius: 10px;
      box-shadow: none;
      color: var(--ink);
      cursor: pointer;
      font: inherit;
      font-size: 12px;
      font-weight: 700;
      min-height: 42px;
      padding: 0 10px;
    }

    .button-row button {
      background: #18211d;
      color: #fff;
    }

    button:hover {
      border-color: var(--line);
    }

    button:active:not(:disabled) {
      transform: translateY(1px);
    }

    button:disabled {
      background: var(--surface-inset);
      border-color: var(--line);
      color: var(--muted);
      cursor: not-allowed;
      opacity: 0.72;
    }

    button:focus-visible,
    input:focus-visible {
      box-shadow: var(--focus), var(--shadow-raised);
      outline: none;
    }

    .toggle-row {
      align-items: center;
      background: var(--surface-inset);
      border: 1px solid var(--line);
      border-radius: 10px;
      display: flex;
      gap: 8px;
      font-size: 13px;
      min-height: 44px;
      padding: 8px 10px;
    }

    input[type="checkbox"] {
      accent-color: var(--green);
      height: 16px;
      width: 16px;
    }

    .privacy-toggles {
      background: var(--surface-raised);
      border: 1px solid var(--line);
      border-radius: 10px;
      box-shadow: none;
      display: grid;
      gap: 6px;
      margin: 0;
      padding: 10px;
    }

    legend {
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      padding: 0 4px;
    }

    .pairing-form {
      display: grid;
      gap: 10px;
      grid-template-columns: 1fr;
    }

    .pairing-field {
      color: var(--muted);
      display: grid;
      font-size: 11px;
      font-weight: 700;
      gap: 5px;
    }

    .pairing-form button {
      background: var(--green);
      color: #fff;
    }

    input[type="password"],
    input[type="url"] {
      background: var(--surface-inset);
      border: 1px solid var(--line);
      border-radius: 10px;
      box-shadow: none;
      box-sizing: border-box;
      font: inherit;
      min-height: 42px;
      padding: 0 9px;
      width: 100%;
    }

    .site-row {
      overflow-wrap: anywhere;
    }
  `;
  document.head.append(style);
}
