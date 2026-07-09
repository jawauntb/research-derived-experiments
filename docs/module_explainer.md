# Module Explainer & Package Catalog

Catalog of packages, modules, major scripts, test areas, and documentation in
**research-derived-experiments**. Use this to find what lives where.

Companion: [system_design.md](system_design.md) (end-to-end operating model).
Update both when the codebase changes meaningfully (see root `AGENTS.md`).

---

## 1. Repo map (top level)

| Path | Responsibility |
|---|---|
| `experiments/` | Research harnesses, Modal sweeps, committed `results/`, `PROVENANCE.md` |
| `papers/` | Paper sources (`paper.md`), figures, shareable PDFs |
| `scripts/` | Quality, provenance, PDF/figure builders, summarizers, Modal paper tasks |
| `tests/` | Root `unittest` suite for core experiment logic |
| `docs/` | Design docs, verification, handoffs, plans, reviews, benchmark schema |
| `notes/` | Program-level research synthesis |
| `references/` | Public source list; local-only full texts (gitignored subdirs) |
| `formal/ontology-hs/` | Haskell typed ontology gate (Arc 2B) |
| `sites/` | Public static sites (atlas, Inquiry landing) |
| `apps/inquiry-black-box/` | Local-first Inquiry product monorepo |
| `coherence-testbench/` | Separate EEG/eyetrack Phase-0 GO/KILL project |
| `data/` | Gitignored raw data; committed exception `data/paper_b/` |
| `artifacts/` | Gitignored raw run outputs (never commit) |
| `README.md` | Human entrypoint: thesis, commands, env, checks |
| `TODO.md` | Active research ledger |
| `AGENTS.md` | Agent/contributor rules (incl. doc sync) |
| `pyproject.toml` | Python ≥3.12, Ruff, ty excludes — **no dependency lock** |

---

## 2. Script / test / doc map (quick lookup)

### 2.1 “I want to…”

| Goal | Start here |
|---|---|
| Understand how the system runs | [system_design.md](system_design.md) |
| Find an experiment’s purpose & entrypoint | §3 below + `experiments/<name>/PROVENANCE.md` |
| Reproduce or get the dispatch command | `python scripts/regen.py list` / `python scripts/regen.py <name>` |
| Refresh provenance index | `python scripts/gen_provenance.py` |
| Run the quality gate | `python3 scripts/run_quality_checks.py` |
| Check API/Modal env without leaking secrets | `python3 scripts/env_probe.py` |
| Public agent benchmark package | [causally_grounded_agents_benchmark.md](causally_grounded_agents_benchmark.md) |
| Modal operator handoff | [next_agent_modal_handoff.md](next_agent_modal_handoff.md) |
| Deploy atlas / Inquiry site | [railway-autodeploy.md](railway-autodeploy.md) |
| See what is verified | [verification.md](verification.md) / `verification.json` |

### 2.2 Scripts by role

| Role | Scripts |
|---|---|
| Provenance / regen | `gen_provenance.py`, `regen.py` |
| Quality / safety | `run_quality_checks.py`, `publication_guard.py`, `env_probe.py` |
| Shared PDF toolkit | `paperkit.py`, `render_paper_pdf.py` |
| PDF builders | `build_*_pdf.py`, `build_exhaustive_literature_audit*.py`, `build_external_citation_review*.py` |
| Figure makers | `make_*_figures.py`, `make_*_figure.py`, `_patch_figure_titles.py` |
| Summarizers | `summarize_*.py` |
| Modal paper tasks | `modal_*_paper_tasks.py` |
| Paper B / grid-cell helpers | `reproduce_paperB_stats.py`, `analyze_gridcell_conference_evidence.py` |
| Misc | `export_structure_compatible_artifacts.py`, `topk_ablation_stroke_benchmark.py` |

Experiment Modal sweeps live under `experiments/*/modal_*.py`, not `scripts/`.

