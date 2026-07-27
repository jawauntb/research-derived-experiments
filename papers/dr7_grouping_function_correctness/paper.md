# DR7: The Grouping Function Inherits the Wall

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Deletion-Repair — DR7 (grouping function correctness)
**Date:** 2026-07-27

---

## Abstract

DR5 established that a proposition-ranking nominator $N$ cannot
distinguish a commitment $D$ from any specific realisation $r_i$ when
$|\mathrm{realisations}(D)| > 1$; escape requires importing an external
grouping function $g$. DR6/DR6c/DR6d/DR6e triangulated: the wall bites
if and only if the realisation set is open at test time and the verifier
lacks semantic reasoning about $D$. DR5 stated that "the correctness of
$g$ becomes the load-bearing question." DR7 formalises what that means
and proves two consequences.

**Theorem 1 (soundness–completeness gap for open realisation sets).**
If a grouping function $g$ is constructed at design time and $D$ admits
realisations at test time that were not observable at design time, then
$g$ cannot be simultaneously sound and complete for $D$. Formally: for
any $g$ constructed as a function of a design-time realisation sample
$S \subsetneq \mathrm{realisations}(D, C)$, either $g$ over-generalises
(includes non-realisations of $D$ in its class) or under-generalises
(excludes realisations of $D$ from its class), on some corpus $C$.

**Theorem 2 (learned-$g$ Spencer collapse).** If $g$ is learned from a
signal that includes the ranker $N$'s output on the training data,
then class-aware ranking under $g$ decomposes into an equivalent
proposition-ranking problem with a larger score function. Class
awareness supplies no additional discriminating power in this case; the
DR5 wall re-appears at the class level.

