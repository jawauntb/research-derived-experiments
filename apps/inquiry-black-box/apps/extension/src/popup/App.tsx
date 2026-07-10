import {
  createPairingChallenge,
  defaultBridgeState,
  isRecordingState,
  normalizeBridgeState,
  type BridgeState,
  type PrivacyToggles,
  type RecordingState,
} from "../lib/localBridge";
import { CONTENT_PING_MESSAGE, CONTENT_PONG_MESSAGE } from "../lib/messages";
import { hashForTelemetry } from "../lib/telemetry";
import {
  defaultSessionTitle,
  recordingIndicator,
  sessionTransportButtons,
  siteCaptureLabel,
  type SessionTransportButton,
} from "@inquiry/ui";
import { renderPrivacyToggles } from "./PrivacyToggles";
import { installPopupStyles } from "./styles";

type PopupState = BridgeState & {
  queueSize: number;
  desktopRecordingState?: RecordingState;
  desktopStatusWarning?: string;
};

type RuntimeLike = {
  sendMessage(message: unknown, callback?: (response: unknown) => void): Promise<unknown> | void;
  lastError?: { message?: string };
};

type ActiveTab = {
  id?: number;
  url?: string;
};

type TabsLike = {
  query(query: { active: boolean; currentWindow: boolean }, callback: (tabs: ActiveTab[]) => void): void;
  sendMessage?(tabId: number, message: unknown, callback?: (response: unknown) => void): Promise<unknown> | void;
};

type ScriptingLike = {
  executeScript(
    details: { target: { tabId: number }; files: string[]; world: "ISOLATED" },
    callback?: () => void,
  ): Promise<unknown> | void;
};

type ChromeLike = {
  runtime?: RuntimeLike;
  scripting?: ScriptingLike;
  tabs?: TabsLike;
};

export type PageListenerStatus = "attached" | "missing" | "unsupported";

type PageListenerCheck = {
  status: PageListenerStatus;
  detail?: string;
};

type PopupModel = {
  pageListener: PageListenerCheck;
  state: PopupState;
  siteHash: string | undefined;
  siteLabel: string;
};

export function mountPopup(root: HTMLElement, chromeApi = readChrome()): void {
  root.className = "popup-root";
  installPopupStyles();

  if (!chromeApi?.runtime) {
    root.replaceChildren(emptyState("Extension runtime unavailable"));
    return;
  }

  void renderFromRuntime(root, chromeApi);
}

async function renderFromRuntime(root: HTMLElement, chromeApi: ChromeLike, notice?: string): Promise<void> {
  const model = await loadModel(chromeApi);
  render(root, model, chromeApi, notice);
}

async function loadModel(chromeApi: ChromeLike): Promise<PopupModel> {
  const response = await sendRuntimeMessage(chromeApi.runtime, { type: "inquiry:get-popup-state" });
  const normalized = normalizeBridgeState(isRecord(response) ? response : undefined);
  const queueSize = isRecord(response) && typeof response.queueSize === "number" ? response.queueSize : 0;
  const desktopRecordingState =
    isRecord(response) && isRecordingState(response.desktopRecordingState) ? response.desktopRecordingState : undefined;
  const desktopStatusWarning =
    isRecord(response) && typeof response.desktopStatusWarning === "string" ? response.desktopStatusWarning : undefined;
  const activeTab = await readActiveTab(chromeApi.tabs);
  const site = siteInfo(activeTab?.url);
  const pageListener = await detectPageListener(chromeApi, activeTab);

  return {
    pageListener,
    state: {
      ...normalized,
      queueSize,
      ...(desktopRecordingState ? { desktopRecordingState } : {}),
      ...(desktopStatusWarning ? { desktopStatusWarning } : {}),
    },
    siteHash: site.hash,
    siteLabel: site.label,
  };
}

