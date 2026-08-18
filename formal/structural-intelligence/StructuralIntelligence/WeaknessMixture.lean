import StructuralIntelligence.WeaknessP1

/-!
# Structural Intelligence — WI overlapping-mixture prior (Wave 11)

Honesty.  Banks the *finite prior-mass* half of the WI PAC-Bayes
sketch (`papers/weakness_invariance_neurips/pac_bayes_weakness_sketch.md`),
on the same registered toy as `WeaknessP1`:

> For the overlapping mixture `P = ∑_k π_k U_k` with `U_k` uniform
> on `{h : W_G(h) ≥ k}`, exact mass `P(h)` is nondecreasing in
> `W_G(h)`, and the one-component certificate
> `P(h) ≥ π_k / |H_{≥k}|` holds whenever `k ≤ W_G(h)`.

The Langford–Seeger–Maurer PAC-Bayes-kl inequality is **not**
proved here.  Neither is OOD transport, a neural posterior, or a
data-dependent group.  Those stay WI-PB / prose.

Cites `WeaknessP1.weakness` on `{shortcut, invariant}`.  Does not
re-prove `coverage_increases`.

No Mathlib.  No `native_decide`.  Kernel `decide` only.

### Mathematical claim card

* Objects.  The Wave-9 toy, mixture weights `π_1 = π_2 = 1/2`,
  nested classes `H_{≥1} = {shortcut, invariant}` and
  `H_{≥2} = {invariant}`, prior mass in units of `1/4`.
* Claims.  Exact masses are `1/4` and `3/4`; mass increases with
  weakness; each registered certificate holds.
* Withheld.  PAC-Bayes-kl, misaligned `G`, continuous posteriors.
-/

namespace StructuralIntelligence
namespace WeaknessMixture

open WeaknessP1

set_option maxRecDepth 400000
set_option maxHeartbeats 2000000

/-- Nested class membership: `f` sits in `H_{≥ k}`. -/
def inGe (k : Nat) (f : Pt → Bool) : Bool :=
  decide (k ≤ weakness f)

/-- `|H_{≥ k}|` on the registered two-point class. -/
def cardGe : Nat → Nat
  | 1 => 2
  | 2 => 1
  | _ => 0

/-- One-component certificate `π_k / |H_{≥ k}|` in units of `1/4`.
    `π_1 = π_2 = 1/2`, so `k = 1` contributes `1` and `k = 2`
    contributes `2`. -/
def cert4 : Nat → Nat
  | 1 => 1
  | 2 => 2
  | _ => 0

/-- Exact mixture mass `P(f) = ∑_{k ≤ W(f)} π_k / |H_{≥ k}|`
    in units of `1/4`. -/
def mass4 (f : Pt → Bool) : Nat :=
  (if inGe 1 f then cert4 1 else 0) +
  (if inGe 2 f then cert4 2 else 0)

theorem shortcut_in_ge1 : inGe 1 shortcut = true := by decide
theorem shortcut_not_ge2 : inGe 2 shortcut = false := by decide
theorem invariant_in_ge1 : inGe 1 invariant = true := by decide
theorem invariant_in_ge2 : inGe 2 invariant = true := by decide

theorem card_ge1 : cardGe 1 = 2 := by decide
theorem card_ge2 : cardGe 2 = 1 := by decide

theorem shortcut_mass : mass4 shortcut = 1 := by decide
theorem invariant_mass : mass4 invariant = 3 := by decide

theorem cert_shortcut_k1 : cert4 1 ≤ mass4 shortcut := by decide
theorem cert_invariant_k1 : cert4 1 ≤ mass4 invariant := by decide
theorem cert_invariant_k2 : cert4 2 ≤ mass4 invariant := by decide

/-- **Overlapping-mixture prior mass increases with weakness.**

    On the registered class `{shortcut, invariant}` with equal
    mixture weights, the weaker candidate gets strictly more prior
    mass.  This is designed into `P`; it is not independent evidence
    that weakness is simple.  Not PAC-Bayes-kl. -/
theorem mixture_prior_mass_increases :
    weakness shortcut < weakness invariant ∧
    mass4 shortcut < mass4 invariant ∧
    cert4 1 ≤ mass4 shortcut ∧
    cert4 1 ≤ mass4 invariant ∧
    cert4 2 ≤ mass4 invariant := by
  decide

#print axioms mixture_prior_mass_increases
#print axioms shortcut_mass
#print axioms invariant_mass

end WeaknessMixture
end StructuralIntelligence
