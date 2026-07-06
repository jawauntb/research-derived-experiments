# From Proxy Transport to Open Models

Phase 6 is the actual-model validation tier following Phase 5. It replaces proxy
harnesses with public decoder language models and frozen sentence encoders,
while preserving predeclared gates, controls, budget accounting, and archived
outputs.

## Run Summary

The full Modal L4 run completed on 2026-07-06 with five model cells under the
`$1000` cap. The conservative timeout-based estimate was `$1.998`; the observed
model rows each completed in about 16-30 seconds.

Overall gate status: **PASS**.

| Track | Status | Key result |
| --- | --- | --- |
| Open LM action coupling | PASS | Three public decoder LMs ran. Mean geometry-action `r=0.340`, mean held-out help-vs-wait margin lift `1.064`, and mean margin AUC `0.688`. Qwen2.5-0.5B-Instruct carried the strongest signal; Pythia-70M remained weak/control-like. |
| Frozen encoder metric deformation | PASS | Two public encoders ran. Raw neighbor precision was already at `1.000`, so the gate used held-out value-margin lift: deformed margin lift `0.409` versus random-label lift `0.008`, transfer AUC `1.000`, and off-target drift `0.000`. |

## Claim Boundary

The allowed claim is narrow: actual open-model logprob/hidden-state evidence and
frozen-encoder metric-deformation evidence. The suite does not claim human
behavioral validity, model agency, or trained concern in the frozen encoders.

## Rebuild

```bash
python3 scripts/build_phase6_real_model_validation_pdf.py \
  --in experiments/phase6_real_model_validation/results/l4_full_suite_2026_07_06.json
```
