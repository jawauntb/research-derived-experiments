# The Lineage and the Trajectory - criticism-to-TODO audit

Source: `history_lineage_and_trajectory_primer.pdf` (27 PDF pages), checked against the source HTML and the current repository on 2026-07-13. The supplied download and `docs/primers/history_lineage_and_trajectory_primer.pdf` are byte-identical. Page references below are PDF page numbers, not printed folios.

## Article thesis

The primer argues that the program inherits a common intellectual lineage from cybernetics, autopoiesis, information theory, efficient coding, symmetry, topology, causal inference, and homeostatic reinforcement learning. Its substantive wager is that finite adaptive systems converge on geometry because geometry is a portable description of compression under constraint. Internally, the program is portrayed as a correction chain: behavioral successes are repeatedly challenged by proxies, causal interventions, gauge problems, environmental shifts, and finally external models. The mature reframe is that weakness, topology, and decodability are often *footprints*; the load-bearing cause must be demonstrated by a gauge-fixed causal effect at a commitment surface. The historical novelty claimed is therefore less a wholly new theory than a fast, machine-authored, human-directed method for turning inherited philosophical claims into preregistered, falsifiable experiments and preserving the negatives.

## Repository reconciliation

- The primer's strongest self-criticism is corroborated. `experiments/external_contact/results/p1_pythia_lora_2026_06_22.md` is a non-degenerate hard kill: weakness/OOD Spearman rho is `-0.0817`, below classical OOD NLL (`|-0.455|`), with weakness at the identity-only floor.
- The topology mediation negative is also current: `experiments/grid_cell_weakness/results/modal_grid_cell_weakness_sweep_2026_07_02.md` reports G2-G4 failures; weakness tracks a spectral aspect but neither governs torus formation nor mediates OOD.
- The effective-dimension statement is current but should cite the exact result: `experiments/grid_cell_weakness/results/reward_deformation_sweep_2026_07_02.md` gives alpha `0.302-0.309`, implying `d_eff=0.869-0.896`, not the nominal two-dimensional exponent `0.5`.
- The primer is stale on E5. Page 25 says “partly run, verdict pending,” but `experiments/commitment_surface/results/e5_generator_vs_coverage.md` records the finished 135-cell strict verdict **coverage**: generator, group-specificity, and transport gates fail.
- The frontier has also moved. E6 now has a Modal runner and real L4 smoke, but `experiments/commitment_surface/results/e6_smoke_readiness_2026_07_13.md` is blocked before round 1 because only `8/104` candidates satisfy the frozen two-surface eligibility threshold when `52` are required. E5-L, E7, and M5 remain preregistered but unbuilt/unrun.
- The TODO ledger understates completed Arc 2A work: pixel observations and a learned pixel extractor already have passing reports. The remaining perception gap is richer object-centric/natural-image perception and open-ended semantics, not pixels per se.
- Several external-contact reports named in `docs/phase2_next_phase_research_handoff.md` (`p2_uncertainty`, `p2_tier_b`, `p3_glove`, `p3_three_family`) are not present under `experiments/external_contact/results/`; the primer's three-family claim therefore lacks a tracked primary result report even though the handoff records the numbers.
- PDF visual QA covered the title/timeline (p.1), the autopoiesis warning (p.7), symmetry/topology warning (p.12), correction-chain table and warning (p.20), external-contact verdict (p.23), reframe/frontier pages (pp.24-25), and novelty/conclusion (p.27). Layout is readable. `pdfinfo`, however, reports the wrong document title: “The Mathematics of the Research Program - A Primer from First Principles.”

## Exhaustive source ledger

`E` = explicit in the primer; `I` = important action inferred from the primer plus repository reconciliation.

