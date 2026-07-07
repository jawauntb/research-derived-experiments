import electron from "electron";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createDesktopIpcFacade, type DesktopIpcFacade } from "./ipc";
import { createDesktopRuntime, type DesktopRuntime } from "./main";

const { app, BrowserWindow, ipcMain } = electron;
const moduleDir = dirname(fileURLToPath(import.meta.url));
let runtime: DesktopRuntime | null = null;
let facade: DesktopIpcFacade | null = null;

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
  ipcMain.handle("inquiry:repair:accept", (_event, repair_id) => nextFacade.acceptRepair(repair_id));
  ipcMain.handle("inquiry:repair:answer", (_event, input) => nextFacade.answerRepair(input));
  ipcMain.handle("inquiry:repair:dismiss", (_event, input) => nextFacade.dismissRepair(input));
}

async function createWindow(): Promise<void> {
  const window = new BrowserWindow({
    width: 1180,
    height: 820,
    minWidth: 900,
    minHeight: 660,
    title: "Inquiry Black Box",
    backgroundColor: "#f6f7f9",
    webPreferences: {
      preload: join(moduleDir, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  await window.loadFile(join(moduleDir, "../renderer/index.html"));
}

void app.whenReady().then(async () => {
  runtime = createDesktopRuntime();
  facade = createDesktopIpcFacade(runtime);
  registerHandlers(facade);
  await createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      void createWindow();
    }
  });
});

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
