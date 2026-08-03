# Representation-Repair Calculus

## A partial function from failure signatures to minimal structural lifts

**Jawaun Brown**
Human author and research director

**Claude Code (agent)**
Experiment code, analysis, and manuscript production under direction and review

**Date:** August 3, 2026
**Status:** two theorems + one exact worked example. Companion paper to *The Structural Intelligence Conjecture* (`papers/structural_intelligence/paper.md`); depends on Theorem 1 of that paper (existence of the master fibration) and instantiates the extended-program clause section 5.8 as a theorem.

---

## Abstract

Extended-program clause section 5.8 of *The Structural Intelligence
Conjecture* conjectures a **library** mapping known failure signatures
of representations to their **minimal structural lifts**:

- scalar to operator,
- global norm to localized measure,
- quotient to restored fiber,
- static to path space,
- affine to projective,
- point to ensemble,
- non-composing to interface,
- symmetry to gauge-fix.

The clause promises to turn the vague debugging move "try another
representation" into the disciplined move "diagnose the lost invariant,
then apply the minimal lift". This paper makes the clause a theorem in
the finite discrete case, with two theorems and one exact instrument.

- **Theorem RR-1 (Lift table is well-defined).** *For each of the eight
  canonical failure signatures in section 5.8, there is a hand-designed
  finite world on which (a) the broken representation ``R`` misses the
  target invariant ``I``, (b) the lifted representation ``R'`` captures
  ``I``, and (c) ``R'`` is minimal: no strictly smaller enlargement of
  ``R`` also captures ``I``.* Case-by-case verification.
- **Theorem RR-2 (Lifts compose).** *If a lift ``R -> R'`` repairs
  failure ``F_1`` and a lift ``R' -> R''`` repairs failure ``F_2``, and
  the two failures are independent (their lifts commute on the product
  world), then ``R -> R''`` repairs both simultaneously.* Follows from
  the pushout construction on feature-tuple representations; witnessed
  exactly on the product of the scalar->operator and static->path
  worlds.

The instrument (`experiments/representation_repair_pair`) exhibits the
eight canonical pairs and the composition witness with four pre-registered
gates, all of which pass exactly.

---

## 1. Setup

Fix a finite state space ``S``. A **representation** ``R : S -> F`` is a
map from states to a finite ordered tuple of feature values (each feature
is a pure function ``S -> Value``). Two representations ``R`` and ``R'``
are related by ``R <= R'`` (``R`` refines-below ``R'``) iff every feature
of ``R`` is also a feature of ``R'`` -- equivalently, the feature-set of
``R`` is a subset of the feature-set of ``R'``. Under this ordering the
finite representations on ``S`` form a lattice with the empty
representation at the bottom and the "all possible features" at the top.

A **target invariant** ``I : S -> V`` is another map from states to some
value space ``V``. A representation ``R`` **captures ``I``** iff ``I``
factors through ``R``:

```
for every s, s' in S:   R(s) = R(s')  ==>  I(s) = I(s').
```

``R`` **misses ``I``** iff it does not capture ``I``: there exist
``s, s'`` with the same ``R``-value but different ``I``-values.

