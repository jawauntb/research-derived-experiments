# Discovery-Regime Audit Ledger

## Project Regime: Initial Publication

Question: how do we turn the paper synthesis into a public, reproducible research workspace without publishing local-only source archives or secrets?

Current regime:

- Artifact types: synthesis notes, source manifest, TODO ledger, experiment scripts, result JSON, audit cards, rejected alternatives.
- Operations: source archiving, text extraction, synthesis, synthetic simulation, env probing, publication guard, GitHub PR workflow.
- Gates/verifiers: no tracked files over 10 MB, no tracked local source archives, no obvious secret values, Python unit tests, syntax checks, publication guard, human review.
- Known limitations: paper PDFs and full extracted text are local-only; Authorea blocked direct download, but a local PDF with the same DOI is archived.

Action class:

- Retrieval/search/discovery: retrieval plus initial search.
- Why: publication adds already representable artifacts; the first synthetic experiment searches inside the weakness-vs-simplicity schema.

Gate:

- Acceptance rule: public repo can be pushed without large files, full extracted corpora, or secrets; first experiment produces deterministic output and unit tests pass.
- Withheld/rejected rule: full PDFs, extracted text, raw API outputs, and any secret-bearing artifacts stay untracked.

Results:

- Accepted artifacts: `experiments/weakness_vs_simplicity/results/pilot_2026_06_08.md`.
- Rejected or withheld artifacts: `references/papers/`, `references/text/`, `references/html/`.
- Key metrics: trap condition weakness mean Jaccard 0.9533; simplicity mean Jaccard 0.0938; random mean Jaccard 0.5061. No-memorizer control weakness mean Jaccard 0.9587; simplicity mean Jaccard 0.9493. Broad-negative-excluder stress weakness mean Jaccard 0.5246; simplicity mean Jaccard 0.9560. Validated-weakness stress validated weakness mean Jaccard 1.0000; pure weakness mean Jaccard 0.5246.
- Variance or ablation: no-memorizer control, unsafe broad-hypothesis stress test, and validation-gated stress run added.

Residual content:

- Explained by old regime: source collection and synthesis.
- New content outside old regime: none yet.
- Retractions or supersessions: none.

Environment note: `superoptimizers` has Doppler project `cofounder` / config `dev` configured. Presence-only probe found OpenAI, Anthropic, Gemini, Hugging Face, and Modal token variables available. No secret values are recorded here.

Next move: run seed/feature sweeps, then move to text/classification prompts or model-derived rule proposals.

## Concept Geometry Probe: OpenAI Embeddings

Question: can model embeddings make the cross-field geometry convergence hypothesis concrete enough to guide follow-up experiments?

Current regime:

- Artifact types: curated concept prompts, embedding vectors, cosine kernels, category labels, nearest-neighbor summaries, audit cards.
- Operations: OpenAI embedding call, cosine kernel construction, within/across category comparison, top-k neighbor inspection.
- Gates/verifiers: category separation threshold, same-category top-k threshold, qualitative bridge inspection, publication guard.
- Known limitations: hand-curated prompts and labels; language embeddings can encode discourse similarity without proving shared dynamics.

Action class:

- Retrieval/search/discovery: search.
- Why: this explores a model-backed concept geometry within the existing schema.

Gate:

- Acceptance rule: within-category mean cosine exceeds across-category mean cosine by at least `0.10`; top-3 same-category neighbor rate is at least `0.40`; bridge neighborhoods appear among core convergence terms.
- Withheld/rejected rule: raw embeddings and secret-bearing runtime context stay local-only.

Results:

- Accepted artifacts: `experiments/concept_geometry/results/openai_embedding_probe_2026_06_08.md`.
- Rejected or withheld artifacts: `artifacts/concept_geometry/openai_embedding_probe.json`.
- Key metrics: within-category mean cosine `0.4513`; across-category mean cosine `0.2781`; category separation `0.1732`; mean top-3 same-category rate `0.5417`.
- Variance or ablation: deterministic dry-run exists for tooling checks; paraphrase and second-model replications remain open.

Residual content:

- Explained by old regime: ordinary language similarity can explain much of the embedding-space structure.
- New content outside old regime: the model places several cross-field bridges in the neighborhoods we care about, including attractor/attractor-network, conceptual-space/representation-manifold, and valence/activation-vector.
- Retractions or supersessions: this should not be cited as evidence of shared active attractor dynamics.

Next move: run paraphrase perturbations and a second embedding model before moving to activation-space probes.

## Concept Geometry Probe: Paraphrase Stability

Question: does the concept-neighborhood signal survive wording perturbation and a second embedding model?

Current regime:

- Artifact types: concept prompts, paraphrase variants, embedding vectors, concept centroids, bridge-pair scores, cross-model kernel summaries.
- Operations: paraphrase expansion, OpenAI embedding calls, centroid construction, cosine-kernel comparison, bridge-pair scoring.
- Gates/verifiers: paraphrase cohesion, centroid category separation, top-k category rate, cross-model kernel correlation, cross-model neighbor overlap, publication guard.
- Known limitations: evidence remains inside language embedding models; paraphrases and bridge pairs are hand-authored.

Action class:

- Retrieval/search/discovery: search.
- Why: this stress-tests an existing concept-geometry claim without changing the artifact schema or adding an activation-space verifier.

Gate:

- Acceptance rule: mean paraphrase cohesion at least `0.70`; minimum concept mean cohesion at least `0.60`; centroid category separation at least `0.10`; mean top-3 same-category rate at least `0.40`; cross-model kernel Pearson at least `0.80`; cross-model neighbor overlap at least `0.50`.
- Withheld/rejected rule: raw embeddings and model payloads stay local-only under `artifacts/`.

Results:

- Accepted artifacts: `experiments/concept_geometry/results/paraphrase_stability_openai_2026_06_08.md`.
- Rejected or withheld artifacts: `artifacts/concept_geometry/paraphrase_stability_openai.json`.
- Key metrics: small-model paraphrase cohesion `0.7685`; large-model paraphrase cohesion `0.7835`; small-model category separation `0.1661`; large-model category separation `0.1559`; cross-model kernel Pearson `0.8884`; cross-model neighbor overlap `0.7292`.
- Variance or ablation: 72 paraphrase variants across two OpenAI embedding models.

Residual content:

- Explained by old regime: language-level semantic similarity can still explain most of the geometry.
- New content outside old regime: the bridge geometry is paraphrase-invariant and model-stable enough to justify moving into activation-space probes.
- Retractions or supersessions: single-prompt embedding claims should now be treated as weaker than paraphrase-centroid claims.

Next move: extract activation vectors from open models and test whether the same bridge directions appear outside embedding-only language space.

## Activation Geometry Probe: Modal Pythia-70M

Question: does the embedding-space bridge geometry appear in open-model hidden states?

Current regime:

- Artifact types: paraphrased concept prompts, pooled hidden-state vectors, raw and mean-centered concept centroids, bridge-pair scores, activation-space audit cards.
- Operations: Modal-backed open-model extraction, attention-mean pooling, global mean-centering, cosine-kernel summary, bridge-lift comparison.
- Gates/verifiers: deterministic dry-run control, anisotropy inspection, category separation threshold, bridge-lift threshold, bridge-pair rate threshold, publication guard.
- Known limitations: one small model, one layer, one pooling rule, hand-authored bridge pairs, no causal intervention yet.

Action class:

- Retrieval/search/discovery: discovery-leaning search.
- Why: this adds activation-space vectors as a new artifact class for the project, but the result still needs layer/model replication before we should call it a stable mechanism.

Gate:

- Acceptance rule: mean-centered category separation at least `0.05`, bridge lift at least `0.05`, and at least `0.75` of bridge pairs above the non-bridge cross-category mean.
- Withheld/rejected rule: raw activation arrays and full model payloads stay local-only under `artifacts/`.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/modal_pythia_70m_layer_last_2026_06_08.md`.
- Rejected or withheld artifacts: `artifacts/activation_geometry/modal_pythia_70m_layer_last.json`.
- Key metrics: raw category separation `0.0002`; raw bridge lift `0.0002`; mean-centered category separation `0.1356`; mean-centered bridge lift `0.1957`; mean-centered bridge-pair above-baseline rate `0.9167`.
- Variance or ablation: raw-vs-centered comparison and deterministic dry-run only.

Residual content:

- Explained by old regime: language-level concept similarity may still drive the bridge geometry.
- New content outside old regime: bridge structure appears in open-model hidden states after removing the dominant common activation direction.
- Retractions or supersessions: raw activation cosine should not be used as evidence without centering or another anisotropy correction.

Next move: run layer sweeps and a second open model, then test whether selected bridge directions can steer generation or classification behavior.

## Source Assimilation: Muon Curvature Paper

Question: should `Why Muon Outperforms Adam: A Curvature Perspective` change the research program or merely join the source list?

Current regime:

- Artifact types: source manifest entries, local-only source PDFs, synthesis notes, experiment TODOs, audit cards.
- Operations: source triage, relevance assessment, public-safe manifest update, local archive update.
- Gates/verifiers: source should add an actionable metric/control or clarify an existing experiment risk; it should not blur optimizer curvature with representation geometry.
- Known limitations: this paper studies optimizer update directions and Hessian curvature, not concept or agency representations directly.

Action class:

- Retrieval/search/discovery: retrieval plus methods calibration.
- Why: the source is added to the bibliography and used to refine future activation-geometry controls, but it does not create a new experiment regime by itself.

Gate:

- Acceptance rule: use the paper only if it sharpens controls for activation geometry: anisotropy checks, centered-vs-raw comparisons, layerwise decomposition, and possible directional-curvature proxies.
- Withheld/rejected rule: do not pivot into optimizer benchmarking; do not claim NDS of optimizer updates is equivalent to concept geometry.

Results:

- Accepted artifacts: `references/SOURCES.md` entry; synthesis note under "Later Added Method Source"; TODO item for anisotropy and directional-curvature proxy checks.
- Rejected or withheld artifacts: local PDF `references/papers/arxiv_2606_04662_muon_curvature.pdf` remains ignored and untracked.
- Key insight: direction geometry needs curvature/anisotropy controls before it can support mechanistic claims.
- Variance or ablation: none; this is source triage, not an experiment.

Residual content:

- Explained by old regime: it extends the recurring "geometry as constraint" frame into optimizer update directions.
- New content outside old regime: it adds NDS as a candidate method-level control for future activation and training experiments.
- Retractions or supersessions: none.

Next move: keep the current activation layer sweep plan, but report anisotropy and consider cheap directional-curvature proxies before any strong mechanistic claim.

## Phase / Arc 2A: Concerned Syntax Design Pilot

Question: can a selector use costly interventions to reveal causal constituency only when the hidden parse matters for viability?

Current regime:

- Artifact types: minimal-agent viability dynamics, probe policies, attribution heads, activation geometry probes, source manifests, paper drafts, preregistrations.
- Operations: symbolic task generation, intervention-choice scoring, anti-cheat selectors, local deterministic pilot, Modal-ready sweep.
- Gates/verifiers: parse congruity, action accuracy, high-concern probe rate, low-concern no-restless-inquiry, subtree accuracy, unittest coverage.
- Known limitations: symbolic parse candidates are evaluator-known; no learned neural perception yet; intervention language is provided.

Action class:

- Retrieval/search/discovery: discovery-leaning benchmark transition.
- Why: adds a new accepted artifact type, causal constituency under concern, that Arc 1 could not represent.

Experiment:

- Manifest/report paths: `experiments/concerned_syntax/results/pilot_2026_06_16.md`; raw JSON withheld under `artifacts/concerned_syntax/pilot.json`.
- Positive targets: `concerned_syntax` selector.
- Negative controls: `null_policy`, `flat_valence`, `compression_proxy`, `uncertainty_only`.
- Stress tests: low-concern ambiguity that should not trigger probing.

Gate:

- Acceptance rule: concerned syntax passes high-concern parse >= 0.75, action >= 0.85, high-concern probe >= 0.70, low-concern probe <= 0.25, subtree >= 0.75.
- Withheld/rejected rule: raw artifacts stay under ignored `artifacts/`; selectors that pass action but fail parse/probe gates remain rejected controls.

Results:

- Accepted artifacts: `experiments/concerned_syntax/results/pilot_2026_06_16.md`; `papers/concerned_syntax/preregistration.md`; `papers/concerned_syntax/paper.md`.
- Rejected or withheld artifacts: `artifacts/concerned_syntax/pilot.json`.
- Key metrics: `concerned_syntax` parse-high 1.000, action 1.000, high-probe 1.000, low-probe 0.000, mean regret 0.001. `uncertainty_only` recovers parse but probes low-concern ambiguity at 1.000 and fails.
- Variance or ablation: deterministic 200-trial design pilot with five selectors.

Residual content:

- Explained by old regime: action accuracy alone can still be achieved by flat or compression-biased policies on many trials.
- New content outside old regime: causal constituency and no-restless-inquiry dissociate syntax under concern from reward, compression, and uncertainty reduction.
- Retractions or supersessions: Phase 2 should not be framed as merely "more probe policy"; it needs parse/intervention constituency gates.

Next move: see the Modal multi-seed sweep below, then replace symbolic selectors with learned agents.

## Phase / Arc 2A: Concerned Syntax Modal Sweep

Question: does the concerned-syntax benchmark retain its anti-cheat separation across remote multi-seed runs?

Current regime:

- Artifact types: Concerned Shape Grammar trials, selector summaries, Modal raw payloads, public markdown reports, paper drafts.
- Operations: Modal-backed parallel seed sweep, seed-level selector summaries, public report generation.
- Gates/verifiers: same Phase 2A parse/action/probe/subtree gate; Modal packaging must mount the `experiments` package; unittest coverage for report aggregation.
- Known limitations: still symbolic selectors; no learned neural perception or intervention-language induction.

Action class:

- Retrieval/search/discovery: search inside the accepted Arc 2A benchmark regime.
- Why: the sweep replicates the new artifact type across seeds but does not add a new verifier or learned mechanism.

Experiment:

- Manifest/report paths: `experiments/concerned_syntax/results/modal_sweep_2026_06_16.md`; raw JSON withheld under `artifacts/concerned_syntax/modal_sweep.json`.
- Positive targets: `concerned_syntax`.
- Negative controls: `null_policy`, `flat_valence`, `compression_proxy`, `uncertainty_only`.
- Stress tests: low-concern ambiguity and seed variation.

Gate:

- Acceptance rule: concerned syntax passes every seed while controls fail for parse, intervention, or restless-inquiry reasons.
- Withheld/rejected rule: raw Modal payload remains ignored; controls remain rejected even when action or parse accuracy is high.

Results:

- Accepted artifacts: `experiments/concerned_syntax/results/modal_sweep_2026_06_16.md`; Modal report generator; updated `papers/concerned_syntax/paper.md`.
- Rejected or withheld artifacts: `artifacts/concerned_syntax/modal_sweep.json`.
- Key metrics: `concerned_syntax` parse-high 1.000, action 1.000, subtree 0.808, high-probe 1.000, low-probe 0.000, gate pass rate 1.000. `uncertainty_only` has parse/action 1.000 but low-probe 1.000, so it remains rejected.
- Variance or ablation: 5 seeds x 1,000 trials = 5,000 shape trials.

Residual content:

- Explained by old regime: the design pilot pattern transported cleanly across seeds.
- New content outside old regime: none beyond replication; this is consolidation, not a new regime transition.
- Retractions or supersessions: "Modal plan" is superseded by an accepted multi-seed result.

Next move: train learned agents on the same gate without direct parse access.

## Phase / Arc 2A: Learned Concerned-Syntax Agents

Question: can learned agents infer causal constituency from intervention observations without direct hidden-parse access?

Current regime:

- Artifact types: vectorized Concerned Shape Grammar examples, learned linear policy/parser/action heads, executable body variants, Modal raw payloads, public reports.
- Operations: train/test split generation with hidden true parse withheld at test time, SGD binary learners, Modal multi-seed sweep, anti-cheat report generation.
- Gates/verifiers: same parse/action/probe/subtree gate; shortcut reward, planner-without-tree, and restless-tree controls; unit tests for learned gate separation.
- Known limitations: vectorized symbolic features and candidate parse hypotheses are provided; no pixel perception or learned motor primitive language yet.

Action class:

- Retrieval/search/discovery: discovery-leaning mechanism transition.
- Why: moves Arc 2A from hand-coded selector behavior to learned policy/parser components while preserving anti-cheat controls.

Experiment:

- Manifest/report paths: `experiments/concerned_syntax/results/learned_agents_modal_2026_06_16.md`; raw JSON withheld under `artifacts/concerned_syntax/learned_agents_modal_sweep.json`.
- Positive targets: `learned_concerned_syntax`.
- Negative controls: `shortcut_reward`, `planner_no_tree`, `restless_tree`.
- Stress tests: hidden true parse at test time, no-tree features, low-concern restless probing, capped calibration guard.

Gate:

- Acceptance rule: learned concerned syntax passes every seed with high-concern parse >= 0.75, action >= 0.85, high-concern probe >= 0.70, low-concern probe <= 0.25, and subtree >= 0.75.
- Withheld/rejected rule: raw Modal payload remains ignored; controls remain rejected when they pass action, parse, or probing alone.

Results:

- Accepted artifacts: `experiments/concerned_syntax/learned_agents.py`; `experiments/concerned_syntax/modal_learned_agents_sweep.py`; `experiments/concerned_syntax/results/learned_agents_modal_2026_06_16.md`.
- Rejected or withheld artifacts: `artifacts/concerned_syntax/learned_agents_modal_sweep.json`; pre-calibration run where guarded syntax reached parse/action 1.000 but aggregate subtree 0.7465 and gate pass rate 0.600.
- Key metrics: `learned_concerned_syntax` parse-high 1.000, action 1.000, subtree 0.797, high-probe 1.000, low-probe 0.202, gate pass rate 1.000. `restless_tree` parse/action 1.000 but low-probe 1.000 and fails. `planner_no_tree` probes correctly but parse-high 0.492 and fails.
- Variance or ablation: 5 seeds x 3,000 train trials x 1,200 test trials, 90 SGD epochs per seed.

Residual content:

- Explained by old regime: symbolic concerned syntax already showed the target anti-cheat pattern.
- New content outside old regime: a learned tree-binding parser plus concern-gated intervention policy can pass without hidden parse access; a small formal calibration budget is needed to keep subtree maintenance robust without restless inquiry.
- Retractions or supersessions: the "zero low-concern probes is always best" story is too brittle for learned syntax maintenance; the accepted gate is capped calibration, not absolute silence.

Next move: replace vectorized symbolic candidate parses with generated shapes or pixels where parse hypotheses must be inferred.

## Phase / Arc 2B: Viable Computational Bodies Design Pilot

Question: does viability-guided architecture evolution find syntax-bearing computational bodies more reliably than reward-only or novelty-only selection?

Current regime:

- Artifact types: architecture motif sets, static admissibility violations, resource costs, search histories, viability gates, pilot reports.
- Operations: typed motif mutation, dependency repair, motif promotion, strategy ranking, quality/archive descriptors.
- Gates/verifiers: formal validity, resource viability, parse congruity, subtree facilitation, intervention invention, self/world split, anti-cheat, formal-guard presence, unittest coverage.
- Known limitations: symbolic motif grammar only; no executable neural modules or external solver integration yet.

Action class:

- Retrieval/search/discovery: discovery-leaning benchmark transition.
- Why: makes computational body grammar itself an accepted search artifact, rather than treating architecture as fixed background.

Experiment:

- Manifest/report paths: `experiments/viable_computational_bodies/results/pilot_2026_06_16.md`; raw JSON withheld under `artifacts/viable_computational_bodies/pilot.json`.
- Positive targets: `viability_guided` search.
- Negative controls: `accuracy_only`, `novelty_only`.
- Stress tests: shortcut reward head and missing formal guard.

Gate:

- Acceptance rule: strategy passes if final viable rate >= 0.75 and mean concerned-syntax score >= 0.80.
- Withheld/rejected rule: raw artifacts stay under ignored `artifacts/`; high-train-return bodies without formal/anti-cheat gates remain rejected.

Results:

- Accepted artifacts: `experiments/viable_computational_bodies/results/pilot_2026_06_16.md`; `papers/viable_computational_bodies/preregistration.md`; `papers/viable_computational_bodies/paper.md`.
- Rejected or withheld artifacts: `artifacts/viable_computational_bodies/pilot.json`.
- Key metrics: `accuracy_only` viable 0.000, train 1.000; `novelty_only` viable 0.000, syntax 0.836; `viability_guided` viable 1.000, syntax 0.830.
- Variance or ablation: 12-seed, 18-generation, 18-population design pilot.

Residual content:

- Explained by old regime: reward-only search can optimize train return while failing the intended representation.
- New content outside old regime: viability-guided body evolution separates train return, novelty, formal validity, and syntax-bearing morphology.
- Retractions or supersessions: Phase 2B should not be presented as generic NAS; its novelty is the formal/viability/concerned-syntax acceptance surface.

Next move: see the Modal multi-seed sweep below, then replace symbolic motifs with executable neural modules.

## Phase / Arc 2B: Viable Computational Bodies Modal Sweep

Question: does viability-guided body evolution retain its advantage over reward-only and novelty-only search across remote multi-seed runs?

Current regime:

- Artifact types: architecture motif sets, final strategy/seed evaluations, Modal raw payloads, public markdown reports, paper drafts.
- Operations: Modal-backed strategy x seed sweep, final-cell aggregation, public report generation.
- Gates/verifiers: formal validity, resource viability, parse congruity, subtree facilitation, intervention invention, self/world split, anti-cheat, unittest coverage for report aggregation.
- Known limitations: symbolic motifs and hand-designed scores; no external solver or executable neural modules yet.

Action class:

- Retrieval/search/discovery: search inside the accepted Arc 2B body-grammar regime.
- Why: the sweep replicates the body-evolution acceptance surface across seeds but does not yet add executable architectures.

Experiment:

- Manifest/report paths: `experiments/viable_computational_bodies/results/modal_sweep_2026_06_16.md`; raw JSON withheld under `artifacts/viable_computational_bodies/modal_sweep.json`.
- Positive targets: `viability_guided`.
- Negative controls: `accuracy_only`, `novelty_only`.
- Stress tests: shortcut reward heads, missing formal guard, strategy-level reliability across seeds.

Gate:

- Acceptance rule: strategy passes if final viable rate >= 0.75, mean concerned-syntax score >= 0.80, and mean formal validity is 1.000.
- Withheld/rejected rule: raw Modal payload remains ignored; reward-only and novelty-only strategies remain controls unless they clear the full strategy gate.

Results:

- Accepted artifacts: `experiments/viable_computational_bodies/results/modal_sweep_2026_06_16.md`; Modal report generator; updated `papers/viable_computational_bodies/paper.md`.
- Rejected or withheld artifacts: `artifacts/viable_computational_bodies/modal_sweep.json`.
- Key metrics: `accuracy_only` viable 0.000, train 1.000, anti-cheat 0.400; `novelty_only` viable 0.167, syntax 0.835; `viability_guided` viable 1.000, syntax 0.830, formal 1.000, anti-cheat 0.950.
- Variance or ablation: 3 strategies x 6 seeds, with 32 generations and population 32.

Residual content:

- Explained by old regime: viability-guided selection was already positive in the design pilot.
- New content outside old regime: novelty-only is now recorded as partially but unreliably viable; that clarifies why novelty alone is not enough.
- Retractions or supersessions: "Modal plan" is superseded by an accepted multi-seed result.

Next move: instantiate the accepted motif grammar as executable modules and route them through Arc 2A tasks.

## Phase / Arc 2B: Executable Body Validation

Question: do executable body variants validate the symbolic Phase 2B motif grammar on the learned Arc 2A gate?

Current regime:

- Artifact types: learned policy/parser/action heads, executable body variants, formal/anti-cheat annotations, public reports.
- Operations: map symbolic body motifs onto executable controls, evaluate each body on the learned concerned-syntax sweep, aggregate across Modal seeds.
- Gates/verifiers: learned Arc 2A gate plus body-side formal validity and anti-cheat thresholds.
- Known limitations: executable bodies are linear components over vectorized symbolic features; no full NAS, neural module search, or external solver yet.

Action class:

- Retrieval/search/discovery: discovery-leaning validation transition.
- Why: gives the symbolic body grammar its first behavioral grounding by testing motif commitments as executable mechanisms.

Experiment:

- Manifest/report paths: `experiments/viable_computational_bodies/results/executable_bodies_modal_2026_06_16.md`; raw JSON withheld under `artifacts/concerned_syntax/learned_agents_modal_sweep.json`.
- Positive targets: `guarded_syntax_body`.
- Negative controls: `shortcut_reward_body`, `planner_without_tree_body`, `restless_tree_body`.
- Stress tests: reward shortcut, missing tree binder, missing formal concern guard.

Gate:

- Acceptance rule: body passes only if it clears the learned Arc 2A gate, formal validity is 1.000, and anti-cheat >= 0.70.
- Withheld/rejected rule: bodies that pass action or parse alone remain rejected controls.

Results:

- Accepted artifacts: `experiments/viable_computational_bodies/results/executable_bodies_modal_2026_06_16.md`; updated Phase 2B paper.
- Rejected or withheld artifacts: raw learned-agent Modal payload under ignored `artifacts/`.
- Key metrics: `guarded_syntax_body` parse-high 1.000, action 1.000, high-probe 1.000, low-probe 0.202, formal 1.000, anti-cheat 0.950, body gate pass rate 1.000. `restless_tree_body` parse/action 1.000 but low-probe 1.000 and fails. `shortcut_reward_body` action 0.880 but parse-high 0.494 and fails.
- Variance or ablation: same 5-seed Modal learned-agent sweep.

Residual content:

- Explained by old regime: symbolic body grammar predicted the guarded syntax body would be favored.
- New content outside old regime: tree binding and formal concern gating are behaviorally necessary in executable variants; neither planning alone nor tree parsing alone is sufficient.
- Retractions or supersessions: "replace symbolic motifs with executable modules" is started but not complete; current modules are linear/vectorized proof-of-mechanism components.

Next move: evolve or search over differentiable modules rather than hand-instantiating four body variants.

## Phase / Arc 2A: Vector-Observation Concerned Syntax

Question: can learned agents pass concerned-syntax gates from generated vector surfaces without visible candidate parse features?

Current regime:

- Artifact types: parse-invariant vector shape surfaces, learned surface/action/binding/policy heads, Modal raw payloads, public reports.
- Operations: generate six-part coordinate surfaces from roles and pair salience, withhold hidden parse identity, train/test SGD heads, evaluate concern-gated pair probing.
- Gates/verifiers: hidden true parse withheld, vector surface invariant under true/alternate parse swap, surface shortcut and passive-vector controls, restless-vector low-concern control.
- Known limitations: vector features are hand-designed; pair-probe intervention is provided; no pixel perception or invented motor primitive language yet.

Action class:

- Retrieval/search/discovery: discovery-leaning observation transition.
- Why: removes candidate-parse descriptors from the learned gate and makes intervention necessary for causal binding.

Experiment:

- Manifest/report paths: `experiments/concerned_syntax/results/vector_shapes_modal_2026_06_16.md`; raw JSON withheld under `artifacts/concerned_syntax/vector_shapes_modal_sweep.json`.
- Positive targets: `concerned_vector_probe`.
- Negative controls: `surface_shortcut`, `passive_vector`, `restless_vector_probe`.
- Stress tests: parse-invariant surface, no-probe passive inference, low-concern restless probing.

Gate:

- Acceptance rule: concerned vector agent passes every seed with high-concern parse >= 0.75, action >= 0.85, high-concern probe >= 0.70, low-concern probe <= 0.25, and subtree >= 0.75.
- Withheld/rejected rule: raw Modal payload remains ignored; controls remain rejected when they pass action, parse, or probing alone.

Results:

- Accepted artifacts: `experiments/concerned_syntax/vector_shapes.py`; `experiments/concerned_syntax/modal_vector_shapes_sweep.py`; `experiments/concerned_syntax/results/vector_shapes_modal_2026_06_16.md`.
- Rejected or withheld artifacts: `artifacts/concerned_syntax/vector_shapes_modal_sweep.json`; small Modal smoke where the mean metrics passed but a seed-level gate failed under 300 train / 140 test trials.
- Key metrics: `concerned_vector_probe` parse-high 1.000, action 1.000, subtree 0.804, high-probe 1.000, low-probe 0.189, gate pass rate 1.000. `restless_vector_probe` parse/action 1.000 but low-probe 1.000 and fails. `passive_vector` action 0.873 but parse-high 0.492 and fails.
- Variance or ablation: 5 seeds x 3,000 train trials x 1,200 test trials, 90 SGD epochs per seed.

Residual content:

- Explained by old regime: learned candidate-parse agents already showed that binding and concern gating can pass together.
- New content outside old regime: the visible vector surface no longer exposes candidate parse trees; the accepted agent must use an intervention to recover the hidden binding bit.
- Retractions or supersessions: candidate-parse features are no longer required for the learned Phase 2A gate, but pixel-level perception remains open.

Next move: replace generated vectors with rendered pixels and require object/part extraction before probing.

## Phase / Arc 2B: Vector Module Bodies and Haskell Typed Ontology

Question: do executable module bodies and a typed ontology gate preserve the Phase 2B distinction under the stronger vector Arc 2A gate?

Current regime:

- Artifact types: vector-observation body summaries, Haskell ADT ontology, Cabal test logs, JSON formal verdicts, public reports.
- Operations: map vector agents onto module bodies, evaluate learned Arc 2A gates, compile Haskell body ontology, test dependency/resource/calibration rules.
- Gates/verifiers: vector Arc 2A gate plus body formal validity, anti-cheat, module coverage; Haskell `cabal test all`.
- Known limitations: module bodies are still hand-instantiated; Haskell verdicts are not yet consumed by Python sweeps; no ASP/s(CASP), Z3, or proof assistant integration.

Action class:

- Retrieval/search/discovery: discovery-leaning formal-methods transition.
- Why: adds a typed external checker that forced ontology clarifications and validates the body admissibility layer outside Python.

Experiment:

- Manifest/report paths: `experiments/viable_computational_bodies/results/vector_module_bodies_modal_2026_06_16.md`; Haskell package under `formal/ontology-hs`.
- Positive targets: `modular_concerned_body`, `guarded_syntax_body`.
- Negative controls: `surface_reward_body`, `passive_vector_body`, `restless_vector_body`, `restless_tree_body`.
- Stress tests: surface reward shortcut, passive vector binding without active concern, restless vector binding without calibration, Haskell resource/dependency checks.

Gate:

- Acceptance rule: body passes only if it clears the vector Arc 2A gate, formal validity is 1.000, anti-cheat >= 0.70, and module coverage >= 0.80.
- Haskell acceptance rule: `cabal test all` passes and `ontology-check` emits valid verdicts for guarded syntax and modular concerned bodies while rejecting restless bodies.

Results:

- Accepted artifacts: `experiments/viable_computational_bodies/results/vector_module_bodies_modal_2026_06_16.md`; `formal/ontology-hs`.
- Rejected or withheld artifacts: raw vector Modal payload under ignored `artifacts/`; Cabal build outputs under ignored `dist-newstyle/`.
- Key metrics: `modular_concerned_body` parse-high 1.000, action 1.000, high-probe 1.000, low-probe 0.189, formal 1.000, anti-cheat 0.950, module coverage 0.950, gate pass rate 1.000.
- Formal catches: initial Haskell rules over-costed concern/calibration guards, then rejected vector causal binding because only `tree_binder` counted as a role-head binder; both were corrected explicitly.

Residual content:

- Explained by old regime: body-side controls still fail for shortcut, passive, or restless reasons.
- New content outside old regime: the typed ontology can catch inconsistencies in the body grammar before the empirical sweep, and vector causal binding is now explicitly admitted as a binder role parallel to symbolic tree binding.
- Retractions or supersessions: "formal guard" is no longer only Python logic; it now has a Haskell prototype, but Python does not yet call it during sweeps.

Next move: make Python consume Haskell JSON verdicts during body evaluation, then evolve/search over module bodies instead of hand-instantiating them.

## Activation Geometry Probe: Pythia-70M Layer Sweep

Question: does activation-space bridge geometry survive a layer sweep?

Current regime:

- Artifact types: paraphrased concept prompts, pooled hidden-state vectors, layer-indexed raw and centered geometry summaries, bridge-lift reports, audit cards.
- Operations: Modal-backed open-model extraction, multi-layer hidden-state pooling, global mean-centering, cosine-kernel summary, bridge-lift comparison.
- Gates/verifiers: layerwise centered category separation, bridge lift, bridge-pair rate, raw anisotropy inspection, publication guard.
- Known limitations: one small model, one pooling rule, hand-authored bridge pairs, no causal intervention.

Action class:

- Retrieval/search/discovery: search.
- Why: the run extends the activation-space artifact across layers inside the current schema; it does not yet add a new verifier or causal operation.

Gate:

- Acceptance rule: at least two transformer block-output layers must have centered category separation at least `0.05`, centered bridge lift at least `0.05`, and bridge-pair above-baseline rate at least `0.75`.
- Withheld/rejected rule: raw activation JSON stays untracked under `artifacts/`; layers that fail the gate remain in the public report.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/modal_pythia_70m_layer_sweep_2026_06_08.md`; `experiments/activation_geometry/modal_layer_sweep.py`; layer-sweep payload helpers in `activation_geometry_probe.py`.
- Rejected or withheld artifacts: local-only `artifacts/activation_geometry/modal_pythia_70m_layer_sweep.json`.
- Key metrics: layer `2` centered bridge lift `0.2248`; layer `2` centered category separation `0.1857`; layer `2` centered bridge-pair rate `0.9167`. Layers `1`, `2`, `5`, and `6` clear the block-output gate.
- Variance or ablation: layer `3` and layer `4` fail the gate; layer `6` reproduces the previous final-layer result.

