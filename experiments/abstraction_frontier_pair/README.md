# Abstraction-Frontier Pair (Theorems AF-1 & AF-2 witness)

Companion instrument for
[`papers/abstraction_frontier/paper.md`](../../papers/abstraction_frontier/paper.md).

Hypothesis: on the 4-bit Boolean world with the shared-through-`Z` task
family (`parity{0,1}`, `parity{2,3}`, `parity{0,1,2,3}`), the Pareto
frontier over the four §5.3 axes

- **task-sufficiency** `max_α H(Y_α | q(X))`,
- **coding cost** `log₂(|image(q)|)`,
- **dynamical closure** (0 uniformly here — static example),
- **control regret** (0 uniformly here — no controller),

is a two-element antichain `{constant, joint(parity{0,1}, parity{2,3})}`.

The constant is the min-cost endpoint (worst sufficiency 1, best cost 0);
the CSS `Z = joint(parity{0,1}, parity{2,3})` is the unique zero-
sufficiency Pareto member (best sufficiency 0, cost 2). The identity has
sufficiency 0 as well, but its coding cost 4 exceeds `Z`'s cost 2, so `Z`
strictly dominates the identity — the *static-case collapse* AF-2
predicts. Every subset parity (coding cost 1, sufficiency 1) is
dominated by the constant. Every non-`Z` joint pair-parity and every
joint bit-read (cost 2, sufficiency 1) is also dominated by the
constant. The single triple-bit read (cost 3, sufficiency 1) is
dominated too.

Method: enumerate the 23-element concern-parameter lattice from
Instrument 4 (`experiments/cross_task_sufficiency`); compute the four
axes exactly under the uniform distribution on `X = {0, 1}⁴`; apply
standard Pareto (weakly dominates + strict on one axis) to select the
frontier; check every gate exactly.

**Note on the two zero axes.** Dynamical closure
`I(Z_{t+1}; X_t | Z_t, A_t)` requires a dynamics
`(Z_{t+1}, A_t)` that this static 4-bit world does not carry; we set
this axis to 0 for every quotient by convention. Likewise control
regret requires a controller; we set it to 0. In the paper §5, these
two axes are the ones that would separate the "sufficient" quotients
from each other in a truly dynamical setting — here they cannot, so the
frontier collapses to the two axes `(task-sufficiency, coding cost)`,
and Theorem AF-2's "segment from `q*` to identity" claim collapses to
`{q*}` alone on the sufficient side. This *is* the AF-2 static-case
corollary, and it is one of the pre-registered gates.

Pre-registered gates (all six pass exactly):

- `af1_frontier_is_antichain`: no two Pareto members dominate each other.
- `af1_frontier_contains_true_Z`: `joint(parity{0,1}, parity{2,3})` is
  on the frontier.
- `af1_frontier_contains_constant`: the constant map is on the frontier.
- `af1_identity_is_dominated_in_static_case`: the identity is strictly
  dominated by `Z` — the AF-2 static-case collapse.
- `af2_sufficient_frontier_is_true_Z_alone`: the only zero-sufficiency
  Pareto member is `Z`.
- `af2_no_pareto_strictly_finer_than_true_Z`: no Pareto member is
  strictly finer than `Z` on the lattice.

Result: all six gates pass exactly. The Pareto frontier is
`{constant, joint(parity{0,1}, parity{2,3})}`. Every subset parity,
every non-`Z` joint pair-parity, every joint bit-read, and the identity
are all dominated — by the constant on the sufficiency-1 plateau, by
`Z` on the sufficiency-0 plateau.

Run:

```bash
python3 experiments/abstraction_frontier_pair/experiment.py
```
