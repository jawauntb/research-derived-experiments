-- =============================================================================
-- Coherence / neurophenom — Corpus Index Schema (Supabase / Postgres)
-- =============================================================================
-- Version:      0.1.0  (initial draft)
-- Date:         2026-07-06
-- Owner:        jawaun@generalintelligencecompany.com
--
-- Rationale
-- ---------
-- The company moat is the CORPUS: paired EEG/fNIRS + objective-label recordings
-- with subject metadata across many trials. This schema is the *index* over
-- that corpus. Large binary signal blobs live outside Postgres (object store);
-- `recordings.file_ref` is the pointer.
--
-- Load-bearing design decisions:
--
--   1. STATE-ONTOLOGY IS VERSIONED, IMMUTABLE ONCE PUBLISHED.
--      Every label row points at a specific `states.id`, which points at a
--      specific `state_ontologies.id`. Re-labeling under a new ontology
--      produces new label rows; it does NOT mutate old ones. This is the
--      only way multi-year training corpora stay auditable.
--
--   2. CONSENT / DATA-RIGHTS IS FIRST-CLASS.
--      `consents` is versioned. `subjects.consent_version_id` is NOT NULL.
--      All FKs use ON DELETE RESTRICT so we cannot lose the paper trail on
--      what data we are and are not allowed to use, derive from, or sell.
--      Getting this wrong destroys the flywheel.
--
--   3. `labels.source` IS LOAD-BEARING.
--      Distinguishes 'measured' (ground truth) from 'model_predicted' /
--      'prior' / 'self_report'. Enforced by CHECK, not convention.
--      If measured and predicted labels ever mix silently, the corpus
--      becomes a hallucinated-fidelity liability rather than an asset.
--
--   4. LEAVE-SUBJECTS-OUT IS THE DEFAULT EVAL PROTOCOL.
--      Every recording carries subject_id transitively via session; the
--      `run_fold_results.held_out_subject_ids` array captures the exact
--      LOSO fold definition per seed.
--
--   5. BBBD INGEST SHAPE.
--      subject -> session -> recording (experiment_id 1..5) -> epochs -> labels.
--      Matches the public benchmark ingestion; makes onboarding external
--      corpora cheap.
--
--   6. SPONSOR ISOLATION IS PLUMBED EARLY.
--      `sponsors` + `sponsor_studies` join is present now so per-partner
--      views / RLS policies can be added without a rewrite.
--
-- What is deliberately NOT here yet
-- ---------------------------------
--   - Concrete RLS policies (auth model unresolved — see TODOs).
--   - Signal-level indexing (channel maps, montage, filter chain). Add when
--     needed; keep it in a separate `recording_meta` table so this file
--     stays a stable index.
--   - Payments / usage metering.
--   - Any secrets. This file must remain safe to commit.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------
create extension if not exists "pgcrypto";  -- gen_random_uuid()
create extension if not exists "citext";    -- case-insensitive text (emails)

-- ---------------------------------------------------------------------------
-- Enum-ish CHECK domains
-- ---------------------------------------------------------------------------
-- We use CHECK constraints rather than Postgres ENUMs so that adding a new
-- allowed value does not require an ALTER TYPE migration (which is painful
-- inside transactions and inside Supabase migrations).

-- ===========================================================================
-- 1. CONSENT + SUBJECTS
-- ===========================================================================

create table if not exists consents (
    id                    uuid primary key default gen_random_uuid(),
    consent_version       text not null,               -- e.g. 'v2026.03'
    jurisdiction          text not null,               -- e.g. 'US-CA', 'EU'
    allows_commercial_use boolean not null,
    allows_derived_data   boolean not null,            -- can we train on derivatives?
    field_of_use          text not null,               -- free-text scope, e.g. 'neurotech diagnostics, non-medical wellness'
    effective_at          timestamptz not null,
    document_ref          text,                        -- pointer to the signed PDF in object store
    notes                 text,
    created_at            timestamptz not null default now(),
    constraint consents_version_jurisdiction_unique
        unique (consent_version, jurisdiction)
);

comment on table  consents is 'Versioned consent + data-rights records. Every subject binds to one row here. Immutable in practice.';
comment on column consents.field_of_use is 'Scope of allowed downstream use. Free-text now; consider structured enum once patterns stabilize.';