Residual content:

- Explained by old regime: language-level semantic similarity and embedding geometry may explain layer `0`.
- New content outside old regime: centered bridge geometry survives multiple transformer block outputs but weakens sharply in the middle layers.
- Retractions or supersessions: the final-layer result should be treated as one point in a layer-dependent profile, not as the canonical activation geometry of the model.

Next move: replicate the layer sweep on a second open model, then convert the strongest layer-2 bridge pairs into steering or classification interventions.

## Activation Geometry Probe: GPT-2 Layer Sweep

Question: does activation-space bridge geometry replicate in a second open model?

Current regime:

- Artifact types: paraphrased concept prompts, pooled hidden-state vectors, model-indexed and layer-indexed raw and centered geometry summaries, bridge-lift reports, audit cards.
- Operations: Modal-backed open-model extraction, multi-layer hidden-state pooling, global mean-centering, cosine-kernel summary, bridge-lift comparison.
- Gates/verifiers: model replication, layerwise centered category separation, bridge lift, bridge-pair rate, raw anisotropy inspection, publication guard.
- Known limitations: same prompt set, same mean-pooling rule, hand-authored bridge pairs, no causal intervention.

Action class:

- Retrieval/search/discovery: search.
- Why: the run tests transport across a second model inside the current activation-geometry artifact schema.

Gate:

- Acceptance rule: at least two transformer block-output layers must have centered category separation at least `0.05`, centered bridge lift at least `0.05`, and bridge-pair above-baseline rate at least `0.75`.
- Withheld/rejected rule: raw activation JSON stays untracked under `artifacts/`; layers that fail the gate remain in the public report.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/modal_gpt2_layer_sweep_2026_06_08.md`.
- Rejected or withheld artifacts: local-only `artifacts/activation_geometry/modal_gpt2_layer_sweep.json`.
- Key metrics: layer `1` centered bridge lift `0.2348`; layer `1` centered category separation `0.1767`; layer `1` centered bridge-pair rate `1.0000`. Layers `1`, `2`, and `11` clear the block-output gate.
- Variance or ablation: middle layers `3..10` fail the bridge-rate criterion except layer `11`; final layer `12` fails the bridge-rate criterion.

Residual content:

- Explained by old regime: early layers may still reflect lexical and phrase-level semantic geometry rather than active attractor dynamics.
- New content outside old regime: centered bridge geometry replicates across a second open model, but the exact layer profile is not invariant.
- Retractions or supersessions: the Pythia final-layer pass should not be generalized to final layers across models.

Next move: run a pooling ablation, comparing mean pooling against final-token pooling for Pythia and GPT-2 before steering or causal claims.

## Activation Geometry Probe: Pooling Ablation

Question: does centered activation bridge geometry survive a pooling ablation?

Current regime:

- Artifact types: paraphrased concept prompts, pooled hidden-state vectors, model-indexed and layer-indexed raw and centered geometry summaries, pooling-indexed bridge-lift reports, audit cards.
- Operations: Modal-backed open-model extraction, mean pooling, final-token pooling, global mean-centering, cosine-kernel summary, bridge-lift comparison.
- Gates/verifiers: pooling perturbation, model replication, layerwise centered category separation, bridge lift, bridge-pair rate, raw anisotropy inspection, publication guard.
- Known limitations: same prompt set, hand-authored bridge pairs, no causal intervention, no bridge-pair-level stability analysis yet.

Action class:

- Retrieval/search/discovery: verifier upgrade.
- Why: the run adds pooling as an explicit verifier dimension and revises the accepted activation-geometry claim.

Gate:

- Acceptance rule: each model must have at least two transformer block-output layers with centered category separation at least `0.05`, centered bridge lift at least `0.05`, and bridge-pair above-baseline rate at least `0.75`.
- Withheld/rejected rule: raw activation JSON stays untracked under `artifacts/`; failed layers remain in the public report.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/pooling_ablation_pythia_gpt2_2026_06_08.md`; pooling-aware manifest and runner updates.
- Rejected or withheld artifacts: local-only final-token raw activation payloads under `artifacts/activation_geometry/`.
- Key metrics: Pythia final-token layer `5` bridge lift `0.1811`; GPT-2 final-token layer `12` bridge lift `0.3619`.
- Variance or ablation: mean pooling emphasizes early block outputs; final-token pooling emphasizes later block outputs.

Residual content:

- Explained by old regime: centered bridge geometry persists across models and pooling rules.
- New content outside old regime: layer profiles are pooling-dependent; "best layer" is not an intrinsic model property.
- Retractions or supersessions: previous early-layer claims should be stated as mean-pooling claims, not as pooling-independent activation geometry.

Next move: choose candidate intervention layers separately for mean-pooling-style classifiers and final-token-style generation/steering probes.

## Activation Geometry Probe: Intervention Layer Candidates

Question: which layers are eligible for the first classifier and steering interventions?

Current regime:

- Artifact types: concept prompts, activation-layer metrics, pooling-indexed layer profiles, bridge-pair candidates, intervention preregistration notes.
- Operations: layer eligibility filtering, primary/backup/control selection, bridge-pair triage, gate definition.
- Gates/verifiers: centered activation gate, pooling-specific readout rule, held-out paraphrase gate, control-layer gate, control-pair gate.
- Known limitations: pair-level stability has not yet been recomputed for every selected layer; no causal patching has been run.

Action class:

- Retrieval/search/discovery: gate-setting search.
- Why: the run constrains the next causal/search step before outcomes are known.

Gate:

- Acceptance rule: candidate layers must come from accepted model/pooling sweeps and satisfy the role-specific selection rule.
- Withheld/rejected rule: embedding layer `0` and failed bridge-rate layers cannot be primary intervention targets.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/intervention_layer_candidates_2026_06_08.md`.
- Rejected or withheld artifacts: no raw activations added; raw payloads remain local-only.
- Key metrics: mean-pooling primaries Pythia `2` and GPT-2 `1`; final-token primaries Pythia `5` and GPT-2 `12`.
- Variance or ablation: backup/control layers are preregistered for each model/readout.

Residual content:

- Explained by old regime: layer scores can select candidates.
- New content outside old regime: intervention targets are now readout-specific, not global layer claims.
- Retractions or supersessions: do not use a single "best layer" across classifier and generation settings.

Next move: implement the held-out paraphrase classifier/readout pilot before any generative steering claim.

## Activation Geometry Probe: Held-Out Readout Pilot

Question: do selected activation layers preserve bridge structure under held-out paraphrase readout?

Current regime:

- Artifact types: concept prompts, paraphrase-indexed activation payloads, train/holdout centroid readouts, bridge-pair pass tables, control-pair warnings.
- Operations: train-variant centering, nearest-centroid readout, held-out bridge cosine comparison, control-layer comparison.
- Gates/verifiers: held-out paraphrases, preselected primary/backup/control layers, positive bridge-pair gate, valence control gate, publication guard.
- Known limitations: only one holdout variant per concept, hand-authored control pairs, no matched random-pair distribution yet, no causal intervention.

Action class:

- Retrieval/search/discovery: verifier upgrade.
- Why: the run tests whether the earlier activation geometry survives an unseen paraphrase split and exposes control leakage before steering.

Gate:

- Acceptance rule: pass all preregistered held-out readout gates.
- Withheld/rejected rule: raw activation/readout payloads stay local-only under `artifacts/`; mixed gates are reported rather than promoted to causal claims.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/heldout_readout_pilot_2026_06_08.md`; `experiments/activation_geometry/heldout_readout_pilot.py`.
- Rejected or withheld artifacts: local-only raw activation/readout payloads under `artifacts/activation_geometry/`.
- Key metrics: Pythia layer `2` concept accuracy `1.000`, bridge rate `0.833`, positive pairs `4/4`; GPT-2 layer `1` concept accuracy `1.000`, bridge rate `0.917`, positive pairs `4/4`.
- Variance or ablation: Pythia layer `6` has cleaner control pairs than layer `2`; GPT-2 layer `1` has strong positive pairs but leaky valence controls.

Residual content:

- Explained by old regime: concept identity readout can be strong even when some control pairs leak.
- New content outside old regime: held-out bridge structure survives for the four intended pairs, but specificity is not yet adequate for steering claims.
- Retractions or supersessions: do not proceed as if the valence controls failed; at least one valence control is now an adversarial positive control.

Next move: run the pair-level control-leakage diagnostic before the first final-token steering pilot.

## Activation Geometry Probe: Pair-Control Diagnostic

Question: which held-out bridge pairs survive pair-level matched and shuffled controls?

Current regime:

- Artifact types: concept prompts, selected activation payloads, held-out vectors, pair-control distributions, promotion tables.
- Operations: train-variant centering, held-out cosine scoring, exact category-pair matched controls, category-preserving label shuffles.
- Gates/verifiers: matched-control p95, shuffled-label p95, valence adversarial controls, primary/backup/control layers.
- Known limitations: same-category pools are small; this is readout-only and mean-pooling-only.

Action class:

- Retrieval/search/discovery: verifier upgrade.
- Why: the run adds a stronger accepted verifier that the earlier non-bridge baseline could not represent.

Gate:

- Acceptance rule: at least two positive pairs promote in both primary layers and no valence control promotes in either primary layer.
- Withheld/rejected rule: raw activation and diagnostic payloads stay local-only under `artifacts/`; model-specific or layer-control-positive pairs remain warnings rather than promoted causal claims.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/pair_control_diagnostic_2026_06_08.md`; `experiments/activation_geometry/pair_control_diagnostic.py`.
- Rejected or withheld artifacts: local-only payloads under `artifacts/activation_geometry/`.
- Key metrics: Pythia primary layer `2` promotes `3/4` positive pairs and `0/2` valence controls; GPT-2 primary layer `1` promotes `4/4` positive pairs and `0/2` valence controls.
- Variance or ablation: Pythia backup layer `6` promotes `4/4` positive pairs with clean valence controls; control layers are not inert.

Residual content:

- Explained by old regime: weak cross-category baselines can make valence controls look bridge-like.
- New content outside old regime: three bridge pairs survive matched and shuffled controls in both primary layers.
- Retractions or supersessions: `conceptual_space` -> `representation_manifold` is no longer a cross-model primary candidate under strict controls.

Next move: run the first final-token steering pilot using the cross-model promoted pairs, with `conceptual_space` -> `representation_manifold` retained as a backup/model-specific probe.

## Activation Geometry Probe: Final-Token Steering Pilot

Question: do promoted final-token bridge directions causally shift target next-token choice margins?

Current regime:

- Artifact types: selected final-token layers, held-out concept prompts, source-target activation directions, signed intervention payloads, next-token option-margin probes.
- Operations: final-token activation extraction, raw target-minus-source direction construction, transformer-block forward hooks, signed log-probability margin scoring.
- Gates/verifiers: primary/backup/control layers, valence controls, signed reverse intervention, scale ablation.
- Known limitations: fixed option order, raw uncentered directions only, next-token multiple-choice probe rather than free-form generation, no random direction controls yet.

Action class:

- Retrieval/search/discovery: discovery attempt that failed gate.
- Why: this is the first operation that moves from readout geometry to a direct activation intervention, but it does not produce an accepted steering artifact.

Gate:

- Acceptance rule: at scale `1.0`, at least two positive pairs pass in primary and backup layers, no primary valence controls pass, and control layers do not show the same pattern.
- Withheld/rejected rule: raw steering payloads stay local-only under `artifacts/`; failed steering effects are reported as rejected rather than promoted.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/final_token_steering_pilot_2026_06_08.md`; `experiments/activation_geometry/modal_final_token_steering.py`; `experiments/activation_geometry/final_token_steering_pilot.py`.
- Rejected or withheld artifacts: local-only Modal steering payloads.
- Key metrics: Pythia primary layer `5` positive pass `0/3`, valence control pass `2/2`; GPT-2 primary layer `12` positive pass `1/3`, valence control pass `1/2`.
- Variance or ablation: effects are stable across scales `0.5` and `1.0`; Pythia promoted positive directions are consistently opposite-signed for the next-token probe.

Residual content:

- Explained by old regime: readout geometry can select plausible directions but does not guarantee causal control.
- New content outside old regime: raw bridge directions can be systematically wrong-signed or non-specific when hooked into final-token generation layers.
- Retractions or supersessions: do not claim the promoted readout pairs are steering directions without calibration.

Next move: implement a steering calibration diagnostic before any free-form generation run.

## Activation Geometry Probe: Steering Calibration Diagnostic

Question: can steering calibration turn promoted bridge readouts into reliable final-token interventions?

Current regime:

- Artifact types: selected final-token layers, held-out concept prompts, source-target activation directions, direction-mode calibration payloads, option-order randomized next-token margin probes.
- Operations: final-token activation extraction, direction sign/normalization variants, same-norm random direction controls, transformer-block forward hooks, option-order randomized log-probability margin scoring.
- Gates/verifiers: primary/backup/control layers, valence controls, random direction controls, option-order robust-pass rule, cross-model replication.
- Known limitations: one fixed intervention scale, centroid directions only, multiple-choice next-token probe rather than free-form generation, no learned direction objective.

Action class:

- Retrieval/search/discovery: verifier upgrade that rejects the current steering operation.
- Why: this run adds option-order and random-direction controls that the previous steering pilot could not represent, and it clarifies that the current intervention is underidentified.

Gate:

- Acceptance rule: a direction mode must pass at least two of three positive bridge pairs in primary and backup layers, pass no primary valence controls, avoid control-layer replication, and replicate across models.
- Withheld/rejected rule: raw Modal payloads remain local-only under `artifacts/`; partial primary-layer effects are recorded but not promoted.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/steering_calibration_diagnostic_2026_06_08.md`; `experiments/activation_geometry/modal_steering_calibration.py`; `experiments/activation_geometry/steering_calibration_diagnostic.py`.
- Rejected or withheld artifacts: local-only Modal calibration payloads under `artifacts/activation_geometry/`.
- Key metrics: Pythia primary positive pass count never exceeds `1/3`; GPT-2 `raw_target_minus_source` reaches `2/3` primary positives with `0/2` valence controls but fails backup replication; GPT-2 `unit_target_minus_source` reaches `2/3` primary and backup positives but also `2/3` control-layer positives.
- Variance or ablation: direction sign, unit normalization, same-norm random directions, and three option orders tested.

Residual content:

- Explained by old regime: readout-selected bridge pairs can create plausible but non-specific next-token margin shifts.
- New content outside old regime: option-order and random-direction controls show that the current final-token additive intervention is too underidentified for causal claims.
- Retractions or supersessions: do not treat sign-flipped or unit-normalized centroid directions as accepted steering directions.

Next move: redesign the intervention verifier around learned/readout-conditioned directions or causal patching before any free-form generation run.

## Activation Geometry Probe: Steering Gradient-Alignment Diagnostic

Question: are bridge centroid directions aligned with the local output-margin gradient used by the final-token multiple-choice steering probe?

Current regime:

- Artifact types: selected final-token layers, held-out concept prompts, source-target centroid directions, prompt-local output-margin gradients, option-order randomized intervention payloads, centroid-gradient alignment summaries.
- Operations: final-token activation extraction, output-margin gradient capture via activation leaf hook, same-norm gradient and random controls, transformer-block forward hooks, option-order randomized log-probability margin scoring.
- Gates/verifiers: primary/backup/control layers, valence controls, random same-norm controls, option-order robust-pass rule, centroid-gradient cosine, cross-model replication.
- Known limitations: gradients are prompt-local and option-token-local; this is still a multiple-choice next-token probe, not free-form behavior.

Action class:

- Retrieval/search/discovery: verifier transition.
- Why: the run adds a new causal-alignment artifact, `centroid-gradient cosine`, and distinguishes representational readout axes from output-control axes.

Gate:

- Acceptance rule: a semantic steering direction would need primary and backup positive passes without primary valence-control passes or control-layer replication, plus materially positive centroid-gradient alignment.
- Withheld/rejected rule: raw Modal payloads remain local-only under `artifacts/`; gradient directions are treated as nonspecific controls unless they clear specificity gates.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/steering_gradient_alignment_2026_06_08.md`; `experiments/activation_geometry/modal_steering_gradient_alignment.py`; `experiments/activation_geometry/steering_gradient_alignment.py`.
- Rejected or withheld artifacts: local-only Modal gradient-alignment payloads under `artifacts/activation_geometry/`.
- Key metrics: primary positive centroid-gradient cosine is `0.004070` for Pythia-70M and `0.000151` for GPT-2; gradient directions pass `3/3` primary positives but also `2/2` primary valence controls and `3/3` control-layer positives in both models.
- Variance or ablation: centroid, gradient same-norm, gradient unit, random same-norm, and three option orders tested across both models.

Residual content:

- Explained by old regime: readout-selected centroid directions can be stable representational axes without being local causal output-control axes.
- New content outside old regime: bridge centroids are near-orthogonal to prompt-local target-margin gradients across two models, suggesting a separation between representation geometry and the next-token option-control interface.
- Retractions or supersessions: do not use the current multiple-choice gradient as semantic steering evidence; do not expect larger centroid scale alone to solve the causal mismatch.

