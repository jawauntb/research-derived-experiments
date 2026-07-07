# Inquiry Black Box Deployment

The desktop and extension remain local-first. Railway and Modal are optional
cloud surfaces for redacted sync, report lookup, and heavier batch jobs.

## Railway API

Create one Railway service rooted at `apps/inquiry-black-box` and point it at
`apps/cloud/railway.json`. The service starts the Bun API with:

```bash
bun run --cwd apps/cloud dev
```

Required variables:

- `INQUIRY_CLOUD_AUTH_SECRET`: HMAC secret used to verify cloud bearer tokens.
- `DATABASE_URL`: Railway Postgres connection string for the future durable
  store. The current foundation uses an in-memory store for local smoke tests.
- `RAILWAY_PUBLIC_API_URL`: public API base URL used by clients.
- `SYNC_ENCRYPTION_KEY`: key material for encrypted redacted sync payloads.
- `INQUIRY_ALLOW_IN_MEMORY_CLOUD=1`: only for ephemeral Railway smoke tests
  until a durable store is wired. Leave unset for real deployments.

Optional Modal orchestration variables:

- `MODAL_JOB_WEBHOOK_URL` or `MODAL_WEBHOOK_URL`: HTTP entrypoint for a deployed
  Modal job trigger.
- `MODAL_JOB_WEBHOOK_TOKEN` or `MODAL_WEBHOOK_TOKEN`: bearer token for that
  trigger.
- `MODAL_JOB_TIMEOUT_MS`: cloud-to-Modal timeout in milliseconds.
- `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, `MODAL_ENVIRONMENT`: Modal CLI and
  deployment credentials.

Use Doppler locally and Railway variables or a Doppler integration in deploys:

```bash
doppler setup
doppler run -- bun run --cwd apps/cloud dev
railway link
railway variables set INQUIRY_CLOUD_AUTH_SECRET=...
railway variables set DATABASE_URL=...
railway variables set SYNC_ENCRYPTION_KEY=...
railway variables set MODAL_JOB_WEBHOOK_URL=...
railway up --service inquiry-black-box-api
```

Smoke checks:

```bash
curl "$RAILWAY_PUBLIC_API_URL/health"
doppler run -- bun run --cwd apps/cloud test
```

The sync API accepts only `public` and `redacted-sync` event envelopes. It
rejects local-only, debug, document, blocked, or sensitive-field payloads even
when the request is authenticated.
Railway/production startup fails with the local in-memory cloud store unless
`INQUIRY_ALLOW_IN_MEMORY_CLOUD=1` is explicitly set, so a smoke deploy cannot be
mistaken for durable storage.

## Modal Jobs

Modal jobs live in `modal/`. They consume redacted session exports or explicitly
selected content snapshots and return reports with provenance and limitations.
Do not commit `.env` files; run with Doppler or provider-managed variables.

Local verification:

```bash
cd modal
python3 -m pytest
```

Deployment and smoke:

```bash
cd modal
doppler run -- modal deploy inquiry_jobs.py
doppler run -- modal run inquiry_jobs.py::smoke_job
```

The deployed `job_webhook` endpoint returns `modal_call_id` and `status` for the
Bun cloud API. Configure its URL as `MODAL_JOB_WEBHOOK_URL` and protect it with
`MODAL_JOB_WEBHOOK_TOKEN` when exposed.

If Modal is not configured, the Railway API falls back to a local Modal client
that records job submission state without requiring cloud credentials. Local
replay and export paths do not depend on Railway or Modal being available.
