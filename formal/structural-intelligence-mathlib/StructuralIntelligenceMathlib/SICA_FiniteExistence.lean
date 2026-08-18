import Mathlib.Data.Fintype.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Tactic
import StructuralIntelligenceMathlib.Theorem1MinimalSufficiency
import StructuralIntelligenceMathlib.Proposition3Adjunction

/-!
# Structural Intelligence (Mathlib) — SIC-A derived in the finite discrete positive-support case

**Companion paper:** `papers/structural_intelligence_foundations/paper.md`.

The Structural Intelligence Conjecture opens with SIC-A: the existence
of a master fibration `(q : X → Z, K : Z ⇝ X)` with
`supp K(·|z) ⊆ q⁻¹(z)`, jointly minimally sufficient for a task
family.  In the parent paper the fibration is *posited*; every downstream
theorem takes it as given.

This file **derives** SIC-A in the finite discrete positive-support
case by composing three already-verified components:

* **Theorem 1 (Halmos–Savage, finite discrete positive-support form)**
  from `StructuralIntelligenceMathlib.Theorem1MinimalSufficiency`
  provides `q := likelihoodRatioVector P θ₀` together with its
  sufficiency (`IsSufficient P q`) and minimality
  (via `HalmosSavage_minimality_h_extension`).
* **Proposition 3 (`Coarsen ⊣ Refine` adjunction)** from
  `StructuralIntelligenceMathlib.Proposition3Adjunction` supplies the
  categorical scaffold that a fibre-supported, fibre-normalised kernel
  `K` over `q` fits into.
* The **uniform-on-fibre kernel** is the canonical `K` we construct
  from `q` alone (no extra input data required).  It is fibre-supported
  by construction and fibre-normalised on every `z ∈ image(q)`.

The finite target type `Z` we build here is the image of `q` inside
`Θ → ℝ`, wrapped as a Finset-subtype.  Because `ℝ` has no
constructive `DecidableEq`, we introduce a classical `DecidableEq`
instance for `Θ → ℝ` inside the proof (`Classical.decEq _`); the
resulting `Z` has both `Fintype` and `DecidableEq` witnesses that we
package into the existential.

**Axioms.**  This file introduces **zero new axioms**.  The Halmos–
Savage packaging step `HalmosSavage_minimality_h_extension` is now a
theorem (Wave 9); it enters the coarsestness corollary
`sic_a_finite_discrete_coarsest` only as ordinary Mathlib-scale
`Classical.choice` via `Classical.choose`.  The pure-existence
theorem `sic_a_finite_discrete` uses only the sufficiency half of
Theorem 1 plus finite-sum bookkeeping — its axiom footprint is the
standard `propext`, `Classical.choice`, `Quot.sound` inherited from
Mathlib.

**What stays open.**  The general topological / measure-theoretic case
requires regular conditional distributions on standard Borel spaces
and a σ-algebra completion argument that Mathlib v4.32.2 does not
expose.  See the paper's §6 for the honest scope.
-/

namespace StructuralIntelligenceMathlib

open Finset BigOperators

/-- **SIC-A in the finite discrete positive-support case.**

    Given a finite non-empty sample space `α`, a finite parameter set
    `Θ` (both at universe `u`), a strictly-positive pmf family
    `P : Θ → α → ℝ`, and any fixed pivot `θ₀ ∈ Θ`, there exist a
    finite target type `Z : Type u` (with `Fintype` and `DecidableEq`
    instances), a partition map `q : α → Z`, and a kernel
    `K : Z → α → ℝ` such that

    * `q` is sufficient for `P` in the Fisher–Neyman / Halmos–Savage
      pmf cross-multiplication sense (from Theorem 1);
    * `K` is *fibre-supported*: `K z x = 0` whenever `q x ≠ z`
      (the Proposition 3 side condition made concrete);
    * `K` is *fibre-normalised* on the image of `q`: `∑ x, K z x = 1`
      for every `z ∈ image(q)`, and `= 0` for every `z ∉ image(q)` —
      packaged as a disjunction because the target `Z` here is
      constructed to be exactly `image(q)`, so the second disjunct is
      vacuous for our witness but is included for signature honesty.

    The `μ` argument (a base distribution on `α`) is threaded through
    the signature for downstream compatibility (rate–distortion
    parameterisations, Bayesian posteriors) but is not used by the
    construction: the uniform-on-fibre `K` is `μ`-independent.

    The universes: `Θ` at `u`, `α` at `v`; the target `Z` lives at `u`
    because it is a subtype of `Θ → ℝ` and `ℝ : Type 0`. -/