Next move: test causal patching from target concept activations before searching for larger or more complex additive steering vectors.

## Activation Geometry Probe: Causal Patching Diagnostic

Question: does direct target-concept activation patching rescue final-token bridge interventions?

Current regime:

- Artifact types: selected final-token layers, held-out concept prompts, target/distractor/random/source patch activations, option-order randomized target-margin payloads, specificity summaries.
- Operations: final-token activation extraction, activation replacement hooks, option-order randomized log-probability margin scoring, target-vs-control patch comparison.
- Gates/verifiers: primary/backup/control layers, valence controls, distractor/random/source patch controls, robust positive option-order rule, target-over-best-control specificity rule.
- Known limitations: patch activations are extracted from concept-definition prompts, while the behavioral probe uses an option-choice prompt.

Action class:

- Retrieval/search/discovery: verifier upgrade that rejects the current behavioral interface.
- Why: the run adds full-state causal patching as a stricter intervention operation than additive centroid steering.

Gate:

- Acceptance rule: positive bridge pairs must show primary-layer target-specific passes that beat distractor, random, and source-concept patch controls without valence-control leakage or control-layer replication.
- Withheld/rejected rule: raw Modal payloads remain local-only under `artifacts/`; backup-only and control-layer-only target-specific rows are warnings.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/causal_patching_diagnostic_2026_06_08.md`; `experiments/activation_geometry/modal_causal_patching.py`; `experiments/activation_geometry/causal_patching_diagnostic.py`.
- Rejected or withheld artifacts: local-only Modal causal-patching payloads under `artifacts/activation_geometry/`.
- Key metrics: Pythia primary positive target-specific passes `0/3`; GPT-2 primary positive target-specific passes `0/3`.
- Variance or ablation: target, distractor, random, and source-concept patch controls tested across primary, backup, and control layers with three option orders.

Residual content:

- Explained by old regime: readout-selected bridge pairs need not become final-token answer-choice controls.
- New content outside old regime: full target activation patching fails the same primary-layer target-specific gate, suggesting the answer-choice surface or context mismatch is the likely failure source.
- Retractions or supersessions: do not treat direct concept activation patching as accepted causal bridge evidence for this probe.

Next move: run matched-context activation patching before abandoning the final-token multiple-choice interface.

## Activation Geometry Probe: Matched-Context Patching Diagnostic

Question: does matched-context activation patching rescue final-token bridge interventions?

Current regime:

- Artifact types: selected final-token layers, matched option-choice patch prompts, target/distractor/random/source hook-surface activations, option-order randomized target-margin payloads, specificity summaries.
- Operations: answer-choice prompt construction, hook-surface activation capture, activation replacement hooks, option-order randomized log-probability margin scoring, target-vs-control patch comparison.
- Gates/verifiers: exact `source_noop` sanity control, primary/backup/control layers, valence controls, distractor/random/source patch controls, robust option-order rule, target-over-best-control specificity rule.
- Known limitations: one context variant, one random-patch seed, two small causal LMs, and no free-form or downstream behavioral task.

Action class:

- Retrieval/search/discovery: regime refinement.
- Why: the run revises the intervention artifact from bare concept-state patching to matched answer-choice context-state patching, and the no-op sanity gate exposes the need to capture patch vectors at the hook surface.

Gate:

- Acceptance rule: promote only cross-model primary positive target-specific passes without primary valence-control leakage or control-layer replication.
- Withheld/rejected rule: model-specific pockets and leaky controls are reported but not promoted to semantic bridge-causality claims.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/matched_context_patching_2026_06_08.md`; `experiments/activation_geometry/modal_matched_context_patching.py`; `experiments/activation_geometry/matched_context_patching.py`.
- Rejected or withheld artifacts: cross-model semantic bridge claim is rejected; Pythia-specific matched-context pocket is withheld pending replication.
- Key metrics: Pythia primary positive target-specific passes `2/3` with `1/2` valence-control leakage; GPT-2 primary positive target-specific passes `0/3`; max absolute `source_noop` aggregate delta `0.0` in both models.
- Variance or ablation: target, distractor, random, and exact source-context patch controls tested across primary, backup, and control layers with three option orders.

Residual content:

- Explained by old regime: readout-selected bridge pairs do not automatically imply cross-model causal steering.
- New content outside old regime: context matching can turn previously rejected direct patching into a Pythia-specific causal pocket.
- Retractions or supersessions: do not say final-token patching is simply dead; do not promote the Pythia pocket until it survives replication and leakage controls.

Next move: replicate the Pythia matched-context pocket across variants, random seeds, and a nearby layer scan before trying free-form generation.

## Activation Geometry Probe: Pythia Matched-Context Replication

Question: does the Pythia matched-context patching pocket survive variants, random-control seeds, and nearby layers?

Current regime:

- Artifact types: matched-context patch payloads, hook-surface no-op controls, specificity rows, replication-grid summaries.
- Operations: context-variant sweep, random-control seed sweep, nearby-layer sweep, target-vs-control aggregation.
- Gates/verifiers: exact `source_noop` aggregate gate, target-over-best-control specificity gate, valence-control leakage check, variant/seed/layer stability check.
- Known limitations: Pythia-only, three layers, three context variants, three random-control seeds, no third-model replication yet.

Action class:

- Retrieval/search/discovery: search inside the matched-context patching regime.
- Why: the experiment perturbs variants, seeds, and layers without changing the artifact type or verifier.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/pythia_matched_context_replication_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_matched_context_repl_v*_s*_l456.json`.
- Positive targets: `attractor` -> `attractor_network`, `autopoiesis` -> `homeostasis`, `validity_gate` -> `weak_constraint`.
- Negative controls: `valence` -> `activation_vector`, `valence` -> `steering_vector`, distractor/random/source patch modes.
- Stress tests: context variants `0/1/2`, seeds `20260608/20260609/20260610`, layers `4/5/6`.

Gate:

- Acceptance rule: promote only effects that pass across variants and seeds at the target layer and do not look like valence-control leakage.
- Withheld/rejected rule: broad bridge mechanism is withheld if only one pair survives or controls show similar target-specific passes.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/pythia_matched_context_replication_2026_06_08.md`; `experiments/activation_geometry/matched_context_replication.py`.
- Rejected or withheld artifacts: broad Pythia matched-context bridge mechanism remains withheld.
- Key metrics: layer-5 `attractor` -> `attractor_network` specific passes `9/9`; layer-5 `autopoiesis` -> `homeostasis` specific passes `3/9`; layer-5 `validity_gate` -> `weak_constraint` specific passes `0/9`; layer-5 valence controls specific passes `9/18`.
- Variance or ablation: `attractor` survives all variants and seeds; other candidate pairs are variant-dependent or fail.

Residual content:

- Explained by old regime: context matching can make some final-token patches causal in Pythia.
- New content outside old regime: the stable residual is not a broad bridge class; it is a narrow attractor-network pocket at layer `5`.
- Retractions or supersessions: supersede the previous "Pythia matched-context pocket" phrasing with the narrower "Pythia layer-5 attractor-network pocket".

Next move: run a focused attractor-pocket diagnostic with distractor sweeps, adversarial near-neighbor controls, and third-model or second-checkpoint replication.

## Activation Geometry Probe: Focused Attractor-Pocket Diagnostic

Question: does the focused attractor-network pocket survive distractor sweeps, adversarial near-neighbor controls, and second-checkpoint replication?

Current regime:

- Artifact types: matched-context patch payloads, specificity rows, focused gate summaries, near-neighbor leakage rows.
- Operations: distractor/frame sweep, target near-control, source near-control, second-checkpoint replication.
- Gates/verifiers: exact `source_noop` gate, positive distractor-sweep gate, near-control leakage gate, checkpoint-stability gate.
- Known limitations: only two Pythia-70M checkpoints, one context variant, answer-choice prompt surface only.

Action class:

- Retrieval/search/discovery: search inside the matched-context patching regime.
- Why: this run changes prompts, distractors, controls, and checkpoint while preserving the same causal-patching artifact type and verifier family.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/attractor_pocket_diagnostic_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m*_attractor_pocket.json`.
- Positive targets: `attractor` -> `attractor_network` across two prompt frames and four distractors.
- Negative controls: `attractor` -> `prototype`, `attractor` -> `schema`, `prototype` -> `attractor_network`, `schema` -> `attractor_network`, plus distractor/random/source patch modes.
- Stress tests: prompt-frame sweep, distractor sweep, near-neighbor source/target swaps, second Pythia-family checkpoint.

Gate:

- Acceptance rule: promote the pocket only if all positive primary rows pass, near-neighbor controls clear, source no-op is exact, and the second checkpoint supports the effect.
- Withheld/rejected rule: reject a clean bridge claim if near-neighbor controls mimic the same target-specific pattern or if the effect weakens on the second checkpoint.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/attractor_pocket_diagnostic_2026_06_08.md`; `experiments/activation_geometry/attractor_pocket_diagnostic.py`; `experiments/activation_geometry/modal_attractor_pocket_diagnostic.py`.
- Rejected or withheld artifacts: clean `attractor` -> `attractor_network` bridge claim is rejected.
- Key metrics: deduped primary positives `6/8`; deduped primary near-controls `4/8`; non-deduped primary positives `4/8`; non-deduped primary near-controls `1/8`; max source-noop delta `0.0`.
- Variance or ablation: deduped has a stronger but leakier basin; non-deduped has a weaker basin and no positive mean advantage.

Residual content:

- Explained by old regime: matched-context final-token patching can bias answer-choice margins.
- New content outside old claim: the surviving pattern is broader than one semantic bridge and looks like an attractor-family answer-choice basin.
- Retractions or supersessions: supersede "Pythia layer-5 attractor-network pocket" with "Pythia-70M-deduped layer-5 attractor-family answer-choice basin."

Next move: implement the answer-surface basin diagnostic to distinguish semantic source/target effects from label/option-surface effects.

## Activation Geometry Probe: Answer-Surface Basin Diagnostic

Question: does the attractor-family basin follow semantic source/target content, visible labels, or the option-choice surface?

Current regime:

- Artifact types: answer-surface patch payloads, label-regime rows, patch-text-regime rows, specificity summaries.
- Operations: canonical/alias/symbol relabeling, neutral-carrier patch prompts, source-family sweep, layer comparison.
- Gates/verifiers: exact definition-source no-op gate, neutral-carrier failure gate, symbol-label failure gate, alias-preservation gate.
- Known limitations: one model checkpoint, one context variant, still uses an answer-choice interface.

Action class:

- Retrieval/search/discovery: discovery-leaning verifier revision.
- Why: this adds new accepted artifact dimensions, label regimes and patch-text regimes, that the previous matched-context verifier could not represent.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/answer_surface_basin_diagnostic_2026_06_08.md`; local ignored payload under `artifacts/activation_geometry/modal_pythia_70m_deduped_answer_surface_basin.json`.
- Positive targets: `attractor` -> `attractor_network`.
- Negative controls: neutral patch text, symbol labels, distractor/random/source patch modes.
- Stress tests: source-family sweep, canonical/alias/symbol labels, definition/neutral patch text, primary/control layer comparison.

Gate:

- Acceptance rule: call it semantically mediated only if aliases preserve the effect while neutral patch prompts and symbol labels break it.
- Withheld/rejected rule: reject label-free activation-space claims until a no-answer-choice readout test reproduces the basin.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/answer_surface_basin_diagnostic_2026_06_08.md`; `experiments/activation_geometry/answer_surface_basin_diagnostic.py`; `experiments/activation_geometry/modal_answer_surface_basin.py`.
- Rejected or withheld artifacts: pure label-only artifact claim is rejected; label-free activation-space basin claim is withheld.
- Key metrics: primary canonical definitions `3/5`; primary alias definitions `3/5`; primary canonical neutral `0/5`; primary alias neutral `0/5`; primary symbol definitions `0/5`; exact definition-source no-op max delta `0.0`.
- Variance or ablation: control layer `6` has weak canonical-definition passes, so the basin is not uniquely localized to layer `5`.

Residual content:

- Explained by old regime: the multiple-choice final-token surface can carry target-margin effects.
- New content outside old claim: the effect requires semantic definitions and meaningful labels, but spreads across nearby source concepts.
- Retractions or supersessions: supersede "answer-choice label artifact" with "semantically mediated answer-surface basin."

Next move: run a label-free readout basin diagnostic to test whether the basin exists in activation space without visible answer choices.

## Activation Geometry Probe: Label-Free Readout Basin Diagnostic

Question: does the semantically mediated attractor-family basin exist in activation space without visible answer choices?

Current regime:

- Artifact types: label-free patch payloads, centroid-readout rows, definition/neutral patch-text controls, specificity summaries.
- Operations: held-out centroid readout training, layer-5 activation patching, layer-6 downstream readout scoring.
- Gates/verifiers: exact definition-source no-op gate, target-over-control readout specificity gate, neutral-carrier failure gate, generic-transfer control check.
- Known limitations: one model checkpoint, one injection/readout layer pair, centroid readout rather than a trained linear classifier.

Action class:

- Retrieval/search/discovery: search inside the upgraded label-free readout regime.
- Why: this run tests the new no-answer-choice verifier but does not yet establish a new attractor-specific artifact class.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/label_free_readout_basin_2026_06_08.md`; local ignored payload under `artifacts/activation_geometry/modal_pythia_70m_deduped_label_free_readout_basin.json`.
- Positive targets: `attractor` -> `attractor_network`.
- Negative controls: neutral patch text, distractor/random/source patch modes.
- Stress tests: source-family sweep into `attractor_network`, generic valence/vector transfer controls.

Gate:

- Acceptance rule: accept label-free transfer if definition target patches pass specificity and neutral label-carrier patches fail.
- Withheld/rejected rule: withhold attractor-specific basin claims if generic transfer controls also pass.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/label_free_readout_basin_2026_06_08.md`; `experiments/activation_geometry/label_free_readout_basin.py`; `experiments/activation_geometry/modal_label_free_readout_basin.py`.
- Rejected or withheld artifacts: attractor-specific activation-space basin claim is withheld.
- Key metrics: definition positive `1/1`; definition source-family `4/4`; definition generic controls `2/2`; neutral rows `0/7`; definition source-noop max delta `0.0`.
- Variance or ablation: definition patches transfer strongly; neutral label-carrier patches do not pass specificity.

Residual content:

- Explained by old regime: answer-choice target-margin effects can be semantically mediated.
- New content outside old claim: the target-state transfer survives without visible answer choices, but it appears generic rather than attractor-specific.
- Retractions or supersessions: supersede "semantically mediated answer-surface basin" with "generic label-free definition-derived target-state transfer; attractor-family rows are currently a special case only by topic, not by mechanism."

Next move: build a broad label-free target-state transfer baseline across many concept pairs and compare the attractor-family rows against that null distribution.

## Activation Geometry Probe: Label-Free Transfer Baseline

Question: are the attractor-family label-free transfer rows exceptional against a broad null distribution?

Current regime:

- Artifact types: label-free patch payloads, centroid-readout rows, sampled baseline-pair rows, transfer-baseline summaries.
- Operations: held-out centroid readout training, layer-5 activation patching, layer-6 downstream readout scoring, sampled same-category and cross-category baseline construction.
- Gates/verifiers: exact definition-source no-op gate, target-over-control readout specificity gate, neutral-carrier stress test, baseline percentile comparison.
- Known limitations: one checkpoint, one injection/readout layer pair, one alpha, limited concept inventory.

Action class:

- Retrieval/search/discovery: search inside the label-free readout regime.
- Why: the run extends the null distribution without changing the intervention artifact type.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/label_free_transfer_baseline_2026_06_08.md`; local ignored payload under `artifacts/activation_geometry/modal_pythia_70m_deduped_label_free_transfer_baseline.json`.
- Positive targets: `attractor` -> `attractor_network`.
- Negative controls: neutral patch text, distractor/random/source patch modes.
- Stress tests: 56 sampled baseline pairs split across same-category and cross-category rows.

Gate:

- Acceptance rule: promote attractor exceptionality only if focus/source-family rows sit high in the baseline advantage distribution.
- Withheld/rejected rule: withhold attractor-specific claims if baseline rows pass at comparable or higher rates.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/label_free_transfer_baseline_2026_06_08.md`; `experiments/activation_geometry/label_free_readout_basin.py`; `experiments/activation_geometry/modal_label_free_readout_basin.py`.
- Rejected or withheld artifacts: attractor-specific activation basin claim is withheld.
- Key metrics: definition baseline passes `43/56`; definition positive `1/1`; definition source-family `4/4`; source-family mean advantage percentile `71.4%`; source-family max advantage percentile `85.7%`; neutral baseline passes `7/56`.
- Variance or ablation: definition content dominates neutral label-carrier transfer; cross-category definition baseline rows are stronger than same-category rows in this sample.

Residual content:

- Explained by old regime: the label-free attractor rows are examples of generic definition-derived target-state transfer.
- New content outside old regime: the broader mechanism itself is now the residual worth explaining.
- Retractions or supersessions: supersede "generic label-free target-state transfer, attractor-family special case uncertain" with "broad label-free target-state transfer; attractor-specific exceptionality rejected for now."

Next move: run a layer/alpha dose-response to determine whether generic transfer is a late-state overwrite artifact or a propagating intervention.

## Activation Geometry Probe: Label-Free Transfer Dose Response

Question: is broad label-free target-state transfer a late overwrite, or does it have a downstream layer/alpha regime?

Current regime:

- Artifact types: label-free patch payloads, centroid-readout rows, sampled baseline-pair rows, patch-alpha grid summaries.
- Operations: held-out centroid readout training, activation patching at selected injection layers, downstream layer-6 readout scoring, target-vs-control specificity aggregation.
- Gates/verifiers: strict downstream source-noop gate, target-over-control specificity gate, neutral-carrier stress test, alpha dose-response.
- Known limitations: one checkpoint, one readout layer, small baseline sample, unresolved same-layer hook/readout mismatch.

Action class:

- Retrieval/search/discovery: discovery-leaning verifier refinement.
- Why: the run adds alpha as a first-class grid dimension and exposes a missing artifact type for same-layer hook/readout-surface validity.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/label_free_transfer_dose_response_2026_06_08.md`; local ignored payload under `artifacts/activation_geometry/modal_pythia_70m_deduped_label_free_dose_response.json`.
- Positive targets: focus rows plus 8 sampled baseline pairs.
- Negative controls: neutral patch text, distractor/random/source patch modes.
- Stress tests: injection layers `2,3,4,5,6`; patch alphas `0.25,0.5,0.75,1.0`; strict downstream no-op filtering.

Gate:

- Acceptance rule: accept a downstream transfer ridge only if strict downstream source-noop is exact and definition patches show a layer/alpha increase that neutral carriers do not match.
- Withheld/rejected rule: withhold same-layer cells if source-noop is nonzero; reject a pure late-overwrite interpretation if earlier strict downstream layers show specific dose-responsive transfer.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/label_free_transfer_dose_response_2026_06_08.md`; `experiments/activation_geometry/label_free_readout_basin.py`; `experiments/activation_geometry/modal_label_free_readout_basin.py`.
- Rejected or withheld artifacts: same-layer `6 -> 6` interpretation is withheld.
- Key metrics: strict downstream definition source-noop max delta `0.0`; layer `4 -> 6` definition pass rate reaches `10/15`; layer `5 -> 6` definition pass rate reaches `11/15`; neutral carrier pass rates remain at or below `2/15` in all strict downstream cells.
- Variance or ablation: baseline-only rows show the same layer/alpha ridge with lower pass rates; source-family rows are stronger but no longer the sole phenomenon.

Residual content:

- Explained by old regime: broad target-state transfer is a generic definition-derived phenomenon, not attractor-specific.
- New content outside old regime: the transfer has a mid/late downstream ridge and an alpha dose-response.
- Retractions or supersessions: supersede "maybe a late overwrite" with "strict downstream transfer is strongest from layers 4-5 into layer 6; same-layer cells are invalid under current hook/readout instrumentation."

Next move: replicate the downstream ridge with more baseline rows and a second seed/checkpoint, while separately diagnosing same-layer hook/readout validity.

## Activation Geometry Probe: Same-Layer Hook-Surface Diagnostic

Question: did same-layer label-free patching fail because the intervention is non-identity, or because patch vectors were captured at the wrong surface?

Current regime:

- Artifact types: label-free patch payloads, patch-vector-surface summaries, source-noop sanity tables.
- Operations: hidden-state vector capture, hook-output vector capture, transformer-block final-token patching, downstream readout scoring.
- Gates/verifiers: source-noop max absolute delta by patch-vector surface and injection/readout pair.
- Known limitations: one model checkpoint, one patch alpha, focus pairs only.

Action class:

- Retrieval/search/discovery: verifier refinement.
- Why: the run adds patch-vector surface as a first-class verifier dimension and fixes an invalid same-layer measurement.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/same_layer_hook_surface_diagnostic_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_same_layer_*_surface.json`.
- Positive targets: focus rows from the label-free readout diagnostic.
- Negative controls: distractor/random/source-noop patch modes.
- Stress tests: compare `hidden_state` against `hook_output` for `5 -> 6` and `6 -> 6`.

Gate:

- Acceptance rule: same-layer cells become interpretable only if `source_noop` is exactly zero at the hook surface.
- Withheld/rejected rule: withhold any same-layer surface that fails source-noop identity.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/same_layer_hook_surface_diagnostic_2026_06_08.md`; `experiments/activation_geometry/modal_label_free_readout_basin.py`; `experiments/activation_geometry/label_free_readout_basin.py`.
- Rejected or withheld artifacts: hidden-state same-layer `6 -> 6` remains rejected as an invalid surface.
- Key metrics: hidden_state `6 -> 6` max source-noop delta `0.247`; hook_output `6 -> 6` max source-noop delta `0.0`; hook_output preserves `5 -> 6` source-noop max delta `0.0`.
- Variance or ablation: `5 -> 6` is identical across surfaces; final-layer same-layer behavior changes only when surface alignment matters.

Residual content:

- Explained by old regime: PR #24's strict downstream ridge remains valid.
- New content outside old regime: patch-vector surface must be explicit for same-layer/final-layer patching.
- Retractions or supersessions: supersede "same-layer cells invalid/unknown" with "same-layer cells are valid under hook-output patch vectors and invalid under post-final-LN hidden-state patch vectors."

Next move: rerun the broader dose-response with `hook_output` and a larger baseline sample.

## Activation Geometry Probe: Hook-Output Dose-Response Replication

Question: does the label-free transfer ridge survive hook-output surface correction, a broader baseline, and a second seed?

Current regime:

- Artifact types: label-free patch payloads, hook-output patch-vector manifests, sampled baseline-pair rows, source-noop identity tables, dose-response summaries.
- Operations: hook-output activation capture, held-out centroid readout training, final-token activation patching at transformer-block outputs, target-vs-control specificity aggregation.
- Gates/verifiers: exact source-noop identity, definition-vs-neutral stress, alpha dose-response, baseline percentile comparison, two-seed replication.
- Known limitations: one checkpoint, one readout layer, nearest-centroid readout, no behavior-level task yet.

Action class:

- Retrieval/search/discovery: consolidation search with verifier refinement.
- Why: the run keeps the existing label-free patch schema but tests the ridge under a corrected surface, larger null, and second seed; the accepted same-layer cell revises a previously withheld artifact class.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/hook_output_dose_response_replication_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_hook_output_dose_response_seed*.json`.
- Positive targets: focus rows plus 24 sampled baseline pairs per seed.
- Negative controls: neutral patch text, distractor/random/source-noop patch modes, broad baseline rows.
- Stress tests: injection layers `3,4,5,6`; alphas `0.5,0.75,1.0`; two seeds; same-layer hook-output identity.

Gate:

- Acceptance rule: accept the replicated ridge only if source-noop is exact, definition patches show a stable layer/alpha specificity ridge across seeds, and neutral carriers do not match it.
- Withheld/rejected rule: reject attractor-specific revival unless focus/source-family rows are clearly exceptional against baseline and generic controls.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/hook_output_dose_response_replication_2026_06_08.md`; `scripts/summarize_label_free_dose_response.py`.
- Rejected or withheld artifacts: no hook-output same-layer cells are withheld; attractor-specific revival is rejected.
- Key metrics: source-noop max delta `0.0` across 744 aggregates; combined definition pass rates reach `38/62` at `4 -> 6`, `46/62` at `5 -> 6`, and `54/62` at `6 -> 6`; neutral at `6 -> 6`, alpha `1.0` reaches only `13/62`.
- Variance or ablation: two seeds agree on the layer/alpha ridge; baseline-only rows show the same ridge, with `40/48` passes at `6 -> 6`, alpha `1.0`.

Residual content:

- Explained by old regime: broad definition-derived transfer remains generic rather than attractor-specific.
- New content outside old regime: same-layer `6 -> 6` is now a valid hook-output artifact and is the strongest point on the ridge.
- Retractions or supersessions: supersede "same-layer cells are invalid/unknown" with "same-layer cells are valid under hook-output patch vectors, but not attractor-specific."

Next move: use trained readouts and behavior-level gates to distinguish representational transport from readout-only movement.

## Activation Geometry Probe: Trained Readout Gate

Question: does the hook-output label-free transfer ridge survive a trained readout?

Current regime:

