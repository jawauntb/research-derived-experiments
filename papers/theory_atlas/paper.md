# The Theory Atlas

## A sheaf-of-theories formalisation of §5.5 with the cocycle condition classifying obstructions

**Jawaun Brown**
Human author and research director

**Claude Code (agent)**
Experiment code, analysis, and manuscript production under direction and review

**Date:** August 3, 2026
**Status:** two theorems + one worked example (4-bit Boolean world). Companion paper to *The Structural Intelligence Conjecture* (`papers/structural_intelligence/paper.md`); depends on Theorem 1 of that paper (existence of the master fibration) and instantiates the extended-program clause §5.5 as two theorems.

---

## Abstract

Extended-program §5.5 of *The Structural Intelligence Conjecture*
conjectures that theories can be treated as local charts `M_i` on
contexts `U_i` with translations `T_ij : M_i → M_j`, and that where the
cocycle `T_jk ∘ T_ij = T_ik` fails the discrepancy is an *informative*
obstruction — missing latent, phase transition, or category error.
This paper turns that conjecture into two clean theorems.

- **Theorem TA-1 (Cocycle condition is necessary and sufficient for
  gluing).** *A presheaf of theories `{M_i, T_ij}` on a context poset
  extends to a global theory `M` on the union `⋃ U_i` if and only if
  the cocycle `T_jk ∘ T_ij = T_ik` holds for every triple `(i, j, k)`
  with pairwise overlap.* Standard sheaf/descent argument, executed in
  the discrete-poset setting with a target label alphabet.
- **Theorem TA-2 (Cocycle failure classifies obstructions).** *If the
  cocycle fails, the discrepancy `D := T_ik^{-1} ∘ T_jk ∘ T_ij` is a
  permutation on the target alphabet whose rank and edge-support
  classify the obstruction: rank-zero on every triple = **glue**;
  rank ≥ 1 with the non-identity transitions supported on a single
  pairwise overlap = **phase transition / boundary**; rank ≥ 1 with
  every pairwise transition non-identity = **missing latent**.*

The theorems are elementary: TA-1 is the discrete analogue of the
Čech-descent equivalence familiar from sheaf theory, executed on a
context poset without measure-theoretic overhead; TA-2 reads the
same equivalence backwards to make the *shape* of the failure into a
diagnostic.

An exact instrument (`experiments/theory_atlas_pair`) exhibits both on
the 4-bit Boolean world of Instrument 4. Three contexts
`U_1 = {x_0 = 0}`, `U_2 = {x_1 = 0}`, `U_3 = {x_2 = 0}` share the same
chart maps into a target `T = Z/4`; the good family
`(T_12, T_23, T_13) = (+1, +1, +2)` satisfies the cocycle and glues to
the global theory `M(x) = (2·x_2 + x_3) mod 4`; the bad family
`(+1, +1, +3)` fails the cocycle with discrepancy shift-by-3 (rank 4,
no fixed points), does not glue on 6 of 14 union worlds, and matches
the missing-latent signature exactly. A third
`(+1, id, id)` phase-boundary reference is evaluated in parallel as a
control that TA-2's taxonomy separates the two regimes on identical
machinery. All four pre-registered gates pass exactly.

---

## 1. Setup

We inherit the master object of *The Structural Intelligence
Conjecture* §1: a stochastic fibration `(q : X → Z, K : Z ⇝ X)` on
a standard Borel `X`. Here we do *not* fix a global `q`; instead we
consider a family of local charts, each carrying its own coarse view.

**Contexts.** A finite index set `A` with a *context poset*
`{U_α ⊆ X : α ∈ A}` partially ordered by inclusion. Overlaps
`U_αβ := U_α ∩ U_β` and triple overlaps
`U_αβγ := U_α ∩ U_β ∩ U_γ` are the pairwise and triple intersections
of the covering family.

**Charts.** A *chart* on context `U_α` is a measurable map
`M_α : U_α → 𝒯` into a fixed target alphabet `𝒯`. In this paper `𝒯`
is finite; the extension to a general standard Borel target is the
same argument with regular conditional kernels replacing set functions.

**Transitions.** For every pair of overlapping contexts, a *transition*
`T_αβ : 𝒯 → 𝒯` — a bijection on `𝒯` — encoding how a chart-`α`
label is re-expressed in chart-`β`'s alphabet on `U_αβ`. Concretely,
the transitions are the identifications that would let a chart-`α`
observer translate their measurements to chart-`β`'s coordinates
without loss.

