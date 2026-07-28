# Relative Identifiability

## A Counterexample-First Theorem-Development Benchmark

**Jawaun Brown**

Research-Derived Experiments

2026-07-27

## Abstract

Scientific access to an internal system is always mediated by an allowed family
of experiments. This note isolates the exact obstruction to recovering a target
property from that family. Candidate realizations are equivalent when every
allowed experiment produces the same outcome. A target is exactly identifiable
if and only if it is constant on those equivalence classes, or equivalently if
it factors through the observational quotient. One target-distinct pair with an
identical complete transcript is therefore a complete counterexample
certificate. Adding experiments can only refine the quotient.

None of this quotient mathematics is new. The same structure appears in
automata minimization, testing and contextual equivalence, comparison of
statistical experiments, causal interventional equivalence, and a recent
probe-family-relative Myhill--Nerode theorem. The contribution here is an
executable theorem-development benchmark: a typed obstruction certificate,
minimum separating-family search, a mechanistic internal-intervention fixture,
a dependency-free Lean proof, and a versioned MIDAS regression contract. The
benchmark changes the research question from “what is the true internal
representation?” to the more disciplined question “which target distinctions
survive this declared experiment family?”

## 1. The narrow question

Let \(R\) be a set of candidate internal realizations. An experiment \(e\) has
an outcome type \(O_e\) and a total observation map

\[
\operatorname{obs}_e:R\to O_e.
\]

An experiment family \(\Gamma\) selects the observations the investigator is
allowed to use. A target

\[
\tau:R\to T
\]

states the distinction the investigator wants to recover: behavior, mechanism,
causal role, coordinate label, source provenance, or another declared object.

The central question is not whether \(R\) has structure in itself. It is:

> Does the complete \(\Gamma\)-transcript contain enough information to recover
> \(\tau\) exactly?

This target-relative wording matters. The same experiment family can identify
one target and fail completely on another.

## 2. Observational quotient

Define

