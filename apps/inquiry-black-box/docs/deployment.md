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

- `DATABASE_URL`: Railway Postgres connection string for the future durable
  store. The current foundation uses an in-memory store for local smoke tests.
- `RAILWAY_PUBLIC_API_URL`: public API base URL used by clients.
- `SYNC_ENCRYPTION_KEY`: key material for encrypted redacted sync payloads.

Optional Modal orchestration variables:

- `MODAL_JOB_WEBHOOK_URL` or `MODAL_WEBHOOK_URL`: HTTP entrypoint for a deployed
  Modal job trigger.
- `MODAL_JOB_WEBHOOK_TOKEN` or `MODAL_WEBHOOK_TOKEN`: bearer token for that
  trigger.
- `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, `MODAL_ENVIRONMENT`: Modal CLI and
  deployment credentials.

Use Doppler locally and Railway variables or a Doppler integration in deploys:

```bash
doppler setup
doppler run -- bun run --cwd apps/cloud dev
railway link
railway variables set DATABASE_URL=...
railway variables set SYNC_ENCRYPTION_KEY=...
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

If Modal is not configured, the Railway API falls back to a local Modal client
that records job submission state without requiring cloud credentials. Local
replay and export paths do not depend on Railway or Modal being available.
