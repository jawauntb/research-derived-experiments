# Architecture

Inquiry Black Box is split into local capture, local interpretation, optional
cloud coordination, and optional batch analysis.

## Local First

Electron is the local source of truth. It owns session state, SQLite, export,
deletion, notification outcomes, and the localhost bridge. The Chrome extension
queues browser events and retries against the local bridge, but SQLite remains
authoritative.

## Shared Schema

`packages/schema` defines the event envelope, privacy classes, retention
policies, and session records. Every producer creates events through this schema
so privacy class and retention are explicit at the point of capture.

## Signals

`packages/signals` converts event streams into windowed replay markers. Markers
must include evidence event ids and a suggested action. They are heuristics, not
diagnostic claims.

## Optional Cloud

Railway hosts the Bun API for redacted sync, report retrieval, device metadata,
and Modal orchestration. It should never be required for local replay.

## Modal

Modal jobs consume redacted exports or explicitly selected content snapshots.
They return reports, model cards, calibration metrics, and provenance rather
than raw private data.
