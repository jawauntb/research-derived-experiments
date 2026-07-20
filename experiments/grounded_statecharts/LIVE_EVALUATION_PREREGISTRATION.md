# Live Evaluation Contract Smoke — Preregistration

**Experiment ID:** `grounded_live_evaluation_smoke`  
**Date:** 2026-07-20  
**Claim tier:** descriptive  
**Status:** accepted mechanics smoke; not a D2 pilot

## Hypothesis

A provider-neutral live-evaluation contract can emit schema-valid sanitized
public rows with matched budgets, fixture replay integrity, and task-clustered
bootstrap intervals without contacting a live provider.

## Design

- Four smoke tasks: two artifact-completion, two recursive constrained tool-use.
- Six core conditions from the grounded-harness handoff.
- Two nested repeats per task × condition cell.
- Default executor: deterministic fixture adapter.
- Live adapter remains opt-in via `GROUNDED_HARNESS_LIVE=1` and is unused here.

## Primary outcomes

- Schema validity and publishable integrity receipts for every public row.
- Budget and sanitization fail-closed behavior.
- Exact fixture no-op replay of normalized actions.
- Seed-stable task-clustered bootstrap summaries.

## Explicit non-claims

- No live-agent population effect.
- No commercial usefulness claim.
- No confirmatory CT/CHS/HU result.
- Smoke outcomes are discarded from any later held-out D2 pilot.

## Kill criteria

- Any public row fails schema, sanitization, budget, or replay integrity.
- Default test path imports a provider SDK, requires credentials, or writes raw
  transcripts into `results/`.
- Bootstrap summaries are not reproducible from frozen public rows under the
  registered seed.
