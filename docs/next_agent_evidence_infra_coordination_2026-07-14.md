---
title: Evidence Infrastructure Coordination Note
date: 2026-07-15
status: active
owner_agent: cursor/u5-public-envelope (this session)
peer_warning: another agent may edit shared paths; rebase/merge carefully
---

# Evidence Infrastructure Coordination Note

Give this file to any other agent working in the same repo so they avoid
merge conflicts with the evidence-infrastructure landing sequence.

## Goal

Ship the six-PR evidence substrate from
`docs/next_agent_evidence_infrastructure_handoff_2026-07-14.md`, merging each
green PR before starting the next tranche from fresh `origin/main`.

| Unit | PR theme | Status |
|---|---|---|
| U2 / PR1 | Unified contract registry + coverage gate | **merged [#365](https://github.com/jawauntb/research-derived-experiments/pull/365)** |
| U3 / PR2 | Exact run provenance + adjudication | **merged [#367](https://github.com/jawauntb/research-derived-experiments/pull/367)** |
| U4 / PR3 | External Contact migration (Phase 5 deferred) | **merged [#368](https://github.com/jawauntb/research-derived-experiments/pull/368)** |
| U5 / PR4 | Public-envelope framework + E5 | **in progress** — `codex/u5-public-envelope` |
| U6 / PR5 | E4 producer + envelope | blocked on U5 |
| U7 / PR6 | Structured regen + clean-clone CI | blocked on U6 |

Current `main` partition after U4: **6 structured + 48 legacy = 54**.
Phase 5 remains a legacy exception pending a runtime-representation decision.

## Files this agent owns during U5

- `schemas/public_artifact_envelope.schema.json`
- `scripts/validate_public_artifact_envelopes.py`
- `templates/experiment/public_artifact_envelope.example.json`
- `experiments/commitment_surface/results/e5_generator_vs_coverage.json.envelope.json`
- `experiments/commitment_surface/experiment_manifest.json` (`envelope_path`)
- `scripts/export_commitment_surface_e5_results.py`
- `schemas/experiment_manifest.schema.json` / `scripts/validate_experiment_manifest.py`
- `scripts/run_quality_checks.py` + focused tests
- `docs/system_design.md`, `docs/module_explainer.md`, `TODO.md`, SE backlog
- this coordination note

## Constraints

- CPU-only for this tranche. Do not launch Modal/GPU.
- Do not regenerate the committed E5 public JSON without its ignored raw source.
- Sidecar binds to the **E5** producer manifest, not the M5 card primary.
- Do not mark broad migration TODOs complete while legacy exceptions remain.

## Handoff sources

- Controlling plan: `docs/next_agent_evidence_infrastructure_handoff_2026-07-14.md`
- Remaining note (execution state stale): `docs/next_agent_evidence_infrastructure_remaining_handoff_2026-07-14.md`
