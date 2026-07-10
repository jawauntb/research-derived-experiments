# E2 + E3 — Compatibility Augmentation vs Readout, with Patch-CE

Total cells trained: 48

## Per-arm summary (selected cell per (n, train_frac))

| Arm | Description | # sel | OOD acc (mean, 95%CI) | Patch-CE Δ | Subspace CE / mass | Wrong subspace CE / mass | Weakness |
|---|---|---:|---|---|---|---|---|
| A | Readout selector (no aug) | 3 | 0.000 [0.000, 0.000] | -0.709 [-1.063, -0.355] | -3.774 [-4.777, -2.771] | -6.022 [-6.652, -5.392] | 0.052 |
| B | Compat aug (true cyclic group) | 12 | 1.000 [1.000, 1.000] | 0.103 [0.073, 0.133] | 1.119 [0.993, 1.246] | 0.001 [0.001, 0.001] | 1.000 |
| C | Wrong-group aug | 12 | 0.099 [0.083, 0.115] | 0.017 [0.010, 0.024] | 0.159 [0.134, 0.184] | -0.014 [-0.029, -0.000] | 0.052 |
| D | Loss selector (no aug) | 3 | 0.000 [0.000, 0.000] | -1.199 [-1.426, -0.973] | -4.139 [-4.699, -3.579] | -5.819 [-5.964, -5.674] | 0.052 |

## Discriminator gates

- **E2 pass — B beats A on OOD by ≥ 0.30:** **True** (gap = 1.000)
- **E2 pass — B beats A on Patch-CE Δ by ≥ 0.50:** **True** (gap = 0.812)
- **E3 pass — ρ(patch-CE, OOD) > ρ(weakness, OOD):** **True** (ρ_patch = 0.915 vs ρ_weakness = 0.653)
- **Rank-normalized patch — Arm B positive:** **True**
- **Rank-normalized patch — B − C ≥ 0.02:** **True** (gap = 0.961)
- **Rank-normalized patch — B true subspace beats wrong control:** **True** (gap = 1.118)

## Per-(modulus, train_frac, arm) breakdown

| Arm | n | train_frac | # seeds | Mean OOD | Mean Patch-CE Δ | Mean subspace CE / mass | Mean Weakness |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 17 | 0.5 | 4 | 0.000 | -0.870 | -3.803 | 0.059 |
| A | 19 | 0.5 | 4 | 0.000 | -1.018 | -3.754 | 0.053 |
| A | 23 | 0.5 | 4 | 0.000 | -0.963 | -4.227 | 0.043 |
| B | 17 | 0.5 | 4 | 1.000 | 0.099 | 1.014 | 1.000 |
| B | 19 | 0.5 | 4 | 1.000 | 0.076 | 1.112 | 1.000 |
| B | 23 | 0.5 | 4 | 1.000 | 0.134 | 1.231 | 1.000 |
| C | 17 | 0.5 | 4 | 0.119 | 0.016 | 0.141 | 0.059 |
| C | 19 | 0.5 | 4 | 0.104 | 0.017 | 0.176 | 0.053 |
| C | 23 | 0.5 | 4 | 0.075 | 0.017 | 0.159 | 0.043 |
| D | 17 | 0.5 | 4 | 0.000 | -0.870 | -3.803 | 0.059 |
| D | 19 | 0.5 | 4 | 0.000 | -1.018 | -3.754 | 0.053 |
| D | 23 | 0.5 | 4 | 0.000 | -0.963 | -4.227 | 0.043 |