- Artifact types: label-free patch payloads, hook-output patch-vector manifests, centroid/ridge readout summaries, source-noop identity tables, baseline percentile summaries.
- Operations: hook-output activation capture, held-out centroid readout scoring, one-vs-all multiclass ridge fitting, final-token activation patching at transformer-block outputs.
- Gates/verifiers: exact definition/source-noop identity, definition-vs-neutral stress, centroid-vs-ridge readout agreement, two-seed replication, baseline percentile comparison.
- Known limitations: one checkpoint, one readout layer, no behavior-level task yet.

Action class:

- Retrieval/search/discovery: verifier refinement.
- Why: the run adds trained readout mode as a first-class verifier dimension and tests whether the existing ridge survives a different scoring surface.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/trained_readout_gate_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_trained_readout_gate_seed*.json`.
- Positive targets: focus rows plus 24 sampled baseline pairs per seed.
- Negative controls: neutral patch text, distractor/random/source-noop patch modes, broad baseline rows.
- Stress tests: readout modes `centroid,ridge`; injection layers `4,5,6`; alphas `0.75,1.0`; two seeds.

Gate:

- Acceptance rule: accept readout-mode robustness only if ridge readout preserves the definition transfer ridge, definition/source-noop is exact, and neutral carriers do not match definition specificity.
- Withheld/rejected rule: reject attractor-specific revival unless focus/source-family rows are clearly exceptional against baseline and generic controls.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/trained_readout_gate_2026_06_08.md`; `experiments/activation_geometry/modal_label_free_readout_basin.py`; `experiments/activation_geometry/label_free_readout_basin.py`; `scripts/summarize_label_free_dose_response.py`.
- Rejected or withheld artifacts: attractor-specific revival remains rejected.
- Key metrics: definition/source-noop max delta `0.0`; ridge definition pass rates reach `42/62` at `4 -> 6`, `53/62` at `5 -> 6`, and `57/62` at `6 -> 6`; ridge neutral at `6 -> 6`, alpha `1.0` reaches `17/62`.
- Variance or ablation: both seeds show the same layer ordering; ridge margins shrink relative to centroid while pass rates stay strong or improve.

Residual content:

- Explained by old regime: broad definition-derived transfer remains generic rather than attractor-specific.
- New content outside old regime: the transfer ridge survives a trained linear readout and is not merely nearest-centroid geometry.
- Retractions or supersessions: supersede "centroid readout may be producing the ridge" with "centroid is not necessary for the ridge, though readout-space movement still needs behavior-level validation."

Next move: add a behavior-level gate that tests whether readout-space transport predicts answer/logprob changes.

## Activation Geometry Probe: Behavior-Level Gate

Question: does the trained-readout-confirmed hook-output transfer ridge change next-token behavior?

Current regime:

- Artifact types: hook-output patch payloads, centroid/ridge readout summaries, behavior prompt frames, option-order logprob rows, target-vs-control specificity summaries.
- Operations: label-free definition/neutral patch-vector capture, final-token activation patching, option-token logprob scoring, prompt-frame ablation.
- Gates/verifiers: target patch must robustly improve target margin across option orders and beat distractor/random/source-noop controls; neutral carriers should not match definition specificity.
- Known limitations: one checkpoint, option-token answer surface, no learned behavior-aligned direction.

Action class:

- Retrieval/search/discovery: verifier transition with rejected claim.
- Why: this run adds behavior-level logprob scoring as a new verifier type and tests whether the representational ridge crosses into model choices.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/behavior_level_gate_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_behavior_gate*.json`.
- Positive targets: focus rows plus 8 sampled baseline pairs.
- Negative controls: neutral patch text, distractor/random/source-noop patch modes, option-order controls.
- Stress tests: prompt frames `source_passage` and `latent_choice`; injection layers `4,5,6`; alphas `0.75,1.0`.

Gate:

- Acceptance rule: accept behavior transfer only if definition target patches have positive robust target-margin movement and positive target-over-control advantage.
- Withheld/rejected rule: withhold behavior-level claims if controls match or exceed target patches.

Results:

- Accepted artifacts: `experiments/activation_geometry/modal_label_free_behavior_gate.py`; `experiments/activation_geometry/label_free_behavior_gate.py`; `scripts/summarize_label_free_behavior_gate.py`; `experiments/activation_geometry/results/behavior_level_gate_2026_06_08.md`.
- Rejected or withheld artifacts: behavior-level transfer claim is withheld.
- Key metrics: definition source-passage max pass rate `3/15`; definition latent-choice max pass rate `2/15`; mean target-over-control advantage is non-positive in every definition cell.
- Variance or ablation: removing source-passage text does not rescue target specificity.

Residual content:

- Explained by old regime: readout-space movement remains real but does not imply behavioral steering.
- New content outside old regime: the project now has a behavior verifier that can reject overclaims.
- Retractions or supersessions: supersede "next step may confirm behavior transfer" with "simple behavior transfer fails under option-token gates; behavior alignment needs a stronger intervention or different interface."

Next move: design a behavior-aligned intervention rather than raw state replacement.

## Activation Geometry Probe: Behavior Alignment Breakthrough Path

Question: after the option-token behavior gate failed, can full-label scoring or learned behavior-aligned directions expose behavior-level transfer?

Current regime:

- Artifact types: hook-output patch payloads, option-token behavior rows, full-label continuation rows, learned-gradient direction rows, target-vs-control specificity summaries.
- Operations: label-free definition/neutral state capture, final-token hook-output replacement, full-label continuation logprob scoring, train-variant gradient averaging, held-out option-token intervention.
- Gates/verifiers: target must beat distractor/random/source-noop controls; definition should exceed neutral carrier; learned target direction should exceed source/distractor/random directions and avoid valence/control-layer leakage.
- Known limitations: one seed, one small causal LM, exact-label scoring, neutral carriers are active, learned directions are still option-token based.

Action class:

- Retrieval/search/discovery: verifier transition plus intervention search.
- Why: full-label scoring creates a new behavior verifier that accepts effects the previous option-token verifier rejected; learned directions add a new behavior-aligned intervention class.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/behavior_alignment_breakthrough_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_full_label_behavior*.json` and `artifacts/activation_geometry/modal_pythia_70m_behavior_aligned_direction_seed20260608.json`.
- Positive targets: focus rows plus 8 sampled baseline pairs for full-label; promoted steering pairs for learned directions.
- Negative controls: neutral patch text, distractor/random/source-noop patch modes, source/distractor learned directions, random same-norm direction, valence controls, control layer.
- Stress tests: prompt frames `latent_choice` and `source_passage`; injection layers `4,5,6`; alphas `0.75,1.0`; learned scales `0.5,1.0,2.0`.

Gate:

- Acceptance rule: accept behavior-surface improvement if definition target patches beat controls and definition carriers exceed neutral carriers on average.
- Withheld/rejected rule: withhold clean semantic-causality or learned-direction claims if neutral carriers, valence controls, or control-layer directions match too much of the effect.

Results:

- Accepted artifacts: full-label behavior scoring surface; learned behavior-aligned direction pilot; Modal packaging fix for learned-direction runner.
- Rejected or withheld artifacts: clean semantic-causality claim and learned-direction mechanism claim remain withheld.
- Key metrics: full-label definition target patches pass up to `12/15`, with mean target-over-control advantage up to `0.881`; definition exceeds neutral mean advantage in every full-label cell; learned target direction passes `3/3` primary positives at all scales but also shows control leakage.
- Variance or ablation: source-passage and latent-choice frames both show full-label movement; neutral carrier and learned-direction controls expose remaining confounds.

Residual content:

- Explained by old regime: broad definition-derived transfer remains generic and label carriers can move behavior surfaces.
- New content outside old regime: the behavior-level negative result is surface-dependent; full-label continuation scoring exposes a behavior-visible effect.
- Retractions or supersessions: supersede "raw state replacement fails behavior-level gates" with "raw state replacement fails option-token gates but passes full-label behavior gates with neutral-carrier caveats."

Next move: replicate full-label behavior gates with stronger carrier/label controls and learn directions against the full-label objective.

## Activation Geometry Probe: Full-Label Carrier Controls

Question: does the full-label behavior effect survive stronger carrier controls?

Current regime:

- Artifact types: full-label behavior payloads, patch-text carrier regimes, target-vs-control specificity rows, definition-minus-control contrast summaries.
- Operations: hook-output state capture from different carrier texts, full-label continuation scoring, source/noop/distractor/random patch controls.
- Gates/verifiers: full definition should exceed label-only, neutral, blank-carrier, and shuffled-label controls; blank and shuffled controls should fail if the effect is concept/label-specific.
- Known limitations: one seed, one model, exact-label scoring, no alias target labels yet.

Action class:

- Retrieval/search/discovery: verifier refinement.
- Why: this run adds new carrier-control artifact classes that distinguish arbitrary carrier movement, wrong-label movement, label-only movement, and definition-context boost.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/full_label_carrier_controls_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_full_label_carrier_controls_*.json`.
- Positive targets: focus rows plus 8 sampled baseline pairs.
- Negative controls: `blank_carrier`, `shuffled_label`, distractor/random/source-noop patch modes.
- Stress tests: prompt frames `latent_choice` and `source_passage`; layers `5,6`; stripped-definition, neutral, and label-only carrier ablations.

Gate:

- Acceptance rule: accept strengthened full-label behavior claim if full definitions beat controls and shuffled/blank carriers fail.
- Withheld/rejected rule: withhold pure semantic transfer if stripped definitions or label-free carriers match the full definition effect.

Results:

- Accepted artifacts: carrier-control regimes in the full-label behavior gate; `experiments/activation_geometry/results/full_label_carrier_controls_2026_06_08.md`.
- Rejected or withheld artifacts: pure semantic-transfer claim remains withheld.
- Key metrics: full definitions pass `9/15` to `12/15`; label-only/neutral are active but weaker; blank carriers pass `0/15`; shuffled-label carriers pass at most `1/15` with negative mean advantage.
- Variance or ablation: source-passage and latent-choice frames agree on the ordering: `definition` > `neutral/label_only` > `blank_carrier/shuffled_label`.

Residual content:

- Explained by old regime: exact label strings can steer full-label behavior.
- New content outside old regime: full definitions add a target-specific boost beyond label-only carriers, while wrong labels actively suppress target-specificity.
- Retractions or supersessions: supersede "neutral carrier activity makes the full-label result uninterpretable" with "the effect is label-anchored and definition-context boosted."

Next move: replicate across seed/model and test alias labels to separate exact-string anchoring from conceptual behavior transfer.

## Activation Geometry Probe: Full-Label Alias Gate

Question: does canonical full-label behavior transfer survive non-identical alias scoring?

Current regime:

- Artifact types: alias-label manifests, full-label behavior payloads, canonical-vs-alias specificity rows, alias survivor pocket tables.
- Operations: hook-output state capture from canonical carriers, full-label continuation scoring over canonical and alias labels, target-vs-control specificity aggregation.
- Gates/verifiers: canonical definition patches should reproduce the carrier-control result; alias patches must beat distractor/random/source-noop controls to count as label-invariant concept transfer.
- Known limitations: one seed, one model, one alias per concept, aliases are hand-authored, no alias-trained behavior direction yet.

Action class:

- Retrieval/search/discovery: verifier refinement with a boundary result.
- Why: this run changes the scored lexical surface and tests whether behavior transfer is label-invariant.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/full_label_alias_gate_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_full_label_alias_*.json`.
- Positive targets: focus rows plus 8 sampled baseline pairs.
- Negative controls: alias scoring against distractor/random/source-noop patch modes, `blank_carrier`, `shuffled_label`, `neutral`, `label_only`.
- Stress tests: prompt frames `latent_choice` and `source_passage`; layers `5,6`; canonical vs alias scoring.

Gate:

- Acceptance rule: accept label-invariant behavior transfer only if alias-scored definition target patches pass robustly and have positive target-over-control advantage.
- Withheld/rejected rule: withhold concept-level behavior transfer if alias target movement is matched or exceeded by controls.

Results:

- Accepted artifacts: alias label manifest, alias scoring support in the behavior gate, `experiments/activation_geometry/results/full_label_alias_gate_2026_06_08.md`.
- Rejected or withheld artifacts: broad label-invariant behavior transfer claim remains withheld.
- Key metrics: canonical definitions pass `9/15` to `12/15` with mean advantage `0.622` to `0.881`; alias definitions pass only `4/15` to `6/15` and have negative mean advantage from `-0.094` to `-0.196`.
- Variance or ablation: both prompt frames agree: canonical effect replicates; alias specificity collapses globally; a few pair-specific alias pockets remain.

Residual content:

- Explained by old regime: exact canonical labels dominate the behavior-visible effect.
- New content outside old regime: alias scoring reveals weak, pair-specific synonym pockets that may mark either true concept transfer or alias-surface confounds.
- Retractions or supersessions: supersede "full-label behavior transfer may be concept-level" with "full-label behavior transfer is currently canonical-label anchored, with only local alias pockets."

Next move: run multiple-alias and alias-shuffle diagnostics, then try alias-trained behavior-aligned directions.

## Activation Geometry Probe: Alias-Trained Behavior Direction

Question: can alias-label behavior be made addressable by learning behavior-aligned directions directly against alias objectives?

Current regime:

- Artifact types: alias-label manifests, full-label gradient directions, canonical/alias eval rows, direction-control rows, leakage tables.
- Operations: train-variant full-label gradient averaging, held-out full-label continuation scoring, cross-label evaluation, source/distractor/random direction controls.
- Gates/verifiers: target-learned direction should beat source/distractor/random controls; alias-trained direction should improve alias labels and transfer to canonical labels; semantic claims require avoiding valence and control-layer leakage.
- Known limitations: one seed, one model, per-pair learned directions, no residualization, no second alias per concept yet.

Action class:

- Retrieval/search/discovery: intervention search with rejected mechanism claim.
- Why: this adds alias full-label gradients as an intervention class, but the resulting direction fails semantic-specificity controls.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/alias_trained_behavior_direction_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_alias_trained_direction*.json`.
- Positive targets: promoted steering pairs.
- Negative controls: source-learned, distractor-learned, random-same-norm directions; valence-control pairs; control layer.
- Stress tests: prompt frames `latent_choice` and `source_passage`; eval labels `alias` and `canonical`; scales `0.5,1.0,2.0`.

Gate:

- Acceptance rule: accept alias addressability if target-learned directions reliably improve alias target margins and beat source/distractor/random directions.
- Withheld/rejected rule: withhold semantic transport if valence controls or control-layer positives pass at comparable strength.

Results:

- Accepted artifacts: full-label alias objective support in the learned-direction runner; `experiments/activation_geometry/results/alias_trained_behavior_direction_2026_06_08.md`.
- Rejected or withheld artifacts: semantic transport claim remains withheld.
- Key metrics: target-learned directions pass `3/3` primary positives for both prompt frames, all scales, and both eval label regimes; source/distractor directions are negative on mean; target-learned valence controls pass `2/2` and control-layer positives pass `3/3`.
- Variance or ablation: source-passage and latent-choice frames agree; alias-trained directions also transfer to canonical scoring.

Residual content:

- Explained by old regime: direct behavior gradients can control label logits.
- New content outside old regime: alias-label behavior is addressable and cross-label transferable, but only through a leaky output-control direction.
- Retractions or supersessions: supersede "alias labels may be unreachable behaviorally" with "alias labels are behaviorally reachable, but raw transported states and direct gradients occupy different regimes."

Next move: build residualized alias directions that subtract source/distractor/control components, then rerun the alias gate against leakage controls.

## Activation Geometry Probe: Residualized Alias Direction

Question: can simple residualization make alias-trained behavior directions less leaky without losing positive concept movement?

Current regime:

- Artifact types: alias-label manifests, full-label gradient directions, residualized direction modes, canonical/alias eval rows, leakage tables.
- Operations: train-variant full-label gradient averaging, projection residualization, leave-one-out control-basis construction, held-out full-label continuation scoring.
- Gates/verifiers: positive pairs must pass in primary/backup layers; valence controls and control-layer positives must not pass at comparable strength; residual modes should improve target-over-control specificity.
- Known limitations: one seed, one model, one alias per concept, post-hoc linear residuals only.

Action class:

- Retrieval/search/discovery: search with a rejected simplification.
- Why: this adds residualized direction modes inside the existing behavior-direction schema and tests whether leakage is linearly removable.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/residualized_alias_direction_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_residualized_alias_direction_*.json`.
- Positive targets: promoted steering pairs.
- Negative controls: same-norm random directions; valence-control pairs; control layer.
- Stress tests: prompt frames `latent_choice` and `source_passage`; eval labels `alias` and `canonical`; scales `0.5,1.0,2.0`.

Gate:

- Acceptance rule: promote residualized semantic transport only if positive pairs remain robust while primary valence controls and control-layer positives fail or become much weaker than positives.
- Withheld/rejected rule: withhold semantic claims if controls still pass, even when their mean deltas are attenuated.

Results:

- Accepted artifacts: residualized direction modes in the learned-direction runner; `experiments/activation_geometry/results/residualized_alias_direction_2026_06_08.md`.
- Rejected or withheld artifacts: the simple linear-removal explanation is rejected; semantic transport remains withheld.
- Key metrics: `target_resid_all` keeps `3/3` primary positives in every frame/eval setting at scale `1.0`; it reduces valence-control means by `23.1%` to `49.4%`; controls still pass `2/2` except source-passage canonical, where they drop to `1/2`.
- Variance or ablation: source/distractor-only and control-only residuals are weaker than the combined residual; source-passage canonical is cleaner than alias scoring.

Residual content:

- Explained by old regime: behavior gradients can move target labels and random directions are much weaker.
- New content outside old regime: leakage has at least two distinguishable channels; `valence->activation_vector` can be suppressed in one setting, but `valence->steering_vector` remains adversarial.
- Retractions or supersessions: supersede "subtract a generic control component" with "post-hoc projection is only an attenuation method, not a specificity method."

Next move: replace post-hoc residualization with a constrained behavior objective that penalizes `valence->steering_vector` during direction construction.

## Activation Geometry Probe: Constrained Alias Direction

Question: can a named adversarial-control penalty make alias-trained behavior directions more specific without destroying positive concept movement?

Current regime:

- Artifact types: alias-label manifests, full-label gradient directions, constrained direction modes, canonical/alias eval rows, adversarial-control tables.
- Operations: train-variant full-label gradient averaging, norm-matched hard-control subtraction, held-out full-label continuation scoring, prompt-frame replication.
- Gates/verifiers: positives must remain robust; independent valence controls should be suppressed; construction-zeroed controls are sanity checks, not independent successes.
- Known limitations: one seed, one model, one manually chosen hard-control channel, one alias per concept.

Action class:

- Retrieval/search/discovery: search with a promising new operation.
- Why: this adds an adversarial-control direction-construction operation and produces a specificity frontier that post-hoc residualization did not expose.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/constrained_alias_direction_2026_06_09.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_constrained_alias_direction_*.json`.
- Positive targets: promoted steering pairs.
- Negative controls: `valence->activation_vector`, `valence->steering_vector`, mean-control penalty, random same-norm controls, control layer.
- Stress tests: prompt frames `source_passage` and `latent_choice`; eval labels `alias` and `canonical`; scales `0.5,1.0,2.0`.

Gate:

- Acceptance rule: accept a constrained-direction improvement if positives remain `3/3` while independent valence-control means fall substantially below raw target-learned means.
- Withheld/rejected rule: withhold full semantic specificity if any independent valence control still passes or if suppression depends on construction-zeroing.

Results:

- Accepted artifacts: hard-control penalty direction modes; `experiments/activation_geometry/results/constrained_alias_direction_2026_06_09.md`.
- Rejected or withheld artifacts: full semantic specificity remains withheld; mean-control subtraction is rejected as insufficient.
- Key metrics: at scale `1.0`, `target_penalty_hard_1_0` keeps `3/3` positives in both prompt frames and both eval regimes; it reduces mean valence-control deltas by `69.0%` to `95.6%`; `valence->activation_vector` still passes.
- Variance or ablation: hard penalty `2.0` suppresses controls more strongly but damages canonical positives; mean-control penalty preserves positives but leaves controls passing.

Residual content:

- Explained by old regime: behavior gradients can move labels and simple projections attenuate leakage.
- New content outside old regime: a named adversarial-control penalty exposes a tunable specificity/strength frontier.
- Retractions or supersessions: supersede "post-hoc residualization is the best available cleanup" with "constrained direction construction is the more promising path."

Next move: build a multi-control constrained objective and evaluate it against held-out aliases/controls.

## Symbolic Weakness Benchmark: Prefix-Shift Pilot

Question: can weakness or invariance identify the OOD-generalizing rule when several train-perfect symbolic rules fit the data?

Current regime:

- Artifact types: symbolic tasks, candidate rules, selector metrics, OOD splits, markdown result reports, audit cards.
- Operations: cyclic task generation, candidate enumeration, translation-equivariance scoring, selector comparison, deterministic pilot runs.
- Gates/verifiers: unit tests, train-perfect selector check, OOD accuracy, invariant-selection rate, local-patch negative controls, publication guard.
- Known limitations: the admissible transformation group is supplied by the evaluator; neural learners and learned transformation discovery are not included yet.

Action class:

- Retrieval/search/discovery: search.
- Why: this creates a sharper benchmark inside the existing weakness-vs-simplicity program. It does not yet add a learned weakness verifier.

Experiment:

- Manifest/report paths: `experiments/symbolic_weakness/results/prefix_shift_pilot_2026_06_09.md`.
- Positive targets: weakness selector should choose the global cyclic shift and generalize OOD.
- Negative controls: train loss, simplicity, compression, flatness proxy, and random train-consistent selection.
- Stress tests: pending seed/modulus/train-window sweeps and wrong/noisy transformation-group controls.

Gate:

- Acceptance rule: all reported selectors train-perfect; weakness invariant rate and mean OOD accuracy at least `0.95`; train loss, simplicity, compression, and flatness proxy local-patch rate at least `0.95` and mean OOD accuracy at most `0.15`.
- Withheld/rejected rule: do not claim neural, learned-rule, learned-symmetry, or strong flatness-baseline evidence from this symbolic oracle pilot.

Results:

- Accepted artifacts: `experiments/symbolic_weakness/experiment.py`, `tests/test_symbolic_weakness.py`, and `experiments/symbolic_weakness/results/prefix_shift_pilot_2026_06_09.md`.
- Rejected or withheld artifacts: raw JSON under `artifacts/symbolic_weakness/`.
- Key metrics: weakness mean OOD accuracy `1.000`, invariant rate `1.000`; train loss, simplicity, compression, and flatness proxy mean OOD accuracy `0.000`, local-patch rate `1.000`; all selectors mean train accuracy `1.000`.
- Variance or ablation: 300 trials over moduli `{7, 11, 13}` with seed `11`; broader sweeps pending.

Residual content:

- Explained by old regime: weak compatible constraints can beat short local descriptions in synthetic settings.
- New content outside old regime: the paper target now has a concrete symbolic symmetry benchmark where weakness cleanly predicts OOD while loss, simplicity, compression, and a flatness proxy fail.
- Retractions or supersessions: the older Boolean-only weakness benchmark should be treated as preliminary; the flagship track should use symmetry and transformation compatibility as the central operationalization.

Next move: run symbolic sweeps, add non-cyclic task families, add wrong/noisy group controls, then train small neural models and measure latent equivariance as model-level weakness.

## Activation Geometry Probe: Multi-Control Alias Holdout

Question: does the constrained alias-direction frontier survive held-out alias and leave-one-out multi-control stress tests?

Current regime:

- Artifact types: alias-indexed label manifests, full-label gradient directions, constrained direction modes, held-out alias eval rows, leave-one-out control rows.
- Operations: alias-indexed label scoring, norm-matched multi-control subtraction, held-out full-label continuation scoring.
- Gates/verifiers: held-out alias positives must remain robust; independent controls must weaken relative to raw target directions; construction-zeroed controls do not count as independent evidence.
- Known limitations: Pythia-70M only, three positives, two valence controls, one held-out alias per concept.

Action class:

- Retrieval/search/discovery: verifier hardening with a rejected candidate.
- Why: this adds a held-out alias verifier and falsifies the current constrained frontier as a paper-level mechanism.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/multicontrol_alias_holdout_2026_06_09.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_multicontrol_alias_holdout_*.json`.
- Positive targets: promoted steering pairs.
- Negative controls: valence controls with leave-one-out control bases; random same-norm controls.
- Stress tests: `source_passage` and `latent_choice`; eval labels `alias_0`, `alias_1`, and `canonical`; penalty weights `0.5`, `1.0`, `2.0`.

Gate:

- Acceptance rule: promote the constrained frontier only if held-out `alias_1` positives remain `3/3` while independent controls weaken.
- Withheld/rejected rule: withhold if any positive systematically fails under held-out alias or if controls still pass.

Results:

- Accepted artifacts: `alias_0`/`alias_1` regimes; multi-control penalty modes; `experiments/activation_geometry/results/multicontrol_alias_holdout_2026_06_09.md`.
- Rejected or withheld artifacts: current constrained alias direction remains non-paper-ready.
- Key metrics: raw target directions pass `3/3` held-out `alias_1` positives but controls pass `2/2`; constrained modes reduce controls but drop held-out positives to `2/3`, consistently failing `attractor->attractor_network`.
- Variance or ablation: both prompt frames agree on the held-out alias failure; canonical and `alias_0` remain easier than `alias_1`.

Residual content:

- Explained by old regime: exact-label and first-alias behavior surfaces are easier to control than label-invariant concept behavior.
- New content outside old regime: held-out alias scoring exposes an alias-specific weakness in the constrained frontier.
- Retractions or supersessions: supersede "hard-control penalty is close to paper-ready" with "hard-control penalty is a useful frontier but not alias-invariant."

