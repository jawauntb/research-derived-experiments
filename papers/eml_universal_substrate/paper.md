# EML as a Universal Substrate

## Why the calculator completeness result is an instance of the master object, and why nobody sane stops at inhabitation

**Jawaun Brown**
Human author and research director

**Cursor Grok 4.6 (cloud agent)**
Experiment code, Lean core, and manuscript production under direction and review

**Date:** August 17, 2026
**Status:** four seams proved on a finite toy (US-1 through US-4); six gates passing on real numbers; Lean US-2/US-3 core kernel-checked on Lean 4.31 (`lake build`, zero `sorry`). US-4′ (fiber free energy predicts EML gradient recovery) is **untested**. Companion to *The Structural Intelligence Conjecture* (`papers/structural_intelligence/paper.md`). External laboratory: Odrzywołek, *All elementary functions from a single binary operator*, arXiv:2603.21852.

---

## Abstract

Odrzywołek's EML paper is not adjacent to the Structural Intelligence
Conjecture. It is an instance of the master object, built from the
calculator side. The homogeneous tree language
`S → 1 | eml(S,S)` is `X`. The scientific-calculator class is `Z`.
Denotation is `q`. Bootstrap synthesis is the compiler `K`. Completeness
is fiber inhabitation: `q⁻¹(z) ≠ ∅` for every `z` in `F_calc`. He built
the substrate and stopped.

SIC is the explanation of why nobody sane stops there. The invariance
theorem is a *sharing-level* fact. Search does not live at the sharing
level. Kolmogorov complexity is invariant across universal machines up
to `O(1)` because programs are DAGs: they can name and reuse. Formula
(tree) description length has no invariance theorem, and the failure is
exactly exponential. Adjoin the definable macro `sq(y) = y·y` to
`{x, ×}` and the minimal formula for `x^(2^n)` drops from `2^{n+1}−1`
to `n+1`, while circuit size stays `Θ(n)` in both bases. Conservative
extension — zero new denotations, exponential change in access.

Odrzywołek already ran Outcome A and buried it in his own table: blind
recovery 100% at depth 2, ~25% at depths 3–4, <1% at depth 5, 0/448 at
depth 6, while perturbed-correct-weights recover 100% even at depths
5–6. Basins exist; access collapses; expressivity is constant the whole
way down. Under a Gibbs prior the discovery probability is fiber free
energy. The toy makes the geometry measurable: at `n=4` the Mul fiber
is a single shell of 9,694,845 trees with mass `7.8×10^{-12}`; the Sq
fiber occupies 27 shells with mass `4.0×10^{-3}`; the `log₂` ratio is
28.92 against a closed-form shortest-witness bound of 28.28.

What is not ours: syntax-quotients-by-denotation is standard
denotational semantics; task-relative quotients are already in the
Bayes-sufficient-representation line; completeness belongs to
Odrzywołek. What is ours: the separation structure (expressivity ≠ tree
complexity ≠ circuit complexity ≠ learnability, with an exact
exponential witness at each seam) and the fiber-mass account of access.
Both can be true — his universality and our task-relativity — because
they are different levels: one substrate, many quotients. Nothing in
`e^x − ln y` has valence. EML is the bottom of the stack. Concern is
still the only thing that makes any of it matter.

---

## 1. Current frame

The accepted story after a Sheffer-style completeness result is:
*expressivity is the phenomenon*. Once every calculator button is a
tree in a one-operator language, the job is done. Search, then, is
treated as a practical nuisance: depths get large, gradients overflow,
recovery rates fall. Those are engineering details around a solved
universality theorem.

The protected assumption — the absolute-time of this subject — is that
**description complexity is invariant**, so substrate choice cannot
matter "in principle." If two bases generate the same functions, access
should be the same up to an additive constant.

That assumption is true for *programs* (DAGs with names). It is false
for *formulas* (trees). Symbolic regression, grammar sampling, and EML
master formulas all live in tree-land. *In principle* is a DAG
statement.

---

## 2. The master-object reading