Given a broken representation ``R`` that misses ``I``, a **structural
lift** is a representation ``R'`` with ``R <= R'`` that captures ``I``.
The lift is **minimal** iff no proper sub-representation of ``R'``
strictly enlarging ``R`` also captures ``I``. Concretely: let
``A = features(R') \ features(R)`` be the *added* components; the lift is
minimal iff for every nonempty subset ``D`` of ``A``, the representation
``R + (A \ D)`` still misses ``I``.

The **representation-repair calculus** is the partial function

```
kappa :  { failure signatures }   -->   { minimal lifts }
```

whose graph is a library of ``(failure_signature, minimal_lift)`` pairs.
Section 5.8 of the parent paper conjectures a specific eight-row seed
for this graph. This paper shows the seed is well-defined and that its
rows compose.

---

## 2. Theorem RR-1: lift table is well-defined

**Setup (RR-1).** For each of the eight canonical rows of the calculus
listed below, we exhibit a finite state space ``S``, a target invariant
``I``, a broken representation ``R``, and a lifted representation ``R'``.
The witness demonstrates three properties: ``R`` misses ``I``, ``R'``
captures ``I``, and no strictly smaller enlargement of ``R`` below ``R'``
captures ``I``.

**Theorem RR-1 (Lift table is well-defined).** *For each of the eight
canonical failure signatures (scalar -> operator, global norm -> localized
measure, quotient -> restored fiber, static -> path space, affine ->
projective, point -> ensemble, non-composing -> interface, symmetry ->
gauge-fix), the pair ``(R, R')`` given in section 3 of this paper is a
witness that ``R`` misses the corresponding target invariant, ``R'``
captures it, and ``R'`` is a minimal enlargement of ``R`` in the
representation lattice.*

**Proof.** Case-by-case verification on the finite witness worlds of
section 3. Every check is a finite enumeration (drop-set minimality is
exhaustive over the ``2^|A| - 1`` nonempty subsets of the added
components) and is executed exactly by the companion instrument
(`experiments/representation_repair_pair`). All four pre-registered
gates pass: 8/8 broken representations miss the invariant, 8/8 lifted
representations capture it, and 8/8 lifts are minimal.

**Consequence (operational).** The extended-program clause section 5.8
is a *theorem* in the finite discrete case: the eight rows are not
programmatic aspirations but genuine, minimal, invariant-restoring
lifts. Adding a new row to the calculus requires exhibiting a witness
world satisfying the same three properties.

**Remark (uniqueness up to isomorphism).** The witnesses in section 3
are one *concrete* choice per row; the theorem asserts existence and
minimality, not uniqueness of the lifted rep. Two different minimal
lifts of the same broken rep can exist; the calculus records a canonical
one for each row. On the eight witness worlds of section 3, the minimal
lifts are unique among the natural candidate features (the theorem is
stated up to isomorphism of feature-tuple representations).

---

## 3. Case-by-case witnesses

Each row uses a small finite world (6 to 16 states) and lists a broken
representation ``R`` (missing the invariant) and a lifted representation
``R'`` (capturing the invariant with a minimal set of added features).
Full arithmetic is in the companion instrument's `core.py`.

**Case 3.1: scalar -> operator.** ``S`` = six pure single-qubit Bloch
states ``{|0>, |1>, |+>, |->, |i>, |-i>}``. Invariant
``I(s) = (<X>_s, <Y>_s, <Z>_s)``. Broken ``R = (<Z>,)``: merges ``|+>``
and ``|->`` (both ``<Z> = 0``) but their ``<X>`` differ, and merges
``|i>`` and ``|-i>``. Lifted ``R' = (<Z>, <X>, <Y>)``: the full Bloch
vector, an operator-valued observable via ``<A> = Tr(rho A)``. Minimal:
dropping any of the three axes creates a state pair with equal reduced
rep but different Bloch vector.

**Case 3.2: global norm -> localized measure.** ``S`` = six mass profiles
``(m_0, m_1, m_2)`` on three cells:
``s_1..s_6 = (1,5,7), (2,5,7), (3,1,7), (3,2,7), (5,5,1), (5,5,2)``.
Invariant ``I(s) = (m_0, m_1, m_2)``. Broken ``R = (support_size,)``:
all six states have support 3, so ``R`` merges everything. Lifted
``R' = (support_size, m_0, m_1, m_2)``: the localized measure. Minimal
by construction: the ``(s_1, s_2)`` pair collides on
``(support, m_1, m_2)``, forcing ``m_0`` to be essential; ``(s_3, s_4)``
forces ``m_1``; ``(s_5, s_6)`` forces ``m_2``.

**Case 3.3: quotient -> restored fiber.** ``S = {0, 1}^3`` (eight states)
with coarse coordinate ``z = state[0]`` and fiber coordinates ``x, y``.
Invariant ``I(s) = s`` (full tuple). Broken ``R = (z,)``: merges the
four states in each fiber. Lifted ``R' = (z, x, y)``: restores the
fiber. Minimal: any drop creates a merge across a distinguishing bit.

**Case 3.4: static -> path space.** ``S = {0, 1}^3`` = eight length-3
binary trajectories. Invariant ``I(s) = s`` (full trajectory). Broken
``R = (current,) = (state[2],)``: throws away history. Lifted
``R' = (current, t0, t1)``: current-step observable together with the
past two coordinates. Minimal by symmetric argument to case 3.3.

**Case 3.5: affine -> projective.** ``S`` = six projective points
``(a : b : c)`` including a finite point ``(2, 3, 1)`` and a point at
infinity ``(2, 3, 0)`` (a "line direction"). Invariant
``I(s) = (a, b, c)``. Broken ``R = (a, b)`` (the affine chart with
``c = 1`` implied): merges the finite point ``(2, 3, 1)`` with the
point at infinity ``(2, 3, 0)`` because both drop to ``(2, 3)``. Lifted
``R' = (a, b, c)``: the homogeneous coordinate, restoring the
distinction. Minimal: added ``{c}`` is essential (the whole reason the
lift exists).

**Case 3.6: point -> ensemble.** ``S`` = eight distributions labelled by
``(mean, variance, skew) in {0,1} x {1,2} x {0,1}``. Invariant
``I(s) = (mean, var, skew)``. Broken ``R = (mean,)``: distributions with
the same mean but different higher moments merge. Lifted ``R' = (mean,
var, skew)``: the ensemble moment vector. Minimal: dropping ``var`` or
``skew`` merges same-mean same-other pairs whose invariant differs.

**Case 3.7: non-composing -> interface.** ``S`` = 16 module-pair
configurations ``(m_1, m_2, family, version)`` on
``{P, Q} x {P, Q} x {json, grpc} x {1, 2}``. Invariant ``I(s) =
(m_1, m_2, family, version)``. Broken ``R = (m_1, m_2)``: the raw module
identity pair, unable to distinguish handshake protocols. Lifted
``R' = (m_1, m_2, family, version)``: the interface is exactly the
protocol tag added on top of the raw pair. Minimal: dropping ``family``
merges json/grpc pairs; dropping ``version`` merges v1/v2 pairs; each
merges states of different invariant.

**Case 3.8: symmetry -> gauge-fix.** ``S`` = six configurations
``(a, b, c)`` under translation symmetry ``(a, b, c) ~ (a+t, b+t, c+t)``:
``{(0,1,2), (1,2,3), (0,2,1), (5,7,6), (0,0,0), (0,1,1)}``. The physical
invariant is the orbit label ``I(s) = (a-b, a-c)`` (translation-invariant).
Broken ``R = (a,)``: the gauge-dependent scalar; four states share ``a
= 0`` but have three distinct orbit labels. Lifted ``R' = (a, a-b,
a-c)``: adds the two gauge-invariant offsets that pin the orbit. Minimal:
dropping ``a-b`` merges the states with ``a = 0`` and equal ``a-c`` but
different orbits (e.g. ``(0,2,1)`` vs ``(0,1,1)``); dropping ``a-c``
merges the symmetric pair.

