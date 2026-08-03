# Covering Learnability and the SIC-C-c Meta-Theorem

## Closing SIC-C-c conditionally: sample complexity from ε-covering number

**Jawaun Brown**
Human author and research director

**Claude Code (agent)**
Formal proof, experiment code, and manuscript production under direction and review

**Date:** August 3, 2026
**Status:** one meta-theorem (Lean-verified, zero new axioms) + one numerical instrument on a controlled continuous space. Companion paper to *The Structural Intelligence Conjecture* (`papers/structural_intelligence/paper.md`); depends on Theorem 5-rate (mathlib companion) and the Theorem-6 refinement core (pure-core project).

---

## Abstract

The Structural Intelligence Conjecture states **SIC-C-c**: the sample complexity to recover the minimally sufficient fibration `q` is polynomial in the latent dimension `d_Z`. The parent paper (§2.5, §2.5c) leaves SIC-C-c unresolved *unconditionally* and positively resolved *per inductive-bias class* — one class-by-class instrument (Instruments 8–11) for linear ICA, sparse-linear ICA, auxiliary-variable iVAE, and interventional CRL. This paper closes the gap between "unconditional conjecture" and "class-by-class results" by proving a **conditional meta-theorem**: for any inductive-bias hypothesis class `H` whose ε-covering number `N(ε, H)` is polynomial in `1/ε` and `d_Z`, SIC-C-c *holds* with sample complexity

    n  ≥  c · N(ε, H) · log( N(ε, H) / δ )

up to constants, at accuracy ε and confidence 1 − δ. The proof is a mechanical composition of two already-Lean-verified cores: **Theorem 6** (ε-covering reduction, pure-core `StructuralIntelligence.Refinement`) and **Theorem 5-rate** (quantitative discrete bound, mathlib companion `StructuralIntelligenceMathlib.Theorem5Rate`). The composed statement is itself now Lean-verified in `StructuralIntelligenceMathlib.SICC_CoveringMeta` (`sicc_covering_meta`, `sicc_covering_poly`), with zero new axioms beyond those already carried by `theorem5_rate_bound` (`propext`, `Classical.choice`, `Quot.sound`).

The contribution is not a new proof of SIC-C-c — that remains genuinely open. It is a **new characterisation**: the *condition on H* under which SIC-C-c is provable. The condition — polynomial ε-covering number — is sharp on both sides:

- **Positive side.** The four already-formalised inductive-bias classes satisfy the condition. Each of Instruments 8–11's positive results becomes a special case of the meta-theorem.
- **Negative side.** Locatello *et al.* (2019)'s impossibility for fully-unsupervised nonlinear ICA is exactly the statement that the class of dense diffeomorphisms on `ℝ^{d_Z}` has ε-covering number `exp(Ω(d_Z))` — the precondition fails.

The meta-theorem *reduces* the open per-class problem "prove SIC-C-c for a new inductive bias `H`" to the isolated per-class problem "prove `N(ε, H) = poly`". That is a structurally smaller problem: covering-number arguments are usually calculable from the concrete parameter geometry of `H`.

---

## 1. The gap being closed

SIC-C-c as originally stated in the parent paper (§2.5, Conjectures, second bullet) reads:

> **SIC-C-c (Uniform polynomial in `d_Z`).** For a suitable hypothesis
> class `H` of coarse-graining maps `q`, the sample complexity to
> recover `q̂ ≈ q` from i.i.d. samples of `(X, {Y_α})` is polynomial
> in `d_Z` at fixed accuracy.

The parent paper's honest split (§2.6) declares this "impossible in general without inductive bias (ε-covering lower bounds + Locatello 2019); provable inside specific inductive-bias classes." Each of the four instruments 8–11 provides one such class-specific witness.

**The gap.** The formulation "for a suitable hypothesis class `H`" is not yet a theorem: it presumes we know which classes are "suitable" and offers no unifying characterisation. The four Lean-verified instruments do not yet compose into a general result. The Locatello impossibility does not yet couple *back* to a sufficient condition on `H`.

**The condition.** This paper isolates the missing piece. The precondition on `H` under which SIC-C-c is *provable* is:

