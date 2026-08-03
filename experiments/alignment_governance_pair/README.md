# Alignment-Governance Pair (Theorems AG-1, AG-2 witness)

Companion instrument for
[`papers/alignment_as_ensemble_governance/paper.md`](../../papers/alignment_as_ensemble_governance/paper.md).

Hypothesis: Theorem AG-1 (Viability under a bounded transition kernel)
says that if the coarse Z-transition kernel satisfies a per-step leakage
certificate `Sum_{z' in V} T(z' | z, a) >= 1 - beta` for every viable
state `z in V` and every action `a`, then
`Pr[q(X_t) in V for all t <= T] >= (1 - beta)^T`. Theorem AG-2 says the
bound is inherited (with only-improving rate) when V is enlarged to any
superset V' >= V.

Method: build a 4-state finite Markov world (Z = {0, 1, 2, 3},
V = {0, 1, 2}, unviable = {3}) with per-step leakage `beta = 0.05` under
a uniformly random policy over actions {stay, move}. Compute exact
survival probabilities by matrix powers for T in {1, 3, 5, 10, 20} and
compare to the AG-1 lower bound `(1 - beta)^T`. Verify AG-2 by extending
V to V' = Z (everything viable) and checking survival is 1.0 at every T.

Pre-registered gates (all four pass exactly):

- `ag1_lower_bound_holds_at_every_T`: for every T in the sweep, exact
  survival >= (1 - beta)^T.
- `ag1_lower_bound_tightness`: at T = 1, exact survival = (1 - beta)
  exactly (within 1e-12); by construction the bound is tight at every T
  on this world.
- `ag2_viability_inherited_by_superset`: when V is extended to
  V' = Z, survival is 1.0 at every T.
- `ag_survival_monotone_decreasing_in_T`: survival probability on V is
  weakly monotone non-increasing across the horizon sweep.

Result: all four gates pass exactly. At T = 10, exact survival equals
0.95^10 = 0.5987369 (matching the AG-1 lower bound to numerical
precision); at T = 20, exact survival equals 0.95^20 = 0.3584859.

Run:

```bash
python3 experiments/alignment_governance_pair/experiment.py
```
