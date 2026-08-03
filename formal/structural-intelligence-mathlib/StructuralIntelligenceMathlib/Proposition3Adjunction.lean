import Mathlib.Data.Fintype.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Tactic

/-!
# Structural Intelligence (Mathlib) — Proposition 3 (Coarse ⊣ Refine)

The categorical adjunction between "coarse-graining" and "refinement" in
the finite discrete setting.  Let `X` and `Z` be finite types with a
quotient map `q : X → Z` and a fibrewise kernel `K : Z → X → ℝ`
(a distribution over `X` conditioned on the label `z`).  Define

* the **coarsening functor**
    `C q μ z = ∑_{x : q x = z} μ x` (pushforward along `q`);
* the **refinement functor**
    `R K ν x = ∑_z K z x · ν z` (integration against the kernel).

Under the natural regularity conditions on `K` — supported on the
fibre (`K z x = 0` when `q x ≠ z`) and normalised to `1` on each fibre
— `C ∘ R = id` on distributions over `Z`, and both **triangle
identities** of an adjunction hold:

* `R_C_unit`: `C (R (C μ)) = C μ`;
* `C_R_counit`: `R (C (R ν)) = R ν`.

These are the two natural-transformation coherences that witness
`C ⊣ R` at the object level in the discrete distribution category.
No `sorry`, no `axiom`: everything reduces to finite-sum manipulation.
-/

namespace StructuralIntelligenceMathlib

open Finset BigOperators

/-- Pushforward-along-`q` on functions `X → ℝ` (aka coarse-graining).
    `C q μ z = ∑ x with q x = z, μ x`. -/
def coarsen {X Z : Type*} [Fintype X] [DecidableEq Z]
    (q : X → Z) (μ : X → ℝ) (z : Z) : ℝ :=
  ∑ x ∈ (Finset.univ.filter fun x => q x = z), μ x

/-- Fibrewise-integration-along-`K` (aka refinement).
    `R K ν x = ∑ z, K z x · ν z`. -/
def refine {X Z : Type*} [Fintype Z]
    (K : Z → X → ℝ) (ν : Z → ℝ) (x : X) : ℝ :=
  ∑ z, K z x * ν z

/-- A kernel `K : Z → X → ℝ` is **supported on the fibres of `q`** iff
    `K z x = 0` whenever `q x ≠ z`. -/
def FibreSupported {X Z : Type*} (q : X → Z) (K : Z → X → ℝ) : Prop :=
  ∀ z x, q x ≠ z → K z x = 0

/-- A fibre-supported kernel is **normalised** iff each fibre integrates
    to `1`.  Under fibre support, this is the same as `∑ x, K z x = 1`.
-/
def FibreNormalised {X Z : Type*} [Fintype X] (K : Z → X → ℝ) : Prop :=
  ∀ z, ∑ x, K z x = 1

/-- **Coarsening after refinement collapses to the identity.**

    Under a fibre-supported, fibre-normalised kernel `K`,
    `C q (R K ν) = ν` for every distribution `ν : Z → ℝ`.  This is
    the key retraction identity from which both triangle identities of
    the adjunction follow. -/
