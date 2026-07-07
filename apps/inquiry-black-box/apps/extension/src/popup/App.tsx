import {
  defaultBridgeState,
  normalizeBridgeState,
  type BridgeState,
  type PrivacyToggles,
  type RecordingState,
} from "../lib/localBridge";
import { hashForTelemetry } from "../lib/telemetry";
import { renderPrivacyToggles } from "./PrivacyToggles";

type PopupState = BridgeState & {
  queueSize: number;
};

type RuntimeLike = {
  sendMessage(message: unknown, callback?: (response: unknown) => void): Promise<unknown> | void;
};

type TabsLike = {
  query(query: { active: boolean; currentWindow: boolean }, callback: (tabs: Array<{ url?: string }>) => void): void;
};

type ChromeLike = {
  runtime?: RuntimeLike;
  tabs?: TabsLike;
};

type PopupModel = {
  state: PopupState;
  siteHash: string | undefined;
  siteLabel: string;
};

export function mountPopup(root: HTMLElement, chromeApi = readChrome()): void {
  root.className = "popup-root";
  installStyles();

  if (!chromeApi?.runtime) {
    root.replaceChildren(emptyState("Extension runtime unavailable"));
    return;
  }

  void renderFromRuntime(root, chromeApi);
}

async function renderFromRuntime(root: HTMLElement, chromeApi: ChromeLike): Promise<void> {
  const model = await loadModel(chromeApi);
  render(root, model, chromeApi);
}

async function loadModel(chromeApi: ChromeLike): Promise<PopupModel> {
  const response = await sendRuntimeMessage(chromeApi.runtime, { type: "inquiry:get-popup-state" });
  const normalized = normalizeBridgeState(isRecord(response) ? response : undefined);
  const queueSize = isRecord(response) && typeof response.queueSize === "number" ? response.queueSize : 0;
  const activeUrl = await readActiveTabUrl(chromeApi.tabs);
  const site = siteInfo(activeUrl);

  return {
    state: {
      ...normalized,
      queueSize,
    },
    siteHash: site.hash,
    siteLabel: site.label,
  };
}

function render(root: HTMLElement, model: PopupModel, chromeApi: ChromeLike): void {
  const page = document.createElement("main");
  page.className = "popup";

  const header = document.createElement("header");
  header.className = "popup-header";
  const title = document.createElement("h1");
  title.textContent = "Inquiry Black Box";
  const status = document.createElement("span");
  status.className = `status status-${model.state.recordingState}`;
  status.textContent = statusLabel(model.state.recordingState);
  header.append(title, status);

  const queue = document.createElement("div");
  queue.className = "queue-row";
  queue.textContent = `${model.state.queueSize} queued`;

  const summary = document.createElement("section");
  summary.className = "pairing-summary";
  summary.append(
    summaryRow("Pairing", model.state.pairingToken ? "Paired" : "Not paired"),
    summaryRow("Endpoint", model.state.endpoint),
    summaryRow("Session", model.state.sessionId),
    summaryRow("Site", model.siteHash && model.state.disabledSiteHashes.includes(model.siteHash) ? "Disabled" : "Allowed"),
  );

  const controls = document.createElement("section");
  controls.className = "button-row";
  const canControl = Boolean(model.state.pairingToken);
  controls.append(
    actionButton("Record", () => setRecordingState(root, chromeApi, "recording"), !canControl),
    actionButton("Pause 15m", () => setRecordingState(root, chromeApi, "paused", Date.now() + 15 * 60_000), !canControl),
    actionButton("Stop", () => setRecordingState(root, chromeApi, "stopped"), !canControl),
  );

  const siteToggle = document.createElement("label");
  siteToggle.className = "toggle-row site-row";
  const siteCheckbox = document.createElement("input");
  siteCheckbox.type = "checkbox";
  siteCheckbox.disabled = !model.siteHash;
  siteCheckbox.checked = Boolean(model.siteHash && model.state.disabledSiteHashes.includes(model.siteHash));
  siteCheckbox.addEventListener("change", () => {
    if (!model.siteHash) {
      return;
    }

    void sendRuntimeMessage(chromeApi.runtime, {
      type: "inquiry:set-site-disabled",
      siteHash: model.siteHash,
      disabled: siteCheckbox.checked,
    }).then(() => renderFromRuntime(root, chromeApi));
  });
  const siteText = document.createElement("span");
  siteText.textContent = `Disable ${model.siteLabel}`;
  siteToggle.append(siteCheckbox, siteText);

  const pairing = pairingForm(model, chromeApi, () => renderFromRuntime(root, chromeApi));
  const togglesMount = document.createElement("section");
  renderPrivacyToggles(togglesMount, model.state.privacyToggles, async (privacyToggles) => {
    await updatePrivacyToggles(chromeApi, privacyToggles);
    await renderFromRuntime(root, chromeApi);
  });

  page.append(header, queue, summary, controls, siteToggle, togglesMount, pairing);
  root.replaceChildren(page);
}

function summaryRow(labelText: string, valueText: string): HTMLElement {
  const row = document.createElement("div");
  row.className = "pairing-summary__row";

  const label = document.createElement("span");
  label.textContent = labelText;

  const value = document.createElement("strong");
  value.textContent = valueText;

  row.append(label, value);
  return row;
}

