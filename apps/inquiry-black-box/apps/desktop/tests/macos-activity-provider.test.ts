import { describe, expect, test } from "bun:test";
import { createMacosActivityProvider } from "../src/main/activity/macosActivityProvider";

describe("macOS desktop activity provider", () => {
  test("reports unavailable off macOS", async () => {
    const provider = createMacosActivityProvider({ platform: "linux" });

    expect(await provider.permissionStatus()).toBe("unavailable");
    expect(await provider.foregroundActivity({ includeWindowTitle: false })).toBeNull();
  });

  test("uses NSWorkspace app identity without touching System Events when titles are off", async () => {
    const scripts: string[] = [];
    const provider = createMacosActivityProvider({
      platform: "darwin",
      runJxa: async (script) => {
        scripts.push(script);
        if (script.includes("NSWorkspace")) {
          return JSON.stringify({
            app_name: "Cursor",
            bundle_id: "com.todesktop.230313mzl4w4u92",
            process_id: 101,
          });
        }
        throw new Error("System Events should not be called");
      },
    });

    const snapshot = await provider.foregroundActivity({ includeWindowTitle: false });

    expect(snapshot).toEqual({
      app_name: "Cursor",
      bundle_id: "com.todesktop.230313mzl4w4u92",
      process_id: 101,
      permission_status: "granted",
    });
    expect(scripts).toHaveLength(1);
    expect(scripts[0]).toContain("NSWorkspace");
  });

  test("keeps app metadata when System Events denies optional window title access", async () => {
    const provider = createMacosActivityProvider({
      platform: "darwin",
      runJxa: async (script) => {
        if (script.includes("NSWorkspace")) {
          return JSON.stringify({
            app_name: "Safari",
            bundle_id: "com.apple.Safari",
            process_id: 202,
          });
        }
        if (script.includes("System Events")) {
          throw new Error("not authorized to send Apple events");
        }
        throw new Error("unexpected script");
      },
    });

    const snapshot = await provider.foregroundActivity({ includeWindowTitle: true });

    expect(snapshot).toEqual({
      app_name: "Safari",
      bundle_id: "com.apple.Safari",
      process_id: 202,
      permission_status: "granted",
    });
  });

  test("adds window title only when the System Events title probe succeeds", async () => {
    const provider = createMacosActivityProvider({
      platform: "darwin",
      runJxa: async (script) => {
        if (script.includes("NSWorkspace")) {
          return JSON.stringify({
            app_name: "Terminal",
            bundle_id: "com.apple.Terminal",
            process_id: 303,
          });
        }
        if (script.includes("System Events")) {
          expect(script).toContain("unixId: 303");
          return JSON.stringify({ window_title: "zsh" });
        }
        throw new Error("unexpected script");
      },
    });

    const snapshot = await provider.foregroundActivity({ includeWindowTitle: true });

    expect(snapshot).toEqual({
      app_name: "Terminal",
      bundle_id: "com.apple.Terminal",
      process_id: 303,
      window_title: "zsh",
      permission_status: "granted",
    });
  });

  test("maps NSWorkspace probe failures to denied permission", async () => {
    const provider = createMacosActivityProvider({
      platform: "darwin",
      runJxa: async () => {
        throw new Error("NSWorkspace probe failed");
      },
    });

    expect(await provider.permissionStatus()).toBe("denied");
    expect(await provider.foregroundActivity({ includeWindowTitle: false })).toBeNull();
  });
});
