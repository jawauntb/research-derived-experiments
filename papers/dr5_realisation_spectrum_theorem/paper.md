# DR5: Proposition-Ranked Nominators Cannot Distinguish a Commitment from Its Realisations

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Deletion-Repair — DR5 (theorem paper)
**Date:** 2026-07-27

---

## Abstract

A nominator that scores individual propositions cannot, by itself, decide
whether a scientific community should delete a commitment $D$ when $D$
has more than one non-equivalent surface realisation in the corpus. The
scores it produces are per-proposition; the object of interest — $D$ —
is a class of propositions. Any move from a set of per-proposition scores
to a single "score for $D$" must import an external grouping function
$g$ that says which propositions realise $D$. Once $g$ is imported, the
ranking is no longer proposition-based but class-based. We state and
prove this as the **DR5 theorem**.

The theorem has a specific empirical shape and a general one. The
specific shape: the DCR1c–DCR1f arc encountered the situation directly
on a real pre-1905 electrodynamics corpus, where the target commitment
T1 (absolute simultaneity) is present in *at least six* non-equivalent
surface registers — Newton's metaphysical assertion, Larmor's
mathematical rewrite $t \to t - vx/c^2$, Lodge's "definite and
motion-independent duration," Maxwell's field-theoretic "instant across
the whole medium," Poincaré's "regarded as simultaneous" convention, and
a literary "duration is intrinsic" register surfaced by a held-out
sanity set. Every matcher tuned to one register missed the others.

