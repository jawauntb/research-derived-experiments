# E7 Selective Subspace — Confirmatory Result

Date: 2026-07-13.
Pre-registration: `papers/commitment_surface/e7_selective_subspace_continual_learning_preregistration_2026-07-13.md`.

Status: **INVALID**.

Streams: 32; checkpoints: 128; earlier-task stability rows: 192.

## Integrity

- seed: **PASS**
- sequential: **PASS**
- protected_mass: **PASS**
- budget: **FAIL**

## Valid-stream aggregate

| Width | Arm | Valid streams | Retained OOD | Earlier patch-CE / mass | Final-task OOD | Effective rank [95% CI] | Dead units [95% CI] |
|---:|---|---:|---:|---:|---:|---:|---:|
| 96 | P_none | 1 | 0.5199 | -2.1812 | 1.0000 | 7.68 [7.68, 7.68] | 0.0271 [0.0271, 0.0271] |
| 96 | P_ewc | 1 | 0.5199 | -2.3407 | 1.0000 | 7.96 [7.96, 7.96] | 0.0104 [0.0104, 0.0104] |
| 96 | P_sub | 1 | 0.5199 | -1.7244 | 1.0000 | 8.09 [8.09, 8.09] | 0.0125 [0.0125, 0.0125] |
| 96 | P_wrong | 1 | 0.5199 | -2.1724 | 1.0000 | 7.96 [7.96, 7.96] | 0.0188 [0.0188, 0.0188] |
| 128 | P_none | 2 | 0.5213 | -0.6629 | 1.0000 | 10.71 [10.04, 11.39] | 0.0723 [0.0663, 0.0782] |
| 128 | P_ewc | 2 | 0.5213 | -0.6960 | 1.0000 | 10.73 [9.79, 11.66] | 0.0531 [0.0380, 0.0683] |
| 128 | P_sub | 2 | 0.5213 | -0.8211 | 1.0000 | 10.85 [10.51, 11.19] | 0.0461 [0.0374, 0.0548] |
| 128 | P_wrong | 2 | 0.5213 | -0.6114 | 1.0000 | 10.98 [10.28, 11.68] | 0.0355 [0.0296, 0.0415] |

## Frozen gates

Strict verdict: **INVALID — NO SCIENTIFIC VERDICT**.

The original shared-barrier makespan made the four arm times nearly identical by construction. Re-auditing the recorded per-arm `median_step_seconds × optimizer_steps` estimates finds 6 of 32 matched groups above the frozen 2% limit (maximum 8.53%). The seed, sequential-exposure, and protected-mass gates pass, but the budget failure kills the confirmatory run.

G1–G4 are not evaluated. Any mechanism or frontier margins from these cells are diagnostic only and cannot accept or reject `H_subspace`.

## Integrity and provenance

- All 32 streams, 128 task checkpoints, and 192 earlier-task evaluations are present.
- Seed collision, matched initialization/split/augmentation, sequential exposure, and exact 0.50 protected mass checks pass.
- Local raw artifact SHA-256: `9a3e9c95f08ccf6fbb6ae13900849abc928c19be31204abb05a169b3b3ceaa0d`.

## Reproduction

Run the frozen pilot, then the locked confirmatory grid:

```bash
.venv/bin/python -m experiments.commitment_surface.e7_selective_subspace \
  --run-kind pilot --out artifacts/commitment_surface/e7_pilot_final_2026_07_13.json

.venv/bin/python -m experiments.commitment_surface.e7_selective_subspace \
  --run-kind confirmatory \
  --pilot-result artifacts/commitment_surface/e7_pilot_final_2026_07_13.json \
  --out artifacts/commitment_surface/e7_confirmatory_2026_07_13.json \
  --public-json experiments/commitment_surface/results/e7_selective_subspace_2026_07_13.json \
  --summary experiments/commitment_surface/results/e7_selective_subspace_2026_07_13.md
```

Raw checkpoint rows stay under gitignored `artifacts/`.