function render(root: HTMLElement, model: PopupModel, chromeApi: ChromeLike, notice?: string): void {
  const page = document.createElement("main");
  page.className = "popup";

  const paired = Boolean(model.state.pairingToken);
  const effectiveState = model.state.desktopRecordingState ?? model.state.recordingState;
  const indicator = recordingIndicator(effectiveState === "stopped" ? "stopped" : effectiveState);

  const header = document.createElement("header");
  header.className = "popup-header";
  const brand = document.createElement("div");
  brand.className = "popup-brand";
  const eyebrow = document.createElement("span");
  eyebrow.className = "popup-eyebrow";
  eyebrow.textContent = "Neurophenom lab";
  const title = document.createElement("h1");
  title.textContent = "Inquiry";
  brand.append(eyebrow, title);
  const status = document.createElement("span");
  status.className = `status ${paired ? `status-${indicator.state}` : "status-setup"}`;
  status.textContent = paired ? indicator.label : "Setup needed";
  status.setAttribute("role", "status");
  header.append(brand, status);

  const queue = document.createElement("div");
  queue.className = "queue-row";
  queue.textContent = queueLabel(model.state);
  queue.setAttribute("role", "status");

  const effectiveNotice = notice ?? (model.state.desktopStatusWarning ? `Desktop status unavailable: ${model.state.desktopStatusWarning}` : undefined);
  const noticeElement = document.createElement("div");
  noticeElement.className = "popup-notice";
  noticeElement.hidden = !effectiveNotice;
  noticeElement.textContent = effectiveNotice ?? "";

  const sessionPanel = document.createElement("section");
  sessionPanel.className = "session-panel";
  const sessionHeading = document.createElement("div");
  sessionHeading.className = "section-heading";
  const sessionTitle = document.createElement("h2");
  sessionTitle.textContent = "Session capture";
  const sessionHelp = document.createElement("p");
  sessionHelp.textContent = paired
    ? sessionHelper(indicator.state)
    : "Pair the desktop app to unlock recording controls.";
  sessionHeading.append(sessionTitle, sessionHelp);
  const controls = document.createElement("div");
  controls.className = "button-row";
  const canControl = paired;
  for (const button of sessionTransportButtons(indicator.state)) {
    if (button.command === "resume") {
      continue;
    }
    const mappedCommand = button.command === "record" ? "recording" : button.command;
    controls.append(
      transportButton(button, () => setRecordingState(root, chromeApi, mappedCommand as RecordingState, model.siteLabel), !canControl || !button.enabled),
    );
  }
  if (indicator.state === "paused") {
    const resume = sessionTransportButtons("paused").find((button) => button.command === "resume");
    if (resume) {
      controls.append(transportButton(resume, () => setRecordingState(root, chromeApi, "recording", model.siteLabel), !canControl || !resume.enabled));
    }
  }
  sessionPanel.append(sessionHeading, controls);
  if (paired || model.state.queueSize > 0) {
    sessionPanel.append(queue);
  }

  const sitePaused = Boolean(model.siteHash && model.state.disabledSiteHashes.includes(model.siteHash));
  const siteToggle = document.createElement("label");
  siteToggle.className = "toggle-row site-row";
  const siteCheckbox = document.createElement("input");
  siteCheckbox.type = "checkbox";
  siteCheckbox.disabled = !model.siteHash;
  siteCheckbox.checked = sitePaused;
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
  siteText.textContent = siteCaptureLabel(model.siteLabel, sitePaused);
  siteToggle.append(siteCheckbox, siteText);

  const health = document.createElement("div");
  health.className = "health-row";
  health.textContent = [
    paired ? "Desktop paired" : "Desktop not paired",
    `Page listener ${pageListenerLabel(model.pageListener).toLowerCase()}`,
    sitePaused ? "Capture paused" : "Capture allowed",
  ].join(" · ");

  const sitePanel = document.createElement("section");
  sitePanel.className = "site-panel";
  const siteHeading = document.createElement("div");
  siteHeading.className = "section-heading";
  const siteTitle = document.createElement("h2");
  siteTitle.textContent = "This page";
  const siteHelp = document.createElement("p");
  siteHelp.textContent = `Browser evidence for ${model.siteLabel}.`;
  siteHeading.append(siteTitle, siteHelp);
  sitePanel.append(siteHeading, siteToggle, health);

  const diagnostics = diagnosticsSection(model);
  const pairing = model.state.pairingToken
    ? pairingEditAction(model, chromeApi, () => renderFromRuntime(root, chromeApi))
    : pairingPanel(root, model, chromeApi);

  const togglesMount = document.createElement("details");
  togglesMount.className = "privacy-disclosure";
  const togglesSummary = document.createElement("summary");
  togglesSummary.textContent = "Privacy toggles";
  togglesMount.append(togglesSummary);
  const togglesBody = document.createElement("div");
  renderPrivacyToggles(togglesBody, model.state.privacyToggles, async (privacyToggles) => {
    await updatePrivacyToggles(chromeApi, privacyToggles);
    await renderFromRuntime(root, chromeApi);
  });
  togglesMount.append(togglesBody);

  page.append(header, noticeElement);
  if (!paired) {
    page.append(pairing);
  }
  page.append(sessionPanel, sitePanel, togglesMount, diagnostics);
  if (paired) {
    page.append(pairing);
  }
  root.replaceChildren(page);
}

