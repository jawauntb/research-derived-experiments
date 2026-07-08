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

`packages/signals` converts event streams into windowed replay markers, then
builds local session interpretations and daily reviews. Markers, themes,
suggestions, and daily sections must include evidence event ids, report ids, or
an explicit low-confidence limitation. They are heuristics, not diagnostic
claims.

Session interpretation writes `report.generated` and `suggestion.candidate`
events back into SQLite when a session is stopped or refreshed. Daily review
aggregates those interpretations plus `suggestion.responded` feedback into the
six review sections: helped, fragmented, retry, ignore, open loops, and care
candidates.

## Notifications

Desktop notifications are opt-in and local. A daily checkup notification is
created from the daily review only after notifications are enabled, quiet hours
and cooldowns pass, and at least one actionable suggestion exists. Candidate and
delivered notifications are stored as local events for auditability.

## Optional Cloud

Railway hosts the Bun API for redacted sync, report retrieval, device metadata,
and Modal orchestration. It should never be required for local replay.

## Modal

Modal jobs consume redacted exports, redacted session interpretation summaries,
or explicitly selected content snapshots. The session-summary path requires
`redacted-sync`, rejects app names, bundle IDs, window titles, raw text, and
desktop event objects, then returns report payloads and model provenance rather
than raw private data.
