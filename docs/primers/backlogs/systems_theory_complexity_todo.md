# Systems That Hold Themselves Together - article-specific improvement and experiment backlog

Source reviewed in full: `/Users/jawaun/Downloads/research_program_primers/systems_theory_complexity_primer.pdf` (25 PDF pages), with `/Users/jawaun/Downloads/research_program_primers/README.md`. The title page, the basin illustration, every `Tension`/limitation/agenda page, the Chapter 8 scorecard, and the conclusion were visually checked against rendered pages. Repository cross-checks used `TODO.md`, `docs/primers/`, `experiments/`, `papers/`, and the current grid-cell preregistration/results.

## Thesis

The article's strongest defensible thesis is narrower than its opening rhetoric: the program has measured small, single-agent homeostatic and repair mechanisms, concern-shaped representation, an ordinal slack/repair relation, and capacity-driven metric deformation; it has not yet shown a distributed complex adaptive system, a dynamical attractor with a mapped basin, a control-parameter phase transition, strict autopoiesis, or self-organized criticality. The most valuable next program is therefore to replace nouns with tests: define control parameters and order parameters, measure response curves and path dependence, map return dynamics and viability sets, and move the virtual-governor and navigation claims into genuinely many-part worlds.

## Exhaustive signal ledger

Every substantive positive result, caveat, criticism, and proposed direction in the article is mapped below. `T-SYS-*` points to executable backlog items later in this file.

| Signal | Source | Article signal | Repository cross-check | Mapped TODOs |
|---|---|---|---|---|
| S01 | p.2, opening and contents | The program is presented as complexity science because constraints organize representations and passive structure may become self-maintaining. | `docs/system_design.md:24-25` repeats the passive/active attractor framing. | T-SYS-002, T-SYS-032 |
| S02 | pp.4-5, §§1.1-1.4 | A classical complex adaptive system has many locally interacting components, but the program mostly studies small single-agent loops. | `TODO.md:188-192` has only an underspecified boundary-priors toy environment; no many-part program is registered. | T-SYS-014, T-SYS-015, T-SYS-016, T-SYS-029, T-SYS-032 |
| S03 | p.6, §2.1 | Decaying energy and two-variable variants are genuine, if minimal, homeostats. | Many benchmark papers use explicit energy/decay; this is earned but should remain scoped to minimal homeostasis. | T-SYS-002, T-SYS-018 |
| S04 | p.6, §2.2 | Allostatic planning can hurt at a confidently wrong boundary. | `papers/allostatic_control/paper.md` reports the boundary failure and only three boundary locations. | T-SYS-013 |
| S05 | pp.6-7, §2.3 and Tension | Live global stress beats stale/wrong/absent stress, but a single policy receiving a hand-computed feature is not distributed coordination. | `experiments/virtual_governor_stress_signal/` is a real signal-ablation scaffold; its paper proposes transfer, not a many-part implementation. | T-SYS-002, T-SYS-014, T-SYS-029 |
| S06 | p.8, §3.1 | An attractor requires restoration, a basin, and stability under perturbation. | `TODO.md:119-122` uses “basin” for language-model state-transfer diagnostics, but that is not a dynamical basin of attraction. | T-SYS-006, T-SYS-030, T-SYS-032 |
| S07 | p.8, §3.2 | Action coupling makes the paraphrase direction roughly seven times more causally load-bearing. | `papers/passive_to_active_geometry/paper.md` reports the paired ablation effect across six model/seed cells. | T-SYS-005, T-SYS-011 |
| S08 | pp.8-9, §3.2 | Wrong-centroid pushes fool the passive readout 85% and the active classifier 0%. | Same paper reports robustness, but its README explicitly says supervised fine-tuning is an action-coupling proxy. | T-SYS-002, T-SYS-006 |
| S09 | p.9, Tension | Robustness is attractor-like, not an established attractor: no basin geometry, stability eigenvalues, or return dynamics. | No passive-to-active runner exposes autonomous state dynamics or Jacobian/return-map analysis. | T-SYS-006, T-SYS-030, T-SYS-031 |
| S10 | p.9, §3.3 | Ring/torus neuroscience is the benchmark for dynamics-backed attractor language. | `experiments/grid_cell_weakness/` measures toroidal topology and OOD behavior, not return dynamics of the program's agent representation. | T-SYS-006, T-SYS-024 |
| S11 | p.10, §4.2 | Valence-coupled supervision causes dramatic reward-axis rather than sensory-axis organization. | `papers/valence_object_formation/paper.md` reports reward gap +1.96 and explicitly calls the mechanism a supervised optimal-action stand-in. | T-SYS-010, T-SYS-022 |
| S12 | p.11, Tension | The cleanest “self-organization” can be deflated to supervised feature selection. | `papers/concern_bootstrap/paper.md` partially answers this; `papers/two_bottlenecks/paper.md` gets XOR reward gap +1.84 without optimal-action labels only after decoupling representation learning from sparse-reward policy learning. | T-SYS-002, T-SYS-010, T-SYS-022, T-SYS-031 |
| S13 | pp.10-11, §4.2 | Geometry tightens gradually while load-bearing appears abruptly. | The passive-to-active paper reports training trajectories, but no model comparison distinguishes discontinuity from a steep continuous curve. | T-SYS-005, T-SYS-011 |
| S14 | p.11, arch analogy before Tension | Abruptness may be only a smooth signal crossing a measurement/detection threshold. | No change-point model, smooth-null comparison, or holdout threshold analysis is reported. | T-SYS-005, T-SYS-011, T-SYS-028 |
| S15 | p.13, §5.1 | Hierarchy and near-decomposability motivate robustness/evolvability. | The program varies frozen regions but does not quantify within- versus between-module coupling. | T-SYS-025 |
| S16 | pp.13-14, §§5.2-5.3 | More lower-layer slack gives more adaptation/repair; alignment can turn a foundation into an aid or trap. | `papers/autopoietic_control/paper.md` and `papers/homeostatic_objects/paper.md` report the ordinal ordering and alignment qualification. | T-SYS-007, T-SYS-016 |
| S17 | p.14, Tension | The Law of the Stack's numerical bound is asserted; only an ordinal ordering across coarse freezes is tested. | `papers/autopoietic_control/paper.md:148,164,167` explicitly concedes that the exponential bound was not tested and suggests finer slack control. | T-SYS-002, T-SYS-007, T-SYS-025 |
| S18 | p.15, §§6.1-6.2 | Finite capacity is the generative constraint behind the rate-distortion allocation prediction. | The initial grid-cell exponent test lacked a hard capacity constraint; `capacity_bottleneck.py` added one and moved alpha from 0.07 to about 0.30. | T-SYS-008, T-SYS-026 |
| S19 | p.16, §6.3 | Alpha about 0.30 versus 0.50 suggests an effective one-dimensional allocation. | `capacity_bottleneck_2026_07_01.md` calls this post-hoc and untested; the frozen preregistration now specifies stripe/aniso2d/point geometries and `d_eff`. The primer overstates this as a revealed dimension. | T-SYS-002, T-SYS-008 |
| S20 | p.16, Tension | One setting and few seeds are a point, not a characterized constraint/order relation. | The frozen addendum requires an amplitude sweep and bootstrap SE <= 0.02, but no corresponding committed result is present. | T-SYS-008, T-SYS-028 |
| S21 | p.17, §7.2 | Test-time recovery after head damage is genuine small-scale ultrastability, and recovery follows slack ordering. | `papers/autopoietic_control/paper.md` reports 0.45 to 0.965 recovery in 10 labeled-gradient updates for full fine-tuning. | T-SYS-009 |
| S22 | pp.17-18, §7.2 and Tension | The prose first calls repair “self-supervised,” then correctly says it uses labeled gradient descent; neither is strict autopoiesis. | The source paper itself uses “self-supervised in the autopoietic sense” but later concedes labeled gradients and no policy generation. This terminology is internally inconsistent. | T-SYS-002, T-SYS-009, T-SYS-017, T-SYS-024 |
| S23 | p.18, §7.3 | Viability buffer is useful, but formal viability kernels are not computed. | `viable_computational_bodies` has viability gates and typed search, not reachability-derived viable sets for the homeostatic dynamics. | T-SYS-018, T-SYS-026 |
| S24 | p.20, §8.1 scorecard | Earned: homeostasis/repair; partial: self-organization, constraint order, Stack ordering; unestablished: attractors/transitions; aspirational: autopoiesis; absent: distributed systems. | This is broadly accurate after correcting S19 and S22. | T-SYS-002, T-SYS-031, T-SYS-032 |
| S25 | p.20, §8.1 | Criticality is rightly not claimed: no avalanches, critical exponents, or edge-of-chaos result. | `TODO.md:192` mentions only an undefined “criticality proxy.” | T-SYS-027, T-SYS-032 |
| S26 | p.21, Limitation 2 | No control-parameter sweep, bifurcation map, or hysteresis test establishes a passive-active transition. | `TODO.md:197` asks the attractor question but does not register a transition experiment. | T-SYS-011, T-SYS-012, T-SYS-013, T-SYS-028 |
| S27 | pp.21 and 23, Limitation 1 and §9.3 | Move to populations, shared worlds, and genuinely distributed governors; a second navigator may disrupt the single-agent torus. | No corresponding experiment package exists. | T-SYS-014, T-SYS-015, T-SYS-016, T-SYS-029 |
| S28 | pp.23-24, §§9.2-9.4 | Build explicit control-parameter/order-parameter maps, not endpoint comparisons. | Relevant metrics exist across packages but there is no shared phase-map schema or analysis utility. | T-SYS-011, T-SYS-013, T-SYS-028 |
| S29 | p.24, §9.5 | Earn deeper terms through self-produced policy, mapped attractor basins, and quantitative Stack tests. | `viable_computational_bodies` searches bodies offline; it does not show an agent rebuilding its own organization during viability breach. | T-SYS-006, T-SYS-007, T-SYS-017 |
| S30 | pp.24-25, §§9.6-9.8 | Far-from-equilibrium throughput, maintenance cost, and entropy export are the richest missing lineage/direction. | Current “energy” is a task variable, not a thermodynamic accounting. | T-SYS-019, T-SYS-027, T-SYS-033 |
| S31 | PDF metadata and p.1 | The visible title is correct, but PDF metadata says “The Mathematics of the Research Program - A Primer from First Principles.” | `pdfinfo` confirms the stale title. | T-SYS-001 |
| S32 | pp.17-18, 20-22, 24-25 | Callouts split badly: the autopoiesis tension, Limitation 1, 8.4 carry-forward, and “A closing thought” are orphaned across pages; p.22 is almost blank. | Visual render confirms the layout defect. | T-SYS-003 |