**Presheaf of theories.** The data `𝒫 := ({M_α}, {T_αβ})` is a
*presheaf of theories* on the context poset: to every context we
assign a chart (a "theory of the local context") and to every overlap
we assign a translation.

**Gluing.** A *global theory* is a measurable map `M : ⋃_α U_α → 𝒯`
together with a family of bijections `ψ_α : 𝒯 → 𝒯` such that
`M(x) = ψ_α(M_α(x))` for all `x ∈ U_α` and every `α`. We say `𝒫`
*glues* if such a `(M, {ψ_α})` exists.

**Cocycle.** The presheaf `𝒫` satisfies the *cocycle condition* if,
for every triple `(α, β, γ)` with non-empty pairwise overlaps,

```
T_βγ ∘ T_αβ  =  T_αγ    as maps 𝒯 → 𝒯.
```

Equivalently, the *cocycle discrepancy*

```
D_αβγ  :=  T_αγ^{-1} ∘ T_βγ ∘ T_αβ
```

is the identity permutation on `𝒯` for every triple.

The rest of the paper proves that gluing is equivalent to the cocycle
condition (Theorem TA-1) and that the failure of the latter classifies
the shape of the obstruction (Theorem TA-2).

---

## 2. Theorem TA-1: cocycle is necessary and sufficient for gluing

**Theorem TA-1 (Cocycle condition is necessary and sufficient for
gluing).** *A presheaf of theories `𝒫 = ({M_α}, {T_αβ})` on a context
poset extends to a global theory `M : ⋃_α U_α → 𝒯` if and only if the
cocycle condition `T_βγ ∘ T_αβ = T_αγ` holds for every triple
`(α, β, γ)` with non-empty pairwise overlaps.*

**Proof.**

*(Necessity.)* Suppose `𝒫` glues via `(M, {ψ_α})`. Then for every
`α, β` with `U_αβ ≠ ∅` and every `x ∈ U_αβ`,

```
M(x)  =  ψ_α(M_α(x))  =  ψ_β(M_β(x)),
```

so `M_β(x) = (ψ_β^{-1} ∘ ψ_α)(M_α(x))` on the overlap. Because the
`ψ_β^{-1} ∘ ψ_α`'s are bijections of `𝒯`, they act pointwise on
labels and the identity `M_β = (ψ_β^{-1} ∘ ψ_α) ∘ M_α` on `U_αβ` forces

```
T_αβ  =  ψ_β^{-1} ∘ ψ_α
```

(uniquely on the image of `M_α`; extended arbitrarily to all of `𝒯`,
but the composition identities below use only image values). Then

```
T_βγ ∘ T_αβ  =  (ψ_γ^{-1} ∘ ψ_β) ∘ (ψ_β^{-1} ∘ ψ_α)
             =   ψ_γ^{-1} ∘ ψ_α
             =   T_αγ.
```

So the cocycle holds on every triple.

*(Sufficiency.)* Assume the cocycle. Fix any base chart index (WLOG
`α = 0`), set `ψ_0 := id`, and define

```
ψ_β  :=  T_0β^{-1}         for every β ≠ 0.
```

Define `M(x) := ψ_β(M_β(x))` for any `β` with `x ∈ U_β`. We show that
`M` is single-valued on `⋃_β U_β`.

Take `x ∈ U_β ∩ U_γ` and suppose `β, γ ≠ 0`. By the pairwise
identification on `U_βγ`,

```
M_γ(x)  =  T_βγ(M_β(x)),
```

hence

```
ψ_γ(M_γ(x))  =  T_0γ^{-1}(T_βγ(M_β(x))).
```

Applying the cocycle to the triple `(0, β, γ)`,

```
T_βγ ∘ T_0β  =  T_0γ    ⟹    T_0γ^{-1} ∘ T_βγ  =  T_0β^{-1}  =  ψ_β,
```

so `ψ_γ(M_γ(x)) = ψ_β(M_β(x))`. The `0 ∈ {β, γ}` case is direct
because `ψ_0 = id` and `T_0β^{-1} ∘ M_β = ψ_β ∘ M_β` on `U_0β` by
definition. So `M` is well-defined on the union, and the pair
`(M, {ψ_α})` witnesses gluing. □