All eight rows pass the three checks exactly; see
`experiments/representation_repair_pair/results/representation_repair_pair_summary.json`
for the full drop-set records.

---

## 4. Theorem RR-2: lifts compose

**Setup (RR-2).** Suppose two failure signatures ``F_1, F_2`` are
*independent*: their broken representations ``R_1, R_2`` act on disjoint
slots of a product world ``S_1 x S_2`` (equivalently, the two lifts
``L_1: R_1 -> R_1'`` and ``L_2: R_2 -> R_2'`` share no feature name).
Define the composite representations pointwise:

```
R    (s_1, s_2)  =  (R_1(s_1),   R_2(s_2))
R''  (s_1, s_2)  =  (R_1'(s_1),  R_2'(s_2))
```

with the composite invariant ``I(s_1, s_2) = (I_1(s_1), I_2(s_2))``.

**Theorem RR-2 (Lifts compose).** *If ``F_1, F_2`` are independent, then*

- *``R`` misses ``I`` (in fact misses both ``I_1`` and ``I_2``);*
- *``R''`` captures ``I`` (and captures both ``I_1`` and ``I_2``
  simultaneously);*
- *``R''`` is minimal on the product world: dropping any added feature
  of ``R''`` (whether it came from ``L_1`` or ``L_2``) breaks capture
  of the composite invariant;*