| Ledger | Type | PDF page / section | Short source phrase or idea | Action implication | TODOs |
|---|---|---|---|---|---|
| HL-01 | E | 5, 1.4 | “thesis as inspiration is borrowed” | Separate historical synthesis from tested novelty. | H-002, H-005 |
| HL-02 | E | 4-5, 1.2-1.3 | “compression under constraint,” not shared substrate | Test finite capacity against alternative convergence explanations. | H-002, H-201, H-202 |
| HL-03 | E | 5, 1.3 | “geometry is not proof of mind” | Enforce claim-boundary language and causal gates. | H-005, H-401 |
| HL-04 | E | 5, verdict | predictive mechanism and passive-to-active threshold remain the real novelty test | Build a claim-by-claim evidence ledger rather than repeat the grand thesis. | H-005, H-402 |
| HL-05 | E | 6, 2.2 | Wiener is “used without always crediting” | Add primary cybernetics attribution where feedback loops are implemented. | H-003, H-301 |
| HL-06 | E | 7, 2.3 | strict component-and-boundary production “is not met” | Rename existing evidence and design a strict self-production experiment. | H-004, H-105, H-203 |
| HL-07 | E | 7, 2.3 | Maturana/Varela absent from primary experiments | Cite primary autopoiesis sources in the experimental paper, not only syntheses. | H-003, H-301 |
| HL-08 | E | 7, 2.4 | program is largely Bennett's empirical test-bed | Diversify competing theories and baseline interpretations. | H-003, H-303, H-501 |
| HL-09 | E | 7, 2.5 | Levin is “scaffold,” not evidence | Preserve framing/evidence separation; test multiscale claims separately. | H-005, H-502 |
| HL-10 | E+I | 9, 3.2; 23, 8.4 | internal weakness win versus implemented MDL proxies does not externally transfer | Retain the hard kill and test stronger classical baselines/new external regimes without moving the old gate. | H-005, H-101, H-303 |
| HL-11 | E | 10, 3.3 | predicted `0.5`, measured about `0.30` | Directly measure effective dimension and rerun the exponent prediction conditionally. | H-104 |
| HL-12 | E | 12-13, 4.3-4.5 | mediation failed; “footprint, not the cause” | Preserve negative, add robustness exports, and stop calling the triangle one causal event. | H-005, H-103, H-501 |
| HL-13 | E | 12, 4.4 | cross-model Platonic mechanism failed | Restore provenance and replicate using explicit cross-substrate invariants. | H-006, H-102 |
| HL-14 | E | 14, 5.1 | decodable is observational; use is interventional | Make interventions mandatory for representational-reality claims. | H-401, H-402 |
| HL-15 | E | 15, 5.3 | viability kernels used informally; active inference only framing | Compute kernels and compare formalisms instead of borrowing vocabulary alone. | H-204, H-304 |
| HL-16 | E | 15, 5.4 | teleosemantics, natural kinds, Dretske are uncited debts | Read, cite, and use their distinctions to sharpen hypotheses. | H-003, H-302 |
| HL-17 | E | 17-18, 6.2 | whether three threads are one is open | Run a joint factorial where weakness, concern geometry, and agency can dissociate. | H-210, H-501 |
| HL-18 | E | 20, 7.2 | representation and competence are independent | Require both representation and behavior/decision gates. | H-401, H-402 |
| HL-19 | E | 20, 7.2 | smooth networks fail sharp boundaries | Finish the boundary-family replication, not a single threshold patch. | H-109 |
| HL-20 | E | 20, 7.2 | ensemble “uncertainty” does not track error | Restore external uncertainty reports and test uncertainty classes separately. | H-108 |
| HL-21 | E | 20, 7.2-7.3 | gauge-symmetric self/world split; probing fixes repeatedly miscalibrated | Consolidate probe calibration and gauge-breaking tests under one reusable suite. | H-106, H-401 |
| HL-22 | E | 20, 7.2 | shared network cannot disambiguate role-specific effects | Replace the shared head with role-conditional/modular mechanisms and preregister identifiability gates. | H-107 |
| HL-23 | E | 20-21, verdict | one self-judged chain can be self-consistent inside toy worlds | Require blind external replication and independent evaluators. | H-503 |
| HL-24 | E | 22, 8.1 | arc became “too demo-shaped” | Prefer invention of interventions/apparatus to using supplied probes. | H-205, H-401 |
| HL-25 | E | 22, 8.2 | natural images and open-ended semantics remain out of reach | Move Arc 2A/2B from generated pixels/finite DSLs to held-out natural tasks. | H-205 |
| HL-26 | E | 23, 8.3 | four “laws” crystallize internal lessons | Treat them as candidate laws until multi-domain external tests pass. | H-005, H-503 |
| HL-27 | E | 23-24, 8.4-9.1 | flagship weakness result hard-killed externally | Make the external kill the default boundary, not a footnote to the internal win. | H-001, H-005, H-101 |
| HL-28 | E | 23, 8.4 | concern geometry has wrong-sign language result | Keep family-level failures visible and retest causal rather than post-hoc deformation. | H-108, H-202 |
| HL-29 | E+I | 24-25, 9.3 | labeled coverage can mimic generator learning; E5 now says coverage | Update the article and study onset longitudinally rather than rerun E5. | H-001, H-207 |
| HL-30 | E+I | 25, 9.4 | self-training, continual learning, and plasticity-trigger frontier | Resolve E6's sparse reward and execute E5-L/E7/M5 under frozen gates. | H-206, H-207, H-208, H-209 |
| HL-31 | E | 26, 10.2 | AI pace requires guardrails against reframing, gaming, leakage | Productize preregistration, publication, and provenance checks. | H-401, H-402, H-403 |
| HL-32 | E | 27, 10.4 | much is “skilled recombination” | Calibrate originality claims and broaden the intellectual comparison set. | H-003, H-005, H-303 |
| HL-33 | E | 27, 10.5 | reach exceeds grasp on real models/open meaning | Allocate priority to external transport and stop conditions. | H-101, H-205, H-501, H-503 |
| HL-34 | E | 25, 9.4; 27, 10.5 | boldest bets remain open | Predeclare decisive outcomes that narrow or stop each direction. | H-401, H-501 |
| HL-35 | I | 1 / PDF metadata | visible title and embedded title disagree | Fix the HTML metadata and verify rebuilt PDF properties. | H-001 |
| HL-36 | I | 25, 9.3-9.4 | status prose is stale relative to E5/E6 results | Generate status blocks from a machine-readable evidence registry. | H-001, H-402 |
| HL-37 | I | 12, 4.4; repo audit | three-family result is cited in a handoff but its report is absent | Recover or rerun the report before relying on the claim. | H-006, H-102 |
| HL-38 | I | 22, 8.2; repo audit | TODO says pixel work is open although passing reports exist | Reconcile TODO with completed pixel work and state the real remaining gap. | H-001, H-205, H-402 |

## Deduplicated per-article backlog

Statuses describe repository state, not task completion: **new** = no implementation found; **partial** = relevant work exists but this action is unfinished; **existing** = evidence already exists and the remaining action is integration/maintenance.

### Article corrections and improvements

#### H-001 - Refresh metadata, experiment statuses, and the Arc 2 gap

- **Priority / status:** P0 / partial
- **Source / inference:** pp.1, 22, 25, sections 8.2, 9.3-9.4; inference from repository state (HL-27, HL-29, HL-35, HL-36, HL-38).
- **Action:** Correct the embedded PDF title; replace “E5 pending” with the strict coverage verdict; describe E6 as runner-complete but frozen-smoke-blocked; list E5-L/E7/M5 as unbuilt; change the Arc 2A gap from generic “pixels” to richer object-centric/natural-image perception.
- **Affected paths:** `docs/primers/history_lineage_and_trajectory_primer.html`, `docs/primers/history_lineage_and_trajectory_primer.pdf`, `docs/primers/README.md`, `TODO.md`.
- **Deliverable:** rebuilt primer plus a one-paragraph dated status box and synchronized TODO entries.
- **Pass/fail gate:** `pdfinfo` title exactly equals “The Lineage and the Trajectory”; text contains E5 `coverage`, E6 `8/104` versus `52`, and no “verdict pending”; TODO no longer marks completed pixel work open.
- **Dependencies:** accepted E5 and E6 public result reports.
- **Rationale:** the current historical narrative is already materially stale on its most important frontier.

