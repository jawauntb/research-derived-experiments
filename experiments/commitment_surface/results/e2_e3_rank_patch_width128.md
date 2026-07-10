# E2 + E3 — Compatibility Augmentation vs Readout, with Patch-CE

Total cells trained: 48

## Per-arm summary (selected cell per (n, train_frac))

| Arm | Description | # sel | OOD acc (mean, 95%CI) | Patch-CE Δ | Subspace CE / mass | Wrong subspace CE / mass | Weakness |
|---|---|---:|---|---|---|---|---|
| A | Readout selector (no aug) | 3 | 0.000 [0.000, 0.000] | -0.327 [-0.591, -0.063] | -2.854 [-3.009, -2.698] | -5.216 [-5.944, -4.488] | 0.052 |
| B | Compat aug (true cyclic group) | 12 | 1.000 [1.000, 1.000] | 0.036 [0.024, 0.048] | 0.868 [0.792, 0.943] | 0.001 [0.001, 0.001] | 1.000 |
| C | Wrong-group aug | 12 | 0.107 [0.090, 0.123] | 0.004 [-0.001, 0.008] | 0.174 [0.148, 0.199] | -0.016 [-0.023, -0.009] | 0.052 |
| D | Loss selector (no aug) | 3 | 0.000 [0.000, 0.000] | -0.263 [-0.471, -0.055] | -3.131 [-3.597, -2.665] | -4.917 [-5.562, -4.272] | 0.052 |

## Discriminator gates

- **E2 pass — B beats A on OOD by ≥ 0.30:** **True** (gap = 1.000)
- **E2 pass — B beats A on Patch-CE Δ by ≥ 0.50:** **False** (gap = 0.362)
- **E3 pass — ρ(patch-CE, OOD) > ρ(weakness, OOD):** **True** (ρ_patch = 0.764 vs ρ_weakness = 0.663)
- **Rank-normalized patch — Arm B positive:** **True**
- **Rank-normalized patch — B − C ≥ 0.02:** **True** (gap = 0.694)
- **Rank-normalized patch — B true subspace beats wrong control:** **True** (gap = 0.867)

## Per-(modulus, train_frac, arm) breakdown

| Arm | n | train_frac | # seeds | Mean OOD | Mean Patch-CE Δ | Mean subspace CE / mass | Mean Weakness |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 17 | 0.5 | 4 | 0.000 | -0.431 | -3.247 | 0.059 |
| A | 19 | 0.5 | 4 | 0.000 | -0.336 | -3.387 | 0.053 |
| A | 23 | 0.5 | 4 | 0.000 | -0.492 | -3.224 | 0.043 |
| B | 17 | 0.5 | 4 | 1.000 | 0.020 | 0.832 | 1.000 |
| B | 19 | 0.5 | 4 | 1.000 | 0.053 | 0.795 | 1.000 |
| B | 23 | 0.5 | 4 | 1.000 | 0.035 | 0.975 | 1.000 |
| C | 17 | 0.5 | 4 | 0.131 | 0.000 | 0.140 | 0.059 |
| C | 19 | 0.5 | 4 | 0.108 | 0.002 | 0.197 | 0.053 |
| C | 23 | 0.5 | 4 | 0.081 | 0.009 | 0.183 | 0.043 |
| D | 17 | 0.5 | 4 | 0.000 | -0.431 | -3.247 | 0.059 |
| D | 19 | 0.5 | 4 | 0.000 | -0.336 | -3.387 | 0.053 |
| D | 23 | 0.5 | 4 | 0.000 | -0.492 | -3.224 | 0.043 |