Next move: jointly train over multiple aliases and broaden the concept/control set before scaling models.

## Weakness Predicts OOD: Multi-Family Symbolic + Neural

Question: does symmetry-compatible-hypothesis weakness predict OOD generalization (a) across symbolic task families that admit local shortcuts, and (b) across trained neural networks with diverse architecture and data-augmentation regimes?

Current regime:

- Artifact types: family registry, selector registry, multi-family benchmark JSON with Wilson 95% CIs, neural sweep JSON with per-model artefacts, correlation summaries, Modal entrypoints.
- Operations: synthetic candidate generation, with-action equivariance counting, leave-one-out validation, MDL-style compression scoring, Hutchinson sharpness probe, group inference from data, group corruption (wrong/noisy), unit tests.
- Gates/verifiers: pre-registered acceptance thresholds in `experiments/symbolic_weakness/results/*.md`; Wilson 95% CIs; `compileall`; `unittest`; publication guard.
- Known limitations: domains are finite and small (n ≤ 13); the parity family is a known negative case (|G|=2 too small to disambiguate); the S_n family is a known partial case (centralizer sizes coincide for many wrong involutions).

Action class:

- Retrieval/search/discovery: discovery + search. The benchmark *discovers* the operating regime in which weakness is and is not load-bearing.

Gate:

- Acceptance: `weakness_oracle` selects the invariant family in ≥95% of cyclic and dihedral trials (Wilson 95% CI lower bound ≥0.95); `weakness_wrong_group` selects the invariant in ≤5% of those trials; on the neural side, `weakness_oracle_norm` Pearson correlation with OOD accuracy exceeds 0.4 across ≥256 models with diverse augmentation/architecture/init/optimizer.
- Withheld: claims of universal weakness superiority, claims about non-symbolic domains (language/perception), claims about parity/S_n where the benchmark explicitly fails.

Results:

- Accepted artifacts: `experiments/symbolic_weakness/results/multi_family_500_2026_06_09.md`, `experiments/symbolic_weakness/results/neural_sweep_v3_2026_06_09.md`, `experiments/symbolic_weakness/results/modal_neural_sweep_v1_2026_06_09.md`, `papers/weakness_invariance_neurips/paper.md`.
- Key metrics: cyclic and dihedral weakness invariant-rate 1.000 with CI lower bound ≥0.992; classical baselines invariant-rate 0.000 with CI upper bound ≤0.008; neural weakness_oracle_norm Pearson with OOD = +0.817 (local 256-MLP sweep) / +0.813 (Modal 1024-MLP sweep), wrong-group control Pearson ≤ −0.116 across both runs.
- Variance or ablation: wrong-group, noisy-group, data-inferred-group, partial-cyclic-group, and random-label controls all show the expected directional behavior (wrong/random → null, noisy/inferred → mostly recover).

Residual content:

- Explained by current regime: simplicity, MDL, training loss, parameter norm, sharpness, and held-out validation are insufficient to disambiguate train-perfect shortcuts from globally invariant rules on the symbolic families where the candidate group is rich enough to separate them.
- New content outside current regime: parity and S_n require either a richer candidate transformation set or a fundamentally different selector — they delineate the operating boundary of weakness-as-symmetry-volume.
- Retractions: none.

Next move: add compositional task families (Z_n × Z_m); add a small-transformer variant; investigate whether learned-group inference can extend weakness to S_n where the oracle group is too coarse.

## Activation Geometry Probe: Multi-Alias Expanded Specificity

Question: does multi-alias objective training plus a larger pair set produce semantic-specific behavior directions?

Current regime:

- Artifact types: alias-indexed label manifests, grouped objective regimes, full-label gradient directions, expanded pair manifests, specificity reports.
- Operations: multi-alias gradient averaging, held-out alias scoring, norm-matched multi-control penalties, specificity-score comparison.
- Gates/verifiers: held-out alias positives must transfer and independent controls must remain lower than positives under the same score surface.
- Known limitations: one model, one seed, no generation scoring yet, expanded controls are hand-picked rather than random-relation nulls.

Action class:

- Retrieval/search/discovery: verifier hardening with a rejected candidate.
- Why: this creates a stronger gate and falsifies the current multi-alias behavior objective as a paper-ready specificity mechanism.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/multialias_expanded_specificity_2026_06_09.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_multialias_expanded_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: expanded control pairs with leave-one-out control bases.
- Stress tests: `source_passage` and `latent_choice`; held-out `alias_2`; canonical labels; three scales.

Gate:

- Acceptance rule: pass if held-out `alias_2` positives remain high while controls are suppressed enough to make specificity clearly positive.
- Withheld/rejected rule: withhold if controls pass broadly or specificity is near zero/negative.

Results:

- Accepted artifacts: grouped objective regimes; third aliases; expanded pair set; result report.
- Rejected or withheld artifacts: multi-alias constrained behavior directions remain non-paper-ready.
- Key metrics: held-out `alias_2` target-learned reaches `6/7` positives in both prompt frames but controls pass `5/5`; specificity is `0.034` in `source_passage` and `0.002` in `latent_choice`.
- Variance or ablation: both prompt frames agree; constrained and residual modes do not improve specificity.

Residual content:

- Explained by old regime: behavior gradients can move many held-out target labels.
- New content outside old regime: the main obstacle is now identifiable as broad control leakage, not just single-alias fragility.
- Retractions or supersessions: supersede "multi-alias training may be enough" with "multi-alias training improves transfer but not specificity."

Next move: diagnose whether leakage is low-rank or pair-specific.

## Activation Geometry Probe: Direction Subspace Diagnostic

Question: is behavior-direction leakage low-rank or pair-specific?

Current regime:

- Artifact types: behavior target-gradient directions, pairwise cosine summaries, singular spectra, control-subspace capture tables.
- Operations: multi-alias target-gradient extraction, normalized direction SVD, control-subspace projection, pairwise cosine ranking.
- Gates/verifiers: low-rank leakage would show high control energy in one or two components and high positive capture by that control subspace; pair-specific leakage would show low average capture but high individual pair overlaps.
- Known limitations: one model, one layer, one seed; no random relation nulls yet.

Action class:

- Retrieval/search/discovery: mechanistic diagnostic.
- Why: this adds a direction-subspace artifact class that was missing from the previous score-only specificity gates.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/direction_subspace_diagnostic_2026_06_09.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_direction_subspace_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: expanded control pairs.
- Stress tests: `source_passage` and `latent_choice`.

Gate:

- Acceptance rule: classify leakage as low-rank only if low-rank control components capture most positive direction energy on average.
- Withheld/rejected rule: withhold low-rank explanation if average positive capture stays low and high overlaps are pair-specific.

Results:

- Accepted artifacts: Modal subspace diagnostic and result report.
- Rejected or withheld artifacts: one-vector or simple low-rank shared leakage explanation.
- Key metrics: control effective rank `4.179`/`4.201`; rank-5 control subspace captures only `0.159`/`0.194` positive energy on average, but max pair capture reaches `0.581`/`0.676`.
- Variance or ablation: source and latent prompt frames agree.

Residual content:

- Explained by old regime: broad full-label gradients move many labels.
- New content outside old regime: leakage is localized in relation pockets, not captured by one shared control vector.
- Retractions or supersessions: supersede "subtract the control subspace" with "stratify controls and add target-disjoint random relation nulls."

Next move: add random relation nulls and target-disjoint controls.

## Activation Geometry Probe: Target-Disjoint Null Controls

Question: do target-disjoint controls turn the multi-alias behavior direction into a semantically specific intervention?

Current regime:

- Artifact types: alias-indexed behavior-direction manifests, target-disjoint control pair sets, specificity tables, result reports.
- Operations: full-label multi-alias target-gradient construction, held-out-alias scoring, residual/penalty baselines, random same-norm comparison.
- Gates/verifiers: positives must transfer on held-out labels; controls with disjoint targets must not move comparably; canonical labels should not make controls stronger than positives.
- Known limitations: one model, one seed, hand-picked target-disjoint controls, label-logprob scoring only.

Action class:

- Retrieval/search/discovery: verifier hardening with a rejected candidate.
- Why: this adds a target-disjoint control family and falsifies the explanation that the main failure was only same-target control overlap.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/target_disjoint_null_controls_2026_06_09.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_target_disjoint_nulls_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: six controls whose targets are disjoint from all positive targets.
- Stress tests: `source_passage` and `latent_choice`; held-out `alias_2`; canonical labels; random same-norm baseline.

Gate:

- Acceptance rule: move toward Phase 2 only if held-out positives remain high and target-disjoint controls fall enough to make specificity clearly positive.
- Withheld/rejected rule: withhold semantic specificity if target-disjoint controls still pass broadly or canonical specificity is negative.

Results:

- Accepted artifacts: `expanded_target_disjoint` pair set and result report.
- Rejected or withheld artifacts: target-disjoint control rescue of the current behavior objective.
- Key metrics: target-learned directions move `6/7` positives and `6/6` controls in both prompt frames; held-out `alias_2` specificity is `0.066` in `source_passage` and `0.007` in `latent_choice`; canonical specificity is negative.
- Variance or ablation: source and latent prompt frames agree; residual and control-penalty modes do not improve the gate.

Residual content:

- Explained by old regime: behavior target gradients can move many labels and random directions are much weaker on mean delta.
- New content outside old regime: target-disjoint controls show that the leakage is broader than same-target-pocket overlap.
- Retractions or supersessions: supersede "target-pocket overlap may be the main issue" with "target-pocket overlap exists, but broad full-label transport also survives target-disjoint controls."

Next move: add randomized relation nulls and CAA/CAV baselines, then shift the main evidence target toward generation/readout behavior rather than relying on full-label logprob gates.

## Activation Geometry Probe: Random Relation Null Controls

Question: do random relation nulls reveal whether the behavior directions are semantic bridges or broad label-surface transport directions?

Current regime:

- Artifact types: alias-indexed behavior-direction manifests, random-relation null pair sets, specificity tables, result reports.
- Operations: deterministic random-null pair construction, fallback distractor selection, full-label multi-alias target-gradient construction, held-out-alias scoring.
- Gates/verifiers: positives must beat random relation nulls under the same score surface; controls should not all pass; canonical controls should not be stronger than canonical positives.
- Known limitations: one model, one seed, random nulls are seeded once, no generation or learned behavior-readout scoring yet.

Action class:

- Retrieval/search/discovery: verifier hardening with a rejected candidate.
- Why: this adds randomized relation nulls and turns the previous ambiguity into a clear falsification of the current logprob-specificity claim.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/random_relation_null_controls_2026_06_09.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_random_relation_nulls_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: ten seeded random relation null controls with targets disjoint from the positive target set.
- Stress tests: `source_passage` and `latent_choice`; held-out `alias_2`; canonical labels; random same-norm baseline.

Gate:

- Acceptance rule: continue toward paper-level semantic specificity only if positives exceed random relation nulls by a clearly positive specificity margin.
- Withheld/rejected rule: reject the current logprob gate if random nulls all pass or their means exceed positives.

Results:

- Accepted artifacts: `expanded_random_nulls` pair set and result report.
- Rejected or withheld artifacts: the current target-gradient/residual/penalty directions as a semantically specific mechanism.
- Key metrics: target-learned directions move `6/7` positives and `10/10` random null controls in both prompt frames; held-out `alias_2` specificity is `-0.101` in `source_passage` and `-0.137` in `latent_choice`.
- Variance or ablation: source and latent prompt frames agree; canonical specificity is also negative; random same-norm controls remain weak.

Residual content:

- Explained by old regime: full-label gradients can move labels, and random directions are much weaker.
- New content outside old regime: random relation nulls move more than intended positives, showing that the verifier itself rewards broad label transport.
- Retractions or supersessions: supersede "more controls may rescue this logprob gate" with "the logprob gate is now a diagnostic failure mode unless a new behavior verifier separates positives from random nulls."

Next move: implement CAA/CAV baselines and a non-logprob behavior gate before spending on more seeds or larger models.

## Activation Geometry Probe: CAA/CAV Baseline Random Nulls

Question: do CAA/CAV-style activation-difference directions avoid the random relation null failure that invalidated target-gradient behavior directions?

Current regime:

- Artifact types: alias-indexed behavior-direction manifests, activation-mean CAA/CAV direction vectors, random-relation null pair sets, specificity tables, result reports.
- Operations: source-passage activation extraction, mean activation differencing, norm matching to target-gradient directions, held-out alias scoring.
- Gates/verifiers: positives must beat random relation nulls under the same score surface; controls should not broadly pass; canonical controls should not be stronger than positives.
- Known limitations: one model, one seed, CAA vectors use simple mean differences, no generation/readout scoring yet.

Action class:

- Retrieval/search/discovery: baseline hardening with a rejected rescue.
- Why: this adds a CAA/CAV-style baseline operation and tests whether the failure was construction-specific rather than verifier-specific.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/caa_cav_baseline_random_nulls_2026_06_09.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_caa_baseline_random_nulls_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: ten seeded random relation null controls.
- Stress tests: `source_passage` and `latent_choice`; held-out `alias_2`; canonical labels; random same-norm baseline.

Gate:

- Acceptance rule: continue toward paper-level semantic specificity only if a CAA/CAV baseline keeps high held-out positive transfer while suppressing random-null controls enough to make specificity clearly positive.
- Withheld/rejected rule: reject the CAA/CAV rescue if random null controls still broadly pass or canonical specificity is negative.

Results:

- Accepted artifacts: CAA/CAV direction modes and result report.
- Rejected or withheld artifacts: CAA/CAV as a semantically specific mechanism under the current full-label logprob verifier.
- Key metrics: best source-passage held-out alias CAA row is `caa_target_minus_source`, with `7/7` positives, `7/10` controls, and specificity `0.066`; best latent held-out alias CAA row is `caa_target_minus_source`, with `7/7` positives, `10/10` controls, and specificity `0.043`.
- Variance or ablation: source and latent prompt frames agree that CAA moves positives but does not suppress random nulls; canonical specificity is negative for all CAA modes.

Residual content:

- Explained by old regime: both gradient and CAA directions can move held-out target labels.
- New content outside old regime: a standard activation-difference baseline also fails the random-null specificity gate, strengthening the case that the verifier/objective, not only the direction-construction method, is the current bottleneck.
- Retractions or supersessions: supersede "CAA may rescue this verifier" with "CAA is a useful baseline but fails the same independent-control gate."

Next move: create a non-logprob generation or learned behavior-readout gate for semantic specificity.

## Activation Geometry Probe: Generation-Match Random Null Gate

Question: does a non-logprob short-generation verifier preserve semantically
specific behavior effects from alias-trained directions?

Current regime:

- Artifact types: alias-indexed behavior-direction manifests, CAA-style
  direction vectors, random-relation null pair sets, generated-text examples,
  target-match generation gates.
- Operations: full-label alias-gradient construction, CAA activation
  differencing, greedy continuation with steering hooks, normalized phrase
  matching over canonical and alias labels.
- Gates/verifiers: positives must generate target labels; random relation nulls
  must not; source-label suppression alone is not a pass.
- Known limitations: one small model, one seed, greedy 8-token continuation,
  exact phrase matcher rather than learned semantic evaluator.

Action class:

- Retrieval/search/discovery: verifier transition with a rejected candidate.
- Why: this adds a non-logprob behavior verifier and changes what counts as an
  accepted behavioral artifact.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/generation_match_random_nulls_2026_06_09.md`;
  local ignored payloads under
  `artifacts/activation_geometry/modal_pythia_70m_generation_match_random_nulls_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: ten seeded random relation null controls.
- Stress tests: `source_passage` and `latent_choice`; target-gradient, CAA, and
  random same-norm directions.

Gate:

- Acceptance rule: continue toward paper-level semantic specificity only if
  steered generations actually match held-out target labels for positives more
  often than for random-null controls.
- Withheld/rejected rule: withhold behavioral semantic steering if target hits
  are zero or if gains come from source/distractor suppression.

Results:

- Accepted artifacts: generation-match scoring surface; generation example
  renderer; target-match-only robust-pass gate.
- Rejected or withheld artifacts: current target-gradient and CAA directions as
  behavior-level semantic steering mechanisms.
- Key metrics: strict target-positive passes are `0/7` for target-gradient, CAA,
  and random directions in both prompt frames; random-null passes are `0/10`.
- Variance or ablation: source-passage has two source-suppression rows but no
  target hits; latent-choice has no target hits and generic repeated
  continuations.

Residual content:

- Explained by old regime: label-logprob movement does not imply generated
  target behavior.
- New content outside old regime: a stricter verifier reveals source-suppression
  artifacts that margin scoring alone would overcount.
- Retractions or supersessions: supersede "nonzero generation margin delta may
  indicate behavior" with "generation behavior requires an explicit steered
  target-label match under this verifier."

Next move: build a learned behavior-readout gate or redesign the short-answer
generation interface before running larger models.

## Activation Geometry Probe: Generation-Readout Random Null Gate

Question: can a learned hidden-state readout recover semantic target behavior
from generated continuations where exact generation matching fails?

Current regime:

- Artifact types: generation-match payloads, generation-readout payloads,
  train-alias role centroids, generated-text example tables, random-null
  specificity reports.
- Operations: full-label alias-gradient construction, CAA activation
  differencing, greedy generation with steering hooks, hidden-state centroid
  scoring of generated continuations.
- Gates/verifiers: positives must improve target margin, increase target score,
  and be classified as target by the steered readout; controls must remain below
  positives.
- Known limitations: one small model, one seed, greedy generation, simple
  centroid readout rather than a cross-validated classifier.

Action class:

- Retrieval/search/discovery: verifier transition with a rejected candidate.
- Why: this adds a learned non-logprob behavior readout and tests whether exact
  label matching was too brittle.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/generation_readout_random_nulls_2026_06_09.md`;
  local ignored payloads under
  `artifacts/activation_geometry/modal_pythia_70m_generation_readout_random_nulls_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: ten seeded random relation null controls.
- Stress tests: `source_passage` and `latent_choice`; target-gradient, CAA, and
  random same-norm directions.

Gate:

- Acceptance rule: continue toward paper-level semantic specificity only if
  steered positive continuations are read out as target more often than random
  null controls.
- Withheld/rejected rule: reject if target hits are zero or if gains occur while
  the readout's best role remains source/distractor.

Results:

- Accepted artifacts: generation-readout scoring surface and strict
  best-target readout gate.
- Rejected or withheld artifacts: current target-gradient and CAA directions as
  hidden-readout behavior mechanisms over generated continuations.
- Key metrics: strict positive passes are `0/7` in both prompt frames for all
  tested directions; random-null passes are `0/10`.
- Variance or ablation: source-passage has one tiny CAA target-score increase,
  but the best role remains source; latent-choice is fully unchanged.

Residual content:

- Explained by old regime: label-score movement can fail to transport into
  generated behavior.
- New content outside old regime: exact-match and learned-readout non-logprob
  gates agree on the negative result.
- Retractions or supersessions: supersede "a learned readout may recover hidden
  target behavior from generated text" with "this readout does not recover
  target behavior from the current generations."

Next move: redesign the behavior interface before scaling models.

## Activation Geometry Probe: Short-Answer Behavior Gate

Question: does a constrained short-answer interface reveal target behavior that
open-ended generation gates miss?

Current regime:

- Artifact types: generation-match payloads, generation-readout payloads,
  prompt-frame manifests, random-null specificity reports, generated-text
  examples.
- Operations: full-label alias-gradient construction, CAA activation
  differencing, short-answer greedy generation with steering hooks, exact target
  phrase matching, learned continuation readout scoring.
- Gates/verifiers: positives must produce target matches or target-readout
  classifications more often than random relation null controls.
- Known limitations: one small model, one seed, greedy short continuation, no
  larger-model replication because the small non-logprob gate is zero.

Action class:

- Retrieval/search/discovery: verifier search with a rejected interface.
- Why: this changes the prompting interface inside the existing non-logprob
  behavior-verifier schema and tests whether the negative result was caused by
  prompt openness.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/short_answer_behavior_gate_2026_06_09.md`;
  local ignored payloads under
  `artifacts/activation_geometry/modal_pythia_70m_short_answer_*_random_nulls_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: ten seeded random relation null controls.
- Stress tests: source-conditioned and source-free short-answer frames;
  exact-match and learned-readout behavior surfaces; target-gradient, CAA, and
  random same-norm directions.

Gate:

- Acceptance rule: continue toward paper-level semantic specificity only if
  short-answer target behavior is nonzero for positives and exceeds random-null
  controls.
- Withheld/rejected rule: reject if target-positive passes are zero or if
  nonzero deltas come from source suppression, generic completions, or unchanged
  readout roles.

Results:

- Accepted artifacts: `source_short_answer` and `latent_short_answer` prompt
  frames.
- Rejected or withheld artifacts: the short-answer interface as a rescue for
  current target-gradient and CAA directions.
- Key metrics: all four surface/prompt combinations show `0/7` target-positive
  passes and `0/10` random-null passes for target-gradient, CAA, and random
  directions.
- Variance or ablation: source-conditioned prompts repeat source text; latent
  prompts collapse to generic text; learned readout agrees with exact matching.

Residual content:

- Explained by old regime: label-score steering does not automatically
  transport into generated target behavior.
- New content outside old regime: the short-answer interface is not sufficient
  to bridge teacher-forced label movement and behavior.
- Retractions or supersessions: supersede "short-answer prompting may recover
  the target behavior" with "current directions remain behavior-inactive under
  short-answer generation."

Next move: build a direct behavior-classification/intervention gate before
adding model scale.

## Activation Geometry Probe: Binary-Relation Behavior Gate

Question: can a direct yes/no relation-classification interface reveal behavior
that generation and short-answer gates miss?

Current regime:

- Artifact types: binary-relation payloads, random-null specificity reports,
  yes/no continuation-margin tables, direction-alignment diagnostics.
- Operations: train-alias binary yes/no gradient construction, held-out-alias
  binary relation scoring, random-null control comparison, CAA/random baselines.
- Gates/verifiers: positives must increase target Yes-No margin and become
  target-positive more often than random relation nulls.
- Known limitations: one small model, one seed, one layer, one scale, no
  explicit yes-bias controls yet.

Action class:

- Retrieval/search/discovery: verifier transition with residual content.
- Why: this adds a new behavior artifact class that is neither label generation
  nor visible option-token choice, and it produces the first nonzero behavior
  target passes after the stricter generation gates failed.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/binary_relation_behavior_gate_2026_06_09.md`;
  local ignored payload
  `artifacts/activation_geometry/modal_pythia_70m_binary_relation_random_nulls_source_seed20260609.json`.
- Positive targets: expanded steering pairs.
- Negative controls: ten seeded random relation null controls.
- Stress tests: target-gradient, CAA, and random same-norm directions under
  held-out `alias_2`.

Gate:

- Acceptance rule: continue toward paper-level semantic specificity only if
  positives beat random-null controls and the effect cannot be explained by a
  broad Yes-bias direction.
- Withheld/rejected rule: withhold semantic-specific claims if controls pass or
  target/source/distractor gradients are too collinear to separate.

Results:

- Accepted artifacts: `binary_relation` scoring surface and direct yes/no
  behavior gate.
- Rejected or withheld artifacts: binary relation result as a final semantic
  specificity claim.
- Key metrics: `target_learned` passes `4/7` positives and `3/10` random nulls;
  CAA and random pass `0/7` positives and `0/10` random nulls.
- Variance or ablation: role-gradient cosines are very high, suggesting broad
  candidate affirmation as a confound.

Residual content:

- Explained by old regime: full-label directions can move text-conditioned
  label surfaces.
- New content outside old regime: direct yes/no relation behavior is
  intervention-sensitive even when generation behavior is zero.
- Retractions or supersessions: supersede "all behavior gates are zero" with
  "generation behavior is zero, but direct binary relation behavior has a
  nonzero, confounded signal."

Next move: separate relation movement from yes-bias with explicit binary
controls before scaling.

## Activation Geometry Probe: Binary Yes-Bias Controls

Question: is the nonzero binary-relation behavior signal relation-specific, or
is it broad Yes-bias?

Current regime:

- Artifact types: binary-relation payloads, candidate-control margins,
  carrier-control margins, random-null specificity reports.
- Operations: held-out binary relation scoring, extra control-candidate scoring,
  always-true/false carrier scoring, target/source/distractor role-margin
  comparison.
- Gates/verifiers: target movement must exceed blank/generic/shuffled/source/
  distractor/false-carrier movement before semantic specificity can be claimed.
- Known limitations: one model, one seed, one layer, one scale; controls are
  diagnostic only and not yet part of robust-pass aggregation.

Action class:

- Retrieval/search/discovery: verifier hardening with a rejected candidate.
- Why: this adds the missing control artifact type needed to distinguish
  relation behavior from answer-polarity behavior.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/binary_yes_bias_controls_2026_06_09.md`;
  local ignored payload
  `artifacts/activation_geometry/modal_pythia_70m_binary_yes_bias_controls_seed20260609.json`.
- Positive targets: expanded steering pairs.
- Negative controls: ten random relation null pairs plus candidate/carrier
  yes-bias controls.
- Stress tests: blank, generic, source, distractor, shuffled-target,
  always-true, and always-false controls under `target_learned`.

Gate:

- Acceptance rule: semantic-specific binary steering requires target movement
  larger than yes-bias controls, with controls not ending broadly positive.
