# Delete the Absolute, Repair the Relations

## Paper A: a three-way taxonomy, five finite theorems, and a list of ways the thesis dies

**Jawaun Brown**
Human author and research director

**Cursor Grok 4.6 (cloud agent)**
Experiment code, Lean core, and manuscript under direction and review

**Date:** August 17, 2026
**Status:** Lean core kernel-checked (`formal/structural-intelligence/StructuralIntelligence/DeleteRepair.lean`, Lean 4.31, no Mathlib, zero `sorry`). Finite symmetry-matching instrument **banked** at `experiments/delete_the_absolute/` (7/7 preregistered gates; exact `n=4` enumeration, no SGD). Paper B swap cell **banked** at `experiments/delete_repair_swap/` (`taxonomy_holds` on this harness; pairing of A's matrix, not new enumeration). This manuscript still does **not** test Possibility 1. Companion constant-grammar EML census **banked** at `experiments/eml_fiber_spectrum/` (197 Catalan trees through `k=6`; size is not a denotation invariant). Papers E–F are banked: the one-shot rule dies, and the written κ is SIC (`calculus_is_sic`). Paper 0 and any claim of a new master object remain **withheld**. This is not a victory lap.

---

## Abstract

The representation-repair library of SIC §5.8 and
`papers/representation_repair_calculus/paper.md` is a catalog. Eight
hand-designed lifts exist. When they commute they compose. That is
Theorem RR-1 plus Theorem RR-2. It is not a function from failure
signatures to lifts, and it is not an engine.

This paper asks whether a coarser object — a **delete–obstruction–repair**
operator with a **three-way taxonomy** — does any work the catalog does
not. The taxonomy, not the eight rows, is the candidate master object:

1. **Over-invariance.** Too much identified. Restore distinctions.
2. **Under-invariance.** Leftover privilege. Quotient or covariantize.
3. **Covariant compensation.** A larger local symmetry breaks naive
   comparison. Add a connection / transport.

Five finite facts are kernel-checked. Four of them are prior art in
group-action, chain-rule, or discrete-Poincaré clothing. One of them —
`repair_paths_disagree` — kills a unique linear hierarchy of
representations (Possibility 4). It does **not** establish a universal
calculus (Possibility 1). Possibility 1 is untested. Possibility 5
(task-relative Pareto) is already the Structural Intelligence
Conjecture: if it is the right reading, delete–repair does not supersede
SIC. It is SIC's dynamics.

The historical slogan that smashes Einstein 1905 and content-only
attention into one arrow is false. Relativity deletes leftover privilege
(under-invariance plus a connection). EML and content-only attention
delete working structure (over-invariance) and must restore distinctions.
A shared diagram — global clock, local frames, relational comparison —
is not a shared theorem. Lorentz geometry is not Lamport causality is
not a positional encoding.

The job of this manuscript is to make the thesis easy to kill. The
banked `n=4` instrument does not kill it and does not save it. It
re-runs the algebra.

---

## Honesty ledger (read this first)

### Prior art (not ours)

- **Denotational syntax quotients.** Identifying terms that denote the
  same value is ordinary denotational semantics. Completeness-as-fiber-
  inhabitation, when it appears, belongs to the laboratory that proved
  it — for the one-operator calculator language, Odrzywołek,
  arXiv:2603.21852. We do not own syntax-by-denotation.
- **Bayes-sufficient task quotients.** Halmos–Savage minimal sufficiency
  and SIC Theorem 1 already give the task-relative quotient
  (`papers/structural_intelligence/paper.md` §2.1;
  `papers/structural_intelligence_foundations/paper.md`).
- **CommonSuffScreen / SIC Theorem 4.** Factorisation through a common
  screen implies fibre-constancy of every task
  (`formal/structural-intelligence/StructuralIntelligence/CommonSuffScreen.lean`,
  `commonSuffScreen_refines`). The symmetry-mismatch no-go is the
  **group-action packaging of that contrapositive**, specialised to an
  orbit relation. It is not a new logical primitive.
- **RR-1 / RR-2** (`papers/representation_repair_calculus/paper.md`).
  Eight hand-designed lifts exist and compose when they commute. That is
  a catalog plus a commuting-lifts theorem, not a function from failure
  signatures to lifts. Lean RR-2
  (`StructuralIntelligence/RepresentationRepair.lean`) records the
  commuting case.
- **TA-1** (`papers/theory_atlas/paper.md`;
  `formal/structural-intelligence/StructuralIntelligence/TheoryAtlas.lean`).
  Cocycle ⇔ gluing **up to injectivity**. The naked `↔` in the informal
  paper is stronger than the Lean core: without injectivity a constant
  family glues for free. We inherit the honest split, not the slogan.
- **DR1–DR4 / DCR date-cut retrodiction.** Nominating Einstein's
  deletion from text mostly **failed**. DR1 returned NO_GO on both
  preregistered hypotheses (`papers/deletion_repair_dr1/paper.md`).
  DCR1 failed its vocabulary-residue gate
  (`papers/date_cut_retrodiction_dcr1/paper.md`). Serial DCR nulls did
  not recover T1 (absolute simultaneity) at the 1904 cut. The program
  pivoted from deletability-at-a-cut to susceptibility
  (`papers/dynamics_of_conceptual_deletion/paper.md`). DCR4 then
  rejected the discussion-spike reading of Einstein 1905
  (`papers/date_cut_retrodiction_dcr4/paper.md`). We do **not** pretend
  we can find the deletion automatically.
- **Information bound.** `H(R | q_D) ≥ I(Y; X | q_D)` is the chain
  rule. We bank only the deterministic split: an exact repair must
  separate any `Y`-disagreement inside a `q_D`-fibre
  (`repair_splits_disagreement`). No reals, no Shannon entropy.
- **Discrete positional integration.** A cycle of relative steps
  integrates to a closed walk if and only if the steps sum to zero;
  two discrete integrals of the same step field differ by a global
  translation. This is the discrete Poincaré / Kirchhoff fact. We
  kernel-check it. We do not invent it.

### Ours (this paper)

- The **three-way taxonomy** as the candidate master object, not the
  eight-row library. Candidate, not promoted: the banked instrument
  does not discriminate the cells against a one-ladder alternative.
- The **dual of the no-go**: leftover privilege is gauge, not
  unrepresentability (`identity_always_factors`; instrument gate
  `DTA_OVERREPAIR_COST` as a fibre-count cost, not an obstruction).
- The **repair noncommutativity witness** (`pathA` vs `pathB`;
  `DTA_NONCOMMUTE`). This kills a unique linear hierarchy of
  representations (Possibility 4). It does not prove Possibility 1.
- The claim that **EML and relativity are dual instances**, not the
  same ladder. Relativity deletes leftover privilege (under-invariance
  plus connection). EML / content-only attention delete working
  structure (over-invariance) and must restore distinctions (macros,
  positions). A slogan that smashes them into one arrow is false.
  **Untested as a discriminator.** The `n=4` matrix does not contain
  an EML toy and a relativity toy on one harness.
- The **shared diagram** (global clock → local frames → relational
  comparison) is not a shared theorem. Lorentz geometry ≠ Lamport
  causality ≠ positional encodings.

If a later reader needs a one-line ownership test: anything that
follows from factorisation, the chain rule, or a cycle sum is prior
art; the taxonomy, the dual reading of leftover privilege, the
noncommutativity witness as a hierarchy-killer, and the dual-instance
claim are the bets this paper is willing to lose.

---

## 1. Why the eight-row library is not the engine

SIC §5.8 conjectured a library mapping failure signatures to minimal
structural lifts (`papers/structural_intelligence/paper.md` §5,
construct 8):

- scalar → operator
- global norm → localized measure
- quotient → restored fiber
- static → path space
- affine → projective
- point → ensemble
- non-composing → interface
- symmetry → gauge-fix

`papers/representation_repair_calculus/paper.md` made the clause a
theorem in the finite discrete case. RR-1: for each of the eight rows
there is a hand-designed finite world on which the broken representation
misses the target invariant, the lift captures it, and the lift is
minimal in the feature-tuple lattice. RR-2: independent lifts compose
when they commute. The instrument
(`experiments/representation_repair_pair`) passes four preregistered
gates.

That is real work. It is also the wrong grain.

RR-1 is **existence on authored toys**. Each row is a witness, not a
diagnostic. The paper says so: "RR-1 says nothing about *how* to
diagnose the failure signature of a real-world representation in the
first place" (limitations, same manuscript). Adding a ninth row
requires another hand-designed world. The calculus scales by
curation.

RR-2 is **composition under a commuting hypothesis**. When lifts share
a feature the informal paper sketches a pushout and stops. The Lean
core records `Independent` as pointwise equality of the two schedules.
Non-independent failures are outside the theorem.

Neither theorem is a function

```
κ : { failure signatures }  →  { minimal lifts }.
```

The graph of `κ` is not computed. It is exhibited in eight places.
"Diagnose the lost invariant, then apply the minimal lift" remains a
slogan until the diagnosis is a map.

The eight rows also hide a directional collapse. "Quotient → restored
fiber" and "symmetry → gauge-fix" look like neighbouring library
entries. They are opposite mistakes. The first deleted a distinction
the task still needed. The second retained a privilege the task did
not. Treating them as two rows of one table invites the one-ladder
reading this paper is here to kill.

So the library is not the engine. At best it is a seed catalog for a
coarser operator. At worst it is a completeness illusion: eight
worked examples, commuting when we already assumed they commute.

Possibility 2 below is the claim that this paragraph is wrong. It is
live until a test exists that the catalog cannot pass and the
taxonomy can. The banked `n=4` run is not that test.

---

## 2. The delete–obstruction–repair operator
### (and why "find a better representation" is the wrong slogan)

Fix a concrete space `X`, a deleted screen `q_D : X → Z`, and a target
`Y : X → 𝒴` (a task, an invariant, a prediction). Write `R` for a
candidate repair `R : X → ℛ`.

**Delete.** Pass to a coarser (or differently invariant) screen `q_D`.
The deletion may be of a coordinate, a privileged origin, a sequential
schedule, a named macro, a global clock. Deletion is typed by what it
identifies, not by a morality tale about "absolutes."

**Obstruction.** Ask whether `Y` still factors through `q_D`:

```
FactorsThrough q_D Y  :≡  ∀ x x',  q_D x = q_D x'  →  Y x = Y x'.
```

If yes, the deletion was free for this target. If no, the fibre of
`q_D` still carries `Y`-disagreement. That disagreement is the
obstruction. It is not a vibe. It is a pair `(x, x')` with
`q_D x = q_D x'` and `Y x ≠ Y x'`.

**Repair.** An **exact repair** is a map `R` such that `(q_D, R)`
factors `Y`:

```
ExactRepair q_D R Y  :≡
  ∀ x x',  q_D x = q_D x'  →  R x = R x'  →  Y x = Y x'.
```

`repair_splits_disagreement` is then tautological and load-bearing:
any leftover `Y`-disagreement on a `q_D`-fibre is already an
`R`-disagreement. The counting form
`|{R-values on the fibre}| ≥ |{Y-values on the fibre}|` is the
discrete `H(R | q_D) ≥ H(Y | q_D)`. We bank the split. We do not
bank Shannon theory.

This is the operator. It is not "find a better representation."

That slogan fails in three independently fatal ways.

1. **Better for whom?** SIC Theorem 4 and the abstraction frontier
   (`papers/abstraction_frontier/paper.md`, AF-1/AF-2) already say
   that task families induce a Pareto antichain, not a total order.
   Two representations can both be "right" and incomparable. "Better"
   smuggles a missing scalar.
2. **Better in which direction?** Restoring a deleted distinction and
   quotienting a leftover privilege are opposite moves. A single
   arrow cannot name both.
3. **Better by which schedule?** Delete-then-default and
   relative-then-drop disagree on a two-point witness
   (`repair_paths_disagree`). Even after the obstruction is known,
   the repair is not unique.

The slogan also pretends we can find the deletion. DR1–DR4 and the
DCR arc are the empirical record against that pretence. On toys, a
nominator can rank a load-bearing deletion once the vocabulary and
the oracle are authored. On a real pre-1905 corpus, nominating
Einstein's deletion failed under every scoring rule so tested; the
program pivoted to susceptibility and then watched its own
discussion-spike hypothesis die on Einstein 1905 and on a Darwin
pilot (`papers/dynamics_of_conceptual_deletion/paper.md` §10).
Paper A does not reopen that hunt. If you cannot name `q_D`, you
are not running this operator. You are writing history fan-fiction.

Relative identifiability
(`papers/relative_identifiability/paper.md`) is the same
obstruction in another costume: a target is identifiable from an
experiment family iff it factors through the observational quotient.
One target-distinct pair with an identical transcript is a complete
counterexample. We use that discipline. We do not re-prove it.

On orbit-canonical screens the operator specialises to a
biconditional the instrument actually checks. Let `G_M` be the
symmetry the model enforces and

```
G_Y = { g : Y(g x) = Y(x) for all x }.
```

For `q` the lex-least `G_M`-orbit map, `Y` factors through `q` iff
`G_M ⊆ G_Y`. If `G_M ⊈ G_Y`, the model identified an orbit the
target still splits: over-invariance, no-go. If `G_M ⊂ G_Y`, the
target still factors and extra coordinates remain: leftover
privilege, a cost, not an obstruction. Maximal safe symmetry
retained from the model is `G_M ∩ G_Y`. That specialisation is
SIC Theorem 4 plus a group action. It is not a new primitive, and
it is not yet a function `κ`.

---

## 3. Two directions, not one ladder

The protected assumption in the surrounding literature — the
absolute-time of this subject — is that representation change is
**one-way**. Either "always quotient" (delete the absolute, go
relational) or "always lift" (restore the fiber, add features).
SIC §5.8's eight rows sit on that ladder without saying so: seven
of them add structure; one of them gauge-fixes. The historical
analogy then smashes Einstein and Vaswani into a single deletion
story (DR1's own opening paragraph does this).

The taxonomy refuses the smash.

### 3.1 Over-invariance

A screen `q` is **over-invariant** for `Y` under an action
`act : G → X → X` when `q` is `act`-invariant and `Y` is not.

```
IsInvariant act q  ∧  ¬ IsInvariant act Y.
```

Then `Y` cannot factor through `q`. That is
`symmetry_mismatch_nogo`: the contrapositive of "factorisation ⇒
fibre-constancy" under the orbit relation. If you identified points
that the target still separates, you must **restore distinctions**.

Content-only attention that throws away position is the architectural
case. A homogeneous formula language that identifies every
macro-expansion with its denotation, then tries to search in the
quotient, is the EML case (§7). In both, the deletion removed
working structure.

### 3.2 Under-invariance

A screen `q` is **under-invariant** for `Y` when `q` is finer than
`Y` requires: leftover coordinates, a privileged origin, a preferred
rest frame, an absolute time. The identity screen always factors
every target (`identity_always_factors`). Leftover privilege is
therefore **not a no-go**. It is gauge. The repair is to **quotient
or covariantize**, not to declare the target unrepresentable.

This is the dual of the no-go and the one fact the one-ladder slogan
cannot absorb. Over-invariance blocks reconstruction. Under-invariance
does not. They are not two severities of one disease.

The instrument's `DTA_OVERREPAIR_COST` is this cell as a count: on
popcount, `q_id` has 16 fibres and `q_perm` has 5. The identity
still represents popcount. It is just expensive. That is leftover
privilege, not a proof that EML and relativity are duals.

### 3.3 Covariant compensation

Sometimes the right screen is already relational, but **naive
comparison** of local values is still meaningless. A larger local
symmetry (change of origin, change of frame, change of chart) acts
on the values themselves. Then a number at `p` and a number at `q`
are not the same type of thing until you specify transport.

On a path of relative steps `rs : List Int`, the prefix potential
is the discrete integral. A cycle closes iff the steps sum to zero
(`cycle_integrates_iff_sum_zero`). Two integrals of the same step
field differ by a constant
(`potentials_unique_up_to_translation`). That is the connection
core we actually have: discrete, one-dimensional, integer-valued.
It is Kirchhoff / discrete Poincaré. It is not Lorentz geometry,
not a principal-bundle connection, and not concern holonomy
(CG-2 in `papers/concern_as_fiber_geometry/paper.md` is a
different 1-form on a different manifold).

TA-1 sits here as a **gluing** fact, not as a repair algorithm:
charts glue iff the cocycle holds, and only up to injectivity in
the Lean core. A failed cocycle is an obstruction signature
(TA-2), not a computed lift.

The three cells do not form a score. They are a diagnosis. Mixing
them is how the slogan dies: deleting a working distinction because
you have been told to "delete the absolute," or adding a connection
because two charts disagree when the actual error was a missing
coordinate.

---

## 4. Relativity, Lamport, Transformers: a shared diagram, named disanalogies

Three stories have the same cartoon.

```
global clock / privileged origin / sequential schedule
        ↓  delete
local frames / logical clocks / content weights
        ↓  compare
relational invariant / happens-before / attention + position
```

The cartoon is useful. It is also how a false theorem gets written.

**Special relativity.** The deleted object is leftover privilege:
absolute simultaneity and a preferred rest frame. The child task
(low velocity) cannot see the deletion; the parent task
(light-speed invariance) can. DR1's toy kinematics was built to
that shape (`papers/deletion_repair_dr1/paper.md` §2.1). The
repair is not "add time back." It is a connection: Lorentz
transport between frames, Minkowski geometry as the invariant.
This is **under-invariance plus covariant compensation**.

**Lamport.** The deleted object is a global clock. The repair is
happens-before, a partial order, not a metric. Logical clocks are
a potential on a message graph. Cycle-consistency is causality,
not `c`. Identifying this with Lorentz geometry is a category
error that has already been made in print, elsewhere, often.

**Transformers / content-only attention.** The deleted object is
**working structure**: recurrence, or position, or both. Parallel
content-only attention is over-invariant for any target that
depends on order. The repair is to **restore distinctions** —
positional encodings, causal masks, recurrence in a new costume.
DR1's toy transduction was built to that shape. The deletion is
the opposite of Einstein's.

The shared diagram is therefore:

| Cell | Relativity | Lamport | Content-only attention |
|---|---|---|---|
| What was deleted | leftover privilege (absolute time / ether frame) | global clock | working order / position |
| Taxonomy cell | under-invariance + connection | under-invariance + partial order | over-invariance |
| Repair | quotient privilege; add Lorentz transport | happens-before; logical clocks | restore positions / masks / macros |
| Invariant type | metric geometry on events | causal partial order | task-relative token distinctions |
| What would be a false transfer | "attention is a Lorentz boost" | "happens-before is `ds²`" | "positions are gauge, delete them" |

Lorentz geometry ≠ Lamport causality ≠ positional encodings.
Paper A will not "unify" them. A transfer experiment that treats
them as one theorem and succeeds would be a surprise large enough
to reopen Possibility 6. A transfer that fails in the way this
table predicts is the expected, boring, honest result.

Einstein 1905 is also not a success story for *finding* the
deletion. The DCR arc could not nominate T1 from pre-1905 text
under the rules it froze. Dynamics-of-conceptual-deletion then
failed its own discussion-spike hypothesis on that paper and on
Darwin. If the historical analogy is going to earn its keep, it
will be as a **typed instance of the taxonomy**, not as a
retrieval benchmark we already lost.

---

## 5. Finite theorems (Lean)

File: `formal/structural-intelligence/StructuralIntelligence/DeleteRepair.lean`.
Pure Lean 4 core, no Mathlib, zero `sorry`. Headlines are printed
from `StructuralIntelligence.lean` via `#print axioms`.

### 5.1 Mathematical objects (claim-routing card)

| Object | Type | Domain / support | Units |
|---|---|---|---|
| `X` | `Type` | arbitrary; finite in the witness | none |
| `act : Act G X` | `G → X → X` | family of maps; **no group laws** | none |
| `q : X → Z` | screen | fibres are the identified sets | none |
| `target : X → Y` | task / invariant | unrestricted | none |
| `FactorsThrough q target` | `Prop` | relational; no chosen section | none |
| `rs : List Int` | relative steps | discrete path | integer steps |
| `prefixSum rs` | `Nat → Int` | potential along the path | same as steps |
| `ExactRepair qD r target` | `Prop` | factorisation through `(qD, r)` | none |
| `pathA`, `pathB` | maps on `Nat × Nat` | two-point witness | none |

**Quantifiers.** All headlines are finite, pointwise, and
universal in the types. No measures. No almost-sure qualifiers.
No completeness theorems for a calculus.

**Assumptions / identification.** `Act` does not require
associativity, inverses, or an identity. The no-go is about
invariance under a family of maps. Cycle integration is the
integer list sum. Exact repair is deterministic factorisation,
not a rate–distortion budget.

**Coordinate / invariance choices.** The potential's origin is
gauge: uniqueness is up to translation. Path-A's default origin
`x = 0` is a gauge-fix, which is why it disagrees with Path-B.

**Edge / null cases.** The empty step list sums to `0` and closes.
The identity screen factors every target (under-invariance is
not a no-go). A constant target is invariant under every action
and factors through every screen.

**Executable checks.** The Lean kernel is the check. The `n=4`
instrument is a second check of the same identities, not an
independent geometry. The optional Shannon form and the
measure-theoretic connection form are **not** claimed.

### 5.2 Over-invariance no-go (prior art, packaged)

**`over_invariance_nogo`.** If `q` is `act`-invariant and
`target` is a postcomposition of `q`, then `target` is
`act`-invariant.

**`symmetry_mismatch_nogo`.** If `q` is `act`-invariant and
`target (act g x) ≠ target x`, then `target` does not factor
through `q`.

Honesty: this is SIC Theorem 4-core / `commonSuffScreen_refines`
in group-action clothing. The logical primitive is
"factorisation ⇒ fibre-constancy." We do not get to name it
again.

**`invariant_orbits_factor`.** If `target` is invariant and every
`q`-fibre is an `act`-orbit, then `target` factors through `q`.
The converse direction needs the orbit-fibre hypothesis; without
it, invariance of `target` does not force factorisation through
an arbitrary invariant `q`.

### 5.3 Under-invariance is not a no-go (ours as a reading)

**`identity_always_factors`.** For every `target : X → Y`,

```
FactorsThrough (fun x => x) target.
```

A finer screen than necessary does not obstruct reconstruction.
Leftover privilege is gauge. This is the dual of the no-go. The
proof is `congrArg`. The reading is the claim: people treat
"we still have a preferred origin" as if it were
unrepresentability. It is not.

### 5.4 Discrete integration (prior art, kernel-checked)

**`path_integrates`.** On a path, the potential after `i+1`
steps is the potential after `i` plus the `i`-th relative step.

**`cycle_integrates_iff_sum_zero`.**
`prefixSum rs rs.length = 0` iff `sumInt rs = 0`.

**`potentials_unique_up_to_translation`.** Two discrete integrals
of the same step field `r` on `{0,…,n}` differ by the constant
`p 0 − q 0`.

Honesty: discrete Poincaré / Kirchhoff. The Lean file records
the integer case. It is not a relativity theorem, not a
curvature theorem, and not CG-2.

### 5.5 Repair debt (deterministic split only)

**`repair_splits_disagreement`.** If `r` is an exact repair of
`qD` for `target`, then any leftover `target`-disagreement on a
`qD`-fibre is an `r`-disagreement.

The information-theoretic inequality is standard and not banked.
The split is what an exact repair *is*.

### 5.6 Noncommutativity witness (ours as a hierarchy-killer)

Concrete world `Nat × Nat`.

- `pathA`: delete the absolute first coordinate, then write the
  default origin `x = 0`. So `pathA (x, y) = (0, y)`.
- `pathB`: form the relative `y − x`, then drop the absolute.
  So `pathB (x, y) = y − x`.

**`repair_paths_disagree`.** There exist `p, q` with
`pathA p = pathA q` and `pathB p ≠ pathB q`. Witness:
`(0,1)` and `(1,1)` share leftover `y = 1` and differ in
`y − x`.

This is "position then pool ≠ pool then position." It kills
Possibility 4 (a unique linear hierarchy of representations).
It does **not** kill or prove Possibility 1. Two disagreeing
schedules on one two-point world do not give a function from
signatures to lifts. They give a counterexample to uniqueness
of the schedule.

---

## 6. Immediate experiment: symmetry matching (banked)

Instrument: `experiments/delete_the_absolute/`.
Preregistration: `experiments/delete_the_absolute/preregistration.json`.
Receipt: `experiments/delete_the_absolute/results/delete_the_absolute_summary.json`.
World `{0,1}^4`, `|X| = 16`, exhaustive, no PRNG, no SGD.

### 6.1 What was asked

On orbit-canonical screens `q_G` (lex-least orbit representative),
does exact representability of `Y` track `G_M ⊆ G_Y`? Is leftover
privilege a fibre-count cost rather than a no-go? Must an exact
repair split mixed fibres? Do Path A and Path B disagree? Does a
4-cycle of integer steps close iff the steps sum to zero?

### 6.2 Models and tasks

Groups act by permuting positions.

| Model | Group | Screen |
|---|---|---|
| `q_id` | `{e}` | identity |
| `q_rot` | `ℤ/4` rotate-left | lex-least rotation |
| `q_perm` | `S_4` | sorted tuple (popcount fibres) |
| `q_stab0` | `Stab(0) ≤ S_4` | keep bit 0; sort the rest |

| Task | `Y` | `G_Y` (enumerated in `S_4`) |
|---|---|---|
| `bag` | popcount | `S_4` |
| `necklace` | lex-least rotation | contains `ℤ/4`, not `S_4` |
| `first_bit` | `x[0]` | `Stab(0)` |
| `identity` | `x` | `{e}` |

Representability is fibre-constancy of `Y`, not risk.

### 6.3 Representability matrix (banked)

`true` iff `Y` is constant on `q`-fibres.

|  | bag | necklace | first_bit | identity |
|---|---|---|---|---|
| `q_id` | true | true | true | true |
| `q_rot` | true | true | false | false |
| `q_perm` | true | false | false | false |
| `q_stab0` | true | false | true | false |

Fibre counts: `q_id` 16, `q_rot` 6, `q_stab0` 8, `q_perm` 5.
On `first_bit`, `G_rot ∩ G_first = {e}`. Three `q_perm` fibres
mix first-bit values; `r = first_bit` splits every leftover
disagreement; a constant dummy `r` is not an exact repair.

Path A / Path B disagree on the Lean pair `(0,1)` vs `(1,1)`
and on the sequence pair `(0,0,0,0)` vs `(1,0,0,0)`.

Holonomy: cycle `(1,-1,2,-2)` sums to 0 and closes; cycle
`(1,1,1,0)` sums to 3 and does not; two potentials differ by
the constant `p(0)-q(0)`.

### 6.4 Gates (all seven passed; noncompensatory)

| Gate | Verdict | What it actually tests |
|---|---|---|
| `DTA_NOGO` | pass (7 mismatch cells, 0 violations) | Lean `symmetry_mismatch_nogo` on this grid |
| `DTA_SAFE` | pass (9 inclusion cells, 0 violations) | Lean `identity_always_factors` / orbit factorisation |
| `DTA_OVERREPAIR_COST` | pass (16 vs 5) | leftover privilege is a count, not a no-go |
| `DTA_MINIMAL_SAFE` | pass | `Stab(0)` represents `first_bit`; `S_4` and `ℤ/4` do not |
| `DTA_REPAIR_DEBT` | pass | Lean `repair_splits_disagreement` |
| `DTA_NONCOMMUTE` | pass | Lean `repair_paths_disagree` |
| `DTA_POSITIONAL_HOLONOMY` | pass | Lean cycle-sum / translation uniqueness |

### 6.5 What this run does **not** show

It does not show a universal calculus. It does not find Einstein's
deletion. It does not identify Lorentz geometry with Lamport or
with positional encodings. It does not speak to US-4′. The
constant-grammar EML census is a companion instrument, not this
run's result. It does not contain a swap cell that applies an
over-invariance repair to an under-invariance toy and conversely.
It does not beat the eight-row catalog at anything the catalog
was not already able to name.

An adversarial reading, which we adopt: **7/7 is the expected
result if Lean is correctly transported to Python.** A fail would
have been a bug. A pass is not a promotion of Paper A's
master-object bet. The preregistration's own claim boundary
says the same: finite exact witness on `n=4`; not a general
theorem; not Shannon; not relativity; not neural.

### 6.6 What would have killed the *algebra* (and did not)

From the frozen `kill_criteria`:

- any `(G_M, Y)` with `G_M ⊈ G_Y` still fibre-constant;
- any `(G_M, Y)` with `G_M ⊆ G_Y` not fibre-constant;
- fibre counts not 16 vs 5 on popcount;
- `q_stab0` failing `first_bit`, or `q_perm` / `q_rot` representing it;
- no mixed `q_perm` fibre, or a constant `r` accepted as exact repair;
- Path A and Path B agreeing on every registered pair;
- zero-sum cycle failing to close, or nonzero-sum cycle closing.

Those killers are real for the Lean packaging. They are not
killers for the taxonomy-as-engine claim. Possibility 3 (one
ladder) and Possibility 2 (catalog is the engine) **survived
this run** because they were not on the table.

### 6.7 The test the taxonomy still owes

A later instrument — not this one — must put an EML-shaped /
content-only toy and a relativity-shaped / preferred-frame toy
on one harness and **swap the repairs**. If restoring distinctions
helps the preferred-frame toy and quotienting privilege helps
the content-only toy, Possibility 3 lives and §3 is rhetoric.
Until that swap cell exists, the dual-instance claim is a
reading.

Do not reopen DCR nomination to fill the gap. Do not train a
network. Do not treat `experiments/eml_fiber_spectrum/` as this
paper's discriminator. That package is a constant-grammar census.
US-4′ stays withheld.

---

## 7. EML as over-invariance; relativity as under-invariance

Odrzywołek (arXiv:2603.21852) shows that a single binary
operator inhabits the scientific-calculator class. Completeness
is fiber inhabitation: every calculator button is some tree.
A companion PR on this program (not present as
`papers/eml_universal_substrate/paper.md` on this branch; do
not invent the file) reads that result as SIC's master object
from the calculator side and separates expressivity from tree
size, circuit size, and Gibbs fiber mass on an `x^(2^n)` toy.
US-4′ — the claim that fiber free energy predicts EML gradient
recovery — is **untested**. The constant-grammar census is now
banked: 197 trees through 6 internal nodes (`C_0+⋯+C_6`); 145
finite closed values in 118 numerical fibers; 52 undefined
(nonpositive right-hand side or overflow); exact size-2 split
`e-1` versus `exp(e)`; five well-resolved exact cross-size
identities (optional gate, not fatal). That is a computational
spectrum of *constants*, not a 1-D invariant and not a
variable-`x` access law. Variable-`x` EML and US-4′ remain
**withheld**. Paper 0 (Lean totalisation of `Complex.log`) is a
different obstruction and is also withheld.

What Paper A needs from that laboratory is one typed sentence.

**EML / content-only search is over-invariance.** The
denotational quotient identifies trees that the *task of
finding a short witness* still separates. Macro-expansion is
a conservative extension of denotations and an exponential
change of access. Restoring a named `sq` is restoring a
distinction the denotation-screen deleted. That is cell 1.
It is the same cell as throwing away positions and then
being surprised that order-sensitive targets do not factor.

**Relativity is under-invariance plus a connection.** Absolute
simultaneity is leftover privilege. The identity on events
always factors the electromagnetic invariants; the problem is
not unrepresentability. The problem is a preferred frame that
the invariants do not need, plus the fact that time-values in
different frames are not comparable without transport. Delete
the privilege; add the connection. That is cell 2 plus cell 3.

These are **dual instances**, not rungs. The one-arrow slogan
("both delete an absolute") is false because it names the
English word "absolute" instead of the cell. Absolute time is
privilege. Absolute position in a sequence is working
structure. Deleting the first is a repair. Deleting the second
is the bug.

If a later experiment shows that restoring macros on EML and
quotienting a preferred frame are the same move on the same
matrix — same `Rep` column, same swap-cell behaviour — then
§3 dies and this section with it. Until that experiment
exists, the dual-instance claim is a **level-1 hypothesis**
with a predeclared killer, not a unification.

Concern, valence, and agency are not in this paper. Nothing
in `e^x − ln y` has valence. Nothing in a Lorentz boost has
a concern weight. CG-1/CG-2 remain the place those objects
live.

---

## 8. What would kill the thesis

Six possibilities. Kill criteria are operational. Possibility 1
is untested. Possibility 4 is already dead as a *unique linear
hierarchy*, and that death does not promote Possibility 1.
Possibility 5 is the conservative live option: we are doing SIC.

### Possibility 1 — Universal obstruction–repair calculus

**Claim.** There is a function `κ` from typed failure signatures
(the three cells, plus a finite list of obstruction witnesses)
to minimal repairs, natural in the world, computable on finite
instances, and stable under relabelling.

**Status.** **TESTED on the registered menu.** RR-1 is not this
function. The Lean core is not this function. The cheap
five-field signature is not this function. The written
`κ_screen` is Theorem 4 plus a total order. Paper F banks
`calculus_is_sic`. Possibility 1 as a *new* master object is
dead on this harness.

**Kill.** A finite family of typed failures on which no
structure-preserving map from signature to lift exists; or two
equally minimal incompatible lifts with no further diagnostic
that the frozen signature can see; or a natural family where
the winning repair is not a function of the signature we can
name without looking at the answer.

**Does not kill it.** One more hand-designed row. A commuting
pair. A green `n=4` regression. Those are necessary and
nowhere near sufficient.

### Possibility 2 — The eight-row library is the engine

**Claim.** The catalog plus commuting composition *is* the
theory. Taxonomy is a rename of rows 3 and 8.

**Kill.** Already conceptually weakened: RR-1/RR-2 do not
compute `κ`. Empirical kill is a test the catalog cannot pass
and the taxonomy can — the swap cell of §6.7. The banked run
did not ask that question. **Live.**

**Partial survival.** The catalog remains a seed even if the
taxonomy later discriminates. Paper A does not need the
library to be useless. It needs it not to be the master object.

### Possibility 3 — One ladder / same arrow

**Claim.** Over-invariance and under-invariance are two
severities of one failure. EML and relativity are the same
move. "Delete the absolute" is the right slogan.

**Kill.** The swap cell of §6.7: the typed repairs are not
interchangeable. Historical argument (not instrumented):
restoring positions is not Lorentz transport.

**Status.** **Live.** The banked matrix is compatible with a
one-ladder reading that says "match `G_M` to `G_Y`." That
biconditional does not name two arrows. Possibility 3 dies
only when opposite repairs fail on opposite toys.

### Possibility 4 — Unique linear hierarchy of representations

**Claim.** Representations form a total order. Repair is a
unique path. "Better" is well-defined.

**Status.** **Killed** as a universal claim by
`repair_paths_disagree` and `DTA_NONCOMMUTE` (and,
independently, by AF-1's antichain). Path-A and Path-B are
not ordered. SIC's Pareto frontier was already the existence
proof that "the" quotient is a fantasy.

**What this does not do.** It does not prove Possibility 1.
Non-uniqueness of the schedule is a negative theorem. A
calculus would need a further diagnostic that picks a
schedule. We do not have one.

### Possibility 5 — Task-relative Pareto (already SIC)

**Claim.** The right object is already SIC: a task-relative
sufficient screen, a compiler on the fibre, an abstraction
frontier that is an antichain (Theorems 1, 4, AF-1/AF-2).
Delete–repair is the **dynamics** of moving on that frontier
when a deletion or a lift changes the axes.

**Status.** **Live, and prior.** If this is the right reading,
Paper A does not supersede SIC. It names a typed dynamics
inside SIC. That is the conservative conclusion, and it may
be the correct one.

The `n=4` biconditional `representable iff G_M ⊆ G_Y` is
exactly Theorem 4 on a group action. That is evidence for
Possibility 5, not against it.

**Kill of the supersession reading (easy, and we accept it).**
Every delete–repair claim that survives reduces to a movement
on the SIC Pareto antichain plus Theorem 4's screen. Then the
honest title is "SIC's dynamics," not "a new master object."

**Kill of the dynamics reading (harder).** A typed
delete–repair phenomenon that cannot be expressed as a change
of `(q, K)` or of the four AF axes. We do not have one. We
are not hunting for one in this paper.

Possibility 5 is the possibility a non-adversarial draft would
bury. It is the one we should currently prefer.

### Possibility 6 — Shared theorem

**Claim.** The shared diagram is a shared mathematical theorem:
Lorentz geometry, Lamport happens-before, and positional
encodings are one object.

**Kill.** Already refused as a claim. Empirical kill: a
transfer that treats them as one theorem and **works** would
force a reopen; a transfer that fails as §4's table predicts
is the default. Either way this paper does not assert the
identification.

**Survival would look like.** A functor, with a stated
forgetful map, under which Lorentz boosts, vector-clock
updates, and positional encodings are images of one
construction, recovering each theory as a limiting case.
Nobody has written that functor. Analogies are not functors.

---

## 9. Sequencing A–F

This is Paper A. Later letters are licensed only by surviving
the previous letter's kill criteria. Three other objects are
**withheld** and are not in the A–F queue.

| Paper | Object | License | Status |
|---|---|---|---|
| **A** | Taxonomy + honesty ledger + Lean core + `n=4` regression | none; this document | Lean banked; instrument banked as regression |
| **B** | Swap-cell instrument: EML-shaped restore vs relativity-shaped delete, same harness | A does not get to claim discrimination until the swap cell exists | banked (`papers/delete_repair_swap/`; `taxonomy_holds`; pairing of A's matrix, not new enumeration) |
| **C** | Connection beyond `List Int` (graph 1-forms, chart transport) | B shows cell 3 is not idle Kirchhoff-packaging | banked (`papers/delete_repair_connection/`; `cell3_holds`; Aff(1, Z/3) escapes sum-b; not Lorentz) |
| **D** | Shared-diagram disanalogy: a transfer that *should* fail across Lorentz / Lamport / PE | B does not collapse to one arrow | banked (`papers/delete_repair_disanalogy/`; `disanalogy_holds`; 196 diamonds, four `s²` values; not a functor) |
| **E** | Assumption-surgery benchmark for agents (typed delete/repair, not text nomination) | B–D survive; DR/DCR stay closed | banked (`papers/delete_repair_surgery/`; `surgery_killed`; unused symmetry ≠ leftover privilege; not an LLM) |
| **F** | Universal calculus (Possibility 1) | B–E survive; `κ` is specified before it is fitted | banked (`papers/delete_repair_kappa/`; `calculus_is_sic`; the written function is Theorem 4 plus a total order) |

**Withheld, not sequenced.**

- **Paper 0** (EML in Lean / `Complex.log 0` totalisation). A
  different obstruction. Not a delete–repair theorem.
- **US-4′** (fiber free energy predicts EML gradient recovery).
  Untested. Not this paper's claim.
- **Variable-`x` EML spectrum** (no 1-D degree invariant; cannot
  be DP'd). The constant-grammar census exists; the free-`x`
  access estimate does not. Withheld.

No letter after A is authorised by A's existence. A without B
is a reading plus a kernel check plus a Python regression.
Readings are cheap. Regressions are cheaper.

---

## 10. Claim boundary

**Claim level (this paper).** Level 1 for the taxonomy as a
discriminator (plausible, not instrumented against a one-ladder
alternative). Level 2 for the finite Lean facts as *algebraic*
statements (kernel-checked and re-run on `n=4`, prior-art-honest).
Level 0 for any universal calculus, any historical retrieval,
any EML-native access law, and any shared theorem across
physics / distributed systems / attention.

**Supported now.**

- `symmetry_mismatch_nogo` and its dual
  `identity_always_factors`, as finite algebra, with the
  Theorem-4 packaging disclosed, re-run as `DTA_NOGO` /
  `DTA_SAFE`.
- Discrete cycle integration and uniqueness up to translation,
  as integer Kirchhoff, with the Poincaré name disclosed,
  re-run as `DTA_POSITIONAL_HOLONOMY`.
- Deterministic repair-split, with the chain-rule name
  disclosed, re-run as `DTA_REPAIR_DEBT`.
- A two-point witness that two repair schedules disagree,
  re-run as `DTA_NONCOMMUTE`.
- Leftover privilege as a fibre-count cost on popcount
  (16 vs 5), `DTA_OVERREPAIR_COST`.
- Constant-grammar EML census through `k=6`: Catalan-complete;
  size is not a denotation invariant. Computational, not US-4′.
- The negative claim that RR-1/RR-2 are not `κ`.
- The negative claim that DR/DCR did not find Einstein's
  deletion automatically.
- The negative claim that Lorentz ≠ Lamport ≠ positional
  encodings.

**Withheld.**

- Possibility 1 (`κ`).
- US-4′ and the variable-`x` EML spectrum.
- Paper 0.
- Any assertion that the taxonomy *discriminates* EML from
  relativity until the swap cell exists.
- Any assertion that we can nominate deletions from text.
- Any valence, concern, agency, or consciousness claim.
- Any identification of this finite connection with Lorentz
  geometry or with CG-2 holonomy.
- Any claim that 7/7 gates promote the master-object bet.

**What would change the conclusion.**

- Swap cell null ⇒ drop the dual-instance claim; revert to
  Possibility 3 or 5.
- Catalog domination on a test the taxonomy was supposed to
  win ⇒ drop "taxonomy is the master object"; keep the Lean
  file as SIC hygiene.
- A computed `κ` that survives relabelling ⇒ reopen
  Possibility 1 (that would be a promotion, not a rescue).
- A functor unifying Lorentz / Lamport / PE ⇒ reopen
  Possibility 6.
- A delete–repair phenomenon that cannot be written as a
  movement of `(q, K)` ⇒ Possibility 5's dynamics reading
  dies, and we would have something new. We do not have it.

**Preferred present tense.** Delete–repair is a typed dynamics
inside SIC, with a finite algebraic core, a Python regression
of that core, and a historical slogan that is false. The
master-object upgrade is a bet. Possibility 5 is the house.

---

## Discovery-loop block

### Current frame

SIC already has a master fibration `(q, K)`, a common-sufficient
screen (Theorem 4), a Pareto antichain of quotients (AF-1/AF-2),
a catalog of eight lifts (RR-1/RR-2), and a cocycle test for
gluing charts (TA-1). The accepted debugging move is "find a
better representation" or "apply the matching row." The
accepted historical cartoon smashes relativity and attention
into one deletion. A parallel temptation, after a green `n=4`
run, is to treat the regression as a discovery.

### Assumption ledger

| Assumption | Type | Load-bearing? | Why believed | Break test |
|---|---|---:|---|---|
| Representation change is one-way | Ontology | high | "Delete the absolute" slogan; seven of eight RR rows add features | Swap cell (§6.7) |
| The eight-row library is `κ` | Causal | high | SIC §5.8 wording | Ask for the function; RR-1 is existence |
| Leftover privilege is unrepresentability | Ontology | high | Ether / absolute-time rhetoric | `identity_always_factors`; 16 vs 5 |
| EML and relativity are the same arrow | Invariance | high | Shared English word "absolute" | Dual-instance table (§4, §7) |
| Shared diagram ⇒ shared theorem | Boundary | high | Cross-domain prestige | Name the functor or withdraw |
| We can find the deletion | Measurement | high | DR opening bet | DR/DCR record |
| "Better" is a scalar | Measurement | high | Benchmark habit | AF-1 antichain; `pathA` ≠ `pathB` |
| Cycle integration is a new geometry | Pragmatic | no | Connection language | Kirchhoff / discrete Poincaré |
| A green `n=4` run promotes the taxonomy | Pragmatic | high | Confirmation habit | §6.5 |
| Delete–repair supersedes SIC | Boundary | high | New-paper incentive | Possibility 5 |
| US-4′ is this paper | Boundary | no | Adjacent PR | Withheld |

### Anomaly map

| Anomaly | Why it strains the frame | Assumption implicated | Artifact risk | Cluster |
|---|---|---|---|---|
| RR-1 is eight authored toys | No map from signature to lift | Library is `κ` | Toys were designed to fit | Catalog ≠ engine |
| `identity_always_factors` | Privilege does not block reconstruction | Privilege = unrepresentability | None (one-line proof) | Dual of no-go |
| `repair_paths_disagree` | Two repairs, one world | Unique hierarchy; "better" | Costume witness? | Possibility 4 |
| DR1–DR4 / DCR nulls | Cannot nominate T1 | We can find the deletion | Extractor / residue / ties | Historical retrieval |
| DCR4 / DCD1: discussion-spike dies | Revolutionary paper is not the spike | Susceptibility-as-peak | Verifier variance | Same cluster |
| EML access collapse at constant expressivity | Completeness ≠ search | One ladder; denotation is enough | Training overflow (EML lab) | Over-invariance |
| Lorentz / Lamport / PE look alike | Cartoon transfers; theorems do not | Shared theorem | Metaphor | Possibility 6 |
| TA-1 needs injectivity in Lean | Informal `↔` was too strong | Slogan over core | Proof engineering | Honesty |
| 7/7 gates on a Lean transport | Looks like confirmation | Green run = promotion | Authored world | Possibility 2/3 still live |

### Candidate reframes

| Move | Assumption killed | Replacement | What becomes simpler | What must be recovered | Falsifier |
|---|---|---|---|---|---|
| Taxonomy as master object | One-way repair | Three cells | EML vs relativity stop colliding | RR rows as instances, not engines | Swap cell null |
| Privilege is gauge | Privilege = no-go | `identity_always_factors` | Under-invariance is not a tragedy | Still need a connection when comparison is untyped | Identity fails to factor some `Y` |
| Dual instances | Same-arrow slogan | Opposite repairs | Historical smash dies | Shared *diagram* remains as pedagogy | Swap succeeds both ways |
| SIC dynamics (Possibility 5) | Supersession | Delete–repair as frontier motion | No second master object | Lean core as hygiene | A phenomenon outside `(q, K)` |
| Refuse shared theorem | Diagram = theorem | Named disanalogies | Stops fake unification | Each domain's actual invariant | A working functor |

The last two reframes are **strictly more conservative** than
the first. An adversarial reader should prefer them until B
lands.

### Discriminating predictions

| Condition | Old frame | New frame | Diagnostic |
|---|---|---|---|
| Apply position-restore to a preferred-frame toy | Should help ("better rep") | Should fail (wrong cell) | Swap cell (not yet run) |
| Apply origin-deletion to a content-only toy | Should help | Should fail | Swap cell (not yet run) |
| `pathA` vs `pathB` on `(0,1)/(1,1)` | One canonical repair | Disagreement | Lean + `DTA_NONCOMMUTE` |
| `G_M ⊈ G_Y` still factors | Possible if "better" is loose | Impossible | `DTA_NOGO` (regression) |
| Nominate T1 from pre-1905 text | In-scope success | Out of scope; expected fail | Already failed |
| Transfer Lorentz proof to Lamport | Shared theorem | Fail at metric vs poset | Paper D |
| Catalog-only vs taxonomy-typed repair | Catalog wins | Taxonomy wins on swap | Paper B |

### Severe experiment with kill criteria

The **banked** experiment (§6) is severe for the Lean packaging
and mild for the thesis. Kill criteria: the seven `DTA_*`
gates. All passed. Interpretation bound: regression, not
promotion.

The **owed** severe experiment is the swap cell (§6.7). That
cell is now banked at `papers/delete_repair_swap/`: opposite
repairs are not interchangeable on this harness. Kill remains
the same if a later cube makes the crossed cells work. Do not
start Paper F. Paper C is next.

### Claim boundary

§10. Lean algebra banked and prior-art-tagged. `n=4` regression
banked. Paper B swap cell banked as a discriminator contract
on that matrix. Possibility 1 untested. Possibility 5
preferred. Paper 0 withheld. US-4′ is process-split in
companion notes, not this manuscript's claim.

### Next best test

A–F are banked. The written κ is SIC, not a new master object.
Possibility 5 is the close. Do not reopen DCR nomination. Do
not turn this into an LLM leaderboard. Do not fit a fancier
cheap signature to erase the collision.

---

## References

- Odrzywołek, A. (2026). All elementary functions from a single binary operator. arXiv:2603.21852.
- Halmos, P. R., & Savage, L. J. (1949). Application of the Radon–Nikodym theorem to the theory of sufficient statistics. *Annals of Mathematical Statistics* 20(2), 225–241.
- Einstein, A. (1905). Zur Elektrodynamik bewegter Körper. *Annalen der Physik* 17, 891–921.
- Lorentz, H. A. (1904). Electromagnetic phenomena in a system moving with any velocity smaller than that of light.
- Lamport, L. (1978). Time, clocks, and the ordering of events in a distributed system. *CACM* 21(7), 558–565.
- Vaswani, A., et al. (2017). Attention is all you need. *NeurIPS*.
- Brown, J. (2026). The Structural Intelligence Conjecture. `papers/structural_intelligence/paper.md`. Especially §5.8.
- Brown, J. (2026). Representation-Repair Calculus. `papers/representation_repair_calculus/paper.md`. RR-1, RR-2.
- Brown, J. (2026). The Theory Atlas. `papers/theory_atlas/paper.md`. TA-1.
- Brown, J. (2026). The Abstraction Frontier. `papers/abstraction_frontier/paper.md`. AF-1, AF-2.
- Brown, J. (2026). DR1. `papers/deletion_repair_dr1/paper.md`.
- Brown, J. (2026). The Dynamics of Conceptual Deletion. `papers/dynamics_of_conceptual_deletion/paper.md`.
- Brown, J. (2026). DCR1. `papers/date_cut_retrodiction_dcr1/paper.md`.
- Brown, J. (2026). DCR4. `papers/date_cut_retrodiction_dcr4/paper.md`.
- Brown, J. (2026). Relative Identifiability. `papers/relative_identifiability/paper.md`.
- Brown, J. (2026). Concern as Fiber Geometry. `papers/concern_as_fiber_geometry/paper.md`. CG-2 (not this paper's connection).
- Lean core: `formal/structural-intelligence/StructuralIntelligence/DeleteRepair.lean`.
- Theorem 4 core: `formal/structural-intelligence/StructuralIntelligence/CommonSuffScreen.lean`.
- Instrument: `experiments/delete_the_absolute/` (7/7 gates, `n=4` regression).
- Conceptual companion (other PR, not on this branch): EML as a universal substrate; Odrzywołek's completeness plus a squaring-separation toy. Do not treat that file as present here.
