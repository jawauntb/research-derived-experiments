import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { DesktopActivityProvider, DesktopActivitySnapshot } from "./desktopActivity";

type MacosAppIdentityResult = {
  app_name?: unknown;
  bundle_id?: unknown;
  process_id?: unknown;
};

type MacosWindowTitleResult = {
  window_title?: unknown;
  window_id?: unknown;
};

export type MacosActivityProviderOptions = {
  platform?: NodeJS.Platform;
  runJxa?: (script: string) => Promise<string>;
  timeoutMs?: number;
};

export function createMacosActivityProvider(options: MacosActivityProviderOptions = {}): DesktopActivityProvider {
  const platform = options.platform ?? process.platform;
  if (platform !== "darwin") {
    return unavailableProvider;
  }
  const runJxa = options.runJxa ?? ((script: string) => runJxaScript(script, options.timeoutMs ?? 1_000));

  return {
    async permissionStatus() {
      return (await readAppIdentity(runJxa)) ? "granted" : "denied";
    },
    async foregroundActivity(input) {
      return readForegroundActivity(runJxa, input.includeWindowTitle);
    },
  };
}

const unavailableProvider: DesktopActivityProvider = {
  permissionStatus: () => "unavailable",
  foregroundActivity: () => null,
};

const execFileAsync = promisify(execFile);

async function runJxaScript(script: string, timeoutMs: number): Promise<string> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const { stdout } = await execFileAsync("osascript", ["-l", "JavaScript", "-e", script], {
      encoding: "utf8",
      signal: controller.signal,
      timeout: timeoutMs,
      maxBuffer: 64 * 1024,
    });
    return stdout.trim();
  } finally {
    clearTimeout(timeout);
  }
}

async function readForegroundActivity(
  runJxa: (script: string) => Promise<string>,
  includeWindowTitle: boolean,
): Promise<DesktopActivitySnapshot | null> {
  const appIdentity = await readAppIdentity(runJxa);
  if (!appIdentity) {
    return null;
  }

  const snapshot: DesktopActivitySnapshot = {
    ...appIdentity,
    permission_status: "granted",
  };

  if (!includeWindowTitle) {
    return snapshot;
  }

  const windowTitle = await readWindowTitle(runJxa, appIdentity.process_id);
  if (!windowTitle) {
    return snapshot;
  }

  return {
    ...snapshot,
    ...windowTitle,
  };
}

async function readAppIdentity(runJxa: (script: string) => Promise<string>): Promise<Omit<DesktopActivitySnapshot, "permission_status"> | null> {
  try {
    const parsed = JSON.parse(await runJxa(appIdentityScript())) as MacosAppIdentityResult;
    if (typeof parsed.app_name !== "string" || parsed.app_name.length === 0) {
      return null;
    }

    return {
      app_name: parsed.app_name,
      ...(typeof parsed.bundle_id === "string" && parsed.bundle_id.length > 0 ? { bundle_id: parsed.bundle_id } : {}),
      ...(typeof parsed.process_id === "number" ? { process_id: parsed.process_id } : {}),
    };
  } catch {
    return null;
  }
}

async function readWindowTitle(
  runJxa: (script: string) => Promise<string>,
  processId: number | undefined,
): Promise<Pick<DesktopActivitySnapshot, "window_id" | "window_title"> | null> {
  try {
    const parsed = JSON.parse(await runJxa(windowTitleScript(processId))) as MacosWindowTitleResult;
    if (typeof parsed.window_title !== "string" || parsed.window_title.length === 0) {
      return null;
    }

    return {
      window_title: parsed.window_title,
      ...(typeof parsed.window_id === "string" && parsed.window_id.length > 0 ? { window_id: parsed.window_id } : {}),
    };
  } catch {
    return null;
  }
}

function appIdentityScript(): string {
  return `
    ObjC.import("AppKit");
    const app = $.NSWorkspace.sharedWorkspace.frontmostApplication;
    const result = {
      app_name: ObjC.unwrap(app.localizedName),
      bundle_id: ObjC.unwrap(app.bundleIdentifier),
      process_id: app.processIdentifier,
    };
    JSON.stringify(result);
  `;
}

function windowTitleScript(processId: number | undefined): string {
  const processSelector = processId === undefined
    ? "systemEvents.applicationProcesses.whose({ frontmost: true })[0]"
    : `systemEvents.applicationProcesses.whose({ unixId: ${processId} })[0]`;
  return `
    const systemEvents = Application("System Events");
    const frontProcess = ${processSelector};
    const windows = frontProcess.windows();
    const result = {
      window_title: "",
      window_id: "",
    };
    if (windows.length > 0) {
      result.window_title = windows[0].name();
    }
    JSON.stringify(result);
  `;
}
