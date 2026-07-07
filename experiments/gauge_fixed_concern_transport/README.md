# Gauge-Fixed Concern Transport Experiments

Synthetic empirical gates for the Gauge-Fixed Transport of Concern paper.

## Local Smoke

```bash
python -m experiments.gauge_fixed_concern_transport.core \
  --preset smoke \
  --out artifacts/gauge_fixed_concern_transport/smoke_suite.json

python -m experiments.gauge_fixed_concern_transport.summarize \
  --in artifacts/gauge_fixed_concern_transport/smoke_suite.json \
  --out experiments/gauge_fixed_concern_transport/results/gfc_smoke_suite_2026_07_07.md
```

## Modal L4 Full Suite

The Modal runner uses `gpu="L4"`, `max_containers=64`, and refuses to dispatch
if the conservative timeout-based cost estimate exceeds `--budget-usd`.

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/gauge_fixed_concern_transport/modal_l4_suite.py \
  --preset full \
  --seeds 64 \
  --budget-usd 250 \
  --out artifacts/gauge_fixed_concern_transport/l4_full_suite.json
```

## Allowed Claim

Passing this suite supports a bounded claim: synthetic L4 empirical validation
of the bridge theorem's measurement obligations. It does not validate human,
neural, biological, or foundation-model generality.