## Backlog

### Article corrections and improvements

#### T-SYS-001 - Fix title metadata and rebuild deterministically
- **Priority / status:** P0 / existing defect.
- **Source:** PDF metadata; visible p.1 title.
- **Action:** Set HTML `<title>` and Chromium document metadata to `Systems That Hold Themselves Together: A Systems-Theory and Complexity-Science Primer`; rebuild and verify with `pdfinfo`.
- **Paths:** `docs/primers/systems_theory_complexity_primer.html`, `docs/primers/systems_theory_complexity_primer.pdf`, `docs/primers/README.md`.
- **Deliverable:** Rebuilt PDF with correct title/subject metadata and unchanged visible title.
- **Pass/fail gate:** PASS iff `pdfinfo` contains the correct title, the PDF remains 25 pages or deliberate pagination changes are documented, and title/cover render has no clipping; otherwise FAIL.
- **Dependencies:** Headless Chromium command documented in `docs/primers/README.md`.
- **Rationale:** The current artifact identifies itself as the mathematics primer to indexing and citation tools.
- **Inference flag:** No - directly observed defect.

#### T-SYS-002 - Reconcile scientific claims with the live evidence ledger
- **Priority / status:** P0 / existing defect.
- **Source:** pp.7, 9, 11, 14, 16, 17-18, 20-21; all Tension/scorecard passages.
- **Action:** Patch the article so: (a) distributed language always says single-policy scaffold; (b) agent “attractor” becomes “attractor-like robustness” until T-SYS-006 passes; (c) alpha ~0.30 implies, but does not reveal, `d_eff ~1`; (d) repair is labeled-gradient test-time adaptation, not self-supervised learning; (e) Stack evidence is ordinal, not a quantitative-law confirmation; and (f) supervised concern geometry is distinguished from the partial label-free `concern_bootstrap`/`two_bottlenecks` result.
- **Paths:** `docs/primers/systems_theory_complexity_primer.html`, `docs/primers/systems_theory_complexity_primer.pdf`, `papers/passive_to_active_geometry/paper.md`, `papers/autopoietic_control/paper.md`, `papers/grid_cell_weakness/preregistration.md`, `experiments/grid_cell_weakness/results/capacity_bottleneck_2026_07_01.md`, `papers/concern_bootstrap/paper.md`, `papers/two_bottlenecks/paper.md`.
- **Deliverable:** Corrected scorecard and all affected prose with evidence links/footnotes.
- **Pass/fail gate:** PASS iff every row in S05/S09/S12/S17/S19/S22 uses the same bounded status as its source paper and a text search finds no unqualified “active attractor,” “distributed system,” “self-supervised repair,” “quantitatively confirmed Stack,” or “revealed effective dimension”; otherwise FAIL.
- **Dependencies:** T-SYS-001 rebuild workflow.
- **Rationale:** These distinctions are the article's main intellectual contribution; internal drift undermines it.
- **Inference flag:** No - source papers explicitly state the limits.

