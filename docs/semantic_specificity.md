# Semantic Specificity

## Working Definition

An activation intervention is semantically specific for a relation family when it
moves held-out target meanings for positive relations while leaving matched
negative-control relations comparatively unmoved under the same score surface.

This project uses a deliberately operational definition:

```text
specificity_score = heldout_positive_mean_delta - independent_control_mean_delta
```

where:

- `heldout_positive_mean_delta` is the mean target-margin improvement over
  positive concept pairs evaluated on label surfaces that were not used alone to
  construct the direction.
- `independent_control_mean_delta` is the mean target-margin improvement over
  control pairs whose target directions were not the exact construction channel
  being subtracted.
- Both terms must be computed at the same model, layer, prompt frame, scoring
  surface, label normalization, scale, and direction-construction mode.

## Pass Conditions

A result can support a paper-level semantic-specificity claim only if all of the
following hold:

- Held-out positives robustly pass: most positive pairs have positive
  target-margin deltas across option orders or full-label score surfaces.
- Independent controls weaken: control-pair deltas are lower than raw target
  gradients and lower than residual-projection baselines.
- Specificity remains positive under held-out aliases, not only canonical labels
  or the training alias.
- Random same-norm directions do not produce the same positive/control pattern.
- The claimed direction mode survives at least one replication axis: seed, model,
  concept set, or prompt frame.

## Non-Claims

The metric does not prove that the model contains a human-like concept or a
unique causal feature. It is a behavior-aligned intervention score. A strong
result still needs mechanistic follow-up:

- whether leakage channels form a low-rank control subspace;
- whether failures are pair-specific or category-specific;
- whether generation behavior changes in the same direction as label logprobs;
- whether larger models preserve the same specificity frontier.

## Current Interpretation

The current evidence supports a weaker claim:

```text
Full-label behavior gradients expose a specificity frontier, but the frontier
has not yet shown stable held-out alias specificity on expanded controls.
```

That statement is publishable only as a negative/diagnostic result unless the
multi-alias and expanded-control gates improve it.
