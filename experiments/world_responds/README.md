# world_responds

Suite C world-change re-engagement workflows. The package contains the original
deterministic policy benchmark, Modal dispatch, neural transfer, teacher-free
inquiry, and source-ablation transfer. Existing 2026-07-06 results are immutable.

## M4 component factorial

The commitment-surface M4 follow-up intervenes inside the existing
`burst_then_refractory` policy; it is not a replacement simulator. Detect and
the eight-probe saturation quota stay fixed while all eight settings of
allocate, cool, and reopen are crossed over eight paired seeds. The original
C1–C6 controls and per-seed matched-random budgets are rerun unchanged.

Pre-registration:
[`suite_c_factorial_ablation_preregistration_2026_07_09.md`](suite_c_factorial_ablation_preregistration_2026_07_09.md).

```bash
python3 -m experiments.world_responds.suite_c_factorial_ablation --seeds 20260709,20261712,20262715,20263718,20264721,20265724,20266727,20267730 --out artifacts/world_responds/suite_c_factorial_ablation_2026_07_09.json --summary-json experiments/commitment_surface/results/m4_suite_c_factorial_ablation_2026_07_09.json --summary-md experiments/commitment_surface/results/m4_suite_c_factorial_ablation_2026_07_09.md
```

The command is deterministic and idempotent: raw paired rows remain under the
gitignored `artifacts/` tree, while public-safe summaries are rewritten only
when bytes change.

**Strict verdict: FAIL.** The complete loop passes 8/8 and transported controls
pass. Removing reopen fails 8/8; removing allocate or cool still passes 8/8.
Terminal main effects are 0.0, 0.0, and +1.0 respectively, and all terminal
interaction contrasts are 0.0. Allocation improves selectivity and probe cost
without becoming necessary at the current threshold; the cooldown is inert in
this schedule. See
[`m4_suite_c_factorial_ablation_2026_07_09.md`](../commitment_surface/results/m4_suite_c_factorial_ablation_2026_07_09.md).
