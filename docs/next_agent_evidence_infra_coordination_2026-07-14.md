---
title: Evidence Infrastructure Coordination Note
date: 2026-07-14
status: active
owner_agent: cursor/u2-contract-registry (this session)
peer_warning: another agent may edit shared paths; rebase/merge carefully
---

# Evidence Infrastructure Coordination Note

Give this file to any other agent working in the same repo so they avoid
merge conflicts with the evidence-infrastructure landing sequence.

## Goal

Ship the six-PR evidence substrate from
`docs/next_agent_evidence_infrastructure_handoff_2026-07-14.md`, merging each
green PR before starting the next tranche from fresh `origin/main`.

| Unit | PR theme | Branch / worktree | Status |
|---|---|---|---|
| U2 / PR1 | Unified contract registry + coverage gate | `codex/u2-experiment-contract-registry` in `~/.codex/worktrees/d3a3/...` | **in progress now** |
| U3 / PR2 | Exact run provenance + adjudication | fresh worktree after U2 merges | blocked on U2 |
| U4 / PR3 | External Contact + Phase 5 migrations | fresh after U3 | blocked |
| U5 / PR4 | Public-envelope framework + E5 | fresh after U4 | blocked |
| U6 / PR5 | E4 producer + envelope | fresh after U5 | blocked |
| U7 / PR6 | Structured regen + clean-clone CI | fresh after U6 | blocked |

Do **not** implement U3+ on the U2 branch.

## Files this agent owns during U2

Treat these as hot. Prefer not to edit them until U2 merges:

- `docs/experiment_contract_registry.json` (new)
- `schemas/experiment_contract_registry.schema.json` (new)
- `scripts/validate_experiment_manifest.py`
- `tests/test_experiment_manifest.py`
- `tests/test_research_contract_schema_parity.py`
- `docs/system_design.md`
- `docs/module_explainer.md`
- `TODO.md`
- `docs/primers/backlogs/software_engineering_todo.md`
- this coordination note / U2 handoff docs under `docs/next_agent_*`

`scripts/run_quality_checks.py` is **not** intentionally changed by U2; the
existing no-argument manifest validator step becomes the coverage gate.

## Safer surfaces for a parallel agent

These are lower conflict risk while U2 lands:

- Scientific experiment code under packages that are not schema/validator work
- Paper/PDF builders unrelated to contract registries
- App / coherence / site lanes
- Read-only audits and review comments

Avoid simultaneous edits to shared schemas, validators, generated provenance
indexes, or the root quality wrapper unless you rebase onto the merged U2 tip.

## Known peer worktree

- `~/.codex/worktrees/0364/...` on `codex/faster-cpu-quality-gate` currently
  sits **behind** `main` (`e541978` ancestor of `befa8be`). If that branch is
  revived, rebase after U2 merges and watch `scripts/run_quality_checks.py` /
  quality tests.

## Constraints

- U2 verification is Modal-only for pytest/Ruff/ty/full quality
  (`tmp/modal_u2_quality.py`, untracked, delete after U2 ships).
- Do not launch GPU experiments (E6/E5-L/E7/M5).
- Do not adjudicate M5 claims in U2.
- Do not mark broad migration TODOs complete while 49 exceptions remain.

## After U2 merges

1. Fetch/prune `origin`.
2. Confirm U2 PR is closed/merged and no open PR owns the registry schema.
3. Create a **new** worktree/branch from `origin/main` for U3.
4. Update this coordination table with PR numbers and SHAs.
5. Continue U3→U7 the same way: one tranche, Modal/full quality, review, merge.

## Handoff sources

- Controlling plan: `docs/next_agent_evidence_infrastructure_handoff_2026-07-14.md`
- U2 resume detail: `docs/next_agent_u2_contract_registry_handoff_2026-07-14.md`