#### T-SYS-003 - Repair PDF pagination, widows, and orphaned callouts
- **Priority / status:** P1 / existing defect.
- **Source:** visual pages 17-18, 20-22, 24-25.
- **Action:** Add print CSS (`break-inside: avoid`, heading/callout keep-with-next rules) and rebalance content so each callout title remains with at least two body lines and p.22 is not a one-line spill page.
- **Paths:** `docs/primers/systems_theory_complexity_primer.html`, `docs/primers/systems_theory_complexity_primer.pdf`.
- **Deliverable:** Reflowed PDF and rendered verification images.
- **Pass/fail gate:** PASS iff no colored callout title is separated from its first two body lines, no section carry-forward has a one-line orphan page, and all 25-page-equivalent renders show no clipping/overlap; otherwise FAIL.
- **Dependencies:** T-SYS-001.
- **Rationale:** The current page breaks visually detach criticisms from their explanations.
- **Inference flag:** No - direct visual observation.

#### T-SYS-004 - Add an evidence-backed control/order-parameter map to the article
- **Priority / status:** P1 / new.
- **Source:** pp.21, 23-24, Limitation 2 and §§9.2-9.4.
- **Action:** Add a table mapping each claimed regime to control parameter, order parameter, current evidence, missing diagnostic, and eligible causal language.
- **Paths:** `docs/primers/systems_theory_complexity_primer.html`, `docs/primers/systems_theory_complexity_primer.pdf`; source metrics in `experiments/passive_to_active/`, `experiments/autopoietic_control/`, `experiments/grid_cell_weakness/`, `experiments/virtual_governor_stress_signal/`.
- **Deliverable:** One article table covering coupling -> load-bearing/robustness/buffer; capacity/amplitude/field shape -> alpha/`d_eff`/toroidal score; slack -> repair/flexibility; governor fidelity -> global stress/recovery; decay -> viability.
- **Pass/fail gate:** PASS iff every proposed order parameter has units/definition, every control parameter has an intervention, and every row names a null and a claim tier; otherwise FAIL.
- **Dependencies:** T-SYS-002.
- **Rationale:** This turns Chapter 9's advice into a reproducible program map.
- **Inference flag:** No - directly requested by §§9.2-9.4.

### Old experiments to correct or replicate

#### T-SYS-005 - Reanalyze “abrupt load-bearing” against continuous and thresholded nulls
- **Priority / status:** P0 / partial.
- **Source:** pp.10-11, §4.2 and arch analogy.
- **Action:** Recompute per-checkpoint geometry and intervention effects with dense checkpointing; fit smooth monotone, segmented/change-point, and thresholded-observation models on preregistered held-out seeds.
- **Paths:** `experiments/passive_to_active/modal_passive_to_active.py`, `experiments/passive_to_active/modal_replication_sweep.py`, new `experiments/passive_to_active/analyze_transition.py`, `papers/passive_to_active_geometry/paper.md`.
- **Deliverable:** Checkpoint-level curves, model-comparison table, and bounded verdict: discontinuity, steep continuous onset, or unresolved.
- **Pass/fail gate:** PASS for “abrupt” only if a change-point model beats the best smooth null by delta AIC >= 10 and a bootstrap 95% interval for the slope/discontinuity excludes the null in >= 5/6 registered cells; otherwise retire “abrupt emergence.”
- **Dependencies:** Access to raw trajectory checkpoints or a frozen rerun.
- **Rationale:** A detection threshold can manufacture apparent emergence from smooth learning.
- **Inference flag:** Partly - model-comparison gate is an operationalization added here.

#### T-SYS-006 - Replicate passive-active with dynamical basin and return diagnostics
- **Priority / status:** P0 / new relative to the existing robustness experiment.
- **Source:** pp.8-9, §§3.1-3.3 and Tension; p.24 §9.5.
- **Action:** Define an autonomous/recurrent update map around the active representation; sample perturbations by direction/magnitude; trace return time, destination, basin boundary, local Jacobian spectrum, and failure escape.
- **Paths:** new `experiments/passive_to_active_dynamics/`; compare `experiments/passive_to_active/`; paper `papers/passive_to_active_geometry/paper.md` or a new dynamics paper.
- **Deliverable:** Basin map, return-time distribution, local stability estimates, matched passive/random/redundant-classifier controls.
- **Pass/fail gate:** PASS “attractor” only if a nonzero-measure basin returns within epsilon to the same invariant set in >= 90% of registered perturbations, dominant local eigenvalue magnitude is <1 where applicable, and passive/random controls fail at least one gate; otherwise retain “attractor-like robustness.”
- **Dependencies:** T-SYS-030; a model with explicit time evolution, not a one-shot classifier alone.
- **Rationale:** A static classifier cannot supply the dynamics that define an attractor.
- **Inference flag:** Yes - the exact numerical gate is proposed here.

