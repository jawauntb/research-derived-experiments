# Module Explainer & Package Catalog

Catalog of packages, modules, major scripts, test areas, and documentation in
**research-derived-experiments**. Companion: [system_design.md](system_design.md).
Update both when the codebase changes meaningfully (see root `AGENTS.md`).

---

## 1. Repo map (top level)

| Path | Responsibility |
|---|---|
| `experiments/` | Research harnesses, Modal sweeps, committed `results/`, `PROVENANCE.md` (49 dirs) |
| `papers/` | Paper sources (`paper.md`), figures, shareable PDFs |
| `scripts/` | ~80 ops scripts: quality, provenance, PDF/figure builders, summarizers |
| `tests/` | Root `unittest` suite for core experiment logic |
| `docs/` | Design docs, verification, handoffs, plans, reviews, solutions |
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
| `pyproject.toml` | Python ≥3.12, Ruff, ty excludes — **no dependency lock** |

---

## 2. Script / test / doc map (quick lookup)

### 2.1 “I want to…”

| Goal | Start here |
|---|---|
| Understand how the system runs | [system_design.md](system_design.md) |
| Find an experiment’s purpose & modules | §3 below + `experiments/<name>/PROVENANCE.md` |
| Reproduce or get the dispatch command | `python scripts/regen.py list` / `regen.py <name>` |
| Refresh provenance index | `python scripts/gen_provenance.py` |
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
| `test_world_responds_suite_c*.py` (5 files) | Suite C reengagement + neural transfer + teacher-free |
| `test_structure_compatible_*.py` (4 files) | SCG suite, row ledgers, semantic selection |
| `test_gridcell_conference_evidence.py` | Paper A evidence export helpers |
| `test_paper_b_reproduce_stats.py` | Paper B CSV reproduction |
| `test_phase4_metaphysics.py`, `test_phase5_*.py`, `test_phase6_*.py` | Phase 4–6 harnesses |
| `test_gauge_fixed_concern_transport_*.py` | Gauge-fixed transport + PDF |
| `test_external_contact_p1_lora.py` | External-contact LoRA metrics |
| `test_semantic_concern_summary.py` | Semantic concern summarizer |
| `test_summarize_label_free_dose_response.py` | Label-free dose-response summarizer |
| `test_virtual_governor_stress_signal.py` | Virtual governor diagnostic |

```bash
uvx --python 3.12 --with torch --with numpy --with scikit-learn --with pytest \
  python -m unittest discover -s tests
# or: python3 scripts/run_quality_checks.py
```

### 2.3 Docs inventory

| Doc / group | Role |
|---|---|
| [system_design.md](system_design.md) | End-to-end design & operating model |
| [module_explainer.md](module_explainer.md) | This catalog |
| [verification.md](verification.md) / `verification.json` | Provenance index (auto-generated; 44 experiments) |
| [causally_grounded_agents_benchmark.md](causally_grounded_agents_benchmark.md) | Benchmark umbrella |
| [causally_grounded_agents_release_schema.md](causally_grounded_agents_release_schema.md) (+ `.json`) | Shared release schema |
| [causally_grounded_agents_next_gap.md](causally_grounded_agents_next_gap.md) | Suite C transfer gaps |
| [publication_sharing_map.md](publication_sharing_map.md) | What to share publicly |
| [paper_readiness.md](paper_readiness.md) | Paper readiness tracking |
| [discovery_regime_audit.md](discovery_regime_audit.md) | Regime audit ledger |
| [next_agent_modal_handoff.md](next_agent_modal_handoff.md) | Modal handoff |
| [railway-autodeploy.md](railway-autodeploy.md) | Railway deploy |
| [external_contact_preregistration.md](external_contact_preregistration.md) / [runbook](external_contact_runbook.md) | External-contact |
| [phase2_*.md](phase2_next_phase_research_handoff.md) | Phase 2 research handoffs (6 files) |
| [semantic_specificity.md](semantic_specificity.md) | Semantic specificity note |
| [neurophenom_project_approach_menu.md](neurophenom_project_approach_menu.md) | Neurophenom approach menu |
| [metaphysics_of_intelligence_reading_log.md](metaphysics_of_intelligence_reading_log.md) | Reading log |
| [gauge_fixed_concern_transport_experiment_audit.md](gauge_fixed_concern_transport_experiment_audit.md) | GFC audit |
| [metaphysics_complete_reading_notes_2026_07_09.md](metaphysics_complete_reading_notes_2026_07_09.md) | Full reading notes for every Metaphysics-of-Intelligence PDF/package listed 2026-07-09 (theorems, methods, findings, next directions); canonical copy also at `~/Metaphysics of Intelligence/COMPLETE_READING_NOTES_2026_07_09.md` |
| `docs/plans/` | 13 dated implementation plans — §8.1 |
| `docs/paper_reviews/` | 15 critical reviews — §8.2 |
| `docs/solutions/` | Architecture-pattern notes — §8.3 |

---

## 3. Experiment catalog

