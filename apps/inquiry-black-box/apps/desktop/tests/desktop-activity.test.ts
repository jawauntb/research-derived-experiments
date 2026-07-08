import { describe, expect, test } from "bun:test";
import type { DesktopPermissionStatus } from "@inquiry/schema";
import { createInquiryDatabase } from "../src/main/db";
import { createDesktopIpcFacade } from "../src/main/ipc";
import { createDesktopRuntime } from "../src/main/main";
import type { DesktopActivityProvider, DesktopActivitySnapshot } from "../src/main/activity/desktopActivity";

type MutableClock = {
  set: (nextMs: number) => void;
  nowMs: () => number;
  nowIso: () => string;
};

function createMutableClock(initialMs = 0): MutableClock {
  let currentMs = initialMs;
  return {
    set(nextMs) {
      currentMs = nextMs;
    },
    nowMs() {
      return currentMs;
    },
    nowIso() {
      return new Date(currentMs).toISOString();
    },
  };
}

function createFakeProvider(
  snapshots: DesktopActivitySnapshot[],
  permissionStatus: DesktopPermissionStatus = "granted",
): DesktopActivityProvider & { foregroundCalls: number; permissionCalls: number; lastIncludeWindowTitle: boolean | null } {
  return {
    foregroundCalls: 0,
    permissionCalls: 0,
    lastIncludeWindowTitle: null,
    permissionStatus() {
      this.permissionCalls += 1;
      return permissionStatus;
    },
    foregroundActivity(input) {
      this.foregroundCalls += 1;
      this.lastIncludeWindowTitle = input.includeWindowTitle;
      return snapshots.shift() ?? null;
    },
  };
}

function createRuntimeWithActivity(provider: DesktopActivityProvider, clock: MutableClock) {
  const database = createInquiryDatabase();
  const runtime = createDesktopRuntime({
    database,
    pairingSecret: "desktop-activity-secret",
    startServer: false,
    desktopActivityProvider: provider,
    desktopActivityClock: clock,
    desktopActivityAutoPoll: false,
  });
  return { database, runtime, facade: createDesktopIpcFacade(runtime) };
}