- *the composite lift is invariant under the ordering of ``L_1`` and
  ``L_2``: applying ``L_1`` first and ``L_2`` second gives the same
  captured invariant as applying ``L_2`` first and ``L_1`` second (the
  two lifts commute).*

*If the two failures interact (their lifts share a feature name), the
composite lift is at least as informative as either one alone (a
categorical pushout in the representation lattice).*

**Proof (independent case).** The product-world semantics of a feature
tuple ``(F_1(s_1), F_2(s_2))`` factors through the disjoint-slot
product: two composite states agree on their feature-tuple iff they
agree slot-wise. By the individual-lift theorems (Theorem RR-1 applied
to each row), ``R_1`` misses ``I_1`` and ``R_2`` misses ``I_2``, so
their product ``R`` misses both ``I_1`` and ``I_2``; and ``R_1'``
captures ``I_1``, ``R_2'`` captures ``I_2``, so ``R''`` captures both.
For the composite invariant ``I(s_1, s_2) = (I_1(s_1), I_2(s_2))``:
capture reduces to slot-wise capture (the composite invariant factors
through ``R''`` iff each slot's invariant factors through the
corresponding sub-representation of ``R''``). Minimality on the product
follows from minimality on each slot: dropping an added feature of
``L_1`` breaks capture of ``I_1`` on the ``S_1``-slot (and therefore
capture of the composite ``I``); symmetrically for ``L_2``. Ordering
invariance is immediate from the disjoint-slot factorisation: the
feature tuples ``L_2(L_1(R))`` and ``L_1(L_2(R))`` are permutations of
the same set of features and induce the same partition of the state
space.

**Proof (interacting case).** If ``L_1`` and ``L_2`` share a feature
``f``, the composite lift is not simply the disjoint union but the
pushout of the two lifts along the shared feature: features are
identified if they carry the same name, and the resulting composite
representation is the finest representation that has both ``R_1'`` and
``R_2'`` as sub-representations. This pushout representation is at
least as informative as either ``R_1'`` or ``R_2'`` (both are
sub-representations of the pushout), so it captures at least what
either lift alone captures. The pushout may or may not be minimal for
either sub-invariant; when both lifts share a feature that is essential
for one but not both, the composite is *strictly* more informative than
either. Full pushout construction is a straightforward exercise in the
feature-set lattice.

**Consequence (operational).** The eight canonical rows are not
mutually exclusive: any two independent failures can be repaired
simultaneously by composing their lifts, and the composite is again a
minimal lift when the two rows are disjoint in their added features.
The calculus is therefore closed under independent composition.

---

## 5. Worked composition: scalar->operator combined with static->path

Take ``S_1`` = the six Pauli states of case 3.1, and ``S_2`` = the eight
length-3 binary trajectories of case 3.4. The composite world has
``6 x 8 = 48`` states. The composite invariant is

```
I(pauli, path)  =  ( (<X>_pauli, <Y>_pauli, <Z>_pauli),  (path[0], path[1], path[2]) ).
```

Composite broken:

```
R  (pauli, path)  =  ( <Z>_pauli,  path[2] )     (two scalar observables, one per slot)
```

Composite lifted:

```
R''  (pauli, path)  =  ( <Z>_pauli, <X>_pauli, <Y>_pauli,   path[2], path[0], path[1] )
```

Added features: ``{<X>, <Y>, path[0], path[1]}``. All four gates of
Theorem RR-2 pass exactly (see the composition record in the summary
JSON):

- ``R`` misses ``I`` on both slots and misses the composite ``I``.
- ``R''`` captures ``I`` on both slots and captures the composite ``I``.
- Dropping any of ``<X>``, ``<Y>``, ``path[0]``, ``path[1]`` breaks
  capture of the composite invariant.