Let `X` be the homogeneous tree language `S → 1 | eml(S,S)` (plus input
leaves when a formula is not closed). Let `Z = F_calc` be the
scientific-calculator class of Table 1 in Odrzywołek 2026. Let
`q : X → Z ∪ {junk}` send a tree to its denotation when the denotation
lands in `F_calc`. Let `K` be any compiler that samples or synthesises
a tree in the fiber — bootstrap search, a master-formula prior, a
Gibbs grammar.

Then:

1. **Task-relevance descends.** Two EML trees that denote the same
   calculator function are interchangeable for any task that only reads
   that function.
2. **Irrelevant variation is confined to fibers.** Distinct trees for
   `ln` differ in syntax, not in the calculator button.
3. **Compact specification.** `|Z|` is the finite calculator basis, not
   the Catalan explosion of trees.
4. **Re-instantiation via `K`.** Completeness is exactly
   `supp K(·|z) ⊆ q⁻¹(z)` and `q⁻¹(z) ≠ ∅`.

Odrzywołek's completeness theorem, in this vocabulary, is fiber
inhabitation. The bootstrap procedure is an explicit (heuristic)
section of `K`. The master formula of his §4.3 is a parameterised
family of compilers on a finite depth cutoff.

This is the same object as SIC §1. It is not an analogy. The maps are
named.

---

## 3. Assumption ledger

| Assumption | Type | Load-bearing? | Why believed | Break test |
|---|---|---:|---|---|
| Completeness is the phenomenon | Ontology | high | Sheffer / NAND prestige | Access collapses at constant expressivity |
| Description complexity is invariant | Invariance | high | Kolmogorov / Solomonoff / Chaitin | True for DAGs; false for trees |
| Tree length is "the" complexity | Measurement | high | Symbolic regression, RPN `K` | Macro extension changes length exponentially |
| Circuit size tracks formula size | Measurement | high | Both count operations | Sharing: `Θ(n)` vs `2^{n+1}−1` |
| Learnability tracks shortest length | Causal | high | MDL habit | Gibbs mass is a *spectrum*, not a min |
| EML denotations have a 1-D invariant | Pragmatic | high for DP | Degree works for monomials | Fails for `eml`; spectrum not DP-able |
| Gibbs base 4 is canonical | Statistical | no | Binary+unary production cost | Any `β > ln 2` keeps the same qualitative split |
| Concern is optional | Boundary | high | Calculator has no valence | Then nothing in the stack matters |

---

## 4. Anomaly map

| Anomaly | Why it strains the frame | Assumption implicated | Artifact risk | Cluster |
|---|---|---|---|---|
| Blind recovery 100% → 0% from depth 2 to 6 | Expressivity is unchanged | Completeness is the phenomenon | Training overflow / NaNs | Access ≠ inhabitation |
| Perturbed-correct-weights recover 100% at depths 5–6 | Basins exist; search cannot find them | Learnability = shortest length | Init / Adam details | Fiber geometry |
| Compiler `K` vs direct-search `K` in Table 4 | Same denotations, wildly different lengths | Tree length is *the* complexity | Search timeout | Conservative extension |
| Lean `Complex.log 0 = 0` breaks the EML chain | Totality is a coordinate, not a fact | Measurement / edge | Junk-value convention | Paper 0, not this paper |
| Kolmogorov invariance cited for formula search | Invariance is a DAG theorem | Description complexity is invariant | Citation packaging | This paper's seam 2 |

Odrzywołek's own numbers (his §4.3):

> Systematic experiments (over 1000 runs) show that blind recovery from
> random initialization succeeds in 100% of runs at depth 2,
> approximately 25% at depths 3–4, and below 1% at depth 5. At depth 6,
> no blind recovery was observed in 448 attempts. … when the weights of
> the correct EML tree are perturbed by Gaussian noise, the optimization
> converges back to the exact values in 100% of runs, even for trees of
> depth 5 and 6.

That is Outcome A. Basins exist. Access collapses. Expressivity is
constant.

---

## 5. The separation theorem

Fix the multiplicative monoid of monomials in one variable. Two
languages:

- **Mul:** `S → x | ×(S,S)`.
- **Sq:** `S → x | ×(S,S) | sq(S)`, with `sq(y) := y·y`.

