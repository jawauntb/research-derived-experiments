# Gauge-Fixed Concern Transport Provenance

- Plan: `docs/plans/2026-07-07-002-feat-gfc-modal-experiments-plan.md`
- Audit: `docs/gauge_fixed_concern_transport_experiment_audit.md`
- Local smoke command: `python -m experiments.gauge_fixed_concern_transport.core --preset smoke --out artifacts/gauge_fixed_concern_transport/smoke_suite.json`
- Committed smoke payload: `experiments/gauge_fixed_concern_transport/results/gfc_smoke_suite_2026_07_07.json`
- Modal budget dry run:

```bash
uvx --python 3.12 --from modal modal run \
  experiments/gauge_fixed_concern_transport/modal_l4_suite.py \
  --preset full \
  --seeds 64 \
  --budget-usd 250 \
  --dry-run-budget
```

- Dry-run app id: `ap-aJ3jMVo96u3f5XMyxeTceu`
- Dry-run decision: `PASS`, with conservative timeout cost `$63.94 / $250.00`
- Modal full command:

```bash
uvx --python 3.12 --from modal modal run \
  experiments/gauge_fixed_concern_transport/modal_l4_suite.py \
  --preset full \
  --seeds 64 \
  --budget-usd 250 \
  --out artifacts/gauge_fixed_concern_transport/l4_full_suite.json
```

- Full app id: `ap-GFeFvaDvcvaKGOjWyeciX8`
- Full result: `PASS`, 320/320 cells complete, all visible workers reported `NVIDIA L4`.
- Committed full payload: `experiments/gauge_fixed_concern_transport/results/gfc_l4_suite_2026_07_07.json`
- Committed full report: `experiments/gauge_fixed_concern_transport/results/gfc_l4_suite_2026_07_07.md`

The allowed claim is synthetic Modal L4 empirical validation only. Human, neural,
biological, and foundation-model generality remain future work.
