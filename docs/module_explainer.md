# Module Explainer & Package Catalog

Catalog of packages, modules, major scripts, test areas, and documentation in
**research-derived-experiments**. Companion: [system_design.md](system_design.md).
Update both when the codebase changes meaningfully (see root `AGENTS.md`).

---

## 1. Repo map (top level)

| Path | Responsibility |
|---|---|
| `experiments/` | 55 research packages plus `common/` shared analysis utilities; harnesses, Modal sweeps, committed `results/`, generated `PROVENANCE.md` |
| `papers/` | Paper sources (`paper.md`), figures, shareable PDFs |
| `scripts/` | 94 Python ops modules: quality, contracts, provenance, PDF/figure builders, summarizers |
| `tests/` | 89 root test files collected together by pytest (`unittest`-style and pytest-native) |
| `docs/` | Design docs, verification, handoffs, plans, reviews, solutions |
| `docs/primers/backlogs/` | Six article-specific, source-anchored research TODOs derived from the primer PDFs |
| `notes/` | Program-level research synthesis |
| `references/` | Public source list; local-only full texts (gitignored subdirs) |
| `formal/ontology-hs/` | Haskell typed ontology gate (Arc 2B) |
| `sites/` | Public static sites (atlas, Inquiry landing) |
| `apps/inquiry-black-box/` | Local-first Inquiry product monorepo (Bun/Electron/MV3) |
| `coherence-testbench/` | Separate EEG/eyetrack Phase-0 GO/KILL project |
| `data/` | Gitignored raw data; committed exception `data/paper_b/` |
| `artifacts/` | Gitignored raw run outputs (never commit) |
| `README.md` | Human entrypoint |
| `TODO.md` | Active research ledger |
| `AGENTS.md` | Agent/contributor rules (incl. doc sync) |
| `pyproject.toml` | Python ≥3.12 project metadata; locked root `quality` dependency group; explicit CPU-only PyTorch index; Ruff and ty configuration; experiment/Modal runtime dependencies remain call-site specific |
| `uv.lock` | Cross-platform lock for the root `quality` dependency group, including CPU-only Torch resolution |

---

## 2. Script / test / doc map (quick lookup)

### 2.1 “I want to…”

| Goal | Start here |
|---|---|
| Understand how the system runs | [system_design.md](system_design.md) |
| Find an experiment’s purpose & modules | §3 below + `experiments/<name>/PROVENANCE.md` |
| Reproduce or get the dispatch command | `python scripts/regen.py list` / `regen.py <name>` / `regen.py verify-clean-clone` |
| Refresh provenance index | `python scripts/gen_provenance.py` |
| Validate research contracts | `python3 scripts/validate_{evidence_registry,claim_registry,experiment_manifest,gate_verdict,public_artifact_envelopes}.py` (manifest validator also enforces `docs/experiment_contract_registry.json` coverage) |
| Run the quality gate | `python3 scripts/run_quality_checks.py` |
| Check API/Modal env without leaking secrets | `python3 scripts/env_probe.py` |
| Public agent benchmark package | [causally_grounded_agents_benchmark.md](causally_grounded_agents_benchmark.md) |
| Modal operator handoff | [next_agent_modal_handoff.md](next_agent_modal_handoff.md) |
| Deploy atlas / Inquiry site | [railway-autodeploy.md](railway-autodeploy.md) |
| Inquiry product work | `apps/inquiry-black-box/README.md` + `AGENTS.md` |
| Coherence Phase-0 | `coherence-testbench/README.md` + `POST_MORTEM.md` |

### 2.2 Tests by area (`tests/`)

| Test file(s) | Covers |
|---|---|
| `test_weakness_vs_simplicity.py` | Boolean weakness vs simplicity pilots |
| `test_symbolic_weakness.py`, `test_symbolic_families.py`, `test_symbolic_neural.py` | Flagship symbolic + neural weakness |
| `test_rotation_weakness.py` | Vision rotation weakness |
| `test_learned_symmetry.py`, `test_causal_validation.py` | Learned symmetry / causal validation |
| `test_concept_geometry_*.py` | Embedding concept geometry |
| `test_activation_geometry_*.py` (14 files) | Hidden-state probes, steering, patching, basins, gates |
| `test_concerned_syntax.py` | Arc 2A concerned-syntax suite |
| `test_viable_computational_bodies.py` | Arc 2B body search / gates |
| `test_long_horizon_bottleneck.py` | Suite D/E long-horizon / tool eval |
| `test_world_responds_suite_c*.py` (6 files) | Suite C reengagement + 2^3 component factorial + neural transfer + teacher-free |
| `test_structure_compatible_*.py` (4 files) | SCG suite, row ledgers, semantic selection |
| `test_gridcell_conference_evidence.py` | Paper A evidence export helpers |
| `test_paper_b_reproduce_stats.py` | Paper B CSV reproduction |
| `test_phase4_metaphysics.py`, `test_phase5_*.py`, `test_phase6_*.py` | Phase 4–6 harnesses |
| `test_gauge_fixed_concern_transport_*.py` | Gauge-fixed transport + PDF |
| `test_external_contact_p1_lora.py` | External-contact LoRA metrics |
| `test_commitment_surface_appendix.py` | Public-safe E4 appendix export, metric retention, raw-field omission |
| `test_commitment_surface_core.py`, `test_commitment_surface_e5.py`, `test_commitment_surface_e6.py`, `test_commitment_surface_e7.py` | Commitment-surface arithmetic; E5 split/leakage/coverage/novel-shift gates; E6 six-round rewards, coupled L4 strata, manifests, resume, and G1–G5 verdicts; and E7 padded-stream encoding, exact-mass subspaces, matched SHA-256 seeds, per-arm budget false-pass prevention, barrier failure handling, sequential exposure, and fail-closed G1–G4 analysis |
| `test_publication_guard.py` | Secret-signature detection and non-secret fixture naming |
| `test_semantic_concern_summary.py` | Semantic concern summarizer |
| `test_commitment_surface_core.py`, `test_e1_misspecification_variance.py` | E1 concern selectors plus conditional-randomization reconstruction, seed, assignment, and statistics contracts |
| `test_summarize_label_free_dose_response.py` | Label-free dose-response summarizer |
| `test_virtual_governor_stress_signal.py` | Virtual governor diagnostic |
| `test_mathematical_claims.py`, `test_bayesian_voi.py` | Executable theorem-assumption examples/failure cases and exact Bayesian VOI regimes |
| `test_seed_bootstrap_calibration.py` | Deterministic seed-floor grid, correct resampling unit, negative-regime retention, exact summary regeneration |
| `test_passive_active_phase_map.py` | Phase-map model comparison, matched-budget path controls, public aggregate contract |
| `test_grounded_statecharts.py` | Exact replay, depth 1–4 constraint lineage, six-surface fault attribution, descendant-aware memory causal use, legal lifecycle transitions, and byte-stable bundles |
| `test_grounded_live_evaluation.py`, `test_grounded_live_provider.py`, `test_grounded_statechart_pilot.py`, `test_grounded_condition_policy.py`, `test_grounded_chs_adjudication.py`, `test_grounded_public_dataset.py` | Shared live-eval schemas, fixture/live adapters, injectible provider transport, harness condition policies, paired-contrast CHS seals, public dataset export, ReplayEngine-backed artifact D2 mechanics, budgets/sanitization, and bootstrap stability |
| `test_causal_use.py` | Shared mass-normalized causal-use dose curves, bootstrap uncertainty, and cross-surface transport |
| `test_experiment_manifest.py`, `test_gate_verdict.py`, `test_evidence_registry.py`, `test_claim_registry.py` | Fail-closed research-contract adapters, package-coverage registry partition, discovery, references, supersession, and bidirectional edges |
| `test_research_contract_schema_parity.py`, `test_gen_provenance.py` | Shared vocabulary/schema parity, support-directory exclusion, non-mutating provenance freshness |
| `test_run_quality_checks.py` | Locked quality-command order, local serial default, bounded xdist worker parsing, `loadscope` scheduling, and native-thread caps |
| `test_build_primer_residuals_pdf.py` | Required six-article residual source sections plus reproducible ReportLab PDF build |
| `test_build_unified_review_superset_pdf.py` | Required four-part review synthesis, fatal-gate semantics, and deterministic ReportLab PDF build |

```bash
python3 scripts/run_quality_checks.py
# Optional local parity with CI's bounded parallel pytest path:
QUALITY_PYTEST_WORKERS=auto python3 scripts/run_quality_checks.py
```

The wrapper performs one
`uv sync --locked --only-group quality --python 3.12`, then runs pytest and
every downstream gate through `uv run --no-sync` in the same environment.
Local pytest is serial unless `QUALITY_PYTEST_WORKERS` is set to `auto` or an
integer from 1 through 4. CI sets `auto`; the wrapper respects usable CPU
affinity, caps the result at four workers, uses xdist `loadscope`, disables
worker restarts, and sets OMP, MKL, OpenBLAS, NumExpr, and vecLib thread counts
to one for the parallel pytest process. PyTorch resolves only from its explicit
CPU wheel index, avoiding CUDA, Triton, and NVIDIA packages on CPU runners.

Root-gate scope is unchanged: it covers `tests/` plus the Python compile,
publication, research-contract, primer-metadata, provenance, Ruff, and ty
checks below. Inquiry, `coherence-testbench`, Haskell/Cabal, and site-specific
suites retain their own workflows. Other documented `uvx` commands, including
Modal and standalone tool workflows, remain independent of this root quality
environment.

### 2.3 Docs inventory