\[
r\sim_\Gamma r'
\quad\Longleftrightarrow\quad
\forall e\in\Gamma,\;
\operatorname{obs}_e(r)=\operatorname{obs}_e(r').
\]

Reflexivity, symmetry, and transitivity follow directly from equality in each
outcome type. The quotient

\[
Q_\Gamma=R/{\sim_\Gamma}
\]

is the set of distinctions exposed by the full allowed experiment family.

This quotient is observer-relative, not a declaration of metaphysical
identity. Two realizations collapsed by external behavior may be separated by
internal activation patching, ablation, feature clamping, or another enriched
experiment family. Conversely, adding a redundant experiment changes no
quotient block.

## 3. Universal obstruction theorem

Call \(\tau\) exactly identifiable from \(\Gamma\) when there is a decoder
\(\bar\tau:Q_\Gamma\to T\) such that

\[
\tau=\bar\tau\circ q_\Gamma,
\]

where \(q_\Gamma:R\to Q_\Gamma\) is the quotient map.

### Theorem 1: factorization criterion

The following are equivalent:

1. \(\tau\) is exactly identifiable from \(\Gamma\);
2. \(\tau\) is constant on every \(\sim_\Gamma\) equivalence class;
3. no pair \(r,r'\) satisfies both
   \(r\sim_\Gamma r'\) and \(\tau(r)\ne\tau(r')\).

### Proof

If \(\tau=\bar\tau\circ q_\Gamma\) and \(r\sim_\Gamma r'\), then
\(q_\Gamma(r)=q_\Gamma(r')\), so applying \(\bar\tau\) yields
\(\tau(r)=\tau(r')\).

If \(\tau\) is constant on equivalence classes, define
\(\bar\tau([r])=\tau(r)\). Constancy makes this definition independent of the
representative, and the factorization equation follows.

Finally, failure of class constancy is exactly the existence of a
target-distinct pair in one class. \(\square\)

The pair

\[
(r,r'):\quad
\forall e\in\Gamma,\;\operatorname{obs}_e(r)=\operatorname{obs}_e(r'),
\qquad
\tau(r)\ne\tau(r')
\]

is the benchmark's `ObstructionCertificate`. It is the smallest kind of exact
evidence that a recovery claim must fail: every decoder receives the same
complete transcript for both realizations and therefore must be wrong on at
least one.

The theorem is a kernel/quotient factorization fact. Its value here is
disciplinary and executable, not mathematical novelty.

## 4. Refinement theorem

### Theorem 2: richer families refine

If \(\Gamma_1\subseteq\Gamma_2\), then

\[
r\sim_{\Gamma_2}r'
\Longrightarrow
r\sim_{\Gamma_1}r'.
\]

Thus \(Q_{\Gamma_2}\) refines \(Q_{\Gamma_1}\), and there is a canonical
surjection

\[
Q_{\Gamma_2}\twoheadrightarrow Q_{\Gamma_1}
\]

that forgets the extra experiments.

### Proof

Agreement on every experiment in \(\Gamma_2\) includes agreement on every
experiment in its subset \(\Gamma_1\). Mapping each richer equivalence class to
the coarser class containing it is well-defined and surjective. \(\square\)

Strictness does not follow. An added experiment may duplicate information
already in the family. This redundancy case is a registered negative control.

Nixon's 2026 bounded-interaction Myhill--Nerode paper already states the direct
probe-family version: smaller probe classes induce coarser quotients. The
present theorem should be read as the elementary target-relative schema around
that established structure, not as an independent novelty claim [1].

## 5. Finite counterexample-first engine

For finite \(R\) and \(E\), the implementation computes the quotient by grouping
equal selected-family transcripts. For a target \(\tau\), it follows one branch:

```text
build observational quotient
        |
        v
is target constant on every block?
        |
   yes  |  no
        |
        +--> emit FactorizationCertificate
             or
             emit first ObstructionCertificate
```

The engine also enumerates experiment subsets by increasing cardinality. It
returns every minimum identifying family, or the obstruction produced by the
full family if no subset can identify the target. The search is exhaustive and
exponential; no efficiency theorem is claimed.

An exhaustive test enumerates all \(2^9=512\) binary observation tables with
three realizations and three experiments, all eight binary targets, and all
eight experiment families. Across 32,768 target/family cases it cross-checks
factorization against direct block constancy and verifies every nested-family
refinement. This is an implementation sanity check, not a substitute for the
Lean proof.

## 6. Mechanistic refinement fixture

The registered fixture crosses two external behaviors with two mechanisms:

| Realization | External readout | Internal patch | Mechanism target |
|---|---:|---|---|
| behavior 0, mechanism A | 0 | A | A |
| behavior 0, mechanism B | 0 | B | B |
| behavior 1, mechanism A | 1 | A | A |
| behavior 1, mechanism B | 1 | B | B |

Under the external readout alone, the behavioral target factors through the
two-block quotient. The mechanism target does not: the A/B pair at each
behavior has the same external transcript. Adding the internal patch splits the
blocks and makes the mechanism target identifiable in this fixture.

This resolves the main interpretability caution. Behavioral collapse is not
mechanistic identity. The quotient is always indexed by the experiment family,
and internal interventions can expose distinctions erased by external tests.
Activation patching is therefore naturally represented as experiment-family
enrichment, although real patching results remain sensitive to metrics,
corruptions, and other methodological choices [7].

## 7. What the schema says about existing programs

### 7.1 DCR

A date-cut protocol declares an evidence family. A claimed provenance or answer
target is exactly recoverable only if it is constant across every candidate
world that agrees on all permitted evidence. A pair with the same permitted
transcript and different target is an obstruction.

The theorem does not show that such a pair exists in a particular DCR run.
That is an empirical and provenance question for the DCR artifacts.

### 7.2 Constraint Swap

The failed hidden-geometry experiment and the exact future-commitment quotient
operate at different validity layers. A local training/probe family may collapse
two delayed rules that a longer intervention word separates. This conditional
instantiation explains what a richer family would need to distinguish; it does
not rescue the rejected geometry-mediated mechanism.

### 7.3 Activation geometry

If two reparameterized systems agree on all selected external experiments but
have different coordinate labels or geometries, that coordinate target does
not factor through the external quotient. The correct conclusion is
family-relative non-identifiability. It is not that coordinates do not exist,
never matter, or cannot be separated by internal interventions.

### 7.4 Causal and mechanistic representation

Interventions refine observational equivalence classes in causal discovery:
general interventions induce interventional Markov equivalence classes, and
active intervention choice can improve identifiability [5, 6]. The present
schema supplies no intervention-selection algorithm for natural systems. It
only states the exact success and failure condition once a family is declared.

## 8. Prior-art boundary

| Component | Direct tradition | Status here |
|---|---|---|
| quotient by future tests | Myhill--Nerode and automata minimization | transported |
| counterexample-guided refinement | Angluin's query learning | transported workflow |
| tests characterize process equivalence | bisimulation/testing semantics | transported |
| richer probes refine quotient | bounded-interaction Myhill--Nerode, Prop. 4.11 | already explicit |
| experiment informativeness | Blackwell comparison of experiments | broader decision-theoretic precedent |
| interventional equivalence class | causal discovery | domain instantiation |
| internal patching | mechanistic interpretability | candidate enriched family |
| quotient factorization criterion | elementary setoid/kernel mathematics | standard |
| typed obstruction receipt + theorem-to-test manifest | this artifact package | engineering contribution |

Blackwell compares statistical experiments by their performance across decision
problems, a stronger decision-theoretic ordering than set inclusion of
deterministic tests [2]. Larsen and Skou characterize process distinctions
through a probabilistic testing language [3]. Angluin's learner uses membership
and equivalence queries, with counterexamples refining an automaton hypothesis
[4]. These traditions already make allowed observations and distinguishing
tests central.

The honest novelty boundary is therefore severe: the mathematical theorem
package is not new. The publishable object, if useful in practice, is the
counterexample-first development environment and its benchmark discipline.

## 9. Lean and MIDAS contract

The dependency-free Lean 4 development proves:

1. observational equivalence;
2. quotient factorization iff fiber constancy;
3. obstruction iff non-factorization;
4. richer-to-coarser quotient surjectivity;
5. empty-family and constant-target edge cases.

The versioned `midas_contract.json` maps every registered theorem to Lean
declarations and executable tests. The intended MIDAS loop is:

```text
Definition
   -> Conjecture
   -> Search for smallest obstruction
   -> Refine experiment family or assumptions
   -> Typecheck proof and replay regressions
```

Failed conjectures remain useful artifacts because the obstruction pair becomes
a stable regression case.

The proof and fixture gates fail independently. Pull requests typecheck the
pinned Lean package with `lake build`; the Python receipt binds itself to the
fixture SHA-256, checks complete registered certificate fields, and is replayed
from a clean checkout against the committed byte oracle. A Python `PASS` is not
used as a substitute for the Lean build.

## 10. Limits and next theorem

The package assumes deterministic exact outcomes in its finite executable
engine. It does not handle:

- stochastic experiments or distributional equality;
- approximate identifiability and quantitative lower bounds;
- continuous or infinite realization spaces;
- adaptive experiment policies;
- partial observation of the experiment table;
- computationally universal realizations;
- learning which internal intervention is scientifically admissible.

The next mathematical step should not be another quotient existence theorem.
It should be one of two genuinely stronger objects:

1. a quantitative obstruction under noisy or approximate transcripts; or
2. an undecidability boundary for exact equivalence in computationally
   universal agents.

Either extension requires a new preregistration and cannot inherit the present
finite exact proof unchanged.

## 11. Conclusion

The universal obstruction is simple:

\[
\boxed{
\exists r,r':
\operatorname{Transcript}_\Gamma(r)
=
\operatorname{Transcript}_\Gamma(r')
\ \land\
\tau(r)\ne\tau(r')
}
\]

When that certificate exists, exact recovery of \(\tau\) is impossible under
\(\Gamma\). When it does not, \(\tau\) factors through the observational
quotient. Richer experiment families can refine the quotient but need not do
so.

This does not produce a grand theory of representation. It produces a precise
stop condition, a counterexample object, and a theorem-to-regression loop. That
is the right scale for MIDAS.

## References

[1] A. T. Nixon. “The Myhill--Nerode Theorem for Bounded Interaction:
Canonical Abstractions via Agent-Bounded Indistinguishability.” 2026.
<https://arxiv.org/abs/2603.21399>.

[2] D. Blackwell. “Equivalent Comparisons of Experiments.” *The Annals of
Mathematical Statistics* 24(2), 1953.
<https://doi.org/10.1214/aoms/1177729032>.

[3] K. G. Larsen and A. Skou. “Bisimulation through Probabilistic Testing.”
*Information and Computation* 94(1), 1991.
<https://doi.org/10.1016/0890-5401(91)90030-6>.

[4] D. Angluin. “Learning Regular Sets from Queries and Counterexamples.”
*Information and Computation* 75(2), 1987.
<https://doi.org/10.1016/0890-5401(87)90052-6>.

[5] K. D. Yang, A. Katcoff, and C. Uhler. “Characterizing and Learning
Equivalence Classes of Causal DAGs under Interventions.” 2018.
<https://arxiv.org/abs/1802.06310>.

[6] A. Hauser and P. Bühlmann. “Two Optimal Strategies for Active Learning of
Causal Models from Interventional Data.” 2012.
<https://arxiv.org/abs/1205.4174>.

[7] F. Zhang and N. Nanda. “Towards Best Practices of Activation Patching in
Language Models: Metrics and Methods.” 2023.
<https://arxiv.org/abs/2309.16042>.

[8] A. Ahmed and M. Blume. “Modular, Fully-abstract Compilation by Approximate
Back-translation.” 2017. <https://arxiv.org/abs/1703.09988>.

[9] Lean FRO. “Managing Toolchains with Elan.” *Lean Language Reference*.
<https://lean-lang.org/doc/reference/latest/Build-Tools-and-Distribution/Managing-Toolchains-with-Elan/>.
