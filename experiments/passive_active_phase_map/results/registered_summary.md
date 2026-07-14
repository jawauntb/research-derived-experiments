# Passive-to-Active Coupling Phase Map

## Scope

This is a controlled local-CPU mechanism diagnostic using a synthetic bottleneck
autoencoder plus action head. It is not evidence of a dynamical attractor, biological
criticality, or foundation-model generality.

Raw per-seed phase, path, and retention cells are generated under
`artifacts/passive_active_phase_map/` and are intentionally not committed.

## Frozen Gate Verdicts

- Bifurcation: **FAIL** -> `bifurcation_not_supported`
- Hysteresis: **PASS** -> `hysteresis`
- Overall: **`bifurcation_not_supported_with_path_dependence`**

A failed bifurcation gate is reported as bifurcation not supported, not as positive proof
of a smooth crossover. A failed hysteresis gate is reported as no registered hysteresis;
neither negative result is upgraded into its alternative by visual inspection.

## Transition Model Comparison

| Order parameter | Preferred | Segmented advantage | Critical estimates |
| --- | --- | ---: | --- |
| `causal_specific_effect` | segmented | 0.112 | linear=0.150, tanh=0.150 |
| `perturbation_failure_rate` | smooth | 0.095 | linear=0.150, tanh=0.150 |
| `viability_buffer` | smooth | 0.084 | linear=0.150, tanh=0.150 |
| `geometry_gap` | smooth | -0.000 | linear=0.450, tanh=0.450 |
| `return` | smooth | 0.054 | linear=0.150, tanh=0.150 |

## Bifurcation Gate Components

- Coverage (>=2 architectures, >=5 seeds): PASS
- Segmented metrics (need >=2): `['causal_specific_effect']`
- Critical stability: FAIL
- Co-located order parameters: FAIL

## Hysteresis Gate Components

- Independent bootstrap unit: seed cluster; both architecture rows remain grouped
- Forward/reverse total budgets matched: PASS
- Continuation loop area: `0.0447` (gate >=0.02)
- Contiguous significant couplings: `6` (gate >=2)
- Survives washout: PASS
- Reinitialization control clear: PASS

## Retention

- Median half-life: `not observed` updates
- Fraction with observed half-life: `0.000`

## Aggregate Coupling Curves

### linear

| Coupling | Causal specificity | Perturbation failure | Buffer | Geometry gap | Return |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.00 | -0.212 | 0.040 | -0.299 | 0.709 | -0.275 |
| 0.10 | 0.274 | 0.611 | 0.479 | 0.710 | 0.435 |
| 0.20 | 0.276 | 0.649 | 0.514 | 0.715 | 0.498 |
| 0.30 | 0.278 | 0.668 | 0.529 | 0.724 | 0.521 |
| 0.40 | 0.282 | 0.659 | 0.540 | 0.736 | 0.527 |
| 0.50 | 0.285 | 0.660 | 0.550 | 0.752 | 0.542 |
| 0.60 | 0.285 | 0.661 | 0.561 | 0.771 | 0.546 |
| 0.70 | 0.286 | 0.656 | 0.571 | 0.793 | 0.558 |
| 0.80 | 0.289 | 0.649 | 0.581 | 0.817 | 0.573 |
| 0.90 | 0.294 | 0.643 | 0.591 | 0.843 | 0.583 |
| 1.00 | 0.295 | 0.636 | 0.601 | 0.871 | 0.590 |

### tanh

| Coupling | Causal specificity | Perturbation failure | Buffer | Geometry gap | Return |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.00 | 0.111 | 0.296 | 0.175 | 0.639 | 0.175 |
| 0.10 | 0.158 | 0.421 | 0.317 | 0.643 | 0.304 |
| 0.20 | 0.237 | 0.642 | 0.502 | 0.650 | 0.467 |
| 0.30 | 0.232 | 0.649 | 0.525 | 0.661 | 0.477 |
| 0.40 | 0.245 | 0.655 | 0.538 | 0.674 | 0.475 |
| 0.50 | 0.257 | 0.667 | 0.550 | 0.691 | 0.490 |
| 0.60 | 0.265 | 0.666 | 0.563 | 0.710 | 0.498 |
| 0.70 | 0.278 | 0.661 | 0.575 | 0.731 | 0.512 |
| 0.80 | 0.279 | 0.657 | 0.587 | 0.755 | 0.537 |
| 0.90 | 0.275 | 0.644 | 0.600 | 0.781 | 0.552 |
| 1.00 | 0.292 | 0.638 | 0.612 | 0.808 | 0.571 |