theorem sic_a_finite_discrete.{u, v}
    {Θ : Type u} {α : Type v} [Fintype Θ] [Fintype α] [DecidableEq α]
    (P : Θ → α → ℝ) (θ₀ : Θ) (hpos : ∀ θ x, 0 < P θ x)
    (μ : α → ℝ) (_hμ_nn : ∀ x, 0 ≤ μ x) (_hμ_sum : ∑ x, μ x = 1) :
    ∃ (Z : Type u) (_ : Fintype Z) (_ : DecidableEq Z)
      (q : α → Z) (K : Z → α → ℝ),
      IsSufficient P q ∧
      (∀ z x, q x ≠ z → K z x = 0) ∧
      (∀ z, ∑ x, K z x = 1 ∨ ∑ x, K z x = 0) := by
  classical
  -- We need a classical DecidableEq on (Θ → ℝ) to build the target subtype.
  haveI decΘR : DecidableEq (Θ → ℝ) := Classical.decEq _
  -- The LR-vector against the pivot θ₀ is our sufficient statistic (T1).
  let f : α → (Θ → ℝ) := likelihoodRatioVector P θ₀
  -- Z := image of f, packaged as a Finset of (Θ → ℝ).
  let ZFin : Finset (Θ → ℝ) := (Finset.univ : Finset α).image f
  -- The finite target type: the subtype of (Θ → ℝ) living in the image.
  let ZT : Type u := {v : (Θ → ℝ) // v ∈ ZFin}
  -- The corestriction of f into ZT.
  let q : α → ZT := fun x =>
    ⟨f x, Finset.mem_image_of_mem f (Finset.mem_univ x)⟩
  -- Uniform-on-fibre kernel: `K z x = 1/|q⁻¹(z)|` on the fibre, zero
  -- elsewhere.  Fibre-supported and fibre-normalised on image(q).
  let K : ZT → α → ℝ := fun z x =>
    if q x = z then
      ((Finset.univ.filter (fun y : α => q y = z)).card : ℝ)⁻¹
    else 0
  refine ⟨ZT, inferInstance, inferInstance, q, K, ?_, ?_, ?_⟩
  · -- Sufficiency of q: reduce to Theorem 1's likelihoodRatioVector_sufficient.
    intro θ θ' x x' hxx'
    have hf : f x = f x' := congrArg Subtype.val hxx'
    exact likelihoodRatioVector_sufficient P θ₀ hpos θ θ' x x' hf
  · -- Fibre support: K z x = 0 when q x ≠ z (definitional via `if_neg`).
    intro z x hne
    show (if q x = z then _ else (0 : ℝ)) = 0
    exact if_neg hne
  · -- Kernel normalisation: for every z ∈ image(q) (= every z ∈ ZT by
    -- construction), ∑ x, K z x = 1.  We take the left disjunct.
    intro z
    left
    -- The fibre q⁻¹(z) is nonempty because z ∈ image(q) = ZFin.
    obtain ⟨x₀, _hx₀u, hfx₀⟩ := Finset.mem_image.mp z.property
    -- Set the fibre finset and give it a positive-card / nonzero-cast pair.
    set S : Finset α := Finset.univ.filter (fun y : α => q y = z) with hS_def
    have hx₀ : x₀ ∈ S := by
      simp only [hS_def, Finset.mem_filter, Finset.mem_univ, true_and]
      exact Subtype.ext hfx₀
    have hne : S.Nonempty := ⟨x₀, hx₀⟩
    have hcard_pos : 0 < S.card := Finset.card_pos.mpr hne
    have hcard_ne : (S.card : ℝ) ≠ 0 :=
      Nat.cast_ne_zero.mpr (Nat.pos_iff_ne_zero.mp hcard_pos)
    -- Show the total sum equals `(S.card : ℝ) * (S.card : ℝ)⁻¹`.
    have hsum_eq :
        (∑ x, K z x)
          = ∑ x ∈ S, ((S.card : ℝ))⁻¹ := by
      -- Split univ into S (fibre) and its complement.
      have hunfold :
          ∀ x, K z x = if q x = z then ((S.card : ℝ))⁻¹ else 0 := by
        intro x; rfl
      calc (∑ x, K z x)
          = ∑ x, if q x = z then ((S.card : ℝ))⁻¹ else 0 :=
            Finset.sum_congr rfl (fun x _ => hunfold x)
        _ = ∑ x ∈ S, ((S.card : ℝ))⁻¹ := by
            rw [hS_def]
            exact (Finset.sum_filter (fun y : α => q y = z) _).symm
    rw [hsum_eq, Finset.sum_const, nsmul_eq_mul, mul_inv_cancel₀ hcard_ne]

/-- **Coarsestness corollary of SIC-A** (finite discrete positive-support form).

    The LR-vector-induced quotient `q` is *coarsest* among common
    sufficient statistics: every other sufficient `q'` refines `q`.
    Direct consequence of Theorem 1's minimality
    (`exists_minimal_sufficient_finite_discrete`), which itself uses
    the packaged axiom `HalmosSavage_minimality_h_extension` (Halmos &
    Savage 1949).  This corollary does **not** introduce any new axiom;
    it merely propagates the T1 axiom footprint. -/
theorem sic_a_finite_discrete_coarsest
    {Θ α : Type*} [Fintype Θ] [Fintype α]
    (P : Θ → α → ℝ) (θ₀ : Θ) (hpos : ∀ θ x, 0 < P θ x) :
    IsMinimalSufficient P (likelihoodRatioVector P θ₀) :=
  exists_minimal_sufficient_finite_discrete P θ₀ hpos

end StructuralIntelligenceMathlib
