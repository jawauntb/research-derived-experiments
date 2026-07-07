PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  active_task TEXT,
  notes TEXT,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  recording_state TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  source TEXT NOT NULL,
  source_version TEXT NOT NULL,
  captured_at TEXT NOT NULL,
  monotonic_ms REAL NOT NULL,
  timezone TEXT NOT NULL,
  event_type TEXT NOT NULL,
  confidence REAL NOT NULL,
  quality_flags TEXT NOT NULL,
  payload TEXT NOT NULL,
  privacy_class TEXT NOT NULL,
  retention_policy TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_session_time
ON events(session_id, monotonic_ms, captured_at);

CREATE TABLE IF NOT EXISTS features (
  feature_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  source TEXT NOT NULL,
  window_start_ms REAL NOT NULL,
  window_end_ms REAL NOT NULL,
  payload TEXT NOT NULL,
  privacy_class TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS labels (
  label_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  event_id TEXT REFERENCES events(event_id) ON DELETE SET NULL,
  label TEXT NOT NULL,
  confidence REAL NOT NULL,
  note TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS content_refs (
  content_ref_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  url_hash TEXT NOT NULL,
  domain TEXT NOT NULL,
  title_hash TEXT,
  media_timestamp_ms REAL,
  selected_text_snapshot TEXT,
  privacy_class TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS probes (
  probe_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  source_event_id TEXT REFERENCES events(event_id) ON DELETE SET NULL,
  question TEXT NOT NULL,
  answer_score REAL,
  repair_event_id TEXT REFERENCES events(event_id) ON DELETE SET NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
  report_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  report_type TEXT NOT NULL,
  payload TEXT NOT NULL,
  source_event_ids TEXT NOT NULL,
  model_run_id TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
  notification_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  candidate_event_id TEXT REFERENCES events(event_id) ON DELETE SET NULL,
  delivery_state TEXT NOT NULL,
  user_response TEXT,
  suppression_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_queue (
  sync_id TEXT PRIMARY KEY,
  session_id TEXT REFERENCES sessions(session_id) ON DELETE CASCADE,
  payload TEXT NOT NULL,
  state TEXT NOT NULL,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS model_runs (
  model_run_id TEXT PRIMARY KEY,
  session_id TEXT REFERENCES sessions(session_id) ON DELETE SET NULL,
  provider TEXT NOT NULL,
  model_name TEXT NOT NULL,
  model_version TEXT NOT NULL,
  input_event_ids TEXT NOT NULL,
  output_payload TEXT NOT NULL,
  limitations TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signal_settings (
  key TEXT PRIMARY KEY,
  enabled INTEGER NOT NULL,
  updated_at TEXT NOT NULL
);
