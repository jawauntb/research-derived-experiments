import electron from "electron";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { findInquiryDeepLinkArg, INQUIRY_DEEP_LINK_PROTOCOL, type InquiryDeepLink } from "./deepLink";
import { createDesktopIpcFacade, type DesktopIpcFacade } from "./ipc";
import { createElectronDesktopNotifier } from "./notifications/desktopNotifier";
import { createDesktopRuntime, type DesktopRuntime } from "./main";

const { app, BrowserWindow, ipcMain } = electron;
const moduleDir = dirname(fileURLToPath(import.meta.url));
let runtime: DesktopRuntime | null = null;
let facade: DesktopIpcFacade | null = null;
let mainWindow: electron.BrowserWindow | null = null;
let pendingDeepLink: InquiryDeepLink | null = findInquiryDeepLinkArg(process.argv);

registerProtocolClient();
const hasSingleInstanceLock = app.requestSingleInstanceLock();
if (!hasSingleInstanceLock) {
  app.quit();
} else {
  app.on("second-instance", (_event, argv) => {
    pendingDeepLink = findInquiryDeepLinkArg(argv) ?? pendingDeepLink;
    void focusOrCreateWindow();
  });

  void app.whenReady().then(async () => {
    runtime = createDesktopRuntime({ notifier: createElectronDesktopNotifier() });
    facade = createDesktopIpcFacade(runtime);
    registerHandlers(facade);
    await focusOrCreateWindow();

    app.on("activate", () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        void createWindow();
      } else {
        void focusOrCreateWindow();
      }
    });
  });
}

app.on("open-url", (event, url) => {
  event.preventDefault();
  pendingDeepLink = findInquiryDeepLinkArg([url]) ?? pendingDeepLink;
  void focusOrCreateWindow();
});

function registerHandlers(nextFacade: DesktopIpcFacade): void {
  ipcMain.handle("inquiry:status", () => nextFacade.status());
  ipcMain.handle("inquiry:session:current", () => nextFacade.currentSession());
  ipcMain.handle("inquiry:session:start", (_event, input) => nextFacade.startSession(input));
  ipcMain.handle("inquiry:session:pause", () => nextFacade.pauseSession());
  ipcMain.handle("inquiry:session:resume", () => nextFacade.resumeSession());
  ipcMain.handle("inquiry:session:stop", () => nextFacade.stopSession());
  ipcMain.handle("inquiry:session:label", (_event, input) => nextFacade.addLabel(input));
  ipcMain.handle("inquiry:camera:append-feature-window", (_event, featureWindow) =>
    nextFacade.appendCameraFeatureWindow(featureWindow),
  );
  ipcMain.handle("inquiry:privacy:settings", () => nextFacade.currentSettings());
  ipcMain.handle("inquiry:privacy:set-signal-enabled", (_event, key, enabled) =>
    nextFacade.setSignalEnabled(key, enabled),
  );
  ipcMain.handle("inquiry:privacy:export", () => nextFacade.exportSession());
  ipcMain.handle("inquiry:privacy:delete", () => nextFacade.deleteSession());
  ipcMain.handle("inquiry:replay:report", () => nextFacade.replayReport());
  ipcMain.handle("inquiry:replay:demo", () => nextFacade.demoReplayReport());
  ipcMain.handle("inquiry:sessions:history", () => nextFacade.listSessionHistory());
  ipcMain.handle("inquiry:sessions:select", (_event, session_id) => nextFacade.selectSession(session_id));
  ipcMain.handle("inquiry:interpretation:session", () => nextFacade.sessionInterpretation());
  ipcMain.handle("inquiry:interpretation:redacted-summary", (_event, input) => nextFacade.requestRedactedSummary(input));
  ipcMain.handle("inquiry:interpretation:daily", () => nextFacade.dailyReview());
  ipcMain.handle("inquiry:interpretation:daily-refresh", () => nextFacade.refreshDailyReview());
  ipcMain.handle("inquiry:suggestion:respond", (_event, input) => nextFacade.respondSuggestion(input));
  ipcMain.handle("inquiry:repair:accept", (_event, repair_id) => nextFacade.acceptRepair(repair_id));
  ipcMain.handle("inquiry:repair:answer", (_event, input) => nextFacade.answerRepair(input));
  ipcMain.handle("inquiry:repair:dismiss", (_event, input) => nextFacade.dismissRepair(input));
}

async function createWindow(): Promise<electron.BrowserWindow> {
  const window = new BrowserWindow({
    width: 1180,
    height: 820,
    minWidth: 900,
    minHeight: 660,
    title: "Inquiry Black Box",
    backgroundColor: "#f6f7f9",
    icon: join(moduleDir, "../../assets/icon.png"),
    webPreferences: {
      preload: join(moduleDir, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  mainWindow = window;
  window.on("closed", () => {
    if (mainWindow === window) {
      mainWindow = null;
    }
  });
  await window.loadFile(join(moduleDir, "../renderer/index.html"));
  consumePendingDeepLink(window);
  return window;
}

async function focusOrCreateWindow(): Promise<void> {
  if (!app.isReady()) {
    return;
  }

  const window = mainWindow ?? (await createWindow());
  if (window.isMinimized()) {
    window.restore();
  }
  window.show();
  window.focus();
  consumePendingDeepLink(window);
}

function consumePendingDeepLink(window: electron.BrowserWindow): void {
  if (!pendingDeepLink) {
    return;
  }

  if (pendingDeepLink.action === "pair" && pendingDeepLink.challenge) {
    try {
      runtime?.pairingChallenges.approveChallenge(pendingDeepLink.challenge);
    } catch {
      // Invalid challenges still focus the app, but they must not mint a bridge token.
    }
  }
  window.webContents.send("inquiry:deep-link", pendingDeepLink);
  pendingDeepLink = null;
}

function registerProtocolClient(): void {
  if (process.defaultApp) {
    const script = process.argv[1];
    if (script) {
      app.setAsDefaultProtocolClient(INQUIRY_DEEP_LINK_PROTOCOL, process.execPath, [script]);
      return;
    }
  }

  app.setAsDefaultProtocolClient(INQUIRY_DEEP_LINK_PROTOCOL);
}

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  runtime?.stop();
  runtime = null;
  facade = null;
});