function sessionHelper(state: "idle" | "recording" | "paused" | "stopped"): string {
  if (state === "recording") {
    return "Recording private browser evidence on this Mac.";
  }
  if (state === "paused") {
    return "Capture is paused until you resume.";
  }
  return "Start when you are ready to begin an inquiry session.";
}

function transportButton(
  button: SessionTransportButton,
  onClick: () => void | Promise<void>,
  disabled: boolean,
): HTMLButtonElement {
  const control = document.createElement("button");
  control.type = "button";
  control.textContent = button.label;
  control.disabled = disabled;
  if (button.active) {
    control.className = "transport-active";
    control.setAttribute("aria-pressed", "true");
  }
  control.addEventListener("click", () => void onClick());
  return control;
}

function diagnosticsSection(model: PopupModel): HTMLElement {
  const details = document.createElement("details");
  details.className = "diagnostics-disclosure";
  const summary = document.createElement("summary");
  summary.textContent = "Diagnostics";
  details.append(summary);
  const body = document.createElement("section");
  body.className = "pairing-summary";
  body.append(
    summaryRow("Endpoint", model.state.endpoint),
    summaryRow("Session", model.state.sessionId),
    summaryRow("Desktop", model.state.desktopRecordingState ? statusLabel(model.state.desktopRecordingState) : "Not checked"),
    summaryRow("Page listener", pageListenerLabel(model.pageListener)),
  );
  details.append(body);
  return details;
}

function pairingEditAction(model: PopupModel, chromeApi: ChromeLike, onSaved: () => void | Promise<void>): HTMLElement {
  const wrapper = document.createElement("details");
  wrapper.className = "pairing-disclosure";
  const summary = document.createElement("summary");
  summary.textContent = "Edit pairing";
  wrapper.append(summary, pairingForm(model, chromeApi, onSaved));
  return wrapper;
}

function pairingPanel(root: HTMLElement, model: PopupModel, chromeApi: ChromeLike): HTMLElement {
  const wrapper = document.createElement("section");
  wrapper.className = "pairing-panel";

  const heading = document.createElement("div");
  heading.className = "section-heading pairing-panel__heading";
  const title = document.createElement("h2");
  title.textContent = "Connect to the desktop";
  const help = document.createElement("p");
  help.textContent = "Pair once to keep browser traces local. No account or cloud sync is required.";
  heading.append(title, help);

  const autoButton = document.createElement("button");
  autoButton.type = "button";
  autoButton.className = "pairing-auto-button";
  autoButton.textContent = "Pair with local desktop";
  autoButton.addEventListener("click", async () => {
    const challenge = createPairingChallenge();
    autoButton.disabled = true;
    autoButton.textContent = "Opening desktop...";
    globalThis.open(pairingDeepLink(challenge), "_blank", "noopener");

    try {
      await autoPairWithRetry(chromeApi.runtime, challenge);
      await renderFromRuntime(root, chromeApi, "Paired with local desktop.");
    } catch (error) {
      await renderFromRuntime(root, chromeApi, `Desktop pairing failed: ${errorMessage(error)}`);
    }
  });

  const openDesktop = document.createElement("button");
  openDesktop.type = "button";
  openDesktop.className = "pairing-open-desktop-button";
  openDesktop.textContent = "Open desktop";
  openDesktop.addEventListener("click", () => {
    globalThis.open("inquiry-black-box://pair?source=chrome-extension", "_blank", "noopener");
  });

  const actions = document.createElement("div");
  actions.className = "pairing-actions";
  actions.append(autoButton, openDesktop);

  const manual = document.createElement("details");
  manual.className = "pairing-disclosure";
  const summary = document.createElement("summary");
  summary.textContent = "Manual token";
  manual.append(summary, pairingForm(model, chromeApi, () => renderFromRuntime(root, chromeApi)));

  wrapper.append(heading, actions, manual);
  return wrapper;
}