#### H-002 - Turn the convergence thesis into competing historical hypotheses

- **Priority / status:** P1 / new
- **Source / inference:** pp.4-5, sections 1.2-1.4; inference is the alternative-hypothesis framing (HL-01, HL-02).
- **Action:** Add a table contrasting finite-capacity convergence with diffusion/cross-citation, shared engineering conventions, generic low-dimensional statistics, and retrospective geometric vocabulary.
- **Affected paths:** primer HTML/PDF, `papers/comprehensive_literature_review/paper.md`, proposed `docs/convergence_hypothesis_ledger.md`.
- **Deliverable:** claims/alternatives/predictions table with one discriminating observation per hypothesis.
- **Pass/fail gate:** every convergence claim has at least one rival explanation and a result that could favor the rival.
- **Dependencies:** H-201 bibliometric design.
- **Rationale:** “apparently without coordination” and “shared problem” are hypotheses, not historical facts established by recurring vocabulary.

#### H-003 - Repair the intellectual attribution graph

- **Priority / status:** P1 / partial
- **Source / inference:** pp.6-8 and 15, sections 2.2-2.6 and 5.4 (HL-05, HL-07, HL-08, HL-16, HL-32).
- **Action:** Add primary citations for Wiener, Maturana/Varela, teleosemantics, Boyd's homeostatic-property-cluster kinds, and Dretske's structuring/triggering causes to the papers that use the concepts; label Bennett-derived terminology explicitly.
- **Affected paths:** `papers/autopoietic_control/paper.md`, `papers/homeostatic_objects/paper.md`, `papers/commitment_surface/paper.md`, `papers/external_citation_review/*`, `papers/exhaustive_literature_audit/*`, `references/SOURCES.md`, primer HTML/PDF.
- **Deliverable:** concept-to-source-to-experiment attribution matrix and corrected bibliographies.
- **Pass/fail gate:** all five named gaps have primary-source entries and at least one in-text citation in the relevant primary experiment; no concept is credited only through a synthesis.
- **Dependencies:** H-301 and H-302 reading notes.
- **Rationale:** attribution makes inherited distinctions usable and prevents novelty inflation.

#### H-004 - Enforce a three-level agency vocabulary

- **Priority / status:** P0 / partial
- **Source / inference:** pp.6-8, sections 2.1-2.6 (HL-06).
- **Action:** Reserve **homeostasis** for staying in range, **ultrastability** for parameter reorganization after breach, and **autopoiesis** for endogenous production of components and boundary. Remove “self-supervised” from the labeled held-out cross-entropy repair description.
- **Affected paths:** `papers/autopoietic_control/paper.md`, primer HTML/PDF, downstream synthesis papers that call the classifier an autopoietic controller.
- **Deliverable:** terminology audit and revised claim-boundary paragraph.
- **Pass/fail gate:** searches for `autopoietic controller` and `self-supervised` either point to strict evidence or carry an adjacent explicit operational qualifier; repair method states that labels are used.
- **Dependencies:** none.
- **Rationale:** the paper's own method uses held-out labels and updates model parameters; this is strong test-time repair evidence but not strict self-production.

#### H-005 - Re-score novelty and “law” language after the external negatives

- **Priority / status:** P0 / partial
- **Source / inference:** pp.5, 12, 23-27, verdicts and conclusion (HL-01, HL-03, HL-04, HL-09, HL-10, HL-12, HL-26, HL-27, HL-32).
- **Action:** Replace unconditional “crown jewel,” “causal predictor,” “laws,” and “one event” language with domain-bounded wording; distinguish internally causal augmentation results from external predictive failure and E5 coverage confounding.
- **Affected paths:** primer HTML/PDF, `papers/weakness_invariance_neurips/paper.md`, `papers/metric_stack_synthesis/paper.md`, `docs/system_design.md`, `docs/next_agent_modal_handoff.md`.
- **Deliverable:** claim matrix with columns `internal synthetic`, `external model`, `causal`, `predictive`, `killed`, and `open`.
- **Pass/fail gate:** no headline asserts external weakness causality; the four agency laws are called candidate laws unless an external gate is cited; every novelty item links to its strongest negative.
- **Dependencies:** H-402 evidence registry.
- **Rationale:** the mature footprint/cause reframe should control the article's own rhetoric.

#### H-006 - Restore missing external-contact result provenance

- **Priority / status:** P0 / partial
- **Source / inference:** p.12, section 4.4; repository inference (HL-13, HL-37).
- **Action:** Recover the raw/source artifacts and commit public-safe reports for P2 uncertainty and P3 GloVe/three-family panels, or rerun them under frozen reconstructed manifests if recovery is impossible.
- **Affected paths:** proposed `experiments/external_contact/results/p2_uncertainty_2026_06_22.md`, `p2_tier_b_2026_06_22.md`, `p3_glove_2026_06_22.md`, `p3_three_family_2026_06_22.md`; `experiments/external_contact/PROVENANCE.md`; `docs/phase2_next_phase_research_handoff.md`.
- **Deliverable:** tracked reports with commands, manifests, row counts, gates, and claim boundaries.
- **Pass/fail gate:** every report cited by the handoff exists and passes `scripts/publication_guard.py`; reported P3 pairwise RSA values reproduce exactly or the primer removes them.
- **Dependencies:** artifact availability; otherwise a new preregistration.
- **Rationale:** a history cannot treat a handoff summary as the primary evidentiary record.

