# SIC-C-c Covering Meta-Theorem Pair

Companion instrument for
[`papers/structural_intelligence_covering_learnability/paper.md`](../../papers/structural_intelligence_covering_learnability/paper.md)
and the Lean-verified meta-theorem
`StructuralIntelligenceMathlib.sicc_covering_meta` /
`StructuralIntelligenceMathlib.sicc_covering_poly` in
`formal/structural-intelligence-mathlib/StructuralIntelligenceMathlib/SICC_CoveringMeta.lean`.

Hypothesis: for a controlled continuous space where the eps-cover of a
hypothesis class `H` has exactly `K` cells (2-D Gaussian world with
rotational latent angle quantised to `K` bins), the empirical sample
complexity of recovery on the cover — the classical coupon-collector
event "each of the `K` cells is instantiated at least once in `N`
uniform iid samples" — is fitted by

    n_emp(K, delta)  =  c * K * log(K / delta)

for a single class-independent constant `c` predicted by
`sicc_covering_meta`.

Method: for each `K ∈ {8, 16, 32, 64, 128, 256}` with `delta = 0.05`:

- Compute the exact recovery probability by inclusion-exclusion:

  ```
  P(all K cells hit in N samples)
    =  sum_{s = 0}^{K}  (-1)^s * C(K, s) * ((K - s) / K)^N.
  ```

- Binary-search for the smallest `N` such that `P(recovery) >= 1 - delta`
  — this is `n_emp(K, delta)`.
- Compute `c_fitted(K) = n_emp(K, delta) / (K * log(K / delta))`.

Pre-registered gates:

- `SICC_META_FITTED_C_STABLE_ACROSS_K`: `(max - min) / mean` of
  `c_fitted` across `K` is `<= 0.20`. This is the sharp test — if `c`
  drifts with `K`, the meta-theorem's `K · log(K/δ)` scaling is wrong.
- `SICC_META_EMPIRICAL_MEETS_TARGET`: `P(recovery at n_emp) >= 0.95` for
  every `K`.
- `SICC_META_EMPIRICAL_IS_TIGHT_BY_ONE_SAMPLE`:
  `P(recovery at n_emp - 1) < 0.95` for every `K` (binary search
  returns the tight smallest `N`).
- `SICC_META_ABOVE_PIGEONHOLE_FLOOR`: `n_emp >= K` for every `K`.

**Result (empirical, all four gates pass to machine precision).**

| K   | n_emp | meta bound (c=1) | c_fitted |
|-----|-------|------------------|----------|
| 8   | 38    | 40.60            | 0.9359   |
| 16  | 90    | 92.29            | 0.9752   |
| 32  | 203   | 206.77           | 0.9818   |
| 64  | 453   | 457.90           | 0.9893   |
| 128 | 998   | 1004.51          | 0.9935   |
| 256 | 2176  | 2186.47          | 0.9952   |

`c_fitted` is monotone increasing toward 1 with `K` (the meta-theorem's
`K · log(K/δ)` is a slightly loose upper bound at small `K` where the
coupon-collector correction terms `K · γ` are still visible), and the
`(max − min) / mean` span across `K` is `6.06%` — well inside the 20%
tolerance. Empirically, the meta-theorem's scaling family
`c · K · log(K/δ)` fits the coupon-collector realisation of the
eps-cover recovery problem exactly at the intended constant `c ≈ 1`.

Run:

```bash
python3 experiments/sicc_covering_meta_pair/experiment.py
```