function queueLabel(state: PopupState): string {
  if (state.queueSize > 0) {
    return `${state.queueSize} queued for retry`;
  }

  if (!state.pairingToken) {
    return "Not paired";
  }

  return state.recordingState === "recording" ? "Queue clear" : "No queued events";
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

  form.append(
    pairingField("Pairing code", token),
    pairingField("Local bridge", endpoint),
    submit,
  );
  return form;
}

function pairingField(labelText: string, input: HTMLInputElement): HTMLLabelElement {
  const field = document.createElement("label");
  field.className = "pairing-field";
  const label = document.createElement("span");
  label.textContent = labelText;
  field.append(label, input);
  return field;
}

async function setRecordingState(
  root: HTMLElement,
  chromeApi: ChromeLike,
  recordingState: RecordingState,
  siteLabel?: string,
  pausedUntilMs?: number,
): Promise<void> {
  const response = await sendRuntimeMessage(chromeApi.runtime, {
    type: "inquiry:set-recording-state",
    recordingState,
    pausedUntilMs,
    ...(recordingState === "recording"
      ? {
          title: defaultSessionTitle(
            siteLabel && siteLabel !== "this site" ? { hostname: siteLabel } : undefined,
          ),
        }
      : {}),
  });
  if (isRecord(response) && response.ok === false) {
    await renderFromRuntime(root, chromeApi, `Desktop control failed: ${String(response.error ?? "unknown error")}`);
    return;
  }

  await detectPageListener(chromeApi);
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

export function pageListenerLabel(check: PageListenerCheck | PageListenerStatus): string {
  const status = typeof check === "string" ? check : check.status;
  const detail = typeof check === "string" ? undefined : check.detail;

  if (status === "attached") {
    return "Attached";
  }

  if (status === "unsupported") {
    return detail ? `Unavailable - ${detail}` : "Unavailable on this page";
  }

  return detail ? `Missing - ${detail}` : "Missing - reload tab";
}

export async function detectPageListener(
  chromeApi: ChromeLike,
  activeTab?: ActiveTab,
): Promise<PageListenerCheck> {
  const tab = activeTab ?? (await readActiveTab(chromeApi.tabs));
  if (!tab?.id || !canAttachToUrl(tab.url)) {
    return { status: "unsupported", detail: tab?.url ? "not an http tab" : "no active tab" };
  }

  const firstPing = await pingContentScript(chromeApi, tab.id);
  if (firstPing.ok) {
    return { status: "attached" };
  }

  const attach = await attachContentScript(chromeApi, tab.id);
  const secondPing = await pingContentScript(chromeApi, tab.id);
  if (secondPing.ok) {
    return { status: "attached" };
  }

  return {
    status: "missing",
    detail: attach.error ?? secondPing.error ?? firstPing.error ?? "reload tab",
  };
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
      const result = runtime.sendMessage(message, (response) => {
        const error = runtime.lastError?.message;
        if (error) {
          reject(new Error(error));
          return;
        }
        resolve(response);
      });
      if (isPromiseLike(result)) {
        result.then(resolve, reject);
      }
    } catch (error) {
      reject(error);
    }
  });
}