### Old experiments to correct or replicate

#### H-101 - Treat Pythia P1 as an accepted kill; run only a genuinely new external regime

- **Priority / status:** P0 / existing
- **Source / inference:** pp.23-24, sections 8.4 and 9.1 (HL-10, HL-27, HL-33).
- **Action:** Do not tune or rerun the same LoRA panel. Preregister one discriminating extension using public grokking checkpoints or full two-input modular addition, with the old P1 gate preserved and a stop rule after one external family.
- **Affected paths:** `experiments/external_contact/results/p1_pythia_lora_2026_06_22.md`, proposed new external-contact preregistration/runner/result, `papers/weakness_invariance_neurips/paper.md`.
- **Deliverable:** either one non-degenerate external replication or an explicit retirement note.
- **Pass/fail gate:** outcome has at least five distinct OOD values, non-identity weakness variance, wrong-group null, and the unchanged rho/margin gate; failure retires universal weakness-to-OOD work.
- **Dependencies:** H-403 model adapter.
- **Rationale:** repeating Pythia with tuned choices would erase rather than learn from the hard kill.

#### H-102 - Rebuild the cross-substrate geometry test around explicit invariant types

- **Priority / status:** P1 / partial
- **Source / inference:** pp.12-13, sections 4.4-4.5 (HL-13, HL-37).
- **Action:** Restore P3 first, then compare linear RSA, kernel alignment, topology, dynamics, and intervention effects separately across at least three unrelated model families.
- **Affected paths:** `experiments/concept_geometry/`, `experiments/activation_geometry/`, `experiments/external_contact/`, proposed `papers/cross_substrate_geometry/`.
- **Deliverable:** preregistered invariant-by-model matrix with family-level results.
- **Pass/fail gate:** a convergence claim passes only if one invariant clears a frozen threshold for every family and its matched random/semantic-frequency control fails; pooled averages cannot rescue a family failure.
- **Dependencies:** H-006 and H-403.
- **Rationale:** “same geometry” is underspecified, and the historical claim changes with the equivalence relation.

#### H-103 - Complete the grid-cell negative with topology robustness and external recordings

- **Priority / status:** P1 / partial
- **Source / inference:** pp.11-13, sections 4.2-4.5 (HL-12).
- **Action:** Rerun the existing registered cells with hidden-state/topology robustness exports, then apply the frozen weakness/H1 prediction to Gardner-style recordings if access is possible.
- **Affected paths:** `experiments/grid_cell_weakness/modal_grid_cell_weakness_sweep.py`, `experiments/grid_cell_weakness/results/`, `papers/grid_cell_weakness/`, `TODO.md`.
- **Deliverable:** bin/edge-cap/sample-density sensitivity report plus a public-data replication or a documented access block.
- **Pass/fail gate:** torus classification is stable across preregistered topology settings; the mediation verdict remains negative unless the original G4 threshold passes on untouched cells; biological test reports a frozen correlation CI.
- **Dependencies:** data license/access and stored hidden-state exports.
- **Rationale:** the negative mediation result is publishable; robustness and biological contact are more valuable than another internal mediation tweak.

#### H-104 - Replace inferred effective dimension with a measured dimension-conditioned law

- **Priority / status:** P1 / partial
- **Source / inference:** p.10, section 3.3 (HL-11).
- **Action:** Measure deformation-rank/effective dimension independently (local PCA/Jacobian spectrum), then predict alpha per cell before fitting it across isotropic 2-D, anisotropic 2-D, stripe, and amplitude conditions.
- **Affected paths:** `experiments/grid_cell_weakness/modal_reward_deformation_sweep.py`, `experiments/grid_cell_weakness/results/reward_deformation_sweep_2026_07_02.md`, `papers/pdf/reward_deformation_effective_dimension_law.pdf` and source.
- **Deliverable:** preregistered cell-level `d_eff -> alpha=d/(d+2)` calibration report.
- **Pass/fail gate:** out-of-sample predicted-versus-measured alpha slope CI contains 1, intercept CI contains 0, and nominal `d=2` remains rejected if the measured rank is near 1.
- **Dependencies:** metric-deformation state exports.
- **Rationale:** deriving dimension from the same fitted exponent is circular evidence for the explanation.

#### H-105 - Correct the repair experiment with label-free and body-level controls

- **Priority / status:** P1 / partial
- **Source / inference:** pp.6-7, sections 2.1-2.3 (HL-06).
- **Action:** Replicate weight-noise recovery with (a) pseudo-label/self-distillation updates, (b) no-label reconstruction/prediction, (c) shuffled labels, and (d) policy/body damage rather than classifier-head-only damage.
- **Affected paths:** `experiments/autopoietic_control/`, `papers/autopoietic_control/paper.md`, tests and results.
- **Deliverable:** correction paper separating supervised reacquisition, ultrastable repair, and boundary/component production.
- **Pass/fail gate:** label-free arm beats frozen/no-update and shuffled-label controls on predeclared recovery AUC; claims remain “ultrastability” unless H-203's production gates pass.
- **Dependencies:** H-004 terminology audit.
- **Rationale:** existing recovery is real but labeled test-time optimization can simply reteach the answer.

#### H-106 - Consolidate the probing correction chain into a cross-world calibration suite

- **Priority / status:** P1 / partial
- **Source / inference:** p.20, sections 7.2-7.3 (HL-21).
- **Action:** Put naive error, stale average, current-model error, scale-normalized error, expected information gain, and oracle value under identical stationary, heteroscedastic, abrupt-shift, and responsive-world conditions.
- **Affected paths:** `experiments/{costly_null_probes,current_error_calibration,scale_normalized_vprobe,probe_value_reengagement,world_responds}/`, proposed shared `experiments/probe_calibration_suite/`.
- **Deliverable:** one preregistered selector-by-world calibration matrix with preserved failed variants.
- **Pass/fail gate:** a promoted selector must have positive calibration in every required world, beat matched-random value net of cost, and pass false-calm/re-engagement controls; no pooled rescue.
- **Dependencies:** shared schema from H-401.
- **Rationale:** four papers fixed one signal locally; a unified suite tests whether the fix generalizes.

