import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { DesktopActivityProvider, DesktopActivitySnapshot } from "./desktopActivity";

type MacosForegroundResult = {
  app_name?: unknown;
  bundle_id?: unknown;
  process_id?: unknown;
  window_title?: unknown;
};

export function createMacosActivityProvider(): DesktopActivityProvider {
  if (process.platform !== "darwin") {
    return unavailableProvider;
  }

  return {
    async permissionStatus() {
      return (await readForegroundActivity(false)) ? "granted" : "denied";
    },
    async foregroundActivity(input) {
      return readForegroundActivity(input.includeWindowTitle);
    },
  };
}

const unavailableProvider: DesktopActivityProvider = {
  permissionStatus: () => "unavailable",
  foregroundActivity: () => null,
};

const execFileAsync = promisify(execFile);

async function readForegroundActivity(includeWindowTitle: boolean): Promise<DesktopActivitySnapshot | null> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 1_000);
  try {
    const script = `
      const includeWindowTitle = ${includeWindowTitle ? "true" : "false"};
      const systemEvents = Application("System Events");
      const frontProcess = systemEvents.applicationProcesses.whose({ frontmost: true })[0];
      const result = {
        app_name: frontProcess.name(),
        bundle_id: frontProcess.bundleIdentifier(),
        process_id: frontProcess.unixId(),
        window_title: "",
      };
      if (includeWindowTitle) {
        const windows = frontProcess.windows();
        if (windows.length > 0) {
          result.window_title = windows[0].name();
        }
      }
      JSON.stringify(result);
    `;
    const { stdout } = await execFileAsync("osascript", ["-l", "JavaScript", "-e", script], {
      encoding: "utf8",
      signal: controller.signal,
      timeout: 1_000,
      maxBuffer: 64 * 1024,
    });
    const parsed = JSON.parse(stdout) as MacosForegroundResult;
    if (typeof parsed.app_name !== "string" || parsed.app_name.length === 0) {
      return null;
    }

    return {
      app_name: parsed.app_name,
      ...(typeof parsed.bundle_id === "string" && parsed.bundle_id.length > 0 ? { bundle_id: parsed.bundle_id } : {}),
      ...(typeof parsed.process_id === "number" ? { process_id: parsed.process_id } : {}),
      ...(includeWindowTitle && typeof parsed.window_title === "string" && parsed.window_title.length > 0
        ? { window_title: parsed.window_title }
        : {}),
      permission_status: "granted",
    };
  } catch {
    return null;
  } finally {
    clearTimeout(timeout);
  }
}