async function autoPairWithRetry(runtime: RuntimeLike | undefined, challenge: string): Promise<Record<string, unknown>> {
  let lastError = "desktop pairing did not complete";
  for (let attempt = 0; attempt < 8; attempt += 1) {
    try {
      const response = await sendRuntimeMessage(runtime, { type: "inquiry:auto-pair", challenge });
      if (isSuccessfulPairingResponse(response)) {
        return response;
      }
      if (isRecord(response) && response.ok === false) {
        lastError = String(response.error ?? lastError);
      } else {
        lastError = "desktop pairing returned an invalid response";
      }
    } catch (error) {
      lastError = errorMessage(error);
    }
    await sleep(attempt < 2 ? 250 : 500);
  }

  throw new Error(lastError);
}

function isSuccessfulPairingResponse(value: unknown): value is Record<string, unknown> {
  return isRecord(value) && value.ok === true && typeof value.pairingToken === "string" && value.pairingToken.length > 0;
}

function pairingDeepLink(challenge: string): string {
  const url = new URL("inquiry-black-box://pair");
  url.searchParams.set("source", "chrome-extension");
  url.searchParams.set("challenge", challenge);
  return url.toString();
}

async function sleep(ms: number): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function readActiveTab(tabs: TabsLike | undefined): Promise<ActiveTab | undefined> {
  if (!tabs) {
    return undefined;
  }

  return await new Promise((resolve) => {
    tabs.query({ active: true, currentWindow: true }, (activeTabs) => resolve(activeTabs[0]));
  });
}

async function pingContentScript(chromeApi: ChromeLike, tabId: number): Promise<{ ok: boolean; error?: string }> {
  const result = await sendTabMessage(chromeApi, tabId, { type: CONTENT_PING_MESSAGE });
  return { ok: isContentPong(result.response), ...(result.error ? { error: result.error } : {}) };
}

async function attachContentScript(chromeApi: ChromeLike, tabId: number): Promise<{ ok: boolean; error?: string }> {
  const scripting = chromeApi.scripting;
  if (!scripting?.executeScript) {
    return { ok: false, error: "scripting unavailable" };
  }

  return await new Promise((resolve) => {
    try {
      const result = scripting.executeScript(
        {
          target: { tabId },
          files: ["dist/content/index.js"],
          world: "ISOLATED",
        },
        () => {
          const error = chromeApi.runtime?.lastError?.message;
          resolve(error ? { ok: false, error } : { ok: true });
        },
      );
      if (isPromiseLike(result)) {
        result.then(() => resolve({ ok: true }), (error) => resolve({ ok: false, error: errorMessage(error) }));
      }
    } catch (error) {
      resolve({ ok: false, error: errorMessage(error) });
    }
  });
}

async function sendTabMessage(
  chromeApi: ChromeLike,
  tabId: number,
  message: unknown,
): Promise<{ response?: unknown; error?: string }> {
  const tabs = chromeApi.tabs;
  const sendMessage = tabs?.sendMessage;
  if (!sendMessage) {
    return { error: "tabs permission unavailable" };
  }

  return await new Promise((resolve) => {
    try {
      const result = sendMessage.call(tabs, tabId, message, (response) => {
        const error = chromeApi.runtime?.lastError?.message;
        resolve(error ? { error } : { response });
      });
      if (isPromiseLike(result)) {
        result.then((response) => resolve({ response }), (error) => resolve({ error: errorMessage(error) }));
      }
    } catch (error) {
      resolve({ error: errorMessage(error) });
    }
  });
}

function canAttachToUrl(url: string | undefined): boolean {
  if (!url) {
    return false;
  }

  try {
    const parsed = new URL(url);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

function isContentPong(value: unknown): value is { type: typeof CONTENT_PONG_MESSAGE; ok: true } {
  return (
    typeof value === "object" &&
    value !== null &&
    (value as { type?: unknown }).type === CONTENT_PONG_MESSAGE &&
    (value as { ok?: unknown }).ok === true
  );
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
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