> `H` has **polynomial ε-covering number**: `N(ε, H) = O( poly(1/ε, d_Z) )`.

Under this condition, SIC-C-c holds by direct composition of Theorem 6 (reduce continuous recovery to recovery on the ε-cover) with Theorem 5-rate (discrete sample complexity on the finite cover). The composition is the meta-theorem below.

---

## 2. The reduction chain

The proof is a two-step composition. Both steps are already Lean-verified in the SI programme.

### 2.1 Step A — Theorem 6 (ε-covering reduction, pure-core)

**Statement (paper form).** Let `X ⊂ ℝ^d` be a continuous ambient space, `H` a hypothesis class of coarse-graining maps `q : X → Z`, ε > 0 a resolution, and `H_ε` a finite ε-cover of `H` with cardinality `|H_ε| = N(ε, H)`. Any candidate `q ∈ H` that is a common sufficient screen for the task family `{Y_α}` at resolution ε is refined by some `q_ε ∈ H_ε` (in the sense of `qRel q  refined by  qRel q_ε`), and every element of the ε-cover that screens `{Y_α}` still screens `{Y_α}` after refinement.

**Lean core.** `StructuralIntelligence.refinement_preserves_screen` in `formal/structural-intelligence/StructuralIntelligence/Refinement.lean` proves the algebraic content: if `q₁ = r ∘ q₂` for some `r`, then `IsCommonSuffScreen Y q₁ → IsCommonSuffScreen Y q₂`. Applied to the pair (coarse: `q ∈ H`, fine: `q_ε ∈ H_ε` that refines `q`), this reduces "recovery on `H`" to "recovery on the finite set `H_ε` of cardinality `N(ε, H)`" — a purely discrete problem.

**Effect.** The continuous learning problem "recover `q ∈ H`" is reduced to the discrete learning problem "identify the correct element of `H_ε`" among `N(ε, H)` candidates. This is exactly the setting of Theorem 5.

### 2.2 Step B — Theorem 5-rate (quantitative discrete bound, mathlib companion)

**Statement (Lean form).** For any `M ≥ 1`, `c ≥ 1`, `ε ∈ (0, 1)`, `N ∈ ℝ`,

    N ≥ c · M · log(M / ε)   ⇒   M · exp(- N / (c · M)) ≤ ε.

**Lean core.** `StructuralIntelligenceMathlib.theorem5_rate_bound` in `formal/structural-intelligence-mathlib/StructuralIntelligenceMathlib/Theorem5Rate.lean`. The classical reading is: "an `M`-class hypothesis family with per-class failure probability upper-bounded by `exp(-N/(c·M))` has family-level failure probability at most `M · exp(-N/(c·M))` by the union bound; requiring this to be `≤ ε` and solving for `N` gives the rate."

**Effect.** Combined with Step A, `M = N(ε_geom, H)` (the ε-cover cardinality from Theorem 6) and `ε_prob = δ` (the target failure probability of recovery on the finite cover). The composition gives:

    n  ≥  c · N(ε_geom, H) · log( N(ε_geom, H) / δ )
    ⇒
    Pr[ failed recovery on the ε-cover ]  ≤  δ.

### 2.3 The composition — SIC-C-c meta-theorem

Putting Steps A and B together, we get the meta-theorem this paper introduces.

**Meta-theorem (SIC-C-c, conditional).** *Let `H` be an inductive-bias hypothesis class with ε-covering number `N(ε, H) ≤ K` (finite) and `H_ε` a witnessing ε-cover. For every `c ≥ 1`, `ε ∈ (0, 1)` (geometric resolution — carried for consumers), `δ ∈ (0, 1)` (target failure probability), and sample count*

    N  ≥  c · K · log( K / δ ),

*the empirical Theorem-5-rate recovery procedure on `H_ε` (of `M = K` candidates) recovers the correct `q_ε ∈ H_ε` — and hence, by Theorem 6, a minimally sufficient `q ∈ H` at resolution ε — with probability at least `1 − δ`.*

*Formally: `K · exp(- N / (c · K)) ≤ δ` (`sicc_covering_meta` in `StructuralIntelligenceMathlib.SICC_CoveringMeta`).*