Together, the two theorems say: **class-aware nomination is not a
complete escape route on its own**. It relocates the wall from
proposition ranking to grouping-function construction. The wall is
still there; it now lives in the question *"was $g$ built with genuine
access to $D$'s realisation structure?"* Sound and complete $g$ is
possible only when the realisation set is closed at design time
(equivalent to DR5's condition (a) closed) or when $D$'s semantic form
is available to construction (equivalent to DR5's condition (b)
satisfied). Neither condition changes; the wall's antecedents transfer
from $N$ to $g$.

**Practical consequence.** DR5 said "class-aware nomination requires
$g$." DR7 says: **$g$ requires the same conditions DR5 required of $N$**.
The wall is not escaped by class-awareness; it is refactored. Genuine
escape requires either closed realisation sets or semantic access to $D$
somewhere in the pipeline. The class-aware framing helps by making the
location of the missing property explicit — but it does not itself
supply the property.

---

## 1. Setup

Reuse DR5's setup. Corpus $C$ finite. Commitment $D$ semantic; a
proposition $p$ realises $D$ iff $p$ asserts or presupposes $D$.
Realisation set $\mathrm{realisations}(D, C)$. Proposition-ranking
nominator $N: C \to \mathbb{R}$.

A **grouping function** for $D$ on $C$ is a map $g_D: C \to \{0, 1\}$
(equivalently a subset of $C$) such that $g_D(p) = 1$ iff $g_D$'s
designer intends $p$ to be grouped with realisations of $D$.

$g_D$ is **sound** for $D$ on $C$ iff $g_D(p) = 1 \Rightarrow p \in
\mathrm{realisations}(D, C)$.

$g_D$ is **complete** for $D$ on $C$ iff $p \in
\mathrm{realisations}(D, C) \Rightarrow g_D(p) = 1$.

The **class score** of $D$ under $(N, g_D)$ is any aggregation of
$\{N(p) : g_D(p) = 1\}$: cardinality, sum, max, spread, or any
function of the class members' $N$-scores.

## 2. Theorem 1 — soundness–completeness gap

**Statement.** Let $g_D$ be constructed at design time as a function of
a sample $S \subseteq C_{\text{design}}$ of design-time realisations,
where $C_{\text{design}}$ is a design-time corpus and
$C_{\text{test}} \supseteq C_{\text{design}}$ is the test-time corpus.
If there exists $r^* \in \mathrm{realisations}(D, C_{\text{test}})$
with $r^* \notin C_{\text{design}}$ (a genuinely novel realisation),
then $g_D$ cannot be simultaneously sound and complete for $D$ on
$C_{\text{test}}$.

**Proof.** $g_D$'s output on $r^*$ is determined by $g_D$'s
construction, which used only $S$. Two cases:

- **Case A:** $g_D(r^*) = 1$. Then $g_D$ is committed to grouping
  something outside $S$ with the design-time realisation set. This can
  happen only if $g_D$ over-generalises the surface features of $S$'s
  members. But an over-generalising $g_D$ will also fire on some
  non-realisations $q \in C_{\text{test}}$ with the same over-general
  surface features — witnessed by any $q$ syntactically similar to
  $S$'s members but semantically distinct from $D$. Such a $q$ exists
  whenever the language of $C_{\text{test}}$ is rich enough to construct
  syntactic near-copies with different semantics; this is guaranteed
  for natural-language corpora and for code corpora with any nontrivial
  vocabulary. Then $g_D$ is unsound: $g_D(q) = 1$ but $q \notin
  \mathrm{realisations}(D, C_{\text{test}})$.

- **Case B:** $g_D(r^*) = 0$. Then $g_D$ excludes a genuine realisation
  of $D$; $g_D$ is incomplete.

Either case establishes the claim. $\square$

**Empirical instance.** DR6d exhibits Case B directly: `regex_verifier`
was designed against 5 realisation labels; R6 was a novel realisation
at test time; `regex_verifier`'s implicit $g_D$ (via the score function)
outputs 0 on R6. R6 is a realisation of naive-UTC; $g_D$ misses it;
$g_D$ is incomplete. Case A is illustrated by DCR1f's target_v4 firing
on Maxwell's `instant across whole medium` at the 1880 placebo — the
matcher over-generalised beyond its design-time realisations and
included a case whose status as "genuine T1 realisation" versus
"projection" is exactly the placebo-invalidity ambiguity DR5 §5 said
is irreducible.

**Corollary (open-enumeration incompatibility).** For any $D$ with
$\mathrm{realisations}(D, C_{\text{test}}) \not\subseteq
C_{\text{design}}$, $g_D$'s soundness and completeness are jointly
unattainable at design time.

## 3. Theorem 2 — learned-$g$ Spencer collapse

**Statement.** Let $g_D^{\text{learned}}$ be a grouping function whose
construction included, as training signal, the ranker $N$'s output on
some training subset $T \subseteq C_{\text{design}}$ (equivalently:
$g_D^{\text{learned}}$ was trained to predict "does this proposition
realise $D$" using a target label that was itself derived from $N$'s
score or its high-scoring behaviour on $T$). Then class-aware ranking
under $(N, g_D^{\text{learned}})$ is equivalent to proposition-ranking
under a score function $N': C \to \mathbb{R}$ where $N'(p)$ depends only
on $p$ and on $N$'s output at $p$. In particular, class-awareness
supplies no additional discriminating power beyond what $N$ already had
on $T$-similar propositions.

**Proof sketch.** $g_D^{\text{learned}}(p)$ can be written as
$f(\phi(p), N(p))$ where $\phi(p)$ is any surface-feature vector of $p$
and $f$ is the learned classifier. Substituting into any class-aware
aggregation $A(\{N(q) : g_D^{\text{learned}}(q) = 1\})$, the outer
aggregation is a function of proposition-level scores, and the
membership determination is itself a function of proposition-level
features and $N$-scores. So the composition
$A \circ (N, g_D^{\text{learned}})$ can be written as a function
$C \to \mathbb{R}^k \to \mathbb{R}$ of per-proposition information
alone. This is a proposition-ranking function of a different score
$N'$; DR5's original theorem applies to $N'$ directly.

**Consequence.** Any learned $g_D$ that pipes $N$'s output through its
training does not escape DR5. It builds a more expensive $N'$ and the
wall reappears at $N'$'s level.

**Empirical instance.** DCR2a's target_v4 was implicitly a learned-$g$
of a different flavour: it was hand-tuned by inspection of the DCR1e
extractor's outputs (which are the "signal" analog to $N$'s output).
DCR1f's held-out validation showed the resulting matcher's precision-
recall wall — exactly the Spencer collapse DR7 Theorem 2 predicts.

