# Target-Disjoint Null Controls - 2026-06-09

## Question

The direction-subspace diagnostic showed that some leakage was concentrated in
target- or relation-sharing pockets. This run asks whether the expanded
specificity failure disappears when controls use targets that are disjoint from
the positive target set.

```text
If leakage is mostly shared target-pocket overlap, target-disjoint controls
should pass less often than positives under the same held-out alias gate.
```

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_target_disjoint_nulls_source_seed20260609.json
artifacts/activation_geometry/modal_pythia_70m_target_disjoint_nulls_latent_seed20260609.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Pair set: `expanded_target_disjoint`, with 7 positives and 6 controls
- Objective labels: `alias_0+alias_1`
- Eval labels: held-out `alias_2` and `canonical`
- Prompt frames: `source_passage`, `latent_choice`
- Layers: primary `5`, backup `6`, control `1`
- Train variants: `0,1`
- Held-out text variant: `2`
- Scale: `1.0`
- Directions: raw target, residual-all, target-penalty-controls-1.0, random same-norm
- Seed: `20260609`

The target-disjoint controls avoid every positive target:

```text
valence -> activation_vector
valence -> steering_vector
simplicity_bias -> embedding
semantic_distance -> validity_gate
family_resemblance -> regime_transition
self_boundary -> residual_content
```

`valence -> steering_vector` remains included because the Modal behavior
runner still treats it as the adversarial hard-control sentinel.

## Scale 1 Primary-Layer Results

Specificity is:

```text
specificity_score = heldout_positive_mean_delta - independent_control_mean_delta
```

Target-disjoint controls do not rescue specificity. The raw target-learned
direction still moves `6/7` held-out positives in both prompt frames, but it
also moves `6/6` target-disjoint controls. Canonical specificity is negative in
both frames because canonical control labels move more than canonical positive
labels.

| Prompt | Eval | Direction | Positive passes | Positive mean | Control passes | Control mean | Specificity |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| source_passage | alias_2 | random_same_norm | 3/7 | 0.004 | 4/6 | 0.003 | 0.000 |
| source_passage | alias_2 | target_learned | 6/7 | 0.326 | 6/6 | 0.260 | 0.066 |
| source_passage | alias_2 | target_penalty_controls_1_0 | 6/7 | 0.313 | 6/6 | 0.264 | 0.049 |
| source_passage | alias_2 | target_resid_all | 6/7 | 0.255 | 6/6 | 0.255 | -0.000 |
| source_passage | canonical | target_learned | 6/7 | 0.342 | 6/6 | 0.514 | -0.171 |
| source_passage | canonical | target_penalty_controls_1_0 | 6/7 | 0.312 | 6/6 | 0.534 | -0.222 |
| source_passage | canonical | target_resid_all | 6/7 | 0.241 | 6/6 | 0.313 | -0.072 |
| latent_choice | alias_2 | random_same_norm | 3/7 | -0.003 | 3/6 | -0.010 | 0.007 |
| latent_choice | alias_2 | target_learned | 6/7 | 0.324 | 6/6 | 0.317 | 0.007 |
| latent_choice | alias_2 | target_penalty_controls_1_0 | 6/7 | 0.322 | 6/6 | 0.319 | 0.003 |
| latent_choice | alias_2 | target_resid_all | 5/7 | 0.272 | 6/6 | 0.286 | -0.014 |
| latent_choice | canonical | target_learned | 6/7 | 0.382 | 6/6 | 0.645 | -0.262 |
| latent_choice | canonical | target_penalty_controls_1_0 | 6/7 | 0.361 | 6/6 | 0.682 | -0.321 |
| latent_choice | canonical | target_resid_all | 6/7 | 0.299 | 5/6 | 0.436 | -0.136 |

## Failure Pattern

The persistent positive failure is still:

```text
phase_space -> conceptual_space
```

