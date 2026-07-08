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
compiled main/preload/renderer files, SQLite migrations, app metadata, and the
macOS `.icns` icon. This is for local installed smoke only.

After package smoke passes, install the app into the user Applications folder:

```bash
bun run install:desktop
```

The install command defaults to `~/Applications/Inquiry Black Box.app`, refuses
to replace an existing app unless you confirm or pass `--overwrite`, and prints
the installed path. Use the system Applications folder only with an explicit
target:

```bash
bun run install:desktop -- --target system
```

For throwaway install smoke, pass a test folder:

```bash
bun run install:desktop -- --destination /tmp/inquiry-apps --overwrite
open /tmp/inquiry-apps/Inquiry\ Black\ Box.app
```

Before wider distribution:

- Put the product logo at `assets/brand/logo.png` and run `bun run brand:sync`
  to regenerate desktop, extension, and site logo assets from that single
  source.
- Sign the app with bundle id `com.inquiry.blackbox`.
- Use `apps/desktop/packaging/mac/entitlements.plist` as the starting point for
  camera and localhost network permissions. Foreground app/window metadata uses
  visible in-app opt-in plus macOS automation/accessibility permission behavior;
  screen-content capture is intentionally not enabled in this package.
- Notarize the signed app with Apple Developer credentials.
- Smoke the signed build with a throwaway `INQUIRY_DESKTOP_DB_PATH`.

Installed desktop smoke:

1. Launch the packaged app.
2. Confirm the ingest bridge URL and pairing token are visible.
3. Pair the unpacked or packaged extension.
4. Enable Desktop app context only when you want cross-app metadata; leave
   Window titles off unless this smoke explicitly needs title capture.
5. Record, switch between Chrome and one or two desktop apps, stop, replay,
   export, delete, quit, relaunch, and confirm state recovery.

ScreenCaptureKit/screen snapshots are deferred. Do not add screen recording,
OCR, screenshot storage, or screen-content sync to this package without a
separate opt-in flow, Screen Recording permission smoke, local-only retention
rules, and schema tests proving raw screen payloads remain rejected by default.

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

Railway is only needed for the optional cloud API. Local desktop recording,
Chrome extension pairing, SQLite replay, local export, and local deletion do
not require Railway or Railway Postgres. Create the Railway app when you want
redacted sync, hosted report lookup, and cloud-to-Modal orchestration.

Create one Railway service rooted at `apps/inquiry-black-box`. The root
`railway.json` builds/tests `apps/cloud` and starts the Bun API with:

```bash
bun run --cwd apps/cloud dev
```

Required variables:

- `NIXPACKS_NODE_VERSION`: set to `22` so Railway/Nixpacks does not fall back to
  its removed Node 18 default.
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
npx -y @railway/cli init --name inquiry-black-box --json
npx -y @railway/cli add --service inquiry-black-box-api --json
npx -y @railway/cli add --database postgres --json
bun run railway:sync-model-env -- \
  --doppler-project cofounder \
  --doppler-config prd_superoptimizers \
  --env-file /Users/jawaun/jackson_prosocial_interp_research/.env \
  --railway-project inquiry-black-box-api \
  --railway-service inquiry-black-box-api \
  --railway-environment production
railway up --service inquiry-black-box-api
```

The sync script pipes values from Doppler to Railway with stdin and prints only
key names/status. It reuses the Superoptimizers Doppler model keys, can use the
social-cohesion/prosocial dotenv file as a fallback for model IDs, accepts
`HF_TOKEN` and `HUGGINGFACE_TOKEN`, and stores default research model IDs for
TRIBE v2, Brain2Qwerty, Braindecode, and Modal GPU selection when Doppler or the
dotenv fallback do not already own those keys. It also defaults
`MODEL_PROVIDER` to Anthropic, `EMBEDDING_MODEL` to `text-embedding-3-small`,
and derives `SESSION_SUMMARY_MODEL` from `ANTHROPIC_MODEL_BULK` when no explicit
summary model is configured.

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

Model/provider environment is resolved in `modal/model_env.py` and included in
Modal report provenance without secret values. Reuse the existing
Superoptimizers/social-cohesion keys wherever possible:

- Providers: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`,
  `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `VOYAGE_API_KEY`.
- Routing: `MODEL_PROVIDER`, `SESSION_SUMMARY_MODEL`, `EMBEDDING_MODEL`,
  `ANTHROPIC_MODEL_JUDGE`, `ANTHROPIC_MODEL_BULK`, `GEMINI_MODEL_VIDEO`,
  `GEMINI_MODEL_JUDGE`.
- Hugging Face: `HF_TOKEN`; `HUGGINGFACE_TOKEN` is accepted as an alias.
- Research model IDs: `TRIBE_MODEL_ID`, `TRIBE_MODEL_REVISION`,
  `TRIBE_GIT_REF`, `BRAIN2QWERTY_REPO`, `BRAIN2QWERTY_DATASET_ID`,
  `BRAINDECODE_MODEL_ID`, `VJEPA_MODEL_ID`, `VJEPA_LARGE_MODEL_ID`,
  `INTERNVIDEO_MODEL_ID`, `QWEN_VL_MODEL_ID`, `WHISPER_MODEL_ID`,
  `FASTER_WHISPER_MODEL_ID`, `SCV_OPEN_LLM_MODEL_ID`,
  `SCV_OPEN_LLM_ACTIVATION_LAYER`, and `SCV_MODAL_APP_BASE_NAME`.

Brain2Qwerty is a research-only, license-gated path until its data/model terms
allow product use. Do not route user production analysis through it by default.

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
