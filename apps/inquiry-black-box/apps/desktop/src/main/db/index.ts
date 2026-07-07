import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  canExportPrivacyClass,
  createEvent,
  createSessionRecord,
  validateEvent,
  type EventEnvelope,
  type JsonObject,
  type SessionRecord,
  type SignalSettings,
} from "@inquiry/schema";

const moduleDir = dirname(fileURLToPath(import.meta.url));
const migrationPath = join(moduleDir, "migrations", "001_initial.sql");
const require = createRequire(import.meta.url);

type StatementResult = {
  changes?: number;
};

type SqliteStatement = {
  run(parameters?: Record<string, unknown>): StatementResult;
  get(parameters?: Record<string, unknown>): unknown;
  all(parameters?: Record<string, unknown>): unknown[];
};

export type SqliteDatabase = {
  exec(sql: string): void;
  query(sql: string): SqliteStatement;
  transaction<T>(callback: () => T): () => T;
  close(): void;
};

export type InquiryDatabase = {
  db: SqliteDatabase;
  createSession(input: { title: string; active_task?: string; notes?: string; session_id?: string }): SessionRecord;
  getSession(sessionId: string): SessionRecord | null;
  stopSession(sessionId: string, endedAt?: string): SessionRecord;
  appendEvent(event: EventEnvelope): EventEnvelope;
  appendEventIfNew(event: EventEnvelope): { inserted: boolean; event: EventEnvelope };
  appendSystemEvent(input: {
    session_id: string;
    event_type: EventEnvelope["event_type"];
    payload?: JsonObject;
    monotonic_ms?: number;
  }): EventEnvelope;
  listEvents(sessionId: string): EventEnvelope[];
  exportSessionJsonl(sessionId: string): string;
  deleteSession(sessionId: string): void;
  enqueueSyncPayload(input: { payload: JsonObject; session_id?: string | null; state?: string }): SyncQueueRecord;
  listSyncQueue(): SyncQueueRecord[];
  setSignalEnabled(key: keyof SignalSettings, enabled: boolean): void;
  signalSettings(): SignalSettings;
  close(): void;
};

export type SyncQueueRecord = {
  sync_id: string;
  session_id: string | null;
  payload: JsonObject;
  state: string;
  attempt_count: number;
  created_at: string;
  updated_at: string;
};

export function createInquiryDatabase(path = ":memory:"): InquiryDatabase {
  const db = createSqliteDatabase(path);
  db.exec("PRAGMA foreign_keys = ON;");
  db.exec(readFileSync(migrationPath, "utf8"));

  return {
    db,
    createSession(input) {
      const record = createSessionRecord(input);
      db.query(
        `INSERT INTO sessions (
          session_id, title, active_task, notes, started_at, ended_at,
          recording_state, created_at, updated_at
        ) VALUES ($session_id, $title, $active_task, $notes, $started_at, $ended_at,
          $recording_state, $created_at, $updated_at)`,
      ).run({
        ...record,
        active_task: record.active_task ?? null,
        notes: record.notes ?? null,
        ended_at: record.ended_at ?? null,
      });
      return record;
    },
    getSession(sessionId) {
      const row = db.query("SELECT * FROM sessions WHERE session_id = $sessionId").get({ sessionId });
      return row ? rowToSession(row as Record<string, unknown>) : null;
    },
    stopSession(sessionId, endedAt = new Date().toISOString()) {
      const existing = this.getSession(sessionId);
      if (!existing) {
        throw new Error(`session not found: ${sessionId}`);
      }

      const updatedAt = new Date().toISOString();
      db.query(
        `UPDATE sessions
         SET ended_at = $endedAt, recording_state = 'stopped', updated_at = $updatedAt
         WHERE session_id = $sessionId`,
      ).run({ sessionId, endedAt, updatedAt });

      return {
        ...existing,
        ended_at: endedAt,
        recording_state: "stopped",
        updated_at: updatedAt,
      };
    },
    appendEvent(event) {
      this.appendEventIfNew(event);
      return event;
    },
    appendEventIfNew(event) {
      validateEvent(event);
      const session = this.getSession(event.session_id);
      if (!session) {
        throw new Error(`cannot append event to missing session: ${event.session_id}`);
      }

      const result = db
        .query(
          `INSERT OR IGNORE INTO events (
          event_id, session_id, source, source_version, captured_at, monotonic_ms,
          timezone, event_type, confidence, quality_flags, payload, privacy_class,
          retention_policy
        ) VALUES (
          $event_id, $session_id, $source, $source_version, $captured_at, $monotonic_ms,
          $timezone, $event_type, $confidence, $quality_flags, $payload, $privacy_class,
          $retention_policy
        )`,
        )
        .run(serializeEvent(event)) as { changes?: number };

      return { inserted: Number(result.changes ?? 0) > 0, event };
    },
    appendSystemEvent(input) {
      return this.appendEvent(
        createEvent({
          session_id: input.session_id,
          source: "desktop-system",
          source_version: "desktop@0.1.0",
          monotonic_ms: input.monotonic_ms ?? 0,
          event_type: input.event_type,
          payload: input.payload ?? {},
          privacy_class: "local-derived",
          retention_policy: "local-default",
        }),
      );
    },
    listEvents(sessionId) {
      const rows = db
        .query("SELECT * FROM events WHERE session_id = $sessionId ORDER BY monotonic_ms, captured_at")
        .all({ sessionId }) as Record<string, unknown>[];
      return rows.map(rowToEvent);
    },
    exportSessionJsonl(sessionId) {
      const session = this.getSession(sessionId);
      if (!session) {
        throw new Error(`session not found: ${sessionId}`);
      }

      const lines = [
        JSON.stringify({ type: "session", session }),
        ...this.listEvents(sessionId)
          .filter((event) => canExportPrivacyClass(event.privacy_class).allowed)
          .map((event) => JSON.stringify({ type: "event", event })),
      ];
      return `${lines.join("\n")}\n`;
    },
    deleteSession(sessionId) {
      db.query("DELETE FROM sessions WHERE session_id = $sessionId").run({ sessionId });
    },
    enqueueSyncPayload(input) {
      const now = new Date().toISOString();
      const record: SyncQueueRecord = {
        sync_id: crypto.randomUUID(),
        session_id: input.session_id ?? null,
        payload: input.payload,
        state: input.state ?? "queued",
        attempt_count: 0,
        created_at: now,
        updated_at: now,
      };

      db.query(
        `INSERT INTO sync_queue (
          sync_id, session_id, payload, state, attempt_count, created_at, updated_at
        ) VALUES (
          $sync_id, $session_id, $payload, $state, $attempt_count, $created_at, $updated_at
        )`,
      ).run({
        ...record,
        payload: JSON.stringify(record.payload),
      });

      return record;
    },
    listSyncQueue() {
      const rows = db.query("SELECT * FROM sync_queue ORDER BY created_at, sync_id").all() as Record<string, unknown>[];
      return rows.map(rowToSyncQueueRecord);
    },
    setSignalEnabled(key, enabled) {
      db.query(
        `INSERT INTO signal_settings (key, enabled, updated_at)
         VALUES ($key, $enabled, $updatedAt)
         ON CONFLICT(key) DO UPDATE SET enabled = excluded.enabled, updated_at = excluded.updated_at`,
      ).run({ key, enabled: enabled ? 1 : 0, updatedAt: new Date().toISOString() });
    },
    signalSettings() {
      const defaults: SignalSettings = {
        browser: true,
        camera: false,
        typingMetrics: true,
        notifications: false,
        cloudSync: false,
      };
      const rows = db.query("SELECT key, enabled FROM signal_settings").all() as { key: keyof SignalSettings; enabled: 0 | 1 }[];
      for (const row of rows) {
        defaults[row.key] = row.enabled === 1;
      }
      return defaults;
    },
    close() {
      db.close();
    },
  };
}

