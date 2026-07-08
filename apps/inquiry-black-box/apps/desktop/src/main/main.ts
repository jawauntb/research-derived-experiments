import { mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { createEvent, type EventEnvelope, type LabelPayload, type SessionRecord } from "@inquiry/schema";
import {
  createDesktopActivityCollector,
  type DesktopActivityClock,
  type DesktopActivityCollector,
  type DesktopActivityProvider,
  type DesktopActivityStatus,
} from "./activity/desktopActivity";
import { createMacosActivityProvider } from "./activity/macosActivityProvider";
import { createInquiryDatabase, type InquiryDatabase } from "./db";
import {
  createIngestRequestHandler,
  startIngestServer,
  type StartedIngestServer,
  type StartIngestServerOptions,
} from "./ingest/server";
import {
  createSessionController,
  type SessionController,
  type SessionStateChangeInput,
  type StartSessionInput,
} from "./ingest/session";
import { createGlobalHotkeyEvent } from "./security/hotkeys";
import { createPairingSecret, createPairingToken } from "./security/pairing";
import type { DesktopNotifier } from "./notifications/desktopNotifier";
import type { CameraFeatureWindow } from "../renderer/camera/featureWorker";

export type DesktopRuntimeOptions = {
  database?: InquiryDatabase;
  databasePath?: string;
  pairingSecret?: string;
  allowedOrigins?: readonly string[];
  ingestPort?: number;
  startServer?: boolean;
  desktopActivityProvider?: DesktopActivityProvider;
  desktopActivityClock?: Partial<DesktopActivityClock>;
  desktopActivityPollIntervalMs?: number;
  desktopActivityAutoPoll?: boolean;
  notifier?: DesktopNotifier;
};

export type DesktopRuntime = {
  database: InquiryDatabase;
  sessions: SessionController;
  ingest: StartedIngestServer | null;
  pairingToken: () => string;
  bridge: DesktopMainBridge;
  desktopActivity: DesktopActivityCollector;
  notifier: DesktopNotifier;
  stop: () => void;
};

export type DesktopMainBridge = {
  currentSession: () => SessionRecord | null;
  startSession: (input: StartSessionInput) => SessionRecord;
  pauseSession: (input?: SessionStateChangeInput) => SessionRecord;
  resumeSession: (input?: SessionStateChangeInput) => SessionRecord;
  stopSession: (input?: SessionStateChangeInput) => SessionRecord;
  addLabel: (input: { label: LabelPayload["label"]; note?: string; monotonic_ms?: number }) => EventEnvelope<LabelPayload>;
  appendCameraFeatureWindow: (featureWindow: CameraFeatureWindow) => EventEnvelope;
  desktopActivityStatus: () => DesktopActivityStatus;
  syncDesktopActivity: () => void;
  handleGlobalHotkey: (input: {
    action: string;
    monotonic_ms: number;
    label?: LabelPayload["label"];
    note?: string;
  }) => EventEnvelope | SessionRecord;
};

const defaultAllowedOrigins = ["chrome-extension://*"] as const;

export function createDesktopRuntime(options: DesktopRuntimeOptions = {}): DesktopRuntime {
  const database = options.database ?? createInquiryDatabase(options.databasePath ?? defaultDesktopDatabasePath());
  const sessions = createSessionController(database);
  const pairingSecret = options.pairingSecret ?? process.env.INQUIRY_PAIRING_SECRET ?? createPairingSecret();
  const allowedOrigins = options.allowedOrigins ?? defaultAllowedOrigins;
  const desktopActivityOptions: Parameters<typeof createDesktopActivityCollector>[0] = {
    provider: options.desktopActivityProvider ?? createMacosActivityProvider(),
    appendEvent: (event) => database.appendEvent(event),
    canCapture: (session_id) => {
      const session = sessions.currentSession();
      return session?.session_id === session_id && session.recording_state === "recording";
    },
  };
  if (options.desktopActivityClock !== undefined) {
    desktopActivityOptions.clock = options.desktopActivityClock;
  }
  if (options.desktopActivityPollIntervalMs !== undefined) {
    desktopActivityOptions.pollIntervalMs = options.desktopActivityPollIntervalMs;
  }
  if (options.desktopActivityAutoPoll !== undefined) {
    desktopActivityOptions.autoPoll = options.desktopActivityAutoPoll;
  }
  const desktopActivity = createDesktopActivityCollector({
    ...desktopActivityOptions,
  });
  const notifier = options.notifier ?? noopNotifier;
  const bridge = createDesktopMainBridge(database, sessions, desktopActivity);
  const serverOptions: StartIngestServerOptions = {
    allowedOrigins,
    database,
    pairingSecret,
    sessions,
    sessionControls: bridge,
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
    desktopActivity,
    notifier,
    stop() {
      desktopActivity.stop();
      ingest?.stop();
      database.close();
    },
  };
}

const noopNotifier: DesktopNotifier = {
  async show() {
    return "failed";
  },
};

export function createDesktopMainBridge(
  database: InquiryDatabase,
  sessions: SessionController,
  desktopActivity: DesktopActivityCollector,
): DesktopMainBridge {
  function configureDesktopActivity(): void {
    const settings = database.signalSettings();
    desktopActivity.configure({
      enabled: settings.desktopActivity,
      includeWindowTitles: settings.desktopWindowTitles,
    });

    const session = sessions.currentSession();
    if (session?.recording_state === "recording" && settings.desktopActivity) {
      desktopActivity.start({ session_id: session.session_id });
    } else {
      desktopActivity.stop();
    }
  }

  return {
    currentSession: () => sessions.currentSession(),
    startSession(input) {
      const session = sessions.startSession(input);
      configureDesktopActivity();
      return session;
    },
    pauseSession(input) {
      desktopActivity.stop();
      return sessions.pauseSession(input ?? { reason: "visible-control" });
    },
    resumeSession(input) {
      const session = sessions.resumeSession(input ?? { reason: "visible-control" });
      configureDesktopActivity();
      return session;
    },
    stopSession(input) {
      desktopActivity.stop();
      return sessions.stopSession(input ?? { reason: "visible-control" });
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
    desktopActivityStatus() {
      return desktopActivity.status();
    },
    syncDesktopActivity() {
      configureDesktopActivity();
    },
    handleGlobalHotkey(input) {
      const session = requireCurrentSession(sessions);
      if (input.action === "pause") {
        desktopActivity.stop();
        return sessions.pauseSession({ reason: "global-hotkey", monotonic_ms: input.monotonic_ms });
      }
      if (input.action === "resume") {
        const resumed = sessions.resumeSession({ reason: "global-hotkey", monotonic_ms: input.monotonic_ms });
        configureDesktopActivity();
        return resumed;
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

function defaultDesktopDatabasePath(): string {
  const configured = process.env.INQUIRY_DESKTOP_DB_PATH;
  const databasePath = configured && configured.length > 0
    ? configured
    : join(homedir(), ".inquiry-black-box", "inquiry.sqlite");
  mkdirSync(dirname(databasePath), { recursive: true });
  return databasePath;
}