#### T-SYS-007 - Test the quantitative Law of the Stack with graded slack
- **Priority / status:** P0 / partial.
- **Source:** pp.13-14, §§5.2-5.3 and Tension; p.24 §9.5.
- **Action:** Replace two coarse freeze patterns with continuous lower-layer controls (LoRA rank, trainable-layer fraction, channel bottleneck, or measured hypothesis volume), measure lower and upper weakness in compatible units, and test the stated `w(next) <= 2^w(lower)` bound plus alignment interaction.
- **Paths:** `experiments/autopoietic_control/modal_autopoietic_sweep.py`, new `experiments/autopoietic_control/modal_stack_quantitative_sweep.py`, `papers/autopoietic_control/paper.md`, `papers/homeostatic_objects/paper.md`.
- **Deliverable:** Registered slack-response curves, bound-violation table, alignment x slack surface, and theory/measurement unit audit.
- **Pass/fail gate:** PASS the law only if >=95% of preregistered cells satisfy the numerical inequality within measurement uncertainty and the relationship replicates across Pythia/GPT-2 plus a non-language homeostat; ordinal monotonicity alone remains partial.
- **Dependencies:** Resolve how formal weakness maps to empirical slack before compute.
- **Rationale:** The article correctly says the named law has not yet been tested as a law.
- **Inference flag:** Yes - replication breadth and tolerance are proposed.

#### T-SYS-008 - Complete the preregistered effective-dimension parameter sweep
- **Priority / status:** P0 / existing but incomplete.
- **Source:** pp.15-16, §§6.2-6.3 and Tension; pp.23-24 §9.4.
- **Action:** Run the frozen stripe/aniso2d/point x amplitude x capacity sweep, add direct anisotropy/PCA estimates of deformation dimension, and compare inferred `d_eff = 2 alpha/(1-alpha)` with direct dimension.
- **Paths:** `experiments/grid_cell_weakness/modal_reward_deformation_sweep.py`, `experiments/grid_cell_weakness/capacity_bottleneck.py`, `papers/grid_cell_weakness/preregistration.md`, new committed result under `experiments/grid_cell_weakness/results/`.
- **Deliverable:** Full response surfaces, bootstrap intervals, coverage/R2 diagnostics, direct-vs-inferred dimension agreement, and registered verdict.
- **Pass/fail gate:** Use the frozen gate: at A=6, SE(alpha) <=0.02; aniso2d CI excludes 1/3 and is closer to 1/2; stripe is closer to/includes 1/3; the between-geometry CI excludes zero. Additionally, direct and inferred `d_eff` must agree within 0.25 for the dimension interpretation to pass.
- **Dependencies:** Modal quota and non-overlapping additional seeds if precision misses.
- **Rationale:** The current article promotes a post-hoc explanation into a finding.
- **Inference flag:** Partly - first gate is existing; direct-agreement threshold is new.

#### T-SYS-009 - Correct and strengthen the repair experiment
- **Priority / status:** P1 / partial.
- **Source:** pp.17-18, §7.2 and Tension.
- **Action:** Re-label the existing result as labeled-gradient test-time repair; add no-label consistency/predictive repair, label-shuffle, replay-buffer, external-optimizer-off, and update-budget controls; test function restoration and representational restoration separately.
- **Paths:** `experiments/autopoietic_control/modal_autopoietic_sweep.py`, `papers/autopoietic_control/paper.md`.
- **Deliverable:** Repair-mechanism ablation table and revised terminology.
- **Pass/fail gate:** PASS “ultrastable repair” if recovery exceeds matched random/retraining controls by >=0.10 accuracy across both models and restores the preregistered causal axis; PASS “self-directed repair” only if a no-label internal signal selects repair timing/direction and beats matched scheduled updates; neither passes strict autopoiesis.
- **Dependencies:** T-SYS-002 terminology patch.
- **Rationale:** Restoration under an external labeled objective is real but weaker than the current headline.
- **Inference flag:** Yes - strengthened gates proposed here.

#### T-SYS-010 - Consolidate supervised versus experience-derived concern geometry
- **Priority / status:** P1 / partial.
- **Source:** pp.10-11, §4.2 and Tension; p.21 Limitation 3.
- **Action:** Run one common harness comparing supervised optimal-action, action-conditioned delta-E without labels, sparse-reward RL joint, staged delta-E then RL, reconstruction, sensory, shuffled-outcome, and oracle-reward controls on additive and XOR shifts.
- **Paths:** `experiments/valence_object_formation/`, `experiments/concern_bootstrap/`, `experiments/two_bottlenecks/`, `experiments/homeostatic_objects/`; synthesis update in their papers.
- **Deliverable:** Same-seed, same-architecture comparison of reward gap, causal load-bearing, return, shift recovery, and supervision provenance.
- **Pass/fail gate:** PASS “self-organized from experience” only if a condition with no optimal-action labels reaches reward gap >=1.0, causal intervention effect >=0.30 over random, and OOD return >=80% of the supervised upper bound on both reward families; otherwise use “self-supervised predictive organization” or “objective-driven reorganization.”
- **Dependencies:** Shared data splits and metric code.
- **Rationale:** Existing papers partially answer the criticism but cannot be compared cleanly across separate harnesses.
- **Inference flag:** Yes - unified gate proposed here.

### New experiments

#### T-SYS-011 - Run the coupling bifurcation experiment
- **Priority / status:** P0 / new.
- **Source:** p.21 Limitation 2; p.23 §9.2.
- **Action:** Sweep action-coupling strength continuously from zero, with identical data/initializations, and measure causal specific effect, perturbation failure rate, buffer, geometry gap, and return.
- **Paths:** new `experiments/passive_active_phase_map/`; reuse `experiments/passive_to_active/` components.
- **Deliverable:** Preregistered coupling/order curves, critical-point estimates, smooth-null comparison, and raw cells in `artifacts/` with summary under `results/`.
- **Pass/fail gate:** PASS a bifurcation only if the registered discontinuous/segmented model beats smooth alternatives out of sample, the estimated critical coupling replicates within 20% across >=2 architectures and >=5 seeds, and at least two independent order parameters change at the same point; otherwise report a continuous crossover.
- **Dependencies:** T-SYS-005 analysis and T-SYS-028 schema.
- **Rationale:** This is the article's highest-value proposed test.
- **Inference flag:** Yes - exact reproducibility gate proposed.

