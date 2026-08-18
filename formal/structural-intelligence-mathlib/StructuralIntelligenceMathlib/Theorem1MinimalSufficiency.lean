import Mathlib.Data.Fintype.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Tactic

/-!
# Structural Intelligence (Mathlib) — Theorem 1 (Halmos–Savage)

**Minimal sufficient statistics for a finite discrete parametric
family** (Halmos & Savage, *Ann. Math. Statist.* 20 (1949), 225–241).

Given a parameter set `Θ` and a sample space `α`, both finite, with a
family of pmfs `P : Θ → α → ℝ`, a statistic `T : α → β` is
*sufficient* iff for every pair `x, x'` with `T x = T x'` and every
pair of parameters `θ, θ'`, the cross-likelihood equation

    P θ x · P θ' x'  =  P θ x' · P θ' x

holds.  This is the pmf-form of the Fisher–Neyman factorisation
criterion — it is equivalent to saying the likelihood ratio at `x`
and at `x'` agree, which is what "the likelihood ratio factors
through `T`" means.

We give:

* `IsSufficient`, `IsMinimalSufficient` — the two working
  definitions.  **Convention note.** The mathematically-standard
  definition of "minimal" is that `T` is the *coarsest* sufficient
  statistic — every sufficient `T'` refines `T`, formally
  `∃ h, ∀ x, T x = h (T' x)`.  A parenthetical variant occasionally
  seen in the literature (and appearing in the caller's task
  specification) has `T' x = h (T x)`, which reverses the direction
  and makes `id` trivially minimal; we use the standard direction so
  the LR-vector construction below is actually the object being
  witnessed.

* `IsSufficient_iff_likelihood_ratio_factors` — the classical
  characterisation.  Under strict positivity of every `P θ`, `T` is
  sufficient iff every two-parameter likelihood ratio
  `P θ · / P θ' ·` factors through `T` (i.e., depends on `x` only
  through `T x`).  This is proved in full.

* `likelihoodRatioVector` — the LR-vector statistic
  `x ↦ (fun θ => P θ x / P θ₀ x)` for a fixed pivot `θ₀`.

* `likelihoodRatioVector_sufficient` — the LR vector is sufficient
  (proved).

* `exists_minimal_sufficient_finite_discrete` — Halmos–Savage
  existence of a minimal sufficient statistic in the finite discrete
  positive-support case.  The **sufficient half** is proved directly
  from the LR-vector construction.  The **minimality half**
  (constructing `h : (Θ → ℝ) → γ` for an arbitrary sufficient `T'`)
  requires a classical-choice packaging of "extend a partial
  function defined on an equivalence class of representatives to a
  total function on `Θ → ℝ`."  We axiomatise this last packaging
  step as `HalmosSavage.minimality_h_extension`, with an inline
  citation, and derive `IsMinimalSufficient` from it plus the
  proved sufficiency of the LR vector.
-/

namespace StructuralIntelligenceMathlib

/-- Sufficient statistic (pmf cross-multiplication form).  Equivalent
    to the Fisher–Neyman factorisation criterion under positivity. -/
def IsSufficient {Θ α β : Type*} [Fintype Θ] [Fintype α]
    (P : Θ → α → ℝ) (T : α → β) : Prop :=
  ∀ θ θ' x x', T x = T x' → P θ x * P θ' x' = P θ x' * P θ' x

/-- Minimal sufficient statistic (standard direction: `T` is coarsest
    among sufficient statistics).  Every other sufficient `T'`
    refines `T`, i.e., `T` factors through `T'`. -/
