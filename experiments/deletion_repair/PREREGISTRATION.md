# DR1 — Deletion-Repair Nomination on Toy Systems (frozen preregistration)

**Package:** `experiments/deletion_repair/`
**Status:** frozen 2026-07-24, BEFORE any scoring row was generated
**Class:** smallest working example. Not a discovery claim.
**Human director:** Jawaun Brown

## 0. The object

A discovery-shaped move is modelled as: hold a representation `R` that works on
a child task `α`, delete an over-specification `D ⊆ R_deletable`, repair with
`r`, and thereby cover a parent task `ω` that `R` could not.

DR1 tests **one** thing: whether a *nominator* — a cheap, execution-free
scoring function over candidate deletions — ranks the load-bearing deletion
highly, against an exhaustive oracle, on toy systems where the answer is known.

DR1 does **not** discover anything. Both canonical cases (relativity,
attention) are already discovered; they are validation targets, not goals.
DR1's toys are miniatures of their *shape*, not of their content.

## 1. The structural hypothesis under test

The motivating claim is that **one nominator is not enough**:

- **Weakness gain** — how much the extension (the set of hypotheses consistent
  with `R`) grows when `D` is removed. Catches over-specifications that block
  *coverage* of `ω`.
- **Cost attribution** — how much a resource bound improves when `D` is
  removed. Catches over-specifications that block *reachability* of `ω`.

**H1.** There exist discovery-shaped cases nominated by weakness but not cost,
and cases nominated by cost but not weakness. Therefore a single-objective
nominator misses at least one.

**H2.** A disjunctive nominator (`max` of the two, after per-toy normalisation)
ranks the load-bearing deletion at least as highly as the better single
nominator on **both** toys.

## 2. The two toys

Both expose the same interface: a finite hypothesis space `H`, a set of
propositions each acting as a predicate filtering `H`, a child task `α`, a
parent task `ω`, and a cost model.

### TK — Toy Kinematics (relativity-shaped)

`H` is a grid of coordinate transformations between frames at relative
velocity `v` (units `c = 1`), parameterised so `k = 0` is the Galilean member
and `k = 1` is the Lorentz member. Propositions include absolute simultaneity,
absence of length contraction, a preferred rest frame, invariant mass,
unbounded velocity, orientation preservation.

- `α`: predictions at `v ∈ {0.01, 0.02, 0.05}`. Galilean and Lorentz agree to
  tolerance here, so **α does not discriminate** — this is the
  over-specification-fitted-to-the-child-task condition.
- `ω`: adds light-propagation invariance — a ray with `x = t` must satisfy
  `x' = t'` at every `v`. Only the Lorentz member satisfies it.

**Expected nomination:** deleting absolute simultaneity enlarges the extension
to include the Lorentz member ⇒ **weakness fires**. Cost is flat across TK's
hypotheses ⇒ **cost is silent**.

### TT — Toy Transduction (attention-shaped)

`H` is a set of computation schemes over sequences, each with an access
pattern and a parallel-depth cost. Propositions include sequential state
update, causal masking, bounded state, absence of explicit position input.

- `α`: short sequences under a loose depth budget. Sequential and parallel
  schemes both pass.
- `ω`: long sequences under a **parallel-depth budget** that sequential
  schemes cannot meet.

**Expected nomination:** dropping sequential update does not enlarge the set of
expressible functions (both schemes express the task class) ⇒ **weakness is
silent or ambiguous**. It does reduce parallel depth from `O(n)` to `O(1)` ⇒
**cost fires**.

## 3. Oracle

Exhaustive over `D ⊆ R_deletable` with `|D| ≤ 2`. For each `D`:

1. Compute the surviving extension `H(R \ D)`.
2. **Validity on α** — the extension must still contain a member fitting `α`.
   A deletion that destroys the child task is invalid regardless of `ω`.
3. **Coverage of ω** — the extension must contain a member fitting `ω` *and*
   meeting the cost budget.

`D` is **load-bearing** iff it is valid on `α` and covers `ω`. The oracle's
load-bearing set is the ground-truth top-k. Because propositions may be
entangled, more than one `D` can be load-bearing; that is intended and is what
gives `Recall@k` structure.

**Negatives are included by construction.** Propositions whose deletion leaves
the extension unchanged (invariant mass, unbounded velocity, orientation) are
*failed deletions* — the analogue of ether-drag models. They are scored, not
filtered out, so the denominator is meaningful.

## 4. Nominators (execution-free, ranked before any oracle call)

| id | score |
|---|---|
| `weakness` | `|H(R \ D)| − |H(R)|` |
| `cost` | `min-cost(H(R)) − min-cost(H(R \ D))` |
| `disjunctive` | `max` of the two after per-toy max-normalisation |
| `random` | seeded permutation (control) |
| `size_only` | prefers larger `|D|` (degenerate control) |

## 5. Metrics

- **`D-recall@k`** — fraction of the oracle's load-bearing set appearing in the
  nominator's top-`k`. Primary, per the finding that in both canonical cases
  the repair pre-existed and the *deletion* was the move.
- **`simple_regret`** — `1` if the nominator's top-1 is not load-bearing, else `0`.
- **`rank_of_first_load_bearing`**.

`k = 3`.

## 6. Frozen GO/NO-GO

- **H1 GO** iff on TK `weakness` ranks a load-bearing `D` in its top-3 while
  `cost` does not, **and** on TT `cost` does while `weakness` does not. Any
  single nominator succeeding on both toys **refutes H1**.
- **H2 GO** iff `disjunctive` attains `D-recall@3 ≥ max(weakness, cost)` on
  **both** toys.
- Both nominators must beat `random` and `size_only` on at least one toy, else
  the harness is not measuring ranking at all.

## 7. Anti-leakage — the E1 gate, applied before freezing

Erratum E1 recorded a program-wide defect: a *permitted* field already
contained the answer. That failure mode is assumed present here until measured.

Before any scoring row is generated, `inverted_signal_audit` is run over
**every nominator signal, in both orderings**, against the oracle's
load-bearing set. If any signal — including weakness or cost itself — reaches
oracle-level recall in either direction *by construction rather than by
merit*, the toy is redesigned before freezing.

The specific risk being guarded: a proposition set assembled knowing the answer
plants the answer. The toys are therefore built so that (a) `α` genuinely
fails to discriminate, and (b) at least three deletions are valid on `α` but do
not cover `ω`.

## 8. Scope limits, stated in advance

Two toy systems, authored propositions, exhaustive oracle over `|D| ≤ 2`. DR1
cannot establish that the nominator works on real corpora, cannot establish
anything about vocabulary extension (`𝔳` is fixed throughout — the known
ceiling), and is not evidence about relativity or attention. A GO licenses
exactly one thing: preregistering a date-cut retrodiction on a real corpus.

Single-shot. No replay knobs. A NO-GO is a real NO-GO.
