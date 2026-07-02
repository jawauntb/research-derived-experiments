# Paper B Moved-Location Metric-Deformation Sweep — Modal Results (2026-07-02)

Pre-registration: [papers/grid_cell_weakness/preregistration.md](../../../papers/grid_cell_weakness/preregistration.md),
frozen addendum "Paper B Moved-Location Metric-Deformation Gate" (2026-07-02). Runner:
`experiments/grid_cell_weakness/modal_reward_location_sweep.py`. Backend: Modal
H200/H100 workers. Raw JSON is gitignored; combined artifact:
`artifacts/grid_cell_weakness/reward_location_sweep_2026_07_02_combined.json`.

Manifest: 3 architectures × 9 reward locations. Observed seed counts by architecture: jepa=64, rnn=64, transformer=64. Each seed shard trains one matched uniform-control model and one reward model per registered location for each architecture present in that shard.

## Primary Gate Verdict

Report precision target: bootstrap SE <= 0.02. The frozen pre-registration also recorded a stricter adaptive target of <= 0.01; that stricter audit is reported below rather than silently relabeled.

| Architecture | lift z | specificity z | rank | peak error | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| jepa | +0.6847 [+0.6476, +0.7228], SE=0.0193, n=576 | +0.9162 [+0.8890, +0.9425], SE=0.0138, n=576 | 0.832 | 0.205 | pass |
| rnn | +1.2013 [+1.1846, +1.2179], SE=0.0085, n=576 | +1.3572 [+1.3372, +1.3774], SE=0.0103, n=576 | 0.930 | 0.069 | pass |
| transformer | +1.9507 [+1.9170, +1.9843], SE=0.0173, n=576 | +2.0053 [+1.9883, +2.0218], SE=0.0086, n=576 | 0.928 | 0.082 | pass |

Architecture-balanced pooled lift: +1.2789 [+1.2610, +1.2965], SE=0.0091, n=1728.
Architecture-balanced pooled specificity: +1.4262 [+1.4139, +1.4391], SE=0.0064, n=1728.

## Strict 1% Precision Audit

| Architecture | <=1% lift SE | <=1% specificity SE | Directional CIs positive | Strict 1% audit |
| --- | ---: | ---: | ---: | --- |
| jepa | False | False | True | fail |
| rnn | True | False | True | fail |
| transformer | False | True | True | fail |

## Companion Area-Density Diagnostics

| Architecture | area lift z | area specificity z | area rank |
| --- | ---: | ---: | ---: |
| jepa | +0.0871 [+0.0334, +0.1439], SE=0.0283, n=576 | +0.3702 [+0.3364, +0.4035], SE=0.0174, n=576 | 0.617 |
| rnn | +1.1867 [+1.1702, +1.2031], SE=0.0084, n=576 | +1.3393 [+1.3195, +1.3595], SE=0.0102, n=576 | 0.930 |
| transformer | +1.9457 [+1.9118, +1.9793], SE=0.0173, n=576 | +2.0072 [+1.9902, +2.0236], SE=0.0085, n=576 | 0.928 |

## Reading

The Paper B primary observable is the original neighbor-stretch metric density: mean latent
displacement per unit physical displacement. Area density is reported only as a companion
rate-distortion diagnostic.

Interpret the claim exactly as preregistered: architectures pass only when the bootstrap
intervals for both control-subtracted lift and moved-location specificity exclude zero on
the positive side, the primary standard errors are at or below the stated report target (0.02 here), and the reward-location rank is above chance. The frozen stricter
1% precision audit is retained separately because the 2% threshold was accepted after the
first-wave results were visible. Failed architecture families must remain failed in the paper.