create table if not exists subjects (
    id                        uuid primary key default gen_random_uuid(),
    external_id               text not null unique,    -- opaque handle; NEVER PII
    consent_version_id        uuid not null references consents(id) on delete restrict,
    cohort                    text,                    -- free-form tag, e.g. 'pilot-2026Q3', 'design-partner-A'
    healthy_high_performer    boolean not null default false,  -- owned-registry oversampling flag
    -- Minimal demographics. Keep this tight; anything sensitive belongs in a
    -- separate PHI-scoped table under stricter RLS.
    age_years                 smallint check (age_years is null or (age_years between 0 and 120)),
    sex_at_birth              text check (sex_at_birth is null or sex_at_birth in ('female','male','intersex','undisclosed')),
    handedness                text check (handedness   is null or handedness   in ('left','right','ambidextrous','unknown')),
    enrolled_at               timestamptz not null default now(),
    withdrawn_at              timestamptz,             -- non-null => subject has revoked; downstream must filter
    created_at                timestamptz not null default now()
);

comment on table  subjects is 'One row per human. external_id is opaque; PII (name, email, contact) MUST NOT live in this table.';
comment on column subjects.healthy_high_performer is 'From guide: owned registry deliberately oversamples healthy high-performers. Track it here so cohorts are auditable.';
comment on column subjects.withdrawn_at is 'If set, downstream queries and label serving MUST exclude this subject. Enforce in views / RLS, not just app code.';

create index if not exists subjects_consent_version_id_idx on subjects(consent_version_id);
create index if not exists subjects_cohort_idx             on subjects(cohort);

-- ===========================================================================
-- 2. STATE ONTOLOGY (VERSIONED)
-- ===========================================================================

create table if not exists state_ontologies (
    id            uuid primary key default gen_random_uuid(),
    version       text not null unique,                -- e.g. 'v1.0.0'
    yaml_hash     text not null,                       -- sha256 of the frozen YAML
    published_at  timestamptz,                         -- NULL => draft; NOT NULL => immutable
    notes         text,
    created_at    timestamptz not null default now()
);

comment on table  state_ontologies is 'Immutable-after-publish registry of state ontologies. Once published_at is set, rows here and their child states MUST NOT be edited.';
comment on column state_ontologies.yaml_hash is 'Hash of the canonical YAML/JSON serialization of the ontology; lets us prove a training run used the exact ontology we claim.';

create table if not exists states (
    id                    uuid primary key default gen_random_uuid(),
    ontology_version_id   uuid not null references state_ontologies(id) on delete restrict,
    name                  text not null,               -- e.g. 'focus', 'valence', 'workload'
    family                text not null,               -- see CHECK
    description           text,
    created_at            timestamptz not null default now(),
    constraint states_family_ck
        check (family in ('attention','affect','load','intent','arousal','other')),
    constraint states_unique_per_ontology
        unique (ontology_version_id, name)
);

comment on column states.family is 'Coarse grouping. Kept as CHECK (not enum) so families can grow without ALTER TYPE.';

create index if not exists states_ontology_idx on states(ontology_version_id);

-- ===========================================================================
-- 3. SPONSORS + STUDIES
-- ===========================================================================

create table if not exists sponsors (
    id                       uuid primary key default gen_random_uuid(),
    name                     text not null unique,
    is_design_partner        boolean not null default false,
    data_license_terms_ref   text,                     -- pointer to the signed contract
    created_at               timestamptz not null default now()
);

comment on table sponsors is 'Commercial counterparties. Present now so RLS / partner-facing views can attach later without migrations.';

create table if not exists studies (
    id                   uuid primary key default gen_random_uuid(),
    name                 text not null,
    sponsor_id           uuid references sponsors(id) on delete restrict,   -- nullable: internal studies allowed
    indication           text,                                              -- e.g. 'sustained attention', 'affective valence'
    protocol_version     text not null,
    pre_registered_at    timestamptz,                                       -- NULL => not pre-registered yet
    pre_registration_ref text,                                              -- OSF / registry URL or hash
    created_at           timestamptz not null default now(),
    constraint studies_name_protocol_unique unique (name, protocol_version)
);

