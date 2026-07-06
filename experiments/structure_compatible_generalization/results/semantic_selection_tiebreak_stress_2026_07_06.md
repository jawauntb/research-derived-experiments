# Phase 6 Semantic Selection Tie-Break Stress

Date: 2026-07-06

- Bootstrap unit: `selection_zoo`
- Bootstrap reps: 1000

| Tie mode | Learned OOD | Learned-random | Learned-ID | Learned-wrong | Accepted? |
| --- | ---: | ---: | ---: | ---: | --- |
| `mean_ties` | 0.978 [0.973, 0.983] | 0.059 [0.052, 0.065] | 0.059 [0.052, 0.065] | 0.227 [0.221, 0.233] | PASS |
| `worst_tie` | 0.954 [0.940, 0.967] | 0.204 [0.190, 0.217] | 0.204 [0.190, 0.217] | 0.203 [0.189, 0.216] | PASS |
| `random_tie` | 0.981 [0.974, 0.986] | 0.068 [0.050, 0.086] | 0.054 [0.036, 0.071] | 0.230 [0.222, 0.236] | PASS |

## Interpretation

Phase 6 learned compatibility remains stress-tested under mean-tie, worst-tie, and random-tie selector interpretations.