#### H-107 - Resolve the role-specific architectural ceiling

- **Priority / status:** P1 / partial
- **Source / inference:** p.20, section 7.2 (HL-22).
- **Action:** Compare shared, role-conditioned, modular-mixture, and intervention-routed heads on mediated/exogenous decomposition with matched capacity and explicit gauge-breaking contrasts.
- **Affected paths:** `experiments/role_specific_identifiability/`, `papers/role_specific_identifiability/`, `experiments/viable_computational_bodies/`.
- **Deliverable:** frozen architecture ablation and causal identifiability report.
- **Pass/fail gate:** food-versus-medicine mediated predictions separate by the preregistered margin, each component MAE clears its gate, and matched wrong-role/shuffled-intervention controls fail.
- **Dependencies:** none.
- **Rationale:** the primer says the next question is structural, so further optimizer tuning is not responsive.

#### H-108 - Reconcile “uncertainty” and concern-geometry external results by mechanism

- **Priority / status:** P1 / partial
- **Source / inference:** pp.20 and 23, sections 7.2 and 8.4 (HL-20, HL-28).
- **Action:** Restore P2 reports, distinguish entropy from ensemble variance and blur from noise/brightness, and report post-hoc encoder deformation separately from train-time causal deformation.
- **Affected paths:** H-006 report paths, `experiments/phase6_real_model_validation/`, `papers/phase6_real_model_validation/paper.md`, primer HTML/PDF.
- **Deliverable:** mechanism-stratified external scorecard.
- **Pass/fail gate:** every statement names uncertainty type, shift family, and intervention timing; wrong-sign/family failures remain visible.
- **Dependencies:** H-006.
- **Rationale:** broad “uncertainty decouples” or “metric deformation transfers” language conceals opposite outcomes across operationalizations.

#### H-109 - Finish the sharp-boundary diagnosis as a function-family study

- **Priority / status:** P2 / partial
- **Source / inference:** p.20, section 7.2 (HL-19).
- **Action:** Sweep boundary location and sharpness with smooth, piecewise, gated, and explicit-regime models; evaluate both pointwise calibration and policy-induced occupancy.
- **Affected paths:** `experiments/{off_policy_state_coverage,regime_sensitive_de}/`, `papers/{off_policy_state_coverage,regime_sensitive_de}/`.
- **Deliverable:** preregistered boundary phase diagram.
- **Pass/fail gate:** failure location tracks the moved boundary; accuracy is reported by distance-to-boundary and along policy trajectories; explicit-regime model must clear the boundary gate without oracle leakage.
- **Dependencies:** none.
- **Rationale:** a single discontinuity at `E=0.5` cannot establish a general architectural limitation.

### New experiments

#### H-201 - Test whether intellectual convergence is independent or diffusive

- **Priority / status:** P1 / new
- **Source / inference:** pp.4-5, chapter 1; inferred discriminating test (HL-02).
- **Action:** Build a dated citation/terminology graph for geometry, constraint, manifold, attractor, compression, and viability across the named fields; compare observed cross-field timing to diffusion-aware nulls.
- **Affected paths:** proposed `experiments/intellectual_convergence/`, `papers/intellectual_convergence/`, `references/SOURCES.md`.
- **Deliverable:** public bibliometric dataset, preregistration, and analysis.
- **Pass/fail gate:** the finite-capacity convergence reading is supported only if independent adoptions exceed the citation-diffusion null and precede direct cross-field links at a frozen rate.
- **Dependencies:** licensed bibliographic metadata.
- **Rationale:** this directly tests the historical premise rather than treating the repeated vocabulary as self-authenticating.

#### H-202 - Causally manipulate capacity, concern, and shared statistics

- **Priority / status:** P1 / new
- **Source / inference:** pp.4-5 and 23, sections 1.2-1.3 and 8.4; inferred factorial (HL-02, HL-28).
- **Action:** Cross capacity bottleneck on/off, concern weighting on/off, task symmetry aligned/misaligned, and input covariance matched/mismatched across RNN/Transformer/JEPA families.
- **Affected paths:** proposed extension under `experiments/grid_cell_weakness/` or `experiments/constraint_convergence_factorial/`; new preregistration/paper.
- **Deliverable:** 2x2x2 causal factorial separating finite capacity from generic shared statistics.
- **Pass/fail gate:** geometry attributed to capacity must show an interaction with bottleneck strength, survive covariance-matched controls, move with concern location, and transport across architectures.
- **Dependencies:** H-104 metrics.
- **Rationale:** the thesis claims a mechanism; causal manipulation is stronger than observing similar shapes.

#### H-203 - Build a strict minimal autopoiesis benchmark

- **Priority / status:** P1 / new
- **Source / inference:** p.7, section 2.3; experiment is inferred from the explicit missing criterion (HL-06).
- **Action:** Create an environment where an agent must synthesize/replace its own functional components and reconstruct a permeability boundary using internally generated policy, under matched homeostasis-only and externally repaired controls.
- **Affected paths:** proposed `experiments/minimal_autopoiesis/`, `papers/minimal_autopoiesis/`, benchmark card and tests.
- **Deliverable:** preregistered benchmark with production-closure, boundary-regeneration, viability, and novelty gates.
- **Pass/fail gate:** after component/boundary ablation, the autonomous arm restores both without labels or external repair actions; homeostasis-only and scripted-repair controls fail production closure.
- **Dependencies:** H-004, H-105, primary definitions from H-301.
- **Rationale:** this is the shortest path from aspirational vocabulary to the criterion the primer says is unmet.