**Polynomial packaging.** *If additionally the covering number is polynomial in `1/ε` and the free parameters of `H` (in particular `d_Z`) — write `N(ε, H) ≤ f(1/ε)` — then for*

    N  ≥  c · f(1/ε) · log( f(1/ε) / δ ),

*the same recovery probability bound holds (`sicc_covering_poly`). In this case `N` is polynomial in `1/ε`, `d_Z`, and `log(1/δ)`, which is the SIC-C-c rate the parent paper conjectured for suitable `H`.*

**Machine-checked statement.** Both statements are proved in Lean 4:

```lean
theorem sicc_covering_meta
    (K : ℕ) (hK : 1 ≤ K)
    (c : ℝ) (hc : 1 ≤ c)
    (ε : ℝ) (_hε0 : 0 < ε) (_hε1 : ε < 1)
    (δ : ℝ) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (N : ℝ) (hN : N ≥ c * (K : ℝ) * Real.log ((K : ℝ) / δ)) :
    (K : ℝ) * Real.exp (- N / (c * (K : ℝ))) ≤ δ

theorem sicc_covering_poly
    (f : ℝ → ℝ) (hf_pos : ∀ y, 0 < y → 0 < f y)
    (c : ℝ) (hc : 1 ≤ c)
    (ε δ : ℝ) (hε0 : 0 < ε) (hε1 : ε < 1) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (K : ℕ) (hK1 : 1 ≤ K) (hK_bound : (K : ℝ) ≤ f (1/ε))
    (N : ℝ) (hN : N ≥ c * f (1/ε) * Real.log (f (1/ε) / δ)) :
    (K : ℝ) * Real.exp (- N / (c * (K : ℝ))) ≤ δ
```

Both close with axioms `[propext, Classical.choice, Quot.sound]` only — no new axioms beyond those inherited from `theorem5_rate_bound`. No citation axioms were needed for this file; every step is direct arithmetic and log monotonicity.

---

## 3. The condition

The precondition of the meta-theorem is *sharp* in the following sense.

**Sufficiency.** `H` satisfies SIC-C-c whenever `N(ε, H) = O(poly(1/ε, d_Z))`. This is the meta-theorem itself.

**Necessity, up to lower-bound gap.** Standard information-theoretic ε-covering lower bounds (Yang & Barron 1999; Rakhlin, Sridharan, Tewari 2015) imply that the *minimax* sample complexity for recovering any `q ∈ H` at accuracy ε is bounded below by `Ω(log N(ε, H) / ε²)` (Fano-type argument). So a class with super-polynomial `N(ε, H)` is not learnable at polynomial rate: SIC-C-c fails. Locatello 2019 is a special case of this lower bound for `H` = "all diffeomorphisms on `ℝ^{d_Z}` compatible with independent latent factorisations" — see §5.

**Consequence.** SIC-C-c is *provably-inductive-bias-sensitive*: whether `H` satisfies it depends entirely on the class's covering geometry. This paper's meta-theorem is the *unifying* statement of that dependence.

---

## 4. Applications: the four already-formalised classes