### 2.3 Tests by area

| Test file(s) | Covers |
|---|---|
| `test_weakness_vs_simplicity.py` | Boolean weakness vs simplicity pilots |
| `test_symbolic_weakness.py`, `test_symbolic_families.py`, `test_symbolic_neural.py` | Flagship symbolic + neural weakness |
| `test_rotation_weakness.py` | Vision rotation weakness |
| `test_learned_symmetry.py`, `test_causal_validation.py` | Learned symmetry / causal validation |
| `test_concept_geometry_*.py` | Embedding concept geometry |
| `test_activation_geometry_*.py` (many) | Hidden-state probes, steering, patching, gates |
| `test_concerned_syntax.py` | Arc 2A concerned-syntax suite |
| `test_viable_computational_bodies.py` | Arc 2B body search / gates |
| `test_long_horizon_bottleneck.py` | Suite D/E long-horizon / tool eval |
| `test_world_responds_suite_c*.py` | Suite C reengagement + neural transfer |
| `test_structure_compatible_*.py` | Structure-compatible generalization / semantic selection |
| `test_gridcell_conference_evidence.py` | Paper A evidence export helpers |
| `test_paper_b_reproduce_stats.py` | Paper B CSV reproduction |
| `test_phase4_metaphysics.py`, `test_phase5_*.py`, `test_phase6_*.py` | Phase 4–6 harnesses |
| `test_gauge_fixed_concern_transport_*.py` | Gauge-fixed transport + PDF |
| `test_external_contact_p1_lora.py` | External-contact LoRA metrics |
| `test_semantic_concern_summary.py` | Semantic concern summarizer |
| `test_summarize_label_free_dose_response.py` | Label-free dose-response summarizer |
| `test_virtual_governor_stress_signal.py` | Virtual governor diagnostic |

Run: `uvx --python 3.12 --with torch --with numpy --with scikit-learn --with pytest python -m unittest discover -s tests`
(or the full wrapper `scripts/run_quality_checks.py`).

### 2.4 Docs by role

| Doc | Role |
|---|---|
| [system_design.md](system_design.md) | End-to-end design & operating model |
| [module_explainer.md](module_explainer.md) | This catalog |
| [verification.md](verification.md) / `verification.json` | Provenance index (auto-generated) |
| [causally_grounded_agents_benchmark.md](causally_grounded_agents_benchmark.md) | Benchmark umbrella |
| [causally_grounded_agents_release_schema.md](causally_grounded_agents_release_schema.md) (+ `.json`) | Shared release schema |
| [causally_grounded_agents_next_gap.md](causally_grounded_agents_next_gap.md) | Suite C transfer gaps |
| [publication_sharing_map.md](publication_sharing_map.md) | What to share publicly |
| [paper_readiness.md](paper_readiness.md) | Paper readiness tracking |
| [discovery_regime_audit.md](discovery_regime_audit.md) | Regime audit ledger |
| [next_agent_modal_handoff.md](next_agent_modal_handoff.md) | Modal handoff |
| [railway-autodeploy.md](railway-autodeploy.md) | Railway deploy |
| [external_contact_*.md](external_contact_runbook.md) | External-contact prereg + runbook |
| [phase2_*.md](phase2_next_phase_research_handoff.md) | Phase 2 research handoffs |
| [semantic_specificity.md](semantic_specificity.md) | Semantic specificity note |
| [neurophenom_project_approach_menu.md](neurophenom_project_approach_menu.md) | Neurophenom approach menu |
| [metaphysics_of_intelligence_reading_log.md](metaphysics_of_intelligence_reading_log.md) | Reading log |
| [gauge_fixed_concern_transport_experiment_audit.md](gauge_fixed_concern_transport_experiment_audit.md) | GFC experiment audit |
| `docs/plans/` | Dated implementation plans |
| `docs/paper_reviews/` | Critical reviews of papers |
| `docs/solutions/` | Architecture-pattern notes |