#### T-SYS-012 - Test hysteresis and path dependence
- **Priority / status:** P0 / new.
- **Source:** pp.21 and 23, Limitation 2 and §9.2.
- **Action:** Train forward on increasing coupling and reverse on decreasing coupling; include washout/reinitialization controls and matched total-update budgets.
- **Paths:** `experiments/passive_active_phase_map/`.
- **Deliverable:** Forward/reverse loops with area-under-hysteresis, retention time, and control comparisons.
- **Pass/fail gate:** PASS hysteresis only if forward/reverse curves differ with bootstrap 95% CI excluding zero over a contiguous coupling interval and the loop survives matched optimization-history controls; otherwise no regime memory.
- **Dependencies:** T-SYS-011.
- **Rationale:** A sharp training onset without path dependence may be optimizer installation, not a persistent regime.
- **Inference flag:** Yes - statistical gate proposed.

#### T-SYS-013 - Build a multi-control phase diagram
- **Priority / status:** P1 / new.
- **Source:** p.21 Limitation 2; pp.23-24 §§9.2-9.4.
- **Action:** Cross coupling with capacity, energy decay, environmental volatility, and repair-update budget; report order parameters and survival on a common grid.
- **Paths:** `experiments/passive_active_phase_map/`, inputs from `experiments/allostatic_control/` and `experiments/grid_cell_weakness/`.
- **Deliverable:** Coupling x constraint heatmaps and interaction models identifying robust versus task-specific thresholds.
- **Pass/fail gate:** PASS a general regime boundary only if its normalized location is stable within 20% across at least three nuisance-control slices and two substrates; otherwise call it harness-specific.
- **Dependencies:** T-SYS-011 and T-SYS-028.
- **Rationale:** A one-dimensional sweep cannot distinguish a general transition from a tuned trajectory.
- **Inference flag:** Yes.

#### T-SYS-014 - Replace the virtual-governor scaffold with many-part coordination
- **Priority / status:** P0 / new.
- **Source:** pp.6-7, §2.3 Tension; p.23 §9.3.
- **Action:** Create N locally observing components with independent policies/resources whose aggregate state defines global stress; compare live broadcast, local-neighbor diffusion, stale, wrong-channel, noisy, delayed, absent, and centralized-oracle signals.
- **Paths:** new `experiments/distributed_virtual_governor/`; seed from `experiments/virtual_governor_stress_signal/`.
- **Deliverable:** Coordination, recovery, fairness, shock propagation, scaling-to-N, and ablation report.
- **Pass/fail gate:** PASS emergent distributed coordination only if decentralized live/diffused signals reduce global violation >=30% versus absent and >=15% versus matched local-only reward across >=5 seeds, scale to at least N={4,16,64}, and no individual component has direct global-state access.
- **Dependencies:** T-SYS-029.
- **Rationale:** This directly closes the article's central single-agent/distributed-language gap.
- **Inference flag:** Yes - exact architecture/gates proposed.

#### T-SYS-015 - Test collective navigation and topology with two-to-many agents
- **Priority / status:** P1 / new.
- **Source:** p.23 §9.3, “second navigating agent explodes the torus.”
- **Action:** Extend the grid-cell harness to 1, 2, 4, and 8 agents under independent, shared-resource, collision, cooperation, and communication regimes; measure individual/joint topology, effective dimension, mutual information, coordination, and OOD navigation.
- **Paths:** new `experiments/collective_grid_cell_dynamics/`; reuse `experiments/grid_cell_weakness/core.py` metrics.
- **Deliverable:** Agent-count/topology phase map and causal communication ablations.
- **Pass/fail gate:** PASS many-part emergence if a preregistered macro order parameter absent at N=1 appears reproducibly for N>1, cannot be reconstructed from an additive mixture of isolated agents, and is destroyed by a targeted interaction ablation but not matched random damage.
- **Dependencies:** T-SYS-029; metric validation on synthetic product manifolds.
- **Rationale:** It tests emergence from interaction rather than simply increasing model size.
- **Inference flag:** Yes.

#### T-SYS-016 - Evolve a population of encoders under viability selection
- **Priority / status:** P1 / partial idea, no experiment.
- **Source:** p.23 §9.3; linked to pp.13-14 Stack discussion.
- **Action:** Spawn populations with varied encoder slack/alignment, select by survival under ecological shifts, mutate/crossover architectures or weights, and compare viability, reward geometry, diversity, and repair to reward-only and novelty-only selection.
- **Paths:** new `experiments/population_encoder_evolution/`; reuse `experiments/homeostatic_objects/` and `experiments/viable_computational_bodies/` search/gates.
- **Deliverable:** Cross-generational curves, lineage trees, and evolutionary Stack test.
- **Pass/fail gate:** PASS if viability-guided populations improve held-out-shift survival and concern-axis geometry over both controls with bootstrap CI excluding zero while retaining population diversity above a preregistered floor; otherwise reject the evolutionary extension.
- **Dependencies:** T-SYS-007 metric alignment and T-SYS-029 population runtime.
- **Rationale:** It instantiates the article's proposed evolutionary many-part form of the Stack.
- **Inference flag:** Yes.

#### T-SYS-017 - Test strict self-production rather than supervised repair
- **Priority / status:** P0 / partial infrastructure only.
- **Source:** pp.17-18, §7 and Tension; p.24 §9.5.
- **Action:** On viability breach, require the system to detect breach, generate/select a new policy/module/boundary rule, integrate it, and maintain function without labeled repair targets; compare externally supplied replacement, fixed candidate menu, offline body search, and no-repair controls.
- **Paths:** new `experiments/operational_closure/`; reuse typed modules from `experiments/viable_computational_bodies/` and concern-gated repair contracts from `experiments/concerned_syntax/`.
- **Deliverable:** Component-production and boundary-maintenance event trace with causal closure graph.
- **Pass/fail gate:** PASS a bounded operational-closure result only if produced components causally enable continued viability, the production process itself depends on and restores the system boundary, the loop persists for >=3 breach/repair cycles, and removal of any registered closure edge breaks maintenance; otherwise call it adaptive policy search, not autopoiesis.
- **Dependencies:** T-SYS-024 definition audit; formal anti-cheat rules.
- **Rationale:** Generating a new organization is the missing step identified by the article.
- **Inference flag:** Yes - operational test proposed here; not a claim of biological life.