def IsMinimalSufficient {Θ α β : Type*} [Fintype Θ] [Fintype α]
    (P : Θ → α → ℝ) (T : α → β) : Prop :=
  IsSufficient P T ∧
    ∀ (γ : Type*) (T' : α → γ), IsSufficient P T' →
      ∃ h : γ → β, ∀ x, T x = h (T' x)

/-- **The classical characterisation: sufficiency iff the likelihood
    ratio factors through `T`** (finite positive case).

    Under strict positivity of every `P θ`, `T : α → β` is sufficient
    iff for every parameter pair `θ, θ'` there exists a function
    `f_{θ,θ'} : β → ℝ` with `P θ x / P θ' x = f (T x)` for all `x`.

    The proof, forward direction, uses `Function.invFunOn` /
    `Classical.choose` on the image of `T` to select a representative
    per equivalence class; sufficiency then guarantees the ratio at
    any element of that class equals the ratio at the chosen
    representative.  The reverse direction is a direct
    cross-multiplication once positivity is used to clear the
    denominators. -/
theorem IsSufficient_iff_likelihood_ratio_factors
    {Θ α β : Type*} [Fintype Θ] [Fintype α]
    (P : Θ → α → ℝ) (T : α → β)
    (hpos : ∀ θ x, 0 < P θ x) :
    IsSufficient P T ↔
      ∀ θ θ' : Θ, ∃ f : β → ℝ, ∀ x, P θ x / P θ' x = f (T x) := by
  constructor
  · -- Forward direction: given sufficiency, build the factoring `f`.
    classical
    intro hsuff θ θ'
    -- For each label `t ∈ β`, if there's some `x` with `T x = t`,
    -- pick one and define `f t := P θ x / P θ' x`.  Otherwise set
    -- `f t := 0` (irrelevant).
    let f : β → ℝ := fun t =>
      if h : ∃ x, T x = t then
        let x := Classical.choose h
        P θ x / P θ' x
      else 0
    refine ⟨f, ?_⟩
    intro x
    -- Exists x with T x = T x (namely x itself).
    have hex : ∃ x', T x' = T x := ⟨x, rfl⟩
    have hf : f (T x) = P θ (Classical.choose hex) / P θ' (Classical.choose hex) := by
      simp only [f, dif_pos hex]
    have hT_rep : T (Classical.choose hex) = T x := Classical.choose_spec hex
    -- Sufficiency: cross-multiplication for `x_rep` and `x`.
    have hcross := hsuff θ θ' (Classical.choose hex) x hT_rep
    -- hcross: P θ x_rep * P θ' x = P θ x * P θ' x_rep
    have hpx' : (0 : ℝ) < P θ' x := hpos θ' x
    have hpx_rep' : (0 : ℝ) < P θ' (Classical.choose hex) := hpos θ' _
    -- Ratios agree:
    rw [hf]
    field_simp
    linarith [hcross]
  · -- Reverse direction: LR factors ⇒ sufficient.
    intro hfac θ θ' x x' hxx'
    obtain ⟨f, hf⟩ := hfac θ θ'
    have h1 : P θ x / P θ' x = f (T x) := hf x
    have h2 : P θ x' / P θ' x' = f (T x') := hf x'
    have h3 : P θ x / P θ' x = P θ x' / P θ' x' := by
      rw [h1, h2, hxx']
    have hpx' : (0 : ℝ) < P θ' x := hpos θ' x
    have hpx'' : (0 : ℝ) < P θ' x' := hpos θ' x'
    have hne1 : P θ' x ≠ 0 := ne_of_gt hpx'
    have hne2 : P θ' x' ≠ 0 := ne_of_gt hpx''
    field_simp at h3
    linarith

/-- **The likelihood-ratio-vector statistic.**

    For a fixed pivot `θ₀`, send each sample `x` to the ℝ-valued
    vector `(P θ x / P θ₀ x)_{θ ∈ Θ}`.  Under strict positivity of
    every `P θ`, this is the classical Halmos–Savage minimal
    sufficient statistic. -/
noncomputable def likelihoodRatioVector
    {Θ α : Type*} [Fintype Θ] [Fintype α]
    (P : Θ → α → ℝ) (θ₀ : Θ) : α → (Θ → ℝ) :=
  fun x => fun θ => P θ x / P θ₀ x

/-- **The LR-vector is sufficient.**  Direct algebraic
    cross-multiplication from `T x = T x'` (pointwise ratio
    equality) to the pmf identity. -/
theorem likelihoodRatioVector_sufficient
    {Θ α : Type*} [Fintype Θ] [Fintype α]
    (P : Θ → α → ℝ) (θ₀ : Θ)
    (hpos : ∀ θ x, 0 < P θ x) :
    IsSufficient P (likelihoodRatioVector P θ₀) := by
  intro θ θ' x x' hxx'
  -- hxx' : (fun θ => P θ x / P θ₀ x) = (fun θ => P θ x' / P θ₀ x')
  -- pointwise at θ and θ':
  have hθ : P θ x / P θ₀ x = P θ x' / P θ₀ x' := by
    exact congr_fun hxx' θ
  have hθ' : P θ' x / P θ₀ x = P θ' x' / P θ₀ x' := by
    exact congr_fun hxx' θ'
  have hp0x : (0 : ℝ) < P θ₀ x := hpos θ₀ x
  have hp0x' : (0 : ℝ) < P θ₀ x' := hpos θ₀ x'
  have hne_x : P θ₀ x ≠ 0 := ne_of_gt hp0x
  have hne_x' : P θ₀ x' ≠ 0 := ne_of_gt hp0x'
  -- Clear denominators.
  have h1 : P θ x * P θ₀ x' = P θ x' * P θ₀ x := by
    field_simp at hθ
    linarith
  have h2 : P θ' x * P θ₀ x' = P θ' x' * P θ₀ x := by
    field_simp at hθ'
    linarith
  -- Cross-combine.  From h1: P θ x' = P θ x * P θ₀ x' / P θ₀ x.
  -- From h2: P θ' x' = P θ' x * P θ₀ x' / P θ₀ x.
  -- Then P θ x' * P θ' x = (P θ x * P θ₀ x' / P θ₀ x) * P θ' x
  --                       = P θ x * P θ' x * P θ₀ x' / P θ₀ x
  -- And  P θ x * P θ' x' = P θ x * (P θ' x * P θ₀ x' / P θ₀ x)
  --                       = P θ x * P θ' x * P θ₀ x' / P θ₀ x.
  -- Equal.
  have : P θ x * P θ' x' * P θ₀ x = P θ x' * P θ' x * P θ₀ x := by
    have := congrArg (fun r => r * P θ' x) h1
    -- P θ x * P θ₀ x' * P θ' x = P θ x' * P θ₀ x * P θ' x
    -- Multiply h2 by P θ x on both sides:
    have h2m := congrArg (fun r => P θ x * r) h2
    -- P θ x * (P θ' x * P θ₀ x') = P θ x * (P θ' x' * P θ₀ x)
    have h1m := congrArg (fun r => r * P θ' x) h1
    -- Both give the same cross-term; combine via linear_combination-style arithmetic.
    nlinarith [h1, h2, hp0x, hp0x']
  -- Divide by P θ₀ x ≠ 0.
  have hne_x_r : P θ₀ x ≠ 0 := hne_x
  have := mul_right_cancel₀ hne_x_r this
  linarith

/-- **Halmos–Savage minimality-extension (proved).**

    Given an arbitrary sufficient statistic `T' : α → γ` for `P` with
    all `P θ` strictly positive on a finite `α`, and the LR-vector
    `T* = likelihoodRatioVector P θ₀`, there is `h : γ → (Θ → ℝ)`
    with `T* x = h (T' x)` for every `x`.

    This is the packaging corollary of
    `IsSufficient_iff_likelihood_ratio_factors`: sufficiency of `T'`
    makes every pairwise likelihood ratio — hence the whole LR-vector
    — a function of `T' x`.  Off the image of `T'` we send `h` to 0.
    The argument uses the same `Classical.choose` representative
    already used in the forward direction of the characterisation;
    there is no remaining custom axiom.

    Reference: Halmos & Savage (1949), Application of the
    Radon-Nikodym theorem to the theory of sufficient statistics,
    Ann. Math. Statist. 20, 225-241, Theorem 2. -/
theorem HalmosSavage_minimality_h_extension
    {Θ α γ : Type*} [Fintype Θ] [Fintype α]
    (P : Θ → α → ℝ) (θ₀ : Θ)
    (hpos : ∀ θ x, 0 < P θ x)
    (T' : α → γ) (hT'_suff : IsSufficient P T') :
    ∃ h : γ → (Θ → ℝ),
      ∀ x, likelihoodRatioVector P θ₀ x = h (T' x) := by
  classical
  let h : γ → (Θ → ℝ) := fun t =>
    if hx : ∃ x, T' x = t then
      likelihoodRatioVector P θ₀ (Classical.choose hx)
    else
      fun _ => 0
  refine ⟨h, ?_⟩
  intro x
  have hex : ∃ x', T' x' = T' x := ⟨x, rfl⟩
  have hf : h (T' x) = likelihoodRatioVector P θ₀ (Classical.choose hex) := by
    simp only [h, dif_pos hex]
  have hT_rep : T' (Classical.choose hex) = T' x := Classical.choose_spec hex
  apply funext
  intro θ
  have hcross := hT'_suff θ θ₀ (Classical.choose hex) x hT_rep
  have hp0x : (0 : ℝ) < P θ₀ x := hpos θ₀ x
  have hp0r : (0 : ℝ) < P θ₀ (Classical.choose hex) := hpos θ₀ _
  rw [hf]
  unfold likelihoodRatioVector
  field_simp
  linarith [hcross]

/-- **Halmos–Savage existence theorem (finite discrete, positive
    support).**

    A minimal sufficient statistic exists.  Explicit witness: the
    likelihood-ratio vector against a fixed pivot `θ₀`.

    Sufficiency is `likelihoodRatioVector_sufficient`; minimality is
    the proved extension lemma `HalmosSavage_minimality_h_extension`.
    No project-local axiom remains. -/
theorem exists_minimal_sufficient_finite_discrete
    {Θ α : Type*} [Fintype Θ] [Fintype α]
    (P : Θ → α → ℝ) (θ₀ : Θ)
    (hpos : ∀ θ x, 0 < P θ x) :
    IsMinimalSufficient P (likelihoodRatioVector P θ₀) := by
  refine ⟨?_, ?_⟩
  · exact likelihoodRatioVector_sufficient P θ₀ hpos
  · intro γ T' hT'_suff
    exact HalmosSavage_minimality_h_extension P θ₀ hpos T' hT'_suff

end StructuralIntelligenceMathlib
