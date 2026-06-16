# Concerned Syntax Modal Sweep

Date: 2026-06-16

Manifest: 5 seeds x 1000 trials = 5000 shape trials.

Remote command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/concerned_syntax/modal_concerned_syntax_sweep.py \
  --trials 1000
```

## Gate Summary

| Selector | Parse high | Action | Subtree | High probe | Low probe | Mean regret | Gate pass rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| compression_proxy | 0.560 | 0.891 | 0.583 | 0.000 | 0.000 | 0.048 | 0.000 |
| concerned_syntax | 1.000 | 1.000 | 0.808 | 1.000 | 0.000 | 0.003 | 1.000 |
| flat_valence | 0.000 | 0.876 | 0.503 | 0.000 | 0.000 | 0.066 | 0.000 |
| null_policy | 0.560 | 0.891 | 0.583 | 0.000 | 0.000 | 0.048 | 0.000 |
| uncertainty_only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |

## Interpretation

`concerned_syntax` is accepted when it passes on every seed while the anti-cheat controls fail for different reasons: flat valence and compression do not recover causal constituency, and uncertainty-only inquiry over-probes low-concern ambiguity.

Accepted selectors: `concerned_syntax`

Raw JSON remains local under `artifacts/concerned_syntax/`.
