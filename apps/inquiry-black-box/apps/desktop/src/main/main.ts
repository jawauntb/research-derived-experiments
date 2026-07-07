import { createEvent, type EventEnvelope, type LabelPayload, type SessionRecord } from "@inquiry/schema";
import { createInquiryDatabase, type InquiryDatabase } from "./db";
import {
  createIngestRequestHandler,
  startIngestServer,
  type StartedIngestServer,
  type StartIngestServerOptions,
} from "./ingest/server";
import { createSessionController, type SessionController } from "./ingest/session";
import { createGlobalHotkeyEvent } from "./security/hotkeys";
import { createPairingSecret, createPairingToken } from "./security/pairing";
import type { CameraFeatureWindow } from "../renderer/camera/featureWorker";

export type DesktopRuntimeOptions = {
  database?: InquiryDatabase;
  databasePath?: string;
  pairingSecret?: string;
  allowedOrigins?: readonly string[];
  ingestPort?: number;
  startServer?: boolean;
};

export type DesktopRuntime = {
  database: InquiryDatabase;
  sessions: SessionController;
  ingest: StartedIngestServer | null;
  pairingToken: () => string;
  bridge: DesktopMainBridge;
  stop: () => void;
};

export type DesktopMainBridge = {
  currentSession: () => SessionRecord | null;
  startSession: (input: { title: string; active_task?: string; notes?: string }) => SessionRecord;
  pauseSession: () => SessionRecord;
  resumeSession: () => SessionRecord;
  stopSession: () => SessionRecord;
  addLabel: (input: { label: LabelPayload["label"]; note?: string; monotonic_ms?: number }) => EventEnvelope<LabelPayload>;
  appendCameraFeatureWindow: (featureWindow: CameraFeatureWindow) => EventEnvelope;
  handleGlobalHotkey: (input: {
    action: string;
    monotonic_ms: number;
    label?: LabelPayload["label"];
    note?: string;
  }) => EventEnvelope | SessionRecord;
};

const defaultAllowedOrigins = ["chrome-extension://*"] as const;

export function createDesktopRuntime(options: DesktopRuntimeOptions = {}): DesktopRuntime {
  const database = options.database ?? createInquiryDatabase(options.databasePath);
  const sessions = createSessionController(database);
  const pairingSecret = options.pairingSecret ?? process.env.INQUIRY_PAIRING_SECRET ?? createPairingSecret();
  const allowedOrigins = options.allowedOrigins ?? defaultAllowedOrigins;
  const bridge = createDesktopMainBridge(database, sessions);
  const serverOptions: StartIngestServerOptions = {
    allowedOrigins,
    database,
    pairingSecret,
    sessions,
  };
  if (options.ingestPort !== undefined) {
    serverOptions.port = options.ingestPort;
  }
  const ingest = options.startServer === false ? null : startIngestServer(serverOptions);

  return {
    database,
    sessions,
    ingest,
    pairingToken: () => createPairingToken({ secret: pairingSecret }),
    bridge,
    stop() {
      ingest?.stop();
      database.close();
    },
  };
}

export function createDesktopMainBridge(database: InquiryDatabase, sessions: SessionController): DesktopMainBridge {
  return {
    currentSession: () => sessions.currentSession(),
    startSession(input) {
      return sessions.startSession(input);
    },
    pauseSession() {
      return sessions.pauseSession({ reason: "visible-control" });
    },
    resumeSession() {
      return sessions.resumeSession({ reason: "visible-control" });
    },
    stopSession() {
      return sessions.stopSession({ reason: "visible-control" });
    },
    addLabel(input) {
      const session = requireCurrentSession(sessions);
      const payload: LabelPayload = { label: input.label };
      if (input.note !== undefined) {
        payload.note = input.note;
      }

      const event = createEvent({
        session_id: session.session_id,
        source: "user",
        source_version: "desktop@0.1.0",
        monotonic_ms: input.monotonic_ms ?? Date.now(),
        event_type: "label.added",
        payload,
        privacy_class: "local-derived",
        retention_policy: "local-default",
      });
      database.appendEvent(event);
      return event;
    },
    appendCameraFeatureWindow(featureWindow) {
      const session = requireCurrentSession(sessions);
      if (session.recording_state !== "recording") {
        throw new Error(`cannot append camera features while session is ${session.recording_state}`);
      }

      return database.appendEvent(
        createEvent({
          session_id: session.session_id,
          source: "desktop-camera",
          source_version: "desktop@0.1.0",
          monotonic_ms: featureWindow.window_end_ms,
          event_type: "camera.feature_window",
          confidence: featureWindow.confidence,
          quality_flags: featureWindow.quality_flags,
          payload: featureWindow.payload,
          privacy_class: "local-derived",
          retention_policy: "local-default",
        }),
      );
    },
    handleGlobalHotkey(input) {
      const session = requireCurrentSession(sessions);
      if (input.action === "pause") {
        return sessions.pauseSession({ reason: "global-hotkey", monotonic_ms: input.monotonic_ms });
      }
      if (input.action === "resume") {
        return sessions.resumeSession({ reason: "global-hotkey", monotonic_ms: input.monotonic_ms });
      }

      const event = createGlobalHotkeyEvent({ ...input, session_id: session.session_id });
      return database.appendEvent(event);
    },
  };
}

export function createDesktopIngestHandler(options: DesktopRuntimeOptions = {}): (request: Request) => Promise<Response> {
  const database = options.database ?? createInquiryDatabase(options.databasePath);
  const sessions = createSessionController(database);
  const pairingSecret = options.pairingSecret ?? process.env.INQUIRY_PAIRING_SECRET ?? createPairingSecret();

  return createIngestRequestHandler({
    allowedOrigins: options.allowedOrigins ?? defaultAllowedOrigins,
    database,
    pairingSecret,
    sessions,
  });
}

function requireCurrentSession(sessions: SessionController): SessionRecord {
  const session = sessions.currentSession();
  if (!session) {
    throw new Error("no active session");
  }
  return session;
}

if (import.meta.main) {
  const runtime = createDesktopRuntime();
  const ingestUrl = runtime.ingest?.url ?? "disabled";
  console.log(`Inquiry Black Box desktop runtime listening at ${ingestUrl}`);
  process.once("SIGINT", () => {
    runtime.stop();
    process.exit(0);
  });
}
