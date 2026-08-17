# Paper E: the taxonomy is not a one-shot agent rule

**Jawaun Brown** (human director) and **Cursor Grok 4.6** (agent, under review)
**Date:** August 17, 2026
**Status:** Possibility that the three-cell taxonomy is a cheap
agent decision procedure is **dead on this harness**. Verdict
`surgery_killed`. Not text nomination. Not an LLM eval. Paper F
is now banked as `calculus_is_sic`.

## Current frame

Papers A–D banked a three-way taxonomy, a swap cell, a connection
that is not integer Kirchhoff, and a failed Lorentz / Lamport /
PE transfer. The leftover reading is that an agent can now
*diagnose the cell from the obstruction* and apply the matching
repair without trying the menu and without reading English.
That would make delete–repair an assumption-surgery procedure
for agents. This paper runs that procedure, name-blind.

## Assumption ledger

| Assumption | Type | Load-bearing? | Break test |
|---|---|---:|---|
| Cell is a cheap signature | Mechanism | high | Held-out gold ≠ `decide(σ)` |
| Unused symmetry is leftover privilege | Ontology | high | `pair_eq` on `q_id` quotients |
| Trying the menu is unnecessary | Pragmatic | high | Menu-relative gold is the only hit |
| This is an LLM benchmark | Boundary | high | Withhold; no model is called |
| Paper B is at stake | Boundary | no | Crossed repairs still fail on A |

## Anomaly map

The taxonomy names three cells. Empirical gold is a fact about
a *menu*: restore if a finer registered screen represents,
quotient if a coarser one does, transport if Kirchhoff
mismatches, otherwise noop. Those can come apart. A target can
have a nontrivial symmetry and still have no cheaper screen in
the menu. That is unused symmetry, not leftover privilege.

## Candidate reframe

The three cells are a reading of menu-relative representability,
not a one-shot diagnostic. An agent that cannot try repairs
cannot trust "has symmetry and the identity screen → quotient."
Possibility 2 (the catalog / the menu is the engine) gains on
the *agent* question. Paper B is untouched: when you *do* try
the typed repair, crossed cells still fail. Possibility 5
remains the house: this is SIC's dynamics, not a new master
object.

## Discriminating predictions

| Transfer | Predicted |
|---|---|
| Authoring toys (construction) | hit (the rule was written there) |
| `last_bit` as a relabel of `first_bit` | hit |
| `parity` as a bag-like leftover | hit |
| `identity` on `q_id` | noop, not a blind quotient |
| `pair_eq` on `q_perm` | restore |
| `pair_eq` on `q_id` | gold noop; cheap rule says quotient |
| New Aff(1, Z/3) cycle | transport |
| Identification / one-shot rule | every held-out row hits |

## Severe experiment

Package: `experiments/delete_repair_surgery/`.
World: `{0,1}^4`. Menu: `q_id`, `q_rot`, `q_perm`, `q_stab0`,
`q_stab_last`. Policy input is only

```
(mixes, n_fibres, n_worlds, y_has_nontrivial_symmetry, connection_mismatch)
```

Pre-registered rule:

1. Kirchhoff mismatch → `transport`
2. else `mixes` → `restore`
3. else symmetry and `n_fibres = n_worlds` → `quotient`
4. else `noop`

Construction (disclosed, not the kill): 4/4.

Held-out: **6/7**. The miss is `pair_eq` on `q_id`:

- Signature: does not mix, 16 fibres, has symmetry (swap of the
  paired bits; permutations of the tail).
- Policy: `quotient`.
- Gold: `noop`. No cheaper registered screen represents
  `x[0] == x[1]`.

The other held-out rows hit: `last_bit` restore/quotient,
`parity` quotient, `identity` noop, `pair_eq` on `q_perm`
restore, Aff(1, Z/3) cycle `C = ((1,0),(1,0),(2,1),(2,2))`
transport (holonomy `(1,1)`, Kirchhoff `(1,0)`).

Best constant baseline on the held-out suite is `restore` at
2/7. The cheap rule beats that consolation score and still
fails the pre-registered exactness kill.

Kill was: any held-out miss. It happened. Verdict:
`surgery_killed`.

Honesty: "you have to check whether a cheaper screen exists"
is not a new theorem. What is ours is the predeclared
name-blind agent rule against a held-out grain, with
construction toys disclosed and a miss that still passes CI.

## Claim boundary

**Supported.** On this harness, the cheap taxonomy signature is
not a complete one-shot agent rule. Unused symmetry is not
leftover privilege. Typed menu search still defines gold.

**Not supported.** Agents in general. Any LLM eval. Text
nomination. Reopening Paper B. Paper F. A better language
model. A claim that the three cells are false.

**What would change the conclusion.** A later menu on which
`pair_eq` becomes quotientable *and* the same cheap rule then
hits every held-out row. That would be a menu change, not a
rescue of this rule on this menu. A name-blind rule that does
not try repairs and still hits a larger held-out suite.

## Next best test

Paper F is banked: the written function is SIC. Do not reopen
DR/DCR. Do not train a net as a substitute. Do not turn this
into an LLM leaderboard. Possibility 5 is the close. The
phenomenon that would kill it is still missing: a delete–repair
fact that cannot be written as a movement of `(q, K)`.