**The general shape is a limit theorem about verification itself.** In
any setting where an oracle is used to check whether an agent has
identified some latent commitment — did it find the requirement, or did
the prompt install it? — the projection-vs-genuine-signal ambiguity is
irreducible whenever the commitment has multiple non-equivalent surface
forms. The DCR arc happens to make that irreducibility visible on a
corpus with ground truth attached (Einstein's actual 1905 deletion),
under a preregistered protocol that ruled out post-hoc matcher tuning,
so the outcome is not a matcher-designer's error. It is what the
theorem says will happen.

Companion empirical run (DCR2a) confirms the specific shape: even
class-based scoring, applied to the DCR1e presupposition-extracted
consensus, ranks T1 at position 3 at the 1904 target cut but *also* at
position 2 at the 1880 deep placebo cut, because a single misfiring
realisation is enough to inflate a low-cardinality class. Class-aware
scoring is a strict generalisation of proposition-ranking, but it does
not, by itself, eliminate the ambiguity. What it does is shift the
locus: the ambiguity is now about whether the grouping function $g$ is
sound and complete for $D$, not about whether the ranking $N$ found the
right proposition.

## 1. Setup and definitions

Let $C$ be a **corpus**: a finite set of propositions $P = \{p_1, \dots,
p_n\}$. Propositions are the atomic units of assertion available to the
community; the corpus is closed under whatever textual pre-processing
extracts them.

A **commitment** $D$ is a semantic property of propositions. A
proposition $p$ *realises* $D$ iff $p$ asserts or presupposes $D$.
Whether $p$ realises $D$ is a fact about the content of $p$ and the
content of $D$, not about $p$'s syntax, provenance, or membership in any
subset.

Define the **realisation set**
$$
\mathrm{realisations}(D, C) = \{p \in C : p \text{ realises } D\}.
$$
This set may have any cardinality. We are interested in the case
$|\mathrm{realisations}(D, C)| = k > 1$, where the commitment appears in
more than one non-equivalent surface form. Call each such $p$ a
**realisation of $D$**, written $r_i$.

A **proposition-ranking nominator** is a function $N: P \to \mathbb{R}$
that assigns a score $N(p)$ to each proposition. We take the defining
property of proposition-ranking to be that $N(p)$ depends only on $p$:
formally, $N$ is invariant under permutations of $P \setminus \{p\}$.
Equivalently, $N$ has no access to which other propositions are in $C$,
and no access to any grouping of $P$. This class includes every matcher
studied in DCR1c–DCR1f — regex, keyword patterns, learned classifiers
scoring each proposition independently — and it also includes the
per-proposition scoring functions used across DR1–DR4.

$N$ is **deletion-competent** for $D$ iff there exists a ranking rule
(top-1, top-$k$, or a fixed threshold) applied to the multiset $\{N(p)
: p \in C\}$ such that the resulting output "identifies $D$" in some
operational sense — e.g., the top-1 proposition realises $D$; the
top-$k$ contains a realisation of $D$; the propositions above threshold
are exactly the realisations of $D$.

A **grouping function** is a map $g: P \to 2^P$ (or equivalently a
partition of $P$ into classes) such that $g$ can identify
$\mathrm{realisations}(D, C)$ as one of its classes. $g$ is external
structure: it is not derivable from the values of $N$ alone.

## 2. Statement of the theorem

**Theorem (DR5).** *Let $D$ be a commitment with $|\mathrm{realisations}(D,
C)| = k > 1$, and let $N: P \to \mathbb{R}$ be a proposition-ranking
nominator. Then:*

*(a) In general, $N$ assigns $k$ distinct scores $\{N(r_1), \dots,
N(r_k)\}$ to the realisations of $D$.*

*(b) No aggregation of $\{N(r_i)\}_{i=1}^{k}$ into a single "class score
for $D$" is derivable from $N$ alone; any such aggregation requires an
external grouping function $g$ that identifies $\mathrm{realisations}(D,
C)$.*

*(c) Consequently, $N$ cannot answer the question "is $D$ ranked
highly?" without importing $g$. Once $g$ is imported, the ranking is
not proposition-based but class-based.*

## 3. Proof

*(a)* The realisations $r_1, \dots, r_k$ are, by hypothesis,
non-equivalent surface forms — distinct propositions differing in
wording, formalism, or presuppositional structure. $N$ is a function on
propositions, so in general $N(r_i) \neq N(r_j)$ for $i \neq j$.
Coincidental equality is possible on measure-zero cases, but nothing in
$N$'s definition forces it.

*(b)* Suppose, for contradiction, that there is a function $A$ such
that $A(N, D, C)$ returns a single score for $D$, using only the values
$N$ takes on $C$. To evaluate $A$, one must at some point select the
subset $\{N(r_1), \dots, N(r_k)\} \subseteq \{N(p) : p \in C\}$ on
which to aggregate. Selecting this subset is exactly the operation of
identifying $\mathrm{realisations}(D, C)$ within $P$. This selection is
not a function of $N$'s output, because $N$'s output is a bag of real
numbers indexed by propositions with no semantic tag for $D$. It
requires a further map $g$ that, given $p$, decides whether $p$
realises $D$. This $g$ is the grouping function.

*(c)* By (a), no single score is available from $N$. By (b),
constructing one requires $g$. Therefore any procedure that answers "is
$D$ ranked highly?" reads $g$'s output — the class of propositions
realising $D$ — and only then reads $N$. The primitive over which
ranking is defined is now the class, not the proposition. $\square$

## 4. The DCR corollary and the empirical companion

**Corollary.** In the DCR arc, T1 (absolute simultaneity) has $k \geq 6$
non-equivalent surface realisations in the pre-1905 corpus. No
proposition-ranking matcher can be simultaneously deletion-competent for
T1 across all six registers; every choice of matcher pattern picks a
subset of the realisation set and ranks the others as if unrelated.
DCR1c–DCR1f's *"the matcher fires on one register at the expense of
another"* is exactly the theorem operating.

**Empirical companion (DCR2a, 2026-07-27, same day as this paper).**
Class-based scoring was implemented over the DCR1e presupposition-
extracted consensus using the target_v4 matcher as the grouping
function $g$. All three preregistered aggregation rules (`cardinality`,
`coverage`, `spread`) rank the T1 class at position 3 at the 1904
target cut — a **one-position improvement** over the best T1
realisation's rank in a proposition-blind baseline (position 4). N3 GO.

But the same rules rank T1 at position **2** at the 1880 deep placebo
cut, because Maxwell's `instant across whole medium` is the single T1
realisation there and low-cardinality classes with any hit at all
dominate the cardinality-based aggregation. N4 NO_GO. DCR2a's overall
verdict is NO_GO, with the licensed reading

> class_scoring_fails_placebo: T1 outranks other classes at 1880 under
> some rule, meaning cardinality-1 hits inflate the class rank.
> Aggregation rule must require multi-document coverage.

This is *not* a refutation of DR5. It is a specification of what DR5
requires. Class-aware nomination adds $g$ (the matcher-derived class
assignment); the theorem says that eliminates the multi-realisation
ambiguity for well-behaved classes. But when $g$ produces
low-cardinality classes with borderline members, a second problem
appears: **the correctness of $g$ itself becomes the load-bearing
question**, and the placebo-vs-projection ambiguity is inherited from
$N$'s wall to $g$'s soundness/completeness. The class-scoring
substitution is a real generalisation, but it moves the ambiguity — it
does not delete it.

## 5. The general shape: a limit theorem about verification

The DCR arc's specific finding — that Einstein's deletion is a
class, not a proposition, and no single-realisation matcher can catch
it — generalises to a claim about verification of agent outputs at
large.

Consider the abstract setting: an agent $\mathcal{A}$ is asked to
identify a latent commitment $D$ from a document (or reasoning trace).
An oracle $\mathcal{O}$ checks whether $\mathcal{A}$'s output corresponds
to $D$. In practice, $\mathcal{O}$ is often a matcher, a classifier, or
an LLM judge — some function that scores individual propositions
(sentences, program tokens, reasoning steps) and reports whether the
target has been identified.

Two failure modes arise:

- **Projection.** The oracle fires on $\mathcal{A}$'s output not because
  $\mathcal{A}$ found $D$ but because the oracle was primed to find $D$
  in any output of the right surface shape.
- **Placebo firing.** The oracle fires on a control input where $D$
  should not be present, revealing the oracle is pattern-matching
  something other than $D$.

The standard diagnostic — check the oracle on a placebo; if it fires,
the oracle is projecting; if it stays silent, trust the positive result
— assumes $D$ has one surface form the oracle can recognise. **When $D$
is a multi-realisation commitment, this diagnostic can be irreducibly
ambiguous:** the placebo firing could indicate projection *or* a
realisation of $D$ the oracle-designer did not anticipate at the placebo
cut.

DCR1f's Maxwell 1865 hit is exactly this. Under the DCR1f preregistered
decision table, the 1880 hit at the deep placebo cut licenses **Reading
B (extractor projecting)**. But the specific hit is a genuine
presupposition of Maxwell's field theory — an "instant" over a
spatially extended field — and by DR5's Corollary is a legitimate
realisation of T1. The projection reading and the "placebo was never
valid because a field theory already presupposes T1" reading are
formally indistinguishable at the oracle level. Distinguishing them
requires knowledge $\mathcal{O}$ does not have access to, and cannot
acquire without importing a $g$ that the DR5 theorem says was already
necessary.

**Practical consequence.** For any agent-output-verification protocol
where the target admits multiple surface forms — LLM reasoning
verification, code-generation correctness, retrieval-augmented factual
grounding, presupposition-detection, latent-goal identification —
placebo-based projection checks can fail to distinguish projection from
signal. The failure is not a design defect. It is a corollary of DR5.
Any such protocol either requires an $a\text{-}priori$ grouping function
$g$ (which shifts the burden of correctness from the ranker to $g$) or
requires machinery beyond proposition-independent scoring.

The DCR arc is, to our knowledge, the cleanest concrete instance of
this pattern with ground truth attached — Einstein's actual 1905
deletion is known; the DCR1c preregistration ruled out post-hoc matcher
tuning; the DCR1f held-out validation was generated by blind subagents
at a fixed digest before target_v4 was drafted. The pattern generalises;
the ground truth is the leverage that lets us see it.

## 6. What DR5 does not claim

DR5 does not claim that class-aware nomination is easy or well-defined;
only that it is *necessary* for commitments with $k > 1$.

It does not claim $g$ must be a matcher. $g$ could be any function
identifying realisations — a presupposition-inferring extractor (as
DCR1e attempted), a learned classifier, a hand-curated ontology, or a
canonical-form transformation applied at extraction time. Each has its
own soundness/completeness questions.

It does not resolve DCR1e/f's B1 versus B2 (extractor projecting vs
placebo invalid); those are separate empirical questions about whether a
given $g$ is sound at the placebo cut.