Denotation is degree. `×` adds degrees; `sq` doubles degree. Expanding
`sq(t)` to `t × t` is a conservative extension: every Sq-tree denotes
some `x^d`, and every `x^d` is already denoted by a Mul-tree (a full
binary tree with `d` leaves). Zero new denotations.

**US-1 (expressivity).** The two languages have the same denotation
class `{x^d : d ≥ 1}`.

**US-2 (tree complexity).** Every Mul-tree of degree `2^n` has size
`2^{n+1}−1`. The tower `sq^n(x)` has size `n+1`. The gap is
exponential. This is finite combinatorics: `size + 1 = 2·degree` on
Mul-trees, by structural induction.

**US-3 (circuit complexity).** A sharing DAG that starts from `x` and
applies `×` or `sq` at most doubles the running max degree at each
step. Degree `2^n` therefore needs `n` steps, and repeated squaring
achieves `n` in both bases. Circuit size is `Θ(n)` on both sides.

**US-4 (learnability / fiber mass).** Under the Gibbs prior
`π(t) ∝ 4^{-|t|}`, discovery probability is language-normalised fiber
mass `P(z) = Φ_z / Z`. On Mul, the entire fiber of `x^{2^n}` sits on
one size shell with Catalan degeneracy `C_{2^n−1}`. On Sq, the same
fiber occupies every size from `n+1` to `2^{n+1}−1`. Identical point
downstairs, different geometry upstairs.

The Lean file
`formal/structural-intelligence/StructuralIntelligence/Compiler/SquaringSeparation.lean`
banks US-1 (expand preserves degree), US-2, and US-3 by structural
induction, with no analysis and no `Complex.log`. Catalan counts and
Gibbs masses are the instrument, not the Lean kernel.

---

## 6. Fiber free energy

Write `Φ_z(L) = Σ_{t : q(t)=z} 4^{-|t|}` and `Z_L = Σ_t 4^{-|t|}` for
language `L`. Then `P_L(z) = Φ_z(L) / Z_L`.

Closed forms at `x = 1/4`:

- `Z_Mul = 2 − √3` (Catalan generating function `x C(x^2)`).
- `Z_Sq = (3 − √5)/2` (the grammar `A = x + xA + xA^2`).

The Mul fiber of `x^{2^n}` is exactly `C_{2^n−1}` trees of size
`2^{n+1}−1`, so `Φ` is closed-form. The Sq fiber is the DP
`count[s][2^n]` over sizes `s ≤ 2^{n+1}−1` (the expand-size bound
proves there is no larger Sq-tree of that degree).

A shortest-witness lower bound uses only the Sq-tower against the Mul
shell:

```
log₂(P_Sq / P_Mul)
    ≥ 2·(2^{n+1} − n − 2) + log₂(Z_Mul / Z_Sq) − log₂(C_{2^n−1}).
```

At `n=4` this is 28.28. Extra Sq shells can only raise the left-hand
side.

Shortest length is the wrong governor. The Gibbs discovery probability
is the *spectrum*. In `{x, ×}` the spectrum is a delta on one Catalan
shell. In the sq-extended basis it is a spread. That is why substrate
choice bites in practice even though "in principle" description
complexity is invariant.

---

## 7. Instrument and amendment

Package: `experiments/squaring_separation`. Exact integer DP, no
sampling. Registered `n ∈ {1,2,3,4}`. Six noncompensatory gates.

**Headline (`n=4`).**

| Quantity | Mul `{x,×}` | Sq `{x,×,sq}` |
|---|---:|---:|
| Min tree size | 31 | 5 |
| Occupied shells | 1 | 27 |
| Fiber count on the min shell | 9,694,845 | 1 (the tower) |
| `P(z)` | `7.845646×10^{-12}` | `3.997773×10^{-3}` |
| `log₂(P_Sq / P_Mul)` | 28.9247 | (bound 28.2797) |

The other registered rows grow as predicted: `log₂` ratios 1.81, 5.68,
13.35, 28.92 against bounds 1.49, 5.17, 12.74, 28.28.