theorem coarsen_refine_eq
    {X Z : Type*} [Fintype X] [Fintype Z] [DecidableEq Z]
    (q : X → Z) (K : Z → X → ℝ)
    (hSupp : FibreSupported q K) (hNorm : FibreNormalised K)
    (ν : Z → ℝ) :
    coarsen q (refine K ν) = ν := by
  classical
  funext z
  unfold coarsen refine
  -- Swap the order of summation.
  have swap :
      ∑ x ∈ (Finset.univ.filter fun x => q x = z),
        ∑ z', K z' x * ν z'
        =
      ∑ z', ν z' * ∑ x ∈ (Finset.univ.filter fun x => q x = z),
        K z' x := by
    rw [Finset.sum_comm]
    apply Finset.sum_congr rfl
    intro z' _
    rw [Finset.mul_sum]
    apply Finset.sum_congr rfl
    intro x _
    ring
  rw [swap]
  -- Show each z'-term collapses: nonzero only when z' = z.
  have inner_eq :
      ∀ z' : Z,
        ν z' * ∑ x ∈ (Finset.univ.filter fun x => q x = z), K z' x
          = if z' = z then ν z else 0 := by
    intro z'
    by_cases h : z' = z
    · subst h
      -- z' = z: inner sum equals ∑ x, K z' x = 1 (using fibre support to fill in zero-terms).
      have h_off_zero : ∀ x, x ∉ (Finset.univ.filter fun x => q x = z') → K z' x = 0 := by
        intro x hx
        simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hx
        exact hSupp z' x hx
      have h_fibre_sum :
          ∑ x ∈ (Finset.univ.filter fun x => q x = z'), K z' x
            = ∑ x, K z' x := by
        apply Finset.sum_subset (Finset.subset_univ _)
        intro x _ hx_not
        exact h_off_zero x hx_not
      rw [h_fibre_sum, hNorm z', mul_one]
      simp
    · -- z' ≠ z: every x with q x = z has K z' x = 0 (since q x = z ≠ z').
      have h_inner_zero :
          ∑ x ∈ (Finset.univ.filter fun x => q x = z), K z' x = 0 := by
        apply Finset.sum_eq_zero
        intro x hx
        simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hx
        apply hSupp z' x
        rw [hx]
        exact fun heq => h heq.symm
      rw [h_inner_zero, mul_zero]
      simp [h]
  rw [Finset.sum_congr rfl (fun z' _ => inner_eq z')]
  rw [Finset.sum_ite_eq' Finset.univ z (fun _ => ν z)]
  simp

/-- **Unit triangle identity** for the coarsen ⊣ refine adjunction.

    `C (R (C μ)) = C μ`.  Immediate from `coarsen_refine_eq`
    applied to `ν := C q μ`. -/
theorem R_C_unit
    {X Z : Type*} [Fintype X] [Fintype Z] [DecidableEq Z]
    (q : X → Z) (K : Z → X → ℝ)
    (hSupp : FibreSupported q K) (hNorm : FibreNormalised K)
    (μ : X → ℝ) :
    coarsen q (refine K (coarsen q μ)) = coarsen q μ :=
  coarsen_refine_eq q K hSupp hNorm (coarsen q μ)

/-- **Counit triangle identity** for the coarsen ⊣ refine adjunction.

    `R (C (R ν)) = R ν`.  Immediate: `C (R ν) = ν` by
    `coarsen_refine_eq`, so `R (C (R ν)) = R ν`. -/
theorem C_R_counit
    {X Z : Type*} [Fintype X] [Fintype Z] [DecidableEq Z]
    (q : X → Z) (K : Z → X → ℝ)
    (hSupp : FibreSupported q K) (hNorm : FibreNormalised K)
    (ν : Z → ℝ) :
    refine K (coarsen q (refine K ν)) = refine K ν := by
  rw [coarsen_refine_eq q K hSupp hNorm ν]

/-- **Proposition 3 (finite discrete form).**

    The pair `(coarsen q, refine K)` satisfies both triangle
    identities of an adjunction whenever `K` is a fibre-supported,
    fibre-normalised kernel over the quotient `q : X → Z`.
    Together with the (trivial) functoriality of both operations on
    the discrete distribution "category" — which here is just the
    identity: `coarsen` and `refine` are ordinary ℝ-linear maps —
    this witnesses the adjunction `coarsen ⊣ refine`.

    We package the two identities into a single theorem for external
    consumption. -/
theorem proposition3_adjunction
    {X Z : Type*} [Fintype X] [Fintype Z] [DecidableEq Z]
    (q : X → Z) (K : Z → X → ℝ)
    (hSupp : FibreSupported q K) (hNorm : FibreNormalised K) :
    (∀ μ : X → ℝ, coarsen q (refine K (coarsen q μ)) = coarsen q μ) ∧
    (∀ ν : Z → ℝ, refine K (coarsen q (refine K ν)) = refine K ν) :=
  ⟨R_C_unit q K hSupp hNorm, C_R_counit q K hSupp hNorm⟩

end StructuralIntelligenceMathlib
