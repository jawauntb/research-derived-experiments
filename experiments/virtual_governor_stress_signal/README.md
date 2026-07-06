# Virtual-Governor Stress Signal

This package turns the virtual-governor framing into a bounded architecture
diagnostic. Small neural policies act in a finite controlled state whose global
target shifts during rollout. The main ablation asks whether a live global
stress signal, translated into local policy features, improves action recovery.

Run the Modal L4 sweep and artifact builder:

```bash
uvx --python 3.12 --from modal modal run \
  experiments/virtual_governor_stress_signal/modal_l4_sweep.py \
  --seeds 8 --budget-usd 50
```

Regenerate artifacts from an existing payload:

```bash
uvx --python 3.12 --from modal modal run \
  experiments/virtual_governor_stress_signal/modal_l4_sweep.py \
  --artifacts-only \
  --artifact-input artifacts/virtual_governor_stress_signal/l4_sweep.json
```

Run Modal quality gates:

```bash
uvx --python 3.12 --from modal modal run \
  experiments/virtual_governor_stress_signal/modal_l4_sweep.py \
  --quality-only
```
