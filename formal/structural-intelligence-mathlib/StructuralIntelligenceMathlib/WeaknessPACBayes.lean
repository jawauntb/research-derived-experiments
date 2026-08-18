import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Tactic

/-!
# Structural Intelligence (Mathlib) — WI PAC-Bayes certificate (Wave 12)

Honesty.  This file proves the *compatibility-indexed KL certificate*
from `papers/weakness_invariance_neurips/pac_bayes_weakness_sketch.md`:

    KL(δ_h ‖ P) = −log P(h) ≤ log |H_{≥k}| − log π_k

whenever `k ≤ W(h)` and the overlapping mixture
`P = ∑_k π_k U_k` puts positive weight `π_k` on the uniform
`U_k` over `{h : k ≤ W(h)}`.

The Langford–Seeger–Maurer PAC-Bayes-kl inequality is **cited, not
proved**:

    kl(L̂_S(Q) ‖ L_D(Q)) ≤ (KL(Q‖P) + log(2√m / δ)) / m

(Langford & Seeger 2001; Seeger 2002; Maurer 2004).  `lsm_plug_certificate`
only says that *if* those real numbers satisfy LSM, the certificate
substitutes.  That is not a proof of LSM, not an OOD transport
theorem, and not a neural PAC-Bayes bound.

The finite prior-mass toy (`1/4` vs `3/4`) lives in the mathlib-free
`WeaknessMixture.lean` and is not re-proved here.

Cited: J. Langford & M. Seeger, *Bounds for Averaging Classifiers*,
CMU-CS-01-102 (2001); M. Seeger, *JMLR* 3:233–269 (2002);
A. Maurer, *A Note on the PAC Bayesian Theorem*, arXiv:cs/0411099
(2004).
-/

namespace StructuralIntelligenceMathlib

open Finset Real

variable {n : ℕ}

/-- Nested class `{h : k ≤ W h}`. -/
def Hge (W : Fin n → ℕ) (k : ℕ) : Finset (Fin n) :=
  Finset.univ.filter (fun h => k ≤ W h)

/-- Overlapping-mixture mass
    `P(h) = ∑_{k ≤ W(h)} π_k / |H_{≥k}|`,
    with a zero junk term when the class is empty. -/
noncomputable def mixtureMass (W : Fin n → ℕ) (prior : ℕ → ℝ) (h : Fin n) : ℝ :=
  ∑ k ∈ Finset.range (W h + 1),
    if Hge W k = ∅ then 0 else prior k / (Hge W k).card

/-- Dirac–prior KL in nats: `KL(δ_h ‖ P) = −log P(h)`. -/
noncomputable def klDirac (p : ℝ) : ℝ :=
  -Real.log p

lemma mem_Hge_of_le {W : Fin n → ℕ} {h : Fin n} {k : ℕ}
    (hk : k ≤ W h) : h ∈ Hge W k :=
  Finset.mem_filter.mpr ⟨Finset.mem_univ h, hk⟩

lemma Hge_nonempty_of_le {W : Fin n → ℕ} {h : Fin n} {k : ℕ}
    (hk : k ≤ W h) : (Hge W k).Nonempty :=
  ⟨h, mem_Hge_of_le hk⟩

lemma mixtureMass_ge_component
    {W : Fin n → ℕ} {prior : ℕ → ℝ} {h : Fin n} {k : ℕ}
    (hprior : ∀ j, 0 ≤ prior j) (hk : k ≤ W h) :
    prior k / (Hge W k).card ≤ mixtureMass W prior h := by
  classical
  have hkR : k ∈ Finset.range (W h + 1) :=
    Finset.mem_range.mpr (Nat.lt_succ_of_le hk)
  have hne : Hge W k ≠ ∅ :=
    Finset.nonempty_iff_ne_empty.mp (Hge_nonempty_of_le hk)
  have hterm :
      (fun j => if Hge W j = ∅ then 0 else prior j / (Hge W j).card) k
        = prior k / (Hge W k).card := by
    simp [hne]
  have hnn : ∀ j ∈ Finset.range (W h + 1),
      0 ≤ (if Hge W j = ∅ then (0 : ℝ) else prior j / (Hge W j).card) := by
    intro j _
    split_ifs
    · exact le_rfl
    · exact div_nonneg (hprior j) (Nat.cast_nonneg _)
  have := Finset.single_le_sum (s := Finset.range (W h + 1))
    (f := fun j => if Hge W j = ∅ then (0 : ℝ) else prior j / (Hge W j).card)
    hnn hkR
  simpa [mixtureMass, hterm] using this