function pairingForm(model: PopupModel, chromeApi: ChromeLike, onSaved: () => void | Promise<void>): HTMLElement {
  const form = document.createElement("form");
  form.className = "pairing-form";

  const token = document.createElement("input");
  token.type = "password";
  token.name = "token";
  token.placeholder = model.state.pairingToken ? "Paired" : "Pairing token";
  token.autocomplete = "off";

  const endpoint = document.createElement("input");
  endpoint.type = "url";
  endpoint.name = "endpoint";
  endpoint.value = model.state.endpoint;
  endpoint.spellcheck = false;

  const submit = document.createElement("button");
  submit.type = "submit";
  submit.textContent = "Pair";

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void sendRuntimeMessage(chromeApi.runtime, {
      type: "inquiry:set-pairing-token",
      token: token.value,
      endpoint: endpoint.value,
      sessionId: model.state.sessionId || defaultBridgeState().sessionId,
    }).then(onSaved);
  });

  form.append(token, endpoint, submit);
  return form;
}

function actionButton(label: string, onClick: () => void | Promise<void>, disabled = false): HTMLButtonElement {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.disabled = disabled;
  button.addEventListener("click", () => void onClick());
  return button;
}

async function setRecordingState(
  root: HTMLElement,
  chromeApi: ChromeLike,
  recordingState: RecordingState,
  pausedUntilMs?: number,
): Promise<void> {
  await sendRuntimeMessage(chromeApi.runtime, {
    type: "inquiry:set-recording-state",
    recordingState,
    pausedUntilMs,
  });
  await renderFromRuntime(root, chromeApi);
}

async function updatePrivacyToggles(chromeApi: ChromeLike, privacyToggles: PrivacyToggles): Promise<void> {
  await sendRuntimeMessage(chromeApi.runtime, {
    type: "inquiry:set-privacy-toggles",
    privacyToggles,
  });
}

function statusLabel(recordingState: RecordingState): string {
  if (recordingState === "recording") {
    return "Recording";
  }

  if (recordingState === "paused") {
    return "Paused";
  }

  return "Stopped";
}

function siteInfo(url: string | undefined): { hash?: string; label: string } {
  if (!url) {
    return { label: "this site" };
  }

  try {
    const parsed = new URL(url);
    return {
      hash: hashForTelemetry(parsed.hostname),
      label: parsed.hostname,
    };
  } catch {
    return { label: "this site" };
  }
}

function emptyState(message: string): HTMLElement {
  const element = document.createElement("main");
  element.className = "popup empty";
  element.textContent = message;
  return element;
}

function readChrome(): ChromeLike | null {
  return (globalThis as { chrome?: ChromeLike }).chrome ?? null;
}

async function sendRuntimeMessage(runtime: RuntimeLike | undefined, message: unknown): Promise<unknown> {
  if (!runtime) {
    return undefined;
  }

  return await new Promise((resolve, reject) => {
    try {
      const result = runtime.sendMessage(message, (response) => resolve(response));
      if (isPromiseLike(result)) {
        result.then(resolve, reject);
      }
    } catch (error) {
      reject(error);
    }
  });
}

async function readActiveTabUrl(tabs: TabsLike | undefined): Promise<string | undefined> {
  if (!tabs) {
    return undefined;
  }

  return await new Promise((resolve) => {
    tabs.query({ active: true, currentWindow: true }, (activeTabs) => resolve(activeTabs[0]?.url));
  });
}

function installStyles(): void {
  if (document.getElementById("inquiry-popup-styles")) {
    return;
  }

  const style = document.createElement("style");
  style.id = "inquiry-popup-styles";
  style.textContent = `
    :root {
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    body {
      margin: 0;
      min-width: 320px;
      background: #f8faf9;
      color: #16211d;
    }

    .popup {
      display: grid;
      gap: 12px;
      padding: 14px;
    }

    .popup-header {
      align-items: center;
      display: flex;
      justify-content: space-between;
      gap: 12px;
    }

    h1 {
      font-size: 16px;
      line-height: 1.2;
      margin: 0;
    }

    .status {
      border-radius: 999px;
      color: #fff;
      font-size: 12px;
      font-weight: 700;
      padding: 4px 8px;
    }

    .status-recording {
      background: #12715b;
    }

    .status-paused {
      background: #8a5a00;
    }

    .status-stopped {
      background: #616b66;
    }

    .queue-row {
      color: #5a665f;
      font-size: 12px;
    }

    .pairing-summary {
      border: 1px solid #dbe3de;
      border-radius: 8px;
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
      color: #5a665f;
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
      background: #18211d;
      border: 0;
      border-radius: 6px;
      color: #fff;
      cursor: pointer;
      font: inherit;
      font-size: 12px;
      font-weight: 700;
      min-height: 34px;
      padding: 0 10px;
    }

    button:hover {
      background: #2d3a34;
    }

    button:disabled {
      background: #cbd5cf;
      cursor: not-allowed;
    }

    .toggle-row {
      align-items: center;
      display: flex;
      gap: 8px;
      font-size: 13px;
      min-height: 28px;
    }

    .privacy-toggles {
      border: 1px solid #dbe3de;
      border-radius: 8px;
      display: grid;
      gap: 6px;
      margin: 0;
      padding: 10px;
    }

    legend {
      color: #3f4d46;
      font-size: 12px;
      font-weight: 700;
      padding: 0 4px;
    }

    .pairing-form {
      display: grid;
      gap: 8px;
      grid-template-columns: 1fr;
    }

    input[type="password"],
    input[type="url"] {
      border: 1px solid #cdd8d2;
      border-radius: 6px;
      box-sizing: border-box;
      font: inherit;
      min-height: 34px;
      padding: 0 9px;
      width: 100%;
    }
  `;
  document.head.append(style);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isPromiseLike<T>(value: unknown): value is Promise<T> {
  return typeof value === "object" && value !== null && "then" in value;
}

if (typeof document !== "undefined") {
  const root = document.getElementById("app");
  if (root) {
    mountPopup(root);
  }
}
