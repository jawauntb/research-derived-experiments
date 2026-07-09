# E1 — Unequal-Consequence Concern-Weighted Selector

Cells: 96

## Selector accuracies on the well-specified deployment slice

| Selector | Mean | 95% CI |
|---|---:|---|
| Unweighted weakness | 0.570 | [0.539, 0.601] |
| Concern-weighted (well-spec) | 0.814 | [0.806, 0.822] |
| Concern-weighted (misspec random) | 0.516 | [0.483, 0.549] |
| Train-loss selector | 0.310 | [0.286, 0.333] |
| Truth (upper bound) | 1.000 | [1.000, 1.000] |

## Gates

- Commitment-first pass (wellspec beats unweighted by ≥0.05): **True** (gap=0.244)
- Commitment-first pass (misspec matches unweighted within 0.05): **False** (gap=-0.054)

## Per-modulus breakdown

| Modulus | # cells | Unweighted | Wellspec | Misspec | Loss |
|---:|---:|---:|---:|---:|---:|
| 7 | 32 | 0.622 | 0.857 | 0.547 | 0.303 |
| 11 | 32 | 0.573 | 0.813 | 0.506 | 0.316 |
| 13 | 32 | 0.516 | 0.773 | 0.494 | 0.310 |
