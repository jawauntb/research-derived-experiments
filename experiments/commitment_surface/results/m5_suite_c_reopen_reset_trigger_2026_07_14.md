# M5 Suite C Reopen/Reset Trigger Comparison (2026-07-14)

**Strict gate verdict: FAIL.**
Claim level: failed diagnostic gate; trigger superiority remains a hypothesis.

The 2026-07-14 pre-run implementation contract transparently repaired
underspecified trigger, budget-routing, latency, and false-calm details
before any M5 outcome cell was executed.

## Exact run config

```bash
uvx --python 3.12 --with numpy python -m experiments.world_responds.suite_c_reopen_reset_trigger --seeds 20260709,20261712,20262715,20263718,20264721,20265724,20266727,20267730 --out artifacts/world_responds/m5_suite_c_reopen_reset_trigger_2026_07_14.json --summary-json experiments/commitment_surface/results/m5_suite_c_reopen_reset_trigger_2026_07_14.json --summary-md experiments/commitment_surface/results/m5_suite_c_reopen_reset_trigger_2026_07_14.md
```

Paired seeds: `[20260709, 20261712, 20262715, 20263718, 20264721, 20265724, 20266727, 20267730]`.
Calibration receipt: `741efa930978a0de622b4fbea4deed82e250535b0b0b37ecaf3f9043136d992b`.
Ignored raw payload SHA-256: `ec666ddb098579897974765c2f5431e0a0c636092f928f63102be85cca2899cc`.
Pre-registration: `experiments/world_responds/suite_c_reopen_reset_trigger_preregistration_2026-07-13.md`.
Implementation contract: `experiments/world_responds/suite_c_reopen_reset_trigger_implementation_contract_2026-07-14.md`.

## Integrity replacement

Two pre-fix raw payloads were invalidated after review found branch-dependent
RNG consumption in the coupled no-change run:
`cf6f640da6d2b37154d0371255730f9f8d28a39a2cad63de61826f4dd02818c1, bd94aedab53b51d0a67668efeaca0ca610a9b0cbbf45459f341813c862bfb0e0`.
The replacement pre-indexes every variate; it does not change the frozen
arms, seeds, thresholds, probe budgets, or F0–F5 gates.

## Arm summaries

| arm | pass | latency | false reopen | selectivity | reopen ratio | final MAE | probes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| T_commit | 1.000 | 0.000 | 0.000 | 3.800 | 16.667 | 0.112 | 27.1 |
| T_util | 0.000 | 1.000 | 0.656 | 3.800 | 9.375 | 0.257 | 27.1 |
| T_norm | 0.000 | 12.000 | 0.000 | 3.800 | 0.000 | 0.553 | 27.1 |
| T_periodic | 1.000 | 0.000 | 0.667 | 3.800 | 16.667 | 0.113 | 27.1 |
| T_none | 0.000 | 12.000 | 0.000 | 3.800 | 0.000 | 0.559 | 27.1 |

## Frozen gates

- **F0_integrity: PASS.**
- **F1_commit_8_of_8: PASS.**
- **F2_latency_dominance: FAIL.**
- **F3_specificity: FAIL.**
- **F4_joint_non_domination: PASS.**
- **F5_none_floor: PASS.**

## Interpretation boundary

The strict verdict is determined only by F0–F5. Failures are not
upgraded by directional metrics. This finite Suite C diagnostic does
not establish a neural continual-learning result.

## Rejected alternatives

- post-outcome trigger threshold tuning.
- unequal actual probe counts.
- filler probes into closed affected buckets.
- impulse-count false-reopen metric.
- aggregate-only unpaired contrasts.