- Two application orderings (Pauli-lift-first vs path-lift-first) give
  the same captured invariant.

The instrument computes both trajectories exactly on the 48-state
composite world.

---

## 6. Instrument: `experiments/representation_repair_pair`

Exact witness of Theorems RR-1 and RR-2:

- **RR-1.** For each of the eight canonical rows, evaluate broken and
  lifted representations on the row's witness world and verify that (a)
  broken misses ``I``, (b) lifted captures ``I``, and (c) every
  nonempty subset of added components is essential to capture (the
  minimality drop set).
- **RR-2.** Build the product world ``PauliStates x PathStates`` (48
  states), evaluate the composite broken and composite lifted
  representations, and verify all four composition subclauses.

The four pre-registered gates:

1. `rr1_every_canonical_pair_broken_representation_misses_invariant`
   (8/8).
2. `rr1_every_lifted_representation_captures_invariant` (8/8).
3. `rr1_every_lift_is_minimal` (8/8).
4. `rr2_two_independent_lifts_compose`.

All four pass exactly on first run; the benchmark is deterministic, no
randomness, and completes in under a second.

---

## 7. Relation to the SIC framework

Theorem RR-1 promotes the extended-program clause section 5.8 of the
parent paper from a *research direction* ("a library mapping failure
signatures to minimal structural lifts") to a *theorem* in the finite
discrete case, with a concrete witness for each of the eight canonical
rows. Theorem RR-2 gives the compositional structure of the calculus:
independent lifts compose to a minimal joint lift, and interacting
lifts compose to a pushout that is at least as informative as either
sub-lift alone.

Together with

- Theorems CG-1, CG-2 (Fisher geometry and holonomy of concern from
  *Concern as Fiber Geometry*),
- Theorems CT-1, CT-2 (MDL identifiability and Boltzmann ecology from
  *Compiler Tomography*),
- Theorem SA-1 (antecedent taxonomy from *Sufficient Antecedents for
  Cross-Task Stability*),
- Theorems AF-1, AF-2 (Pareto antichain from *The Abstraction Frontier*),
- Theorems AG-1, AG-2 (viability governance from *Alignment as Ensemble
  Governance*),

Theorems RR-1 and RR-2 give the SIC extended program another explicit
theorem-instrument pair on top of the seven of the parent paper. The
remaining section 5 constructs (theory atlas section 5.5, causal
semantics section 5.7, autocatalytic artwork section 5.10) remain open
to further companion papers.

---

## 8. Limitations

- **Finite discrete witnesses.** The theorems are stated for finite
  state spaces with finite feature tuples; the extension to continuous
  representation spaces would replace the drop-set enumeration with a
  ``sigma``-algebra-level minimal-sufficiency argument (Halmos-Savage
  minimal sufficiency for the representation lattice). We do not prove
  the continuous version here.
- **Canonical rows only.** The eight rows are the seed proposed by the
  parent paper. Real failure catalogues from machine learning have far
  more rows (mode collapse, adversarial fragility, distributional
  shift, ...). The calculus scales by adding rows with matching
  witnesses; we do not claim completeness.
- **Independence assumption for RR-2.** The clean product-world proof
  requires disjoint-slot independence of the two lifts. For interacting
  lifts we sketch the pushout construction; a full formal treatment
  (categorical pushout in the representation lattice, with the
  associated universal property) is standard but not developed here.
- **No Lean formalisation.** The elementary case-by-case verification
  is straightforward to formalise (parallel to Theorem 5's Lean core
  in `formal/structural-intelligence/StructuralIntelligence/`), but
  that work is not yet done.
- **Not an alignment technology.** RR-1 says nothing about *how* to
  diagnose the failure signature of a real-world representation in the
  first place. That is where the actual work of representation debugging
  lies. The theorem tells you what the minimal lift looks like *once
  you know which row of the calculus you are in*.

---

## 9. Reproduction

```bash
python3 experiments/representation_repair_pair/experiment.py
```

Full development is in the parent paper's section 5.8 and the master
notes file `notes/structural_intelligence_conjecture.md`.
