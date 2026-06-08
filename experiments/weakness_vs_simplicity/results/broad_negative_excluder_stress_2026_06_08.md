# Broad Negative Excluder Stress Test

Date: June 8, 2026

Command:

```bash
python3 experiments/weakness_vs_simplicity/experiment.py --trials 500 --seed 7 --no-memorizer --include-broad-negative-excluder --out artifacts/weakness_vs_simplicity/broad_negative_excluder_stress.json
```

Raw artifacts:

- `artifacts/weakness_vs_simplicity/broad_negative_excluder_stress.json` (local-only, ignored)
- `artifacts/weakness_vs_simplicity/broad_negative_excluder_stress.stdout.json` (local-only, ignored)

## Manifest

- Features: 6
- Worlds: 64
- Trials: 500
- Positive observations per trial: 3
- Negative observations per trial: 3
- Seed: 7
- Base candidate rules: 72
- Memorizer included: no
- Broad negative excluder included: yes

## Summary

| Selector | Mean Jaccard | Mean Accuracy | Mean Form Length | Mean Weakness | Broad Excluder Rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Weakness | 0.5246 | 0.5469 | 9.0000 | 61.0000 | 1.0000 |
| Simplicity | 0.9560 | 0.9670 | 4.0000 | 32.0000 | 0.0000 |
| Random | 0.6543 | 0.7451 | 6.6500 | 37.0160 | 0.3440 |

## Discovery-Regime Audit

Question: does a pure weakness selector fail when the candidate vocabulary includes a training-consistent but unsafe broad hypothesis?

Current regime:

- Artifact types: Boolean worlds, candidate rule extensions, selector choices, Jaccard/accuracy metrics.
- Operations: generate target one-feature rule, sample observations, inject an over-broad candidate that excludes only observed negatives, select by weakness/simplicity/random.
- Gates/verifiers: deterministic seed; pure weakness should pick the broad excluder if the stress test is effective; simplicity should retain high Jaccard when the memorizer is absent.
- Known limitations: the broad excluder is hand-designed; it represents a verifier failure, not a realistic learned hypothesis class yet.

Action class:

- Retrieval/search/discovery: search with residual.
- Why: the run explores a new failure mode inside the current synthetic schema and exposes a missing verifier.

Experiment:

- Manifest/report paths: this file plus local raw JSON in `artifacts/`.
- Positive targets: simplicity should stay near the true reusable rule in the no-memorizer condition.
- Negative controls: the broad excluder should make pure weakness overgeneralize.
- Stress tests: over-broad training-consistent candidate.

Gate:

- Acceptance rule: weakness broad-excluder rate >= 0.95 and weakness mean Jaccard <= 0.60; simplicity mean Jaccard >= 0.90.
- Withheld/rejected rule: if weakness does not pick the broad candidate, the stress candidate is not actually broad enough; if simplicity also collapses, the stress confounds broadness with shortness.

Results:

- Accepted artifacts: this stress summary.
- Rejected or withheld artifacts: raw JSON remains local-only in `artifacts/`.
- Key metrics: weakness broad-excluder rate 1.0; weakness Jaccard 0.5246; simplicity Jaccard 0.9560.
- Variance or ablation: not yet run across seeds/features.

Residual content:

- Explained by old regime: pure weakness chooses the largest compatible extension.
- New content outside old regime: raw weakness needs a validity gate; preserving compatible futures is not enough when a candidate can satisfy observations by refusing to learn the boundary.
- Retractions or supersessions: weaken the initial informal claim from "weakness wins" to "weakness helps when the candidate class excludes degenerate broad hypotheses or when paired with a verifier."

Next move: implement and test a validity-gated weakness selector.