- Withheld/rejected rule: reject the candidate mechanism if yes-bias controls
  move with the target.

Results:

- Accepted artifacts: yes-bias control fields inside binary-relation payloads.
- Rejected or withheld artifacts: the current `target_learned` binary direction
  as relation-specific steering.
- Key metrics: all target/source/distractor/control/carrier Yes-No margins end
  positive in `17/17` target-learned rows.
- Variance or ablation: positives and random nulls show the same broad pattern.

Residual content:

- Explained by old regime: behavior can move on a direct binary surface.
- New content outside old regime: the movement is mainly answer-polarity
  control, not relation-specific transport.
- Retractions or supersessions: supersede "binary relation gives a promising
  semantic pocket" with "binary relation gives a useful behavior surface whose
  first direction is dominated by Yes-bias."

Next move: build contrastive binary directions and make yes-bias controls part
of the acceptance rule.

## Activation Geometry Probe: Contrastive Binary Specificity

Question: can a contrastive binary objective subtract yes-bias while preserving
relation-specific target movement?

Current regime:

- Artifact types: binary-relation payloads, yes-bias control margins,
  contrastive binary direction modes, strict binary-specificity aggregates,
  binary gradient geometry summaries.
- Operations: target Yes-No gradient construction, binary control-gradient
  construction, norm-matched multi-control subtraction, held-out alias binary
  scoring.
- Gates/verifiers: target movement must beat blank/generic/source/distractor/
  shuffled-target/always-false controls and must not make the always-false
  carrier positive.
- Known limitations: one model, one seed, one layer; low-rank diagnosis is
  binary-surface-specific and does not contradict earlier full-label alias
  leakage diagnostics.

Action class:

- Retrieval/search/discovery: verifier hardening plus rejected intervention
  family.
- Why: this upgrades yes-bias controls from post-hoc diagnosis to an acceptance
  rule and tests whether simple linear contrastive subtraction can recover a
  semantic direction.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/contrastive_binary_specificity_2026_06_09.md`;
  local ignored artifact
  `artifacts/activation_geometry/modal_pythia_70m_binary_contrastive_specificity_seed20260609.json`.
- Positive targets: expanded random-null pair set positives.
- Negative controls: ten random relation nulls plus per-row yes-bias controls.
- Stress tests: control-subtraction weights `0.5`, `1.0`, `2.0`, `4.0`.

Gate:

- Acceptance rule: promote only rows that clear the strict binary-specificity
  rule.
- Withheld/rejected rule: reject directions that keep loose target movement but
  fail yes-bias controls, or suppress controls only by also suppressing target.

Results:

- Accepted artifacts: strict binary-specificity gate and contrastive direction
  modes.
- Rejected or withheld artifacts: `target_learned` and all tested
  `target_binary_controls_*` directions as semantic-specific steering.
- Key metrics: strict passes are `0/7` positives and `0/10` controls for every
  tested direction. Target + control gradients have first-PC energy `0.895`,
  with first three PCs explaining `0.930` of normalized-gradient energy.
- Variance or ablation: weight `0.5` keeps loose target behavior but leaves
  controls active; weight `1.0+` suppresses controls by collapsing or reversing
  target movement.

Residual content:

- Explained by old regime: the loose binary surface is answer-polarity
  steerable.
- New content outside old regime: yes-bias-aware acceptance rejects the apparent
  binary pocket; the binary gradient field is low-rank, but simple contrastive
  subtraction cannot separate target relation movement from control movement.
- Retractions or supersessions: supersede "build contrastive binary directions
  next" with "contrastive binary subtraction tested; next need spectrum/low-rank
  diagnosis or a different nonlinear/feature-guided intervention."

Next move completed in
`experiments/activation_geometry/results/binary_pc_residualization_2026_06_10.md`:
top-PC residualization/whitening rejects the binary surface as a linear steering
route for Pythia-70M layer 5.

## Activation Geometry Probe: Binary PC Residualization

Question: is the binary yes/no leakage low-rank enough that removing or
whitening the dominant control PCs reveals relation-specific target movement?

Current regime:

- Artifact types: binary-relation payloads, strict specificity aggregates,
  binary control-PC bases, PC-residualized and PC-whitened direction modes.
- Operations: uncentered SVD over normalized binary control gradients,
  top-PC removal, top-PC damping, target-norm restoration, held-out alias
  scoring.
- Gates/verifiers: strict binary-specificity gate plus loose/basic behavior
  retention.
- Known limitations: one model, one seed, one layer; this probes linear
  directions, not nonlinear feature interventions.

Action class:

- Retrieval/search/discovery: mechanistic falsification of the low-rank rescue
  hypothesis.
- Why: this directly tests the previous residual content: whether the dominant
  low-rank binary axis is separable nuisance structure or the same axis that
  carries target movement.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/binary_pc_residualization_2026_06_10.md`;
  local ignored artifact
  `artifacts/activation_geometry/modal_pythia_70m_binary_pc_residualization_seed20260610.json`.
- Positive targets: seven expanded random-null positives.
- Negative controls: ten random relation nulls plus row-level yes-bias controls.
- Stress tests: remove or whiten top `1` and top `3` binary-control PCs.

Gate:

- Acceptance rule: a PC-adjusted direction must retain loose positive behavior
  and pass the strict yes-bias-aware gate on positives without reviving random
  null controls.
- Withheld/rejected rule: reject directions that suppress controls by
  suppressing target behavior, or keep loose behavior while failing strict
  control dominance.

Results:

- Accepted artifacts: PC-adjusted direction modes and control-PC diagnostics.
- Rejected or withheld artifacts: PC residualization/whitening as a semantic
  steering route for this model/layer.
- Key metrics: all PC modes have `0/7` strict positives. PC1 residualization
  has `0/7` loose positives; PC1/PC3 whitening keep `5/7` loose positives but
  still have negative mean target-over-control margins. Target gradients have
  mean cosine `0.962` with control PC1 on positives and `0.954` on random-null
  controls.
- Variance or ablation: removing PC1 is enough to erase loose target behavior;
  adding PCs does not restore specificity.

Residual content:

- Explained by old regime: binary yes/no movement is low-rank and steerable.
- New content outside old regime: the dominant low-rank control axis is also
  the dominant target movement axis, so linear PC cleanup does not expose a
  hidden semantic relation direction.
- Retractions or supersessions: supersede "try projection/whitening before
  giving up on binary steering" with "binary surface is verifier-only for
  Pythia-70M layer 5 unless a nonlinear or feature-guided intervention changes
  the mechanism."

Next move: stop optimizing this binary surface on Pythia-70M layer 5 as a
linear steering route. For paper-worthiness, either replicate the negative
mechanism on another model/layer or pivot to a nonlinear/feature-guided
intervention that is explicitly evaluated by the same strict binary verifier.

## Activation Geometry Probe: Binary Layer-3 Replication

Question: does the binary low-rank entanglement diagnosis replicate across
layers, or does an earlier layer expose a controlled semantic pocket?

Current regime:

- Artifact types: layer-specific binary-relation payloads, strict specificity
  aggregates, control-PC geometry summaries, strict-pocket pair lists.
- Operations: run the same PC residualization/whitening verifier at another
  transformer block output.
- Gates/verifiers: strict binary-specificity gate, loose behavior retention,
  random-null control suppression.
- Known limitations: same model and same seed; GPT-2 replication was attempted
  but produced no artifact before being stopped, so it is not evidence.

Action class:

- Retrieval/search/discovery: layer replication plus small residual pocket.
- Why: this tests whether the low-rank binary explanation is layer-specific and
  identifies a concrete pair-level pocket for follow-up.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/binary_layer3_replication_2026_06_10.md`;
  local ignored artifact
  `artifacts/activation_geometry/modal_pythia_70m_layer3_binary_pc_residualization_seed20260610.json`.
- Positive targets: seven expanded random-null positives.
- Negative controls: ten random relation nulls plus row-level yes-bias controls.
- Stress tests: compare raw target, control-mean subtraction, PC residualization,
  PC whitening, and random directions at layer 3.

Gate:

- Acceptance rule: require enough strict positives to plausibly satisfy Phase 1
  after scale/layer replication, with `0/10` strict random-null controls.
- Withheld/rejected rule: do not claim success from isolated pair pockets or
  positive means when the strict gate remains sparse.

Results:

- Accepted artifacts: layer-3 replication report and strict-pocket pair list.
- Rejected or withheld artifacts: layer 3 as a completed paper-ready semantic
  steering result.
- Key metrics: `target_binary_pc1_whiten` gives `2/7` strict positives and
  `0/10` strict controls; `target_binary_pc3_whiten` gives `1/7` strict
  positives and `0/10` strict controls.
- Variance or ablation: whitening outperforms residualization; residualization
  still kills loose positives.

Residual content:

- Explained by old regime: binary yes/no gradients remain low-rank and aligned
  with answer-polarity controls.
- New content outside old regime: layer 3 has a small controlled whitening
  pocket absent at layer 5.
- Retractions or supersessions: supersede "binary surface is only verifier-only
  everywhere" with the narrower "layer 5 is verifier-only; layer 3 has a weak
  strict pocket that needs scale/layer stress before it can matter."

Next move: run a focused layer/scale sweep around layer 3 PC whitening, or
replicate this exact pocket on a second model. A paper claim still needs a
stable result across seeds, layers, or models.

## Activation Geometry Probe: Binary Layer-3 Scale Sweep

Question: can scale calibration expand the layer-3 PC1-whitening pocket without
reviving random-null controls?

Current regime:

- Artifact types: scale-specific binary-relation payloads, strict pair curves,
  geometry summaries, rejected scale frontier.
- Operations: sweep intervention scale for the best layer-3 PC-whitened mode.
- Gates/verifiers: strict binary-specificity pass counts for positives and
  random-null controls.
- Known limitations: same model, same seed, same layer; no second-model
  evidence yet.

Action class:

- Retrieval/search/discovery: scale-frontier search inside an already discovered
  weak pocket.
- Why: this tests whether the layer-3 pocket can be made broad enough for the
  Phase 1 paper gate by calibration alone.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/binary_layer3_scale_sweep_2026_06_10.md`;
  local ignored artifact
  `artifacts/activation_geometry/modal_pythia_70m_layer3_pc1_whiten_scale_sweep_seed20260610.json`.
- Positive targets: seven expanded random-null positives.
- Negative controls: ten random relation nulls plus row-level yes-bias controls.
- Stress tests: scales `0.5`, `0.75`, `1.0`, `1.25`, and `1.5`.

Gate:

- Acceptance rule: broaden strict positive passes while preserving `0/10`
  strict random-null controls.
- Withheld/rejected rule: reject scale settings that gain positives only by
  admitting random-null controls.

Results:

- Accepted artifacts: scale frontier and strict pair curve.
- Rejected or withheld artifacts: scale tuning alone as a completed semantic
  specificity solution.
- Key metrics: best clean scale is `1.0` with `2/7` strict positives and `0/10`
  controls. Scale `1.25` reaches `3/7` positives but admits `1/10` controls.
- Variance or ablation: random same-norm remains `0/7` positives and `0/10`
  controls at every scale.

Residual content:

- Explained by old regime: the layer-3 pocket is weak and pair-specific.
- New content outside old regime: `attractor->attractor_network` and
  `fixed_point->prototype` are stable controlled positives around scale `1.0`;
  `basin_of_attraction->schema` appears only when controls begin to leak.
- Retractions or supersessions: supersede "scale sweep may make layer 3
  paper-ready" with "scale sweep maps a real but too-small specificity
  frontier."

Next move: either replicate the two stable layer-3 strict positives across a
second seed/model, or pivot to a pair-focused/nonlinear intervention. A broad
paper claim still needs more than a two-pair pocket.

## Activation Geometry Checkpoint: Second-Model Pocket Replication Handoff

Question: what must be preserved before pausing so the next session can resume
the second-model replication without turning an interrupted run into evidence?

Current regime:

- Artifact types: strict binary-relation reports, focused pair sets, random-null
  controls, failed-run notes, next-command handoffs.
- Operations: pair-set narrowing, Modal replication, strict aggregate analysis,
  discovery-ledger checkpointing.
- Gates/verifiers: strict positive pass count, `0/10` random-null controls,
  comparison to random same-norm, and artifact existence.
- Known limitations: the Pythia-160M run has not completed; the Pythia-70M
  pocket remains only a two-pair signal.

Action class:

- Retrieval/search/discovery: checkpointed search.
- Why: this adds a smaller pair-set operation and preserves an interrupted
  attempted replication, but it does not create a new accepted empirical result.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/nightly_checkpoint_2026_06_10.md`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: ten random relation nulls, including the hard
  `valence->steering_vector` leakage row.
- Stress tests: next run should compare `target_binary_pc1_whiten` against
  `random_same_norm` on Pythia-160M layer 3.

Gate:

- Acceptance rule: the focused Pythia-160M run must preserve both strict
  positives, or at least clearly beat `random_same_norm`, with `0/10` strict
  random-null controls.
- Withheld/rejected rule: if no artifact is produced, the run remains
  non-evidence; if controls revive, treat the result as a specificity failure.

Results:

- Accepted artifacts: `layer3_strict_pocket_random_nulls` pair set and the
  nightly checkpoint report.
- Rejected or withheld artifacts: the interrupted full-pair Pythia-160M Modal
  attempt; no JSON artifact was produced.
- Key metrics: no new experimental metrics.
- Variance or ablation: none yet.

Residual content:

- Explained by old regime: pair narrowing is a search operation inside the
  existing strict binary-verifier regime.
- New content outside old regime: none yet.
- Retractions or supersessions: none; the scale-sweep conclusion still stands.

Next move: run the focused Pythia-160M layer-3 pocket replication, then either
record a second-model pocket report or pivot to a nonlinear/feature-guided
intervention if the pocket disappears.

## Activation Geometry Probe: Pythia-160M Pocket Replication

Question: does the two-pair Pythia-70M layer-3 strict binary-relation pocket
survive in a larger open model?

Current regime:

- Artifact types: focused pair-set payloads, strict binary-relation aggregates,
  random-null control tables, binary gradient geometry summaries, Modal Volume
  raw-payload artifacts.
- Operations: PC1-whitened linear steering, random same-norm baseline, focused
  scale sweep, durable spawned Modal execution with remote volume writes.
- Gates/verifiers: strict positive pass counts, `0/10` strict random-null
  controls, target movement over strongest yes-bias control, low-rank binary
  gradient diagnostics.
- Known limitations: only layer 3 was tested in Pythia-160M; no nonlinear or
  feature-guided intervention has been evaluated yet.

Action class:

- Retrieval/search/discovery: search plus falsification.
- Why: this tests whether an existing pocket transports to a second model; it
  does not add a new accepted semantic steering mechanism.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/binary_pythia160_pocket_replication_2026_06_10.md`;
  local ignored artifacts
  `artifacts/activation_geometry/modal_pythia_160m_layer3_pocket_replication_seed20260610.json`
  and
  `artifacts/activation_geometry/modal_pythia_160m_layer3_pocket_scale_sweep_seed20260610.json`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: ten random relation nulls, including
  `valence->steering_vector`.
- Stress tests: scale `1.0` replication plus focused scale sweep over `0.5`,
  `0.75`, `1.0`, `1.25`, and `1.5`.

Gate:

- Acceptance rule: preserve the two focused strict positives, or clearly beat
  `random_same_norm`, while keeping strict random-null controls at `0/10`.
- Withheld/rejected rule: reject apparent target movement when it fails to beat
  the strongest yes-bias controls.

Results:

- Accepted artifacts: durable Modal Volume runner support and Pythia-160M
  negative replication report.
- Rejected or withheld artifacts: the Pythia-70M layer-3 two-pair pocket as a
  robust cross-model semantic steering result.
- Key metrics: `target_binary_pc1_whiten` gives `0/2` strict positives and
  `0/10` controls at every tested scale from `0.5` to `1.5`; `random_same_norm`
  also gives `0/2` positives and `0/10` controls. Pythia-160M binary gradients
  remain low-rank: target PC1 energy `0.877`, target-plus-control PC1 energy
  `0.715`, always-false PC1 energy `0.913`.
- Variance or ablation: five-scale stress test rules out simple scale mismatch.

Residual content:

- Explained by old regime: the binary relation interface remains dominated by
  answer-polarity or carrier-confirmation geometry.
- New content outside old regime: none accepted; the attempted cross-model
  pocket collapses under the strict verifier.
- Retractions or supersessions: supersede "replicate the two stable layer-3
  strict positives across a second model" with "second-model replication fails;
  pivot away from bigger linear PC-whitening repeats."

Next move: keep the strict binary verifier, but change intervention class:
pair-focused nonlinear optimization, feature-guided steering, or another method
that is not merely a linear direction in the low-rank binary carrier subspace.

## Activation Geometry Probe: Pair-Optimized Binary Direction

Question: can a pair-optimized activation vector recover semantic-specific
binary behavior after PC-whitened linear directions failed to replicate?

Current regime:

- Artifact types: strict binary-relation rows, optimized direction summaries,
  random-null control sets, smoke gates, aggregate frontier tables.
- Operations: batched differentiable Yes/No scoring, pair-specific activation
  vector optimization, norm matching against the target binary-gradient
  direction.
- Gates/verifiers: held-out alias `alias_2`, strict binary specificity,
  always-false carrier rejection, random same-norm and PC1-whitened baselines.
- Known limitations: current optimized vectors are slow; the full two-variant,
  two-alias robustness run was not attempted after the alias0 random-null gate
  failed.

Action class:

- Retrieval/search/discovery: search with a new operation.
- Why: this adds a behavior-optimized intervention operation but does not yet
  produce an accepted semantic-specific mechanism.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/binary_pair_optimized_intervention_2026_06_10.md`;
  local ignored artifacts
  `artifacts/activation_geometry/modal_pythia_70m_layer3_strict_opt8_cw2_smoke_seed20260610.json`,
  `artifacts/activation_geometry/modal_pythia_70m_layer3_strict_opt8_fullnull_alias0_seed20260610.json`,
  and
  `artifacts/activation_geometry/modal_pythia_70m_layer3_strict_opt16_fullnull_alias0_seed20260610.json`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: hard smoke control `valence->steering_vector`; full pilot
  controls are the ten random relation nulls.
- Stress tests: opt8 vs opt16 depth comparison; PC1-whitened and random
  baselines.

Gate:

- Acceptance rule: `2/2` strict positives and `0/10` strict random-null controls
  on held-out alias scoring.
- Withheld/rejected rule: reject rows that only pass by also raising the
  strongest control or always-false carrier.

Results:

- Accepted artifacts: implementation of `target_binary_strict_opt_8` and
  `target_binary_strict_opt_16`; smoke-gate pass for
  `attractor->attractor_network` with hard control rejected.
- Rejected or withheld artifacts: pair-optimized single-vector steering as a
  paper-ready semantic specificity mechanism.
- Key metrics: smoke gate `1/1` positives and `0/1` controls for opt8. Full
  alias0 random-null pilot: opt8 `1/2` positives and `1/10` controls; opt16
  `1/2` positives and `1/10` controls; PC1-whiten `0/2` positives and `1/10`
  controls; random same-norm `0/2` positives and `0/10` controls.
- Variance or ablation: opt16 increases target movement on
  `attractor->attractor_network` but does not recover `fixed_point->prototype`
  or remove random-null leakage.

Residual content:

- Explained by old regime: binary Yes/No behavior remains vulnerable to
  non-semantic carrier and relation-plausibility leakage.
- New content outside old regime: direct pair optimization can recover a
  held-out positive that PC1-whitening misses under the same verifier.
- Retractions or supersessions: supersede "change intervention class may be
  enough" with "single-vector behavior optimization improves target movement
  but still needs better control strata or a genuinely nonlinear/feature-guided
  mechanism."

Next move: stratify controls by semantic plausibility, source overlap, and
target overlap before interpreting random-null failures as either leaks or bad
negatives.

## Activation Geometry Probe: Stratified Binary Control Gate

Question: are pair-optimized strict-binary leaks concentrated in semantically
near-null controls, or do they also arise from source and target overlap?

Current regime:

- Artifact types: strict binary-relation rows, control-class metadata,
  per-class gate summaries, pair-optimized direction summaries.
- Operations: layer-3 strict-pocket pair sets, source-sharing/target-sharing/
  implausible/near-null control strata, Modal strict-binary scoring.
- Gates/verifiers: held-out alias `alias_2`, always-false carrier rejection,
  per-class robust pass counts, random same-norm baseline.
- Known limitations: one seed, one model, one objective alias, and opt8 only.

Action class:

- Retrieval/search/discovery: discovery of a stronger verifier artifact type.
- Why: this adds a new control taxonomy and summary surface that the previous
  pooled random-null regime could not represent.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/stratified_binary_control_gate_2026_06_10.md`;
  local ignored artifact
  `artifacts/activation_geometry/modal_pythia_70m_layer3_strict_opt8_stratified_alias0_seed20260610.json`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: three controls each in `source_sharing`,
  `target_sharing`, `implausible_random_null`, and `semantic_near_null`.
- Stress tests: `target_binary_strict_opt_8` against PC1-whitened and random
  same-norm baselines.

Gate:

- Acceptance rule: preserve positive movement while keeping implausible controls
  clean and identifying which structured strata leak.
- Withheld/rejected rule: reject pooled control claims that do not report
  control stratum.

Results:

- Accepted artifacts: stratified pair sets and per-class gate summary fields.
- Rejected or withheld artifacts: the hypothesis that pair-optimized leakage is
  only caused by semantically near-null random controls.
- Key metrics: `target_binary_strict_opt_8` gives `1/2` strict positives and
  `4/12` strict controls. The leaks split as `0/3` implausible random nulls,
  `1/3` semantic-near nulls, `2/3` source-sharing controls, and `1/3`
  target-sharing controls. `random_same_norm` stays at `0/2` positives and
  `0/12` controls.
- Variance or ablation: PC1-whitening also leaks structured controls
  (`4/12`) while preserving no positives.

Residual content:

- Explained by old regime: arbitrary unrelated controls are rejected, so the
  verifier is not merely a universal Yes-bias detector.
- New content outside old regime: leakage is structured by source/target
  overlap as well as semantic plausibility.
- Retractions or supersessions: supersede "just stratify bad random nulls" with
  "single-vector interventions fail on multiple structured control channels."

Next move: build a pair-conditioned nonlinear or feature/readout-guided
intervention and use the stratified control gate as its acceptance surface.

## Activation Geometry Probe: Positive-Family Binary Direction

Question: can one shared direction learned from positive bridge pairs suppress
stratified controls while preserving strict binary target movement?

Current regime:

- Artifact types: strict binary-relation rows, stratified gate summaries,
  positive-family optimized direction summaries, scale frontiers.
- Operations: one shared final-token vector optimized on positive target prompts
  against stratified control relation prompts and positive-carrier controls.
- Gates/verifiers: held-out alias `alias_2`, per-class strict control counts,
  always-false carrier rejection, random same-norm and pair-specific opt8
  baselines.
- Known limitations: Pythia-70M only, layer 3 only, one objective alias, one
  train variant, two positive pairs.

Action class:

- Retrieval/search/discovery: discovery candidate.
- Why: this creates the first accepted specificity frontier where a learned
  activation direction keeps a strict positive while suppressing all stratified
  controls under the hardened binary verifier.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/positive_family_binary_direction_2026_06_10.md`;
  local ignored artifacts
  `artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_alias0_seed20260610.json`
  and
  `artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_scale_seed20260610.json`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: twelve controls split evenly across `source_sharing`,
  `target_sharing`, `implausible_random_null`, and `semantic_near_null`.
- Stress tests: pair-specific opt8 baseline, random same-norm baseline, and
  scale sweep over `0.5`, `0.75`, `1.0`, `1.25`, `1.5`.

Gate:

- Acceptance rule: improve the specificity frontier over pair-specific opt8 by
  preserving positive movement and reducing structured control passes.
- Withheld/rejected rule: reject any scale whose positive movement depends on
  positive always-false carrier margins or revived structured controls.

Results:

- Accepted artifacts: `target_binary_positive_family_opt_8` mode and a scale
  `1.0` frontier with `1/2` strict positives and `0/12` stratified controls.
- Rejected or withheld artifacts: `2/2` positive semantic steering; scale
  `1.25` because it revives `1/12` target-sharing controls; scale `1.5`
  because the positive fails the always-false carrier check.
- Key metrics: at scale `1.0`, positive-family opt8 improves over pair-specific
  opt8 (`1/2`, `0/12` versus `1/2`, `4/12`). `random_same_norm` remains `0/2`,
  `0/12`. `fixed_point->prototype` fails at every tested scale.
- Variance or ablation: scale stress test identifies a narrow clean band at
  `1.0`; higher scale increases target movement but breaks controls or carrier
  checks.

Residual content:

- Explained by old regime: the binary verifier is still strict enough to reject
  random movement and arbitrary unrelated controls.
- New content outside old regime: semantic-specific movement may be a
  family-level activation feature rather than a pair-specific direction.
- Retractions or supersessions: supersede "single-vector methods are exhausted"
  with "pair-specific vectors fail, but positive-family vectors merit alias and
  model replication."

Next move: replicate the positive-family frontier across objective aliases,
train variants, and a second model/layer before expanding the concept set.

## Activation Geometry Handoff: Positive-Family Replication Gate

Question: what is the pause-safe next action after the positive-family binary
direction produced the cleanest strict frontier so far?

Current regime:

- Artifact types: strict binary-relation rows, stratified gate summaries,
  positive-family optimized direction summaries, scale frontiers, pause-safe
  handoff notes.
- Operations: Modal-backed Pythia activation intervention, objective/eval alias
  perturbation, train-variant perturbation, second-model/layer replication.
- Gates/verifiers: held-out `alias_2`, stratified strict control counts,
  always-false carrier rejection, random same-norm baseline.
- Known limitations: only `1/2` positives currently pass; the result is
  Pythia-70M layer 3 only and may be alias-fragile.

Action class:

- Retrieval/search/discovery: search, with discovery potential.
- Why: the next action perturbs aliases and train variants inside the current
  verifier schema. It becomes discovery-level only if the positive-family
  operation survives those stress tests as a stable artifact class.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/nightly_checkpoint_2026_06_10.md`;
  next recommended report
  `experiments/activation_geometry/results/positive_family_replication_2026_06_10.md`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: twelve controls split across `source_sharing`,
  `target_sharing`, `implausible_random_null`, and `semantic_near_null`.
