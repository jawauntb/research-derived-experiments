# Ecological Compiler Study I Results

**Verdict: REJECTED at the descriptive claim tier.**

Cross-sectional association only; no causal, nutritional, neurobiological, genetic, or Europe-specific superiority inference.

## Gate ledger

| Gate | Verdict |
|---|---|
| EC_G0_PROVENANCE | PASS |
| EC_G1_DATA_INTEGRITY | PASS |
| EC_G2_ADJUSTED_ASSOCIATION | FAIL |
| EC_G3_COASTAL_SEPARATION | FAIL |
| EC_G4_SUBSISTENCE_SPECIFICITY | PASS |
| EC_G5_COMPILER_PATTERN | FAIL |
| EC_G6_TRANSPORT | FAIL |
| EC_G7_ORDINAL_STABILITY | PASS |

## Primary estimates

| Model | n | Fishing coefficient | Standardized coefficient | AIC |
|---|---:|---:|---:|---:|
| m0 | 1155 | -0.3345 | -0.5838 | 2932.32 |
| m1 | 1145 | 0.2585 | 0.4468 | 2468.82 |
| m1_common_m2_sample | 467 | 0.2665 | 0.4800 | 962.76 |
| m2 | 467 | 0.2674 | 0.4816 | 905.29 |

## Dependence and null checks

- Language-family block 95% interval: `[-0.15459664882665117, 0.47762719869056497]` (300/300 fits).
- Spatial-block 95% interval: `[-0.06051727862139018, 0.43636016800260097]` (300/300 fits).
- Within-macroregion permutation p-value: `0.001996007984031936` (500/500 fits).

## Compiler-pattern check

On the common M2 sample, the fishing coefficient changed from `0.2665` to `0.2674`. Proportional attenuation was `-0.0031867500999664955` and the M2 minus M1 AIC change was `-57.47`.

## Interpretation boundary

EA003 measures dependence on fishing, shellfishing, and large aquatic animals. It does not measure vitamin D, omega-3 status, dopamine, cognition, seafaring, or trade-network position. EA033 is an ordinal coding of jurisdictional levels, not a scalar measure of civilizational worth. Failed gates remain failures.