## 4. What DR7 buys, jointly with DR5

DR5 said: proposition-ranking cannot solve multi-realisation
verification; import $g$.

DR7 says: importing $g$ requires either (i) closed realisation set at
design time (equivalent to DR5's condition (a) closed) or (ii)
independent access to $D$'s semantic structure (equivalent to DR5's
condition (b) satisfied). Neither of DR7's conditions is weaker than
DR5's. The wall does not disappear when class-awareness is imported;
it *relocates* from $N$ to $g$.

**The joint claim (DR5+DR7):**

Genuine multi-realisation commitment verification requires either

- **the realisation set is closed at design time**, or
- **at least one component of the verification pipeline has independent
  semantic access to $D$**.

If both conditions fail, no proposition-independent verification
architecture (regex, keyword, learned classifier scoring propositions
independently, or class-aware aggregator with $g$ built from those
signals) can escape the wall. **The only architectural escape is
importing genuine semantic access — either from an LLM (as DR6/DR6e
showed) or from a hand-authored $g$ whose construction included direct
semantic knowledge of $D$.**

Practically:

- **Regex matchers**: escape only when the realisation set is closed
  and the designer enumerates it fully.
- **Learned classifiers on independent features**: escape only when
  labels came from semantic access to $D$ that did not itself run
  through the ranker.
- **LLM verifiers on natural-language prompts**: escape only when $D$
  can be described precisely and the LLM's semantic reasoning is
  adequate for $D$'s domain.
- **Class-aware aggregators over any of the above**: escape only when
  the underlying $g$-construction had access to one of the above
  conditions; class-awareness by itself supplies nothing.

## 5. Open questions

- **Bounded-completeness $g$.** Can we characterise $g_D$ that are
  sound and complete on a *specific known subset* of
  $\mathrm{realisations}(D, C_{\text{test}})$ while explicitly
  admitting incompleteness on the rest? DR7 shows global soundness-
  completeness is impossible on open realisation sets; partial
  guarantees might still be well-defined.
- **Ensemble-$g$.** Does combining multiple partial-$g$s help? Union-$g$
  (any classifier that fires includes $p$) inherits every unsound
  member's unsoundness. Intersection-$g$ inherits every incomplete
  member's incompleteness. Neither escapes the theorem.
- **Semantic-$g$ from LLM.** If $g_D$ is defined as "an LLM says this
  proposition realises $D$," does it satisfy DR7's independent-semantic-
  access condition? Yes, in the same way DR6e's Claude verifier
  satisfied DR5's condition (b) — but the guarantee is only as strong
  as the LLM's semantic accuracy on $D$'s domain, and each LLM's
  accuracy has its own limits.

## 6. Relation to the arc

DR5 stated a structural wall on proposition-ranking. DR7 shows that the
wall transfers to any construction of the grouping function that DR5
proposes as an escape. Read together, DR5 and DR7 characterise the
class of verification problems where no proposition-independent
architecture can succeed and identify the specific structural resource
(semantic access to $D$) that is necessary and sufficient for escape.

DR5 + DR7 + DR5b + the six empirical papers (DCR1f, DR6, DR6c, DR6d,
DR6e, and DCR2a as the class-aware companion) constitute a completed
theoretical-empirical bundle. The wall's shape, empirical scope, and
architectural implications are now on record. The DR-arc has finished
its statement of the problem.

---

## Appendix: reproduction

DR7 is a theorem paper; there is no code artifact. The empirical
instances cited (DR6d Case B, DCR1f Case A, DCR2a Spencer collapse)
each reproduce via their respective runners.