| Doc / group | Role |
|---|---|
| [system_design.md](system_design.md) | End-to-end design & operating model |
| [module_explainer.md](module_explainer.md) | This catalog |
| [verification.md](verification.md) / `verification.json` | Provenance index (auto-generated from all 55 research packages; `experiments/common` excluded) |
| `experiment_contract_registry.json` | Authoritative 55-package coverage partition: 7 structured roots + 48 time-bounded legacy exceptions with frozen digest |
| `program_evidence_registry.json` | 12 canonical evidence records with stable IDs, states, artifact refs, and claim links |
| `claim_registry.json` | 12 canonical claim records with tiers, states, source refs, and bidirectional evidence links |
| [causally_grounded_agents_benchmark.md](causally_grounded_agents_benchmark.md) | Benchmark umbrella |
| [causally_grounded_agents_release_schema.md](causally_grounded_agents_release_schema.md) (+ `.json`) | Shared release schema |
| [causally_grounded_agents_next_gap.md](causally_grounded_agents_next_gap.md) | Suite C transfer gaps |
| [harness_research/README.md](harness_research/README.md) | Staged grounded-harness portfolio with deterministic replay, transport, counterfactual, and functional-unlearning fixtures |
| [next_agent_grounded_harness_experiments_handoff_2026-07-20.md](next_agent_grounded_harness_experiments_handoff_2026-07-20.md) | Post-fixture execution handoff: shared live-evaluation contract, ordered D2–D4 experiments, six safe parallel lanes, pilot gates, kill conditions, and release definition |
| `harness_research/grounded_statecharts.md` | Independent transition-guard design plus links to the implemented deterministic fixture runtime |
| `harness_research/constraint_transport.md` | Recursive constraint-envelope and externally enforced transition-guard benchmark design |
| `harness_research/counterfactual_harness_search.md` | Paired intervention, causal-credit, and equal-budget harness-search design |
| `harness_research/harness_unlearning.md` | Provenance-aware quarantine, commitment-level suppression, and revalidation design |
| [publication_sharing_map.md](publication_sharing_map.md) | What to share publicly |
| [paper_readiness.md](paper_readiness.md) | Paper readiness tracking |
| [discovery_regime_audit.md](discovery_regime_audit.md) | Regime audit ledger |
| [next_agent_modal_handoff.md](next_agent_modal_handoff.md) | Modal handoff |
| [next_agent_evidence_infra_peer_status_2026-07-15.md](next_agent_evidence_infra_peer_status_2026-07-15.md) | Post-tranche peer status after U2–U7 (#365–#371): counts, hot files, deferred Phase 5, safe parallel work |
| [next_agent_evidence_infra_coordination_2026-07-14.md](next_agent_evidence_infra_coordination_2026-07-14.md) | Live merge table for the six evidence-infra PRs |
| [next_agent_evidence_infrastructure_remaining_handoff_2026-07-14.md](next_agent_evidence_infrastructure_remaining_handoff_2026-07-14.md) | Historical six-PR landing plan (execution state superseded by peer-status doc after #371) |
| [railway-autodeploy.md](railway-autodeploy.md) | Railway deploy |
| [external_contact_preregistration.md](external_contact_preregistration.md) / [runbook](external_contact_runbook.md) | External-contact |
| [phase2_*.md](phase2_next_phase_research_handoff.md) | Phase 2 research handoffs (6 files) |
| [semantic_specificity.md](semantic_specificity.md) | Semantic specificity note |
| [neurophenom_project_approach_menu.md](neurophenom_project_approach_menu.md) | Neurophenom approach menu |
| [metaphysics_of_intelligence_reading_log.md](metaphysics_of_intelligence_reading_log.md) | Reading log |
| [gauge_fixed_concern_transport_experiment_audit.md](gauge_fixed_concern_transport_experiment_audit.md) | GFC audit |
| [metaphysics_complete_reading_notes_2026_07_09.md](metaphysics_complete_reading_notes_2026_07_09.md) | Full reading notes for every Metaphysics-of-Intelligence PDF/package listed 2026-07-09 (theorems, methods, findings, next directions); canonical copy also at `~/Metaphysics of Intelligence/COMPLETE_READING_NOTES_2026_07_09.md` |
| [primers/backlogs/README.md](primers/backlogs/README.md) | Six per-primer criticism-to-TODO backlogs (268 gated items) |
| [primers/primer_residuals_2026_07_14.md](primers/primer_residuals_2026_07_14.md) | Residual-only post-merge reconciliation, six article registers, and deduplicated execution waves; rendered at `output/pdf/primer_derived_research_residuals_2026_07_14.pdf` |
| `docs/plans/` | 13 dated implementation plans — §8.1 |
| `docs/paper_reviews/` | 15 critical reviews — §8.2 |
| `docs/solutions/` | Architecture-pattern notes — §8.3 |

---

## 3. Experiment catalog

**Legend:** **P** = `PROVENANCE.md`, **B** = `BENCHMARK_CARD.md`, **R** = `README.md`, **res** = committed `results/`.

**Verification reconciliation:** 55 research packages on disk plus one shared
support package, `experiments/common`. `gen_provenance.py` intentionally excludes
the support package and derives 55 cards/index rows; `gen_provenance.py --check`
fails if any generated card, either verification index, or the site mirror drifts.
The structured registries currently contain 12 claims and 12 evidence records.

Universal dispatcher: `python scripts/regen.py <name>`.

### 3.1 Weakness / geometry / structure

| Package | Artifacts | Purpose | Modules / entrypoints |
|---|---|---|---|
| `weakness_vs_simplicity` | P R res | Toy Boolean worlds: weakness vs simplicity under memorizer / broad-negative stress | `experiment.py` |
| `symbolic_weakness` | P R res | Flagship: symmetry-compatible weakness beats loss/MDL/flatness for OOD | See §3.1.1 |
| `rotation_weakness` | P res | Vision rotation-group weakness correlation | `neural.py`, `dataset.py` |
| `learned_symmetry` | P res | Data-inferred equivariance predicts OOD without oracle symmetry | `sweep.py`, `causal_validation.py`, `transform_generator.py`, `modal_sweep.py`, `modal_causal_validation.py` |
| `neural_group_generator` | P res | Failed neural group-discovery (pixels vs embeddings) | `generator.py`, `encoder_invariance.py`, `modal_rotated_mnist.py`, `modal_cluttered_mnist.py` |
| `grid_cell_weakness` | P R res | Path-integration RNNs: torus + OOD + reward deformation (Papers A/B) | See §3.1.2 |
| `semantic_concern_geometry` | P R res | Moving semantic loss weights deforms geometry (pooled gate FAIL) | `modal_semantic_concern_sweep.py` |
| `structure_compatible_generalization` | custom P R res | Compatibility with deployment transforms for OOD model selection | See §3.1.3 |
| `weakness_temporal` | P | Early-checkpoint weakness as temporal OOD early-warning | `temporal.py` |
| `paraphrase_weakness` | P R res | Paraphrase-invariance of hidden states vs behavior | `modal_paraphrase_probe.py`, `modal_learned_substitution.py`, `summarize.py` |
| `concept_geometry` | P R res | Cross-domain concepts in embedding space | `openai_embedding_probe.py`, `paraphrase_stability_probe.py` |
| `activation_geometry` | P R res (58) | Hidden-state bridges, steering, patching, label-free gates | See §3.1.4 |
| `passive_to_active` | P R res | Action coupling makes paraphrase geometry causally load-bearing | `modal_passive_to_active.py`, `modal_replication_sweep.py` |
| `passive_active_phase_map` | P R res | Registered local coupling sweep: bifurcation not supported; controlled path dependence passed | `core.py`, `preregistration.md`, `experiment_manifest.json` |
| `commitment_surface` | P R res | Commitment-first reframe: severe tests E1–E4 discriminating compatibility-augmented training + patch-CE against weakness readout on both synthetic MLP modular addition and external Pythia LoRA | See §3.1.5 |

#### 3.1.1 `symbolic_weakness` modules

| Module | Purpose |
|---|---|
| `families.py` | Task families (cyclic, dihedral, parity, …) with OOD orbits |
| `selectors.py` | Hypothesis selectors (loss, MDL, flatness, weakness_oracle, …) |
| `benchmark.py` | Multi-family symbolic benchmark CLI |
| `experiment.py` | Symbolic symmetry/weakness benchmark (cyclic tasks) |
| `neural.py` | Neural MLP cyclic-prefix-shift weakness correlation |
| `modal_neural_sweep.py` | Large-scale Modal neural sweep |
| `summarize_neural_sweep.py` | Publishable summary from sweep JSON |

```bash
python3 -m experiments.symbolic_weakness.benchmark --trials-per-family 500 --seed 20260609
```

#### 3.1.2 `grid_cell_weakness` modules

| Module | Purpose |
|---|---|
| `core.py` | Paper A harness: path-integration RNN, topology + weakness metrics |
| `pilot.py` | Cheap metric-discrimination pilot on synthetic manifolds |
| `run_local.py` | Local CPU multi-seed sweep |
| `reward_deformation.py` | Paper B: does injected reward deform representational metric |
| `ratedistortion_test.py` | Rate–distortion exponent test |
| `capacity_bottleneck.py` | Capacity-bottlenecked reward-deformation law test |
| `dump_fields.py` / `dump_manifold.py` | Visualization dumps |
| `modal_grid_cell_weakness_sweep.py` | Modal Paper A |
| `modal_reward_deformation_sweep.py` | Modal Paper B deformation |
| `modal_reward_location_sweep.py` | Modal moved-reward location sweep |

Local regen: `python scripts/regen.py grid_cell_weakness`.

#### 3.1.3 `structure_compatible_generalization` modules

| Module | Purpose |
|---|---|
| `core.py` | `DiagnosticRow` schema + compatibility summaries |
| `modular_domain.py` | Finite modular-addition domain with translation OOD |
| `run_suite.py` | Importable suite runner (Modal-first) |
| `transformation_discovery.py` | Finite transformation-family discovery from train pairs |
| `phase3_learned_generators.py` | Learned affine/rotation generators |
| `template_language_domain.py` | Rendered template-language substitution domain |
| `semantic_retrieval_transfer.py` | Frozen-encoder semantic retrieval + paraphrase orbits |
| `semantic_selection_control.py` | OOD-free semantic model selection |
| `semantic_selection_bootstrap.py` / `semantic_selection_tiebreak_stress.py` | Bootstrap / tie-break stress |
| `modal_l4_suite.py` | Primary Modal L4 suite |
| `modal_phase2_transformations.py` | Phase 2 Modal |
| `modal_phase3_learned_generators.py` | Phase 3 Modal |
| `modal_language_template_substitution.py` | Language-template Modal |
| `modal_semantic_retrieval_transfer.py` / `modal_semantic_selection_control.py` | Semantic Modals |
| `summarize_*.py` / `publish_*.py` | Summaries and row-ledger publishers |

#### 3.1.4 `activation_geometry` modules (by concern)

| Concern | Local helpers | Modal entrypoints |
|---|---|---|
| Core probing / layers | `activation_geometry_probe.py` | `modal_activation_probe.py`, `modal_layer_sweep.py` |
| Final-token steering | `final_token_steering_pilot.py`, `steering_calibration_diagnostic.py`, `steering_gradient_alignment.py` | `modal_final_token_steering.py`, `modal_steering_calibration.py`, `modal_steering_gradient_alignment.py` |
| Causal patching | `causal_patching_diagnostic.py`, `matched_context_patching.py`, `matched_context_replication.py` | `modal_causal_patching.py`, `modal_matched_context_patching.py` |
| Label-free behavior gates | `label_free_behavior_gate.py` | `modal_label_free_behavior_gate.py` |
| Label-free readout basins | `label_free_readout_basin.py` | `modal_label_free_readout_basin.py` |
| Behavior-aligned directions | `behavior_aligned_direction.py` | `modal_behavior_aligned_direction.py`, `modal_behavior_direction_subspace.py` |
| Attractor / answer basins | `attractor_pocket_diagnostic.py`, `answer_surface_basin_diagnostic.py` | `modal_attractor_pocket_diagnostic.py`, `modal_answer_surface_basin.py` |
| Held-out / pair controls | `heldout_readout_pilot.py`, `pair_control_diagnostic.py` | (summarized from Modal payloads) |

#### 3.1.5 `commitment_surface` modules

Severe tests for the commitment-first reframe. See
[`papers/commitment_surface/paper.md`](../papers/commitment_surface/paper.md)
for the theory (Props 1+2, corollary, M4 anti-Goodhart loop) and
[`papers/commitment_surface/PLAN.md`](../papers/commitment_surface/PLAN.md)
for the frozen original pre-registration. The E1 variance follow-up is frozen
separately in
[`e1_misspecification_variance_preregistration_2026-07-09.md`](../papers/commitment_surface/e1_misspecification_variance_preregistration_2026-07-09.md).

The corrected formal surface treats Proposition 1 as non-identification,
requires deployment-restricted weakness (or an ordering-preservation
assumption) in Proposition 2, and uses finite-candidate order equivalence for
concern weighting. E4 is a directional result with a strict gate failure; its
labeled-orbit-coverage confound and timestamped post-hoc E5 severe follow-up
are recorded in paper §6.6 and PLAN.md. The exact E5 grid passed integrity and
returned strict verdict `coverage` (Cov/B-ref 0.741/0.741 canonical OOD versus
G-reg/A-ref 0.063/0.069); generator, group-specificity, and transport gates
failed. Grid completeness is part of `confirmatory_ready`, not inferred from
per-arm counts.
The later E7 CPU follow-up transports #344's normalized compatibility subspace
into continual learning, but its post-run timing re-audit fails 6/32 matched
groups. The run is integrity-invalid, so the apparent mechanism/behavior
separation is diagnostic only and paper §6.4 withholds a scientific verdict.

| Module | Purpose |
|---|---|
| `core.py` | Stdlib primitives: concern deployments (uniform / unequal / misspec), weighted extension mass, candidate hypothesis families (shifts, random train-perfect completions, biased-to-focus), selectors, `run_e1_cell` |
| `run_e1.py` | E1 CPU sweep entrypoint (unequal-consequence selector comparison) |
| `e1_misspecification_variance.py` | Stdlib CPU conditional-randomization harness: freezes 96 E1 structures, redraws 2,048 independent marginal-preserving assignments, estimates gap distribution/tail probability, and gates exchangeability assumptions |
| `e2_e3_neural_sweep.py` | E2/E3 four-arm neural MLP sweep on cyclic modular addition; preserves fixed-top-k patching and adds spectral-mass-normalized compatibility/wrong-subspace projection for width-comparable causal localization |
| `modal_e4_pythia_lora_v2.py` | E4 Modal L4 external contact: four arms A (readout) / B (cyclic-orbit augmentation) / C (wrong-group aug) / D (loss selector) on Pythia 70m/160m/410m LoRA modular addition; adapter-disable patch-CE |
| `e5_core.py` | E5 typed configs, disjoint support/intervention splits, supervised-vs-consistency exposure plans, G/W schedule matching, leakage/coverage audits, deterministic launch manifests, exact Cartesian-grid and metric-range audits, and frozen smoke/confirmatory analysis gates |
| `e5_requirements.txt` | Fully pinned 43-package Linux/Python runtime lock for the E5 training and CPU preflight image; included in the implementation fingerprint and manifest environment |
| `modal_e5_generator_vs_coverage.py` | E5 Modal Pythia-LoRA five-arm runner: explicit smoke/development/confirmatory regimes and dry-run/inspect/execute actions; hard-locked confirmatory config and pinned runtime/model revisions; CPU image/Volume preflight, status scan, and model prefetch; bounded, leased, partial-failure-safe, resumable, longest-first per-cell L4 submission observed by one detached remote orchestrator and checkpointed through a V2 result Volume; fresh workers consume the committed prefetch snapshot without an unsafe concurrent cache reload; train-support-only correct/wrong generator consistency, weighted pair-microbatch backpropagation for 410m/L4 memory safety, orbit and coverage references, novel-shift/paraphrase transport, exposure ledgers, and spectral-mass-normalized LoRA patching |
| `e6_core.py` | E6 dependency-free protocol scaffold: frozen six-round SC/CS/GT/A-ref reward selection; reward-neutral candidates and truth-label-free typed CS patch signals; strict transport eligibility; matched pool digests and candidate/selection counts; and namespaced SHA-256 seeds |
| `e6_analysis.py` | E6 manifest and analysis scaffold: exact 108-cell confirmatory manifests; strict frozen-config, metric-range, top-half selection-volume, trajectory/resume, integrity, and matched-pool audits; and frozen G1–G5 aggregate verdicts |
| `e6_runtime.py` | Pure E6 execution planner: frozen paired-half current-adapter proposer, candidate support, coupled arm-cell strata, run-kind arm validation, L4 resource constants, launch ordering, and lease validation |
| `e6_training.py` | E6 GPU stratum implementation: shared E5-matched bootstrap, symmetric current-SC/current-CS generation, typed reward scoring, strict transport eligibility, matched pseudo-label fine-tuning, per-round patch/equivariance/coverage measurements, and integrity-rich cell payloads |
| `e6_requirements.txt` | Fully pinned 43-package E6 Linux/Python runtime lock used by CPU preflight and L4 training images and included in the implementation fingerprint |
| `modal_e6_commitment_reward.py` | Guarded E6 Modal runner: exact dry-run/inspect/execute actions, immutable Pythia revisions, CPU image/Volume preflight, separate result Volume and fail-closed stratum leases, exact returned-cell validation, bounded checkpointed L4 dispatch, resumable per-arm cells, nonzero exit on worker or selected-checkpoint failures, and confirmatory manifest acknowledgement |
| `e7_selective_subspace.py` | E7 CPU continual-learning runner: fixed padded 29-class depth-2 MLP over moduli 17/19/23/29; cyclic compatibility augmentation; naive/EWC/compatibility-subspace/wrong-subspace arms; replay-free Fisher and projected-parameter anchors; exact 50% boundary-weighted protection; full-rank #344 patch metrics; matched namespaced seeds; fail-closed per-arm median-step budget auditing with barrier-abort safety; exact pilot receipt lock; public-safe aggregation; and frozen G1–G4 analysis only for four-seed-valid widths |
| `results/e1_concern_weighted.{json,md}` | E1 summary + per-cell provenance |
| `results/e1_misspecification_variance.{json,md}` | E1 follow-up aggregate draws, quantiles/CI, assumption audit, and randomization verdict |
| `results/e2_e3_neural.{json,md}` | E2/E3 summary + per-cell provenance |
| `results/e2_e3_rank_patch_width{96,128}.{json,md}` | Rank-normalized E2/E3 per-cell sweeps across n=17/19/23 |
| `results/e2_e3_rank_normalized_patch_2026_07_10.{json,md}` | Frozen-gate aggregate: strict PASS, 77.5% width retention, group-specific subspace effect |
| `results/e5_smoke_summary.md` | Public-safe one-seed harness-validation report; integrity pass, explicitly non-confirmatory |
| `results/e5_launch_readiness_2026_07_10.md` | Operational no-compute audit: exact 135-cell manifest, dispatch/checkpoint design, resource formula, and development timing-calibration boundary; no scientific result |
| `results/e5_generator_vs_coverage.{json,md}` | Generated public-safe confirmatory artifact: exact-grid audit, frozen mechanism verdict, per-arm means, and compact metrics for all 135 cells |
| `results/e6_smoke_readiness_2026_07_13.md`, `results/e6_smoke_readiness.json` | Public-safe negative L4 readiness record: pinned preflight pass, round-1 CS eligibility 8/104 versus 52 required, no completed trajectory, and development/confirmatory dispatch withheld |
| `results/e7_selective_subspace_2026_07_13.{json,md}` | E7 public-safe 32-stream/128-checkpoint integrity report: seed/sequential/mass checks pass, but 6/32 matched groups exceed the 2% timing limit (max 8.53%); run INVALID, G1–G4 withheld, no scientific verdict |
| `results/m4_suite_c_factorial_ablation_2026_07_09.{json,md}` | M4 public-safe factorial summary: strict FAIL; reopen necessary, allocate/cool terminal-null |

Run:

```bash
python3 -m experiments.commitment_surface.run_e1
python3 -m experiments.commitment_surface.e1_misspecification_variance
python3 -m experiments.commitment_surface.e2_e3_neural_sweep
python3 -m unittest tests.test_commitment_surface_e6
python3 -m unittest tests.test_commitment_surface_e7
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
        experiments/commitment_surface/modal_e4_pythia_lora_v2.py \
        --sizes 70m,160m,410m --ns 13,17,23 --seeds 3 --arms A,B,C,D
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal==1.2.6 modal run \
        experiments/commitment_surface/modal_e5_generator_vs_coverage.py \
        --sizes 70m --ns 13 --seeds 1 --arms G-reg,Cov,A-ref --epochs 20 \
        --run-kind smoke --execute --max-gpu-cells 3 \
        --out artifacts/commitment_surface/e5_smoke.json
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal==1.2.6 modal run \
        experiments/commitment_surface/modal_e6_commitment_reward.py \
        --sizes 70m,160m,410m --ns 13,17,23 --seed-slots 1 \
        --arms SC,CS,GT,A-ref --run-kind development --dry-run \
        --out artifacts/commitment_surface/e6_development.json
```

Use `--run-kind confirmatory --dry-run` with the exact full-grid command in the
experiment README to validate all 135 cells without GPU work, and `--inspect`
to report checkpoints and leases without dispatch. Only explicit `--execute`
with the expected manifest ID and a sufficient `--max-gpu-cells` authorization
can produce a confirmatory verdict.
E6 follows the same action discipline but counts coupled GPU strata in
`--max-gpu-cells`; its current smoke is readiness-blocked, so further execution
requires a newly frozen design rather than replaying the failed objective.

Rebuild the paper PDF:

```bash
python3 scripts/make_commitment_surface_figures.py
python3 scripts/build_commitment_surface_pdf.py
```

### 3.2 Arc 2A / 2B (deep)

#### 3.2.1 `concerned_syntax` — variant ladder

**Artifacts:** P · R · res (30) · paper *Constituency Tests for Concerned Representation in Minimal Agents*.

| Module | What it tests |
|---|---|
| `benchmark.py` | Symbolic Arc 2A baseline: six-part shape, hidden parse trees, concern-gated costly probes |
| `learned_agents.py` | Learned intervention + parse inference with **visible** candidate-parse hypotheses |
| `vector_shapes.py` | Removes visible parses; six-part **vector** surface invariant to true parse |
| `pixel_shapes.py` | RGB render; CC extractor → object features |
| `intervention_invention.py` | Agent must learn **when** and **which pair** to probe |
| `intervention_transfer_repair.py` | Held-out role transfer repair (role-equivariant decode) |
| `rich_program_language.py` | **2A-v2**: richer finite intervention-program language |
| `rich_program_transfer_repair.py` | Held-out role/parse transfer repair for v2 |
| `learned_pixel_extractor.py` | Replaces algorithmic CC with learned foreground + slot centers |
| `learned_slot_semantics.py` | Supervised learned role-slot classifier |
| `unsupervised_slot_semantics.py` | Label-free appearance clustering + rich-program grounding |
| `discovered_semantic_profiles.py` | Induces semantic profile table from anonymous intervention traces |
| `learned_object_slots.py` | Learned foreground slots + discovered profiles on held-out transfer |
| `searched_program_policy.py` | Bounded recipe search over v1 program menu |
| `searched_rich_program_policy.py` | Recipe search over v2 rich-program primitives |
| `mechanism_trace.py` | Trajectory audit: state → program → obs → belief → action |
| `modal_report.py` | Summarize Modal JSON → tracked markdown |
| `modal_*_sweep.py` (×17) | Thin Modal wrappers for each local module |

```bash
python3 -m experiments.concerned_syntax.benchmark --trials 200 --seed 20260616 \
  --out artifacts/concerned_syntax/pilot.json \
  --report experiments/concerned_syntax/results/pilot_2026_06_16.md
```

#### 3.2.2 `viable_computational_bodies` — all modules

**Artifacts:** P · R · res (14) · paper *Viability-Guided Evolution of Syntax-Bearing Computational Bodies*.

| Module | Purpose |
|---|---|
| `search.py` | Arc 2B symbolic typed-architecture grammar + viability/anti-cheat gates |
| `program_body_search.py` | Search motif bodies against frozen **2A-v1 invention** contract |
| `rich_program_body_search.py` | Bodies against **2A-v2 rich-program** contract |
| `learned_executable_modules.py` | Executable module bodies vs held-out v2 transfer |
| `searched_executable_modules.py` | Mutate/search executable module sets vs label-free slot-semantics gate |
| `object_slot_executable_modules.py` | Bodies vs learned-object-slot + discovered-profile path |
| `haskell_gate.py` | Python bridge to `formal/ontology-hs` |
| `modal_body_evolution_sweep.py` | Modal for symbolic `search.py` |
| `modal_program_body_search.py` | Modal v1 program-body search |
| `modal_rich_program_body_search.py` | Modal v2 rich-program body search |
| `modal_learned_executable_modules.py` | Modal executable-module gate |
| `modal_searched_executable_modules.py` | Modal searched executable bodies |
| `modal_object_slot_executable_modules.py` | Modal object-slot executable search |
| `modal_report.py` | Summarize Modal Arc 2B sweeps |

```bash
python3 -m experiments.viable_computational_bodies.search \
  --seeds 12 --generations 18 --population 18 --base-seed 20260616
```

### 3.3 Causally grounded agents / long horizon

#### 3.3.1 `world_responds` — Suite C

**Artifacts:** P · **B** · res · paper *When the World Responds…*.

| Module | Purpose |
|---|---|
| `modal_world_responds_sweep.py` | Paper 22: action-correlated shocks + regime shift |
| `suite_c_contract.py` | Shared Suite C condition constants |
| `suite_c_reengagement.py` | Deterministic Suite C re-engagement (silence/anxiety/false-calm/cost), with typed allocate/cool/reopen action-gate interventions that default to the unchanged policy and an opt-in probe trace used to freeze M5 budgets |
| `suite_c_factorial_ablation.py` | Local deterministic 2^3 allocate × cool × reopen runner using the real burst/refractory workflow; paired bootstrap contrasts, transported controls, strict gates, idempotent raw/public artifacts |
| `suite_c_factorial_ablation_preregistration_2026_07_09.md` | Timestamped follow-up addendum frozen before implementation/run; exact component semantics, seeds, gates, kill criteria, rejected alternatives |
| `suite_c_reopen_reset_trigger.py` | M5 CPU runner comparing commitment, utility/age, robust-normalized, periodic, and never-reopen triggers over a common exact M4 probe plan; hash-pinned M4-only calibration, frozen eight-seed integrity, coupled no-change occupancy, paired bootstrap summaries, strict F0–F5 gates, and idempotent raw/public artifacts |
| `suite_c_reopen_reset_trigger_preregistration_2026-07-13.md` / `suite_c_reopen_reset_trigger_implementation_contract_2026-07-14.md` | Frozen M5 question/gates plus the timestamped pre-outcome repair that operationalizes missing trigger, budget-routing, latency, and false-calm details |
| `suite_c_reopen_reset_trigger_calibration_2026_07_14.json` | Outcome-blind pre-first-shift M4 calibration receipt binding the two internal-trigger thresholds before M5 cells |
| `suite_c_reopen_reset_trigger_integrity_manifest_2026_07_14.json` | Post-audit frozen digest manifest binding the corrected M5 rows, exact per-seed M4 plans/budgets, transported reference suite, config, seeds, and calibration receipt after invalidating branch-desynchronized precursor payloads; schedules/reference use a declared 12-decimal semantic digest for macOS/Linux stability while the final-row digest remains exact |
| `modal_suite_c_reengagement.py` | Modal Suite C dispatch |
| `suite_c_neural_transfer.py` | Learned probe-head transfer on held-out seeds |
| `modal_suite_c_neural_transfer.py` | Modal neural-transfer sweep |
| `suite_c_teacher_free.py` | CEM teacher-free adaptive inquiry |
| `suite_c_teacher_free_wide_stats.py` | Wide-stats aggregation |
| `suite_c_source_ablation_transfer.py` | Source ablation transfer |
| `summarize_suite_c.py` / `summarize_suite_c_neural_transfer.py` / `summarize_suite_c_teacher_free.py` | Summaries |
| `validate_suite_c_neural_transfer_release.py` | Release validation |

#### 3.3.2 `long_horizon_bottleneck` — Suite D/E

**Artifacts:** P · **B** · R · res (24) · paper *Future Control Moves Memory…*.

| Module | Purpose |
|---|---|
| `core.py` | Shared manifest, budget guard, gate summaries |
| `eval.py` | CLI evaluator / benchmark driver |
| `prompt_json_tasks.py` | Prompt-JSON action helpers for open-model sweeps |
| `api_blackbox.py` / `api_blackbox_report.py` | Multi-provider API black-box cases + reports |
| `api_dispatch_characterization.py` | Provider dispatch characterization |
| `modal_moved_bottleneck_sweep.py` | Core moved-bottleneck memory diagnostic |
| `modal_tool_commitment_sweep.py` | Tool-slot commit + closed-loop return |
| `modal_tool_recovery_sweep.py` | Recovery after commitment |
| `modal_structured_tool_call_sweep.py` | Structured tool-call surface |
| `modal_multifield_tool_schema_sweep.py` | Multi-field schema |
| `modal_stochastic_tool_failure_sweep.py` | Stochastic tool failure |
| `modal_prompt_json_transfer_sweep.py` | Prompted open-model JSON transfer |
| `modal_prompt_json_hidden_localization_sweep.py` | Hidden-state localization |
| `modal_prompt_json_causal_patch_sweep.py` | Causal patch on prompt-JSON regime |
| `modal_api_dispatch_robustness_sweep.py` | API dispatch robustness |

```bash
python3 -m experiments.long_horizon_bottleneck.eval --provider fixture --models fixture ...
```

#### 3.3.3 `grounded_statecharts` — shared grounded-harness bedrock

**Artifacts:** P · R · res · typed replay, delegation, intervention, and memory-ledger bundles.

| Module / artifact | Purpose |
|---|---|
| `runtime.py` | Minimal Observe/Act/Verify/Commit/Repair interpreter, typed events, serializable checkpoint, and single-component replay enforcement |
| `run_fixture.py` | One-command deterministic fixture runner and static HTML replay generator |
| `constraint_transport.py` | Versioned constraint envelopes, hash-linked derivation, capability narrowing, tamper rejection, and deterministic depth 1–4 evaluator |
| `run_constraint_transport.py` | Two-family benchmark runner, joint-success scorer, known-fault export, and compact static replay |
| `constraint_pilot.py` / `run_constraint_pilot_smoke.py` | Credential-free D2 bridge that maps the committed prose/no-guard and typed/guarded diagonal into compact rows while explicitly marking the two crossed factorial cells unobserved |
| `counterfactual_search.py` | Six-surface fault manifests, deterministic outcome vectors, isolated repair/placebo replay, attribution credit, and equal-budget trace baseline |
| `run_counterfactual_search.py` | Pilot runner, fault-integrity gates, attribution/repair metrics, and compact static replay |
| `chs_sealed.py` / `run_chs_sealed_smoke.py` | Credential-free synthetic-to-sealed-label plumbing for one clean and six single-fault cases, scored against a separate label artifact |
| `chs_repair_search.py` / `run_chs_repair_search.py` | Re-runs the equal-budget (identical per-arm cost) counterfactual repair/placebo search fresh and scores it against both the adjudicated injected-fault seal tier (`results/chs_injected_faults/labels.jsonl`) and the hand-authored fixture label file (`fixtures/chs_sealed_labels.json`); gates on zero placebo credit, exact budget parity, and cross-source label agreement; writes `results/chs_repair_search/`; explicitly not CHS1 on naturalistic live failures |
| `harness_unlearning.py` | Scoped memory ledger, descendant families, commitment harness, paired causal-use gate, and legal lifecycle transitions |
| `run_harness_unlearning.py` | Fail-closed causal prerequisite plus deterministic shift, quarantine, retirement, recurrence, restoration, and replay bundle |
| `unlearning_multishift.py` / `run_unlearning_multishift_smoke.py` | Credential-free draft extension with nine independently authored shift instances (distinct memory ids, content actions, and regime ids) across three families — three tool-schema variants, three environment-policy variants, three model/version-identical-semantics false-forgetting-control variants; writes compact summary/rows only, no live calls |
| `run_unlearning_multishift_live_smoke.py` | Opt-in credentialed live-adapter mechanics smoke for a name-free memory-sensitivity probe shape (observed/target-suppressed/placebo-suppressed prompt conditions) over 3 of the 9 draft cases; validates prompt/parse/budget plumbing, derives a prompt-level causal-use-shaped signal (`evaluate_kill_criteria`), and applies two explicit live kill criteria — an identical-semantics case must never look quarantine-worthy, and a quarantine-worthy pattern must never fire without the target-specific/placebo-unaffected contrast; writes under gitignored `artifacts/`, and is explicitly not a HU1–HU7 result |
| `constraint_ood.py` / `run_constraint_ood_smoke.py` | Runs two Constraint Transport OOD probes for real, credential-free: a held-out paraphrase of 4 `recursive_constrained_tool_use` D2 tasks through the real `condition_policy`-enforced harness (fixture adapter; `envelope_only` vs `envelope_external_guards`), and a deterministic depth-5/6 extension of the typed/lossy transport benchmark beyond the committed depth-1..4 ceiling; the fixture-adapter paraphrase slice is mechanics-only (FixtureExecutor never reads instruction text) |
| `run_constraint_ood_live_smoke.py` | Opt-in credentialed rerun of the held-out paraphrase probe against a live, name-free provider (rejects `GROUNDED_HARNESS_LABELED_PROMPT=1`); reports the joint_success paired effect for `envelope_external_guards` vs `envelope_only` against a 0.15 kill threshold and records a collapse honestly instead of reinterpreting it; writes only under gitignored `artifacts/` |
| `adapters/` | Provider-neutral executor boundary; deterministic `fixture` adapter plus opt-in OpenAI/Anthropic `live` backend |
| `budgets.py` | Matched call/token/tool/latency/cost ceilings with fail-closed planning receipts |
| `sanitization.py` | Fail-closed public-row projection that blocks raw provider material |
| `evaluation.py` | Normalized live task/episode/result records, smoke matrix, integrity receipts, and task-clustered bootstrap |
| `condition_policy.py` | Harness-enforced condition policies: G3 artifact repair, external envelope capability narrowing, evidence-based scoring |
| `chs_adjudication.py` / `run_chs_adjudication.py` | Two independent seal tiers: paired-contrast live seals (orchestration/output only, real D2 rows) writing labels under `artifacts/` never into episode rows, plus `seal_from_injected_faults`/`generate_injected_results` (six-surface, constructed single-fault fixtures reusing `counterfactual_search.py`'s search) writing public-safe labels under `results/chs_injected_faults/`; `summarize_combined_coverage` / `--with-injected` report both tiers without claiming six-surface CHS1 |
| `run_chs_injected_faults_smoke.py` | Credential-free entrypoint for the injected-fault seal tier under `results/chs_injected_faults/` |
| `publish_public_dataset.py` | Fail-closed sanitized public D2 dataset exporter with checksums and claim boundary |
| `d2_tasks.py` / `fixtures/d2_held_out_tasks.json` | Frozen 24-task D2 bank (12 fresh-verification artifact tasks + 12 constrained-delegation tasks), closed-schema/`LiveTask` loader, and task-digest validation; no answer keys or hidden labels |
| `run_live_smoke.py` | Clean-clone-safe smoke bundle under `results/live_evaluation/` |
| `run_live_credentialed_smoke.py` / `modal_live_credentialed_smoke.py` | Opt-in credentialed mechanics smoke writing only under gitignored `artifacts/`; smoke rows discarded from held-out D2 |
| `d2_tasks.py` / `run_d2_pilot.py` | Frozen held-out D2 task bank loader and fixture/live matrix runner (family/condition filters; `--confirmatory`) |
| `manifests/d3_ct_confirmatory/experiment_manifest.json` | Frozen CT-primary D3 confirmatory contract under harness-enforced name-free prompts |
| `run_weak_prompt_ablation.py` / `live_ablation.py` | Name-free default prompt contract and sensitivity path; labeled prompts are diagnostic-only |
| `live_replay.py` / `chs_from_live.py` | Artifact-first live failure replay and heuristic CHS candidate harvest from sanitized rows |
| `manifests/d2_pilot/experiment_manifest.json` | Planned two-family D2 pilot contract (status=`planned` until held-out freeze) |
| `statechart_pilot.py` / `run_statechart_pilot_smoke.py` | D2 mechanics bridge: ReplayEngine-backed artifact G0/G3 and wrong-edge conditions, fixture-executor constraint delegation, matched-budget public rows, and non-held-out smoke entrypoint |
| `replay_viewer.py` / `run_unified_replay.py` | Fixture-only public failure replay renderer and runner under `results/unified_replay/`, with observations, intervention, causal-credit scope, uncertainty, cost, and claim boundary separated |
| `live_replay.py` / `run_live_failure_replay.py` | Selects one matched authentic live failure/contrast pair and renders a metadata-only replay under `artifacts/`; explicit public mode fails closed unless every source row already matches the sanitized public schema |
| `chs_from_live.py` / `run_chs_from_live_smoke.py` | Converts sanitized live-row outcome patterns into an artifact-only, unsealed heuristic component-candidate ledger for later independent adjudication; it does not score CHS |
| `STATECHART_D2_PREREGISTRATION.md` | Draft/mechanics-only two-family D2 gate, controls, matched ceilings, kill criteria, and held-out claim boundary |
| `CONSTRAINT_TRANSPORT_D2_PREREGISTRATION.md` / `CHS_SEALED_PREREGISTRATION.md` | Draft bridge assumptions, discriminating tests, kill criteria, and strict non-publishable claim boundaries |
| `UNLEARNING_MULTISHIFT_PREREGISTRATION.md` | Draft three-family semantic-shift assumptions, causal-use prerequisite, identical-semantics control, kill criteria, and claim boundary |
| `manifests/*.json` | Matched G0 self-report and G3 artifact-digest harness conditions; only `guard` differs |
| `manifests/constraint_transport/experiment_manifest.json` | Separate structured run contract for the deterministic transport diagnostic |
| `fixtures/*.json` | Registered replay/transport/fault cases, a versioned memory shift/recurrence episode, and the held-out D2 task bank |
| `schemas/*.json` | Public event, constraint-envelope, and live task/episode/intervention/result contracts |
| `results/` | Replay, transport, attribution, functional-memory, and live-smoke summaries with row-level evidence |

```bash
python3 -m experiments.grounded_statecharts.run_fixture
python3 -m experiments.grounded_statecharts.run_constraint_transport
python3 -m experiments.grounded_statecharts.run_counterfactual_search
python3 -m experiments.grounded_statecharts.run_harness_unlearning
python3 -m experiments.grounded_statecharts.run_live_smoke
python3 -m experiments.grounded_statecharts.run_unified_replay
python3 -m experiments.grounded_statecharts.run_statechart_pilot_smoke
python3 -m experiments.grounded_statecharts.run_constraint_pilot_smoke
python3 -m experiments.grounded_statecharts.run_chs_sealed_smoke
python3 -m experiments.grounded_statecharts.run_chs_injected_faults_smoke
python3 -m experiments.grounded_statecharts.run_chs_repair_search
python3 -m experiments.grounded_statecharts.run_unlearning_multishift_smoke
# Opt-in credentialed HU live-adapter smoke (writes under artifacts/ only):
# GROUNDED_HARNESS_LIVE=1 GROUNDED_HARNESS_PROVIDER=... GROUNDED_HARNESS_MODEL=... \
#   python3 -m experiments.grounded_statecharts.run_unlearning_multishift_live_smoke
python3 -m experiments.grounded_statecharts.run_constraint_ood_smoke
# Opt-in credentialed CT OOD held-out-paraphrase smoke (writes under artifacts/ only):
# GROUNDED_HARNESS_LIVE=1 GROUNDED_HARNESS_PROVIDER=... GROUNDED_HARNESS_MODEL=... \
#   python3 -m experiments.grounded_statecharts.run_constraint_ood_live_smoke
python3 -m experiments.grounded_statecharts.run_live_failure_replay --rows /path/to/rows.jsonl
python3 -m experiments.grounded_statecharts.run_chs_from_live_smoke --rows /path/to/rows.jsonl
python3 -m experiments.grounded_statecharts.run_chs_adjudication --with-injected \
  --rows /path/to/rows.jsonl
```

#### 3.3.4 Related reengagement packages

| Package | Purpose | Entrypoint |
|---|---|---|
| `habituated_reengagement` | Post-probe cooling stabilizes re-engagement (Paper 23B) | `modal_habituated_reengagement_sweep.py` |
| `probe_value_reengagement` | Value-of-information re-probing | `modal_probe_value_reengagement_sweep.py` |

### 3.4 Maintained-concern / control stack (thin Modal + paper)

These packages are typically **one Modal sweep + a paper**. Many have status
`paper` in verification with **0 committed result reports** — the paper is the
public record; raw Modal JSON stays local under `artifacts/`.

| Package | Paper title (short) | Entrypoint |
|---|---|---|
| `valence_object_formation` | Objects Form from Concern: valence clusters by causal role | `modal_object_formation_sweep.py` |
| `homeostatic_objects` | Valence-pretrained encoders survive episodic homeostatic RL | `modal_homeostatic_sweep.py` |
| `concern_bootstrap` | ΔE aux builds valence geometry; sparse-reward policies cannot exploit it | `modal_concern_sweep.py` |
| `two_bottlenecks` | ΔE aux bootstraps XOR valence when decoupled from sparse PG | `modal_two_bottlenecks_sweep.py` |
| `planning_from_concern` | Model-based ΔE planning without optimal-action supervision | `modal_planning_sweep.py` |
| `planning_hardening` | Planning depends on latent geometry, not a single reward axis | `modal_hardening_sweep.py` |
| `epistemic_exploration` | Conservative epistemic exploration recovers concern; novelty-seeking does not | `modal_exploration_sweep.py` |
| `exploration_diagnostics` | Skip-branch calibration; margin-based recovery; high-noise failure | `modal_diagnostics_sweep.py` |
| `state_dependent_concern` | State-dependent concern fails under online homeostatic training | `modal_state_dependent_sweep.py` |
| `off_policy_state_coverage` | Off-policy ΔE partially recovers; refutes coverage-only diagnosis | `modal_off_policy_sweep.py` |
| `regime_sensitive_de` | Regime-sensitive ΔE at E=0.5 boundary | `modal_regime_sensitive_sweep.py` |
| `autopoietic_control` | Viability slack as bottleneck for adaptive generalization | `modal_autopoietic_sweep.py` |
| `allostatic_control` | Regulate + planner at concern boundaries (honest falsification of 4 gates) | `modal_allostatic_sweep.py` |
| `ensemble_uncertainty` | Bootstrap ensembles fail at regime boundary; greedy planning remains robust | `modal_ensemble_uncertainty_sweep.py` |
| `valence_tapestry` | Vector ΔV adapts under internal-weight shifts; scalar cannot | `modal_tapestry_sweep.py` |
| `first_order_self` | Architectural factorization alone does not recover self/world attribution | `modal_first_order_self_sweep.py` |
| `null_intervention` | Null actions break gauge symmetry; active anchoring cuts false-credit | `modal_null_intervention_sweep.py` |
| `costly_null_probes` | Costly null probes for self/world identifiability | `modal_costly_null_probes_sweep.py` |
| `online_identifying_interventions` | Factorial isolation of probe-target bias | `modal_online_identifying_interventions_sweep.py` |
| `current_error_calibration` | Recent residuals insufficient unless recomputed against present model | `modal_current_error_calibration_sweep.py` |
| `vector_first_order_self` | Multi-valence agents with autonomous identifying interventions | `modal_vector_first_order_self_sweep.py` |
| `scale_normalized_vprobe` | Scale-normalized probe calibration (target × threshold factorial) | `modal_scale_normalized_vprobe_sweep.py` |
| `interventional_contrast` | Interventional contrast; hand-coded buckets → learned probe abstractions | `modal_interventional_contrast_sweep.py` |
| `role_specific_identifiability` | Architectural endpoint of autonomous-probing arc | `modal_role_specific_identifiability_sweep.py` |

Figures for these papers are produced by matching `scripts/make_*_figures.py`
(see §4.4). Reproduce dispatch: `python scripts/regen.py <name>`.

### 3.5 External validity / phases / governor

| Package | Modules | Notes |
|---|---|---|
| `commitment_surface` | `core.py`, `run_e1.py`, `e2_e3_neural_sweep.py`, `modal_e4_pythia_lora_v2.py` | E1–E4 severe tests; compact 108-cell E4 appendix JSON supports clean-clone PDF reproduction without raw Modal output |
| `external_contact` | `modal_p1_pythia_weakness.py`, `modal_p1_pythia_lora.py`, `p1_lora_metrics.py` | LoRA run does not pass P1; hard-kills external-transfer threshold |
| `gauge_fixed_concern_transport` | `core.py`, `budget.py`, `summarize.py`, `modal_l4_suite.py` | Gauge-fixed transport; smoke: `python -m experiments.gauge_fixed_concern_transport.core --preset smoke` |
| `phase4_metaphysics` | `core.py`, `summarize.py`, `modal_l4_suite.py` | Seven cheap parallel diagnostics |
| `phase5_external_validity` | `core.py`, `budget.py`, `summarize.py`, `modal_l4_suite.py` | Transport toward foundation-model proxies |
| `phase6_real_model_validation` | `core.py`, `real_models.py`, `budget.py`, `summarize.py`, `modal_l4_suite.py` | Public decoder LMs under predeclared gates |
| `virtual_governor_stress_signal` | `core.py`, `summarize.py`, `modal_l4_sweep.py` | README + committed stress-signal result |

### 3.6 Primer-derived local experiments and shared analysis

| Package / module | Contract and result | Entrypoints / artifacts |
|---|---|---|
| `mathematical_claims` | M-201 theorem-assumption matrix: seven finite satisfying examples plus paired assumption/predicate failures; accepted audit that does not establish theorem necessity or minimality | `core.py`, `experiment.py`, `theorem_assumption_matrix.json`, `results/mathematical_claims_summary.json`, `experiment_manifest.json` |
| `bayesian_voi` | M-208 exact two-state outcome enumeration across learnable, irreducible-noise, and misspecified-signal regimes; accepted gates separate oracle EVSI/true regret reduction from error heuristics | `core.py`, `experiment.py`, `preregistration.json`, `results/bayesian_voi_summary.json`, `experiment_manifest.json` |
| `seed_bootstrap_calibration` | S-022 simulation over 3/5/8/10/16/64 seeds and five effect/noise/hierarchy regimes; compares naive row percentile with paired seed-cluster resampling and emits 30 pilot/promotion decisions | `simulation.py`, `PREREGISTRATION.md`, `results/summary.{json,md}`, `experiment_manifest.json` |
| `passive_active_phase_map` | T-SYS-011/012 NumPy phase map with held-out segmented-vs-smooth fits and matched-budget continuation/reinit/washout paths; registered outcome is bifurcation not supported with path dependence | `core.py`, `preregistration.md`, `results/registered_summary.{json,md}`, `experiment_manifest.json` |
| `common/causal_use.py` | Shared non-experiment utility: mass-normalized target-minus-wrong-subspace dose curves, positive AUC, replicate bootstrap interval, and minimum transport across surfaces | Imported by experiment/test code; excluded from provenance inventory |

### 3.7 Experiment conventions

From `experiments/README.md`:

- hypothesis README/manifest
- deterministic seeds
- positive targets, negative controls, stress tests
- accepted and rejected artifacts
- discovery-regime audit after meaningful runs

Raw outputs stay under `artifacts/` until summarized.

---

## 4. Scripts catalog (`scripts/` — all files)

### 4.1 Provenance, quality, environment

| Script | Purpose | Flags / I/O |
|---|---|---|
| `research_contracts.py` | Shared schema version, identifier patterns, claim tiers/statuses, and evidence statuses used by registry/verdict adapters | Library; parity-tested against JSON Schemas |
| `gen_provenance.py` | Validate registries, resolve structured primary-run bindings from the contract registry, regenerate all experiment `PROVENANCE.md` files + `docs/verification.{md,json}` + site mirror; `--check` compares expected bytes without writing; legacy packages still use labeled heuristic extraction | In: 55 experiment dirs + claim/evidence/contract registries; excludes `experiments/common` |
| `validate_evidence_registry.py` | Validate canonical evidence IDs, gate statuses, artifact refs, and supersession shape | `docs/program_evidence_registry.json` |
| `validate_claim_registry.py` | Validate exact claim shape/tiers/states and bidirectional claim↔evidence edges | Reads `docs/claim_registry.json` + `docs/program_evidence_registry.json`; never writes either |
| `validate_experiment_manifest.py` | Enforce the authoritative package-contract registry (55 = 7 structured + 48 legacy), then discover and dependency-free validate every v1 experiment-package contract; every registered run `manifest_path` must be an `experiment_manifest.json` inside its publication package and validate as v1 by content; run records may declare `preregistration_digest` + `preregistration_path` (SHA-256 of a tracked pre-reg file, content-verified) and `producing_agent` (`identity` + `session_ref`); when the registry sets `preregistration_policy.required_after_run_date`, any run whose `run_id` ends with a date on or after the cutoff must supply all three | Reads `docs/experiment_contract_registry.json` and `experiments/**/experiment_manifest.json`; portable contracts in `schemas/experiment_contract_registry.schema.json` and `schemas/experiment_manifest.schema.json` |
| `validate_gate_verdict.py` | Discover per-gate verdicts, require registered claim IDs/canonical tiers/statuses, and resolve evidence paths | Reads `experiments/*/results/gate_verdicts/*.json` + `docs/claim_registry.json` |
| `validate_public_artifact_envelopes.py` | Validate declared public digest sidecars against tracked public bytes and embedded raw-source receipts | Reads manifest `envelope_path` entries and `*.envelope.json`; portable contract in `schemas/public_artifact_envelope.schema.json` |
| `check_primer_metadata.py` | Require matching titles across all six primer HTML `<title>` values and PDF metadata | Needs `pdfinfo` (`poppler-utils` in CI) |
| `regen.py` | List/reproduce experiments from the registered primary run, print documented Modal commands, or verify allowlisted clean-clone CPU recipes | `list`, `<name>`, `--deps`, `verify-clean-clone`, `--verify-clean-clone` |
| `run_quality_checks.py` | Locked `quality` sync → pytest → compileall → publication guard → four research-contract validators → primer metadata → provenance freshness → Ruff → ty; all post-sync commands use `uv run --no-sync` | Exit code; canonical local/CI root gate; local pytest serial by default, CI/opt-in local pytest bounded to four `loadscope` xdist workers with native math-library thread caps |
| `publication_guard.py` | Block tracked secrets, forbidden paths, oversized files; exposes a tested text-signature helper | Exit code |
| `env_probe.py` | Report env var presence/length only | `--json` |

### 4.2 PDF toolkit & builders

| Script | Purpose |
|---|---|
| `paperkit.py` | Shared reportlab/matplotlib PDF helpers (library) |
| `render_paper_pdf.py` | Markdown → PDF via markdown-pdf (`--in`, `--out`, `--title`, …) |
| `export_commitment_surface_e4_appendix.py` | Raw E4 sweep → compact public-safe 108-cell/aggregate JSON plus receipt-only envelope sidecar (`--input`, `--output`, `--envelope-output`) |
| `export_commitment_surface_e5_results.py` | Complete raw E5 grid → validated public-safe JSON/Markdown/envelope plus bounded abstract/discussion claim update |
| `build_commitment_surface_pdf.py` | Commitment-surface reframe paper PDF with repeating-header Appendix A.2 tables (E1–E5); synchronizes both PDF destinations |
| `build_weakness_pdf.py` | Flagship weakness→OOD PDF |
| `build_gridcell_pdf.py` | Paper A PDF |
| `build_paperB_pdf.py` | Paper B reward-deformation PDF |
| `build_effective_dimension_pdf.py` | Rate-distortion effective-dimension PDF |
| `build_concern_weighted_weakness_pdf.py` | Concern-weighted weakness note |
| `build_gauge_fixed_concern_transport_pdf.py` | GFC transport PDF; always writes repository copies and optionally mirrors to an injected external archive path (the CLI uses it only when the local archive exists) |
| `build_primer_residuals_pdf.py` | Render the post-merge six-primer residual register to `output/pdf/primer_derived_research_residuals_2026_07_14.pdf` with deterministic metadata, headers, and page numbers |
| `build_unified_portfolio_pdf.py` | Unified portfolio PDF |
| `build_structure_compatible_pdf.py` | SCG base paper (`--in`, `--out`, `--figure-dir`) |
| `build_structure_compatible_phase2_pdf.py` | SCG phase-2 inferred transformations |
| `build_structure_compatible_phase3_pdf.py` | SCG phase-3 learned generators |
| `build_structure_compatible_language_pdf.py` | SCG language-template paper |
| `build_structure_compatible_semantic_retrieval_pdf.py` | SCG semantic retrieval |
| `build_structure_compatible_semantic_selection_pdf.py` | SCG semantic selection-control |
| `build_phase4_metaphysics_pdf.py` | Phase 4 PDF |
| `build_phase5_external_validity_pdf.py` | Phase 5 PDF |
| `build_phase6_real_model_validation_pdf.py` | Phase 6 PDF |
| `build_comprehensive_literature_review_paper_pdf.py` | Literature review PDF |
| `build_exhaustive_literature_audit.py` | Scan local PDFs/refs → audit dataset |
| `build_exhaustive_literature_audit_pdf.py` | Render exhaustive audit PDF |
| `build_external_citation_review.py` | External scholarly metadata enrichment |
| `build_external_citation_review_pdf.py` | Render external citation review PDF |
| `build_unified_review_superset_pdf.py` | Validate and render `papers/unified_citation_grounded_review/paper.md` to its deterministic shareable PDF |

### 4.3 Figure makers

| Script | Paper / figure set |
|---|---|
| `make_commitment_surface_figures.py` | E1–E4 figure set (selectors, arm bars, patch-CE vs weakness scatter, taxonomy schematic) |
| `make_paper_figures.py` | Learned symmetry discovery |
| `make_neural_generator_figure.py` | When-Pixels-Beat-Embeddings comparison |
| `make_cluttered_mnist_figure.py` | Cluttered-MNIST heatmap |
| `make_rotated_mnist_figure.py` | Rotated MNIST threshold sweep |
| `make_topk_figure.py` | Top-K=8 ablation |
| `make_passive_to_active_figures.py` | Passive→Active geometry |
| `make_replication_figures.py` | Passive→Active replication v2 |
| `make_phase2_step4_figures.py` | Arc 2 Step 4 gate-margin |
| `make_concern_figures.py` | Paper 8 — Concern Bootstrap |
| `make_homeostatic_figures.py` | Paper 7 — Homeostatic Object Formation |
| `make_valence_object_figures.py` | Paper 6 — Valence-Induced Object Formation |
| `make_autopoietic_figures.py` | Paper 5b — Autopoietic Control |
| `make_allostatic_figures.py` | Paper 14 — Allostatic State Control |
| `make_tapestry_figures.py` | Paper 15 — Tapestry of Valence |
| `make_first_order_self_figures.py` | Paper 16 — First-Order Self |
| `make_agents_reafference_plasma.py` | Plasma concept figure for reafference |
| `make_null_intervention_figures.py` | Paper 16b — Identifiability Through Intervention |
| `make_exploration_figures.py` | Paper 11 — Epistemic Exploration |
| `make_diagnostics_figures.py` | Paper 11b — Exploration Diagnostics |
| `make_planning_figures.py` | Paper 10 — Planning from Concern |
| `make_hardening_figures.py` | Paper 10b — Hardening the Loop |
| `make_two_bottlenecks_figures.py` | Paper 9 — Two Bottlenecks |
| `make_off_policy_figures.py` | Paper 13a — Off-Policy State Coverage |
| `make_regime_sensitive_figures.py` | Paper 13b — Regime-Sensitive ΔE |
| `make_ensemble_figures.py` | Paper 14b — Ensemble Uncertainty |
| `make_state_dependent_figures.py` | Paper 12 — State-Dependent Concern |
| `make_costly_null_probes_figures.py` | Paper 17A — Learning When Not to Act |
| `make_online_identifying_interventions_figures.py` | Paper 18 |
| `make_current_error_calibration_figures.py` | Paper 19 |
| `make_vector_first_order_self_figures.py` | Paper 20B |
| `make_scale_normalized_vprobe_figures.py` | Paper 21A |
| `make_world_responds_figures.py` | Paper 22 |
| `make_long_horizon_bottleneck_figures.py` | Long-horizon moved-bottleneck |
| `make_metric_stack_synthesis_figures.py` | Metric-stack synthesis (Papers 16b–25) |
| `make_synthesis_anchor_figures.py` | Per-anchor synthesis figures |
| `make_gauge_fixed_concern_transport_figures.py` | GFC figures (`--in`, `--out-dir`) |
| `_patch_figure_titles.py` | One-off PNG title renumbering |

### 4.4 Summarizers & helpers

| Script | Purpose | Flags |
|---|---|---|
| `summarize_reward_location_sweep.py` | Modal reward-location shards → Paper B report | `--pattern`, `--combined`, `--report`, `--target-se` |
| `summarize_semantic_concern_sweep.py` | Semantic-concern sweep summary | `--input`, `--summary-json`, `--report` |
| `summarize_label_free_dose_response.py` | Public-safe dose-response tables | — |
| `summarize_label_free_behavior_gate.py` | Label-free behavior gate Markdown | — |
| `summarize_behavior_aligned_direction.py` | Behavior-aligned direction summaries | `--scale`, `--role` |
| `reproduce_paperB_stats.py` | Recompute Paper B stats from `data/paper_b/` | `--spatial-csv`, `--semantic-csv`, `--out` |
| `analyze_gridcell_conference_evidence.py` | Export Paper A reviewer stats from Modal JSON | `--raw-json`, `--out-dir`, … |
| `export_structure_compatible_artifacts.py` | Copy SCG artifacts to local archive | `--dest`, `--include-supporting`, `--clean`, `--dry-run` |
| `topk_ablation_stroke_benchmark.py` | Top-K=8 ablation on synthetic-stroke group inference | — |

### 4.5 Modal paper-task dispatchers

| Script | Purpose |
|---|---|
| `modal_lineage_paper_tasks.py` | Render lineage paper PDFs on Modal L4 (`--papers`) |
| `modal_metric_stack_paper_tasks.py` | Metric-stack artifacts/checks on L4 (`--mode`) |
| `modal_first_order_self_paper_tasks.py` | First-order-self paper artifacts on L4 |
| `modal_long_horizon_paper_tasks.py` | Long-horizon paper artifacts on L4 |
| `modal_planning_paper_tasks.py` | Planning-from-concern paper artifacts on L4 |
| `modal_world_responds_paper_tasks.py` | World-responds paper artifacts on L4 |

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run scripts/<script>.py --<flags>
```

---

## 5. Papers, notes, formal, references

### 5.1 `papers/`

Pattern: `papers/<topic>/paper.md` (+ optional prereg/runbook/figures).
`papers/pdf/` holds shareable renders.

Notable bundles:

- `papers/icml_publication_package_2026/` — submission packages
- Synthesis: `metaphysics_synthesis`, `metric_stack_synthesis`, literature audits/reviews
- Review methods: `unified_citation_grounded_review` (framework, ontology, executable reviewer, and alpha-research operating system)
- Benchmark framing: `causally_grounded_agents_benchmark`, `weakness_invariance_neurips`
- `papers/weakness_invariance_neurips/pac_bayes_weakness_sketch.md` — finite
  compatibility-class PAC-Bayes derivation, assumption ledger, severe
  aligned/wrong-group enumeration, and kill criteria; analytic only
- Most §3.4 experiment names have a matching `papers/<name>/paper.md`

Claim-bounded grounded-harness writeups also live under `docs/papers/`:

- [`docs/papers/grounded_harness_ct_preprint_2026-07-20.md`](papers/grounded_harness_ct_preprint_2026-07-20.md)
  — name-free / harness-enforced Constraint Transport preprint (D2 + D3 CT)
- [`docs/papers/grounded_harness_brief_2026-07-20.md`](papers/grounded_harness_brief_2026-07-20.md)
  — one-paragraph executive brief for the same slice

### 5.2 `notes/`

| File | Role |
|---|---|
| `geometric_convergence_research_synthesis.md` | Master program synthesis |
| `webb_miolane_fit.md` | Geometry-of-consciousness talk fit |
| `weakness_topology_program_synthesis.md` | Publication-strategy ranking |
| `reward_deformation_ratedistortion.md` | Rate-distortion law for Paper B |
| `virtual_governor_alignment_fit.md` | Virtual-governor preprint fit |

### 5.3 `formal/ontology-hs/`

| Path | Role |
|---|---|
| `src/ConcernedOntology.hs` | Typed ontology rules |
| `app/Main.hs` | `ontology-check` CLI |
| `test/Main.hs` | Cabal tests |
| `concerned-ontology.cabal` | Package manifest |

Python bridge: `experiments/viable_computational_bodies/haskell_gate.py`.

```bash
cd formal/ontology-hs && cabal test all && cabal run ontology-check
```

### 5.4 `references/`

| Path | Role |
|---|---|
| `SOURCES.md` | Public source manifest |
| `webb-miolane-geometry-of-consciousness-transcript.md` | Committed talk transcript |
| `philosophy_claim_boundaries.md` | Dretske/Millikan/Boyd/Dennett/Metzinger claim boundaries and experiment consequences |
| `science_methodology_claim_boundaries.md` | Preregistration, bootstrap/power, independent analysis, provenance, and execution-grounded review decisions |
| `papers/`, `text/`, `html/` | **Local-only** full texts (gitignored) |

---

## 6. Product & adjacent projects

### 6.1 `sites/reafference_attribution/` — Research Mechanism Atlas

| Item | Detail |
|---|---|
| Role | Public animated mechanism atlas + paper/PDF index |
| Stack | Static Node `server.js`, canvas `app.js`, no build step |
| Served | `index.html`, `styles.css`, `app.js`, `verification.json`, `papers/*.pdf` |
| Port | `PORT` (default 3000) |
| Server behavior | GET/HEAD; path-traversal guard; open static tree under site root |
| Tests | `npm test` → `node --test tests/*.test.js` |
| Deploy | Railway via `.github/workflows/railway-deploy.yml` |

### 6.2 `sites/inquiry_black_box/` — Inquiry landing

| Item | Detail |
|---|---|
| Role | Marketing/landing for Inquiry Black Box |
| Stack | Whitelist static Node server |
| Served | `index.html`, `styles.css`, `app.js`, `assets/aperture-*.png` **only** |
| Port | `PORT` (default 3010) |
| Server behavior | Explicit `isPublicPath()` whitelist; other paths → 404 |
| Deploy | Separate Railway service in same Actions matrix |

### 6.3 `apps/inquiry-black-box/` — full catalog

Local-first Neurophenom cockpit: pair extension → record → replay → daily review → export/delete.

#### Workspace scripts (`package.json`)

| Script | Purpose |
|---|---|
| `install:check` | Frozen lockfile install |
| `lint` / `typecheck` / `test` / `test:e2e` | Quality |
| `build:desktop` / `build:extension` / `build:prototype` | Builds |
| `package:desktop` / `package:extension` / `package:local` | macOS app + MV3 ZIP |
| `dev:desktop` / `dev:extension` / `dev:cloud` | Dev servers |
| `brand:sync` | Sync logo assets |
| `railway:sync-model-env` | Push model env to Railway via Doppler |
| `modal-check` | Modal pytest |
| `validation:smoke` / `test:validation` | Research validation |

#### Packages

| Package | Purpose |
|---|---|
| `packages/schema` | Event envelope, privacy classes, retention, session validation |
| `packages/signals` | Windowing, heuristics, heatmaps, interpretation, daily review, redacted Modal inputs |
| `packages/ui` | Shared view models and warm-neutral/teal tokens used by desktop and extension |

#### Apps

| App | Role | Key areas |
|---|---|---|
| `apps/desktop` | Electron main + renderer; SQLite source of truth | first-viewport recording controls, guided extension pairing, ingest, db, privacy, reports, notifications, security, activity, packaging |
| `apps/extension` | Chrome MV3 | pairing-first popup, session/page capture controls, privacy disclosures, service-worker, content telemetry, localBridge |
| `apps/cloud` | Optional Railway Bun API | sync/reports/jobs routes, Postgres, Modal bridge |

#### Modal jobs (`modal/`)

| File | Purpose |
|---|---|
| `inquiry_jobs.py` | `smoke_job`, `session_summary_job`, webhook FastAPI |
| `model_env.py` | Provider/env resolution |
| `models/session_features.py` | Redacted feature extraction |
| `models/session_summary.py` | Redacted LLM summaries |
| `models/calibration.py` | Toy calibration model card |
| `tests/test_session_*.py` | Reject sensitive fields before extraction |

#### Tests

Desktop (17+), extension, cloud, schema, signals, ui, `tests/e2e/`,
`tests/fixtures/`, `research/validation.test.ts`, `modal/tests/`.

#### Docs inside the app

`README.md`, `AGENTS.md`, `docs/local-dev.md`, `docs/architecture.md`,
`docs/privacy-model.md`, `docs/deployment.md`, `docs/prototype-demo.md`,
`docs/release-checklist.md`, `docs/research-validation.md`.

#### Install / test / run

```bash
cd apps/inquiry-black-box
bun install
bun run lint && bun run typecheck && bun run test && bun run test:e2e
bun run build:prototype
bun run package:local
# Modal: cd modal && doppler run -- modal deploy inquiry_jobs.py
```

#### Env vars (selected)

`INQUIRY_LOCAL_API_PORT`, `INQUIRY_PAIRING_SECRET`, `INQUIRY_DESKTOP_DB_PATH`,
`INQUIRY_CLOUD_AUTH_SECRET`, `INQUIRY_CLOUD_BEARER_TOKEN`, `DATABASE_URL`,
`RAILWAY_PUBLIC_API_URL`, `MODAL_JOB_WEBHOOK_URL`, `MODAL_JOB_WEBHOOK_TOKEN`,
`MODAL_TOKEN_*`, model provider keys, `MODEL_PROVIDER`, `SESSION_SUMMARY_MODEL`,
`SYNC_ENCRYPTION_KEY`. Full list: app `AGENTS.md`.

### 6.4 `coherence-testbench/` — full catalog

Phase-0 GO/KILL bench for cross-subject cognitive-state decoding on BBBD.
**Status:** EEG **KILL**; eyetrack **INCONCLUSIVE**; Phase 3 **FROZEN**.

#### Top-level docs

| File | One-liner |
|---|---|
| `README.md` | Phase-0 GO/KILL bench overview |
| `POST_MORTEM.md` | EEG KILL / eyetrack INCONCLUSIVE / Phase 3 frozen |
| `NEXT_STEPS.md` | Post-KILL thinking menu |
| `PHASE0_TODO.md` | Closed checklist — verdict 2026-07-06 |
| `MODALITY_COMPARISON.md` | EEG vs eyetrack head-to-head |
| `QUIZ_VERIFICATION.md` | Adversarial verification of retracted quiz GO |
| `MORNING_BRIEF.md` | Overnight run timeline |

#### Config

| File | Purpose |
|---|---|
| `kill_criterion.yaml` | EEG attention-binary pre-reg (`phase0.v1`) |
| `kill_criterion_eyetrack.yaml` | Eyetrack attention-binary |
| `kill_criterion_eyetrack_quiz.yaml` | Eyetrack quiz-score regression |
| `kill_criterion_eeg_labram.yaml` | LaBraM rescue pre-reg |
| `phase0.yaml` / `phase0_eyetrack.yaml` / `phase0_eyetrack_quiz.yaml` / `phase0_eyetrack_quiz_residual.yaml` / `phase0_labram.yaml` | Run configs |

#### `src/coherence/`

| Module | Purpose |
|---|---|
| `config.py` | Typed kill-criterion + phase-0 loaders (content hash) |
| `ingest/bbbd.py` | BBBD Zenodo/BIDS EEG ingest |
| `ingest/eyetrack.py` | BBBD eyetrack TSV ingest |
| `preprocess/pipeline.py` | EEG HPF/notch/resample/epoch/artifacts |
| `preprocess/eyetrack_features.py` | Windowed eyetrack features |
| `decoders/baseline.py` | Per-subject Riemannian upper bound |
| `decoders/cross_subject.py` | Alignment + domain-adversarial + SSL hook |
| `decoders/eyetrack.py` | Flat-feature eyetrack analogues |
| `decoders/eyetrack_regression.py` | Quiz-score regression head |
| `evaluate/leave_subjects_out.py` | LSO CV; balanced accuracy + bits/sec MI |
| `report/go_kill_report.py` | Auto GO/KILL report |

#### Modal jobs / scripts / tests

| Path | Purpose |
|---|---|
| `modal_jobs/prepare_bbbd.py` | One-time BBBD download to Modal volume |
| `modal_jobs/train.py` | EEG Phase-0 gate |
| `modal_jobs/train_eyetrack*.py` | Eyetrack binary / quiz / residual |
| `modal_jobs/train_labram.py` | LaBraM rescue |
| `scripts/run_phase0.py` | Local driver (`--smoke`, `--config`, `--out`) |
| `scripts/spawn_phase0.py` | Fire-and-forget Modal |
| `scripts/generate_report.py` | Report from saved artifacts |
| `scripts/env_probe.py` | Env presence |
| `tests/test_kill_criterion.py` | Locks pre-reg hash + verdict logic |
| `tests/test_smoke_pipeline.py` | Synthetic LSO+report (needs torch+pyriemann) |
| `supabase/schema.sql` | Corpus index schema |
| `site/` | Marketing landing (Phase 3 on pause) |

```bash
python3 scripts/run_phase0.py --smoke
# Full gate: doppler … modal run modal_jobs/train.py --config config/phase0.yaml
```

---

## 7. CI / config modules

| File | Role |
|---|---|
| `.github/workflows/quality.yml` | Required push/PR workflow: installs uv with cache keys derived from `uv.lock`, installs `poppler-utils`, sets `QUALITY_PYTEST_WORKERS=auto`, then runs the canonical root quality wrapper |
| `.github/workflows/railway-deploy.yml` | Deploy atlas + Inquiry landing on `main` |
| `schemas/{experiment_contract_registry,experiment_manifest,program_evidence_registry,claim_registry,gate_verdict,public_artifact_envelope}.schema.json` | Portable JSON Schema contracts for package coverage, package intent, evidence, claims, gate outcomes, and public-artifact envelopes |
| `templates/experiment/{manifest,gate_verdict}.example.json` | Copyable version-1 examples validated by the same adapters used in CI |
| `pyproject.toml` | Project metadata; root `quality` dependency group (pytest/xdist, scientific/PDF, Ruff, ty); explicit CPU-only PyTorch source; existing Ruff rules and ty exclusions |
| `uv.lock` | Locked Python 3.12 root-quality graph used by `uv sync --locked`; records platform-specific CPU-only Torch wheels and excludes CUDA/Triton/NVIDIA packages |
| `pyrightconfig.json` | Editor typecheck: missing imports silenced |
| `.gitignore` | Secrets, `artifacts/`, `data/`, reference full texts, caches |

---

## 8. Plans, paper reviews, solutions

### 8.1 `docs/plans/` (14)

| File | Summary |
|---|---|
| `2026-07-06-001-feat-structure-compatible-generalization-plan.md` | SCG L4 suite |
| `2026-07-06-002-feat-inferred-transformations-intervention-plan.md` | Inferred transformations + compatibility intervention |
| `2026-07-06-003-feat-suite-c-neural-transfer-plan.md` | Suite C neural probe transfer |
| `2026-07-07-001-feat-inquiry-black-box-plan.md` | Inquiry Black Box product |
| `2026-07-07-002-feat-gfc-modal-experiments-plan.md` | Gauge-Fixed Concern Transport Modal |
| `2026-07-07-003-feat-inquiry-live-prototype-plan.md` | Inquiry live prototype |
| `2026-07-07-004-feat-inquiry-evidence-context-plan.md` | Inquiry evidence context |
| `2026-07-08-001-feat-inquiry-opt-in-text-context-plan.md` | Opt-in text context |
| `2026-07-08-002-feat-inquiry-recording-coordination-plan.md` | Recording coordination |
| `2026-07-08-003-feat-inquiry-finish-product-plan.md` | Finish product |
| `2026-07-08-004-feat-inquiry-desktop-app-watch-plan.md` | Desktop app watch |
| `2026-07-08-005-feat-inquiry-llm-daily-suggestions-plan.md` | LLM session interpretation + daily suggestions |
| `2026-07-08-006-feat-inquiry-usability-value-redesign-plan.md` | Usability / value / design coherence |
| `2026-07-14-001-perf-faster-quality-gate-plan.md` | Locked CPU-only root quality gate with bounded parallel pytest |

### 8.2 `docs/paper_reviews/` (15)

| File | Subject |
|---|---|
| `architecture_laws_machine_agency_critical_review.md` | Architecture Laws for Machine Agency |
| `current_error_calibration_critical_review.md` | Current-Error Calibration |
| `first_order_self_critical_review.md` | First-Order Self |
| `inferred_transformations_intervention_critical_review.md` | Inferred Transformations for SCG |
| `long_horizon_bottleneck_critical_review.md` | Long-Horizon Moved-Bottleneck |
| `metric_stack_synthesis_critical_review.md` | Metric Stack Synthesis |
| `planning_from_concern_critical_review.md` | Planning from Concern |
| `scale_normalized_vprobe_critical_review.md` | Scale-Normalized V_probe |
| `structure_compatible_generalization_critical_review.md` | Structure-Compatible Generalization |
| `suite_c_neural_probe_transfer_critical_review.md` | Suite C Neural Probe Transfer |
| `suite_c_reengagement_under_world_change_critical_review.md` | Suite C Re-Engagement |
| `vector_first_order_self_critical_review.md` | Vector First-Order Self |
| `virtual_governor_alignment_preprint_critical_review.md` | Alignment Is to a Virtual Governor |
| `virtual_governor_stress_signal_critical_review.md` | Virtual-Governor Stress Signals |
| `world_responds_critical_review.md` | When the World Responds |

### 8.3 `docs/solutions/`

| File | Summary |
|---|---|
| `architecture-patterns/pixel-rendered-concerned-syntax-gate.md` | Pixel-rendered concerned-syntax gates should transport controls when changing observation surface |

---

## 9. Maintenance checklist for this catalog

Root `AGENTS.md` routes experiment-boundary work through
`scientific-discovery-regime-audit` and the relevant modules in
`papers/unified_citation_grounded_review/paper.md`. It deliberately does not run
the full reviewer on routine code/docs work. Preregistrations or audit cards
carry the compact target, representation/data-clock, assumption, fatal-gate,
control, and evidence-path record; failed or unknown necessary gates cannot be
offset by aggregate scores.

The adjacent mathematical-claim rule is conditional rather than always-on. It
applies to new or materially changed theorems, derivations, stochastic models,
geometric constructions, estimators, statistical tests, and objectives. The
claim record fixes objects/types, domains/support, units, quantifiers,
assumptions, proof dependencies, representation choices, and boundary cases;
symbolic or numerical checks supplement but never replace theorem-level proof.

When you add or materially change code:

1. Update [system_design.md](system_design.md) if runtime flow, deps, deploy, or capabilities/limitations change.
2. Update this file: experiment modules, script entries, test mapping, plans/reviews, or product surfaces.
3. Regenerate all experiment cards/indexes via `python scripts/gen_provenance.py`; never hand-edit generated cards.
4. Add or update the versioned experiment manifest and per-gate verdict where the structured-contract surface applies.
5. Keep `experiments/README.md` active-track list honest.
6. Link new public-facing docs from root `README.md` when they are start-here material.

```bash
python scripts/gen_provenance.py
```
