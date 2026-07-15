---
title: Evidence Infrastructure Completion Status for Peer Agents
date: 2026-07-15
status: complete_for_six_pr_tranche
---

# Evidence Infrastructure Completion Status for Peer Agents

Hand this to any other agent before touching shared schemas, validators,
provenance, envelopes, or `scripts/regen.py`.

## What landed (merge in order)

| Unit | PR | Merge commit | What changed |
|---|---|---|---|
| U2 | [#365](https://github.com/jawauntb/research-derived-experiments/pull/365) | `9587eb8` | Authoritative `docs/experiment_contract_registry.json` + fail-closed coverage gate |
| U3 | [#367](https://github.com/jawauntb/research-derived-experiments/pull/367) | `723a46a` | Exact primary-run provenance / adjudication semantics |
| U4 | [#368](https://github.com/jawauntb/research-derived-experiments/pull/368) | `2b9decd` | External Contact LoRA structured migration (**Phase 5 deferred**) |
| U5 | [#369](https://github.com/jawauntb/research-derived-experiments/pull/369) | `beb2dd8` | Public-envelope schema/validator + E5 sidecar |
| U6 | [#370](https://github.com/jawauntb/research-derived-experiments/pull/370) | `0654d50` | E4 nested producer manifest + unadjudicated E4 envelope |
| U7 | [#371](https://github.com/jawauntb/research-derived-experiments/pull/371) | `593bdfa` | Allowlisted clean-clone argv regen + CI `clean-clone-cpu` job |

Current `main` tip after this tranche: **`593bdfa`**.

## Exact post-tranche counts

- Research packages: **54** (`common` excluded)
- Structured roots: **6**
- Legacy exceptions: **48**
- Frozen legacy digest unchanged:
  `86703ca46bc2a759a5f054247512c9c0df558404711db5c564ca58dfc76f2c77`
- Public envelopes: **2**
  - `e5_generator_vs_coverage.json.envelope.json` (bound; E5 producer)
  - `e4_pythia_lora_v2_appendix.json.envelope.json` (unadjudicated; E4 producer)
- Clean-clone allowlist: `bayesian_voi`, `mathematical_claims`
- `commitment_surface` run coverage: **partial**
  - structured: E4, E5, M5
  - legacy-report: E6 (`not_assessed`), E7 (`invalid`)
  - primary display run: **M5**

## Intentionally still open

- Phase 5 structured migration (manifest v1 is one command; Phase 5 has producer + summarizer)
- Remaining 48 legacy exceptions / partial histories
- `semantic_concern_geometry` multi-execution contract
- Broad public-envelope adoption beyond E4/E5
- Expanding clean-clone beyond the two CPU allowlisted packages
- Do **not** mark the broad TODO migration items complete

## Hot files (assume contended)

If you edit these, rebase onto `origin/main` after `593bdfa` and expect conflicts with this tranche:

- `docs/experiment_contract_registry.json`
- `schemas/experiment_contract_registry.schema.json`
- `schemas/public_artifact_envelope.schema.json`
- `schemas/experiment_manifest.schema.json`
- `scripts/validate_experiment_manifest.py`
- `scripts/validate_public_artifact_envelopes.py`
- `scripts/gen_provenance.py`
- `scripts/regen.py`
- `scripts/run_quality_checks.py`
- `.github/workflows/quality.yml`
- `docs/system_design.md`, `docs/module_explainer.md`, `TODO.md`

## Safer parallel work

- Scientific experiment code unrelated to contracts
- Paper/PDF builders that do not rewrite E4/E5 public JSON
- App / coherence / site lanes
- Read-only audits

## Guardrails that still apply

- No GPU launches (E6/E5-L/E7/M5) as infrastructure side effects
- Do not infer claim status from manifest/evidence/gate pass-fail
- Do not regenerate E4/E5 public JSON without ignored raw sources
- Envelope sidecars bind to their own producer manifests, not the M5 card primary

## Sources

- Plan: `docs/next_agent_evidence_infrastructure_handoff_2026-07-14.md`
- Remaining-work note (execution state now stale): `docs/next_agent_evidence_infrastructure_remaining_handoff_2026-07-14.md`
- Live coordination table: `docs/next_agent_evidence_infra_coordination_2026-07-14.md`