---

## 3. Experiment catalog

Legend: **P** = `PROVENANCE.md`, **B** = `BENCHMARK_CARD.md`, **R** = `README.md`, **res** = committed `results/`.

Universal dispatcher: `python scripts/regen.py <name>`.

### 3.1 Flagship / geometry / weakness

| Package | P/B/R/res | Purpose | Primary entrypoints |
|---|---|---|---|
| `weakness_vs_simplicity` | P R res | Toy Boolean worlds: weakness vs simplicity under memorizer / broad-negative stress | `experiment.py` |
| `symbolic_weakness` | P R res | Flagship: symmetry-compatible weakness beats loss/MDL/flatness for OOD | `python -m experiments.symbolic_weakness.benchmark`, `neural.py`, `modal_neural_sweep.py` |
| `rotation_weakness` | P res | Vision rotation-group weakness correlation | `python -m experiments.rotation_weakness.neural` |
| `learned_symmetry` | P res | Data-inferred equivariance predicts OOD without oracle symmetry | `sweep.py`, `modal_sweep.py`, `modal_causal_validation.py` |
| `neural_group_generator` | P res | Failed neural group-discovery approaches (pixels vs embeddings) | `generator.py`, `modal_rotated_mnist.py`, `modal_cluttered_mnist.py` |
| `grid_cell_weakness` | P R res | Path-integration RNNs: torus + OOD + reward deformation (Papers A/B) | `pilot.py`, `run_local.py`, `reward_deformation.py`, `modal_*` |
| `semantic_concern_geometry` | P R res | Non-spatial: moving semantic loss weights deforms geometry | `modal_semantic_concern_sweep.py` |
| `structure_compatible_generalization` | P R res | Compatibility with deployment transforms for OOD model selection | `core.py`, `run_suite.py`, `modal_l4_suite.py`, `summarize_*` |
| `weakness_temporal` | P | Early-checkpoint weakness as temporal OOD early-warning | `temporal.py` |
| `paraphrase_weakness` | P R res | Paraphrase-invariance of hidden states vs behavior | `modal_paraphrase_probe.py`, `summarize.py` |
| `concept_geometry` | P R res | Cross-domain concepts in embedding space | `openai_embedding_probe.py`, `paraphrase_stability_probe.py` |
| `activation_geometry` | P R res | Hidden-state bridges, steering, patching, label-free gates | many `modal_*.py` + probe modules |
| `passive_to_active` | P R res | Action coupling makes paraphrase geometry causally load-bearing | `modal_passive_to_active.py`, `modal_replication_sweep.py` |

### 3.2 Arc 2A / 2B

| Package | P/B/R/res | Purpose | Primary entrypoints |
|---|---|---|---|
| `concerned_syntax` | P R res | Causal constituency + concern-gated interventions | `python -m experiments.concerned_syntax.benchmark` + many variant modules / `modal_*` |
| `viable_computational_bodies` | P R res | Typed body evolution under viability + Haskell + syntax gates | `search.py`, `haskell_gate.py`, `program_body_search.py`, `modal_*` |

### 3.3 Causally grounded agents / long horizon

| Package | P/B/R/res | Purpose | Primary entrypoints |
|---|---|---|---|
| `world_responds` | P B res | Suite C: world shocks, reengagement, neural probe transfer | `suite_c_*.py`, `modal_suite_c_*.py`, `summarize_*` |
| `long_horizon_bottleneck` | P B R res | Moved-bottleneck memory + tool/JSON/agent long-horizon suite | `python -m experiments.long_horizon_bottleneck.eval`, `core.py`, many `modal_*` |
| `habituated_reengagement` | P | Decision-layer cooling after probes (Paper 23B) | `modal_habituated_reengagement_sweep.py` |
| `probe_value_reengagement` | P | Value-of-information re-probing | `modal_probe_value_reengagement_sweep.py` |