#### H-204 - Compute formal viability kernels and compare them with the heuristic buffer

- **Priority / status:** P1 / new
- **Source / inference:** p.15, section 5.3 (HL-15).
- **Action:** On small exact MDPs, compute Aubin-style viability kernels by dynamic programming/reachability and compare them with the program's extension-count “viability buffer” under controlled disturbances.
- **Affected paths:** proposed `experiments/formal_viability_kernel/`, `papers/formal_viability_kernel/`, `papers/concern_weighted_weakness/paper.md`.
- **Deliverable:** exact-kernel oracle, approximation method, and failure map.
- **Pass/fail gate:** preregistered rank correlation/coverage thresholds hold across at least three dynamics families; counterexamples are preserved and delimit when “buffer” may be used.
- **Dependencies:** H-304 literature synthesis.
- **Rationale:** the current work borrows viability-theory language without evaluating the mathematical object.

#### H-205 - Advance intervention invention to natural images and open semantics

- **Priority / status:** P0 / partial
- **Source / inference:** p.22, sections 8.1-8.2 (HL-24, HL-25, HL-33, HL-38).
- **Action:** Replace generated shapes/finite program DSLs with held-out natural-image tasks whose useful intervention vocabulary and semantic categories are not supplied; require transfer to a new dataset/domain.
- **Affected paths:** `experiments/concerned_syntax/`, `experiments/viable_computational_bodies/`, new preregistrations/results, `TODO.md`.
- **Deliverable:** natural-image intervention-invention benchmark and executable neural-module body search.
- **Pass/fail gate:** learned system discovers an intervention category not enumerated in the training scaffold, beats supplied-vocabulary/uncertainty/compression controls, passes low-concern anti-probing, and transfers across datasets.
- **Dependencies:** H-403 dataset adapters and executable neural modules.
- **Rationale:** pixel rendering already passes; scaffold removal and semantic openness are the real remaining tests.

#### H-206 - Redesign E6 around preregistered reward-density feasibility

- **Priority / status:** P0 / partial
- **Source / inference:** p.25, section 9.4 plus current smoke (HL-30).
- **Action:** Preserve frozen E6 as a blocked readiness result. Draft a new preregistration that first estimates the density of transport-surviving patch-CE rewards without using correctness, then chooses a selection contract before any self-training result is seen.
- **Affected paths:** `experiments/commitment_surface/e6_*`, `experiments/commitment_surface/results/e6_smoke_readiness_2026_07_13.md`, new E6b preregistration/runner/result.
- **Deliverable:** reward-density diagnostic, frozen feasible E6b design, dev calibration, and confirmatory trajectory or kill.
- **Pass/fail gate:** round-1 matched exposure is feasible in every dev stratum without threshold retuning; confirmatory G1-G4 and integrity gates remain frozen and all round trajectories are reported.
- **Dependencies:** current E6 smoke and compute budget approval.
- **Rationale:** `8/104` eligible cannot satisfy a 52-candidate matched-volume contract; lowering gates post hoc would invalidate the experiment.

#### H-207 - Run E5-L longitudinal generator-versus-coverage separation

- **Priority / status:** P1 / partial
- **Source / inference:** pp.24-25, sections 9.3-9.4 (HL-29, HL-30).
- **Action:** Build the frozen per-round runner and test whether self-training collapse onset coincides with coverage gain without generator gain.
- **Affected paths:** `papers/commitment_surface/e5_longitudinal_self_training_preregistration_2026-07-13.md`, proposed runner under `experiments/commitment_surface/`, result and paper updates.
- **Deliverable:** 810-cell public-safe trajectory summary under the existing preregistration.
- **Pass/fail gate:** exact grid/integrity passes; per-round generator gain, coverage gain, group specificity, and normalized patch-CE are emitted; no aggregate-only verdict.
- **Dependencies:** reusable E5 runner/manifest discipline and budget approval.
- **Rationale:** E5 resolved the static confound as coverage; E5-L tests whether that mechanism explains dynamics.

#### H-208 - Execute E7 selective subspace protection

- **Priority / status:** P1 / partial
- **Source / inference:** p.25, section 9.4 (HL-30).
- **Action:** Implement the frozen P_sub/P_ewc/P_none/P_wrong continual-learning stream and compare retention, causal patch-CE, new-task learning, and protected-rank cost.
- **Affected paths:** `papers/commitment_surface/e7_selective_subspace_continual_learning_preregistration_2026-07-13.md`, `experiments/commitment_surface/e2_e3_neural_sweep.py`, new E7 runner/tests/results.
- **Deliverable:** CPU confirmatory result with complete task-by-task trajectories.
- **Pass/fail gate:** use the preregistered Pareto/retention/plasticity gates without retuning; wrong-subspace must not reproduce the benefit.
- **Dependencies:** #344 subspace implementation.
- **Rationale:** this is the cleanest direct test of whether a commitment-surface diagnostic is useful for learning.

#### H-209 - Execute M5 commitment-change plasticity trigger

- **Priority / status:** P1 / partial
- **Source / inference:** p.25, section 9.4 (HL-30).
- **Action:** Implement only the trigger swap specified by the frozen preregistration and compare commitment-change, utility/age, normalized drift, periodic, and never-reopen arms at matched budgets.
- **Affected paths:** `experiments/world_responds/suite_c_reopen_reset_trigger_preregistration_2026-07-13.md`, `suite_c_factorial_ablation.py`, new runner/tests/results.
- **Deliverable:** eight-seed paired bootstrap report with byte-stability check.
- **Pass/fail gate:** F0-F5 exactly as frozen; especially lower false-reopen and non-worse latency versus every internal-statistic trigger.
- **Dependencies:** M4 reference artifacts.
- **Rationale:** it directly tests the primer's proposed commitment-change plasticity signal and is cheaper than E6/E5-L.

#### H-210 - Make the three-thread unity claim falsifiable in one system

