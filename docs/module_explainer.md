# Module Explainer & Package Catalog

Catalog of packages, modules, major scripts, test areas, and documentation in
**research-derived-experiments**. Companion: [system_design.md](system_design.md).
Update both when the codebase changes meaningfully (see root `AGENTS.md`).

---

## 1. Repo map (top level)

| Path | Responsibility |
|---|---|
| `experiments/` | 57 research packages plus `common/` shared analysis utilities; harnesses, Modal sweeps, committed `results/`, generated `PROVENANCE.md` |
| `papers/` | Paper sources (`paper.md`), figures, shareable PDFs |
| `scripts/` | 94 Python ops modules: quality, contracts, provenance, PDF/figure builders, summarizers |
| `tests/` | 103 root test files collected together by pytest (`unittest`-style and pytest-native) |
| `docs/` | Design docs, verification, handoffs, plans, reviews, solutions |
| `docs/primers/backlogs/` | Six article-specific, source-anchored research TODOs derived from the primer PDFs |
| `notes/` | Program-level research synthesis |
| `references/` | Public source list; local-only full texts (gitignored subdirs) |
| `formal/ontology-hs/` | Haskell typed ontology gate (Arc 2B) |
| `sites/` | Public static sites (atlas, Inquiry landing, Envelope Guard) |
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
| Concern-gated retrieval theory and next experiments | [concern_gated_retrieval_research_program.md](concern_gated_retrieval_research_program.md) + [next-agent handoff](next_agent_concern_gated_retrieval_handoff_2026-07-23.md) |
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
| `test_concern_gated_retrieval.py` | PPR fixed points, concern warping, spectral epiplexity checks, two-sided retrieval controls, care updates, and byte-stable pilot receipt |
| `test_cogr_wave0_graph_learn.py` | Wave 0 fixed-withheld-geometry stubs: determinism, cross-family disjoint namespaces, warp preserves node support, PPR fixed-point residual < 1e-9, rarity aggregator invariants |
| `test_cogr_wave0_maintenance_fault.py` | Wave 0 `maintenance_fault` procedural family: determinism, adversarial wrong prior, off-context load-bearing target, non-ceiling utility-differential cap, paraphrase-family holdout honored, seed-range refusal |
| `test_cogr_wave0_concern_update.py` | Wave 0 concern-update learner (exploratory only): epsilon-greedy propensity is logged correctly, IPS reduces wrong-prior bias vs a propensity-blind naive aggregator, the single-source influence bound (poisoning guard) holds, and the pair `LoggedProbePolicy.select` + `update_concern` is deterministic given a seed and receipt/outcome batch |
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
| `test_grounded_chs_withheld_seal_search.py` | `BlindFaultCase`/`BlindSearchResult` carry no `responsible_component`; the blind pilot matches the original pilot case-by-case; withheld-seal writing/loading gates; end-to-end withheld equal-budget search-vs-seal scoring, including a corrupted-label failure case |
| `test_grounded_chs_live_withheld_score.py` | Harvest-vs-seal join by result digest only (agree/disagree/no-coverage cases); refuses `results/` output; end-to-end fresh seal+harvest+join on fixture-deterministic live rows |
| `test_causal_use.py` | Shared mass-normalized causal-use dose curves, bootstrap uncertainty, and cross-surface transport |
| `test_experiment_manifest.py`, `test_gate_verdict.py`, `test_evidence_registry.py`, `test_claim_registry.py` | Fail-closed research-contract adapters, package-coverage registry partition, discovery, references, supersession, and bidirectional edges |
| `test_research_contract_schema_parity.py`, `test_gen_provenance.py` | Shared vocabulary/schema parity, support-directory exclusion, non-mutating provenance freshness |
| `test_run_quality_checks.py` | Locked quality-command order, local serial default, bounded xdist worker parsing, `loadscope` scheduling, and native-thread caps |
| `test_build_primer_residuals_pdf.py` | Required six-article residual source sections plus reproducible ReportLab PDF build |
| `test_build_unified_review_superset_pdf.py` | Required four-part review synthesis, fatal-gate semantics, and deterministic ReportLab PDF build |
| `test_cogr_wave0_pdf.py` | Wave 0 PDF builder smoke test: skips if `papers/concern_gated_retrieval_wave0/paper.md` does not yet exist (upstream report-draft has not run) or if `reportlab` is unavailable; otherwise builds into a `tmp_path` (never touches the committed PDF or the Metaphysics archive), and asserts the output starts with `%PDF`, exists, is at least 30 KB, and matches the mirrored `papers/pdf/` copy byte-for-byte. |

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
| [verification.md](verification.md) / `verification.json` | Provenance index (auto-generated from all 57 research packages; `experiments/common` excluded) |
| `experiment_contract_registry.json` | Authoritative 57-package coverage partition: 9 structured roots + 48 time-bounded legacy exceptions with frozen digest |
| `program_evidence_registry.json` | 12 canonical evidence records with stable IDs, states, artifact refs, and claim links |
| `claim_registry.json` | 12 canonical claim records with tiers, states, source refs, and bidirectional evidence links |
| [causally_grounded_agents_benchmark.md](causally_grounded_agents_benchmark.md) | Benchmark umbrella |
| [causally_grounded_agents_release_schema.md](causally_grounded_agents_release_schema.md) (+ `.json`) | Shared release schema |
| [causally_grounded_agents_next_gap.md](causally_grounded_agents_next_gap.md) | Suite C transfer gaps |
| [concern_gated_retrieval_research_program.md](concern_gated_retrieval_research_program.md) | Canonical two-flashlight intuition, mechanism decomposition, split generic/concern claim ladder, staged COGR-E2, safety gates, and live-agent advancement program |
| [next_agent_concern_gated_retrieval_handoff_2026-07-23.md](next_agent_concern_gated_retrieval_handoff_2026-07-23.md) | Pointer-first continuation contract for premise/calibration work, staged concern recovery and learned geometry, separate L1/L2 gates, and live-agent validation |
| [harness_research/README.md](harness_research/README.md) | Staged grounded-harness portfolio with deterministic replay, transport, counterfactual, and functional-unlearning fixtures |
| [next_agent_grounded_harness_experiments_handoff_2026-07-20.md](next_agent_grounded_harness_experiments_handoff_2026-07-20.md) | Post-fixture execution handoff: shared live-evaluation contract, ordered D2–D4 experiments, six safe parallel lanes, pilot gates, kill conditions, and release definition |
| [next_agent_envelope_guard_product_ct_chs_handoff_2026-07-21.md](next_agent_envelope_guard_product_ct_chs_handoff_2026-07-21.md) | Next tranche after CT ship: Envelope Guard product contract editor (Track 1), powered CT multi-model/OOD stress (Track 2), author-blind CHS1 (Track 3) — implement/run/learn/report |
| `harness_research/grounded_statecharts.md` | Independent transition-guard design plus links to the implemented deterministic fixture runtime |
| `harness_research/constraint_transport.md` | Recursive constraint-envelope and externally enforced transition-guard benchmark design |
| `harness_research/counterfactual_harness_search.md` | Paired intervention, causal-credit, and equal-budget harness-search design |
| `harness_research/harness_unlearning.md` | Provenance-aware quarantine, commitment-level suppression, and revalidation design |
| [`harness_research/load_bearing_prose_test.md`](harness_research/load_bearing_prose_test.md) | Thesis for the concern-transport bridge-theorem test on LLM-produced prose over CT κ (plan and preregistration frozen 2026-07-21; scaffolding follows) |
| [`plans/2026-07-21-001-feat-load-bearing-prose-test-plan.md`](plans/2026-07-21-001-feat-load-bearing-prose-test-plan.md) | Load-bearing prose test plan (Goal Capsule + Product Contract + weekly execution + kill criteria) |
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