- Stress tests: objective `alias_1` with held-out `alias_2`; train variant `1`
  with held-out variant `2`; then second model/layer if the first two hold.

Gate:

- Acceptance rule: preserve at least `1/2` strict positives and `0/12`
  stratified controls under alias or train-variant perturbation.
- Withheld/rejected rule: if positive movement vanishes or controls revive,
  record the frontier as fragile and pivot to pair-conditioned nonlinear or
  readout-guided intervention.

Results:

- Accepted artifacts: pause-safe command and gate checkpoint.
- Rejected or withheld artifacts: none in this checkpoint; no new experiment was
  run.
- Key metrics: inherited frontier is `1/2` strict positives and `0/12`
  stratified controls at Pythia-70M layer 3, scale `1.0`, objective `alias_0`,
  eval `alias_2`.
- Variance or ablation: pending alias and train-variant replication.

Residual content:

- Explained by old regime: pair-specific optimized vectors can exploit
  structured source/target overlap channels.
- New content outside old regime: a shared positive-family direction may
  suppress those structured channels while preserving one semantic bridge.
- Retractions or supersessions: do not call the frontier paper-ready until it
  survives alias/train perturbation and at least one broader replication.

Next move: run the `alias_1` objective replication first, then train-variant
`1`, then second model/layer only if the frontier survives.

## Activation Geometry Probe: Positive-Family Robustness

Question: does the positive-family strict-binary frontier survive objective
alias and train-variant perturbations?

Current regime:

- Artifact types: strict binary-relation rows, stratified gate summaries,
  positive-family optimized direction summaries, alias/train perturbation
  reports.
- Operations: Modal-backed Pythia activation intervention, held-out alias
  scoring, train-variant perturbation, random same-norm baseline.
- Gates/verifiers: held-out `alias_2`, strict positive counts, stratified
  control counts, always-false carrier rejection.
- Known limitations: Pythia-70M layer 3 only; two positive pairs only; no new
  intervention class in this run.

Action class:

- Retrieval/search/discovery: search.
- Why: this perturbs aliases and train variants inside the current
  positive-family vector schema; it does not add a new artifact type.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/positive_family_replication_2026_06_10.md`;
  local ignored artifacts
  `artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_alias1_seed20260610.json`
  and
  `artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_trainv1_seed20260610.json`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: twelve controls split across `source_sharing`,
  `target_sharing`, `implausible_random_null`, and `semantic_near_null`.
- Stress tests: objective `alias_1` with held-out `alias_2`; train variant `1`
  with held-out variant `2`.

Gate:

- Acceptance rule: preserve at least `1/2` strict positives and `0/12`
  stratified controls under alias or train-variant perturbation.
- Withheld/rejected rule: reject the frontier if positives vanish or structured
  controls revive.

Results:

- Accepted artifacts: the negative replication report and two ignored Modal
  payloads.
- Rejected or withheld artifacts: the hypothesis that the current
  positive-family single-vector direction is a stable paper nucleus.
- Key metrics: objective `alias_1` gives `0/2` strict positives and `0/12`
  controls. Train variant `1` gives `1/2` strict positives and `1/12`
  controls, with a source-sharing leak on `attractor->semantic_distance`.
  `random_same_norm` remains `0/2`, `0/12` in both runs.
- Variance or ablation: alias perturbation and train-variant perturbation both
  fail the pre-registered robustness gate for different reasons.

Residual content:

- Explained by old regime: the strict binary verifier catches answer-surface and
  structured-overlap leakage.
- New content outside old regime: the `attractor` movement can be made clean in
  one narrow setup, but it is not stable under the smallest alias/train changes.
- Retractions or supersessions: supersede "positive-family vector may be the
  paper nucleus" with "positive-family vector is a useful rejected frontier;
  pivot to pair-conditioned nonlinear or readout-guided interventions."

Next move: keep the stratified strict verifier and change intervention class.
Do not spend the next run on a larger repeat of the same positive-family global
vector unless a new variant changes the gate.

## Activation Geometry Probe: Readout-Span Binary Direction

Question: can a pair-conditioned readout/control-span optimizer reduce
structured leakage while preserving strict binary target movement?

Current regime:

- Artifact types: strict binary-relation rows, stratified gate summaries,
  pair-specific optimized direction summaries, scale frontiers, rejected
  intervention classes.
- Operations: Modal-backed Pythia activation intervention, pair-local basis
  construction, Gram-Schmidt orthogonalization, coefficient optimization,
  held-out alias scoring, random same-norm baseline.
- Gates/verifiers: held-out `alias_2`, strict positive counts, stratified
  control counts, always-false carrier rejection, scale stress.
- Known limitations: Pythia-70M layer 3 only; two positive pairs only; the
  intervention is still linear even though the basis is pair-conditioned.

Action class:

- Retrieval/search/discovery: search.
- Why: this changes the parameterization of the pair-specific optimizer inside
  the current strict binary verifier, but does not add a new verifier or
  accepted behavior class.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/readout_span_binary_direction_2026_06_10.md`;
  local ignored artifacts
  `artifacts/activation_geometry/modal_pythia_70m_layer3_readout_span_opt8_stratified_alias0_seed20260610.json`
  and
  `artifacts/activation_geometry/modal_pythia_70m_layer3_readout_span_opt8_stratified_scale_seed20260610.json`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: twelve controls split across `source_sharing`,
  `target_sharing`, `implausible_random_null`, and `semantic_near_null`.
- Stress tests: free pair-specific opt8 baseline, random same-norm baseline,
  and scale sweep over `0.5`, `0.75`, `1.0`, `1.25`, `1.5`.

Gate:

- Acceptance rule: preserve at least `1/2` strict positives while reducing
  structured controls relative to free pair-specific opt8.
- Withheld/rejected rule: reject the intervention class if positives vanish or
  scale only revives controls.

Results:

- Accepted artifacts: `target_binary_readout_span_opt_8` implementation,
  negative report, and two ignored Modal payloads.
- Rejected or withheld artifacts: the hypothesis that a local linear
  readout/control span is enough to recover semantic-specific behavior.
- Key metrics: at scale `1.0`, readout-span opt8 gives `0/2` strict positives
  and `1/12` controls, versus free opt8 at `1/2` positives and `4/12`
  controls. The scale sweep stays at `0/2` positives across every scale and
  revives controls to `2/12` by scales `1.25` and `1.5`.
- Variance or ablation: scale stress and free-pair/random baselines.

Residual content:

- Explained by old regime: linear activation directions can suppress controls
  by also suppressing target movement.
- New content outside old regime: the surviving leakage is not merely
  source/target sharing at scale `1.0`; semantic-near controls remain the
  easiest false positives for this constrained span.
- Retractions or supersessions: supersede "readout-guided linear span may be
  the next intervention class" with "linear readout/control span is a rejected
  alternative; the next intervention should be nonlinear or feature-selective."

Next move: keep the stratified strict verifier and build a genuinely nonlinear
or feature-selective pair-conditioned intervention. Do not continue with larger
linear span sweeps unless a new basis or gate changes the hypothesis.

## Activation Geometry Probe: Sparse Feature-Mask Binary Direction

Question: can coordinate-sparse feature selection recover strict binary target
movement after the readout/control span suppressed positives?

Current regime:

- Artifact types: strict binary-relation rows, stratified gate summaries,
  feature-mask optimized direction summaries, rejected intervention classes.
- Operations: Modal-backed Pythia activation intervention, pair-local
  target-vs-control coordinate scoring, sparse mask construction, masked
  coefficient-free optimization, held-out alias scoring.
- Gates/verifiers: held-out `alias_2`, strict positive counts, stratified
  control counts, always-false carrier rejection, random same-norm baseline.
- Known limitations: Pythia-70M layer 3 only; two positive pairs only; still an
  additive final-token vector after feature selection.

Action class:

- Retrieval/search/discovery: search.
- Why: this adds a feature-selection operation inside the existing strict
  binary verifier, but does not produce an accepted behavior class.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/feature_mask_binary_direction_2026_06_10.md`;
  local ignored artifact
  `artifacts/activation_geometry/modal_pythia_70m_layer3_feature_mask_opt8_stratified_smoke_seed20260610.json`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: twelve controls split across `source_sharing`,
  `target_sharing`, `implausible_random_null`, and `semantic_near_null`.
- Stress tests: random same-norm baseline; comparison against prior free-pair
  and readout-span reports.

Gate:

- Acceptance rule: recover at least `1/2` strict positives while keeping fewer
  structured controls than free pair-specific opt8.
- Withheld/rejected rule: reject the intervention class if positives vanish or
  sparse coordinates still revive structured controls.

Results:

- Accepted artifacts: `target_binary_feature_mask_opt_8` implementation,
  negative report, and ignored Modal payload.
- Rejected or withheld artifacts: the hypothesis that target/control separation
  is cleanly coordinate-sparse in this layer/surface.
- Key metrics: feature-mask opt8 gives `0/2` strict positives and `2/12`
  controls, leaking `steering_vector->semantic_distance` and
  `attractor->semantic_distance`. The mask keeps `77/512` coordinates; only
  `75/512` coordinates have positive target-minus-control score.
- Variance or ablation: random same-norm remains `0/2`, `0/12`; prior
  readout-span and free-pair results provide the intervention-class comparison.

Residual content:

- Explained by old regime: additive directions can create broad binary-surface
  movement without semantic specificity.
- New content outside old regime: the target/control conflict is not solved by
  sparse coordinate selection; it appears distributed or conditional rather than
  axis- or coordinate-local.
- Retractions or supersessions: supersede "feature-selective additive vector may
  rescue the pocket" with "additive vector variants are substantially pruned."

Next move: keep the strict stratified verifier, but change the intervention
operation to something genuinely conditional or non-additive: a learned
prompt-conditioned gate, a nonlinear behavior readout intervention, or a
feature-circuit causal patch instead of a single final-token vector.

## Activation Geometry Probe: State-Gated Binary Direction

Question: can a genuinely conditional final-token intervention recover the
strict focused binary pocket after additive free vectors, readout/control spans,
and sparse feature masks failed?

Current regime:

- Artifact types: strict binary-relation rows, stratified gate summaries,
  state-gated optimized direction summaries, scale-frontier reports, rejected
  and provisional intervention classes.
- Operations: Modal-backed Pythia activation intervention, pair-local binary
  objective optimization, residualized hidden-state gate construction, sigmoid
  attenuation at intervention time, held-out alias scoring.
- Gates/verifiers: held-out `alias_2`, strict positive counts, stratified
  control counts, always-false carrier rejection, random same-norm baseline,
  scale stress, gate-calibration audit.
- Known limitations: Pythia-70M layer 3 only; two positive pairs only; the gate
  is hand-calibrated from training prompts and not yet a clean target/control
  separator.

Action class:

- Retrieval/search/discovery: discovery-leaning search.
- Why: this changes the intervention operation from unconditional additive
  vectors to hidden-state-conditioned application, but it produces only a narrow
  provisional frontier rather than an accepted behavior class.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/state_gate_binary_direction_2026_06_10.md`;
  local ignored artifacts
  `artifacts/activation_geometry/modal_pythia_70m_layer3_state_gate_opt8_stratified_seed20260610.json`
  and
  `artifacts/activation_geometry/modal_pythia_70m_layer3_state_gate_opt8_stratified_scale_seed20260610.json`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: twelve controls split across `source_sharing`,
  `target_sharing`, `implausible_random_null`, and `semantic_near_null`.
- Stress tests: random same-norm baseline and scale sweep over `0.5`, `0.75`,
  `1.0`, `1.25`, `1.5`.

Gate:

- Acceptance rule: recover at least `1/2` strict positives and `0/12`
  stratified controls at a clean scale, with random same-norm at `0/2`, `0/12`.
- Withheld/rejected rule: reject a broad mechanism claim if the clean point is
  scale-fragile or if target hidden-state gate scores do not separate from
  control scores.

Results:

- Accepted artifacts: `target_binary_state_gate_opt_8` implementation,
  provisional positive report, and two ignored Modal payloads.
- Rejected or withheld artifacts: the stronger hypothesis that the current gate
  is a robust hidden-state target/control classifier.
- Key metrics: at scale `1.0`, state-gate opt8 gives `1/2` strict positives
  and `0/12` controls; random same-norm gives `0/2`, `0/12`. The scale sweep
  gives `0/2` positives at `0.5` and `0.75`, revives `3/12` controls at
  `1.25`, and revives `1/12` controls at `1.5`.
- Variance or ablation: scale stress and random same-norm baseline. Gate
  calibration is weak: target-over-max-control gate scores are negative for
  both positive pairs (`-0.0046` and `-0.0114`).

Residual content:

- Explained by old regime: the strict verifier still exposes answer-carrier and
  structured-overlap leakage, and scale tuning alone is not enough.
- New content outside old regime: conditional attenuation can recover the
  narrow clean `attractor` pocket that additive vector variants either lost or
  leaked.
- Retractions or supersessions: supersede "additive variants are the only
  tested operation class" with "a conditional operation can reopen the frontier,
  but the current gate is fragile and not yet a mechanism."

Next move: stress-test the state-gated frontier across objective alias and train
variant, then improve gate calibration if the conditional operation still shows
residual target movement.

## Activation Geometry Probe: State-Gate Robustness

Question: does the state-gated strict-binary frontier survive objective-alias
and train-variant perturbations?

Current regime:

- Artifact types: strict binary-relation rows, stratified gate summaries,
  state-gated optimized direction summaries, alias/train perturbation reports.
- Operations: Modal-backed Pythia activation intervention, held-out alias
  scoring, train-variant perturbation, state-gated final-token deltas, random
  same-norm baseline.
- Gates/verifiers: held-out `alias_2`, strict positive counts, stratified
  control counts, always-false carrier rejection, random same-norm baseline.
- Known limitations: Pythia-70M layer 3 only; two positive pairs only; the gate
  is still hand-calibrated and does not cleanly separate target states from
  controls.

Action class:

- Retrieval/search/discovery: search.
- Why: this perturbs aliases and train prompts inside the current state-gated
  intervention schema.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/state_gate_robustness_2026_06_10.md`;
  local ignored artifacts
  `artifacts/activation_geometry/modal_pythia_70m_layer3_state_gate_opt8_stratified_alias1_seed20260610.json`
  and
  `artifacts/activation_geometry/modal_pythia_70m_layer3_state_gate_opt8_stratified_trainv1_seed20260610.json`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: twelve controls split across `source_sharing`,
  `target_sharing`, `implausible_random_null`, and `semantic_near_null`.
- Stress tests: objective `alias_1` with held-out `alias_2`; train variant `1`
  with held-out variant `2`.

Gate:

- Acceptance rule: preserve at least `1/2` strict positives and `0/12`
  stratified controls under both perturbations, with random same-norm at
  `0/2`, `0/12`.
- Withheld/rejected rule: reject the frontier if positives vanish or structured
  controls revive.

Results:

- Accepted artifacts: the robustness report and two ignored Modal payloads.
- Rejected or withheld artifacts: the hypothesis that the current state-gated
  intervention is robust enough for model/concept expansion.
- Key metrics: objective `alias_1` gives `1/2` strict positives and `0/12`
  controls. Train variant `1` gives `1/2` strict positives and `1/12` controls,
  with the leak in `semantic_near_null` on `steering_vector->semantic_distance`.
  `random_same_norm` remains `0/2`, `0/12` in both runs.
- Variance or ablation: alias perturbation survives; train-variant
  perturbation fails.

Residual content:

- Explained by old regime: the strict verifier still catches structured
  semantic-near leakage even for conditional interventions.
- New content outside old regime: the `attractor` state-gated pocket is more
  alias-stable than the positive-family vector, but not train-variant stable.
- Retractions or supersessions: supersede "state gate might be ready for
  expansion" with "state gate needs a better control-aware gate calibration
  before expansion."

Next move: build a control-aware state gate that explicitly suppresses
semantic-near hidden states, then rerun the same alias/train robustness gate.

## Activation Geometry Probe: Relation-Control State Gate

Question: can relation-level control prompts calibrate the state gate enough to
remove the train-variant semantic-near leak without losing positives?

Current regime:

- Artifact types: strict binary-relation rows, stratified gate summaries,
  relation-control state-gate optimized summaries, scale-frontier reports,
  rejected intervention classes.
- Operations: Modal-backed Pythia activation intervention, relation-level
  control prompt construction from stratified controls, state-gated final-token
  deltas, held-out alias scoring, scale stress.
- Gates/verifiers: held-out `alias_2`, strict positive counts, stratified
  control counts, always-false carrier rejection, random same-norm baseline.
- Known limitations: Pythia-70M layer 3 only; two positive pairs only; still a
  pair-specific additive delta under a gate.

Action class:

- Retrieval/search/discovery: search.
- Why: this adds relation-level control prompts to an existing state-gated
  intervention class, but it does not create an accepted behavior class.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/relation_control_state_gate_2026_06_10.md`;
  local ignored artifacts
  `artifacts/activation_geometry/modal_pythia_70m_layer3_relation_state_gate_opt8_stratified_trainv1_seed20260610.json`
  and
  `artifacts/activation_geometry/modal_pythia_70m_layer3_relation_state_gate_opt8_stratified_trainv1_scale_seed20260610.json`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: twelve controls split across `source_sharing`,
  `target_sharing`, `implausible_random_null`, and `semantic_near_null`.
- Stress tests: direct comparison against the original state gate under train
  variant `1`; scale sweep over `1.0`, `1.25`, `1.5`.

Gate:

- Acceptance rule: recover at least `1/2` strict positives and keep `0/12`
  stratified controls under train variant `1`.
- Withheld/rejected rule: reject the mechanism if positives vanish, or if scale
  recovers positives only by reviving the always-false carrier.

Results:

- Accepted artifacts: `target_binary_relation_state_gate_opt_8` implementation,
  negative report, and two ignored Modal payloads.
- Rejected or withheld artifacts: the hypothesis that relation-control prompts
  are sufficient to calibrate the existing pair-specific state gate.
- Key metrics: the relation-control gate gives `0/2` positives and `0/12`
  controls at scale `1.0`; the original state gate in the same run gives `1/2`
  positives and `1/12` controls. The relation-control scale sweep remains
  `0/2`, `0/12` at scales `1.0`, `1.25`, and `1.5`.
- Variance or ablation: at higher scales, `attractor->attractor_network`
  achieves positive steered-over-control margins, but always-false margins turn
  positive, so strict behavior still fails.

Residual content:

- Explained by old regime: relation-level controls can suppress semantic-near
  leakage by suppressing target movement or carrier safety.
- New content outside old regime: the failure is a three-way tradeoff among
  target movement, semantic-near suppression, and carrier safety.
- Retractions or supersessions: supersede "add relation controls to the state
  gate" with "pair-specific additive/gated variants appear exhausted under this
  strict verifier."

Next move: try a learned multi-class gate or shared conditional operation that
separates target, semantic-near, and carrier-control states as distinct classes,
or pivot away from pair-specific binary optimization.

## Activation Geometry Probe: Multi-Class State Gate

Question: can a target-vs-control prototype gate incorporate relation-level
controls without killing the train-variant `attractor` positive?

Current regime:

- Artifact types: strict binary-relation rows, stratified control summaries,
  optimized gated-intervention summaries, ignored Modal payloads, checkpoint
  reports.
- Operations: Modal-backed Pythia-70M layer-3 intervention, hidden-state
  prototype construction, target-vs-control max-margin gating, held-out alias
  scoring.
- Gates/verifiers: held-out `alias_2`, strict positive/control pass counts,
  always-false carrier, random same-norm baseline.
- Known limitations: two positive pairs only; Pythia-70M layer 3 only; stress
  runs beyond the first train-variant check are recorded in the follow-up
  stress audit below.

Action class:

- Retrieval/search/discovery: discovery.
- Why: this adds a new accepted intervention object, `multiclass_state_gate`,
  that the prior scalar gate could not express, and it changes the
  relation-control tradeoff.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/multiclass_state_gate_2026_06_10.md`;
  local ignored artifact
  `artifacts/activation_geometry/modal_pythia_70m_layer3_multiclass_state_gate_trainv1_seed20260610.json`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: twelve controls split across `source_sharing`,
  `target_sharing`, `implausible_random_null`, and `semantic_near_null`.
- Stress tests: direct comparison against scalar state gate and random baseline
  under train variant `1`.

Gate:

- Acceptance rule: improve over scalar state gate by preserving at least `1/2`
  strict positives while reducing semantic-near leaks to `0/12` controls.
- Withheld/rejected rule: withhold paper-ready claims until alias and scale
  stress finish; the follow-up stress audit below now records the result.

Results:

- Accepted artifacts: `target_binary_multiclass_state_gate_opt_8`,
  `target_binary_relation_multiclass_state_gate_opt_8`, checkpoint report, and
  ignored Modal payload.
- Rejected or withheld artifacts: paper-ready mechanism claim; alias and scale
  stress artifacts were completed in the follow-up stress audit below.
- Key metrics: scalar state gate gives `1/2` positives and `1/12` controls;
  non-relation multi-class gate gives `1/2` positives and `1/12` controls;
  relation multi-class gate gives `1/2` positives and `0/12` controls;
  random gives `0/2` positives and `0/12` controls.
- Variance or ablation: the recovered positive remains
  `attractor->attractor_network`; `fixed_point->prototype` remains absent.

Residual content:

- Explained by old regime: the narrow `attractor` pocket persists across several
  conditional variants.
- New content outside old regime: relation-level controls are not inherently
  lethal; they become usable when represented as hidden-state control
  prototypes inside the gate.
- Retractions or supersessions: supersede "relation controls kill positives"
  with "relation controls kill positives under scalar gates, but not necessarily
  under prototype gates."

Next move: see the scale and alias stress audit below before model, concept, or
generation expansion.

## Activation Geometry Probe: Multi-Class State-Gate Stress

Question: does the relation-level multi-class prototype gate remain a clean
strict-binary semantic-specific intervention under scale and objective-alias
stress?

Current regime:

- Artifact types: strict binary-relation rows, stratified control summaries,
  optimized gated-intervention summaries, ignored Modal payloads, stress reports.
- Operations: Modal-backed Pythia-70M layer-3 intervention, hidden-state
  prototype construction, target-vs-control max-margin gating, held-out alias
  scoring, scale stress, objective-alias perturbation.
- Gates/verifiers: held-out `alias_2`, strict positive/control pass counts,
  always-false carrier, random same-norm baseline, stratified control classes.
- Known limitations: two positive pairs only; Pythia-70M layer 3 only; no
  second seed/model acceptance; strict behavior measured by binary classifier,
  not generation.

Action class:

- Retrieval/search/discovery: search.
- Why: this perturbs scale and objective aliases inside the already-created
  `multiclass_state_gate` schema. It does not add a new accepted mechanism
  class.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/multiclass_state_gate_stress_2026_06_12.md`;
  local ignored artifacts
  `artifacts/activation_geometry/modal_pythia_70m_layer3_relation_multiclass_state_gate_scale_seed20260610.json`
  and
  `artifacts/activation_geometry/modal_pythia_70m_layer3_relation_multiclass_state_gate_alias1_seed20260610.json`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: twelve controls split across `source_sharing`,
  `target_sharing`, `implausible_random_null`, and `semantic_near_null`.
- Stress tests: scale sweep over `0.75`, `1.0`, `1.25`, `1.5`; objective
  `alias_1` with held-out eval `alias_2`.

Gate:

- Acceptance rule: preserve at least `1/2` strict positives and `0/12`
  stratified controls across the objective-alias perturbation and a nontrivial
  scale neighborhood, with random same-norm at `0/2`, `0/12`.
- Withheld/rejected rule: withhold paper-ready mechanism claims if the effect is
  a single-scale operating point, if controls revive under alias shift, or if
  higher scale breaks the always-false carrier.

Results:

- Accepted artifacts: stress report and two ignored Modal payloads.
- Rejected or withheld artifacts: the hypothesis that the current relation
  multi-class prototype gate is a stable semantic-specific intervention.
- Key metrics: scale `1.0` gives `1/2` positives and `0/12` controls; scale
  `0.75` gives `0/2`, `0/12`; scale `1.25` gives `1/2`, `4/12`; scale `1.5`
  gives `0/2`, `2/12` and flips the always-false carrier positive on the
  `attractor` row. Objective `alias_1` gives `1/2` positives and `1/12`
  controls through target-sharing leakage, while scalar state gating gives
  `1/2`, `0/12` in the same slice.
- Variance or ablation: random same-norm remains `0/2`, `0/12` in both stress
  runs, so the revived controls are structured intervention failures rather
  than verifier permissiveness.