#### T-SYS-018 - Compute viability kernels, not only buffers
- **Priority / status:** P1 / new.
- **Source:** p.18 §7.3.
- **Action:** For tractable homeostatic environments, solve/approximate the controlled invariant viable set and compare buffer estimates with true distance-to-kernel-boundary and survival under disturbances.
- **Paths:** new `experiments/viability_kernels/`; reuse state/action dynamics from homeostatic and allostatic packages.
- **Deliverable:** Exact small-state kernels, approximate neural kernels, calibration curves, and disturbance tests.
- **Pass/fail gate:** PASS buffer-as-viability proxy only if Spearman rho >=0.8 with true boundary distance and calibrated survival error <=0.05 across registered disturbance families; otherwise restrict buffer language.
- **Dependencies:** Formal transition model and Aubin review in T-SYS-024/T-SYS-026.
- **Rationale:** This upgrades an attractive informal quantity into a systems-theory measurement.
- **Inference flag:** Yes.

#### T-SYS-019 - Add throughput and maintenance-cost experiments
- **Priority / status:** P2 / new.
- **Source:** pp.24-25, §9.6 and conclusion.
- **Action:** Treat resource inflow, dissipation, boundary-maintenance cost, and repair cost as explicit conserved/accounted quantities; vary driving and measure order/viability after shutdown and resumption.
- **Paths:** new `experiments/dissipative_homeostat/`.
- **Deliverable:** Energy/resource ledger, throughput-order curves, shutdown decay, and matched free-energy/task-reward controls.
- **Pass/fail gate:** PASS “far-from-equilibrium maintained order” only if order persists under throughput, decays after inflow removal, recovers on restoration, and maintenance cost/entropy proxy balances within preregistered accounting tolerance; otherwise retain only metaphorical thermodynamic framing.
- **Dependencies:** T-SYS-027 literature and careful statement that task energy is not physical energy.
- **Rationale:** Current scalar “energy” lacks thermodynamic meaning.
- **Inference flag:** Yes.

### Research to read, internalize, and cite

#### T-SYS-020 - Read dynamical-systems transition methods
- **Priority / status:** P0 / new synthesis.
- **Source:** pp.8-9 and 21-24, attractor/transition gaps.
- **Action:** Read primary/standard sources on bifurcation, local stability, return maps, hysteresis, critical slowing, and finite-size scaling; extract an analysis checklist for T-SYS-005/006/011/012.
- **Paths:** `references/` notes, `papers/external_citation_review/`, new `notes/dynamical_transition_methods.md`.
- **Deliverable:** Claim-to-diagnostic matrix with equations, assumptions, and citation-ready entries; candidates include Strogatz for nonlinear dynamics and primary critical-transition literature.
- **Pass/fail gate:** PASS iff every proposed attractor/transition statistic names its assumptions, estimator, finite-sample failure mode, and one primary citation; otherwise incomplete.
- **Dependencies:** Bibliographic resolution/full-text provenance rules.
- **Rationale:** The article asks for methods the current program does not yet implement.
- **Inference flag:** Yes - specific reading candidates extend the article.

#### T-SYS-021 - Read self-organization versus supervision literature
- **Priority / status:** P1 / partial.
- **Source:** pp.10-11 and p.21, supervised-feature-selection criticism.
- **Action:** Synthesize operational definitions of self-organization, objective-driven representation, emergent computation, unsupervised disentanglement limits, intrinsic motivation, and predictive/self-supervised learning.
- **Paths:** `papers/comprehensive_literature_review/paper.md`, `papers/external_citation_review/`, new `notes/self_organization_claim_criteria.md`.
- **Deliverable:** Terminology rubric that assigns each concern-geometry experiment a defensible label and evidence tier.
- **Pass/fail gate:** PASS iff at least three competing definitions are compared, each live experiment is classified, and the rubric prevents supervised optimal-action labels from satisfying the strongest tier.
- **Dependencies:** Full-text review of cited sources, including the already cited Locatello et al. limit and appropriate complexity primary sources.
- **Rationale:** The article's central criticism is partly terminological and partly causal.
- **Inference flag:** Yes.

#### T-SYS-022 - Read distributed coordination and collective emergence
- **Priority / status:** P1 / new.
- **Source:** pp.6-7, 20-23, single-agent limitation and multi-agent agenda.
- **Action:** Review distributed control, consensus, stigmergy, collective behavior, multi-agent RL, public-goods/global-signal problems, and macro-variable detection.
- **Paths:** new `notes/distributed_complexity_experiment_design.md`, `papers/external_citation_review/`.
- **Deliverable:** Baseline/ablation catalog for T-SYS-014-016 and definitions separating centralized, broadcast, decentralized, and emergent coordination.
- **Pass/fail gate:** PASS iff each planned many-part experiment has at least one classical systems baseline, one modern MARL baseline, one no-interaction null, and one macro-emergence test with primary citations.
- **Dependencies:** Bibliographic resolution.
- **Rationale:** Without this lineage, a multi-agent extension could still be centralized control in disguise.
- **Inference flag:** Yes.

#### T-SYS-023 - Read autopoiesis, operational closure, and viability theory closely
- **Priority / status:** P0 / partial.
- **Source:** pp.17-18 and p.24, autopoiesis/viability gaps.
- **Action:** Read Maturana and Varela, Ashby, Di Paolo, and Aubin at primary-source depth; separate homeostasis, ultrastability, organizational closure, component production, boundary production, and viability kernels.
- **Paths:** `papers/comprehensive_literature_review/paper.md`, `papers/external_citation_review/`, new `notes/autopoiesis_operationalization.md`.
- **Deliverable:** Necessary/sufficient-criterion matrix for claim labels and experimental proxies.
- **Pass/fail gate:** PASS iff every criterion is tied to a quotable-but-paraphrased primary-source location, and T-SYS-009/017/018 are each assessed against it without collapsing repair into autopoiesis.
- **Dependencies:** Full-text provenance.
- **Rationale:** The current paper title and primer both use “autopoietic” more broadly than the strict tradition.
- **Inference flag:** No - authors/lineage are named by the article.

