# Virtual-Governor Stress-Signal L4 Suite

## Manifest

- **base_seed:** `20260706`
- **conditions:** `['reward_only', 'local_state', 'stale_governor', 'wrong_governor', 'virtual_governor']`
- **epochs:** `180`
- **eval_episodes:** `96`
- **eval_steps:** `72`
- **gpu:** `L4`
- **max_containers:** `24`
- **post_shift_window:** `16`
- **seeds_per_condition:** `8`
- **shift_period:** `18`
- **suite:** `virtual governor stress-signal diagnostic`
- **train_episodes:** `96`
- **train_steps:** `56`
- **budget:** 40 L4 cells, conservative $7.99 against $50.00

## Headline

The live virtual-governor condition achieved the strongest closed-loop stress control. The diagnostic isolates the architecture move: translate global constraint violation into local policy features.

Top condition: `virtual_governor` with global recovery score 0.843 and action accuracy 0.976.

## Condition Summary

| Condition | N | Action accuracy | Mean stress | Post-shift stress | Recovery rate | Recovery steps | Global recovery |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| reward only | 8 | 0.002 | 0.693 | 0.714 | 0.000 | 16.000 | 0.184 |
| local state proxy | 8 | 0.357 | 0.408 | 0.414 | 0.246 | 12.064 | 0.520 |
| stale governor memory | 8 | 0.615 | 0.274 | 0.353 | 0.950 | 11.476 | 0.678 |
| wrong stress signal | 8 | 0.352 | 0.410 | 0.412 | 0.249 | 12.030 | 0.517 |
| live virtual governor | 8 | 0.976 | 0.133 | 0.151 | 1.000 | 4.442 | 0.843 |

## Regime Audit

- Old regime: architecture laws were mostly inferred from concern, reafference, re-engagement, and long-horizon commitment surfaces.
- Transition: make the virtual-governor claim executable as a stress transduction ablation.
- Rejected alternatives: reward-only competence, local-state proxy, stale stress memory, and wrong stress signal.
- Residual finding: this is a finite synthetic closed-loop policy task, not evidence about biological virtual governors or subjective experience.
- Allowed claim: in this diagnostic, a live global-stress channel can be the load-bearing architecture feature for local action recovery after target shifts.

## Local Artifacts

- Paper: `papers/virtual_governor_stress_signal/paper.md`
- Figures: `papers/virtual_governor_stress_signal/figures/*.png`
