# Suite C Allocate × Cool × Reopen Factorial (2026-07-09)

**Strict gate verdict: FAIL.**
Claim level: failed diagnostic gate; M4 remains a compression hypothesis.

## Exact run config

```bash
python3 -m experiments.world_responds.suite_c_factorial_ablation --seeds 20260709,20261712,20262715,20263718,20264721,20265724,20266727,20267730 --out artifacts/world_responds/suite_c_factorial_ablation_2026_07_09.json --summary-json experiments/commitment_surface/results/m4_suite_c_factorial_ablation_2026_07_09.json --summary-md experiments/commitment_surface/results/m4_suite_c_factorial_ablation_2026_07_09.md
```

Paired seeds: `[20260709, 20261712, 20262715, 20263718, 20264721, 20265724, 20266727, 20267730]`. Detect and saturate were frozen on.
The unmodified Suite C controls and per-seed matched-random budgets were rerun.

## Factorial cells

| allocate | cool | reopen | terminal pass | re-engage | selectivity | reopen ratio | final MAE | probes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 0.000 | 11.135 | 4.125 | 0.000 | 0.550 | 19.1 |
| 0 | 0 | 1 | 1.000 | 11.135 | 4.125 | 16.667 | 0.113 | 27.1 |
| 0 | 1 | 0 | 0.000 | 11.135 | 4.125 | 0.000 | 0.550 | 19.1 |
| 0 | 1 | 1 | 1.000 | 11.135 | 4.125 | 16.667 | 0.113 | 27.1 |
| 1 | 0 | 0 | 0.000 | 11.135 | 17.188 | 0.000 | 0.550 | 15.1 |
| 1 | 0 | 1 | 1.000 | 11.135 | 17.188 | 16.667 | 0.113 | 23.1 |
| 1 | 1 | 0 | 0.000 | 11.135 | 17.188 | 0.000 | 0.550 | 15.1 |
| 1 | 1 | 1 | 1.000 | 11.135 | 17.188 | 16.667 | 0.113 | 23.1 |

## Primary factorial effects (terminal pass)

| contrast | effect | paired bootstrap 95% CI |
| --- | ---: | ---: |
| allocate | +0.000 | [+0.000, +0.000] |
| cool | +0.000 | [+0.000, +0.000] |
| reopen | +1.000 | [+1.000, +1.000] |
| allocate_x_cool | +0.000 | [+0.000, +0.000] |
| allocate_x_reopen | +0.000 | [+0.000, +0.000] |
| cool_x_reopen | +0.000 | [+0.000, +0.000] |
| allocate_x_cool_x_reopen | +0.000 | [+0.000, +0.000] |

## Single-removal necessity

| removed stage | knockout pass rate | full minus knockout | gate |
| --- | ---: | ---: | :---: |
| allocate | 1.000 | +0.000 | FAIL |
| cool | 1.000 | +0.000 | FAIL |
| reopen | 0.000 | +1.000 | PASS |

## Transported controls

- Reference C1–C6 suite: PASS.
- False-calm control no-false-calm rate: 0.000 (rejected).
- Headline vs matched-random selectivity: 17.188 vs 0.771; per-seed budgets exact: True.

## Frozen gate verdicts

- **F0_integrity: PASS.**
- **F1_full_loop_replication: PASS.**
- **F2_single_removal_necessity: FAIL.**
- **F3_main_effects: FAIL.**
- **F4_interactions: PASS.**
- **F5_no_interaction_rescue: FAIL.**
- **F6_transported_controls: PASS.**

## Interpretation boundary

The strict verdict is determined only by F0–F6. A failure remains a failure even when the complete policy or some directional contrasts pass.
This is finite-harness diagnostic evidence, not neural or external validation.

## Rejected alternatives

- new toy state machine.
- neural-transfer policy-learning confound.
- three single knockouts without the remaining factorial cells.
- aggregate-only unpaired reporting.
- post-result threshold retuning.
