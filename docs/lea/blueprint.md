# Blueprint — SIC Dynamics

One `## ` section per node. Status is not stored here; Lea derives it from the
latest Lean verdict. Independent P0/P1 nodes may be proved in parallel (one
file per agent). Do not add slogan nodes.

## cheap_signature
- kind: definition
- uses:

Five-field cheap diagnostic used by Paper E `decide` and Paper F `κ_cheap`:
`(mixes, n_fibres, n_worlds, y_has_nontrivial_symmetry, connection_mismatch)`.
Finite. No analysis.

## menu_screen
- kind: definition
- uses:

A named screen on `{0,1}^4` from the disclosed menu
`{q_id, q_rot, q_perm, q_stab0, q_stab_last}`.

## gold_repair
- kind: definition
- uses: menu_screen

Menu-relative gold in `{noop, restore, quotient, transport}`. Empirical on the
registered suite; do not refit it.

## kappa_cheap_not_function
- kind: theorem
- uses: cheap_signature, gold_repair

There exist two registered worlds with the same cheap signature and different
golds (`pair_eq_q_id` is `noop`; `bag_q_id` is `quotient`). Therefore κ_cheap
is not a function from cheap signatures to golds.

## representing_screens
- kind: definition
- uses: menu_screen, gold_repair

The set of menu screens that represent a given `Y`.

## kappa_screen
- kind: definition
- uses: representing_screens

If `connection_mismatch` then `transport`, else the coarsest representing
menu screen (fewest fibres, then lexicographic name), then the typed
restore/quotient/noop. This is Theorem 4 plus a total order, not a new
primitive. Do not re-prove CommonSuffScreen.

## kappa_screen_hits_suite
- kind: theorem
- uses: kappa_screen, gold_repair

On the registered 11-row Paper F suite, `κ_screen` equals gold.

## bag_not_unique
- kind: theorem
- uses: representing_screens

The `bag` task has five representing menu screens. Uniqueness fails even
though `κ_screen` is a function via the named tie-break.

## kappa_relabel_natural
- kind: theorem
- uses: kappa_screen

The bit-label swap `0 ↔ 3` sends `first_bit` / `q_stab0` to
`last_bit` / `q_stab_last` (and conversely). Names are not essence.

## aff13
- kind: definition
- uses:

The affine group `Aff(1, Z/3)` with composition
`(a,b) ∘ (c,d) = (a*c, a*d + b)` (mod 3).

## affine_escapes_kirchhoff
- kind: theorem
- uses: aff13

There exist 4-cycles whose path-ordered holonomy is not the integer
Kirchhoff prediction (`sum b`). Additive cycles remain the control.
Not a Lorentz theorem.

## diamond_placement
- kind: definition
- uses:

An integer embedding of the causal diamond (two-event poset) into a
discrete grid with a declared interval function `s²`.

## poset_not_determine_interval
- kind: theorem
- uses: diamond_placement

There exist two diamond embeddings with the same causal poset and different
`s²` values (the registered set is `{-1,-3,-4,-8}`). The poset does not
determine the interval. Not continuum physics.

## surgery_miss_pair_eq
- kind: theorem
- uses: cheap_signature, gold_repair

On held-out `pair_eq` / `q_id`, the cheap rule returns `quotient` and the
gold is `noop`. Unused symmetry is not leftover privilege.

## dta_n4_representable_iff
- kind: theorem
- uses: menu_screen

On the registered `{0,1}^4` harness, `Y` is representable from screen `q`
iff `G_q ⊆ G_Y`. Finite biconditional only; do not claim general `n`.

## swap_typed_wins
- kind: theorem
- uses: menu_screen, gold_repair

On the Paper B swap cell, typed restore/quotient succeed and the crossed
over-repair fails. Opposite repairs are not interchangeable.
