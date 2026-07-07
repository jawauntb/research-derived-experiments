# Local Development

Run from `apps/inquiry-black-box`.

```bash
bun install
bun run lint
bun run typecheck
bun run test
bun run test:e2e
```

The app is intentionally useful without cloud credentials. Desktop SQLite,
extension telemetry fixtures, replay heuristics, privacy export/delete, and
cloud rejection tests all run locally.

The committed local demo fixture lives at
`tests/fixtures/demo-article.html`. `bun run test:e2e` exercises a fixture path
that captures browser scroll, revisit, highlight/copy, media seek, tab churn,
self-label, and recall-probe events, then verifies replay evidence, JSONL
export, local delete, and the redacted cloud-delete tombstone.

## Desktop

```bash
bun run dev:desktop
```

The desktop side owns SQLite, the localhost ingest bridge, session lifecycle,
pairing tokens, privacy export/delete, notifications, and sync queueing.

## Extension

```bash
bun run dev:extension
```

The build command creates unpacked MV3 assets under `apps/extension/dist`.
Load `apps/inquiry-black-box/apps/extension` as the unpacked extension folder in
Chrome. The root folder contains `manifest.json` and `popup.html`; the built
background, content, and popup bundles live under `dist`.

Pairing smoke:

1. Run `bun run dev:desktop` and start a session in the desktop window.
2. Copy the desktop pairing token.
3. Load the unpacked extension folder in Chrome and pin/open the popup.
4. Paste the token, keep the endpoint at `http://127.0.0.1:39170/v1/extension/events`, and pair.
5. Click Record in the popup, visit a normal `http` or `https` page, then scroll, highlight/copy, and seek media.
6. Use Pause, Stop, and Disable site from the popup to confirm new events stop posting.

CI tests use fixture-friendly content and bridge modules instead of a real
browser. `bun run test:e2e` includes a pairing smoke that posts extension-shaped
browser events through the desktop ingest handler into SQLite.

## Human Demo Checklist

Use this as the short manual proof after the fixture tests pass:

1. Start `bun run dev:desktop`.
2. Start a session, copy the pairing token, and pair the unpacked extension.
3. Open `tests/fixtures/demo-article.html` through a local `http` server or any
   normal `http`/`https` research page.
4. Scroll quickly, highlight/copy one claim, seek the media control, switch tabs,
   and add a self-label in the desktop window.
5. Stop the session, inspect replay markers, export JSONL, then delete the
   session and confirm the cloud-delete tombstone is queued locally.

## Cloud

```bash
doppler run -- bun --cwd apps/cloud run dev
```

Cloud sync is optional. The API accepts `public` and `redacted-sync` payloads
only and rejects raw-sensitive fields.

## Modal

```bash
cd modal
python3 -m pytest
doppler run -- python3 -m pytest
```

Use Doppler when credentials or provider keys are needed. The committed tests do
not require Modal credentials.