Residual content:

- Explained by old regime: the narrow `attractor` pocket survives many
  conditional variants, but its specificity is sensitive to scale and alias.
- New content outside old regime: relation controls can help under one
  train-variant slice, but target-sharing leakage under alias stress shows the
  gate is not separating target identity from target-family overlap.
- Retractions or supersessions: supersede "relation multi-class prototype gate
  may be the paper nucleus" with "relation multi-class prototype gate is a
  diagnostic boundary that motivates held-out-control conditional training."

Next move: train/evaluate a conditional gate with held-out control classes,
especially source-sharing and target-sharing controls, or pivot to a learned
classifier/gate that explicitly separates target identity from target-family and
source-family overlap.

## Activation Geometry Probe: Held-Out Control Conditional Gate

Question: does the relation multi-class prototype gate leak target-sharing
controls because those control classes are present during relation-control
training?

Current regime:

- Artifact types: strict binary-relation rows, stratified control summaries,
  optimized gated-intervention summaries, ignored Modal payloads, stress
  reports, held-out-control filtering reports.
- Operations: Modal-backed Pythia-70M layer-3 intervention, relation-control
  prompt construction from stratified controls, relation-control class
  filtering, hidden-state prototype construction, target-vs-control max-margin
  gating, held-out alias scoring.
- Gates/verifiers: held-out `alias_2`, strict positive/control pass counts,
  always-false carrier, random same-norm baseline, stratified source-sharing and
  target-sharing controls.
- Known limitations: two positive pairs only; Pythia-70M layer 3 only; strict
  behavior measured by binary classifier, not generation.

Action class:

- Retrieval/search/discovery: search.
- Why: this adds held-out control-class filters inside the existing relation
  multi-class state-gate schema, but it does not create an accepted intervention
  class.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/heldout_control_conditional_gate_2026_06_12.md`;
  local ignored artifacts
  `artifacts/activation_geometry/modal_pythia_70m_layer3_heldout_control_conditional_gate_alias1_seed20260610.json`
  and
  `artifacts/activation_geometry/modal_pythia_70m_layer3_heldout_target_conditional_gate_alias1_seed20260610.json`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: twelve controls split across `source_sharing`,
  `target_sharing`, `implausible_random_null`, and `semantic_near_null`.
- Stress tests: withhold `source_sharing`, `target_sharing`, or both from
  relation-control prompt construction; duplicate target-holdout smoke.

Gate:

- Acceptance rule: preserve at least `1/2` strict positives while reducing the
  objective-alias target-sharing leak to `0/12` controls.
- Withheld/rejected rule: reject held-out-control filtering if the same
  target-sharing control passes after its class is withheld from training.

Results:

- Accepted artifacts: three held-out-control direction modes, the negative
  report, and two ignored Modal payloads.
- Rejected or withheld artifacts: the hypothesis that source/target control
  class withholding is sufficient to recover semantic specificity.
- Key metrics: the full relation multi-class gate gives `1/2` positives and
  `1/12` controls; source-holdout, target-holdout, and overlap-holdout variants
  all remain `1/2` positives and `1/12` controls. The shared leaked row is
  `phase_space->attractor_network`.
- Variance or ablation: the duplicate target-holdout smoke confirms the same
  target-sharing leak; `random_same_norm` remains `0/2`, `0/12`.

Residual content:

- Explained by old regime: the narrow `attractor` pocket and target-sharing
  leakage persist under multiple conditional-gate variants.
- New content outside old regime: target-sharing leakage is not explained by
  ordinary exposure to target-sharing controls during optimization; it appears
  tied to a target-family channel shared by the positive and null rows.
- Retractions or supersessions: supersede "held-out control classes might solve
  the relation multi-class leak" with "target-family overlap needs explicit
  target-identity disambiguation or a different behavior interface."

Next move: run an oracle or learned row-conditioned target-family
disambiguation gate that tests whether `attractor->attractor_network` can be
separated from target-sharing nulls such as `phase_space->attractor_network`.

## Activation Geometry Probe: Target-Family Pair Gate

Question: can an oracle-style relation-pair prototype gate separate exact target
identity from target-family overlap?

Current regime:

- Artifact types: strict binary-relation rows, stratified control summaries,
  optimized gated-intervention summaries, ignored Modal payloads, stress
  reports, relation-pair prototype reports.
- Operations: Modal-backed Pythia-70M layer-3 intervention, relation-control
  prompt construction, exact relation-pair prototype grouping, hidden-state
  prototype gating, held-out alias scoring, scale stress.
- Gates/verifiers: held-out `alias_2`, strict positive/control pass counts,
  always-false carrier, random same-norm baseline, stratified source-sharing and
  target-sharing controls.
- Known limitations: two positive pairs only; Pythia-70M layer 3 only; strict
  behavior measured by binary classifier, not generation.

Action class:

- Retrieval/search/discovery: search.
- Why: this sharpens the existing multi-class prototype gate from broad
  relation-control classes to exact relation-pair prototypes, but it does not
  create an accepted mechanism class.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/target_family_pair_gate_2026_06_12.md`;
  local ignored artifacts
  `artifacts/activation_geometry/modal_pythia_70m_layer3_target_family_pair_gate_alias1_seed20260610.json`
  and
  `artifacts/activation_geometry/modal_pythia_70m_layer3_target_family_pair_gate_scale_alias1_seed20260610.json`.
- Positive targets: `attractor->attractor_network` and
  `fixed_point->prototype`.
- Negative controls: twelve controls split across `source_sharing`,
  `target_sharing`, `implausible_random_null`, and `semantic_near_null`.
- Stress tests: direct comparison against class-level relation multi-class gate;
  scale sweep over `0.75`, `1.0`, `1.25`, `1.5`.

Gate:

- Acceptance rule: preserve at least `1/2` strict positives while reducing the
  objective-alias target-sharing leak to `0/12` controls, with random same-norm
  remaining at `0/2`, `0/12`.
- Withheld/rejected rule: reject exact relation-pair prototype gating if
  `phase_space->attractor_network` passes after it has its own prototype class.

Results:

- Accepted artifacts: `target_binary_relation_pair_multiclass_state_gate_opt_8`,
  negative report, and two ignored Modal payloads.
- Rejected or withheld artifacts: the hypothesis that exact relation-pair
  prototypes are sufficient to recover semantic specificity from the relation
  multi-class gate.
- Key metrics: at scale `1.0`, class-level and pair-level relation gates both
  give `1/2` positives and `1/12` controls, leaking the same target-sharing row.
  The pair gate uses `19` prototype groups for the `attractor` row, including a
  dedicated `phase_space->attractor_network` prototype, but still leaks it.
- Variance or ablation: scale `0.75` gives `0/2`, `0/12`; scale `1.0` gives
  `1/2`, `1/12`; scale `1.25` gives `0/2`, `2/12`; scale `1.5` gives `1/2`,
  `2/12`. `random_same_norm` remains `0/2`, `0/12`.

Residual content:

- Explained by old regime: the narrow binary-relation pocket remains sensitive
  to scale and structured source/target overlap.
- New content outside old regime: even exact relation-pair hidden-state
  prototypes do not produce a target-identity separator; the training-time
  target-over-control max margin is near zero for the `attractor` row.
- Retractions or supersessions: supersede "held-out/row-conditioned prototype
  gates might solve target-family leakage" with "the prototype-gated
  binary-relation interface appears under-identified for target-family
  disambiguation."

Next move: stop optimizing this prototype-gated binary-relation interface. Test
supervised exact-relation readout identifiability within target families before
running more steering interventions.

## Arc 2B: Haskell Verdicts Consumed by Python Body Gates

Question: can the empirical Arc 2A/2B body summaries consume the external
Haskell admissibility checker instead of carrying only parallel static verdicts?

Current regime:

- Artifact types: Python agent/body summaries, vector module-body reports,
  Haskell ontology verdict JSON, fallback static formal verdicts.
- Operations: Python learned/vector body evaluation, Cabal-backed
  `ontology-check`, cached subprocess bridge, report table generation.
- Gates/verifiers: Python unit tests for parser and provenance, live Haskell
  integration test when Cabal is available, Haskell test suite, full Python
  quality wrapper.
- Known limitations: the checker remains a small typed admissibility layer over
  named motifs, not full program verification or neural architecture proof.

Action class:

- Retrieval/search/discovery: search.
- Why: this moves an existing verifier into the empirical gate path without
  adding a new body grammar or accepted mechanism class.

Experiment:

- Manifest/report paths: `experiments/viable_computational_bodies/haskell_gate.py`;
  `formal/ontology-hs/app/Main.hs`;
  `tests/test_viable_computational_bodies.py`.
- Positive targets: `modular_concerned_body` and `guarded_syntax_body` should
  record `formal_source = "haskell"` and valid formal verdicts when Cabal is
  available.
- Negative controls: `restless_vector_body` and `restless_tree_body` should
  retain the `restless_without_calibration_guard` violation.
- Stress tests: Cabal/Haskell unavailable path falls back to `python_static`
  provenance rather than failing Modal or lightweight Python runs.

Gate:

- Acceptance rule: Python body summaries record Haskell source, formal validity,
  resource cost, and violations when the external checker is present, while
  preserving executable body gate outcomes.
- Withheld/rejected rule: do not claim full formal verification; reject the
  integration if Haskell failures are silently converted into passing verdicts.

Results:

- Accepted artifacts: named Haskell CLI verdicts, Python cached bridge, summary
  provenance fields, parser/fallback/live integration tests.
- Rejected or withheld artifacts: full shared JSON schema across search and
  Haskell motif bodies remains future work.
- Key metrics: expected Haskell costs are `8` for `modular_concerned_body`,
  `6` for `restless_vector_body`, and `12` for symbolic guarded/restless tree
  bodies.
- Variance or ablation: unavailable Haskell toolchain path preserves old static
  Python behavior with explicit `python_static` provenance.

Residual content:

- Explained by old regime: the pass/fail body gate shape and four-body vector
  comparison are unchanged.
- New content outside old regime: external typed verdicts now participate in
  the Python empirical summaries and reports.
- Retractions or supersessions: supersede "Haskell ontology is only a parallel
  artifact" with "Haskell admissibility can be consumed by Python body gates."

Next move: define a shared motif JSON schema so body search candidates can be
checked by Haskell before or during vector/pixel gate evaluation.

## Arc 2A: Pixel-Rendered Concerned Syntax

Question: does the concerned-syntax gate survive when vector parts are replaced
by rendered pixels and object attributes must be extracted from the image?

Current regime:

- Artifact types: vector-shape examples, learned agent summaries, body
  summaries, Haskell admissibility verdicts, tracked reports.
- Operations: vector rendering, linear learned probe/action models,
  concern-gated pair probing, passive/restless/surface controls.
- Gates/verifiers: parse-high, action, subtree, high-probe, low-probe, surface
  ambiguity, targeted Python tests, full quality wrapper.
- Known limitations: vector parts were previously given as object-level
  coordinates and roles; no pixel observation or perceptual extraction was
  required.

Action class:

- Retrieval/search/discovery: discovery-leaning transition.
- Why: this adds a new observation surface and operation: RGB rendering plus
  connected-component object extraction. The old vector schema cannot represent
  the image-to-object step, although the downstream gate is intentionally
  transported.

Experiment:

- Manifest/report paths:
  `experiments/concerned_syntax/pixel_shapes.py`;
  `experiments/concerned_syntax/results/pixel_shapes_local_2026_06_16.md`;
  local ignored artifact
  `artifacts/concerned_syntax/pixel_shapes_local_sweep.json`.
- Positive targets: `concerned_pixel_probe` should pass the transported 2A
  gate after object extraction.
- Negative controls: `surface_pixel_shortcut`, `passive_pixel`, and
  `restless_pixel_probe`.
- Stress tests: hidden true/alternate parse swap must leave the RGB image
  unchanged; connected-component extraction must recover six objects; five
  local seeds must preserve the failure taxonomy.

Gate:

- Acceptance rule: object extraction rate >= 0.99, parse-high >= 0.75, action
  >= 0.85, subtree >= 0.75, high-concern probe >= 0.70, and low-concern probe
  <= 0.25 for the concerned pixel agent, with controls failing for diagnostic
  reasons.
- Withheld/rejected rule: withhold human-vision, natural-image, or
  unsupervised-slot claims; reject the result if passive object features recover
  hidden binding or if the rendered image leaks the parse.

Results:

- Accepted artifacts: pixel renderer, connected-component extractor,
  pixel-agent report, Modal sweep entrypoint, tests, and paper update.
- Rejected or withheld artifacts: no claim of learned object-slot perception;
  no Modal-scale pixel sweep yet.
- Key metrics across five local seeds: `concerned_pixel_probe` parse-high
  `0.996`, action `0.999`, subtree `0.786`, object extraction `1.000`,
  high-probe `0.993`, low-probe `0.187`, gate pass rate `1.000`.
  `passive_pixel` parse-high is `0.503`; `surface_pixel_shortcut` parse-high
  is `0.503`; `restless_pixel_probe` low-probe is `1.000`.
- Variance or ablation: concerned pixel gate pass SD is `0.000`; parse-high SD
  is `0.007`; object extraction SD is `0.000`.

Residual content:

- Explained by old regime: the same concern-gated intervention separates
  passive, shortcut, and restless controls once object features are available.
- New content outside old regime: the accepted gate now includes an explicit
  pixel-to-object operation, and passive object extraction is not enough to
  recover hidden causal constituency.
- Retractions or supersessions: supersede "Arc 2A has no pixel surface" with
  "Arc 2A has a pixel-rendered, object-extracted concerned-syntax gate."

Next move: either run the Modal-scale pixel sweep or replace the
connected-component extractor with a learned object-slot encoder while keeping
the same hidden-parse invariance and no-restless controls.

## Arc 2A: Concerned Intervention Invention

Question: can the pixel-level concerned-syntax agent learn both when to
intervene and which object-pair probe program makes the viability-relevant
hidden binding observable?

Current regime:

- Artifact types: pixel-rendered shape examples, extracted object features,
  learned probe policy, provided pair probe target, tracked reports and tests.
- Operations: RGB rendering, connected-component extraction, concern-gated
  pair probing, passive/restless/surface controls.
- Gates/verifiers: parse-high, action, subtree, high-probe, low-probe,
  object-extraction rate, hidden-parse-invariant rendering, targeted tests.
- Known limitations: the previous pixel agent was given the causal probe
  target; it did not have to choose which pair to observe.

Action class:

- Retrieval/search/discovery: discovery-leaning transition.
- Why: this adds a probe-program selection operation and target-accuracy gate.
  The old pixel regime could test probe use, but not intervention-target
  invention.

Experiment:

- Manifest/report paths:
  `experiments/concerned_syntax/intervention_invention.py`;
  `experiments/concerned_syntax/modal_intervention_invention_sweep.py`;
  `experiments/concerned_syntax/results/intervention_invention_local_2026_06_16.md`;
  `experiments/concerned_syntax/results/intervention_invention_modal_2026_06_16.md`;
  local ignored artifact
  `artifacts/concerned_syntax/intervention_invention_local.json`.
- Positive targets: `concerned_program_inventor` should pass the transported
  2A gate plus target/useful-program gates.
- Negative controls: `surface_program_shortcut`, `random_program_probe`,
  `concern_without_target`, and `target_without_concern`.
- Stress tests: selected object pair must be learned from pixel-object features
  rather than `trial.causal_pair`; target-only control must fail low-concern
  discipline; concern-only control must fail target usefulness.

Gate:

- Acceptance rule: object extraction >= 0.99, parse-high >= 0.75, action >=
  0.85, subtree >= 0.75, high-concern probe >= 0.70, low-concern probe <=
  0.25, target accuracy high-concern >= 0.75, and useful-program rate
  high-concern >= 0.70.
- Withheld/rejected rule: withhold claims of raw motor-program invention,
  natural-image perception, or open-ended apparatus discovery. Reject the
  result if target selection succeeds without concern discipline or concern
  discipline succeeds without useful target selection.

Results:

- Accepted artifacts: intervention-invention module, Modal sweep entrypoint,
  public local report, tests, Phase 2 trajectory note, paper update, and source
  manifest update for the A-CBO causal-discovery critique.
- Rejected or withheld artifacts: no learned object-slot encoder; no raw motor
  primitive invention; no movement/ablation/two-step program language yet.
- Key metrics across five Modal seeds: `concerned_program_inventor` parse-high
  `1.000`, action `1.000`, subtree `0.796`, object extraction `1.000`,
  high-probe `1.000`, low-probe `0.156`, target-high `1.000`, useful-high
  `1.000`, gate pass rate `1.000`. `target_without_concern` target-high
  `1.000` but low-probe `1.000`; `concern_without_target` low-probe `0.156`
  but target-high `0.088`.
- Variance or ablation: concerned inventor gate pass SD `0.000`; subtree SD
  `0.013`; low-probe SD `0.009`; target-high SD `0.000`. The local 1,200/500
  split also passed and is tracked separately.

Residual content:

- Explained by old regime: concern-gated probing and pixel-object extraction
  still explain the transported parse/action/subtree gate.
- New content outside old regime: probe target selection is now learned as a
  program-selection step, and the gate separates "knows when to ask" from
  "knows what to ask."
- Retractions or supersessions: supersede "intervention invention is not done"
  with "minimal `observe_pair(a,b)` target invention is locally passed; open
  program invention remains future work."

Next move: extend the program language to `move(anchor)`, `ablate(role)`, and
two-step compositions while adding held-out role-pair and parse-family
transfer.

## Arc 2A/2B: Program-Body Search Against 2A-v1

Question: can Arc 2B search discover formal, resource-bounded bodies whose
motifs express the current Arc 2A intervention-invention contract?

Current regime:

- Artifact types: 2A-v1 intervention-invention empirical summaries,
  2B motif bodies, static body contracts, Modal reports.
- Operations: train/evaluate the 2A-v1 pixel/program gate on Modal, map body
  motifs to empirical 2A controls, mutate/repair/promote bodies, and score
  final bodies by both empirical gate and formal/static body validity.
- Gates/verifiers: empirical 2A gate pass, body formal validity, resource
  budget, calibration/formal guard requirements, targeted unit tests, Modal
  five-seed sweep.
- Known limitations: body motifs still map to existing 2A controls rather than
  neural modules; Haskell motif checking is compatible but not yet in the
  inner search loop.

Action class:

- Retrieval/search/discovery: discovery-leaning coupled transition.
- Why: this freezes the first explicit 2A contract
  (`2A-v1-pixels-observe_pair`) and makes 2B search consume that empirical
  contract instead of only optimizing a symbolic proxy.

Experiment:

- Manifest/report paths:
  `experiments/viable_computational_bodies/program_body_search.py`;
  `experiments/viable_computational_bodies/modal_program_body_search.py`;
  `experiments/viable_computational_bodies/results/program_body_search_modal_2026_06_16.md`;
  local ignored artifact
  `artifacts/viable_computational_bodies/program_body_search_modal.json`.
- Positive target: `viability_guided` should discover a formal concerned
  program body that maps to `concerned_program_inventor`.
- Negative controls: `reward_only` should find shortcut reward and fail;
  `syntax_proxy` should chase target/useful metrics but fail the full formal
  or concern/calibration contract.
- Stress tests: 2A role-transfer hook records held-out role-pair performance
  without making it a required body gate yet; the user explicitly requested
  Modal rather than local CPU for sweeps.

Gate:

- Acceptance rule: body gate rate >= 0.75 across Modal seeds, empirical gate
  rate >= 0.75, formal valid rate 1.000, target/useful high-concern rates
  >= 0.75, low-concern probe <= 0.25, and controls fail for distinct reasons.
- Withheld/rejected rule: do not claim neural architecture search or Haskell
  in-loop verification yet. Reject if reward-only or syntax-proxy satisfies the
  full body gate.

Results:

- Accepted artifacts: program-body search module, Modal entrypoint, Modal
  report, tests, README command, and remote-first handoff rule.
- Rejected or withheld artifacts: local diagnostic report not tracked; Haskell
  motif verdicts not yet consumed inside program-body search; richer 2A
  program language remains future work.
- Key metrics across five Modal seeds: `viability_guided` body gate `1.000`,
  empirical gate `1.000`, formal valid `1.000`, target-high `1.000`,
  useful-high `1.000`, low-probe `0.156`, best body
  `calibration_guard+causal_binding_head+concern_policy+formal_guard+intervention_planner+reward_head+vector_surface_encoder+world_model`.
  `reward_only` body gate `0.000`, target-high `0.000`, shortcut body.
  `syntax_proxy` target-high `1.000` and useful-high `1.000`, but body gate
  `0.000` and low-probe `0.830`.
- Variance or ablation: Modal five-seed body gate rate is stable at `1.000` for
  `viability_guided`; controls remain rejected.

Residual content:

- Explained by old regime: the 2A-v1 empirical gate still supplies the
  underlying concerned-program-inventor behavior.
- New content outside old regime: 2B search now discovers a valid body motif
  set that expresses the empirical 2A contract, making Arc 2A and 2B coupled
  rather than parallel artifacts.
- Retractions or supersessions: supersede "2B has only proxy intervention
  invention scores" with "2B search can consume the actual 2A-v1 program gate."

Next move: put Haskell motif verdicts inside `program_body_search`, then lift
the contract to `2A-v2` with `move(anchor)`, `ablate(role)`, two-step programs,
and held-out role/parse transfer as an actual body gate.

## Phase / Arc 2A: Rich Intervention-Program Language

Question: can a pixel-level concerned-syntax agent choose the right family of
intervention program, not only the right `observe_pair(a,b)` target, while
preserving low-concern discipline?

Current regime:

- Artifact types: 2A-v1 pixel/program examples, extracted object features,
  learned concern policy, learned target selector, Modal reports, targeted
  tests.
- Operations: choose whether to intervene, select a target pair, and run the
  provided `observe_pair(a,b)` program.
- Gates/verifiers: object extraction, parse/action/subtree, high/low probe
  discipline, target accuracy, useful-program rate, Modal five-seed sweep.
- Known limitations: `observe_pair(a,b)` was the only useful program family,
  so target selection could pass without learning a richer intervention
  grammar.

Action class:

- Retrieval/search/discovery: discovery-leaning intervention-language
  transition.
- Why: this changes the program grammar and gate. The accepted agent must
  select among `observe_pair`, `move_anchor`, `ablate_pair`, and
  `compose_move_observe` families, not merely decide which pair to observe.

Experiment:

- Manifest/report paths:
  `experiments/concerned_syntax/rich_program_language.py`;
  `experiments/concerned_syntax/modal_rich_program_language_sweep.py`;
  `experiments/concerned_syntax/results/rich_program_language_local_2026_06_17.md`;
  `experiments/concerned_syntax/results/rich_program_language_modal_2026_06_17.md`;
  local ignored artifacts under
  `artifacts/concerned_syntax/rich_program_language_*.json`.
- Positive target: `concerned_program_composer` should pass the transported
  2A gate plus family, target, useful-program, and rich-program gates.
- Negative controls: `surface_rich_shortcut`, `random_rich_program`,
  `family_without_target`, `target_without_family`, and
  `rich_without_concern`.
- Stress tests: target-only and family-only controls must fail separately;
  a rich composer without concern must fail low-concern discipline.

Gate:

- Acceptance rule: object extraction >= 0.99, parse-high >= 0.75, action >=
  0.85, subtree >= 0.75, high-concern program rate >= 0.70, low-concern
  program rate <= 0.25, target-high >= 0.70, family-high >= 0.70,
  useful-high >= 0.70, and rich-high >= 0.70.
- Withheld/rejected rule: do not claim open-ended apparatus discovery,
  learned object-slot perception, or body-level consumption of the v2 contract.
  Reject controls that pass target, family, action, or parse alone.

Results:

- Accepted artifacts: rich program-language module, Modal sweep entrypoint,
  public local and Modal reports, targeted tests, README commands, trajectory
  and handoff updates.
- Rejected or withheld artifacts: raw JSON under ignored `artifacts/`; no
  learned object-slot encoder; no search-discovered grammar; no 2B body search
  against the v2 contract yet.
- Key metrics across five Modal seeds: `concerned_program_composer`
  parse-high `1.000`, action `1.000`, subtree `0.794`, object extraction
  `1.000`, high-program `1.000`, low-program `0.162`, family-high `1.000`,
  target-high `1.000`, useful-high `1.000`, rich-high `1.000`, mean regret
  `0.004`, gate pass rate `1.000`.
  `target_without_family` gets target-high `1.000` but family-high `0.000`
  and useful-high `0.000`. `family_without_target` gets family-high `1.000`
  but target-high `0.080`. `rich_without_concern` gets parse/action/family/
  target all `1.000` but low-program `1.000`.
- Variance or ablation: Modal five-seed gate pass is stable at `1.000` for the
  composer; controls remain rejected for distinct family, target, or concern
  failures. The local 1,200/500 split also passed.

Residual content:

- Explained by old regime: pixel-object extraction, concern gating, and target
  selection still explain part of the result.
- New content outside old regime: useful intervention now depends on program
  family, so `observe_pair(a,b)` is no longer a universal solution. The gate
  separates "knows what object pair matters" from "knows which manipulation
  makes that binding legible."
- Retractions or supersessions: supersede "richer program language remains
  future work" with "provided rich program grammar passes; open-ended program
  discovery and held-out transfer remain future work."

Next move: add held-out role/parse transfer, then make 2B body search and the
Haskell admissibility layer consume `2A-v2-pixels-rich_programs`.