**Amendment after run 1.** Gate
`SS_FIBER_MASS_EXCEEDS_SHORTEST_BOUND` first used the unnormalised
form `2·Δsize − log₂(C_{2^n−1})` (28.79 at `n=4`). That treats `Φ` as
if it were a probability. The Gibbs probability is `Φ/Z`, and
`log₂(Z_Mul/Z_Sq) ≈ −0.511`. The corrected bound is 28.28. The
measured 28.92 exceeds both; the amendment is a criterion identity,
not a result-dependent relaxation. It is in this section and in
`experiments/squaring_separation/core.py` (`AMENDMENT`).

**US-4′ is untested.** The conjecture that fiber free energy predicts
gradient recovery on EML master formulas is the first genuinely hard
piece of the EML-native story. EML denotations have no 1-D invariant
like degree, so the spectrum cannot be DP'd. Estimating it is where
the conjecture either earns its keep or dies usefully.

**Citations pending verification.** (1) Stachowiak 2026,
arXiv:2604.23893, algebraic structure of EML — listed from secondary
mention, primary text not checked here. (2) Internal program-note
packaging of the Kolmogorov invariance theorem — the public sources
are Kolmogorov 1965 and the standard prefix-complexity invariance
argument; the program-note wording is not treated as a source.

---

## 8. Honesty ledger

| Claim | Owner | Status |
|---|---|---|
| Syntax quotients by denotation | Denotational semantics | Prior art |
| Task-relative quotients | Bayes / Halmos–Savage / SIC Theorem 1 | Prior art |
| `{1, eml}` inhabits every calculator button | Odrzywołek 2026 | His |
| Expressivity ≠ tree ≠ circuit ≠ learnability, with an exponential witness at each seam | This paper | Ours |
| Discovery probability = fiber free energy under a Gibbs prior | This paper | Ours, on the toy; EML-native untested |
| Kolmogorov invariance for *formulas* | Nobody | False; the theorem is for programs |
| EML has valence | Nobody | False |

His universality and our task-relativity do not compete. They are
different levels: one substrate, many quotients.

---

## 9. Claim boundary

**Supported (this toy, exact).** US-1 through US-4 for
`n ∈ {1,2,3,4}` on real numbers; US-2/US-3 for all `n` as finite
combinatorics (Lean). The `n=4` masses and the 27-shell occupancy.

**Withheld.** US-4′ on EML. Any claim that EML search *is* fiber free
energy. Any claim that Gibbs base 4 is canonical. Any claim that
`eml` itself is a preferred compiler rather than one complete
substrate. Any valence, concern, or agency claim. Paper 0
(totalisation of `Complex.log`) is a different obstruction.

**What would change the conclusion.** A conservative extension of
`{x,×}` that does *not* move tree size by more than `O(1)` while
adding a definable macro; a sharing circuit for `x^{2^n}` with
`o(n)` steps; a Gibbs prior under which the Mul and Sq fibers of
`x^{16}` have `log₂` mass ratio `O(1)`; or an EML-native spectrum
estimate showing recovery rates track shortest depth rather than
fiber mass.

---

## 10. Sequencing

Paper 0 (EML in Lean) fights `Complex.log 0`. This paper's separation
theorem does not. `Compiler/SquaringSeparation.lean` is kernel-checked
on Lean 4.31: structural induction on finite trees, zero analysis,
zero `sorry`. Paper 0 remains blocked on totalization.

The open problem this paper exposes: estimate the EML-native fiber
spectrum without a 1-D invariant. That is the first hard piece of the
access story, and it is where US-4′ lives or dies.

---

## References

- Odrzywołek, A. (2026). All elementary functions from a single binary operator. arXiv:2603.21852.
- Kolmogorov, A. N. (1965). Three approaches to the quantitative definition of information. *Problems of Information Transmission* 1(1), 1–7.
- Halmos, P. R., & Savage, L. J. (1949). Application of the Radon–Nikodym theorem to the theory of sufficient statistics. *Annals of Mathematical Statistics* 20(2), 225–241.
- Brown, J. (2026). The Structural Intelligence Conjecture. `papers/structural_intelligence/paper.md`.
- Stachowiak, T. (2026). Algebraic structure behind Odrzywołek's EML operator. arXiv:2604.23893. **Pending primary-text verification.**
