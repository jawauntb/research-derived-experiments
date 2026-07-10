# E2/E3 Rank-Normalized Patch Follow-up

Date: 2026-07-10.  
Pre-registration:
`papers/commitment_surface/e2_e3_rank_normalized_patch_preregistration_2026-07-10.md`.

## Result

**Strict verdict: PASS.** The compatibility-aligned activation subspace has a
positive, group-specific, width-stable causal effect after normalizing by the
realized removed between-orbit spectral mass.

| Width | Arm B CE / mass | Arm C CE / mass | B wrong-subspace CE / mass | B − C | B true − wrong |
|---:|---:|---:|---:|---:|---:|
| 96 | 1.119 | 0.159 | 0.0010 | +0.961 | +1.118 |
| 128 | 0.868 | 0.174 | 0.0009 | +0.694 | +0.867 |

Width-128 retains **0.775** of the width-96 Arm B effect, above the frozen
0.50 gate. All twelve Arm B cells at each width reach OOD accuracy 1.000.

## Frozen gates

- Arm B positive at both widths: **PASS**.
- Arm B − Arm C ≥ +0.02 at both widths: **PASS**.
- Arm B true compatibility subspace exceeds its `a`-only wrong-subspace
  control at both widths: **PASS**.
- Width-128 retains at least 50% of width-96: **PASS** (77.5%).

## Interpretation

The earlier fixed-top-k collapse was a measurement-scaling problem in this MLP
regime. A minimum-rank SVD subspace explaining at least 50% of between-orbit
activation mass recovers a large causal effect at both widths while the
matched wrong-subspace effect remains approximately zero. This upgrades the
E2/E3 localization claim from preliminary to supported **for small modular
MLPs**.

It does not establish that the same subspace construction localizes a
generator in Pythia or language. The E5 Pythia experiment uses a separate
LoRA spectral-mass intervention and retains its own claim boundary.

## Reproduction

Run `experiments.commitment_surface.e2_e3_neural_sweep` once per width with:

```bash
--moduli 17,19,23 --train-fracs 0.5 --seeds 4 --selector-pool 4 \
--epochs 1000 --depth 2 --aug-orbit-size 4 --top-k-patch 16 \
--subspace-mass-fraction 0.5 --hidden-width {96|128}
```

Detailed per-cell artifacts:

- `e2_e3_rank_patch_width96.{json,md}`
- `e2_e3_rank_patch_width128.{json,md}`
