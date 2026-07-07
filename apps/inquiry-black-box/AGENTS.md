# Inquiry Black Box Agent Guide

This folder is a self-contained greenfield app inside a Python-heavy research
repo. Treat `apps/inquiry-black-box` as the project root for JavaScript,
desktop, extension, cloud, and Modal work.

## Fast Orientation

- Product: local-first Neurophenom research cockpit for browser traces, camera
  feature windows, typing rhythm aggregates, labels, probes, replay, and
  privacy-safe optional cloud analysis.
- Plan: `../../docs/plans/2026-07-07-001-feat-inquiry-black-box-plan.md`.
- Default privacy stance: no raw camera frames, no raw typed content, no hidden
  recording, no cloud upload unless the user explicitly opts in.
- Core schema: `packages/schema/src`.
- Local desktop and SQLite boundary: `apps/desktop/src/main`.
- Chrome MV3 telemetry boundary: `apps/extension/src`.
- Optional Railway API: `apps/cloud/src`.
- Modal jobs: `modal`.

## Commands

Run from this folder unless noted:

```bash
bun install
bun run lint
bun run typecheck
bun run test
bun run test:e2e
```

Modal checks:

```bash
cd modal
python3 -m pytest
```

When Modal credentials are needed, use Doppler instead of local env files:

```bash
doppler run -- python3 -m pytest
doppler run -- modal run inquiry_jobs.py::smoke_job
```

Cloud local dev:

```bash
doppler run -- bun --cwd apps/cloud run dev
```

Desktop and extension dev:

```bash
bun run dev:desktop
bun run dev:extension
```

## Architecture Map

- `packages/schema`: canonical event envelope, privacy classes, retention
  policies, session records, and validation helpers. Add new event types here
  before using them elsewhere.
- `packages/signals`: windowing and heuristic markers for replay,
  notifications, and report generation.
- `packages/ui`: dependency-light shared view models. Keep browser/Electron
  APIs out of this package.
- `apps/desktop`: local source of truth. Electron main owns SQLite, ingest,
  notifications, exports, deletion, and sync queueing. Renderer owns camera
  permission, visible recording controls, labels, probes, replay, and settings.
- `apps/extension`: content scripts observe allowed pages, background/service
  worker batches events, popup exposes recording state and site/privacy toggles.
- `apps/cloud`: optional Railway Bun API for redacted sync, reports, device
  metadata, and Modal orchestration.
- `modal`: Python jobs for redacted feature extraction, content scoring,
  embeddings, summaries, calibration, model cards, and smoke reports.

## Privacy Invariants

- Store camera-derived features and quality flags only by default.
- Store typing timing/edit metrics only; never store raw text or raw keys.
- Every event must declare `privacy_class` and `retention_policy` at creation.
- Only `public` and `redacted-sync` payloads may be sent to cloud sync.
- Default local export omits `debug-sensitive` and `blocked-sensitive` events.
- Debug/document snapshots require explicit opt-in and must be easy to delete.
- Notifications are opt-in, inspectable, rate-limited, quiet-hours aware, and
  tracked as outcomes.

## Environment Variables

Do not commit `.env` files or real secrets. Use Doppler locally and provider
managed variables in Railway/Modal.

Common variables:

- `INQUIRY_LOCAL_API_PORT`: localhost desktop ingest API.
- `INQUIRY_PAIRING_SECRET`: desktop-extension pairing secret.
- `DATABASE_URL`: Railway Postgres connection string for the cloud API.
- `RAILWAY_PUBLIC_API_URL`: deployed cloud API base URL.
- `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`: Modal credentials.
- `MODAL_ENVIRONMENT`: Modal environment name.
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`: optional model providers.
- `MODEL_PROVIDER`, `EMBEDDING_MODEL`, `SESSION_SUMMARY_MODEL`: model routing.
- `SYNC_ENCRYPTION_KEY`: encryption key for redacted sync payloads.

Local secret pattern:

```bash
doppler setup
doppler run -- bun --cwd apps/cloud run dev
doppler run -- python3 -m pytest modal/tests
```

## Railway

Railway is the optional always-on control plane, not a requirement for local
replay. Deploy only the `apps/cloud` Bun service. Required deployment files and
docs live under `apps/cloud/railway.json` and `docs/deployment.md`.

Expected flow:

```bash
railway link
railway variables set DATABASE_URL=...
railway up --service inquiry-black-box-api
```

Use Railway variables or Doppler integrations for secrets. The API must reject
raw-sensitive privacy classes even when authenticated.

## Modal

Modal is for heavier batch work only: redacted feature extraction, embeddings,
session summaries, and calibration. Jobs should consume redacted session exports
or explicitly selected content snapshots and return reports/model artifacts with
provenance. Each model run should record inputs, model version, outputs, and
limitations.

Keep local replay useful when Modal is unavailable. If a cloud or Modal action
is attempted while sync is disabled, explain the opt-in requirement and leave
local data untouched.

## Working Rules

- Keep all app-local commands and dependencies inside `apps/inquiry-black-box`.
- Do not turn the repository root into a JavaScript monorepo.
- Prefer fixture-based tests over real camera/Chrome automation in CI.
- If you touch behavior, add or update focused tests before relying on manual
  smoke checks.
- Run `bun run lint`, `bun run typecheck`, `bun run test`, and relevant targeted
  checks before committing.
