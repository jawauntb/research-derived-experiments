# Phase 6 Real-Model Validation

Phase 6 replaces the Phase 5 proxy harnesses with actual public open models:

- decoder language models for hidden-state geometry plus help-vs-wait logprob margins;
- frozen sentence encoders for post-hoc value-weighted metric deformation.

The allowed claim is bounded. These are actual open-model measurements, not
human behavioral data and not proof that a foundation model has learned concern.

## Run

Budget dry-run:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/phase6_real_model_validation/modal_l4_suite.py \
  --preset full --budget-usd 1000 --dry-run-budget
```

Full L4 suite:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/phase6_real_model_validation/modal_l4_suite.py \
  --preset full --budget-usd 1000 \
  --out artifacts/phase6_real_model_validation/l4_full_suite.json
```

Summarize and render:

```bash
python3 experiments/phase6_real_model_validation/summarize.py \
  --in experiments/phase6_real_model_validation/results/l4_full_suite_2026_07_06.json \
  --out experiments/phase6_real_model_validation/results/phase6_real_model_suite_2026_07_06.md

python3 scripts/build_phase6_real_model_validation_pdf.py \
  --in experiments/phase6_real_model_validation/results/l4_full_suite_2026_07_06.json
```