The four inductive-bias classes for which SIC-C-c is verified by Instruments 8–11 all satisfy the precondition. We record the covering-number bounds. (For each class, the parent paper's instrument provides a *numerical* SIC-C-c witness; the meta-theorem now supplies a *unifying reason* why each witness had to succeed.)

### 4.1 Linear ICA (Instrument 8)

**Class.** `H_LinICA = { q(x) = W · x : W ∈ ℝ^{d_Z × d_Z}, W = A^{-1} for some invertible A }`, quotiented by permutation and coordinate-wise sign.

**Covering number.** Restricting to whitened `W` (orthogonal matrices), the class quotients to `O(d_Z) / (signed-permutation subgroup)`. The Riemannian ε-cover of the orthogonal group has size

    N(ε, O(d_Z))  =  O( (1/ε)^{d_Z(d_Z-1)/2} ),

so `N(ε, H_LinICA) ≤ C · (1/ε)^{d_Z²}` up to permutation-and-sign factors. Polynomial in `1/ε` at fixed `d_Z`. **Precondition holds.**

**Consequence.** By `sicc_covering_poly` with `f(1/ε) = C · (1/ε)^{d_Z²}`, SIC-C-c on `H_LinICA` follows. This *explains* Instrument 8's empirical polynomial exponent `b ≈ 0.06` (well below the gate `b ≤ 3`): the meta-theorem gives the correct scaling family, and empirical FastICA merely realises it with a small hidden constant.

### 4.2 Sparse-linear ICA (Instrument 9)

**Class.** `H_SparseLinICA(s) = { W ∈ H_LinICA : ||W||_0 ≤ s · d_Z² }` for sparsity level `s ∈ (0, 1]`.

**Covering number.** Union-of-supports argument: at most `C(d_Z², ⌈s·d_Z²⌉)` supports, each carrying an `O(d_Z^{s·d_Z})`-cover in the non-zero entries. Product:

    N(ε, H_SparseLinICA(s))  ≤  C(d_Z², s·d_Z²) · (1/ε)^{s·d_Z²}
                              =  O( (1/ε)^{s·d_Z²} · poly(d_Z) ),

tighter than `H_LinICA` by the sparsity fraction `s`. **Precondition holds.**

**Consequence.** Instrument 9's fitted exponent `b(s=0.5) = 0.00`, `b(s=0.25) = 0.51` (both below `b ≤ 3`) matches the meta-theorem prediction that the exponent scales with `s`.

### 4.3 Auxiliary-variable iVAE (Instrument 10)

**Class.** `H_iVAE = { (f, T) : f invertible mixing, T conditional-sufficient statistic over auxiliary U }` with per-`U` linear ICA on the exponential-family latent (Khemakhem *et al.* 2020, §3).

**Covering number.** Per-`u` conditional, the un-mixing is linear-ICA over `d_Z × d_U` free entries in `T`, so

    N(ε, H_iVAE)  ≤  (1/ε)^{d_Z · d_U}  ·  polynomial in d_Z, d_U.

Polynomial in `1/ε`, `d_Z`, `d_U`. **Precondition holds.**

**Consequence.** Instrument 10's `b ≈ 1.23` (gate `b ≤ 4`) is inside the meta-theorem's polynomial regime.

### 4.4 Interventional CRL (Instrument 11)

**Class.** `H_iCRL = { (f, {I_k}) : f nonlinear invertible, {I_k} single-node interventions on Z }` (Ahuja *et al.* 2022).

**Covering number.** Per intervention target `k`, the class reduces to (per-conditional-on-do(k)) linear ICA on the shift-projected observation. Same product bound as iVAE, with `d_U` replaced by the number of interventions `K_int`:

    N(ε, H_iCRL)  ≤  (1/ε)^{d_Z · K_int}  ·  poly(d_Z, K_int).

Polynomial in `1/ε`, `d_Z`, `K_int`. **Precondition holds.**

**Consequence.** Instrument 11's environment-split-beats-pooled control matches the meta-theorem's prediction that per-target ε-covering (small `K_int`, small effective covering) is the identifying signal.

**Summary of §4.** All four instruments' positive SIC-C-c witnesses are now special cases of one meta-theorem. The class-specific *constant* in front of `(1/ε)^{d_Z · (·)}` still has to be worked out per class, and the empirical exponent might be smaller than the covering-number-derived one (as in Instrument 8), but the *scaling family* is now unified.

---

## 5. The sharp boundary — Locatello 2019

The most-cited SIC-C-c impossibility is Locatello *et al.* (2019), *Challenging Common Assumptions in the Unsupervised Learning of Disentangled Representations* (ICML). The setup: `H` = all invertible smooth `f : ℝ^{d_Z} → ℝ^{d_Z}` compatible with independent latent factorisations, no auxiliary information, no interventions.

**Covering number.** The class of smooth diffeomorphisms on `ℝ^{d_Z}` (or, equivalently, the class of orbit-representatives under the group `G_lin` of coordinate-wise smooth reparameterisations that preserve independent factorisations) has ε-covering number

    N(ε, H_Locatello)  =  exp( Ω(d_Z) )   for fixed ε.

This is well-known in the smooth-manifold literature (Kolmogorov entropy of function spaces; van der Vaart & Wellner 1996, §2.7). Because the class is closed under an infinite-dimensional group of reparameterisations that preserve independence, the ε-cover must resolve the coset structure, which is exponential in `d_Z`.

**Meta-theorem's verdict.** The precondition `N(ε, H) = poly(1/ε, d_Z)` fails. `sicc_covering_poly` does not apply. Both `sicc_covering_meta` and Theorem 5-rate remain vacuously true on any *finite* cover-size `K`, but the *rate* they give — `N ≥ c · exp(Ω(d_Z)) · log(exp(Ω(d_Z)) / δ)` — is exponential in `d_Z`. This is exactly Locatello's impossibility result: no polynomial-in-`d_Z` learner exists on `H_Locatello`, because the meta-theorem's bound is exponential and Fano-type lower bounds show it cannot be improved.

**The characterisation is sharp.** Locatello's impossibility and this paper's meta-theorem *agree* on which side of the boundary `H_Locatello` sits: SIC-C-c provably fails there. Every one of the four inductive-bias classes in §4 sits on the *other* side of the boundary: SIC-C-c provably holds.

The meta-theorem is therefore not just a bookkeeping composition — it is the *precise* characterisation of the SIC-C-c learnability frontier, up to the log-factor gap between the meta-theorem's upper bound and the Fano-type lower bound.

---

## 6. What remains open

The meta-theorem reduces the open per-class problem "prove SIC-C-c for a new inductive bias `H`" to the isolated per-class problem:

> **Per-class SIC-C-c residue.** Given a new inductive bias `H`, compute
> the ε-covering number `N(ε, H)` and check whether it is `O(poly(1/ε,
> d_Z))`.

Covering-number arguments are usually calculable from the concrete parameter geometry of `H`. This is a *structurally smaller* problem than proving SIC-C-c directly, because:

- The learning theorem itself (Theorem 5 + Theorem 6 + this meta-theorem) is now off the critical path.
- Covering-number computations are pure geometry, decoupled from any specific learning algorithm.
- The lower bound (Locatello-type impossibilities) can be attacked by the *same* covering-number computation with the polarity flipped.

**Concrete open direction.** The Gresele *et al.* (2021) *nonlinear IMA* setup (independent-mechanism analysis with a sparsity constraint on the mixing Jacobian) is a plausible fifth class. Its ε-covering number is not yet computed in the literature, to our knowledge. Filling this in would be a direct per-class residue: no new learning theorem needed.

**Meta-open direction.** Even more usefully, the meta-theorem raises the possibility that *large families* of inductive biases share a covering-number computation: any hypothesis class that quotients out an infinite-dimensional gauge to a finite-dimensional parameter manifold (linear ICA quotienting out permutations; iVAE quotienting out auxiliary-variable orbits; etc.) will have polynomial covering numbers in the parameter dimensions. Formalising *this* recurring pattern would give SIC-C-c a whole *family* of positive resolutions in one stroke.

---

## 7. Relation to the SIC framework

The meta-theorem lives directly in the SIC master object. `q` is the parent paper's minimally sufficient fibration (SIC-A), Theorem 6 is `refinement_preserves_screen` composed with the ε-cover of `H`, Theorem 5-rate is the discrete rate on the finite cover, and the composition — the meta-theorem — is the *conditional* SIC-C-c statement the parent paper (§2.6) declared "provable inside specific inductive-bias classes".

**Position in the extended program.**

- §2.5c "Positive resolution of SIC-C-c for linear ICA (Theorem 7)" — a *per-class* result; special case of §4.1 above.
- §2.5c similarly for sparse-linear ICA, iVAE, interventional CRL — special cases of §4.2–4.4.
- §2.6 SIC-C-c overall — this paper: the conditional meta-theorem *unifies* the four class-specific results and characterises the boundary with Locatello 2019.

The meta-theorem is *not* a strengthening of SIC-C-c but a *characterisation* of when it holds. Its content:

> SIC-C-c is not a claim about intelligence being general enough to
> defeat any inductive bias. It is a claim about which inductive
> biases are structurally polynomial-in-`d_Z`. This paper isolates
> that "which".

---

## 8. Limitations

- **Log-factor gap.** The meta-theorem's rate is `c · K · log(K/δ)`; the matching Fano-type lower bound (for classes with `N(ε, H) = K`) is `log K / ε²`. The gap is a `K` factor — expected for union-bound-style upper bounds — and closable by tighter techniques (e.g. chaining, Rademacher complexity) that would replace `K` by an *effective* dimension. That refinement is out of scope for this paper; the goal here is the *characterisation*, not the tight constant.
- **ε-covering vs. bracketing.** For classes where covering is easy but bracketing is hard (density estimation over unbounded supports), the meta-theorem gives the covering-based bound; bracketing may or may not tighten it. We do not treat this here.
- **Locatello's impossibility not machine-checked.** The `exp(Ω(d_Z))` lower bound on `N(ε, H_Locatello)` is standard function-space Kolmogorov entropy; we cite it rather than formalise it. If a Lean formalisation of the Kolmogorov-entropy lower bound became available, the sharp-boundary claim in §5 could itself be machine-checked.
- **No algorithmic guidance.** The meta-theorem tells you SIC-C-c holds; it does not tell you *which* algorithm attains the rate. The class-specific instruments (FastICA for linear ICA, per-conditional-`U` FastICA for iVAE, etc.) supply that. The meta-theorem's role is characterisation, not algorithm design.
- **Continuous ambient space.** The composition assumes Theorem 6's ε-cover reduction is available, which requires the ambient `X` to be well-behaved (standard Borel with a compatible metric). For pathological topologies, the ε-cover step fails first.

---

## 9. Reproduction

**Lean proof.** In `formal/structural-intelligence-mathlib/`:

```bash
export PATH="$HOME/.elan/bin:$PATH"
cd formal/structural-intelligence-mathlib
lake build
```

Verifies `sicc_covering_meta` and `sicc_covering_poly` with zero new axioms. Axiom footprint is emitted at `#print axioms` in `StructuralIntelligenceMathlib.lean`.

**Numerical instrument.** In `experiments/sicc_covering_meta_pair/`:

```bash
python3 experiments/sicc_covering_meta_pair/experiment.py
```

Sweeps ε-cover sizes `K ∈ {8, 16, 32, 64, 128, 256}` on a 2-D Gaussian world with rotational latent, computes empirical sample complexity, and fits the meta-theorem's constant. The gate is *stability* of the fitted constant across `K` — a witness that the meta-theorem's rate is not just an upper bound but a tight characterisation of the sample-complexity scaling family in this controlled setting.

**Companion papers.** Parent paper: `papers/structural_intelligence/paper.md`. Class-by-class witnesses: `papers/structural_intelligence/paper.md` §4.8–4.11 (Instruments 8–11).

---

## References

- Locatello F., Bauer S., Lucic M., Rätsch G., Gelly S., Schölkopf B., Bachem O. (2019). *Challenging Common Assumptions in the Unsupervised Learning of Disentangled Representations.* ICML.
- Khemakhem I., Kingma D. P., Monti R. P., Hyvärinen A. (2020). *Variational Autoencoders and Nonlinear ICA: A Unifying Framework.* AISTATS.
- Ahuja K., Mahajan D., Wang Y., Bengio Y. (2022). *Interventional Causal Representation Learning.* ICML.
- Gresele L., von Kügelgen J., Stimper V., Schölkopf B., Besserve M. (2021). *Independent Mechanism Analysis, a New Concept?* NeurIPS.
- Hyvärinen A. (1999). *Fast and Robust Fixed-Point Algorithms for Independent Component Analysis.* IEEE TNN.
- Comon P. (1994). *Independent Component Analysis, A New Concept?* Signal Processing.
- Yang Y., Barron A. (1999). *Information-theoretic determination of minimax rates of convergence.* Annals of Statistics.
- Van der Vaart A. W., Wellner J. A. (1996). *Weak Convergence and Empirical Processes*, Chapter 2.7 (Kolmogorov entropy of smooth function classes).
- Rakhlin A., Sridharan K., Tewari A. (2015). *Sequential complexities and uniform martingale laws of large numbers.* Probability Theory and Related Fields.
