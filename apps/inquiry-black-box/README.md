# Inquiry Black Box

Local-first Neurophenom cockpit for capturing private research-session traces,
replaying comprehension moments, and building a longitudinal dataset without
storing raw camera frames or raw keystrokes by default.

## Workspace

```bash
cd apps/inquiry-black-box
bun install
bun run lint
bun run typecheck
bun run test
bun run test:e2e
```

Packages:

- `apps/desktop`: Electron-oriented local shell, ingest bridge, SQLite-facing
  repository, camera features, notifications, replay, and privacy controls.
- `apps/extension`: Chrome MV3 telemetry capture with pairing and offline queue.
- `apps/cloud`: optional Railway Bun API for redacted sync and Modal job control.
- `packages/schema`: canonical event envelope, privacy classes, and session
  validation.
- `packages/signals`: windowing and heuristic markers.
- `packages/ui`: dependency-light UI view models shared by renderer surfaces.
- `modal`: Python batch-analysis jobs and model calibration helpers.

Cloud sync, desktop notifications, debug captures, and any document text upload
are opt-in. The default local loop stores derived events, timing aggregates, and
quality flags only.

## Guides

- [Agent guide](AGENTS.md)
- [Local development](docs/local-dev.md)
- [Architecture](docs/architecture.md)
- [Privacy model](docs/privacy-model.md)
- [Deployment](docs/deployment.md)
- [Research validation](docs/research-validation.md)
