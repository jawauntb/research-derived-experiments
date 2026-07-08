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
bun run package:desktop
bun run install:desktop -- --destination /tmp/inquiry-apps --overwrite
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

## Manual QA Matrix

Use this matrix for each dogfood pass. Record the result in the ledger below
instead of editing this runbook.

| Area | Action | Expected result |
| --- | --- | --- |
| Desktop startup | Start `bun run dev:desktop` with a throwaway `INQUIRY_DESKTOP_DB_PATH`. | Header shows ingest URL, recording state, and a visible pairing token. |
| Pairing | Pair the unpacked extension with the desktop token. | Popup shows paired state without requiring desktop Start. |
| Extension Record | Click Record in the extension popup. | Desktop session starts or resumes and the popup switches to Recording. |
| Cross-tab capture | Interact with the demo article, then a second normal `http` or `https` tab. | Browser events from both tabs land in the same desktop session. |
| Unsupported page | Open `chrome://extensions` or another restricted page. | Popup reports the page is unsupported rather than implying capture is broken. |
| Camera permission | Enable camera features with permission allowed, denied, and not yet granted where possible. | UI distinguishes permission, enabled state, feature heartbeat, and degraded quality. |
| Desktop activity off | Leave Desktop app context off, switch from Chrome to another app, then stop. | Replay/export contain no `desktop.app_focus` or `desktop.window_focus` events. |
| Desktop activity on | Enable Desktop app context with Window titles off, switch among Chrome, Cursor/Terminal, and back. | Replay shows app-level desktop context and no window title strings. |
| Window titles opt-in | Enable Window titles only for a throwaway session. | Desktop window events are `document-opt-in`, bounded, exportable locally, and cloud-ineligible. |
| Selected text off | Copy/highlight text with `Selected text excerpts` off. | Replay/export show counts, lengths, hashes, and privacy limits without raw snippets. |
| Selected text on | Repeat after enabling `Selected text excerpts`. | Bounded local snippets appear as `document-opt-in`; cloud sync remains ineligible. |
| Stop/replay | Stop from extension, then inspect the desktop replay. | Replay refreshes, leads with evidence episodes, and shows heatmap and repair prompt. |
| Export/delete | Export JSONL, then delete the session. | Export omits raw frames/raw typed content by default; delete removes local rows and queues a redacted tombstone if cloud sync applies. |
| Restart/reload | Restart desktop and reload the extension. | Pairing and recording state reconcile; stale Recording state does not silently keep capturing. |
| Design QA | Capture desktop wide, desktop narrow, and Chrome popup screenshots. | Soft raised/inset controls are readable, focus is visible, text wraps, and no dense workflow state overlaps. |

## Dogfood Ledger Template

Copy this template into the PR, issue, or release notes for each manual pass.

```markdown
### Inquiry dogfood ledger

- Date:
- Build commit:
- OS / Chrome version:
- Desktop command:
- DB path:
- Extension path:
- Session id:
- Pages exercised:
- Camera permission state:
- Selected text excerpts: off / on
- Cloud sync: off / on
- Events captured by type:
- Replay outcome:
- Export/delete outcome:
- Restart/reload outcome:
- Screenshots or recordings:
- Design QA screenshots: desktop wide / desktop narrow / popup
- Bugs found:
- Follow-up tickets:
- Release decision: pass / blocked
```

## Database Inspection

With the desktop stopped or while using a throwaway demo DB, inspect the local
SQLite file directly:

```bash
sqlite3 /tmp/inquiry-demo.sqlite '.tables'
sqlite3 /tmp/inquiry-demo.sqlite 'select session_id,title,recording_state,started_at,ended_at from sessions;'
sqlite3 /tmp/inquiry-demo.sqlite 'select event_type,privacy_class,retention_policy,count(*) from events group by 1,2,3 order by 1;'
sqlite3 /tmp/inquiry-demo.sqlite 'select kind,payload from sync_queue order by queued_at desc limit 5;'
```

Useful checks:

- `camera.feature_window` events exist after a camera-enabled run, with quality
  flags but no raw image fields.
- `browser.copy` and `browser.highlight` events are `local-derived` unless
  selected-text excerpts were explicitly enabled.
- `document-opt-in` events appear only for local/exportable selected snippets.
- Sync tombstones contain the session id and delete action, not raw local data.

## Demo Script

1. Open the desktop app and copy the visible pairing token. You do not need to
   click desktop Start for a browser-plus-desktop demo; extension Record starts
   the desktop session after pairing.
2. Open the extension popup, leave the endpoint as
   `http://127.0.0.1:39170/v1/extension/events`, paste the token, and pair.
3. Click Record in the extension popup. The popup should switch to Recording
   and show `Queue clear` when no retry backlog exists.
4. Leave `Selected text excerpts` off for a derived-only run, or enable it when
   you want copied/highlighted excerpts stored locally as `document-opt-in`.
5. On the article page, scroll quickly, dwell briefly, highlight/copy a claim,
   seek the media control, and switch tabs once or twice.
6. Add a self-label in the desktop app.
7. Stop the session from the extension popup. For browser-plus-desktop demos,
   extension Stop also asks the desktop session to stop.
8. Inspect replay markers, evidence episodes, the comprehension heatmap, and the
   repair prompt.
9. Click Start on the repair prompt, answer it, then Save or Dismiss.
10. Export JSONL and confirm it contains derived events and repair outcomes, not
    raw camera frames, raw typed content, or raw article text by default. If
    `Selected text excerpts` was enabled, copied/highlighted excerpts appear as
    local `document-opt-in` events.
11. Delete the session and confirm the local session disappears.

For packaged smoke, run `bun run package:desktop`, then
`bun run install:desktop -- --destination /tmp/inquiry-apps --overwrite`, open
the installed app manually, and repeat the same pair/record/replay/export/delete
loop. Move to `~/Applications` only after this throwaway install passes.

## Expected Demo Signals

- The desktop header shows recording state, ingest URL, and pairing token.
- Replay includes event-backed evidence episodes and markers such as skim risk,
  copied passage, rewind, tab churn, app churn, desktop work spans, labels, and
  probes.
- Copy/highlight evidence shows selected text snippets only when `Selected text
  excerpts` was enabled.
- The heatmap separates stimulus evidence from behavior evidence and shows
  confidence plus limitation copy.
- Repair actions are stored as `repair.candidate`, `probe.requested`,
  `probe.answered`, and `repair.outcome` events.
- Export/delete works without cloud credentials. Optional cloud sync remains
  limited to `public` and `redacted-sync` payloads.

## Known Failure Modes

- `Queue clear` means no retry backlog exists; it is healthy when events are
  posting successfully.
- Restricted pages such as `chrome://extensions` cannot run the content script.
  Use the popup listener status to distinguish unsupported pages from a missing
  listener on a normal page.
- A desktop Stop, desktop crash, extension reload, or popup reopen should
  reconcile recording state before additional capture continues.
- Real camera permission prompts are OS/browser controlled and are not proven by
  fixture tests; smoke them manually on the target Mac.
- Fixture E2E does not prove a packaged app, installed extension, Railway,
  Modal, or Chrome Web Store behavior.

## Packaging Notes

`bun run build:prototype` creates local desktop and extension build artifacts.
It is a developer-run prototype build, not a signed distribution.

Unsigned local package commands:

```bash
bun run package:desktop
bun run package:extension
```

Smoke the packaged desktop app and packaged/staged extension with the same demo
script above after app restart and extension reload. macOS signing,
notarization, auto-update, and Chrome Web Store publication require account-level
credentials outside the repo.
