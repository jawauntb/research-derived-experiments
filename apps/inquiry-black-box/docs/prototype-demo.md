# Prototype Demo

Run all commands from `apps/inquiry-black-box`.

The local prototype does not require Railway, Modal, Doppler, or model-provider
keys. It uses desktop SQLite, the Electron shell, the unpacked Chrome extension,
local replay heuristics, deterministic stimulus heatmaps, repair prompts, JSONL
export, and local delete.

## Automated Fixture Proof

```bash
bun install
bun run demo:fixture
```

`bun run demo:fixture` runs `bun run test:e2e`. It proves both local fixture
paths:

- Extension-shaped browser telemetry posts through the paired desktop ingest
  handler into SQLite.
- A research-session fixture captures scroll, revisit, highlight/copy, media
  seek, tab churn, self-label, stimulus attachment, heatmap evidence, repair
  candidates, JSONL export, local delete, and a redacted cloud-delete tombstone.

Use this before a manual demo:

```bash
bun run lint
bun run typecheck
bun run test
bun run demo:fixture
bun run build:prototype
```

## Manual Desktop + Extension Demo

Build the prototype assets:

```bash
bun run build:prototype
```

Start the desktop app. The optional `INQUIRY_DESKTOP_DB_PATH` keeps a demo in a
throwaway SQLite file.

```bash
INQUIRY_DESKTOP_DB_PATH=/tmp/inquiry-demo.sqlite bun run dev:desktop
```

In Chrome:

1. Open `chrome://extensions`.
2. Enable Developer Mode.
3. Choose "Load unpacked".
4. Select `apps/inquiry-black-box/apps/extension`.

The extension root contains `manifest.json` and `popup.html`. Its built
background, content, and popup bundles are under `apps/extension/dist`.

Serve the demo article from a normal local HTTP origin:

```bash
python3 -m http.server 4173 --directory tests/fixtures
```

Open `http://127.0.0.1:4173/demo-article.html`.

## Demo Script

1. In the desktop app, start a session and copy the visible pairing token.
2. Open the extension popup, leave the endpoint as
   `http://127.0.0.1:39170/v1/extension/events`, paste the token, and pair.
3. Click Record in the extension popup.
4. Leave `Selected text excerpts` off for a derived-only run, or enable it when
   you want copied/highlighted excerpts stored locally as `document-opt-in`.
5. On the article page, scroll quickly, dwell briefly, highlight/copy a claim,
   seek the media control, and switch tabs once or twice.
6. Add a self-label in the desktop app.
7. Stop the session.
8. Inspect replay markers, evidence episodes, the comprehension heatmap, and the
   repair prompt.
9. Click Start on the repair prompt, answer it, then Save or Dismiss.
10. Export JSONL and confirm it contains derived events and repair outcomes, not
    raw camera frames, raw typed content, or raw article text by default. If
    `Selected text excerpts` was enabled, copied/highlighted excerpts appear as
    local `document-opt-in` events.
11. Delete the session and confirm the local session disappears.

## Expected Demo Signals

- The desktop header shows recording state, ingest URL, and pairing token.
- Replay includes event-backed evidence episodes and markers such as skim risk,
  copied passage, rewind, tab churn, labels, and probes.
- Copy/highlight evidence shows selected text snippets only when `Selected text
  excerpts` was enabled.
- The heatmap separates stimulus evidence from behavior evidence and shows
  confidence plus limitation copy.
- Repair actions are stored as `repair.candidate`, `probe.requested`,
  `probe.answered`, and `repair.outcome` events.
- Export/delete works without cloud credentials. Optional cloud sync remains
  limited to `public` and `redacted-sync` payloads.

## Packaging Notes

`bun run build:prototype` creates local desktop and extension build artifacts.
It is a developer-run prototype build, not a signed distribution. macOS signing,
notarization, auto-update, and Chrome Web Store publication remain follow-up
work.