**Verification reconciliation:** 57 research packages on disk plus one shared
support package, `experiments/common`. `gen_provenance.py` intentionally excludes
the support package and derives 57 cards/index rows; `gen_provenance.py --check`
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
| `counterfactual_search.py` | Six-surface fault manifests, deterministic outcome vectors, isolated repair/placebo replay, attribution credit, and equal-budget trace baseline; also `BlindFaultCase`/`BlindCounterfactualHarnessPilot`/`BlindSearchResult`, a structurally label-free variant with no `responsible_component` attribute on either the case or the result, used by the withheld-at-score-time CHS tier |
| `run_counterfactual_search.py` | Pilot runner, fault-integrity gates, attribution/repair metrics, and compact static replay |
| `chs_sealed.py` / `run_chs_sealed_smoke.py` | Credential-free synthetic-to-sealed-label plumbing for one clean and six single-fault cases, scored against a separate label artifact |
| `chs_repair_search.py` / `run_chs_repair_search.py` | Re-runs the equal-budget (identical per-arm cost) counterfactual repair/placebo search fresh and scores it against both the adjudicated injected-fault seal tier (`results/chs_injected_faults/labels.jsonl`) and the hand-authored fixture label file (`fixtures/chs_sealed_labels.json`); gates on zero placebo credit, exact budget parity, and cross-source label agreement; writes `results/chs_repair_search/`; explicitly not CHS1 on naturalistic live failures |
| `chs_repair_search.py`'s withheld tier / `run_chs_withheld_seal_search.py` | `seal_withheld_labels`/`generate_withheld_seals` write a separate label store (`results/chs_withheld_seals/labels.jsonl`); `score_withheld_repair_search`/`generate_withheld_results` (`--sealed-labels`) run `BlindCounterfactualHarnessPilot` over `BlindFaultCase` (no `responsible_component` attribute) and join `recovered_component` to that store by `fault_id` only, after the search has already returned; gates assert both `BlindFaultCase` and `BlindSearchResult` have no label attribute; writes `results/chs_withheld_seal_search/`; a CHS1-bridge, not author-blind human adjudication CHS1 |
| `chs_live_withheld_score.py` / `run_chs_live_withheld_score_smoke.py` | Joins the already-mutually-blind live heuristic harvest (`chs_from_live.harvest_candidates`, never sees `responsible_component`) against the paired-contrast seal (`chs_adjudication.seal_from_paired_contrasts`, never sees `predicted_component`) by `source_result_digest` only, after writing and re-reading both from disk; writes under gitignored `artifacts/grounded_statecharts/chs_live_withheld_score/`; on `d2_pilot_harness_v2` rows this covers 12 of 144 rows (orchestration/output-only seal) with 100% top-1 agreement, and is explicitly not an equal-budget repair/placebo search or CHS1 |
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
python3 -m experiments.grounded_statecharts.run_chs_withheld_seal_search
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
# Live withheld-at-score-time harvest-vs-seal join (writes under artifacts/ only):
python3 -m experiments.grounded_statecharts.run_chs_live_withheld_score_smoke \
  --rows /path/to/rows.jsonl