**Legend:** **P** = `PROVENANCE.md`, **B** = `BENCHMARK_CARD.md`, **R** = `README.md`, **res** = committed `results/`.

**Verification reconciliation:** 49 on disk, 44 in `docs/verification.json`.
Missing from manifest: `gauge_fixed_concern_transport`, `phase4_metaphysics`,
`phase5_external_validity`, `phase6_real_model_validation`,
`virtual_governor_stress_signal`.

**Custom (hand-maintained) provenance:** `structure_compatible_generalization`,
`gauge_fixed_concern_transport`, `phase4_metaphysics`, `phase5_external_validity`,
`phase6_real_model_validation`. **No provenance yet:** `virtual_governor_stress_signal`.

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
| `suite_c_reengagement.py` | Deterministic Suite C re-engagement (silence/anxiety/false-calm/cost) |
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

#### 3.3.3 Related reengagement packages

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
| `external_contact` | `modal_p1_pythia_weakness.py`, `modal_p1_pythia_lora.py`, `p1_lora_metrics.py` | LoRA run does not pass P1; hard-kills external-transfer threshold |
| `gauge_fixed_concern_transport` | `core.py`, `budget.py`, `summarize.py`, `modal_l4_suite.py` | Custom P; **not** in verification.json; smoke: `python -m experiments.gauge_fixed_concern_transport.core --preset smoke` |
| `phase4_metaphysics` | `core.py`, `summarize.py`, `modal_l4_suite.py` | Custom P; seven cheap parallel diagnostics |
| `phase5_external_validity` | `core.py`, `budget.py`, `summarize.py`, `modal_l4_suite.py` | Custom P; transport toward foundation-model proxies |
| `phase6_real_model_validation` | `core.py`, `real_models.py`, `budget.py`, `summarize.py`, `modal_l4_suite.py` | Custom P; public decoder LMs under predeclared gates |
| `virtual_governor_stress_signal` | `core.py`, `summarize.py`, `modal_l4_sweep.py` | README + res; **no** PROVENANCE; not in verification.json |

### 3.6 Experiment conventions

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
| `gen_provenance.py` | Regenerate all auto `PROVENANCE.md` + `docs/verification.{md,json}` + site mirror | In: experiment dirs |
| `regen.py` | List/reproduce experiments or print documented Modal commands | `list`, `<name>`, `--deps` |
| `run_quality_checks.py` | unittest → compileall → publication_guard → ruff → ty (uvx 3.12) | Exit code |
| `publication_guard.py` | Block tracked secrets, forbidden paths, oversized files | Exit code |
| `env_probe.py` | Report env var presence/length only | `--json` |

### 4.2 PDF toolkit & builders

| Script | Purpose |
|---|---|
| `paperkit.py` | Shared reportlab/matplotlib PDF helpers (library) |
| `render_paper_pdf.py` | Markdown → PDF via markdown-pdf (`--in`, `--out`, `--title`, …) |
| `build_weakness_pdf.py` | Flagship weakness→OOD PDF |
| `build_gridcell_pdf.py` | Paper A PDF |
| `build_paperB_pdf.py` | Paper B reward-deformation PDF |
| `build_effective_dimension_pdf.py` | Rate-distortion effective-dimension PDF |
| `build_concern_weighted_weakness_pdf.py` | Concern-weighted weakness note |
| `build_gauge_fixed_concern_transport_pdf.py` | GFC transport PDF |
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

### 4.3 Figure makers

| Script | Paper / figure set |
|---|---|
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
- Benchmark framing: `causally_grounded_agents_benchmark`, `weakness_invariance_neurips`
- Most §3.4 experiment names have a matching `papers/<name>/paper.md`

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
| `packages/ui` | Shared view models/tokens |

#### Apps

| App | Role | Key areas |
|---|---|---|
| `apps/desktop` | Electron main + renderer; SQLite source of truth | ingest, db, privacy, reports, notifications, security, activity, packaging |
| `apps/extension` | Chrome MV3 | service-worker, content telemetry, popup, localBridge |
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
| `.github/workflows/railway-deploy.yml` | Deploy atlas + Inquiry landing on `main` |
| `pyproject.toml` | Project meta, Ruff, ty excludes |
| `pyrightconfig.json` | Editor typecheck: missing imports silenced |
| `.gitignore` | Secrets, `artifacts/`, `data/`, reference full texts, caches |

---

## 8. Plans, paper reviews, solutions

### 8.1 `docs/plans/` (13)

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

When you add or materially change code:

1. Update [system_design.md](system_design.md) if runtime flow, deps, deploy, or capabilities/limitations change.
2. Update this file: experiment modules, script entries, test mapping, plans/reviews, or product surfaces.
3. Add/refresh `experiments/<name>/PROVENANCE.md` via `python scripts/gen_provenance.py` (or hand-edit custom cards).
4. Shrink the verification.json gap when phase/gauge/governor packages join the verified set.
5. Keep `experiments/README.md` active-track list honest.
6. Link new public-facing docs from root `README.md` when they are start-here material.

```bash
python scripts/gen_provenance.py
```
