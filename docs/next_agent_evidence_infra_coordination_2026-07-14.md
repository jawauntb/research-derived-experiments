---
title: Evidence Infrastructure Coordination Note
date: 2026-07-14
status: active
owner_agent: cursor/u3-run-provenance (this session)
peer_warning: another agent may edit shared paths; rebase/merge carefully
---

# Evidence Infrastructure Coordination Note

Give this file to any other agent working in the same repo so they avoid
merge conflicts with the evidence-infrastructure landing sequence.

## Goal

Ship the six-PR evidence substrate from
`docs/next_agent_evidence_infrastructure_handoff_2026-07-14.md`, merging each
green PR before starting the next tranche from fresh `origin/main`.

Execution state is refreshed by
`docs/next_agent_evidence_infrastructure_remaining_handoff_2026-07-14.md`
(PR #366), except that **U2 / PR1 is now merged** (see below). Do not recover
the superseded remote branch `claude/evidence-infrastructure-handoff-r7h0h3`.

| Unit | PR theme | Branch / worktree | Status |
|---|---|---|---|
| U2 / PR1 | Unified contract registry + coverage gate | `codex/u2-experiment-contract-registry` | **merged [#365](https://github.com/jawauntb/research-derived-experiments/pull/365)** at `9587eb8` |
| U3 / PR2 | Exact run provenance + adjudication | `codex/u3-run-provenance` in `~/.codex/worktrees/u3-run-provenance/...` | **in progress now** |
| U4 / PR3 | External Contact + Phase 5 migrations | fresh after U3 | blocked |
| U5 / PR4 | Public-envelope framework + E5 | fresh after U4 | blocked |
| U6 / PR5 | E4 producer + envelope | fresh after U5 | blocked |
| U7 / PR6 | Structured regen + clean-clone CI | fresh after U6 | blocked |

Do **not** implement U4+ on the U3 branch.

## Files this agent owns during U3

Treat these as hot until U3 merges:

- `docs/experiment_contract_registry.json`
- `scripts/gen_provenance.py`
- `scripts/validate_gate_verdict.py`
- `experiments/commitment_surface/manifests/m5/experiment_manifest.json` (new)
- focused provenance / gate-verdict tests
- generated provenance outputs when `gen_provenance.py` is run
- `docs/system_design.md`, `docs/module_explainer.md`, `TODO.md`, SE backlog

## Safer surfaces for a parallel agent

- Unrelated scientific experiment packages
- Paper/PDF builders that do not touch contract registries or provenance generators
- App / coherence / site lanes
- Read-only audits

Avoid simultaneous edits to shared schemas, validators, `gen_provenance.py`,
generated verification indexes, or root quality wiring.

## Already landed today

- PR [#364](https://github.com/jawauntb/research-derived-experiments/pull/364): PAC-Bayes weakness sketch (unrelated docs)
- PR [#366](https://github.com/jawauntb/research-derived-experiments/pull/366): remaining-work handoff doc
- PR [#365](https://github.com/jawauntb/research-derived-experiments/pull/365): U2 contract registry

## Constraints

- U3+ follows the remaining handoff: CPU-only repository work; do not launch GPU
  experiments (E6/E5-L/E7/M5) or change scientific verdicts.
- Do not mark broad migration TODOs complete while exceptions / partial histories remain.
- Do not adjudicate M5 claims; keep M5 rejected/valid/unadjudicated.

## After each merge

1. Fetch/prune `origin`.
2. Confirm the PR is closed/merged.
3. Create a **new** worktree/branch from `origin/main` for the next unit.
4. Update this table with PR numbers and SHAs.