```

#### 3.3.4 `load_bearing_prose_test` — prose commitment-surface test (Weeks 1–2 landed)

Concern-transport bridge-theorem test on LLM-produced prose. Weeks 1
and 2 are landed as deterministic scaffolding plus a runnable pilot
that reuses the CT κ substrate and CT commitment-surface oracle.

| Path | Purpose |
|---|---|
| `experiments/load_bearing_prose_test/PREREGISTRATION.md` | Fatal gates, kill criteria, escalation sequence |
| `experiments/load_bearing_prose_test/experiment_manifest.json` | Root manifest bound in `docs/experiment_contract_registry.json` as `structured_manifest` |
| `experiments/load_bearing_prose_test/claims.py` | Typed `Claim`, `ClaimBundle`, `Ablation`, `AblationSet`, `Verdict` dataclasses with canonical digests |
| `experiments/load_bearing_prose_test/extraction.py` | `ClaimExtractor` protocol plus `RuleBasedExtractor` and `KappaVocabulary` |
| `experiments/load_bearing_prose_test/live_extraction.py` | Env-gated `LiveClaimExtractor` (Week 2 punt-recovered); falls back to `RuleBasedExtractor` when `LBPT_LIVE` is unset |
| `experiments/load_bearing_prose_test/ablation.py` | Atomic-alternation `delete_claim`, `negate_claim`, `paraphrase_claim`, and `ablate_bundle` transforms |
| `experiments/load_bearing_prose_test/executor.py` | `PlanEpisode`, `PlanSensitiveFixtureExecutor` (deterministic, keyword-driven), env-gated `CTPlanLiveExecutor` wrapping the CT `LiveExecutor`, and `run_plan_episode` which applies CT `condition_policy` |
| `experiments/load_bearing_prose_test/scoring.py` | `CommitmentSurface` tuple (`action` + `capability_used` + `artifact_created` + `workspace_digest` + `false_completion` + `joint_success`), `surface_delta`, `classify_claim`, `AggregatedMetrics` with κ odds ratio |
| `experiments/load_bearing_prose_test/fixtures/*.json` | Frozen seed plans mirroring the two CT task families with κ vocabulary |
| `experiments/load_bearing_prose_test/run_lbpt_smoke.py` | Deterministic scaffold smoke — writes `results/summary.json` |
| `experiments/load_bearing_prose_test/run_lbpt_pilot.py` | Pilot orchestrator — baseline + delete/negate/paraphrase ablations under primary and control conditions per family; writes `results/pilot/{summary,rows}.jsonl?` |
| `tests/test_lbpt_{claims,extraction,ablation,smoke,executor,scoring,pilot}.py` | 46 deterministic tests |
| [`harness_research/load_bearing_prose_test/README.md`](harness_research/load_bearing_prose_test/README.md) | Package contract and non-claims |

Week-3 (paraphrase-invariance gauge check, κ concordance, CHS-style
injected-fault sealing) and Week-4 (held-out confirmatory + public
dataset + preprint) are the remaining stages. Live provider spend
requires `LBPT_LIVE=1` plus the CT live env vars.

#### 3.3.5 `concern_gated_retrieval` - two-sided off-context retrieval

Deterministic synthetic diagnostic derived from the concern-weighted retrieval
proposal and Zhang-Levin reservoir epiplexity estimator. It separates cheap
graph nomination, goal-conditioned utilization verification, and exploratory
online care updates; graph roles and simulator utility remain authored.

| Path | Purpose |
|---|---|
| `experiments/concern_gated_retrieval/PREREGISTRATION.md` | Abstract, typed object/representation card, equations, controls, fatal gates, audit, and claim boundary |
| `experiments/concern_gated_retrieval/graph.py` | Weighted graph, concern warp, personalized PageRank, fixed-point receipt, rarity-corrected Hadamard score |
| `experiments/concern_gated_retrieval/epiplexity.py` | Frozen random reservoir, stable ridge readout, and spectral log-determinant epiplexity estimator |
| `experiments/concern_gated_retrieval/benchmark.py` | Seeded base/sparse/noisy episodes, one-sided/additive/product policies, reachable-future controls, and selected-probe care update |
| `experiments/concern_gated_retrieval/run_pilot.py` | Byte-stable 192-episode pilot and noncompensatory gate evaluation |
| `experiments/concern_gated_retrieval/results/{summary.json,pilot_2026_07_23.md}` | Machine receipt and claim-bounded interpretation; additive necessity and care-learning claims withheld |
| `experiments/concern_gated_retrieval/experiment_manifest.json` | Structured local-CPU contract bound to the exact pilot run |
| `tests/test_concern_gated_retrieval.py` | Numerical, invariance, selectivity, update, and frozen-receipt tests |
| `docs/concern_gated_retrieval_research_program.md` | Canonical intuition, evidence ledger, split claim ladder, staged E2 design, safety gates, application boundary, and advancement program |
| `docs/next_agent_concern_gated_retrieval_handoff_2026-07-23.md` | COGR-E2a/E2b preregistration target, dependency order, separate fatal gates, continuation constraints, and later live/transfer path |

```bash
python3 -m experiments.concern_gated_retrieval.run_pilot
pytest -q tests/test_concern_gated_retrieval.py
```

#### 3.3.5b `concern_gated_retrieval_e2` — Wave 0 calibration and freeze

Successor to `concern_gated_retrieval`. Hosts the staged COGR-E2 program and,
in `wave0/`, the calibration-only premise-scaffolding and threshold-freeze
step described in
[`docs/concern_gated_retrieval_research_program.md`](concern_gated_retrieval_research_program.md).
Wave 0 imports (never edits) the pilot's `WeightedGraph`,
`personalized_pagerank`, and Zhang-Levin epiplexity primitives.

| Path | Purpose |
|---|---|
| `experiments/concern_gated_retrieval_e2/__init__.py` | Package marker for the E2 successor package; documents the reuse boundary against the frozen pilot. |
| `experiments/concern_gated_retrieval_e2/README.md` | Wave layout, reuse boundary, and Wave 0 claim boundary; points at the roadmap and handoff. |
| `experiments/concern_gated_retrieval_e2/wave0/__init__.py` | Package marker for the Wave 0 calibration subpackage; documents the wave's non-claims. |
| `experiments/concern_gated_retrieval_e2/wave0/PREREGISTRATION.md` | Wave 0 preregistration: abstract, target object, data clock, anti-leakage boundaries, wrong-prior spec, three procedural families, baseline slate, threshold shape (TBD until Modal fills), fatal gates (integrity/non-ceiling/robustness/adversarial), calibration seed range 100000-100999, reserved confirmatory range 200000-201999, and analysis-code freeze hash. |
| `experiments/concern_gated_retrieval_e2/wave0/PROMOTION_CONTRACT.md` | Non-compensatory Wave 0 promotion contract: claim id, gates G0-G6, promotion rule, retroactive demotion rule, and required artifacts. |
| `experiments/concern_gated_retrieval_e2/wave0/PROVENANCE.md` | Skeleton receipt filled by the Wave 0 Modal calibration step (deploy hash, L4 cost, per-family variance, gate receipts, `WAVE0_ANALYSIS_HASH`, premise-audit stub marked non-evidential). |
| `experiments/concern_gated_retrieval_e2/wave0/graph_learn.py` | Wave 0 fixed-withheld-geometry builders (`build_withheld_graph` per family, `apply_concern_warp` facade over the pilot's `WeightedGraph.concern_warped`, `rarity_scores` inverse-frequency aggregator, and a Wave 0-boundary re-export of `personalized_pagerank`). Independent of role labels and any evaluator-only field; imports `WeightedGraph` / `personalized_pagerank` from the frozen pilot and does not fork them. Wave 1 learned-geometry code is out of scope here. |
| `tests/test_cogr_wave0_graph_learn.py` | Wave 0 graph-learn stub tests: determinism given a seed, cross-family node-namespace disjointness, family / seed / size input validation, concern warp preserves node support and edge sign, zero-prior warp is identity, PPR fixed-point residual < 1e-9 pre- and post-warp, and rarity aggregator determinism and shared-vs-singleton ordering. |
| `experiments/concern_gated_retrieval_e2/wave0/sealed_env.py` | Sealed environment interface: `EpisodeSpec` (full evaluator-side episode with sealed `role` / `utility` / `_answer_key` fields), `EpisodeContext` (policy-visible view returned by `observe`), `RetrievalChoice`, `SealedOutcome`, `SealedEnvironment` (single-shot `evaluate` guard + calibration/confirmatory family-split guard), and `IntegrityAudit` (AST static walker that raises `LeakageError` on any policy that dereferences the sealed field names). Wave 0 anti-leakage boundary between policy and evaluator per PREREGISTRATION.md §4. |
| `tests/test_cogr_wave0_sealed_env.py` | Wave 0 sealed-env regression tests: `evaluate` twice raises, `observe` view carries no sealed fields, `IntegrityAudit` flags policies that read `role` / `utility` / `_answer_key`, and a clean policy passes. |
| `experiments/concern_gated_retrieval_e2/wave0/template_split.py` | Calibration/confirmatory family-split guard (`TemplateBucket`, `TemplateRegistry`, `TemplateRow`, `assert_calibration_only`, `stable_template_id`, `LeakageError`). `load()` default-denies confirmatory rows; `allow_confirmation=True` requires the caller-side `COGR_WAVE0_CONFIRMATORY_RUN` env token in addition. Template ids are deterministic in `(family, seed, bucket)`. The immutable bucket tag survives `dataclasses.replace` and the runtime tripwire refuses any non-calibration row at calibration entry points. |
| `tests/test_cogr_wave0_template_split.py` | Four unit tests for `template_split.py`: default surface is calibration-only, confirmatory surface requires the env token in addition to the flag, `LeakageError` fires on misuse (confirmation row, missing bucket, dict masquerade), and the bucket tag survives `dataclasses.replace` while remaining process-stable. |
| `experiments/concern_gated_retrieval_e2/wave0/concern_update.py` | Wave 0 exploratory concern-update learner. `LoggedProbePolicy` wraps a nomination policy in an epsilon-greedy exploration branch and writes a `ProbeReceipt` (`episode_id`, `candidate`, `selection_propensity`, `source_id`, `template_family_split`, `exploratory`) per selection whose propensity is the closed-form logging-policy probability of the recorded action. `update_concern(prior, receipts, outcomes, estimator)` takes an IPS or doubly-robust value estimate and applies a multiplicative (exponentiated) mirror-descent step on the non-negative concern-anchor weights; the DR baseline is a per-candidate mean of `SealedOutcome.realized_reward`. A single-source aggregate influence bound (`max_source_influence`, default `1.0`) is applied per update before the mirror step so no single `source_id` can move any anchor's weight by more than a factor of `exp(eta * max_source_influence)`; this is the poisoning guard documented in `wave0/PREREGISTRATION.md` §4.4. Refuses confirmatory receipts at calibration entry points, never touches the sealed `role`/`utility`/`_answer_key` fields, and does not fork PPR or the pilot's rarity-corrected fusion. Wave 0 is exploratory only — the wave's promotable claim is calibration and family scaffolding + wrong-prior initialization, not concern recovery. |
| `experiments/concern_gated_retrieval_e2/wave0/families/__init__.py` | Subpackage marker for the three Wave 0 procedural family generators. Documents the shared `generate_episode(seed, bucket, holdout=None) -> EpisodeSpec` public API and the Wave 0 style boundary (no learned memory / concern-recovery / meaning / selfhood claims). |
| `experiments/concern_gated_retrieval_e2/wave0/families/maintenance_fault.py` | `maintenance_fault` family generator: 16 calibration (`MF-C-01`..`MF-C-16`) + 32 confirmatory (`MF-X-01`..`MF-X-32`) templates over four paraphrase families (`system_logs`, `sensor_stream`, `warning_ledger`, `diagnostic_tape`). `generate_episode` picks a template deterministically from `(bucket, seed, holdout)`, emits a sealed `EpisodeSpec` whose off-context load-bearing node is the buried early observation, with context-only sensor-noise, chronic critical-alert alarm, and neutral maintenance-log distractors; the wrong prior (`W_ALARM_INIT=1.0`, `W_COMMIT_INIT=0.05`, `W_UNIFORM_INIT=0.20`) overweights the alarm region and suppresses the load-bearing region; utility differential is capped at `MAX_UTILITY_DIFF=0.6` for non-ceiling. Refuses out-of-range seeds and unknown paraphrase-family holdouts. |
| `tests/test_cogr_wave0_maintenance_fault.py` | Wave 0 `maintenance_fault` family tests: at-least-30 template registry shape, determinism given `(seed, bucket, holdout)`, cross-seed disjoint candidate namespaces, adversarial wrong prior (alarm inflated, commitment suppressed, uniform baseline present), off-context load-bearing target, non-ceiling utility-differential cap, holdout excludes named paraphrase family, unknown holdout refused, calibration/confirmatory seed-range refusal, non-int seed and bad bucket rejected. |
| `experiments/concern_gated_retrieval_e2/wave0/families/resource_constrained.py` | `resource_constrained` family generator: 32 calibration (`RC-C-01`..`RC-C-32`; seeds `100_200`..`100_231`) plus a 32-seed reserved confirmatory block (`RC-X-01`..`RC-X-32`; seeds `200_200`..`200_231`) over a bipartite ledger surface (`DEFAULT_GRAPH_SIZE=16` left-obligation / right-action nodes reused from `graph_learn.build_withheld_graph`). `generate_episode(seed, bucket, holdout=None)` deterministically assigns eight roles (load-bearing prior obligation, alarm, context-only alternate action, care-only global obligation, two neutral policy notes, two active pending actions) via a per-seed layout PRNG and returns a sealed `EpisodeSpec` at `DEFAULT_BUDGET=2`. The wrong prior (`W_ALARM_INIT=1.0`, `W_COMMIT_SUPPRESSED_INIT=0.05`, `W_UNIFORM_INIT=0.5`) inflates the alarm region and suppresses the load-bearing obligation strictly below uniform, leaving the care-only global at uniform; utility magnitudes (`U_OBLIGATION=0.60`, `U_ALARM=0.20`, `U_CONTEXT_ALT=0.15`, `U_CARE_GLOBAL=0.10`, `U_NEUTRAL_NOTE=0.0`) keep the oracle differential ≤ 0.6 and the reward domain in `[-1, +1]` for non-ceiling. `calibration_slate()` returns the 32 calibration episodes in ascending seed order; `confirmatory_seeds()` declares the reserved Wave 1 seeds without permitting Wave 0 to touch them. Refuses out-of-range seeds and non-`TemplateBucket` inputs. |
| `tests/test_cogr_wave0_resource_constrained.py` | Wave 0 `resource_constrained` family tests: (1) slate size and shape — ≥ 30 calibration templates whose `family`, `template_family_split`, seeds, budget, and context/candidate disjointness are all valid and admissible to a calibration-mode `SealedEnvironment`; (2) adversarial wrong-prior misspecification — every template inflates the alarm at `W_ALARM_INIT`, suppresses the load-bearing obligation to `W_COMMIT_SUPPRESSED_INIT < W_UNIFORM_INIT`, and leaves at least one care-only global obligation at `W_UNIFORM_INIT`; (3) anti-ceiling holdout — a wrong-prior pass-through ranker always picks the alarm ahead of the obligation and its sealed reward is strictly ≥ 0.30 below the oracle policy on every calibration seed, oracle reward stays strictly below the `+1.0` reward-domain ceiling, and calibration and confirmatory seed ranges are disjoint (and inside the master `100_000..100_999` / `200_000..201_999` blocks). Bonus tests: `generate_episode` refuses confirmatory-range seeds in a calibration bucket and vice versa; `SealedEnvironment.evaluate` remains single-shot on this family. |
| `experiments/concern_gated_retrieval_e2/wave0/families/delayed_commitments.py` | `delayed_commitments` family generator: 16 calibration (`DC-C-01`..`DC-C-16`) + 32 confirmatory (`DC-X-01`..`DC-X-32`) templates over four paraphrase families (`partner_birthday`, `wedding_anniversary`, `child_school_deadline`, `friend_host_night`) on a `GRAPH_SIZE=32` withheld timeline chain from `graph_learn.build_withheld_graph`. `generate_episode(seed, bucket, holdout=None)` picks a template deterministically from `(bucket, seed, holdout)` and emits a sealed `EpisodeSpec` at `DEFAULT_BUDGET=2` whose load-bearing off-context commitment lives in a commitment zone far from the active-context zone along the chain; distractors are calendar-trivia (context-only), current-day trending news (care-only alarm), commitment-neighbor lookalikes, and neutral filler drawn from a family-local role vocabulary disjoint from the L0 pilot's. The wrong prior (`W_ALARM_INIT=1.0`, `W_COMMIT_INIT=0.05`, `W_UNIFORM_INIT=0.20`) inflates the alarm and suppresses the load-bearing commitment; utility magnitudes (`U_LOAD_BEARING=0.55`, `U_ALARM=0.15`, `U_CONTEXT_DISTRACTOR=0.10`, `U_COMMITMENT_NEIGHBOR=0.10`, `U_NEUTRAL=0.0`) plus a per-episode `MAX_UTILITY_DIFF=0.6` clamp keep the reward domain in `[-1, +1]` and non-ceiling. Holdout accepts either a paraphrase-family name in `PARAPHRASE_FAMILIES` or a whole template id in `TEMPLATE_IDS`; unknown holdouts are refused. `calibration_template_ids()` / `confirmatory_template_ids()` expose the ordered id tuples. Refuses out-of-range seeds and non-`TemplateBucket` inputs. |
| `tests/test_cogr_wave0_delayed_commitments.py` | Wave 0 `delayed_commitments` family tests: registry shape (≥ 30 templates, calibration/confirmatory id disjointness, paraphrase-family coverage), determinism given `(seed, bucket, holdout)`, cross-seed candidate-namespace disjointness, calibration and confirmatory seed-range refusal, bucket tag matches split literal, paraphrase-family holdout excludes the named family across 200 seeds, whole-template holdout excludes the named template id, unknown holdout rejected, sealed-env `EpisodeContext` carries no role / utility / answer key, wrong prior matches PREREGISTRATION.md §5 magnitudes, and non-trivial distractor difficulty — a plain context-only PPR baseline and a wrong-prior care-only PPR baseline on the fixed withheld geometry each miss on ≥ 10% of the first 100 calibration seeds. |
| `experiments/concern_gated_retrieval_e2/wave0/baselines.py` | Wave 0 baseline slate for PREREGISTRATION.md §7: `no_retrieval`, `random_rank`, `freq_only` (rarity-inverse via `graph_learn.rarity_scores` over a fixed withheld-graph batch), `context_only_ppr`, `care_only_ppr`, `additive_ppr`, `multiplicative_ppr` (rarity-corrected Hadamard product — the **candidate mechanism** for Wave 1), `embedding_similarity` (frozen `all-MiniLM-L6-v2` when importable; otherwise deterministic SHA-256 pseudo-embedding recorded in `EMBEDDING_PROVENANCE`), `learned_one_stage` (frozen single-hidden-layer MLP over eight policy-visible per-candidate features; `learned_one_stage_parameter_count()` sits within 5% of the declared `CANDIDATE_MECHANISM_PARAM_COUNT = 128`), `info_matched_value` / `info_matched_priority` / `info_matched_recency` (generic value-, task-priority-, and recency-second-signal proxies computed only from `context.care_anchors`), `wrong_agent_concern` (concern anchors permuted deterministically per episode, then run through the same multiplicative fusion), and `oracle_ceiling` (CEILING-ONLY; reads a pre-registered per-episode answer key via `register_oracle_answer`, is flagged `is_ceiling_only=True`, and is refused by `promotion_admit`). Every rank callable is passed through `IntegrityAudit.assert_clean` at module import so a leaky baseline fails CI at collection time. `match_budget(baseline, target_flops)` returns a wrapper that reports and enforces matched compute against the candidate mechanism's `CANDIDATE_MECHANISM_FLOPS` estimate; overruns raise `BudgetExceeded`. Imports `WeightedGraph` and `personalized_pagerank` from the frozen L0 pilot and does not fork them. |
| `tests/test_cogr_wave0_baselines.py` | Wave 0 baseline slate regression tests: (1) every baseline in `BASELINES` is deterministic on a fixed calibration seed and returns only candidate-set members with no duplicates; (2) `oracle_ceiling` is flagged `is_ceiling_only=True` and refused by `promotion_admit` with a `PromotionRefused` matching "CEILING-ONLY", while every other baseline is admitted unchanged; (3) `wrong_agent_concern` retrieves the load-bearing target strictly less often than `multiplicative_ppr` over a 40-seed `delayed_commitments` calibration window; (4) `learned_one_stage_parameter_count()` sits within 5% of the declared `CANDIDATE_MECHANISM_PARAM_COUNT`. |
| `experiments/concern_gated_retrieval_e2/wave0/calibrate.py` | Wave 0 calibration orchestrator. `build_cells(...)` produces the sweep grid across `family` (three procedural families), `distractor_density` in `{light, medium, heavy}` (disjoint calibration-seed slices per family), `retrieval_budget` (default `{1, 2}`), and `epsilon` (LoggedProbePolicy coverage side-channel, default `0.05`). `execute_cell(cell_dict)` runs one cell: for every seed it generates a sealed `EpisodeSpec`, registers the oracle answer key on the `oracle_ceiling` module registry, and runs every baseline in `BASELINES` against a **fresh** single-shot `SealedEnvironment`, returning one row per `(seed, baseline)` plus a `LoggedProbePolicy` exploration-coverage receipt. `summarize_rows(rows)` reduces baseline-level rows into the PREREGISTRATION.md §8.1 threshold-row shape per family (`mu_hat_multiplicative`, `sigma_hat_multiplicative`, `mu_hat_best_matched`, `sigma_hat_best_matched`, `mu_hat_oracle_ceiling`, `headroom_to_ceiling`, `delta_thresh_L1 = max(2 * sigma_hat_best_matched, 0.10 * headroom_to_ceiling)`) plus a non-ceiling integrity flag sized against §9.2's `0.05 * BOUNDED_REWARD_RANGE` tolerance. `estimate_cost_usd(n_cells)` returns a conservative Modal-cost estimate (cells × `1800s` × L4 `$0.80/hr` rate) and a wall-clock-bounded figure computed against `max_containers=10`; the CLI refuses to dispatch when the conservative figure exceeds the `$10.0` hard cap. Public receipt path: `experiments/concern_gated_retrieval_e2/wave0/results/calibration_summary.json`. Reuses `WeightedGraph` / `personalized_pagerank` transitively via `baselines.py`; imports the sealed-env types and `LoggedProbePolicy` directly. |
| `experiments/concern_gated_retrieval_e2/wave0/modal_l4_sweep.py` | Wave 0 Modal L4 fan-out. `modal.App` named `research-derived-cogr-wave0-calibration`. The `run_cell` function is decorated with `gpu="L4"`, `timeout=1800`, `cpu=4`, `memory=16384`, `max_containers=10`, `single_use_containers=True`, and `retries=1` per the build brief. Image is `debian_slim` py3.12 with `numpy`, `torch`, `sentence-transformers`, and `uv`; local project is added to `/root/project` via `add_local_dir(".")`. The local entrypoint calls `calibrate.build_cells(...)`, prints the plan plus a conservative cost estimate, refuses to dispatch if the estimate exceeds `$10.0`, and otherwise fans `run_cell.map(cell_args)` out across the cells and writes the merged manifest to `artifacts/cogr_wave0/calibration.json` via `calibrate.write_calibration_summary`. Deploy is done outside this module by `scripts/deploy_and_run_cogr_wave0.sh`. |
| `experiments/concern_gated_retrieval_e2/wave0/results/.gitkeep` | Preserves the `results/` directory in git so `calibrate.py`'s default `calibration_summary.json` output path exists before the first run. |
| `scripts/deploy_and_run_cogr_wave0.sh` | Wrapper that (1) `modal deploy`s `wave0/modal_l4_sweep.py` under Doppler scope `/Users/jawaun/superoptimizers`, and (2) `modal run`s it with `--preset calibration --out artifacts/cogr_wave0/calibration.json`. Supports `--preset`, `--out`, and `--dry-run`; enforces the "deploy before spawn" rule that the wave brief requires. |
| `papers/concern_gated_retrieval_wave0/figures/build_figures.py` | Wave 0 report figure builder. Emits six figures (`fig1_pipeline`, `fig2_wrong_prior`, `fig3_family_matrix`, `fig4_baseline_slate`, `fig5_leakage_barriers`, `fig6_calibration_grid`) as `_dark.png` / `_light.png` pairs at 8×5 in @ 200 dpi using a Dither-Kit-inspired retro palette, matplotlib hatch-pattern overlays as an ordered-dither approximation, monospace typography, and letter-spaced UPPERCASE titles. Loads `experiments/concern_gated_retrieval_e2/wave0/results/calibration_summary.json` when present; `fig6` annotates each `(family, budget)` cell with `sigma_hat_multiplicative` and per-cell `exploration_fraction`. When the JSON is absent every figure stamps a "placeholder" watermark and `fig6` swaps to "placeholder — replaced by Modal run". Idempotent and deterministic; imports no evaluator-only field. |
| `papers/concern_gated_retrieval_wave0/figures/PLACEHOLDER_NOTICE.md` | Notice covering the committed Wave 0 figure PNGs: labels each figure's structural vs numeric content, names the figures placeholders until the Modal calibration run signs `PREREGISTRATION.md`, and documents how to regenerate. |

#### 3.3.5c `concern_gated_retrieval_e2/wave1a` — COGR-E2a concern-recovery screen scaffold

The Wave 1a subpackage (`experiments/concern_gated_retrieval_e2/wave1a/`)
hosts the COGR-E2a concern-recovery screen defined in
`docs/concern_gated_retrieval_research_program.md` § "COGR-E2a — concern-
recovery screen" and preregistered in
`experiments/concern_gated_retrieval_e2/wave1a/PREREGISTRATION.md`. Wave
1a is a **screen** for the concern-update rule under the Wave 0
adversarially wrong prior. It CAN reject the rule; it CANNOT establish
learned memory geometry, an L1 dual-source-retrieval claim, or an L2
history-derived-concern-recovery claim (those are Wave 1b / COGR-E2b
objects). Sweep, Modal L4 fan-out, and the paired-seed variance
estimator arrive in follow-up build tasks; the files below are
scaffolding for that follow-up work.

| Path | What it does |
|---|---|
| `experiments/concern_gated_retrieval_e2/wave1a/conditions.py` | Enum-like registry of the six Wave 1a conditions declared in `PREREGISTRATION.md` §4: `FROZEN_WRONG` (baseline; no update rule; promotable), `ONLINE_IPS` and `ONLINE_DR` (candidate variants; `update_concern` estimator tag `"ips"` / `"dr"`; promotable), `ORACLE_CEILING` (diagnostic ceiling; `promotion_admit_condition` refuses with `PromotionRefused`), `SHUFFLED` (anchor-label permutation control; promotable), and `WRONG_AGENT` (different-agent-history control; promotable). Each `Condition` carries a name, an evaluator-side `initial_concern_factory(EpisodeSpec) -> dict[str, float]`, an `update_rule` in `{None, "ips", "dr"}`, and a `promotion_eligible` flag; `factory_reads_sealed_fields` tags the two factories (oracle, wrong-agent) whose evaluator-side reads are legitimate and must not be run through `IntegrityAudit`. Public helpers: `CONDITIONS` (frozen registry), `condition_by_name`, `promotable_conditions`, `promotion_admit_condition`, and `PromotionRefused`. |
| `experiments/concern_gated_retrieval_e2/wave1a/coverage_audit.py` | Wave 1a coverage-audit scaffold for `PREREGISTRATION.md` §5.1. `propensity_weighted_coverage(receipts, target_region)` returns `( Σ 1[r.candidate ∈ TCR(f)] / r.selection_propensity ) / len(receipts)` per the frozen preregistration formula. `audit_coverage(receipts, target_region, floor=DEFAULT_COVERAGE_FLOOR)` returns a `CoverageVerdict(passed, coverage, floor, n_receipts, n_hits)` on pass and raises `CoverageAuditFailure` on floor breach, carrying the numeric verdict on `.verdict`. Empty cells are treated as failures; negative floors are rejected. `DEFAULT_COVERAGE_FLOOR = 0.01` mirrors the preregistration. |
| `experiments/concern_gated_retrieval_e2/wave1a/e2a_runner.py` | Wave 1a per-episode runner. `run_e2a_episode(episode, condition, rng_seed, *, nomination_factory=None, epsilon=DEFAULT_EPSILON, source_id="trusted") -> E2aEpisodeResult` composes the frozen Wave 0 primitives: (1) runs the condition's evaluator-side `initial_concern_factory`, (2) audits the policy-side nomination callable with `IntegrityAudit.assert_clean`, (3) wraps it in `LoggedProbePolicy(epsilon)`, (4) constructs a `SealedEnvironment` in the mode matching the episode's `template_family_split`, (5) draws one logged probe with a caller-driven `random.Random(rng_seed)`, (6) submits a single-shot `RetrievalChoice` and captures the `SealedOutcome`, and (7) if the condition has an `update_rule`, calls Wave 0's `update_concern`. `E2aEpisodeResult` carries `episode_id`, `condition_name`, `family`, `template_family_split`, `rng_seed`, `concern_before`, `concern_after` (or `None` for frozen conditions), the `ProbeReceipt`, the `RetrievalChoice`, the `SealedOutcome`, and the `sealed_env_evaluate_calls` regression counter (`1` on success). Scaffold `_concern_biased_ranker` supplies a concern-weight nomination policy the sweep runner will replace with the Wave 0 rarity-corrected multiplicative fusion. |
| `experiments/concern_gated_retrieval_e2/wave1a/controls.py` | Wave 1a fixed-prior control-runner batch layer. Four public entry points — `run_frozen_wrong(family, seeds)` (C1 baseline), `run_oracle_ceiling(family, seeds)` (C3 diagnostic ceiling; refused by `promotion_admit_condition` at the promotion boundary but still executed here for the ceiling-headroom receipt), `run_shuffled(family, seeds)` (C4 anchor-permutation control), `run_wrong_agent(family, seeds)` (C5 different-agent-history control) — each returning a `ControlTrace(condition_name, family, seeds, results, mean_realized_reward, sealed_env_evaluate_calls, promotion_eligible)`. Runners dispatch through `_FAMILY_GENERATORS` (Wave 0's `delayed_commitments` / `maintenance_fault` / `resource_constrained` `generate_episode`, always `TemplateBucket.CONFIRMATION`), lock `rng_seed = seed` on the `LoggedProbePolicy` draw so a `(family, seed)` pair produces a byte-identical trace across processes, and delegate per-episode work to `run_e2a_episode`. `CONTROL_CONDITION_NAMES` exposes the four control names in canonical order. The two on-line-learned variants (`ONLINE_IPS`, `ONLINE_DR`) are not run here — they live on a sibling sweep runner. |
| `tests/test_cogr_wave1a_conditions.py` | Wave 1a condition-registry regression tests: the six declared conditions are registered exactly once; five are promotable and the oracle is the sole ceiling; `update_rule` tags match the preregistration; `condition_by_name` round-trips; every factory produces a non-negative numeric prior on the observed candidate set; `promotion_admit_condition` refuses the oracle with `PromotionRefused` and admits the other five. |
| `tests/test_cogr_wave1a_coverage_audit.py` | Wave 1a coverage-audit tests: closed-form check of `propensity_weighted_coverage` against a hand-computed reference; a passing cell returns a `CoverageVerdict(passed=True)` with the coverage / floor / receipt counts on the dataclass; a below-floor cell raises `CoverageAuditFailure` and the exception's `.verdict` carries the numeric verdict; an empty cell is treated as a failure; negative floors and non-`ProbeReceipt` batches are rejected early. |
| `tests/test_cogr_wave1a_e2a_runner.py` | Wave 1a runner tests: one confirmatory `delayed_commitments` episode under `FROZEN_WRONG` yields a well-formed `E2aEpisodeResult` (`concern_after is None`); `ONLINE_IPS` populates `concern_after` with the same anchor set as `concern_before`; the runner reports `sealed_env_evaluate_calls == 1` and an independent Wave 0 `SealedEnvironment` still refuses a second `evaluate()` call with `SealedEvaluationError`; the oracle is refused by `promotion_admit_condition` with `PromotionRefused` but still runs for the diagnostic ceiling receipt. |
| `tests/test_cogr_wave1a_controls.py` | Wave 1a control-runner regression tests, one per fixed-prior condition. Each test drives its runner (`run_frozen_wrong` / `run_oracle_ceiling` / `run_shuffled` / `run_wrong_agent`) twice on the same `(family, seeds)` and asserts (1) the two `ControlTrace` values are equal on every field (byte-stable determinism), (2) the trace's `condition_name`, `family`, `seeds`, `results`, and `sealed_env_evaluate_calls` are well-formed and align with the input seeds, and (3) `promotion_eligible` matches the condition's registered flag. The oracle test additionally verifies `promotion_admit_condition(CONDITIONS[ORACLE_CEILING])` raises `PromotionRefused` — the ceiling still executes on the runner surface but is refused at the promotion boundary. |
| `experiments/concern_gated_retrieval_e2/wave1a/modal_l4_sweep.py` | Wave 1a Modal L4 fan-out for the E2a confirmatory sweep. `modal.App` named `research-derived-cogr-wave1a-e2a`. `run_cell` is decorated with `gpu="L4"`, `timeout=1800`, `cpu=4`, `memory=16384`, `max_containers=32` (Wave 1a §7 explicit authorization above Wave 0's `10` ceiling), `single_use_containers=True`, and `retries=1`. Image mirrors Wave 0 (`debian_slim` py3.12 + numpy / torch / sentence-transformers / uv) and ships the repo into `/root/project` via `add_local_dir(".")`. `build_cells(...)` returns one `CellPlan(family, seeds, cell_id)` per family covering the family's confirmatory seed tuple — 300 seeds each for `delayed_commitments` (`200000..200299`) and `maintenance_fault` (`200300..200599`) per PREREGISTRATION.md §7, and 32 seeds for `resource_constrained` clamped to the Wave 0 generator's actual `confirmatory_seeds()` (`200200..200231`) because the §7 slice `200600..200899` is outside that family's accepted range (documented scaffold gap). `execute_cell(cell_dict)` walks the seeds sequentially and, for each seed, runs `run_e2a_episode` on 10 arms: the seven canonical specificity slots (`frozen_wrong`, `online_learned_ips`, `online_learned_dr`, `info_matched_value`, `info_matched_priority`, `info_matched_recency`, and the ranker-level `wrong_agent` comparator) plus three condition-only arms (`condition::shuffled`, `condition::wrong_agent`, `condition::oracle_ceiling`) whose receipts feed the coverage audit and the diagnostic ceiling receipt. The on-line-learned variants carry a running concern-anchor prior across seeds; each seed updates it via `_apply_online_update`, a Wave 1a-owned helper that mirrors `wave0.concern_update.update_concern`'s IPS/DR math for a single-receipt confirmatory batch (Wave 0's helper refuses confirmatory receipts at its calibration entry point; PREREGISTRATION.md §5.2 explicitly authorizes the confirmatory sweep's confirmatory-batch use, so the math is inlined here without editing any Wave 0 file). `estimate_cost_usd(n_cells)` returns a conservative Modal-cost estimate (cells × 1800s × L4 `$0.80/hr`) and a wall-clock-bounded figure computed against `max_containers=32`; the local entrypoint refuses to dispatch when the conservative figure exceeds the `$20` hard cap (Wave 1a build brief). Writes the raw per-arm rows to `artifacts/cogr_wave1a/e2a_rows.json`. Deploy is done outside this module by `scripts/deploy_and_run_cogr_wave1a.sh`. |
| `experiments/concern_gated_retrieval_e2/wave1a/run_confirmatory.py` | Wave 1a confirmatory aggregator. Loads the raw Modal receipt at `artifacts/cogr_wave1a/e2a_rows.json`, buckets rows by `(family, seed)`, builds `SpecificityRow` objects with all seven canonical arm rewards, composes each family's rows into a `SpecificityReport`, and scores the reports through `promotion_harness.score_e2a_all` against `WAVE1A_PREREGISTERED_THRESHOLDS`. Reconstructs a `ProbeReceipt` from each row in `COVERAGE_AUDIT_ARMS` (the four receipt-producing conditions `C2a/C2b/C4/C5`), resolves the per-family `TCR(f)` by unioning the sealed `EpisodeSpec._answer_key` across the family's episodes (evaluator-side, never enters a policy callable), and runs `coverage_audit.audit_coverage(..., floor=DEFAULT_COVERAGE_FLOOR)` per `(family, arm)` cell. Writes the screen verdict to `experiments/concern_gated_retrieval_e2/wave1a/results/verdict.json` carrying per-family specificity contrasts, coverage receipts, promotion verdicts, diagnostic oracle-ceiling means, and the aggregate non-compensatory decision (`PASS` iff every family PASSes and every coverage audit passes; `KILL` with the enumerated per-gate kill reasons otherwise). CLI exit code is `0` on `PASS`, `2` on `KILL`. |
| `scripts/deploy_and_run_cogr_wave1a.sh` | Wrapper that (1) `modal deploy`s `wave1a/modal_l4_sweep.py` under Doppler scope `/Users/jawaun/superoptimizers`, (2) `modal run`s it with `--preset confirmatory --out artifacts/cogr_wave1a/e2a_rows.json` (sets `COGR_WAVE0_CONFIRMATORY_RUN=1` so the Wave 0 template-split guard admits the confirmatory pool while calibration seeds `100000..100999` remain refused), and (3) invokes `run_confirmatory.py` to aggregate the raw receipt into `experiments/concern_gated_retrieval_e2/wave1a/results/verdict.json`. Supports `--preset`, `--out`, `--verdict`, `--dry-run` (deploy-only, no dispatch), `--smoke` (tiny 4-seed slice for a fast round-trip), and `--no-aggregate`. Enforces the deploy-before-spawn rule. |

#### 3.3.6 Related reengagement packages

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
| `gen_provenance.py` | Validate registries, resolve structured primary-run bindings from the contract registry, regenerate all experiment `PROVENANCE.md` files + `docs/verification.{md,json}` + site mirror; `--check` compares expected bytes without writing; legacy packages still use labeled heuristic extraction | In: 57 experiment dirs + claim/evidence/contract registries; excludes `experiments/common` |
| `validate_evidence_registry.py` | Validate canonical evidence IDs, gate statuses, artifact refs, and supersession shape | `docs/program_evidence_registry.json` |
| `validate_claim_registry.py` | Validate exact claim shape/tiers/states and bidirectional claim↔evidence edges | Reads `docs/claim_registry.json` + `docs/program_evidence_registry.json`; never writes either |
| `validate_experiment_manifest.py` | Enforce the authoritative package-contract registry (57 = 9 structured + 48 legacy), then discover and dependency-free validate every v1 experiment-package contract; every registered run `manifest_path` must be an `experiment_manifest.json` inside its publication package and validate as v1 by content; run records may declare `preregistration_digest` + `preregistration_path` (SHA-256 of a tracked pre-reg file, content-verified) and `producing_agent` (`identity` + `session_ref`); when the registry sets `preregistration_policy.required_after_run_date`, any run whose `run_id` ends with a date on or after the cutoff must supply all three | Reads `docs/experiment_contract_registry.json` and `experiments/**/experiment_manifest.json`; portable contracts in `schemas/experiment_contract_registry.schema.json` and `schemas/experiment_manifest.schema.json` |
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
| `build_cogr_wave0_pdf.py` | Concern-Gated Retrieval Wave 0 report PDF. Reads `papers/concern_gated_retrieval_wave0/paper.md` (produced upstream by report-draft) and embeds the six dark-mode figures referenced by the markdown (produced upstream by report-figures). Uses a monospace body font (DejaVu Sans Mono when the matplotlib TTF is available; otherwise ReportLab's built-in Courier). Deterministic (`rl_config.invariant = True`). Writes `papers/concern_gated_retrieval_wave0/paper.pdf` and `papers/pdf/concern_gated_retrieval_wave0.pdf`; mirrors to `/Users/jawaun/Metaphysics of Intelligence/Concern_Gated_Retrieval_Wave0_2026_07_23.pdf` only when that parent directory already exists (never creates it). |
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

- [`docs/papers/grounded_harness_ct_preprint_2026-07-20.md`](papers/grounded_harness_ct_preprint_2026-07-20.md) (+ PDF `papers/33_Grounded_Harness_CT_NameFree_2026_07_20.pdf`, brief PDF `papers/33b_Grounded_Harness_Brief_2026_07_20.pdf`)
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

### 6.2b `sites/envelope_guard/` — Envelope Guard

| Item | Detail |
|---|---|
| Role | Interactive Constraint Transport product demo + research explainer |
| Stack | Whitelist static Node server; browser port of `condition_policy.py` in `policy.js` |
| Served | `index.html`, `styles.css`, `app.js`, `policy.js`, `scenarios.json`, `assets/mark.svg` |
| Port | `PORT` (default 3020) |
| Product | Compare soft-prompt vs external envelope guards; emit audit receipts |
| Domain | `https://envelope-guard-production.up.railway.app` |
| Deploy | Railway project `envelope-guard` via `.github/workflows/railway-deploy.yml` |
| Tests | `npm test` → Node test runner on `tests/policy.test.js` |

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
| `.github/workflows/railway-deploy.yml` | Deploy atlas + Inquiry landing + Envelope Guard on `main` |
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