**Corollary (uniqueness up to relabelling of `𝒯`).** *If two global
theories `(M, {ψ_α})` and `(M', {ψ'_α})` witness gluing of the same
presheaf, then `M' = π ∘ M` for a single bijection `π : 𝒯 → 𝒯` and
`ψ'_α = π ∘ ψ_α` for every `α`.* Direct from
`M'(x) = ψ'_α(M_α(x)) = (ψ'_α ∘ ψ_α^{-1})(M(x))`, with the composition
`π := ψ'_α ∘ ψ_α^{-1}` independent of `α` by the cocycle on `(α, β)`
overlaps.

**Remark (relation to sheaf descent).** In the discrete-poset setting
with a finite target `𝒯`, Theorem TA-1 is the standard
Čech-degree-1 descent statement: the cocycle condition on triples
`𝒞²` maps to zero exactly when a section on the cover extends. The
proof is executed here without cohomological language because the
setting is finite and the target is a set alphabet. The theorem
generalises to standard Borel targets by replacing the pointwise
identity `T_αβ ∘ M_α = M_β` with an almost-sure identity, at the
cost of an almost-everywhere qualifier throughout.

---

## 3. Theorem TA-2: cocycle failure classifies obstructions

**Setup (Theorem TA-2).** Assume the presheaf `𝒫` does *not* satisfy
the cocycle: at least one triple `(α, β, γ)` has non-identity
discrepancy `D_αβγ`. We classify the shape of the failure by two
quantities:

- **Rank.** `rank(D_αβγ) := |{a ∈ 𝒯 : D_αβγ(a) ≠ a}|` — the number of
  labels moved by the discrepancy permutation. Rank 0 iff `D_αβγ` is
  the identity.
- **Support.** The set of pairwise transitions that are non-trivial:
  `supp(𝒫) := {(α, β) : T_αβ ≠ id_𝒯}`. Encodes *which* overlaps
  contribute to the obstruction.

**Theorem TA-2 (Cocycle failure classifies obstructions).** *For a
presheaf `𝒫` on the context poset with at least three contexts and
non-empty pairwise overlaps:*

1. *(`glue`.)* *If `rank(D_αβγ) = 0` for every triple, `𝒫` glues by
   Theorem TA-1 and no obstruction is present.*
2. *(`phase transition / boundary`.)* *If some `rank(D_αβγ) ≥ 1` and
   `supp(𝒫)` is a strict subset of the pairwise-overlap edges (i.e.,
   at least one `T_αβ = id_𝒯`), the obstruction is **localised** to
   the non-trivial edges and admits a boundary interpretation: a
   region-change or scale/phase transition witnessed by a specific
   pair of contexts.*
3. *(`missing latent`.)* *If some `rank(D_αβγ) ≥ 1` and every pairwise
   `T_αβ` is non-identity, the obstruction is **spread across all
   overlaps** and admits a missing-latent interpretation: no chart is
   individually the anomalous one — the failure to glue is a
   collective property of the presheaf, consistent with the absence
   of a global label alphabet that would let all charts agree.*

**Proof.**

*(1)* Immediate from Theorem TA-1: rank-zero discrepancy on every
triple is the cocycle, so `𝒫` glues.

*(2)* Suppose `T_αβ = id` for some edge and some other triple has
`rank ≥ 1`. Then the presheaf restricted to the sub-poset of
identity-edged pairs satisfies the cocycle on that sub-poset
(compositions of identities are identities), so the failure is
supported on `supp(𝒫)` — a proper subset of edges. Every gluing
attempt through a chart in the trivial sub-poset agrees on that
sub-poset; the disagreement is *only* along the non-trivial edges,
and hence is diagnosable as a boundary between two "self-consistent"
regions joined by a non-trivial identification. This is the discrete
analogue of a phase transition or scale change: one direction glues,
the other does not.

*(3)* Suppose every `T_αβ` is non-identity. Then no chart can be
singled out as the anomalous one on the basis of `supp(𝒫)`: every
edge carries non-trivial identification, so removing any single chart
still leaves a non-trivial residual presheaf. The failure to glue is
a *joint* property of the transitions, not localised to a subset. The
natural repair is to enlarge the target alphabet `𝒯` — i.e., to
posit an additional latent variable that all charts have been
implicitly quotienting over — because in the enlarged `𝒯'` the
transitions can be lifted to bijections that do close the cocycle.
This is the operational content of "missing latent". A formal
existence theorem for the enlargement — the smallest `𝒯' ⊇ 𝒯` in
which a lift closing the cocycle exists — is a separate result
(a discrete analogue of universal covers of groupoids) that we do not
prove here. □

