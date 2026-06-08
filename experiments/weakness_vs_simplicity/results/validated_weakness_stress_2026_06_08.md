# Validated Weakness Stress Test

Date: June 8, 2026

Command:

```bash
python3 experiments/weakness_vs_simplicity/experiment.py --trials 500 --seed 7 --no-memorizer --include-broad-negative-excluder --validation-negatives 6 --out artifacts/weakness_vs_simplicity/validated_weakness_stress.json
```

Raw artifacts:

- `artifacts/weakness_vs_simplicity/validated_weakness_stress.json` (local-only, ignored)
- `artifacts/weakness_vs_simplicity/validated_weakness_stress.stdout.json` (local-only, ignored)

## Manifest

- Features: 6
- Worlds: 64
- Trials: 500
- Positive training observations per trial: 3
- Negative training observations per trial: 3
- Positive validation observations per trial: 0
- Negative validation observations per trial: 6
- Seed: 7
- Base candidate rules: 72
- Memorizer included: no
- Broad negative excluder included: yes

## Summary

| Selector | Mean Jaccard | Mean Accuracy | Mean Form Length | Mean Weakness | Broad Excluder Rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Validated Weakness | 1.0000 | 1.0000 | 4.0000 | 32.0000 | 0.0000 |
| Weakness | 0.5246 | 0.5469 | 9.0000 | 61.0000 | 1.0000 |
| Simplicity | 0.9640 | 0.9730 | 4.0000 | 32.0000 | 0.0000 |
| Random | 0.6697 | 0.7635 | 6.4680 | 35.4260 | 0.2980 |

## Discovery-Regime Audit

Question: can a validity-gated weakness selector keep the benefit of broad reusable rules while rejecting the unsafe broad-negative-excluder candidate?

Current regime:

- Artifact types: Boolean worlds, candidate rule extensions, training observations, withheld validation observations, selector choices, Jaccard/accuracy metrics.
- Operations: generate target one-feature rule, sample training observations, sample withheld validation negatives, inject a broad training-consistent candidate, select by pure weakness and validation-gated weakness.
- Gates/verifiers: deterministic seed; `validated_weakness` should reject the broad excluder and recover high Jaccard; pure weakness should still fail in the same run.
- Known limitations: the validation gate uses additional labeled evidence from the same target distribution; this is verifier-assisted weakness, not unsupervised weakness.

Action class:

- Retrieval/search/discovery: search with a small regime repair.
- Why: the run adds a verifier operation inside the existing synthetic schema rather than a new artifact class.

Experiment:

- Manifest/report paths: this file plus local raw JSON in `artifacts/`.
- Positive targets: `validated_weakness` should outperform pure weakness under broad-excluder stress.
- Negative controls: pure weakness should continue choosing the broad excluder.
- Stress tests: over-broad training-consistent candidate plus withheld negative observations.

Gate:

- Acceptance rule: validated weakness mean Jaccard >= 0.90; pure weakness mean Jaccard <= 0.60; validated broad-excluder rate <= 0.05.
- Withheld/rejected rule: if validated weakness also picks the broad excluder, the verifier is too weak; if pure weakness no longer fails, the stress condition changed.

Results:

- Accepted artifacts: this stress summary.
- Rejected or withheld artifacts: raw JSON remains local-only in `artifacts/`.
- Key metrics: validated weakness Jaccard 1.0000; pure weakness Jaccard 0.5246; validated broad-excluder rate 0.0.
- Variance or ablation: not yet run across seeds/features.

Residual content:

- Explained by old regime: withheld negative examples reject candidates that simply exclude the observed negatives.
- New content outside old regime: weakness should be treated as a selection pressure after validity gates, not a standalone rule.
- Retractions or supersessions: update the working claim to "maximize weakness among candidates that survive explicit verifiers."

Next move: run seed/feature sweeps, then port the benchmark to text/classification prompts.

