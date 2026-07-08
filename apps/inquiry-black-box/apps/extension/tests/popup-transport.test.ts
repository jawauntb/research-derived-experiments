import { describe, expect, test } from "bun:test";
import { recordingIndicator, sessionTransportButtons } from "@inquiry/ui";

describe("popup transport view model", () => {
  test("disables record while recording and enables pause and stop", () => {
    const buttons = sessionTransportButtons("recording");
    expect(buttons.find((button) => button.command === "record")).toMatchObject({ enabled: false, active: true });
    expect(buttons.find((button) => button.command === "pause")).toMatchObject({ enabled: true });
    expect(buttons.find((button) => button.command === "stop")).toMatchObject({ enabled: true });
  });

  test("enables resume and stop while paused", () => {
    const buttons = sessionTransportButtons("paused");
    expect(buttons.find((button) => button.command === "resume")).toMatchObject({ enabled: true });
    expect(buttons.find((button) => button.command === "stop")).toMatchObject({ enabled: true });
    expect(buttons.find((button) => button.command === "record")).toMatchObject({ enabled: false });
  });

  test("enables record only while stopped", () => {
    const buttons = sessionTransportButtons("stopped");
    expect(buttons.find((button) => button.command === "record")).toMatchObject({ enabled: true, active: false });
    expect(buttons.find((button) => button.command === "pause")).toMatchObject({ enabled: false });
    expect(buttons.find((button) => button.command === "stop")).toMatchObject({ enabled: false });
  });

  test("maps indicator labels for popup status header", () => {
    expect(recordingIndicator("recording").label).toBe("Recording");
    expect(recordingIndicator("paused").label).toBe("Paused");
  });
});