function createSqliteDatabase(path: string): SqliteDatabase {
  if (isBunRuntime()) {
    const moduleName = "bun:sqlite";
    const { Database } = require(moduleName) as {
      Database: new (databasePath: string, options: { create: boolean; strict: boolean }) => SqliteDatabase;
    };
    return new Database(path, { create: true, strict: true });
  }

  const moduleName = "node:sqlite";
  const { DatabaseSync } = require(moduleName) as {
    DatabaseSync: new (databasePath: string) => {
      exec(sql: string): void;
      prepare(sql: string): SqliteStatement;
      close(): void;
    };
  };
  const database = new DatabaseSync(path);

  return {
    exec(sql) {
      database.exec(sql);
    },
    query(sql) {
      return database.prepare(sql);
    },
    transaction(callback) {
      return () => {
        database.exec("BEGIN IMMEDIATE");
        try {
          const result = callback();
          database.exec("COMMIT");
          return result;
        } catch (error) {
          database.exec("ROLLBACK");
          throw error;
        }
      };
    },
    close() {
      database.close();
    },
  };
}

function isBunRuntime(): boolean {
  return typeof (globalThis as { Bun?: unknown }).Bun === "object";
}

function serializeEvent(event: EventEnvelope): Record<string, string | number> {
  return {
    event_id: event.event_id,
    session_id: event.session_id,
    source: event.source,
    source_version: event.source_version,
    captured_at: event.captured_at,
    monotonic_ms: event.monotonic_ms,
    timezone: event.timezone,
    event_type: event.event_type,
    confidence: event.confidence,
    quality_flags: JSON.stringify(event.quality_flags),
    payload: JSON.stringify(event.payload),
    privacy_class: event.privacy_class,
    retention_policy: event.retention_policy,
  };
}

function rowToEvent(row: Record<string, unknown>): EventEnvelope {
  const event = {
    event_id: String(row.event_id),
    session_id: String(row.session_id),
    source: row.source,
    source_version: String(row.source_version),
    captured_at: String(row.captured_at),
    monotonic_ms: Number(row.monotonic_ms),
    timezone: String(row.timezone),
    event_type: row.event_type,
    confidence: Number(row.confidence),
    quality_flags: JSON.parse(String(row.quality_flags)) as string[],
    payload: JSON.parse(String(row.payload)) as JsonObject,
    privacy_class: row.privacy_class,
    retention_policy: row.retention_policy,
  };
  validateEvent(event);
  return event;
}

function rowToSyncQueueRecord(row: Record<string, unknown>): SyncQueueRecord {
  return {
    sync_id: String(row.sync_id),
    session_id: row.session_id === null ? null : String(row.session_id),
    payload: JSON.parse(String(row.payload)) as JsonObject,
    state: String(row.state),
    attempt_count: Number(row.attempt_count),
    created_at: String(row.created_at),
    updated_at: String(row.updated_at),
  };
}

function rowToSession(row: Record<string, unknown>): SessionRecord {
  const record: SessionRecord = {
    session_id: String(row.session_id),
    title: String(row.title),
    started_at: String(row.started_at),
    recording_state: row.recording_state as SessionRecord["recording_state"],
    created_at: String(row.created_at),
    updated_at: String(row.updated_at),
  };

  if (row.active_task !== null) {
    record.active_task = String(row.active_task);
  }

  if (row.notes !== null) {
    record.notes = String(row.notes);
  }

  if (row.ended_at !== null) {
    record.ended_at = String(row.ended_at);
  }

  return record;
}