It does not require $k$ to be known exactly; the theorem holds whenever
$k > 1$, and the empirical companion DCR2a offered a lower bound on $k$
for T1 in the pre-1905 corpus without needing an exact count.

It does not prescribe *which* class-aware nomination scheme to use.
Cardinality, coverage, spread, and various IR-style aggregations are all
compatible with the theorem's structural claim. The DCR2a run tested
three and found all three insufficient at the placebo. Others may work;
the theorem does not settle the question empirically.

## 7. Open questions

- **Correctness conditions on $g$.** Under what conditions is $g$ sound
  and complete for $D$? Soundness (every $p \in g(D)$ realises $D$) and
  completeness (every realisation of $D$ in $C$ is in $g(D)$) are the
  obvious candidates, but each is separately non-trivial. Constructing
  $g$ empirically (as DCR1e/f attempted) is precisely the exercise
  DCR1f's precision-recall wall showed to be over-constrained.
- **Extractor-implicit grouping.** Under what conditions does an
  extraction step *implicitly* define $g$? DCR1e's presupposition-
  inferring extractor arguably rewrites distinct surface forms into a
  canonical presuppositional statement before matching. If so, part of
  $g$'s work is being done at extraction time, before the matcher sees
  the data. The DCR1f placebo firing at Maxwell suggests this is not
  yet fully deliberate.