### 3.4 Maintained-concern / control stack (Modal-heavy paper family)

Most of these are thin packages: a Modal sweep + paper under `papers/<name>/`.

| Package | Purpose (one line) | Entrypoint |
|---|---|---|
| `valence_object_formation` | Supervised valence clusters by causal role | `modal_object_formation_sweep.py` |
| `homeostatic_objects` | Valence encoders → episodic homeostatic RL | `modal_homeostatic_sweep.py` |
| `concern_bootstrap` | ΔE aux + curriculum without optimal-action labels | `modal_concern_sweep.py` |
| `two_bottlenecks` | ΔE aux bootstraps XOR valence when decoupled from sparse PG | `modal_two_bottlenecks_sweep.py` |
| `planning_from_concern` | Model-based ΔE planning without optimal-action supervision | `modal_planning_sweep.py` |
| `planning_hardening` | Planning depends on latent geometry, not one reward axis | `modal_hardening_sweep.py` |
| `epistemic_exploration` | Margin-based epistemic exploration | `modal_exploration_sweep.py` |
| `exploration_diagnostics` | Skip-branch / exploration failure diagnostics | `modal_diagnostics_sweep.py` |
| `state_dependent_concern` | State-dependent concern under online homeostatic training | `modal_state_dependent_sweep.py` |
| `off_policy_state_coverage` | Off-policy ΔE for state-dependent concern | `modal_off_policy_sweep.py` |
| `regime_sensitive_de` | Regime-sensitive ΔE at E=0.5 boundary | `modal_regime_sensitive_sweep.py` |
| `autopoietic_control` | Viability buffer + repair + Law-of-the-Stack | `modal_autopoietic_sweep.py` |
| `allostatic_control` | Regulate + uncertainty-aware planner at concern boundaries | `modal_allostatic_sweep.py` |
| `ensemble_uncertainty` | Ensemble variance vs probe-value signals | `modal_ensemble_uncertainty_sweep.py` |
| `valence_tapestry` | Vector ΔV heads under shifted priorities | `modal_tapestry_sweep.py` |
| `first_order_self` | Self/world factorization for ΔE attribution | `modal_first_order_self_sweep.py` |
| `null_intervention` | Null actions break gauge symmetry via active anchoring | `modal_null_intervention_sweep.py` |
| `costly_null_probes` | Costly null-probe policies under viability pressure | `modal_costly_null_probes_sweep.py` |
| `online_identifying_interventions` | Probe-target bias in online identifying interventions | `modal_online_identifying_interventions_sweep.py` |
| `current_error_calibration` | Current error vs value-of-probing | `modal_current_error_calibration_sweep.py` |
| `vector_first_order_self` | Multi-valence agents with identifying interventions | `modal_vector_first_order_self_sweep.py` |
| `scale_normalized_vprobe` | Scale-normalized probe calibration | `modal_scale_normalized_vprobe_sweep.py` |
| `interventional_contrast` | Interventional contrast for mediated attribution | `modal_interventional_contrast_sweep.py` |
| `role_specific_identifiability` | Role-specific mediated effects / gauge anchoring | `modal_role_specific_identifiability_sweep.py` |

### 3.5 External validity / phases / diagnostics

| Package | Purpose | Entrypoints |
|---|---|---|
| `external_contact` | Claims on systems not built in-lab (e.g. Pythia) | `modal_p1_pythia_weakness.py`, `modal_p1_pythia_lora.py` |
| `gauge_fixed_concern_transport` | Synthetic L4 gauge-fixed transport suite | `python -m experiments.gauge_fixed_concern_transport.core`, `modal_l4_suite.py` |
| `phase4_metaphysics` | Cheap parallel diagnostics for cross-paper open questions | `core.py`, `modal_l4_suite.py` |
| `phase5_external_validity` | Transport toward foundation-model proxies | `core.py`, `modal_l4_suite.py` |
| `phase6_real_model_validation` | Public decoder LMs / frozen encoders under predeclared gates | `real_models.py`, `modal_l4_suite.py` |
| `virtual_governor_stress_signal` | Live global stress → local policy features after target shifts | `core.py`, `modal_l4_sweep.py` |