- **Priority / status:** P1 / new
- **Source / inference:** pp.17-18, section 6.2 (HL-17).
- **Action:** In one shared environment, independently manipulate group compatibility, concern weighting, and action coupling, measuring weakness, metric deformation, topology, behavior, and causal commitment effects.
- **Affected paths:** proposed `experiments/three_thread_factorial/`, `papers/three_thread_factorial/`.
- **Deliverable:** preregistered mediation/dissociation factorial.
- **Pass/fail gate:** “one optimization” survives only if predeclared cross-thread mediation holds and single-factor controls cannot dissociate the measures; otherwise publish a typed map of independent footprints.
- **Dependencies:** H-202 and stable commitment-effect metrics.
- **Rationale:** the primer explicitly calls unity the open question around which the trajectory circles.

### Research to read, internalize, and cite

#### H-301 - Primary cybernetics, autopoiesis, and enactivism dossier

- **Priority / status:** P1 / partial
- **Source / inference:** pp.6-8, chapter 2 (HL-05, HL-07).
- **Action:** Read and annotate Wiener, Ashby, Maturana/Varela, Thompson, and Di Paolo against the exact implemented mechanisms.
- **Affected paths:** proposed `references/reading_notes/cybernetics_autopoiesis.md`, `references/SOURCES.md`, H-003 paper paths.
- **Deliverable:** claim-source-operation table distinguishing feedback, ultrastability, adaptivity, operational closure, and autopoiesis.
- **Pass/fail gate:** every term used in a primary paper has a page-level source and an explicit operational match/mismatch note.
- **Dependencies:** source access.
- **Rationale:** the primer itself says the oldest lineage is invoked unevenly and often through Bennett.

#### H-302 - Teleosemantics, causal-role kinds, and causal-use dossier

- **Priority / status:** P1 / new
- **Source / inference:** p.15, section 5.4 (HL-16).
- **Action:** Read Millikan, Dretske, Papineau, and Boyd; translate proper function, structuring/triggering cause, and homeostatic-property-cluster kinds into competing experimental predictions.
- **Affected paths:** proposed `references/reading_notes/teleosemantics_natural_kinds.md`, `papers/homeostatic_objects/paper.md`, `papers/commitment_surface/paper.md`.
- **Deliverable:** literature matrix plus at least three preregisterable discriminators.
- **Pass/fail gate:** each source changes or sharpens a concrete hypothesis/control, not merely the bibliography.
- **Dependencies:** source access.
- **Rationale:** these literatures already contain distinctions the program currently rediscovers.

#### H-303 - Strong alternatives to weakness dossier

- **Priority / status:** P1 / partial
- **Source / inference:** pp.9 and 27, sections 3.2 and 10.4 (HL-08, HL-10, HL-32).
- **Action:** Benchmark the program's claims against modern MDL, PAC-Bayes, function-space priors, IRM/group DRO, causal representation learning, grokking, and learned-equivariance work rather than simple stand-ins.
- **Affected paths:** `papers/weakness_invariance_neurips/paper.md`, proposed `references/reading_notes/weakness_competitors.md`, H-101/H-210 preregistrations.
- **Deliverable:** baseline-access table and prioritized implementations.
- **Pass/fail gate:** every “beats classical simplicity” statement lists the exact implemented proxy; at least one strong modern baseline enters the next confirmatory external test.
- **Dependencies:** none.
- **Rationale:** the current paper responsibly calls its MDL/flatness measures proxies; the primer's rhetoric should be equally narrow.

#### H-304 - Viability theory versus active inference comparison

- **Priority / status:** P2 / partial
- **Source / inference:** p.15, section 5.3 (HL-15).
- **Action:** Read Aubin viability theory and formal active-inference/expected-free-energy treatments; map where each predicts different probing or control behavior from the current value-of-information rule.
- **Affected paths:** proposed `references/reading_notes/viability_active_inference.md`, `papers/concern_weighted_weakness/paper.md`, H-204/H-106 designs.
- **Deliverable:** notation crosswalk and two discriminating experiments.
- **Pass/fail gate:** each borrowed term has an equation-level mapping or is labeled framing-only; at least one case yields opposite policy predictions.
- **Dependencies:** source access.
- **Rationale:** implementing a formalism is more informative than citing it as broad interpretive support.

### Software, framework, and skill work

#### H-401 - Create a proxy-resistant experiment-package skill

- **Priority / status:** P0 / partial
- **Source / inference:** pp.17-26, correction chain and machine-authorship sections (HL-03, HL-14, HL-18, HL-21, HL-24, HL-31, HL-34).
- **Action:** Turn the repository's best practices into a reusable Codex skill/template: competing hypotheses, frozen gates, anti-cheat controls, observational-versus-interventional metric tags, dry-run/dev/confirmatory states, public-safe outputs, negative-result publication, and documentation/provenance hooks.
- **Affected paths:** proposed repo-local `.agents/skills/proxy-resistant-experiment/SKILL.md` or personal skill, template assets/scripts, `docs/system_design.md`, `docs/module_explainer.md`.
- **Deliverable:** skill plus one generated example experiment package and validation tests.
- **Pass/fail gate:** generated package includes preregistration, runner, tests, manifest, results schema, claim boundary, publication guard, provenance, and docs stubs; a deliberate leakage fixture fails validation.
- **Dependencies:** follow the `skill-creator` workflow when implemented.
- **Rationale:** this directly answers the request for a science-experiment ML repository framework skill and encodes the correction chain as infrastructure.

#### H-402 - Add a machine-readable evidence and status registry