describe("desktop activity collector", () => {
  test("keeps desktop activity off by default and does not poll while recording", async () => {
    const clock = createMutableClock(1_000);
    const provider = createFakeProvider([
      {
        app_name: "Cursor",
        bundle_id: "com.todesktop.230313mzl4w4u92",
        permission_status: "granted",
      },
    ]);
    const { database, runtime, facade } = createRuntimeWithActivity(provider, clock);
    const session = await facade.startSession({ title: "Disabled desktop activity" });

    await runtime.desktopActivity.tick();

    expect(provider.permissionCalls).toBe(0);
    expect(provider.foregroundCalls).toBe(0);
    expect(database.listEvents(session.session_id).map((event) => event.event_type)).toEqual(["session.started"]);
    runtime.stop();
  });

  test("coalesces app focus spans while enabled and recording", async () => {
    const clock = createMutableClock();
    const provider = createFakeProvider([
      {
        app_name: "Cursor",
        bundle_id: "com.todesktop.230313mzl4w4u92",
        process_id: 101,
        window_title: "Draft.md",
        permission_status: "granted",
      },
      {
        app_name: "Cursor",
        bundle_id: "com.todesktop.230313mzl4w4u92",
        process_id: 101,
        window_title: "Draft.md",
        permission_status: "granted",
      },
      {
        app_name: "Terminal",
        bundle_id: "com.apple.Terminal",
        process_id: 202,
        permission_status: "granted",
      },
    ]);
    const { database, runtime, facade } = createRuntimeWithActivity(provider, clock);
    await facade.setSignalEnabled("desktopActivity", true);
    const session = await facade.startSession({ title: "Enabled desktop activity" });

    clock.set(1_000);
    await runtime.desktopActivity.tick();
    clock.set(1_500);
    await runtime.desktopActivity.tick();
    clock.set(3_000);
    await runtime.desktopActivity.tick();
    clock.set(4_000);
    await facade.stopSession();

    const desktopEvents = database.listEvents(session.session_id).filter((event) => event.source === "desktop-activity");
    expect(provider.lastIncludeWindowTitle).toBe(false);
    expect(desktopEvents.map((event) => event.event_type)).toEqual(["desktop.app_focus", "desktop.app_focus"]);
    expect(desktopEvents[0]?.payload).toMatchObject({
      app_name: "Cursor",
      bundle_id: "com.todesktop.230313mzl4w4u92",
      focus_started_monotonic_ms: 1_000,
      focus_ended_monotonic_ms: 3_000,
      duration_ms: 2_000,
      permission_status: "granted",
    });
    expect(JSON.stringify(desktopEvents[0]?.payload)).not.toContain("Draft.md");
    expect(desktopEvents[1]?.payload).toMatchObject({
      app_name: "Terminal",
      focus_started_monotonic_ms: 3_000,
      focus_ended_monotonic_ms: 4_000,
      duration_ms: 1_000,
    });
    runtime.stop();
  });

  test("flushes the active span before pause and stops polling while paused", async () => {
    const clock = createMutableClock();
    const provider = createFakeProvider([
      {
        app_name: "Preview",
        bundle_id: "com.apple.Preview",
        process_id: 303,
        permission_status: "granted",
      },
      {
        app_name: "Slack",
        bundle_id: "com.tinyspeck.slackmacgap",
        process_id: 404,
        permission_status: "granted",
      },
    ]);
    const { database, runtime, facade } = createRuntimeWithActivity(provider, clock);
    await facade.setSignalEnabled("desktopActivity", true);
    const session = await facade.startSession({ title: "Pause desktop activity" });

    clock.set(500);
    await runtime.desktopActivity.tick();
    clock.set(2_000);
    await facade.pauseSession();
    await runtime.desktopActivity.tick();

    const desktopEvents = database.listEvents(session.session_id).filter((event) => event.source === "desktop-activity");
    expect(desktopEvents).toHaveLength(1);
    expect(desktopEvents[0]?.payload).toMatchObject({
      app_name: "Preview",
      focus_started_monotonic_ms: 500,
      focus_ended_monotonic_ms: 2_000,
      duration_ms: 1_500,
    });
    expect(provider.foregroundCalls).toBe(1);
    runtime.stop();
  });

  test("starts and stops desktop capture when privacy settings change mid-recording", async () => {
    const clock = createMutableClock();
    const provider = createFakeProvider([
      {
        app_name: "Cursor",
        bundle_id: "com.todesktop.230313mzl4w4u92",
        process_id: 101,
        permission_status: "granted",
      },
      {
        app_name: "Terminal",
        bundle_id: "com.apple.Terminal",
        process_id: 202,
        permission_status: "granted",
      },
    ]);
    const { database, runtime, facade } = createRuntimeWithActivity(provider, clock);
    const session = await facade.startSession({ title: "Toggle desktop activity" });

    clock.set(1_000);
    await runtime.desktopActivity.tick();
    expect(provider.foregroundCalls).toBe(0);

    await facade.setSignalEnabled("desktopActivity", true);
    await runtime.desktopActivity.tick();
    expect(provider.foregroundCalls).toBe(1);
    expect((await facade.currentSettings()).desktop_activity).toMatchObject({
      active: true,
      last_app_name: "Cursor",
    });

    clock.set(2_000);
    await facade.setSignalEnabled("desktopActivity", false);
    await runtime.desktopActivity.tick();

    const settings = await facade.currentSettings();
    const desktopEvents = database.listEvents(session.session_id).filter((event) => event.source === "desktop-activity");
    expect(settings.signals.desktopActivity).toBe(false);
    expect(settings.signals.desktopWindowTitles).toBe(false);
    expect(settings.desktop_activity).toMatchObject({
      active: false,
      permission_status: "not_requested",
    });
    expect(settings.desktop_activity?.last_app_name).toBeUndefined();
    expect(provider.foregroundCalls).toBe(1);
    expect(desktopEvents).toHaveLength(1);
    expect(desktopEvents[0]?.payload).toMatchObject({
      app_name: "Cursor",
      focus_started_monotonic_ms: 1_000,
      focus_ended_monotonic_ms: 2_000,
    });
    runtime.stop();
  });

  test("enforces dependent desktop signal settings in the IPC path", async () => {
    const clock = createMutableClock();
    const provider = createFakeProvider([]);
    const { runtime, facade } = createRuntimeWithActivity(provider, clock);

    let settings = await facade.setSignalEnabled("desktopWindowTitles", true);
    expect(settings.signals.desktopActivity).toBe(false);
    expect(settings.signals.desktopWindowTitles).toBe(false);

    settings = await facade.setSignalEnabled("screenSnapshots", true);
    expect(settings.signals.screenSnapshots).toBe(false);

    settings = await facade.setSignalEnabled("desktopActivity", true);
    expect(settings.signals.desktopActivity).toBe(true);
    settings = await facade.setSignalEnabled("desktopWindowTitles", true);
    expect(settings.signals.desktopWindowTitles).toBe(true);
    settings = await facade.setSignalEnabled("desktopActivity", false);
    expect(settings.signals.desktopWindowTitles).toBe(false);
    settings = await facade.setSignalEnabled("desktopActivity", true);
    expect(settings.signals.desktopWindowTitles).toBe(false);
    runtime.stop();
  });

  test("flushes active focus span on permission loss", async () => {
    const clock = createMutableClock();
    const provider = createFakeProvider([
      {
        app_name: "Cursor",
        bundle_id: "com.todesktop.230313mzl4w4u92",
        process_id: 101,
        permission_status: "granted",
      },
      {
        app_name: "Cursor",
        bundle_id: "com.todesktop.230313mzl4w4u92",
        process_id: 101,
        permission_status: "denied",
      },
    ]);
    const { database, runtime, facade } = createRuntimeWithActivity(provider, clock);
    await facade.setSignalEnabled("desktopActivity", true);
    const session = await facade.startSession({ title: "Permission loss" });

    clock.set(1_000);
    await runtime.desktopActivity.tick();
    clock.set(2_000);
    await runtime.desktopActivity.tick();

    const desktopEvents = database.listEvents(session.session_id).filter((event) => event.source === "desktop-activity");
    expect(desktopEvents).toHaveLength(1);
    expect(desktopEvents[0]?.payload).toMatchObject({
      app_name: "Cursor",
      focus_started_monotonic_ms: 1_000,
      focus_ended_monotonic_ms: 2_000,
    });
    expect((await facade.currentSettings()).desktop_activity?.permission_status).toBe("denied");
    runtime.stop();
  });

  test("records provider failures in status without throwing from tick", async () => {
    const clock = createMutableClock(1_000);
    const provider: DesktopActivityProvider = {
      permissionStatus: () => "granted",
      foregroundActivity: () => {
        throw new Error("osascript timed out");
      },
    };
    const { database, runtime, facade } = createRuntimeWithActivity(provider, clock);
    await facade.setSignalEnabled("desktopActivity", true);
    const session = await facade.startSession({ title: "Provider failure" });

    await expect(runtime.desktopActivity.tick()).resolves.toBeNull();

    expect((await facade.currentSettings()).desktop_activity?.last_error).toBe("osascript timed out");
    expect(database.listEvents(session.session_id).filter((event) => event.source === "desktop-activity")).toHaveLength(0);
    runtime.stop();
  });

  test("reports denied permission without app metadata", async () => {
    const clock = createMutableClock(1_000);
    const provider = createFakeProvider([], "denied");
    const { database, runtime, facade } = createRuntimeWithActivity(provider, clock);
    await facade.setSignalEnabled("desktopActivity", true);
    const session = await facade.startSession({ title: "Denied desktop activity" });

    await runtime.desktopActivity.tick();
    const settings = await facade.currentSettings();

    expect(settings.desktop_activity?.permission_status).toBe("denied");
    expect(database.listEvents(session.session_id).filter((event) => event.source === "desktop-activity")).toHaveLength(0);
    runtime.stop();
  });

  test("captures bounded window titles only when the title toggle is enabled", async () => {
    const longTitle = `${"x".repeat(140)}.md`;
    const clock = createMutableClock();
    const provider = createFakeProvider([
      {
        app_name: "Cursor",
        bundle_id: "com.todesktop.230313mzl4w4u92",
        process_id: 101,
        window_id: "cursor-window-1",
        window_title: longTitle,
        permission_status: "granted",
      },
      {
        app_name: "Terminal",
        bundle_id: "com.apple.Terminal",
        process_id: 202,
        window_id: "terminal-window-1",
        window_title: "zsh",
        permission_status: "granted",
      },
    ]);
    const { database, runtime, facade } = createRuntimeWithActivity(provider, clock);
    await facade.setSignalEnabled("desktopActivity", true);
    await facade.setSignalEnabled("desktopWindowTitles", true);
    const session = await facade.startSession({ title: "Window title desktop activity" });

    clock.set(1_000);
    await runtime.desktopActivity.tick();
    clock.set(2_000);
    await runtime.desktopActivity.tick();

    const desktopEvents = database.listEvents(session.session_id).filter((event) => event.source === "desktop-activity");
    expect(provider.lastIncludeWindowTitle).toBe(true);
    expect(desktopEvents).toHaveLength(1);
    expect(desktopEvents[0]).toMatchObject({
      event_type: "desktop.window_focus",
      privacy_class: "document-opt-in",
      retention_policy: "session-delete",
    });
    expect(desktopEvents[0]?.payload).toMatchObject({
      app_name: "Cursor",
      window_title: "x".repeat(120),
      title_truncated: true,
    });
    runtime.stop();
  });
});
