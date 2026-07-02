# Pre-registration: Semantic Concern Geometry

**Frozen:** 2026-07-02, before the Modal semantic-concern sweep is dispatched.

## Question

Paper B shows that a movable spatial loss-weight field deforms the learned
metric in path-integration RNN, causal Transformer, and JEPA-style models. This
follow-up asks whether the same causal pattern appears in a non-spatial text
setting with pretrained transformer encoders.

Operationally, **concern** means only a scalar training loss weight. It is not a
claim about sentience, consciousness, or affect. The intervention is:

`w(example) = concern_weight` for examples from one registered semantic class,
and `w(example) = 1` otherwise, normalized to mean one inside each training run.

The core moved-location question is whether moving the upweighted semantic class
moves the representation-geometry change to that class.

## Dataset and Registered Semantic Targets

Primary dataset: the scikit-learn 20 Newsgroups train/test split, with headers,
footers, and quoted replies removed.

Registered classes:

- `sci.space`
- `sci.med`
- `rec.sport.hockey`
- `comp.graphics`

The text task is deliberately non-spatial. If dataset download fails, a synthetic
template fallback may be used only for smoke/debugging. It cannot support the
externality claim and must be reported as withheld for the "real text" gate.

## Model Families

Confirmatory model families:

- `sentence-transformers/all-MiniLM-L6-v2` with a supervised classifier head.
- `sentence-transformers/all-MiniLM-L6-v2` with a supervised classifier head plus
  a JEPA-like predictive latent objective.
- `distilbert-base-uncased` with a supervised classifier head.
- `distilbert-base-uncased` with a supervised classifier head plus a JEPA-like
  predictive latent objective.

The JEPA-like text objective predicts the stop-gradient latent of another
same-class text example from the current text latent. This is a joint-embedding
predictive analogue for the paper's causal test; it is not claimed to be the
official I-JEPA architecture.

All confirmatory geometry is measured in the learned finite-dimensional latent
used by the classifier/predictive head, not in the classifier logits.

## Conditions

For each seed, model family, and semantic target:

- `uniform`: all examples have equal loss weight.
- `concern`: the registered target class receives the high loss weight.
- `random_matched`: a same-sized random subset of training examples receives the
  high loss weight, independent of semantic class.

`uniform` is trained once per seed/family and evaluated for all registered
targets. `concern` and `random_matched` are trained separately for each target.

## Primary Geometry Metrics

For each trained model, compute latent embeddings on the held-out test set and
use cosine distance.

Primary local semantic margin for a class:

`margin = mean_k_nearest_different_class_distance - mean_k_nearest_same_class_distance`

The registered primary z-score is the class margin z-scored across the four
registered classes inside the same model.

Primary causal effects:

- `margin_lift_vs_uniform = concern_target_margin_z - uniform_target_margin_z`
- `margin_lift_vs_random = concern_target_margin_z - random_matched_target_margin_z`

Primary specificity:

- `specificity_z = concern_target_margin_z - mean(non_target_margin_z)`

Since the class z-scores have mean zero, this is reported directly from the
within-model class vector rather than inferred post hoc.

## Companion Geometry Metrics

Companion metrics are confirmatory context, not substitutes for the primary
gate:

- centroid margin z-score: target centroid distance to nearest other centroid
  minus within-class radius, z-scored across classes.
- k-nearest-neighbor purity z-score.
- effective-rank z-score of the target class covariance.
- target F1 and overall accuracy, reported to separate behavioral improvement
  from representational geometry.

## Precision and Acceptance Gate

The user-approved precision rule for this follow-up is **standard error <= 2%**
on the primary causal effects.

For each registered model family, the semantic-concern gate passes only if:

1. `margin_lift_vs_uniform` bootstrap 95% CI lower bound is greater than 0.
2. `margin_lift_vs_random` bootstrap 95% CI lower bound is greater than 0.
3. `specificity_z` bootstrap 95% CI lower bound is greater than 0.
4. Bootstrap SE for both primary causal effects is <= 0.02.
5. Mean target margin rank percentile is greater than 0.5.
6. The dataset used for the run is the real 20 Newsgroups dataset, not the
   synthetic fallback.

The pooled gate is architecture-balanced across all model families and uses the
same criteria except item 5 is computed from pooled rank percentiles.

## Withheld or Rejected Outcomes

- If a family fails any condition above, that family is reported as failed or
  withheld; it is not averaged away.
- If the random-matched control matches or exceeds the semantic-concern effect,
  the interpretation is "generic sample weighting / optimization artifact," not
  semantic concern.
- If the behavior metrics improve but the geometry gate fails, the result is a
  behavioral weighting effect, not a metric-deformation result.
- If only the synthetic fallback runs, the experiment is a local smoke test and
  cannot be used to claim external generalization beyond spatial tasks.

## Planned Run

Default scale run:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
    experiments/semantic_concern_geometry/modal_semantic_concern_sweep.py \
    --seeds 64 --steps 90 --batch-size 32 --target-se 0.02 \
    --out artifacts/semantic_concern_geometry/semantic_concern_sweep_2026_07_02.json
```

The Modal entrypoint requests H200 or H100 GPUs and dispatches independent
training cells with high container concurrency. B200 was intentionally excluded
after smoke validation showed the stable PyTorch wheel lacks Blackwell `sm_100`
kernels. Raw JSON remains local in
`artifacts/`; committed reports carry the gate statistics.