comment on column studies.pre_registered_at is 'From guide: qualification-grade means pre-specified endpoints. Non-null timestamp is the audit anchor.';

create index if not exists studies_sponsor_id_idx on studies(sponsor_id);

-- Explicit join table so a study can have multiple sponsors (or be shared).
create table if not exists sponsor_studies (
    sponsor_id   uuid not null references sponsors(id) on delete restrict,
    study_id     uuid not null references studies(id)  on delete restrict,
    role         text,                                 -- e.g. 'funder', 'co-sponsor', 'data-recipient'
    created_at   timestamptz not null default now(),
    primary key (sponsor_id, study_id)
);

-- ===========================================================================
-- 4. SESSIONS -> RECORDINGS -> EPOCHS
-- ===========================================================================

create table if not exists sessions (
    id           uuid primary key default gen_random_uuid(),
    subject_id   uuid not null references subjects(id) on delete restrict,
    study_id     uuid          references studies(id)  on delete restrict,
    started_at   timestamptz not null,
    ended_at     timestamptz,
    location     text,                                 -- lab site / clinic tag
    notes        text,
    created_at   timestamptz not null default now()
);

create index if not exists sessions_subject_id_idx on sessions(subject_id);
create index if not exists sessions_study_id_idx   on sessions(study_id);

create table if not exists recordings (
    id             uuid primary key default gen_random_uuid(),
    session_id     uuid not null references sessions(id) on delete restrict,
    experiment_id  smallint,                           -- BBBD 1..5; nullable for non-BBBD
    modality       text not null,
    sfreq_hz       double precision not null,
    n_channels     integer not null,
    duration_s     double precision,
    file_ref       text not null,                      -- object-store path / URI to the raw blob
    file_hash      text,                               -- sha256 of the blob; enables integrity checks
    license        text not null,                      -- e.g. 'CC-BY-4.0', 'proprietary', 'sponsor-A-restricted'
    created_at     timestamptz not null default now(),
    constraint recordings_modality_ck
        check (modality in ('eeg','fnirs','both')),
    constraint recordings_experiment_id_ck
        check (experiment_id is null or experiment_id between 1 and 5),
    constraint recordings_sfreq_ck
        check (sfreq_hz > 0),
    constraint recordings_n_channels_ck
        check (n_channels > 0)
);

comment on column recordings.experiment_id is 'BBBD experiment index (1..5). NULL for internally collected recordings that do not follow BBBD.';
comment on column recordings.file_ref is 'Pointer to the signal blob in object storage. Postgres never stores the blob itself.';

create index if not exists recordings_session_id_idx    on recordings(session_id);
create index if not exists recordings_experiment_id_idx on recordings(experiment_id);
create index if not exists recordings_modality_idx      on recordings(modality);

create table if not exists epochs (
    id              uuid primary key default gen_random_uuid(),
    recording_id    uuid not null references recordings(id) on delete restrict,
    start_s         double precision not null,
    stop_s          double precision not null,
    dropped_reason  text,                              -- non-null => epoch excluded from analysis; keep for provenance
    created_at      timestamptz not null default now(),
    constraint epochs_time_order_ck check (stop_s > start_s)
);

comment on column epochs.dropped_reason is 'Non-null means the epoch is excluded from training/eval. We keep the row for provenance, not delete it.';

create index if not exists epochs_recording_id_idx on epochs(recording_id);

-- ===========================================================================
-- 5. LABELS  (the load-bearing table)
-- ===========================================================================

create table if not exists labels (
    id             uuid primary key default gen_random_uuid(),
    epoch_id       uuid not null references epochs(id) on delete restrict,
    state_id       uuid not null references states(id) on delete restrict,
    value_type     text not null,                      -- see CHECK
    value_num      double precision,
    value_str      text,
    source         text not null,                      -- see CHECK; separates measured from predicted
    model_version  text,                               -- required when source in ('model_predicted','prior')
    confidence     double precision,                   -- optional; 0..1 when meaningful
    labeled_at     timestamptz not null default now(),
    created_at     timestamptz not null default now(),

    constraint labels_value_type_ck
        check (value_type in ('binary','continuous','categorical')),
    constraint labels_source_ck
        check (source in ('measured','model_predicted','prior','self_report')),
    constraint labels_confidence_range_ck
        check (confidence is null or (confidence >= 0 and confidence <= 1)),

    -- Enforce value / type coherence.
    constraint labels_value_coherence_ck check (
        (value_type = 'binary'      and value_num is not null and value_str is null)
     or (value_type = 'continuous'  and value_num is not null and value_str is null)
     or (value_type = 'categorical' and value_str is not null and value_num is null)
    ),

    -- Model-derived rows MUST declare a model version. Prevents silent
    -- contamination of the corpus with un-attributable predictions.
    constraint labels_model_version_required_ck check (
        source not in ('model_predicted','prior') or model_version is not null
    )
);

