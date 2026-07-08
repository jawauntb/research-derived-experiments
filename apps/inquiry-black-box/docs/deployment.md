# Inquiry Black Box Deployment

The desktop and extension remain local-first. Railway and Modal are optional
cloud surfaces for redacted sync, report lookup, and heavier batch jobs.

## Desktop Package

The repo-verifiable desktop package is an unsigned macOS developer bundle:

```bash
bun run package:desktop
```

The command builds the desktop app and writes
`apps/desktop/release/mac/Inquiry Black Box.app`. It stages the Electron runtime,
compiled main/preload/renderer files, SQLite migrations, app metadata, and icon
source. This is for local installed smoke only.

Before wider distribution:

- Convert `apps/desktop/assets/icon.svg` into the required `.icns` sizes.
- Sign the app with bundle id `com.inquiry.blackbox`.
- Use `apps/desktop/packaging/mac/entitlements.plist` as the starting point for
  camera and localhost network permissions.
- Notarize the signed app with Apple Developer credentials.
- Smoke the signed build with a throwaway `INQUIRY_DESKTOP_DB_PATH`.

Installed desktop smoke:

1. Launch the packaged app.
2. Confirm the ingest bridge URL and pairing token are visible.
3. Pair the unpacked or packaged extension.
4. Record, stop, replay, export, delete, quit, relaunch, and confirm state
   recovery.

## Chrome Extension Package

Build a reviewable MV3 ZIP with:

```bash
bun run package:extension
```

The command writes
`apps/extension/release/extension/inquiry-black-box-extension-0.1.0.zip` from a
clean staging folder containing only `manifest.json`, `popup.html`, runtime
bundles, and assets.

Permission rationale for review:

- `activeTab`, `scripting`, and `tabs`: detect or inject the content listener on
  the active normal page and show unsupported-page status.
- `storage`: keep pairing, privacy toggles, disabled-site hashes, and the retry
  queue local to the browser profile.
- `alarms`: retry queued events and reconcile desktop recording state.
- `http://*/*` and `https://*/*`: content scripts run only on normal web pages;
  restricted Chrome/internal pages are reported as unsupported.

Store/privacy copy should say that the extension sends derived browser telemetry
to the paired local desktop app, stores selected text excerpts only after an
explicit local opt-in, and does not silently upload local-only data to cloud
services.

Installed extension smoke:

1. Load the ZIP or staged folder in Chrome.
2. Pair with the packaged desktop app.
3. Click Record, interact with two normal `http`/`https` tabs, reload the
   extension, reload a page, disable a site, stop, and inspect desktop replay.
4. Confirm `Selected text excerpts` defaults off after a fresh install.

## Installed Bridge Decision

Native messaging is not part of the default release path. The desktop remains
the source of truth through the localhost bridge and paired status
reconciliation. Add a native messaging host only if installed smoke shows a
specific failure that localhost polling cannot solve, such as a required
desktop-to-extension command or a packaged security policy that blocks the
local bridge.

If native messaging becomes necessary, document host registration, uninstall,
pairing-token checks, and message rejection for unpaired or privacy-ineligible
payloads before shipping it.

## Railway API

Create one Railway service rooted at `apps/inquiry-black-box` and point it at
`apps/cloud/railway.json`. The service starts the Bun API with:

```bash
bun run --cwd apps/cloud dev
```

Required variables:

- `INQUIRY_CLOUD_AUTH_SECRET`: HMAC secret used to verify cloud bearer tokens.
- `DATABASE_URL`: Railway Postgres connection string. When present, the API
  selects the Postgres cloud store and runs idempotent table/index creation
  during health/readiness checks and first store use.
- `RAILWAY_PUBLIC_API_URL`: public API base URL used by clients.
- `SYNC_ENCRYPTION_KEY`: key material for encrypted redacted sync payloads.
- `INQUIRY_ALLOW_IN_MEMORY_CLOUD=1`: only for ephemeral Railway smoke tests
  without `DATABASE_URL`. Leave unset for real deployments.

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
curl "$RAILWAY_PUBLIC_API_URL/ready"
doppler run -- bun run --cwd apps/cloud test
```

The `/health` response includes `storage` and waits for the configured store to
initialize, so a Postgres migration/connection failure fails the Railway health
check instead of silently passing a process-only probe.
The `/ready` response returns `200` only for durable Postgres-backed storage and
returns `503` for local in-memory storage, which keeps ephemeral smoke mode
separate from a release-ready Railway service.

The sync API accepts only `public` and `redacted-sync` event envelopes. It
rejects local-only, debug, document, blocked, or sensitive-field payloads even
when the request is authenticated.
Railway/production startup fails with the local in-memory cloud store unless
`INQUIRY_ALLOW_IN_MEMORY_CLOUD=1` is explicitly set, so a smoke deploy cannot be
mistaken for durable storage.
Railway/production startup also fails without `INQUIRY_CLOUD_AUTH_SECRET`, even
before the first authenticated sync request.

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

Cloud-to-Modal smoke can be verified through the Bun API with a redacted input:

```bash
curl -X POST "$RAILWAY_PUBLIC_API_URL/jobs" \
  -H "authorization: Bearer $INQUIRY_CLOUD_BEARER_TOKEN" \
  -H "content-type: application/json" \
  --data '{
    "kind": "session_summary",
    "session_id": "smoke-session",
    "input": {
      "privacy_class": "redacted-sync",
      "payload": { "export_ref": "smoke-fixture" }
    }
  }'
```

The response should include a `job.modal_call_id` and `job.status`. Do not send
raw page text, typed content, camera frames, or video bytes in a `redacted-sync`
Modal job; the API rejects those fields before the Modal webhook is called.

If Modal is not configured, the Railway API falls back to a local Modal client
that records job submission state without requiring cloud credentials. Local
replay and export paths do not depend on Railway or Modal being available.

## Hosted Redacted Reports

Hosted reports are a remote review surface for `public` or `redacted-sync`
analysis outputs only. They are not a mirror of local replay and must not expose
`local-derived`, `document-opt-in`, debug, blocked, raw camera, raw typed, or raw
page/selection payloads.

Report lookup:

```bash
curl "$RAILWAY_PUBLIC_API_URL/reports" \
  -H "authorization: Bearer $INQUIRY_CLOUD_BEARER_TOKEN"

curl "$RAILWAY_PUBLIC_API_URL/reports/$REPORT_ID" \
  -H "authorization: Bearer $INQUIRY_CLOUD_BEARER_TOKEN"
```

The route is scoped to the authenticated user and redacts sensitive payload or
provenance fields before returning a hosted review response. Document-opt-in
snippets remain local/exportable unless a separate explicit share flow is
designed later.