**Note:** Some of the phase/gauge/virtual-governor packages may not yet appear in
`docs/verification.json`; prefer on-disk `PROVENANCE.md` / README when present.

### 3.6 Experiment conventions

From `experiments/README.md`, every experiment should include:

- hypothesis README/manifest
- deterministic seeds
- positive targets, negative controls, stress tests
- accepted and rejected artifacts
- discovery-regime audit after meaningful runs

Raw outputs stay under `artifacts/` until summarized.

---

## 4. Scripts catalog (detail)

### 4.1 Provenance & quality

| Script | Responsibility |
|---|---|
| `gen_provenance.py` | Emit all `PROVENANCE.md` + `docs/verification.{md,json}` + site mirror |
| `regen.py` | List/reproduce experiments or print documented Modal commands |
| `run_quality_checks.py` | unittest → compileall → publication_guard → ruff → ty |
| `publication_guard.py` | Block tracked secrets, forbidden paths, oversized files |
| `env_probe.py` | Report env var presence/length only |

### 4.2 PDF builders & toolkit

| Script | Responsibility |
|---|---|
| `paperkit.py` | Shared reportlab/matplotlib PDF helpers |
| `render_paper_pdf.py` | Markdown → PDF via markdown-pdf |
| `build_weakness_pdf.py` | Flagship weakness→OOD PDF |
| `build_gridcell_pdf.py` | Paper A PDF |
| `build_paperB_pdf.py` | Paper B reward-deformation PDF |
| `build_effective_dimension_pdf.py` | Rate-distortion effective-dimension PDF |
| `build_concern_weighted_weakness_pdf.py` | Concern-weighted weakness note |
| `build_gauge_fixed_concern_transport_pdf.py` | GFC transport PDF |
| `build_unified_portfolio_pdf.py` | Unified portfolio PDF |
| `build_structure_compatible_*.py` | SCG family PDFs (base, phase2/3, language, semantic retrieval/selection) |
| `build_phase4_metaphysics_pdf.py` / `phase5` / `phase6` | Phase paper PDFs |
| `build_comprehensive_literature_review_paper_pdf.py` | Literature review PDF |
| `build_exhaustive_literature_audit.py` (+ `_pdf`) | Local PDF/ref audit → data → PDF |
| `build_external_citation_review.py` (+ `_pdf`) | External scholarly metadata enrichment |

### 4.3 Figure makers

`make_*_figures.py` scripts render paper figures from committed or local
payloads. Naming usually matches the paper family (`make_concern_figures.py` →
concern bootstrap, `make_world_responds_figures.py`, etc.).
`_patch_figure_titles.py` is a one-off title renumbering helper.

### 4.4 Summarizers & Modal paper tasks

| Script | Responsibility |
|---|---|
| `summarize_reward_location_sweep.py` | Modal reward-location shards → Paper B report |
| `summarize_semantic_concern_sweep.py` | Semantic-concern sweep summary |
| `summarize_label_free_dose_response.py` | Public-safe dose-response tables |
| `summarize_label_free_behavior_gate.py` | Label-free behavior gate Markdown |
| `summarize_behavior_aligned_direction.py` | Behavior-aligned direction summaries |
| `modal_*_paper_tasks.py` | Remote L4 builds for metric-stack, lineage, first-order-self, long-horizon, planning, world-responds papers |
| `reproduce_paperB_stats.py` | Recompute Paper B stats from `data/paper_b/` |
| `analyze_gridcell_conference_evidence.py` | Export Paper A reviewer stats from Modal JSON |
| `export_structure_compatible_artifacts.py` | Copy SCG artifacts to local archive |
| `topk_ablation_stroke_benchmark.py` | Top-K ablation on synthetic-stroke group inference |

