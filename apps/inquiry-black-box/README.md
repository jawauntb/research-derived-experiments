# Inquiry Black Box

Local-first Neurophenom cockpit for capturing private research-session traces,
replaying comprehension moments, turning sessions into daily next-action
suggestions, and building a longitudinal dataset without storing raw camera
frames or raw keystrokes by default.

The current activation loop is: pair desktop + extension, start a titled session,
review daily replay and deterministic daily review, answer repair prompts, browse
recent session history, then export or confirm-delete local data.

Marketing site: `sites/inquiry_black_box` (repo-relative) links to this app path,
privacy model, and README.

## Workspace

```bash
cd apps/inquiry-black-box
bun install
bun run lint
bun run typecheck
bun run test
bun run test:e2e
bun run build:prototype
bun run package:local
bun run validation:smoke
```

`bun run test:e2e` includes the local demo fixture loop and extension pairing
smoke, so it works without Railway, Modal, Doppler, or model-provider keys.
For manual release proof, use the QA matrix and dogfood ledger in
[Prototype demo](docs/prototype-demo.md).

Packages:

- `apps/desktop`: Electron-oriented local shell, ingest bridge, SQLite-facing
  repository, camera features, notifications, replay, and privacy controls.
- `apps/extension`: Chrome MV3 telemetry capture with pairing and offline queue.
- `apps/cloud`: optional Railway Bun API for redacted sync and Modal job control.
- `packages/schema`: canonical event envelope, privacy classes, and session
  validation for replay, report, suggestion, notification, and model provenance
  events.
- `packages/signals`: windowing, heuristic markers, heatmaps, repair
  candidates, session interpretation, daily review, and redacted Modal job
  inputs.
- `packages/ui`: dependency-light UI view models shared by renderer surfaces.
- `modal`: Python batch-analysis jobs and model calibration helpers.

Cloud sync, desktop notifications, debug captures, document text upload, and
redacted LLM summaries are opt-in. The default local loop stores derived events,
timing aggregates, quality flags, local interpretations, suggestion feedback,
and daily reviews only.

## Guides

- [Agent guide](AGENTS.md)
- [Local development](docs/local-dev.md)
- [Prototype demo](docs/prototype-demo.md)
- [Architecture](docs/architecture.md)
- [Privacy model](docs/privacy-model.md)
- [Deployment](docs/deployment.md)
- [Research validation](docs/research-validation.md)
- [Release checklist](docs/release-checklist.md)
