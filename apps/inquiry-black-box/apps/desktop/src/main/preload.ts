import { contextBridge, ipcRenderer } from "electron";
import type { LabelPayload, SignalSettings } from "@inquiry/schema";
import type { RepairCandidate } from "@inquiry/signals";
import type { CameraFeatureWindow } from "../renderer/camera/featureWorker";

type CameraPermissionState = "prompt" | "granted" | "denied" | "unavailable";

async function invoke<T>(channel: string, ...args: unknown[]): Promise<T> {
  return (await ipcRenderer.invoke(channel, ...args)) as T;
}

const desktopBridge = {
  status: {
    current: () => invoke("inquiry:status"),
  },
  session: {
    currentSession: () => invoke("inquiry:session:current"),
    startSession: (input: { title: string; active_task?: string; notes?: string }) =>
      invoke("inquiry:session:start", input),
    pauseSession: () => invoke("inquiry:session:pause"),
    resumeSession: () => invoke("inquiry:session:resume"),
    stopSession: () => invoke("inquiry:session:stop"),
    addLabel: (label: LabelPayload["label"], note?: string) =>
      invoke("inquiry:session:label", { label, ...(note ? { note } : {}) }),
  },
  camera: {
    async requestCamera(): Promise<CameraPermissionState> {
      if (!navigator.mediaDevices?.getUserMedia) {
        return "unavailable";
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        for (const track of stream.getTracks()) {
          track.stop();
        }
        return "granted";
      } catch {
        return "denied";
      }
    },
    async disableCamera(): Promise<void> {
      return undefined;
    },
    appendFeatureWindow: (featureWindow: CameraFeatureWindow) =>
      invoke("inquiry:camera:append-feature-window", featureWindow),
  },
  privacy: {
    currentSettings: () => invoke("inquiry:privacy:settings"),
    setSignalEnabled: (key: keyof SignalSettings, enabled: boolean) =>
      invoke("inquiry:privacy:set-signal-enabled", key, enabled),
    exportSession: () => invoke("inquiry:privacy:export"),
    deleteSession: () => invoke("inquiry:privacy:delete"),
  },
  replay: {
    report: () => invoke("inquiry:replay:report"),
  },
  repair: {
    accept: (repair_id: RepairCandidate["repair_id"]) => invoke("inquiry:repair:accept", repair_id),
    answer: (input: { repair_id: RepairCandidate["repair_id"]; answer: string; confidence: number }) =>
      invoke("inquiry:repair:answer", input),
    dismiss: (input: { repair_id: RepairCandidate["repair_id"]; reason?: string }) =>
      invoke("inquiry:repair:dismiss", input),
  },
};

contextBridge.exposeInMainWorld("inquiryDesktop", desktopBridge);