- **Priority / status:** P0 / new
- **Source / inference:** pp.24-27 plus repository drift (HL-04, HL-14, HL-18, HL-31, HL-36, HL-38).
- **Action:** Define one registry row per claim/experiment with preregistration, implementation, run, verdict, claim tier, supersessions, negative, and public artifact hashes; render TODO/status/primer tables from it.
- **Affected paths:** proposed `docs/evidence_registry.yaml`, schema/test/generator under `scripts/`, generated sections in `TODO.md`, `docs/verification.md`, and primers.
- **Deliverable:** validated registry and generated status pages.
- **Pass/fail gate:** CI fails on a claimed result with missing report/hash, impossible status transition, or stale generated block; E5/E6/Arc2 pixel states render correctly.
- **Dependencies:** H-006 artifact repair.
- **Rationale:** a stateless-agent lab needs one authoritative memory rather than divergent handoffs, TODOs, and prose.

#### H-403 - Build external-replication adapters and provenance checks

- **Priority / status:** P1 / partial
- **Source / inference:** pp.20-23 and 26, external-check and memory-infrastructure critique (HL-23, HL-31, HL-33).
- **Action:** Standardize model, dataset, intervention, and metric adapters so the same frozen experiment can run across unrelated external families; record revisions/licenses/splits privately while publishing safe hashes.
- **Affected paths:** proposed `research_harness/external/`, refactors in `experiments/external_contact/` and `phase6_real_model_validation/`, tests, `scripts/publication_guard.py`.
- **Deliverable:** adapter API with at least three model families and two datasets, deterministic manifests, and public-safe release schema.
- **Pass/fail gate:** byte-identical manifest on rerun; no model IDs/secrets leak where forbidden; same gate code executes unchanged across families; a missing revision or split hash fails closed.
- **Dependencies:** H-401 schema conventions.
- **Rationale:** external contact should vary the substrate, not quietly vary the measurement contract.

### New directions to consider

#### H-501 - Pivot from a universal weakness scalar to a regime map

- **Priority / status:** P0 / partial
- **Source / inference:** pp.12, 23-25, footprint/cause reframe; direction is inferred (HL-08, HL-12, HL-17, HL-33, HL-34).
- **Action:** Model when a scored transformation family matches the deployment generator, when it is merely correlated, and when topology/geometry/weakness dissociate; publish a typed regime map with stopping rules.
- **Affected paths:** `papers/commitment_surface/paper.md`, `papers/concern_weighted_weakness/paper.md`, H-101/H-102/H-210 outputs.
- **Deliverable:** decision tree mapping observable assumptions to permitted claims and next experiment.
- **Pass/fail gate:** every regime has a falsifier and a “do not use weakness” condition; another external hard kill in an aligned, non-degenerate regime retires the universal scalar framing.
- **Dependencies:** H-402 registry.
- **Rationale:** the negatives support conditional diagnostic value, not a substrate-independent law.

#### H-502 - Seek biological and multiscale agency contact only with operational matches

- **Priority / status:** P2 / new
- **Source / inference:** pp.7, 11-12, Levin/grid-cell lineage; direction is inferred (HL-09, HL-12).
- **Action:** Prioritize one public neural recording test and one multiscale repair/control dataset where the program's metric, intervention, and boundary have direct operational correspondents.
- **Affected paths:** proposed `experiments/biological_external_contact/`, H-103 result, new preregistration/paper.
- **Deliverable:** two feasibility cards and at most one preregistered pilot per domain.
- **Pass/fail gate:** no study launches without a matched variable/intervention/commitment-surface table and a negative control; inaccessible or mismatched data yields a documented no-go, not a proxy substitution.
- **Dependencies:** data access and domain collaborator review.
- **Rationale:** Levin and autopoiesis are currently scaffold-level; biological contact is valuable only if the operationalization survives transport.

#### H-503 - Make independent replication a gate for machine-made science

- **Priority / status:** P0 / new
- **Source / inference:** pp.20-21 and 26-27, self-judged-chain and AI-authorship discussion (HL-23, HL-31, HL-33).
- **Action:** Package one flagship positive and one flagship negative for blind reproduction by a separate human/agent team that cannot see the original results until gates are frozen.
- **Affected paths:** proposed `replications/`, public release bundles, `docs/verification.md`, `docs/publication_sharing_map.md`.
- **Deliverable:** sealed manifests, reproduction instructions, independent reports, and discrepancy ledger.
- **Pass/fail gate:** reproducer rebuilds environment and verdict from public artifacts; any discrepancy changes the evidence tier; no “law” or cross-substrate novelty claim advances without one independent pass.
- **Dependencies:** H-401, H-402, H-403.
- **Rationale:** external models are not the same as external judgment; the primer identifies same-system authorship and adjudication as a structural risk.

## Coverage and deduplication notes

- Every ledger item HL-01 through HL-38 maps to at least one TODO in the final column; no criticism is left as prose-only advice.
- The E5 confound is not proposed as a new static run: H-001 integrates the completed **coverage** verdict and H-207 moves to the already preregistered longitudinal question.
- The Pythia external hard kill is not proposed again with tuned gates: H-101 preserves it and permits only one genuinely different, preregistered external regime with a retirement rule.
- Pixel Arc 2A work is not re-proposed: H-001 corrects the stale TODO and H-205 targets the remaining natural-image/open-semantics/scaffold-removal gap.
- The topology mediation failure is not treated as an unrun idea: H-103 protects the negative and adds robustness/biological contact.
- Inference-only additions are explicitly marked in the source ledger (`I`) and in each TODO's source/inference field. The principal inferences are the metadata/status fixes, bibliometric test, causal capacity factorial, strict autopoiesis benchmark, joint three-thread factorial, infrastructure skill/registry, regime-map pivot, biological contact, and independent replication gate.
- Suggested execution order: H-001/H-004/H-005/H-006 (repair the public record), H-401/H-402 (prevent recurrence), H-206/H-209/H-208/H-207 (frontier under frozen gates), then H-101/H-102/H-205/H-210 (decisive external and unification tests). H-201/H-203/H-204 are higher-cost new programs and should wait for preregistration review.
