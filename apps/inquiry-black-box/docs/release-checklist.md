# Release Checklist

Use this checklist from `apps/inquiry-black-box` when deciding whether Inquiry
Black Box is ready for a local demo, packaged demo, cloud smoke, or validation
review.

## Automated Gates

```bash
bun install
bun run install:check
bun run lint
bun run typecheck
bun run test
bun run test:e2e
bun run build:prototype
bun run package:extension
bun run package:desktop
bun run validation:smoke
cd modal && python3 -m pytest
```

`bun run package:desktop` creates a local macOS app bundle. It signs the app
when `INQUIRY_MAC_CODESIGN_IDENTITY` or `INQUIRY_MAC_DEVELOPER_ID` is set on a
macOS release machine; otherwise it records that signing was skipped in the
package README. Notarize signed release archives before external distribution.

## Local Developer Demo

```bash
bun run build:prototype
mkdir -p tmp
INQUIRY_DESKTOP_DB_PATH=tmp/inquiry-demo.sqlite bun run dev:desktop
python3 -m http.server 4173 --directory tests/fixtures
```

Load `apps/inquiry-black-box/apps/extension` as an unpacked Chrome extension,
open `http://127.0.0.1:4173/demo-article.html`, click **Pair with local
desktop** in the popup, click Record in the extension, interact with two normal
`http`/`https` tabs, stop, inspect replay, request a redacted LLM summary only
after enabling Cloud sync, export, delete, restart desktop, and reload the
extension.

Record the result with the dogfood ledger in
[Prototype Demo](prototype-demo.md).

## Database Inspection

```bash
sqlite3 tmp/inquiry-demo.sqlite '.tables'
sqlite3 tmp/inquiry-demo.sqlite 'select session_id,title,recording_state,started_at,ended_at from sessions;'
sqlite3 tmp/inquiry-demo.sqlite 'select event_type,privacy_class,retention_policy,count(*) from events group by 1,2,3 order by 1;'
sqlite3 tmp/inquiry-demo.sqlite 'select kind,payload from sync_queue order by queued_at desc limit 5;'
```

Expected local evidence:

- Browser events from normal tabs share one authoritative desktop session.
- `camera.feature_window` has quality flags and derived feature payloads only.
- Selected text snippets appear only as local `document-opt-in` events after
  the explicit opt-in.
- Delete removes local session/events and queues only redacted cloud-delete
  tombstone metadata when needed.

## Packaged Smoke

```bash
bun run package:desktop
bun run package:extension
```

Smoke `apps/desktop/release/mac/Inquiry Black Box.app` and
`apps/extension/release/extension/inquiry-black-box-extension-0.1.0.zip`.
Confirm `inquiry-black-box://pair` opens or focuses the desktop app, the popup
one-click pairing succeeds, and manual token pairing remains available as a
fallback.

Optional redacted desktop LLM summaries require Cloud sync opt-in plus a
pre-issued desktop bearer token:

- `RAILWAY_PUBLIC_API_URL` or `INQUIRY_CLOUD_API_URL`
- `INQUIRY_CLOUD_BEARER_TOKEN` (legacy alias: `INQUIRY_CLOUD_AUTH_TOKEN`)

Store art lives in `assets/store`:

- `chrome-store-small-tile.png` (440 x 280)
- `chrome-store-marquee.png` (1280 x 800)
- `chrome-store-screenshot.png` (1280 x 800)

## Railway Smoke

Required variables:

- `INQUIRY_CLOUD_AUTH_SECRET`
- `DATABASE_URL`
- `SYNC_ENCRYPTION_KEY`
- `RAILWAY_PUBLIC_API_URL`

```bash
curl "$RAILWAY_PUBLIC_API_URL/health"
curl "$RAILWAY_PUBLIC_API_URL/ready"
```

`/ready` must report durable `postgres` storage before a cloud release is
considered ready. In-memory storage is allowed only for explicit ephemeral smoke.

## Modal Smoke

```bash
cd modal
python3 -m pytest
doppler run -- modal deploy inquiry_jobs.py
doppler run -- modal run inquiry_jobs.py::smoke_job
```

Then submit a redacted `session_summary` job through Railway `/jobs`. Sensitive
fields must reject before Modal invocation.

## Hosted Reports

Hosted report routes are for redacted review only:

```bash
curl "$RAILWAY_PUBLIC_API_URL/reports" \
  -H "authorization: Bearer $INQUIRY_CLOUD_BEARER_TOKEN"
```

Document-opt-in snippets, local-derived data, raw page text, raw typed content,
and raw camera frames must stay out of hosted responses.

## Validation

```bash
bun run validation:smoke
```

Review `research/validation-smoke-report.md`. G0-G1 are fixture smoke only.
G2-G4 must remain `insufficient-data` until held-out dogfood sessions and repair
comparisons exist.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Popup says `0 queued` or `Queue clear` | Healthy if events are posting; inspect event counts in SQLite. |
| Popup says page listener missing | Reload a normal page; restricted `chrome://` pages are unsupported by design. |
| Extension still says Recording after desktop Stop | Reopen popup or wait for heartbeat; desktop status should reconcile to Stopped. |
| Desktop bridge offline | Confirm the desktop app is running and endpoint is `http://127.0.0.1:39170/v1/extension/events`. |
| Camera looks inactive | Check permission, enabled state, feature heartbeat, and quality rows in the camera panel. |
| Replay empty | Confirm the session was stopped after events arrived and inspect event counts in SQLite. |
| Cloud sync rejected | Confirm privacy class is `public` or `redacted-sync` and payload has no sensitive aliases. |
| Modal job failed | Check webhook URL/token, timeout, and that input is redacted before invocation. |

## Outside MVP

- Medical, diagnostic, emotion-certainty, lie-detection, or workplace
  surveillance claims.
- Hidden recording, raw keylogging, routine raw video, routine raw typed
  content, ambient page text capture, or silent cloud upload.
- Paid accounts, teams, billing, organization admin, auto-update, native mobile,
  or EEG expansion.
- Native messaging unless installed localhost reconciliation fails for a
  concrete distribution reason.