---

## 5. Papers, notes, formal, references

### 5.1 `papers/`

Pattern: `papers/<topic>/paper.md` (+ optional prereg/runbook/figures).
`papers/pdf/` holds shareable renders. Notable bundles:

- `papers/icml_publication_package_2026/` — submission packages
- Synthesis dirs: `metaphysics_synthesis`, `metric_stack_synthesis`, literature audits/reviews
- Benchmark framing: `causally_grounded_agents_benchmark`, `weakness_invariance_neurips`

### 5.2 `notes/`

| File | Role |
|---|---|
| `geometric_convergence_research_synthesis.md` | Master program synthesis |
| `webb_miolane_fit.md` | Geometry-of-consciousness talk fit |
| `weakness_topology_program_synthesis.md` | Publication-strategy ranking |
| `reward_deformation_ratedistortion.md` | Rate-distortion law for Paper B |
| `virtual_governor_alignment_fit.md` | Virtual-governor preprint fit |

### 5.3 `formal/ontology-hs/`

Haskell Cabal project (`ConcernedOntology.hs`, `ontology-check` app, tests).
Validates typed body motifs; Python bridge in
`experiments/viable_computational_bodies/haskell_gate.py`.

### 5.4 `references/`

| Path | Role |
|---|---|
| `SOURCES.md` | Public source manifest / recreate instructions |
| `webb-miolane-geometry-of-consciousness-transcript.md` | Committed talk transcript |
| `papers/`, `text/`, `html/` | **Local-only** full texts (gitignored) |

---

## 6. Product & adjacent projects

### 6.1 `sites/reafference_attribution/`

Research Mechanism Atlas: static Node server, papers, `verification.json`,
mechanism visuals. Deployed via Railway (see [railway-autodeploy.md](railway-autodeploy.md)).

### 6.2 `sites/inquiry_black_box/`

Landing/marketing site for Inquiry Black Box. Separate Railway service in the
same GitHub Actions matrix.

### 6.3 `apps/inquiry-black-box/`

Local-first capture product: Electron desktop + Chrome extension, SQLite,
heuristic interpretation, optional Modal batch jobs. Bun monorepo
(`packages/schema`, `packages/signals`, `packages/ui`, `apps/desktop`,
`apps/extension`). See that tree’s `AGENTS.md` / `README.md`.

### 6.4 `coherence-testbench/`

Standalone Phase-0 Neurophenom/Coherence GO/KILL bench on BBBD EEG (and
eyetrack). Own `pyproject.toml`, `config/`, `modal_jobs/`, `src/coherence/`,
`tests/`, `supabase/schema.sql`, `site/`. Status docs at package root
(`POST_MORTEM.md`, `NEXT_STEPS.md`, etc.). Not part of root `run_quality_checks.py`.

---

## 7. CI / config modules

| File | Role |
|---|---|
| `.github/workflows/railway-deploy.yml` | Deploy atlas + Inquiry landing on `main` |
| `pyproject.toml` | Project meta, Ruff, ty excludes |
| `pyrightconfig.json` | Editor typecheck: missing imports silenced |
| `.gitignore` | Secrets, `artifacts/`, `data/`, reference full texts, caches |

---

## 8. Maintenance checklist for this catalog

When you add or materially change code:

1. Update [system_design.md](system_design.md) if runtime flow, deps, deploy, or
   capabilities/limitations change.
2. Update this file: new experiment row, script group entry, test mapping, or doc link.
3. Add/refresh `experiments/<name>/PROVENANCE.md` via `python scripts/gen_provenance.py`
   when the experiment is part of the verified set.
4. Keep `experiments/README.md` active-track list honest for the main entry points.
5. Link new public-facing docs from root `README.md` when they are start-here material.

Regenerate the verification index after experiment/result changes:

```bash
python scripts/gen_provenance.py
```
