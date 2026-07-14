---
title: Evidence Infrastructure Coordination Note
date: 2026-07-14
status: active
owner_agent: cursor/evidence-infra (this session)
peer_warning: rebase onto latest main; avoid concurrent edits to registry/validators/provenance
---

# Evidence Infrastructure Coordination Note

Hand this to any other agent working in the same repo.

## Merged today

| PR | Unit | Merge SHA | What landed |
|---|---|---|---|
| [#365](https://github.com/jawauntb/research-derived-experiments/pull/365) | U2 / PR1 | `9587eb8` | Authoritative `docs/experiment_contract_registry.json` (54 = 5 structured + 49 legacy), fail-closed coverage gate, frozen digest, CI historical-inspection ban |
| [#366](https://github.com/jawauntb/research-derived-experiments/pull/366) | docs | `8e5f3b6` | Remaining-work handoff (written before #365; recover-branch instructions are **obsolete**) |
| [#367](https://github.com/jawauntb/research-derived-experiments/pull/367) | U3 / PR2 | `723a46a` | Nested M5 manifest; commitment_surface E5/M5/E6/E7 runs; provenance consumes primary run; gate verdicts use registry-bound manifests |

Do **not** cherry-pick or recover `claude/evidence-infrastructure-handoff-r7h0h3`. U2 already landed via #365.

## Remaining sequence (dependency order)

| Unit | Theme | Status | Notes |
|---|---|---|---|
| U4 / PR3 | External Contact (+ optional Phase 5) | **in progress** on `codex/u4-external-contact-migration` | Phase 5 deferred → target **6 structured + 48 legacy** |
| U5 / PR4 | Public-envelope framework + E5 sidecar | blocked on U4 | Committed E5 digests are in the remaining handoff |
| U6 / PR5 | E4 nested manifest + envelope | blocked on U5 | Keep package history partial |
| U7 / PR6 | Structured regen + clean-clone CI | blocked on U6 | Allowlist: `bayesian_voi`, `mathematical_claims` |

Governing docs:

- `docs/next_agent_evidence_infrastructure_handoff_2026-07-14.md` (R1–R18, AE1–AE10)
- `docs/next_agent_evidence_infrastructure_remaining_handoff_2026-07-14.md` (execution refresh; ignore stale “PR1 unmerged” audit)

## Hot files during remaining work

Avoid parallel edits to:

- `docs/experiment_contract_registry.json`
- `schemas/*.schema.json`
- `scripts/validate_experiment_manifest.py`
- `scripts/gen_provenance.py`
- `scripts/validate_gate_verdict.py`
- `scripts/regen.py` / envelope validators (U5+)
- generated `PROVENANCE.md` / `docs/verification.*`
- `docs/system_design.md`, `docs/module_explainer.md`, `TODO.md`

Safer parallel work: unrelated experiment science, papers, app/coherence/site lanes, read-only review.

## Scientific guardrails

- Do not launch E6 / E5-L / E7 / M5 / GPU sweeps.
- Do not change frozen gates or scientific outcomes.
- M5 remains rejected / integrity-valid / unadjudicated.
- E7 remains integrity-invalid (not “rejected”).
- Empty `gate_verdict_paths` ≠ pass; only E5 currently binds a verdict file.

## Worktrees

- U2 (done): `~/.codex/worktrees/d3a3/...` on merged branch history
- U3 (done): `~/.codex/worktrees/u3-run-provenance/...`
- U4 (starting): `~/.codex/worktrees/u4-external-contact/...` on `codex/u4-external-contact-migration`