- **Learning $g$ from data.** Can $g$ be learned? A learned $g$ risks
  Spencer's candidate-selection circularity one level up: if $g$ is
  trained on labels derived from the same source as the ranking signal,
  the wall re-appears. This is the same argument that killed COGR Wave
  1a; DR5 says it operates at the class-identification level too.
- **Non-linguistic verification.** DR5 was stated over corpora of
  propositions but generalises to any $C$ of items and any $D$
  admitting multi-form realisations. Code correctness, protocol
  compliance, and constraint satisfaction each admit multi-form
  realisations of "the correct implementation," and each should be
  susceptible to the same wall.

## 8. Relation to prior program findings

**DR2 precedent.** DR2 proved a two-nominator claim unreachable under
its original cost definition. Progress required redefining cost so the
primitive was no longer the extension whose cost was being counted. DR5
is parallel: it proves a class of nomination questions is unreachable
under the proposition-ranking primitive, and progress requires
redefining the primitive — here, from proposition to class. Both are
structural walls, converted by proof, that admit the same rescue: the
primitive was wrong, and once it is restated the corresponding empirical
question becomes tractable.

**Spencer's candidate-selection circularity, generalised.** COGR Wave 1a
died of a candidate-selection leak: the ranker was fed candidates
constructed with knowledge of what would rank highly. DR5 says the leak
has a formal analogue at the class-identification level: any grouping
function $g$ trained on the ranker's own signal collapses back into a
proposition-ranking problem. Class-aware nomination is only a
generalisation to the extent that $g$ is *independent* of $N$.

**The DCR1c–DCR1f arc.** DCR1c through DCR1f can be re-read as three
questions:

1. Can the extractor be honest? (DCR1: yes, with structural chrome
   removal, relational residue, and provenance-cleared source vehicles.)
2. Can the matcher be validated? (DCR1d: yes, on Newton's explicit
   register.)
3. Can extractor + matcher together identify a multi-realisation
   commitment? (DCR1e/f: no, on this corpus, with these instruments; and
   DR5 shows the "no" is structural for any such combination when $k >
   1$.)

The DCR arc has not proved deletion-repair nomination is unworkable in
general. It has shown that its formulation as proposition-ranking hits a
structural wall on the specific class of commitments Einstein deleted
was drawn from. The wall is not a bug; it is what a well-run empirical
program looks like when it correctly hits the limit of its primitive.

---

## Appendix: reproduction

DR5 is a theorem paper; there is no code artifact. The empirical
companion DCR2a reproduces via:

```
uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr2a
```

Its verdict at `experiments/date_cut_retrodiction/results/dcr2a_verdict.json`
supplies the numbers cited in §4.

The DCR1c–DCR1f arc that motivates DR5 reproduces via each paper's own
`run_dcr1*.py`. All prior verdicts are byte-identical to their published
numbers; DR5 does not edit any prior module.

**Preregistration.** DR5 has no preregistration: it is a theorem paper,
not an empirical run. The empirical companion DCR2a has one, at
`DCR2A_PREREGISTRATION.md`, SHA-256
`76d95494ca8968814a062f0b6bd9ceb287fcb3c135fe8647186b387a87a96717`.