#### T-SYS-024 - Read hierarchy, near-decomposability, and the Stack theorem
- **Priority / status:** P1 / partial.
- **Source:** pp.13-14, Chapter 5.
- **Action:** Read Simon on near-decomposability and the precise Bennett/Suzuki theorem/proof; audit empirical units and whether measured “slack,” “weakness,” flexibility, and repair are commensurable.
- **Paths:** new `notes/law_of_stack_measurement_audit.md`, relevant paper references and `papers/external_citation_review/`.
- **Deliverable:** Formal-to-empirical variable map and list of theorem assumptions violated/satisfied by T-SYS-007.
- **Pass/fail gate:** PASS iff the empirical inequality is dimensionally well-defined, all theorem assumptions are enumerated, and preregistration states which result would falsify the mapped claim.
- **Dependencies:** Obtain the exact primary theorem source.
- **Rationale:** Testing a numerical bound requires more than interpolating between freeze conditions.
- **Inference flag:** No.

#### T-SYS-025 - Read high-resolution rate-distortion and effective-dimension methods
- **Priority / status:** P1 / partial.
- **Source:** pp.15-16 and pp.23-24.
- **Action:** Review quantization/rate-distortion asymptotics, anisotropic allocation, information bottlenecks, intrinsic/effective dimension estimators, and finite-sample metric-field estimation.
- **Paths:** `notes/reward_deformation_ratedistortion.md`, new `notes/effective_dimension_measurement_audit.md`, `papers/grid_cell_weakness/preregistration.md`.
- **Deliverable:** Assumption checklist and estimator comparison used by T-SYS-008/018.
- **Pass/fail gate:** PASS iff the audit covers hard versus soft capacity, high-resolution assumptions, anisotropy, periodic codes, estimator bias, seed/coverage precision, and identifies at least one direct dimension estimator independent of alpha.
- **Dependencies:** Resolve primary quantization citations.
- **Rationale:** The present alpha-to-dimension inference is too fragile to stand alone.
- **Inference flag:** Yes - literature expansion beyond the article's summary.

#### T-SYS-026 - Read far-from-equilibrium and dissipative-structure work
- **Priority / status:** P2 / new.
- **Source:** pp.24-25, §9.6.
- **Action:** Read Prigogine primary work and modern non-equilibrium/dissipative-adaptation treatments; identify what can be measured in a computational model without falsely equating reward or an energy variable with thermodynamic energy.
- **Paths:** new `notes/far_from_equilibrium_scope.md`, `papers/external_citation_review/`.
- **Deliverable:** Measurement boundary document and citation set for T-SYS-019/article revision.
- **Pass/fail gate:** PASS iff it explicitly lists lawful quantities, metaphors that must be prohibited, and an experimental accounting equation with units; otherwise do not add thermodynamic claims.
- **Dependencies:** Full-text primary sources and domain review if publication-bound.
- **Rationale:** This direction is promising but especially vulnerable to category errors.
- **Inference flag:** No - explicitly proposed by §9.6.

#### T-SYS-027 - Define a no-hype criticality reading and decision gate
- **Priority / status:** P3 / new.
- **Source:** pp.5 and 20, lineage and “not claimed” scorecard.
- **Action:** Read Kauffman/Bak and modern cautions about false power laws; specify what would be required before adding a criticality experiment.
- **Paths:** new `notes/criticality_claim_gate.md`, `papers/external_citation_review/`.
- **Deliverable:** Go/no-go checklist for avalanches, exponent fitting, finite-size scaling, alternative heavy-tail models, and edge-of-chaos metrics.
- **Pass/fail gate:** PASS iff the checklist requires finite-size scaling and model comparison and rejects a single log-log line or an undefined “criticality proxy” as evidence.
- **Dependencies:** None; do not launch compute until checklist passes.
- **Rationale:** The program is currently correct not to claim criticality.
- **Inference flag:** Yes - this is a protective extension.

### Software, framework, and skill work

#### T-SYS-028 - Build a complexity-experiment control/order-parameter framework
- **Priority / status:** P0 / new.
- **Source:** pp.21 and 23-24, transition and curves agenda.
- **Action:** Create a reusable registry for controls, order parameters, sweep grids, forward/reverse paths, null models, change-point/smooth fits, bootstrap uncertainty, finite-size slices, and preregistered gates.
- **Paths:** new `research_tools/complexity_sweeps/` or `src/...`; consumers `experiments/passive_active_phase_map/`, `experiments/grid_cell_weakness/`, `experiments/distributed_virtual_governor/`; tests under `tests/`.
- **Deliverable:** Typed configs, deterministic seed expansion, tidy cell schema, phase-map plots, gate evaluator, docs, and reference synthetic bifurcation fixtures.
- **Pass/fail gate:** PASS iff synthetic smooth crossover, pitchfork/saddle-node, and hysteretic systems are correctly distinguished in tests; deterministic reruns are byte-equivalent aside from timestamps; missing controls/order parameters fail schema validation.
- **Dependencies:** T-SYS-020 methods checklist.
- **Rationale:** The article asks for the same analysis pattern across several experiments.
- **Inference flag:** Yes.

#### T-SYS-029 - Build a reproducible many-agent environment scaffold
- **Priority / status:** P0 / new.
- **Source:** pp.7, 20-23, distributed limitation/agenda.
- **Action:** Implement vectorized N-agent local observations/actions, communication topologies, global metrics unavailable to policies, shock schedules, interaction ablations, scaling runs, and anti-centralization audits.
- **Paths:** new `research_tools/multi_agent/`; consumers T-SYS-014-016; tests under `tests/`.
- **Deliverable:** Local deterministic smoke environment plus Modal sweep adapter and standardized global/local event log.
- **Pass/fail gate:** PASS iff tests prove policies cannot read global state, N=1 reproduces the single-agent baseline, permutation of agent IDs leaves results invariant, fixed seeds reproduce trajectories, and communication/interaction edges can be causally ablated.
- **Dependencies:** T-SYS-022 design notes.
- **Rationale:** “Multiple agents” is not enough if one controller or leaked global feature still does all coordination.
- **Inference flag:** Yes.