The more important failure is that the controls pass even when their targets are
fully disjoint from the positive target list. This means the current
full-label-gradient direction is not merely exploiting shared target labels. It
is also using a broader label-surface boosting channel.

## Diagnosis

Accepted:

```text
The target-disjoint control verifier is implemented and exposes a stricter
negative-control family than the previous expanded control set.
```

Rejected:

```text
Target-disjoint controls explain away the expanded specificity failure as
target-pocket overlap.
```

Rejected:

```text
The current target-learned, residualized, or simple target-penalized directions
are semantically specific enough for a paper-level claim.
```

Withheld:

```text
Any claim that held-out alias transfer alone demonstrates semantic concept
transport.
```

Best current interpretation:

```text
The behavior directions are real intervention directions, but the full-label
objective rewards a broad answer-label transport channel. Pair-specific target
pockets are part of the problem, but target-disjoint nulls show they are not the
whole problem. A paper-worthy mechanism now needs either a better verifier
(generation/readout behavior) or a stronger objective with randomized relation
nulls and CAA/CAV baselines.
```

## Next Move

- Add random relation nulls, not only hand-picked target-disjoint controls.
- Add CAA/CAV-style activation-difference baselines under the same verifier.
- Add seeds and bootstrap confidence intervals over pairs and random relation
  nulls.
- Move toward generation or learned behavior-readout tests before scaling this
  exact objective to larger models.

## Discovery-Regime Audit

Question: do target-disjoint controls turn the multi-alias behavior direction
into a semantically specific intervention?

Current regime:

- Artifact types: alias-indexed behavior-direction manifests, target-disjoint
  control pair sets, specificity tables, result reports.
- Operations: full-label multi-alias target-gradient construction,
  held-out-alias scoring, residual/penalty baselines, random same-norm
  comparison.
- Gates/verifiers: positives must transfer on held-out labels; controls with
  disjoint targets must not move comparably; canonical labels should not make
  controls stronger than positives.
- Known limitations: one model, one seed, hand-picked target-disjoint controls,
  label-logprob scoring only.

Action class:

- Retrieval/search/discovery: verifier hardening with a rejected candidate.
- Why: this adds a target-disjoint control family and falsifies the explanation
  that the main failure was only same-target control overlap.

Experiment:

- Manifest/report paths: this report; local ignored payloads under
  `artifacts/activation_geometry/modal_pythia_70m_target_disjoint_nulls_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: six controls whose targets are disjoint from all positive
  targets.
- Stress tests: `source_passage` and `latent_choice`; held-out `alias_2`;
  canonical labels; random same-norm baseline.

Gate:

- Acceptance rule: move toward Phase 2 only if held-out positives remain high
  and target-disjoint controls fall enough to make specificity clearly positive.
- Withheld/rejected rule: withhold semantic specificity if target-disjoint
  controls still pass broadly or canonical specificity is negative.

Results:

- Accepted artifacts: `expanded_target_disjoint` pair set and this report.
- Rejected or withheld artifacts: target-disjoint control rescue of the current
  behavior objective.
- Key metrics: target-learned directions move `6/7` positives and `6/6`
  controls in both prompt frames; held-out `alias_2` specificity is `0.066` in
  `source_passage` and `0.007` in `latent_choice`; canonical specificity is
  negative.
- Variance or ablation: source and latent prompt frames agree; residual and
  control-penalty modes do not improve the gate.

Residual content:

- Explained by old regime: behavior target gradients can move many labels and
  random directions are much weaker on mean delta.
- New content outside old regime: target-disjoint controls show that the leakage
  is broader than same-target-pocket overlap.
- Retractions or supersessions: supersede "target-pocket overlap may be the main
  issue" with "target-pocket overlap exists, but broad full-label transport also
  survives target-disjoint controls."

Next move: add randomized relation nulls and CAA/CAV baselines, then shift the
main evidence target toward generation/readout behavior rather than relying on
full-label logprob gates.