comment on table  labels is 'One row per (epoch, state). source distinguishes ground truth from model-derived; enforced by CHECK.';
comment on column labels.source is 'measured = objective ground truth; self_report = subject-reported; model_predicted = derived from a trained model; prior = derived from a hand-set prior. NEVER conflate.';
comment on column labels.model_version is 'REQUIRED when source is model_predicted or prior. Enforced by CHECK.';

create index if not exists labels_epoch_id_idx on labels(epoch_id);
create index if not exists labels_state_id_idx on labels(state_id);
create index if not exists labels_source_idx   on labels(source);

-- ===========================================================================
-- 6. RUNS + FOLD RESULTS  (experiment tracking)
-- ===========================================================================

create table if not exists runs (
    id                    uuid primary key default gen_random_uuid(),
    kind                  text not null,               -- e.g. 'phase0', 'confound_ablation', 'holdout_eval'
    config_yaml_hash      text not null,               -- sha256 of the frozen config
    kill_criterion_version text not null,              -- version of the pre-registered kill/GO rule
    verdict               text,                        -- filled in at run end; NULL while running
    notes                 text,
    started_at            timestamptz not null default now(),
    finished_at           timestamptz,
    constraint runs_verdict_ck
        check (verdict is null or verdict in ('GO','KILL','INCONCLUSIVE'))
);

comment on table  runs is 'Pre-registered analysis run. verdict is set once against a frozen kill criterion. Never rewrite verdict after finished_at.';

create index if not exists runs_kind_idx    on runs(kind);
create index if not exists runs_verdict_idx on runs(verdict);

create table if not exists run_fold_results (
    id                     uuid primary key default gen_random_uuid(),
    run_id                 uuid not null references runs(id) on delete restrict,
    seed                   integer not null,
    n_train_subjects       integer not null,
    held_out_subject_ids   text[] not null,            -- opaque external_ids (or uuids as text); the exact LOSO fold
    balanced_accuracy      double precision,
    bits_per_second        double precision,
    n_test_epochs          integer,
    created_at             timestamptz not null default now(),
    constraint run_fold_results_run_seed_unique unique (run_id, seed),
    constraint run_fold_n_train_ck check (n_train_subjects >= 0)
);

comment on column run_fold_results.held_out_subject_ids is 'Exact LOSO fold definition. Kept as text[] so the row survives subject uuid rotation.';

create index if not exists run_fold_results_run_id_idx on run_fold_results(run_id);

-- ===========================================================================
-- 7. ROW-LEVEL SECURITY (STUBS)
-- ===========================================================================
-- Enable RLS on the two tables most likely to leak: subjects (identity /
-- consent) and labels (the actual training signal). Policies are intentionally
-- left as TODOs — the auth model (Supabase auth JWT? service-role only?
-- per-sponsor JWT claims?) is not yet decided.
--
-- TODO: define policy for `subjects` — likely service-role only for now, plus
--       a per-sponsor SELECT policy once sponsor JWT claims exist.
-- TODO: define policy for `labels` — mirror `subjects` policy via the
--       epoch -> recording -> session -> subject join, OR denormalize
--       subject_id onto labels (perf vs. purity trade-off).
-- TODO: decide whether `consents`, `state_ontologies`, `states`, `studies`,
--       `sponsors` should also be RLS-gated. Default assumption: readable by
--       any authenticated corpus consumer, writable service-role only.
-- TODO: enforce `subjects.withdrawn_at is null` inside SELECT policies so
--       withdrawal is honored at the DB layer, not the app layer.

alter table subjects enable row level security;
alter table labels   enable row level security;

-- ===========================================================================
-- END
-- ===========================================================================