**Corollary (`category error` as a rank saturation).** *If
`rank(D_αβγ) = |𝒯|` on every triple (the discrepancy has no fixed
points), the presheaf carries no partial agreement between charts:
every chart-α label is mapped to a *different* label by the loop
`α → β → γ → α`. This is the extreme missing-latent regime and, on
finite target alphabets of small size, indistinguishable from a
category error where the charts are measuring genuinely different
things.* On a two-element alphabet, for instance, `rank = 2` is the
only non-trivial possibility and the missing-latent and category-error
signatures coincide; distinguishing them requires either a larger `𝒯`
or additional context beyond the presheaf. This is a limitation on the
diagnostic resolution of Theorem TA-2, not on its statement.

**Corollary (relation to the parent paper's fiber audit).** *A
cocycle failure of missing-latent type witnesses a `Δ_q(z) > 0`
regime in the fiber audit of parent-paper §5.4: the transitions
identify chart-values across contexts as if they addressed the same
`z`, but the loop discrepancy shows that the identification is not
consistent — i.e., there is a hidden coordinate on the fibre that the
charts have been marginalising over.* Whether that hidden coordinate
is task-relevant is a separate empirical question; the cocycle
diagnostic identifies its existence, not its behaviour.

---

## 4. Worked example: three contexts on the 4-bit Boolean world

**World.** `X = {0, 1}^4` (16 elements, uniform base distribution).

**Contexts.**

- `U_1 := { x : x_0 = 0 }` (8 worlds),
- `U_2 := { x : x_1 = 0 }` (8 worlds),
- `U_3 := { x : x_2 = 0 }` (8 worlds).

Pairwise overlaps: `U_12 = {x_0 = x_1 = 0}` (4 worlds),
`U_13 = {x_0 = x_2 = 0}` (4 worlds),
`U_23 = {x_1 = x_2 = 0}` (4 worlds). Triple overlap
`U_123 = {x_0 = x_1 = x_2 = 0}` (2 worlds). The union
`U_1 ∪ U_2 ∪ U_3` covers 14 of the 16 worlds; the two uncovered
worlds are `(1, 1, 1, 0)` and `(1, 1, 1, 1)`.

**Target alphabet.** `𝒯 = Z/4 = {0, 1, 2, 3}`.

**Underlying observable.** `g(x) := (2·x_2 + x_3) mod 4`, valued in
`𝒯`, defined on all of `X`.

**Chart maps** (identical between the good and bad families):

- `M_1(x) := g(x)` on `U_1` — identity presentation on chart 1;
- `M_2(x) := (g(x) + 1) mod 4` on `U_2` — shift-by-1 presentation;
- `M_3(x) := (g(x) + 2) mod 4` on `U_3` — shift-by-2 presentation.

**Good chart family** (`(+1, +1, +2)`). Transitions:

- `T_12(a) = (a + 1) mod 4`,
- `T_23(a) = (a + 1) mod 4`,
- `T_13(a) = (a + 2) mod 4`.

Cocycle discrepancy on the single triple `(1, 2, 3)`:

```
D_123(a)  =  T_13^{-1}(T_23(T_12(a)))
         =  T_13^{-1}((a + 1) + 1)
         =  (a + 2) − 2
         =  a           for every a ∈ 𝒯.
```

`D_123` is the identity permutation on `𝒯`; `rank(D_123) = 0`. By
Theorem TA-1 the presheaf glues, and the pivot-through-chart-1
construction (`ψ_1 = id`, `ψ_2 = T_12^{-1} = -1`,
`ψ_3 = T_13^{-1} = -2`) yields the global theory

```
M(x)  =  g(x)  =  (2·x_2 + x_3) mod 4    on U_1 ∪ U_2 ∪ U_3.
```

The 14-world union is covered consistently (every world in a
multi-chart overlap receives a single candidate value).

**Bad chart family** (`(+1, +1, +3)`). Same chart maps `M_i`.
Transitions:

- `T_12(a) = (a + 1) mod 4`,
- `T_23(a) = (a + 1) mod 4`,
- `T_13(a) = (a + 3) mod 4` — differs from the good case only in the
  chart-1-to-chart-3 identification (the two-step consistent value
  would be `+2`; the bad table asserts `+3`).

Cocycle discrepancy:

```
D_123(a)  =  T_13^{-1}(T_23(T_12(a)))
         =  T_13^{-1}((a + 1) + 1)
         =  (a + 2) − 3
         =  (a − 1) mod 4
         =  (a + 3) mod 4.
```

`D_123` is the shift-by-3 permutation on `Z/4`; `rank(D_123) = 4` (no
fixed points). Every pairwise transition is non-identity (each is a
non-zero shift), so `supp(𝒫_bad) = {(1,2), (1,3), (2,3)}` — the full
edge set. By Theorem TA-2 clause (3), the bad presheaf is classified
as *missing latent*.

Concretely, no global theory `M` on the union exists: the
pivot-through-chart-1 attempt (`ψ_1 = id`, `ψ_2 = T_12^{-1} = -1`,
`ψ_3 = T_13^{-1} = -3`) assigns two distinct candidate values to
every world in the pairwise overlaps involving both chart 2 and chart
3 (6 worlds), witnessing the failure to glue as a set-theoretic
inconsistency in the presheaf.

**Phase-boundary reference family** (`(+1, id, id)`). Same chart maps.
Transitions:

- `T_12(a) = (a + 1) mod 4`,
- `T_23(a) = id(a) = a`,
- `T_13(a) = id(a) = a`.

Cocycle discrepancy:

```
D_123(a)  =  T_13^{-1}(T_23(T_12(a)))
         =  id(id((a + 1)))
         =  (a + 1) mod 4.
```

`rank(D_123) = 4`, but `supp(𝒫_phase) = {(1,2)}` — a *strict* subset
of the edges. By Theorem TA-2 clause (2), the phase-boundary
reference is classified as *phase transition / boundary*: the
disagreement is localised to a single overlap and admits the
interpretation of a boundary between chart 1's regime and the
`(chart 2, chart 3)`-agreeing regime.

The three verdicts — `glue`, `missing latent`, `phase transition` —
separate the good, bad, and reference families cleanly under
identical rank/support machinery, exhibiting TA-2's taxonomy in one
computation.

---

## 5. Instrument: `experiments/theory_atlas_pair`

Exact witness of Theorems TA-1 and TA-2 on the setup above.

- Enumerate the 16-world Boolean cube; construct the three contexts,
  three pairwise overlaps, and one triple overlap by set-theoretic
  intersection.
- Represent each `T_ij` as an explicit permutation of the 4-element
  target alphabet; permutation validity (bijection) is enforced by
  construction and re-checked by the test suite.
- For every triple `(i, j, k)` compute the cocycle discrepancy
  `T_ik^{-1} ∘ T_jk ∘ T_ij` as a permutation on `𝒯`; report its rank
  (number of moved elements) and whether it equals the identity.
- Attempt to construct a global theory by pivoting through chart 1
  (`ψ_1 = id`, `ψ_i = T_1i^{-1}` for `i > 1`); flag every world in any
  pairwise overlap that receives more than one candidate value.
- Compute the taxonomy verdict per family (`glue` / `phase transition`
  / `missing latent`) from the rank/support rule of Theorem TA-2.

**Pre-registered gates (all four pass exactly):**

- `ta1_good_charts_satisfy_cocycle`: cocycle holds on every triple for
  the good family (discrepancy = identity).
- `ta1_bad_charts_violate_cocycle`: at least one triple has non-zero
  discrepancy for the bad family (rank ≥ 1).
- `ta1_glue_iff_cocycle`: pivot-through-chart-1 gluing is consistent
  for the good family and inconsistent for the bad family. Together
  with the previous two gates, this is the computational instantiation
  of Theorem TA-1's equivalence on this world.
- `ta2_bad_discrepancy_matches_missing_latent_signature`: bad family
  is classified as `missing_latent`; the phase-boundary reference is
  classified as `phase_transition`; the good family is classified as
  `glue`. Verifies Theorem TA-2's rank/support taxonomy on one
  presheaf-per-verdict.

The instrument is deterministic (no random seeds, no Monte Carlo);
verdicts are exact. Bad-family discrepancy has rank 4 on `Z/4` (no
fixed points), all three transitions are non-identity, gluing fails on
exactly 6 of the 14 union worlds. Phase-boundary reference has rank 4
on the loop but exactly one non-identity transition and two identity
transitions.

---

## 6. Relation to the SIC framework

Theorem TA-1 turns extended-program §5.5 from a *research direction*
into a *theorem* about when a family of local theories can be
integrated into a single global theory: exactly when the cocycle on
triples holds. Theorem TA-2 turns the *failure* of the cocycle into a
*diagnostic*: the rank / support signature of the discrepancy tells
you what kind of disagreement you are looking at (localised boundary
versus distributed missing-latent) — an informative obstruction
rather than a bare inconsistency. Together with:

- Theorem CG-1 / CG-2 (concern as fiber geometry, Fisher metric and
  holonomy — `papers/concern_as_fiber_geometry/paper.md`),
- Theorem CT-1 / CT-2 (compiler tomography, MDL identifiability and
  compiler ecology — `papers/compiler_tomography/paper.md`),
- Theorem SA-1 (antecedent taxonomy — four canonical `(U, P)` recipes
  populating Theorem 4 — `papers/sufficient_antecedents/paper.md`),
- Theorem AF-1 / AF-2 (abstraction frontier as a Pareto antichain —
  `papers/abstraction_frontier/paper.md`),
- Theorem AG-1 / AG-2 (viability under bounded leakage —
  `papers/alignment_as_ensemble_governance/paper.md`),

the SIC extended program now has *seven* explicit theorem-instrument
pairs beyond the six of the parent paper. The remaining §5 constructs
(conditional rate–distortion control limit §5.2, causal semantics
§5.7, representation-repair calculus §5.8, autocatalytic artwork
§5.10) remain open — each is a direction rather than a theorem.

The sheaf framing sharpens the parent paper's honesty condition on
theory integration: two disagreeing charts on overlapping contexts do
not have to be reconciled into one — the honest question is whether
their transitions close the cocycle, and, if not, whether the
discrepancy signature indicates a boundary to respect or a missing
latent to lift. The parent paper's Wigner-effectiveness worry (§5.5)
becomes tractable: cross-domain theories glue exactly when the
cocycle closes, and the rank / support of a failure reads off whether
the "unreasonable" resemblance was a coincidence, a boundary, or a
common latent waiting to be found.

---

## 7. Limitations

- **Three contexts and one triple.** The instrument uses three
  contexts, which yields exactly one triple and one cocycle
  discrepancy to inspect. The taxonomy is exercised on *edges* — the
  three pairwise transitions — so the missing-latent-vs-phase-boundary
  distinction is fully witnessed on this world. A follow-up
  instrument with four or more contexts (yielding multiple triples)
  would exhibit the rank/support classification *across* triples, at
  which point "spread across all overlaps" becomes literal on more
  than one axis.
- **Finite target alphabet.** `𝒯 = Z/4` is a small finite set; the
  proofs generalise to standard Borel targets with the pointwise
  cocycle identity replaced by almost-sure identities. The
  cohomological framing (Čech-degree-1 with values in the automorphism
  sheaf of `𝒯`) is the standard higher generalisation; it is not
  needed here and would not sharpen the finite-case statement.
- **Category-error and missing-latent coincide at rank saturation.**
  On small alphabets the extreme missing-latent regime and a category
  error are indistinguishable from the presheaf alone — the corollary
  in §3 makes this explicit. Distinguishing them requires either a
  larger target or additional side information (e.g. a semantic
  signature on the labels).
- **The lift theorem is not proved.** Theorem TA-2's missing-latent
  clause asserts the *natural repair* is to enlarge `𝒯` so the
  cocycle can close; the formal existence of a smallest such lift
  (analogue of a universal cover of a groupoid) is a separate result
  that we do not prove. The instrument witnesses the diagnostic, not
  the repair.
- **No Lean formalisation.** Both proofs are elementary and the sheaf
  descent argument in the discrete setting is amenable to Lean/mathlib
  once the permutation-composition machinery is imported. The
  formalisation is left for future work; the numerical witness in
  Instrument 5 provides the analogue check.

---

## 8. Reproduction

```bash
python3 experiments/theory_atlas_pair/experiment.py
python3 -m unittest tests.test_theory_atlas_pair
```

Full development is in the parent paper's §5.5 and the notes file
`notes/structural_intelligence_conjecture.md`.