/-- **Compatibility-indexed KL certificate.**

    For a deterministic posterior `δ_h` and any `k ≤ W(h)` with
    `π_k > 0`,

        −log P(h) ≤ log |H_{≥k}| − log π_k.
-/
theorem weakness_kl_certificate
    {W : Fin n → ℕ} {prior : ℕ → ℝ} {h : Fin n} {k : ℕ}
    (hprior : ∀ j, 0 ≤ prior j) (hpriork : 0 < prior k) (hk : k ≤ W h) :
    klDirac (mixtureMass W prior h)
      ≤ Real.log ((Hge W k).card : ℝ) - Real.log (prior k) := by
  have hne := Hge_nonempty_of_le (W := W) (h := h) hk
  have hcardpos : (0 : ℝ) < (Hge W k).card := by
    exact_mod_cast (Finset.card_pos.mpr hne)
  have hcomp : 0 < prior k / (Hge W k).card := div_pos hpriork hcardpos
  have hge := mixtureMass_ge_component (W := W) (prior := prior) (h := h)
    hprior hk
  have hmasspos : 0 < mixtureMass W prior h := lt_of_lt_of_le hcomp hge
  have hlog : Real.log (prior k / (Hge W k).card)
      ≤ Real.log (mixtureMass W prior h) :=
    (Real.log_le_log_iff hcomp hmasspos).mpr hge
  unfold klDirac
  have hdiv : Real.log (prior k / (Hge W k).card)
      = Real.log (prior k) - Real.log ((Hge W k).card : ℝ) :=
    Real.log_div (ne_of_gt hpriork) (ne_of_gt hcardpos)
  linarith

/-- If Langford–Seeger–Maurer holds numerically at this
    `(klEmp, KL, m, extra)`, the certificate substitutes.
    This is not a proof of LSM. -/
theorem lsm_plug_certificate
    {klEmp KL cert extra m : ℝ}
    (hKL : KL ≤ cert) (_hex : 0 ≤ extra) (hm : 0 < m)
    (hLSM : klEmp ≤ (KL + extra) / m) :
    klEmp ≤ (cert + extra) / m := by
  have : (KL + extra) / m ≤ (cert + extra) / m := by gcongr
  exact le_trans hLSM this

/-- LSM extra term `log(2 √m / δ)` for `m > 0`, `δ ∈ (0,1)`.
    Defined so the citation has a Lean name; positivity is the
    only lemma. -/
noncomputable def lsmExtra (m δ : ℝ) : ℝ :=
  Real.log (2 * Real.sqrt m / δ)

lemma lsmExtra_nonneg {m δ : ℝ} (hm : 1 ≤ m) (hδ0 : 0 < δ) (hδ1 : δ ≤ 1) :
    0 ≤ lsmExtra m δ := by
  have hsqrt : (1 : ℝ) ≤ Real.sqrt m := by
    calc (1 : ℝ) = Real.sqrt 1 := (Real.sqrt_one).symm
      _ ≤ Real.sqrt m := Real.sqrt_le_sqrt hm
  have hfrac : (1 : ℝ) ≤ 2 * Real.sqrt m / δ := by
    rw [le_div_iff₀ hδ0]
    nlinarith [hδ1, hsqrt]
  exact Real.log_nonneg hfrac

/-- **WI certificate plugged into the LSM shape.**

    *If* the Langford–Seeger–Maurer numbers hold for this
    deterministic posterior, then

        klEmp ≤ (log |H_{≥k}| − log π_k + log(2√m/δ)) / m.

    The `hLSM` hypothesis *is* the citation; it is not discharged. -/
theorem weakness_lsm_bound
    {W : Fin n → ℕ} {prior : ℕ → ℝ} {h : Fin n} {k : ℕ}
    {klEmp m δ : ℝ}
    (hprior : ∀ j, 0 ≤ prior j) (hpriork : 0 < prior k) (hk : k ≤ W h)
    (hm : 1 ≤ m) (hδ0 : 0 < δ) (hδ1 : δ ≤ 1)
    (hLSM : klEmp ≤ (klDirac (mixtureMass W prior h) + lsmExtra m δ) / m) :
    klEmp
      ≤ (Real.log ((Hge W k).card : ℝ) - Real.log (prior k)
          + lsmExtra m δ) / m :=
  lsm_plug_certificate
    (weakness_kl_certificate (W := W) (prior := prior) (h := h)
      hprior hpriork hk)
    (lsmExtra_nonneg hm hδ0 hδ1)
    (lt_of_lt_of_le zero_lt_one hm)
    hLSM

end StructuralIntelligenceMathlib
