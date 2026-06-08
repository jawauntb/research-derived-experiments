# Pooling-Aware Intervention Layer Candidates - 2026-06-08

## Question

Which activation layers should be used for the first classifier/readout and steering/generation pilots?

The pooling ablation showed that centered bridge geometry survives across models and pooling rules, but the layer profile depends on the readout. This report turns the accepted sweeps into a preregistered candidate list before any causal intervention is run.

## Inputs

- Pythia mean-pooling sweep: `experiments/activation_geometry/results/modal_pythia_70m_layer_sweep_2026_06_08.md`
- GPT-2 mean-pooling sweep: `experiments/activation_geometry/results/modal_gpt2_layer_sweep_2026_06_08.md`
- Pooling ablation: `experiments/activation_geometry/results/pooling_ablation_pythia_gpt2_2026_06_08.md`
- First bridge-pair evidence: `experiments/activation_geometry/results/modal_pythia_70m_layer_last_2026_06_08.md`

## Selection Rule

Eligible layers must clear the accepted centered activation gate:

- Mean-centered category separation at least `0.05`.
- Mean-centered bridge lift at least `0.05`.
- At least `0.75` of bridge pairs above the non-bridge cross-category mean.

For each model/readout:

- Primary: strongest passing layer by centered bridge lift.
- Backup: nearby or second-strong passing layer that preserves the qualitative pattern.
- Control: a layer that fails the gate, preferably by bridge-pair rate rather than total collapse.

Layer `0` is excluded from intervention candidates because it is the embedding hidden state, not a transformer block output.

## Candidate Layers

### Mean-Pooling Classifier/Readout Pilot

Mean pooling is the right readout for pooled concept classifiers or nearest-centroid experiments because it treats the prompt as a bag of contextualized token evidence.

| Model | Role | Layer | Centered category separation | Centered bridge lift | Centered bridge rate | Reason |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Pythia-70M | Primary | 2 | 0.1857 | 0.2248 | 0.9167 | Strongest mean-pooling block layer. |
| Pythia-70M | Backup | 6 | 0.1356 | 0.1957 | 0.9167 | Reproduces final-layer signal and tests depth shift. |
| Pythia-70M | Control | 4 | 0.0007 | 0.0985 | 0.5833 | Positive bridge lift but fails category separation and bridge rate. |
| GPT-2 | Primary | 1 | 0.1767 | 0.2348 | 1.0000 | Strongest mean-pooling block layer. |
| GPT-2 | Backup | 11 | 0.1894 | 0.1422 | 0.7500 | Later passing layer, useful against early-layer-only explanations. |
| GPT-2 | Control | 4 | 0.0528 | 0.0974 | 0.5000 | Passes separation/lift but fails bridge-pair rate. |

### Final-Token Steering/Generation Pilot

Final-token pooling is the right readout for generation or steering because the last prompt position is where a causal LM has accumulated the prompt context before predicting the next token.

| Model | Role | Layer | Centered category separation | Centered bridge lift | Centered bridge rate | Reason |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Pythia-70M | Primary | 5 | 0.1643 | 0.1811 | 0.8333 | Strongest final-token block layer. |
| Pythia-70M | Backup | 6 | 0.1565 | 0.1670 | 0.8333 | Final layer remains strong under final-token pooling. |
| Pythia-70M | Control | 1 | 0.1022 | 0.0715 | 0.5000 | Has separation/lift but fails bridge-pair rate. |
| GPT-2 | Primary | 12 | 0.2700 | 0.3619 | 0.8333 | Strongest final-token layer and final generation state. |
| GPT-2 | Backup | 11 | 0.1612 | 0.1355 | 0.7500 | Adjacent passing layer for depth robustness. |
| GPT-2 | Control | 4 | 0.0989 | 0.0393 | 0.5000 | Similar category separation but weak bridge signal. |

## Bridge-Pair Candidates

The first intervention should use bridge pairs that were strong or interpretable in the existing activation reports, while preserving weak pairs as controls.

Positive candidates:

