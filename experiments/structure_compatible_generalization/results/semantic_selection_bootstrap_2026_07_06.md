# Phase 6 Semantic Selection Bootstrap

Date: 2026-07-06

## Setup

- Bootstrap unit: `selection_zoo`
- Zoos: 120
- Selection records: 840
- Bootstrap reps: 1000

## Metrics

| Metric | Point | 95% CI |
| --- | ---: | ---: |
| `learned_selected_ood` | 0.978 | [0.973, 0.983] |
| `random_selected_ood` | 0.919 | [0.915, 0.924] |
| `id_selected_ood` | 0.919 | [0.915, 0.924] |
| `train_selected_ood` | 0.919 | [0.915, 0.924] |
| `wrong_selected_ood` | 0.751 | [0.750, 0.753] |
| `true_selected_ood` | 0.993 | [0.990, 0.995] |
| `learned_regret` | 0.014 | [0.011, 0.018] |
| `learned_lift_vs_random` | 0.059 | [0.052, 0.065] |
| `learned_lift_vs_id` | 0.059 | [0.052, 0.065] |
| `learned_lift_vs_wrong` | 0.227 | [0.221, 0.233] |
| `accepted_rate` | 1.000 | [1.000, 1.000] |

## Interpretation

For the regenerated Phase 6 semantic-selection payload, learned compatibility selects higher OOD candidates than random, train, ID, and wrong-compatibility selectors under a zoo-level bootstrap.
