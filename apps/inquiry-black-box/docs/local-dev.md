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
Manual Chrome loading is still a smoke step; CI tests use fixture-friendly
content and bridge modules instead of a real browser.

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
