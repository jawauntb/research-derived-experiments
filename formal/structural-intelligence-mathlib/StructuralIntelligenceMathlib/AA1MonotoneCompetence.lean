import Mathlib.Analysis.Convex.SpecificFunctions.Basic
import Mathlib.Analysis.Convex.Jensen
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Fintype.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Positivity

/-!
# Structural Intelligence (Mathlib) — AA-1 monotone predictive competence

The load-bearing inequality behind Theorem AA-1 from the *Autocatalytic
Artwork* companion paper (`papers/autocatalytic_artwork/paper.md`):
the Bayes-mixture predictor's log-likelihood is bounded **below** by the
prior-weighted average of the individual component log-likelihoods,

    log (∑ i, π i · p i)   ≥   ∑ i, π i · log (p i),

for any finite prior `π` (nonneg, `∑ π = 1`) and any positive family
of component predictives `p : Fin n → ℝ`.

This is the finite-dimensional case of concave Jensen's inequality
applied to `Real.log` on `Set.Ioi 0`.  Under the reading of AA-1 where
`p i` is the sample-likelihood `p_i(x_{1:T})` under hypothesis `i`,
the LHS is `log q(x_{1:T})` for the Bayes-mixture predictor
`q = ∑ π_i · p_i`, and the RHS is the prior-weighted average of the
individual hypothesis log-likelihoods.

The consequence — **audience-predictive log-likelihood is monotone
under refinement of the prior** in the sense that reweighting `π` to
concentrate more mass on higher-`log p_i` components raises the RHS
(and therefore raises the Bayes-mixture lower bound) — is captured
in `aa1_refinement_raises_lower_bound`.

Neither result axiomatises anything Mathlib-external.

Cited: Barron, A. R. (1998), *Information-theoretic characterization
of Bayes performance and the choice of priors in parametric and
nonparametric problems*, in Bayesian Statistics 6, Oxford University
Press, 27-52.
-/

namespace StructuralIntelligenceMathlib

open Finset

/-- **AA-1 core (concave-log Jensen inequality).**

    For a finite prior `π : Fin n → ℝ` (nonneg, `∑ π = 1`) and a
    strictly positive family of component predictives
    `p : Fin n → ℝ`, the log of the mixture dominates the weighted
    log-mean:

        ∑ i, π i · log (p i)   ≤   log (∑ i, π i · p i).

    This is Jensen's inequality for `Real.log` on `Set.Ioi (0 : ℝ)`.
    In the Bayes-mixture predictor reading (with `p i = p_i(x_{1:T})`
    the sample likelihood under hypothesis `i` and
    `q = ∑ π_i · p_i` the mixture), the LHS is the prior-averaged
    per-hypothesis log-likelihood and the RHS is the mixture
    predictive log-likelihood `log q(x_{1:T})`.

    Reference: Barron 1998, Bayesian Statistics 6, 27-52. -/
theorem aa1_log_mixture_ge_weighted_log
    {n : ℕ} (π : Fin n → ℝ) (p : Fin n → ℝ)
    (hπ_nn : ∀ i, 0 ≤ π i)
    (hπ_sum : ∑ i, π i = 1)
    (hp_pos : ∀ i, 0 < p i) :
    (∑ i, π i * Real.log (p i)) ≤ Real.log (∑ i, π i * p i) := by
  -- Concavity of `Real.log` on `Set.Ioi (0 : ℝ)`.
  have hconcave : ConcaveOn ℝ (Set.Ioi (0 : ℝ)) Real.log :=
    strictConcaveOn_log_Ioi.concaveOn
  -- Apply concave Jensen: rewrite `π i * y` as `π i • y` for `y : ℝ`.
  have h_jensen :
      (∑ i : Fin n, π i • Real.log (p i))
        ≤ Real.log (∑ i : Fin n, π i • p i) := by
    refine hconcave.le_map_sum ?_ hπ_sum ?_
    · intro i _; exact hπ_nn i
    · intro i _; exact hp_pos i
  -- `smul = mul` for reals.
  simp only [smul_eq_mul] at h_jensen
  exact h_jensen

/-- **AA-1 pointwise sample form.**  Specialise the previous theorem to
    the sample-likelihood picture: for each fixed observation sample
    `x` in some outcome type `X`, if `L : Fin n → X → ℝ` gives the
    positive per-hypothesis likelihood, then

        ∑ i, π i · log (L i x)   ≤   log (∑ i, π i · L i x).

    In the AA-1 reading this is `∑ π_i · log p_i(x_{1:T}) ≤ log q(x_{1:T})`
    for every sample; taking expectation under any generative
    distribution then gives the audience-averaged form. -/
theorem aa1_log_mixture_ge_weighted_log_sample
    {n : ℕ} {X : Type*} (π : Fin n → ℝ) (L : Fin n → X → ℝ)
    (hπ_nn : ∀ i, 0 ≤ π i)
    (hπ_sum : ∑ i, π i = 1)
    (hL_pos : ∀ i x, 0 < L i x)
    (x : X) :
    (∑ i, π i * Real.log (L i x))
      ≤ Real.log (∑ i, π i * L i x) :=
  aa1_log_mixture_ge_weighted_log π (fun i => L i x)
    hπ_nn hπ_sum (fun i => hL_pos i x)

/-- **AA-1 monotone-under-refinement corollary.**

    Suppose two finite priors `π, π' : Fin n → ℝ` (both nonneg, both
    summing to 1) are ordered pointwise in log-likelihood weight: for
    every hypothesis index `i`, `π i · log(p i) ≤ π' i · log(p i)`.
    Then the prior-averaged log-likelihood is monotone in the prior:

        ∑ i, π i · log(p i)   ≤   ∑ i, π' i · log(p i)
                              ≤   log (∑ i, π' i · p i).

    Combining with `aa1_log_mixture_ge_weighted_log` shows the Bayes
    mixture under the refined prior `π'` dominates the *lower bound*
    for the coarse prior `π`; this is the "refinement preserves the
    Barron lower bound" content of AA-1. -/
theorem aa1_refinement_raises_lower_bound
    {n : ℕ} (π π' : Fin n → ℝ) (p : Fin n → ℝ)
    (_hπ_nn  : ∀ i, 0 ≤ π i)  (_hπ_sum  : ∑ i, π i  = 1)
    (hπ'_nn : ∀ i, 0 ≤ π' i) (hπ'_sum : ∑ i, π' i = 1)
    (hp_pos : ∀ i, 0 < p i)
    (h_refine :
        ∀ i, π i * Real.log (p i) ≤ π' i * Real.log (p i)) :
    (∑ i, π i * Real.log (p i))
      ≤ Real.log (∑ i, π' i * p i) := by
  have h_mono :
      (∑ i, π i * Real.log (p i))
        ≤ (∑ i, π' i * Real.log (p i)) :=
    Finset.sum_le_sum (fun i _ => h_refine i)
  have h_jensen :
      (∑ i, π' i * Real.log (p i))
        ≤ Real.log (∑ i, π' i * p i) :=
    aa1_log_mixture_ge_weighted_log π' p hπ'_nn hπ'_sum hp_pos
  linarith

end StructuralIntelligenceMathlib