| Bridge pair | Why it is useful |
| --- | --- |
| `attractor` -> `attractor_network` | Strongest first activation-space bridge and central to the convergence thesis. |
| `conceptual_space` -> `representation_manifold` | Directly tests whether linguistic and AI geometry terms align in activations. |
| `autopoiesis` -> `homeostasis` | Good boundary/self-maintenance pair for the agency track. |
| `validity_gate` -> `weak_constraint` | Methodological bridge that may support discovery-process experiments. |

Negative or cautionary candidates:

| Pair | Why it should be handled as a control |
| --- | --- |
| `valence` -> `activation_vector` | Weak or negative in the first activation report; useful as a non-transporting bridge. |
| `valence` -> `steering_vector` | Also weak/negative; good guard against over-broad steering claims. |
| `embedding` -> `steering_vector` | Interpretable but confounded by shared AI vocabulary; use only after stronger pairs. |

## First Pilot Shape

### Classifier/Readout

Use mean-pooling primary and backup layers. Construct concept centroids from two paraphrases per concept and hold out the third paraphrase. Evaluate whether bridge-pair cosine/lift on held-out variants beats non-bridge cross-category pairs.

Acceptance gate:

- Primary layers must outperform their control layers on bridge-pair above-baseline rate by at least `0.20`.
- At least three of four positive bridge-pair candidates must beat the non-bridge cross-category mean in both models.
- Valence control pairs should not pass both models.

### Steering/Generation

Use final-token primary and backup layers. For each positive bridge pair, compute a direction from the source concept centroid toward the target concept centroid. Apply small signed interventions at the selected final-token layer and evaluate next-token/generation shifts with lightweight semantic probes.

Acceptance gate:

- Target bridge concept similarity must increase more than unrelated cross-category concept similarity.
- The backup layer must show the same sign of effect, even if smaller.
- Control layers or valence control pairs must not show the same targeted effect.
- Outputs must be inspected for generic semantic drift, repetition, or category leakage.

## Interpretation

The next experiment should not ask "which layer is best?" in the abstract. It should ask which layer is best under a declared readout:

- Mean-pooling classifier/readout: start with Pythia layer `2` and GPT-2 layer `1`.
- Final-token steering/generation: start with Pythia layer `5` and GPT-2 layer `12`.

This prevents the pooling ablation from becoming a confusing pile of layer scores. We now have a preregistered layer, backup, and control for each model/readout combination.

## Discovery-Regime Audit

Question: which layers are eligible for the first classifier and steering interventions?

Current regime:

- Artifact types: concept prompts, activation-layer metrics, pooling-indexed layer profiles, bridge-pair candidates, intervention preregistration notes.
- Operations: layer eligibility filtering, primary/backup/control selection, bridge-pair triage, gate definition.
- Gates/verifiers: centered activation gate, pooling-specific readout rule, held-out paraphrase gate, control-layer gate, control-pair gate.
- Known limitations: pair-level stability has not yet been recomputed for every selected layer; no causal patching has been run.

Action class:

- Retrieval/search/discovery: gate-setting search.
- Why: this does not add a new experimental result; it constrains the next causal/search step before outcomes are known.

Experiment:

- Manifest/report paths: this report.
- Positive targets: selected classifier and steering layers, plus positive bridge-pair candidates.
- Negative controls: failed layers and weak valence pairs.
- Stress tests: backup layers, held-out paraphrases, and control layers.

Gate:

- Acceptance rule: candidate layers must come from accepted model/pooling sweeps and satisfy the role-specific selection rule.
- Withheld/rejected rule: embedding layer `0` and failed bridge-rate layers cannot be primary intervention targets.

Results:

- Accepted artifacts: this report.
- Rejected or withheld artifacts: no raw activations added; raw payloads remain local-only.
- Key metrics: mean-pooling primaries Pythia `2` and GPT-2 `1`; final-token primaries Pythia `5` and GPT-2 `12`.
- Variance or ablation: backup/control layers are preregistered for each model/readout.

Residual content:

- Explained by old regime: layer scores can select candidates.
- New content outside old regime: intervention targets are now readout-specific, not global layer claims.
- Retractions or supersessions: do not use a single "best layer" across classifier and generation settings.

Next move: implement the held-out paraphrase classifier/readout pilot before any generative steering claim.
