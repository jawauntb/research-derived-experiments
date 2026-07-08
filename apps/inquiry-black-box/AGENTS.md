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
bun run build:prototype
bun run package:extension
bun run package:desktop
bun run validation:smoke
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
doppler run -- bun run --cwd apps/cloud dev
```

Desktop and extension dev:

```bash
bun run build:prototype
bun run dev:desktop
bun run dev:extension
```

Release checklist:

```bash
bun run package:local
bun run validation:smoke
```

Use `docs/release-checklist.md` for the full local, packaged, cloud, Modal,
database, troubleshooting, and validation gate list.

## Architecture Map

- `packages/schema`: canonical event envelope, privacy classes, retention
  policies, session records, and validation helpers. Add new event types here
  before using them elsewhere.
- `packages/signals`: windowing, heuristic markers, heatmaps, repair
  candidates, notifications, and report generation.
- `packages/ui`: dependency-light shared view models. Keep browser/Electron
  APIs out of this package.
- `apps/desktop`: local source of truth. Electron main owns SQLite, ingest,
  notifications, exports, deletion, and sync queueing. Renderer owns camera
  permission, visible recording controls, labels, probes, replay, heatmap,
  repair prompts, and settings.
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

- `NIXPACKS_NODE_VERSION`: set to `22` for Railway/Nixpacks builds.
- `INQUIRY_LOCAL_API_PORT`: localhost desktop ingest API.
- `INQUIRY_PAIRING_SECRET`: desktop-extension pairing secret.
- `INQUIRY_DESKTOP_DB_PATH`: optional desktop SQLite path; defaults to
  `~/.inquiry-black-box/inquiry.sqlite`.
- `INQUIRY_CLOUD_AUTH_SECRET`: HMAC secret for signed cloud bearer tokens.
- `INQUIRY_CLOUD_BEARER_TOKEN`: pre-issued desktop bearer token for optional
  redacted cloud summaries. Do not ship `INQUIRY_CLOUD_AUTH_SECRET` in desktop
  app environments.
- `INQUIRY_ALLOW_IN_MEMORY_CLOUD=1`: Railway/production smoke-test escape
  hatch for the local in-memory cloud store. Do not use for real data.
- `DATABASE_URL`: Railway Postgres connection string for the cloud API.
- `RAILWAY_PUBLIC_API_URL`: deployed cloud API base URL.
- `MODAL_JOB_WEBHOOK_URL` / `MODAL_WEBHOOK_URL`: Modal HTTP job entrypoint.
- `MODAL_JOB_WEBHOOK_TOKEN` / `MODAL_WEBHOOK_TOKEN`: bearer token for Modal
  webhook calls.
- `MODAL_JOB_TIMEOUT_MS`: cloud-to-Modal HTTP timeout in milliseconds.
- `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`: Modal credentials.
- `MODAL_ENVIRONMENT`: Modal environment name.
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`: optional model providers.
- `GOOGLE_API_KEY`, `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`,
  `VOYAGE_API_KEY`: additional optional model providers reused from existing
  Superoptimizers/social-cohesion envs.
- `HF_TOKEN` / `HUGGINGFACE_TOKEN`: Hugging Face access; `HF_TOKEN` is the
  canonical Doppler key and `HUGGINGFACE_TOKEN` is accepted for compatibility.
- `MODEL_PROVIDER`, `EMBEDDING_MODEL`, `SESSION_SUMMARY_MODEL`: model routing.
- `TRIBE_MODEL_ID`, `BRAIN2QWERTY_REPO`, `BRAIN2QWERTY_DATASET_ID`,
  `BRAINDECODE_MODEL_ID`, `VJEPA_MODEL_ID`, `VJEPA_LARGE_MODEL_ID`,
  `INTERNVIDEO_MODEL_ID`, `QWEN_VL_MODEL_ID`, `WHISPER_MODEL_ID`,
  `FASTER_WHISPER_MODEL_ID`: optional research model IDs. Keep Brain2Qwerty
  research-only/license-gated unless its terms permit product use.
- `SYNC_ENCRYPTION_KEY`: encryption key for redacted sync payloads.

Local secret pattern:

```bash
doppler setup
doppler run -- bun run --cwd apps/cloud dev
doppler run -- python3 -m pytest modal/tests
```

## Railway

Railway is the optional always-on control plane, not a requirement for local
replay. Deploy only the `apps/cloud` Bun service from the app root. Required
deployment files and docs live under `railway.json` and `docs/deployment.md`.

Expected flow:

```bash
railway link
bun run railway:sync-model-env -- \
  --doppler-project cofounder \
  --doppler-config prd_superoptimizers \
  --env-file /Users/jawaun/jackson_prosocial_interp_research/.env \
  --railway-project inquiry-black-box-api \
  --railway-service inquiry-black-box-api \
  --railway-environment production
railway up --service inquiry-black-box-api
```

Use Railway variables or Doppler integrations for secrets. The API must reject
raw-sensitive privacy classes even when authenticated.
This foundation intentionally refuses Railway/production startup with the local
in-memory cloud store unless `INQUIRY_ALLOW_IN_MEMORY_CLOUD=1` is set for an
ephemeral smoke test.

## Modal

Modal is for heavier batch work only: redacted feature extraction, embeddings,
session summaries, and calibration. Jobs should consume redacted session exports
or explicitly selected content snapshots and return reports/model artifacts with
provenance. Each model run should record inputs, model version, outputs, and
limitations.

Keep local replay useful when Modal is unavailable. If a cloud or Modal action
is attempted while sync is disabled, explain the opt-in requirement and leave
local data untouched.
When `MODAL_JOB_WEBHOOK_URL` is configured, the cloud API submits jobs to that
endpoint and expects `modal_call_id` plus `status` in the response. Without it,
local development uses a stub Modal client so desktop replay still works.

## Working Rules

- Keep all app-local commands and dependencies inside `apps/inquiry-black-box`.
- Do not turn the repository root into a JavaScript monorepo.
- Prefer fixture-based tests over real camera/Chrome automation in CI.
- If you touch behavior, add or update focused tests before relying on manual
  smoke checks.
- Run `bun run lint`, `bun run typecheck`, `bun run test`, and relevant targeted
  checks before committing.
- Use `docs/prototype-demo.md` as the canonical local demo runbook. The current
  local loop proves desktop + extension pairing, replay, heatmap, repair
  outcomes, export, and delete without cloud credentials.
