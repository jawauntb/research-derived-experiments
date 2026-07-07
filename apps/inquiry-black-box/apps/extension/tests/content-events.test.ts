import { describe, expect, test } from "bun:test";
import {
  createContentTelemetry,
  type ContentEventMessage,
  type EditableElementLike,
  type MediaElementLike,
} from "../src/content";

describe("content telemetry capture", () => {
  test("captures scroll and media events from fixture inputs", () => {
    const messages: ContentEventMessage[] = [];
    let now = 100;
    const telemetry = createContentTelemetry({
      now: () => now,
      sessionId: "session-fixture",
      settings: recordingSettings(),
      location: {
        href: "https://research.example.test/paper?private=query",
        hostname: "research.example.test",
      },
      sendMessage: (message) => {
        messages.push(message);
      },
    });

    telemetry.captureScroll({
      scrollX: 4,
      scrollY: 320,
      viewportHeight: 900,
      documentHeight: 2_400,
    });
    now += 30;
    const media = fixtureMedia({ currentTime: 12.5, duration: 240 });
    telemetry.captureMedia("play", media);
    now += 40;
    media.currentTime = 42;
    telemetry.captureMedia("seeked", media);

    const events = messages.flatMap((message) => message.events);
    expect(events.map((event) => event.event_type)).toEqual([
      "browser.scroll",
      "browser.media",
      "browser.media",
    ]);
    expect(events[0]?.payload).toMatchObject({
      scroll_y: 320,
      delta_y: 0,
      scroll_x: 4,
      viewport_h: 900,
      document_h: 2400,
    });
    expect(events[1]?.payload).toMatchObject({
      action: "play",
      current_time_s: 12.5,
      delta_ms: 0,
      duration_s: 240,
      media_kind: "video",
    });
    expect(events[2]?.payload).toMatchObject({
      action: "seeked",
      delta_ms: 29_500,
    });
    expect(JSON.stringify(events)).not.toContain("private=query");
  });

  test("captures selection, copy, and highlight metrics without selected text", () => {
    const messages: ContentEventMessage[] = [];
    const telemetry = createContentTelemetry({
      now: () => 200,
      sessionId: "session-selection",
      settings: recordingSettings(),
      location: {
        href: "https://research.example.test/notes",
        hostname: "research.example.test",
      },
      sendMessage: (message) => {
        messages.push(message);
      },
    });

    telemetry.captureSelection("selection", { selectionLength: 17, rangeCount: 1 });
    telemetry.captureSelection("copy", { selectionLength: 17, rangeCount: 1 });
    telemetry.captureSelection("highlight", { selectionLength: 17, rangeCount: 1 });

    const events = messages.flatMap((message) => message.events);
    expect(events.map((event) => event.event_type)).toEqual([
      "browser.selection",
      "browser.copy",
      "browser.highlight",
    ]);
    expect(events.every((event) => event.payload.selection_length === 17)).toBe(true);
    expect(JSON.stringify(events)).not.toContain("selected phrase");
  });

  test("typing payloads contain timing and edit metrics but no typed content", () => {
    const messages: ContentEventMessage[] = [];
    let now = 1_000;
    const telemetry = createContentTelemetry({
      now: () => now,
      sessionId: "session-typing",
      settings: recordingSettings(),
      location: {
        href: "https://research.example.test/search",
        hostname: "research.example.test",
      },
      sendMessage: (message) => {
        messages.push(message);
      },
    });
    const input: EditableElementLike = {
      tagName: "INPUT",
      type: "search",
      value: "",
      isContentEditable: false,
    };

    telemetry.recordKeydown({ key: "s", target: input });
    input.value = "sensitive typed query";
    now += 120;
    telemetry.captureTypingInput({ target: input, inputType: "insertText" });
    now += 180;
    telemetry.recordKeydown({ key: "Backspace", target: input });
    input.value = "sensitive typed quer";
    telemetry.captureTypingInput({ target: input, inputType: "deleteContentBackward" });

    const events = messages.flatMap((message) => message.events);
    expect(events).toHaveLength(2);
    const latest = events.at(-1);
    expect(latest?.event_type).toBe("browser.typing_metrics");
    expect(latest?.payload).toMatchObject({
      field_role: "search",
      burst_length: 2,
      backspace_count: 1,
    });

    const serialized = JSON.stringify(events);
    expect(serialized).not.toContain("sensitive typed query");
    expect(serialized).not.toContain("sensitive typed quer");
    expect(serialized).not.toContain('"key"');
    expect(serialized).not.toContain('"value"');
    expect(serialized).not.toContain('"text"');
  });

  test("respects pause, site disable, and privacy toggles before sending", () => {
    const messages: ContentEventMessage[] = [];
    const telemetry = createContentTelemetry({
      now: () => 3_000,
      wallClockNow: () => 300_000,
      sessionId: "session-paused",
      settings: recordingSettings(),
      location: {
        href: "https://research.example.test/paused",
        hostname: "research.example.test",
      },
      sendMessage: (message) => {
        messages.push(message);
      },
    });

    telemetry.setSettings({ recordingState: "paused" });
    telemetry.captureScroll({ scrollY: 10, viewportHeight: 100, documentHeight: 500 });
    telemetry.setSettings({ recordingState: "recording", siteDisabled: true });
    telemetry.captureMedia("pause", fixtureMedia({ currentTime: 3, duration: 10 }));
    telemetry.setSettings({
      siteDisabled: false,
      privacyToggles: { browser: true, typingMetrics: false, selection: true, media: true },
    });
    telemetry.captureTypingInput({
      target: { tagName: "TEXTAREA", value: "private note", isContentEditable: false },
      inputType: "insertText",
    });
    telemetry.setSettings({
      privacyToggles: { browser: true, typingMetrics: true, selection: true, media: true },
    });
    telemetry.captureScroll({ scrollY: 20, viewportHeight: 100, documentHeight: 500 });

    const events = messages.flatMap((message) => message.events);
    expect(events).toHaveLength(1);
    expect(events[0]?.event_type).toBe("browser.scroll");
    expect(events[0]?.payload.scroll_y).toBe(20);
  });

  test("defaults to stopped capture and resumes after timed pauses expire", () => {
    const messages: ContentEventMessage[] = [];
    let wallClockNow = 10_000;
    const telemetry = createContentTelemetry({
      now: () => 4_000,
      wallClockNow: () => wallClockNow,
      sessionId: "session-default-safe",
      location: {
        href: "https://research.example.test/default",
        hostname: "research.example.test",
      },
      sendMessage: (message) => {
        messages.push(message);
      },
    });

    telemetry.captureScroll({ scrollY: 10, viewportHeight: 100, documentHeight: 500 });
    telemetry.setSettings({ recordingState: "paused", pausedUntilMs: 20_000, privacyToggles: recordingSettings().privacyToggles });
    telemetry.captureScroll({ scrollY: 20, viewportHeight: 100, documentHeight: 500 });
    wallClockNow = 20_001;
    telemetry.captureScroll({ scrollY: 30, viewportHeight: 100, documentHeight: 500 });

    const events = messages.flatMap((message) => message.events);
    expect(events).toHaveLength(1);
    expect(events[0]?.payload.scroll_y).toBe(30);
  });
});

function fixtureMedia(input: { currentTime: number; duration: number }): MediaElementLike {
  return {
    tagName: "VIDEO",
    currentTime: input.currentTime,
    duration: input.duration,
    paused: false,
    playbackRate: 1,
  };
}

function recordingSettings() {
  return {
    recordingState: "recording" as const,
    siteDisabled: false,
    privacyToggles: {
      browser: true,
      typingMetrics: true,
      selection: true,
      media: true,
    },
  };
}
