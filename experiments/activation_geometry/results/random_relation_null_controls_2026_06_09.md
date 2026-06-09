# Random Relation Null Controls - 2026-06-09

## Question

Target-disjoint hand-picked controls still moved under the current full-label
behavior objective. This run asks whether the same failure appears for seeded
random relation nulls whose targets are disjoint from the expanded positive
target set.

```text
If current behavior directions are semantically specific, random relation nulls
should be weaker than positive bridge pairs under the same held-out alias gate.
```

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_random_relation_nulls_source_seed20260609.json
artifacts/activation_geometry/modal_pythia_70m_random_relation_nulls_latent_seed20260609.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Pair set: `expanded_random_nulls`, with 7 positives and 10 random relation null controls
- Objective labels: `alias_0+alias_1`
- Eval labels: held-out `alias_2` and `canonical`
- Prompt frames: `source_passage`, `latent_choice`
- Layers: primary `5`, backup `6`, control `1`
- Train variants: `0,1`
- Held-out text variant: `2`
- Scale: `1.0`
- Directions: raw target, residual-all, target-penalty-controls-1.0, random same-norm
- Seed: `20260609`

The random relation null controls are seeded, category-mismatched pairs drawn
from concepts outside the expanded positive pair set, with
`valence -> steering_vector` retained as the runner's required hard-control
sentinel.

## Scale 1 Primary-Layer Results

Specificity is:

```text
specificity_score = heldout_positive_mean_delta - independent_control_mean_delta
```

The random relation null gate fails decisively. Target-learned directions move
`6/7` held-out positives in both prompt frames, but they also move `10/10`
random null controls. More importantly, random-null control means are larger
than positive means, making specificity negative in both prompt frames and both
label regimes.

| Prompt | Eval | Direction | Positive passes | Positive mean | Control passes | Control mean | Specificity |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| source_passage | alias_2 | random_same_norm | 3/7 | 0.004 | 3/10 | -0.024 | 0.028 |
| source_passage | alias_2 | target_learned | 6/7 | 0.326 | 10/10 | 0.427 | -0.101 |
| source_passage | alias_2 | target_penalty_controls_1_0 | 6/7 | 0.314 | 10/10 | 0.399 | -0.085 |
| source_passage | alias_2 | target_resid_all | 6/7 | 0.205 | 10/10 | 0.265 | -0.060 |
| source_passage | canonical | target_learned | 6/7 | 0.343 | 10/10 | 0.516 | -0.174 |
| source_passage | canonical | target_penalty_controls_1_0 | 6/7 | 0.331 | 10/10 | 0.471 | -0.140 |
| source_passage | canonical | target_resid_all | 6/7 | 0.275 | 10/10 | 0.325 | -0.049 |
| latent_choice | alias_2 | random_same_norm | 3/7 | -0.003 | 3/10 | -0.046 | 0.043 |
| latent_choice | alias_2 | target_learned | 6/7 | 0.324 | 10/10 | 0.461 | -0.137 |
| latent_choice | alias_2 | target_penalty_controls_1_0 | 6/7 | 0.323 | 10/10 | 0.449 | -0.127 |
| latent_choice | alias_2 | target_resid_all | 6/7 | 0.213 | 10/10 | 0.360 | -0.147 |
| latent_choice | canonical | target_learned | 6/7 | 0.382 | 10/10 | 0.585 | -0.203 |
| latent_choice | canonical | target_penalty_controls_1_0 | 6/7 | 0.398 | 10/10 | 0.561 | -0.163 |
| latent_choice | canonical | target_resid_all | 5/7 | 0.337 | 10/10 | 0.398 | -0.061 |

## Failure Pattern

The one positive that still fails under held-out `alias_2` is:

```text
phase_space -> conceptual_space
```

That positive failure is no longer the main bottleneck. The decisive result is
that all ten random null controls pass for target-learned, residualized, and
target-penalty directions. The current full-label behavior objective is
therefore not measuring a specific concept bridge. It is exposing a broad
answer-label transport channel.

## Diagnosis

Accepted:

```text
The random relation null verifier is implemented and stronger than the
hand-picked control verifier.
```

Rejected:

```text
The current full-label target-gradient directions are semantically specific
under random relation nulls.
```

Rejected:

```text
Residualizing against all controls or subtracting the control mean at weight 1.0
fixes the label-surface transport channel.
```

Withheld:

```text
Any paper claim that uses held-out full-label logprob movement as primary
evidence for semantic concept transport.
```

Best current interpretation:

```text
The intervention directions are causally active, but the verifier rewards broad
target-label promotion. Random relation nulls move more than the intended
positive concept bridges, so the current logprob gate should become a diagnostic
failure mode, not the core success claim.
```

## Next Move

- Add CAA/CAV-style activation-difference baselines to quantify whether the
  failure is specific to target-gradient construction.
- Add a generation or learned behavior-readout gate that does not reward every
  target label equally.
- Add seeds/bootstrap confidence intervals once the verifier can distinguish
  positives from random relation nulls.
- Treat larger-model replication as premature until a non-logprob behavior gate
  passes.

## Discovery-Regime Audit

Question: do random relation nulls reveal whether the behavior directions are
semantic bridges or broad label-surface transport directions?

Current regime:

- Artifact types: alias-indexed behavior-direction manifests, random-relation
  null pair sets, specificity tables, result reports.
- Operations: deterministic random-null pair construction, fallback distractor
  selection, full-label multi-alias target-gradient construction,
  held-out-alias scoring.
- Gates/verifiers: positives must beat random relation nulls under the same
  score surface; controls should not all pass; canonical controls should not be
  stronger than canonical positives.
- Known limitations: one model, one seed, random nulls are seeded once, no
  generation or learned behavior-readout scoring yet.

Action class:

- Retrieval/search/discovery: verifier hardening with a rejected candidate.
- Why: this adds randomized relation nulls and turns the previous ambiguity
  into a clear falsification of the current logprob-specificity claim.

Experiment:

- Manifest/report paths: this report; local ignored payloads under
  `artifacts/activation_geometry/modal_pythia_70m_random_relation_nulls_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: ten seeded random relation null controls with targets
  disjoint from the positive target set.
- Stress tests: `source_passage` and `latent_choice`; held-out `alias_2`;
  canonical labels; random same-norm baseline.

Gate:

- Acceptance rule: continue toward paper-level semantic specificity only if
  positives exceed random relation nulls by a clearly positive specificity
  margin.
- Withheld/rejected rule: reject the current logprob gate if random nulls all
  pass or their means exceed positives.

Results:

- Accepted artifacts: `expanded_random_nulls` pair set and this report.
- Rejected or withheld artifacts: the current target-gradient/residual/penalty
  directions as a semantically specific mechanism.
- Key metrics: target-learned directions move `6/7` positives and `10/10`
  random null controls in both prompt frames; held-out `alias_2` specificity is
  `-0.101` in `source_passage` and `-0.137` in `latent_choice`.
- Variance or ablation: source and latent prompt frames agree; canonical
  specificity is also negative; random same-norm controls remain weak.

Residual content:

- Explained by old regime: full-label gradients can move labels, and random
  directions are much weaker.
- New content outside old regime: random relation nulls move more than intended
  positives, showing that the verifier itself rewards broad label transport.
- Retractions or supersessions: supersede "more controls may rescue this
  logprob gate" with "the logprob gate is now a diagnostic failure mode unless
  a new behavior verifier separates positives from random nulls."

Next move: implement CAA/CAV baselines and a non-logprob behavior gate before
spending on more seeds or larger models.