#### T-SYS-030 - Build dynamical basin/stability analysis utilities
- **Priority / status:** P0 / new.
- **Source:** p.9 Tension; p.24 §9.5.
- **Action:** Add trajectory perturbation grids, recurrence/return-time metrics, basin labeling, Jacobian/eigenspectrum estimation, Floquet support for cycles, and uncertainty under stochastic dynamics.
- **Paths:** `research_tools/complexity_sweeps/dynamics.py` or new `research_tools/dynamics/`; synthetic tests; consumer T-SYS-006.
- **Deliverable:** API plus notebook/report example on known fixed-point, cycle, and non-attractor classifiers.
- **Pass/fail gate:** PASS iff utilities recover known basins/stability signs within tolerance on analytic fixtures and correctly refuse eigenvalue claims for non-differentiable/ill-posed maps.
- **Dependencies:** T-SYS-020.
- **Rationale:** Basin language should be backed by reusable dynamical diagnostics.
- **Inference flag:** Yes.

#### T-SYS-031 - Add a claim-evidence lint for complexity vocabulary
- **Priority / status:** P1 / new.
- **Source:** pp.20-24, scorecard and “earn the deeper words.”
- **Action:** Extend documentation/paper checks with a machine-readable ledger requiring evidence tags for `attractor`, `phase transition`, `emergence`, `self-organization`, `autopoiesis`, `distributed`, and `criticality`.
- **Paths:** new `config/complexity_claims.yaml`, extension to `scripts/run_quality_checks.py` or paper validation tools; article and paper sources.
- **Deliverable:** Lint that flags unqualified strong terms unless the artifact links the required evidence or explicitly marks metaphor/aspiration.
- **Pass/fail gate:** PASS iff seeded bad fixtures for all seven terms fail, bounded phrases pass, and existing papers can be migrated without silent exemptions.
- **Dependencies:** T-SYS-021/T-SYS-023 terminology rubrics.
- **Rationale:** The scorecard should become a durable publication guard, not remain a one-off essay.
- **Inference flag:** Yes.

### New directions to consider

#### T-SYS-032 - Adopt explicit system tiers and retire distributed language below Tier 3
- **Priority / status:** P0 / new program policy.
- **Source:** pp.5, 7, 20-23, single-agent limitation.
- **Action:** Define Tier 1 regulator (single feedback loop), Tier 2 adaptive/self-repairing agent, Tier 3 interacting population, Tier 4 emergent macro-order, and tag every experiment/paper accordingly.
- **Paths:** `docs/system_design.md`, `docs/module_explainer.md`, paper templates, T-SYS-031 ledger.
- **Deliverable:** Tier rubric and corpus audit.
- **Pass/fail gate:** PASS iff every current systems-language claim is assigned a tier, no Tier 1/2 artifact says “distributed/collective emergence” without an explicit scaffold qualifier, and promotion requires registered evidence.
- **Dependencies:** T-SYS-031.
- **Rationale:** This is the cleanest response to the article's deepest limitation.
- **Inference flag:** Yes - tier labels are proposed here.

#### T-SYS-033 - Treat thermodynamic self-maintenance as a separate research track
- **Priority / status:** P2 / new.
- **Source:** pp.24-25, §9.6.
- **Action:** Separate computational viability/resource accounting from literal thermodynamics; only merge them when a model has explicit physical units and conservation/dissipation accounting.
- **Paths:** `docs/system_design.md`, new `notes/far_from_equilibrium_scope.md`, `experiments/dissipative_homeostat/`.
- **Deliverable:** Track charter with allowed claims and progression from resource-flow toy to physically grounded model.
- **Pass/fail gate:** PASS iff all documents distinguish task reward, internal resource, free energy, and thermodynamic energy and forbid cross-level substitution without a derivation.
- **Dependencies:** T-SYS-026.
- **Rationale:** This direction can deepen the program only if it avoids thermodynamic metaphor inflation.
- **Inference flag:** Yes.

#### T-SYS-034 - Make boundary production the decisive autopoiesis frontier
- **Priority / status:** P1 / new direction.
- **Source:** pp.17-18, operational-closure definition and conclusion.
- **Action:** Reframe the next autopoiesis claim around endogenous production/repair of the sensor-action-resource boundary, not merely policy accuracy or head-weight recovery.
- **Paths:** `docs/system_design.md`, `papers/autopoietic_control/paper.md` future-work section, T-SYS-017 package.
- **Deliverable:** Boundary ontology, interventions that damage boundary/process/components separately, and closure graph.
- **Pass/fail gate:** PASS a bounded self-production claim only if boundary damage triggers endogenous component production that restores selective exchange and viability, and targeted closure-edge ablations prevent it; otherwise retain ultrastability terminology.
- **Dependencies:** T-SYS-017 and T-SYS-023.
- **Rationale:** Boundary regeneration, not generic adaptation, is the article's own strict definition of autopoiesis.
- **Inference flag:** Yes.

## Suggested execution order

1. **Truth and artifact repair:** T-SYS-001 to 004, T-SYS-031, T-SYS-032.
2. **Highest-value empirical corrections:** T-SYS-005 to 012, especially the bifurcation/hysteresis pair and quantitative Stack test.
3. **Complexity proper:** T-SYS-014/015 with T-SYS-029, then T-SYS-016.
4. **Deep-word frontier:** T-SYS-017/018/034 after the autopoiesis and viability reading audit.
5. **Separate exploratory track:** T-SYS-019/026/033; T-SYS-027 remains a no-go gate until the program has finite-size evidence.

## Counts

- Signals mapped: **32/32**.
- Executable TODOs: **34** total.
- By category: **4** article corrections/improvements; **6** old experiments to correct/replicate; **9** new experiments; **8** research/read/cite tasks; **4** software/framework tasks; **3** new directions.
- By priority: **15 P0**, **14 P1**, **3 P2**, **1 P3**. (T-SYS-019/026/033 are intentionally downstream exploratory work.)
