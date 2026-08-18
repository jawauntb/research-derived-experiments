import StructuralIntelligence.ConcernChoice

/-!
# Structural Intelligence — CONC-EST (Wave 8)

Honesty.  This file banks the kernel-decidable core of
`experiments/delete_repair_concern_estimation/`: on door 3's unchanged
menu and cost rule, registered frequency counting recovers the oracle
concern choice at the registered prefixes **1 / 2 / 6**, those steps
are minimal, and the misspecification gap is the recorded rational
**4** (sum-gap 8).  We cite `ConcernChoice.cost` / `pick` /
`candidates` and do **not** re-prove door 3, Theorem 4, or any Wave 2
headline.  No Mathlib.  No `native_decide`.  Kernel `decide` only.

The 24-row choice traces stay Python (quarantined by the 2026-08-18
receipt).  Nothing here is SGD, valence, a learned representation, or
a new master object.

Arithmetic.  Plug-in weights after `n` draws are empirical
frequencies `count(t)/n`.  Expected serving cost of a screen is
`Σ_t (count(t)/n) · cost(t, s)`.  The `n` cancels in the argmin, so
`pluginChoose` is door 3's `pick` on the **prefix sum** of serving
costs.  Half–half misspecification is the same scaling door 3 already
uses: expected costs 20 vs 16 become sum-costs 40 vs 32.

### Mathematical claim card

* Objects.  Door 3 `cost` / `pick` / `candidates`; three literal
  24-draw sequences `seqBag` / `seqMix` / `seqPair`; prefix argmin
  `pluginChoose`.
* Claims.  `seqBag` stays `q_perm` on every prefix (step 1);
  `seqMix` is `q_perm` at n = 1 and `q_stab0` from n = 2 (step 2);
  `seqPair` is `q_perm` at n = 5 and `q_id` from n = 6 (step 6);
  holding `q_stab0` under the `bag`/`pair_eq` oracle costs 8 more
  in the sum (expected gap 4).
* Assumptions.  Menu, cost, and tie-break are door 3's.  Sequences
  are the registered literals, not samples.
* Withheld.  The 3×24 choice traces; stochastic concentration;
  concern drift; anything off this menu.
-/

namespace StructuralIntelligence
namespace ConcernEst

open KappaScreen (ScreenId TaskId)
open ConcernChoice (cost pick candidates)

set_option maxRecDepth 4000000
set_option maxHeartbeats 16000000

/-! ## Registered sequences (24 draws, literal) -/

def interleave (n : Nat) (a b : TaskId) : List TaskId :=
  match n with
  | 0 => []
  | n + 1 => a :: b :: interleave n a b

def seqBag : List TaskId := List.replicate 24 TaskId.bag
def seqMix : List TaskId := interleave 12 TaskId.bag TaskId.first_bit
def seqPair : List TaskId := interleave 12 TaskId.bag TaskId.pair_eq

theorem seqBag_length : seqBag.length = 24 := by decide
theorem seqMix_length : seqMix.length = 24 := by decide
theorem seqPair_length : seqPair.length = 24 := by decide

/-! ## Plug-in choice = door 3 κ_concern of empirical frequencies -/

/-- Prefix-sum serving cost: `n` times the plug-in expected cost. -/
def pluginCost (seq : List TaskId) (n : Nat) (s : ScreenId) : Nat :=
  (seq.take n).foldl (fun acc t => acc + cost t s) 0

def pluginChoose (seq : List TaskId) (n : Nat) : Option ScreenId :=
  pick (pluginCost seq n) candidates

def prefixes24 : List Nat :=
  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
   13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]

def from2 : List Nat :=
  [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
   13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]

def from6 : List Nat :=
  [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]

/-! ## SEQ_BAG — oracle `q_perm`, registered step 1 -/

theorem bag_stays :
    ∀ n ∈ prefixes24, pluginChoose seqBag n = some ScreenId.q_perm := by
  decide

theorem bag_step_minimal :
    pluginChoose seqBag 1 = some ScreenId.q_perm := by
  decide

/-! ## SEQ_MIX — oracle `q_stab0`, registered step 2 -/

/-- n = 1 is δ_bag, so the plug-in still picks door 3's δ_bag screen. -/
theorem mix_before_step :
    pluginChoose seqMix 1 = some ScreenId.q_perm := by
  decide

theorem mix_stays :
    ∀ n ∈ from2, pluginChoose seqMix n = some ScreenId.q_stab0 := by
  decide

theorem mix_step_minimal :
    pluginChoose seqMix 1 ≠ some ScreenId.q_stab0 := by
  decide

/-! ## SEQ_PAIR — oracle `q_id`, registered step 6

Odd-prefix `pair_eq` frequency `k/(2k+1)` sits below door 3's
`11/27` boundary at n = 5 (`2/5`) and above it from n = 7 (`3/7`);
even prefixes sit at `1/2`.  The plug-in therefore locks at n = 6.
-/

theorem pair_before_step :
    pluginChoose seqPair 5 = some ScreenId.q_perm := by
  decide

theorem pair_stays :
    ∀ n ∈ from6, pluginChoose seqPair n = some ScreenId.q_id := by
  decide

theorem pair_step_minimal :
    pluginChoose seqPair 5 ≠ some ScreenId.q_id := by
  decide

/-! ## Misspecification: SEQ_MIX's screen under SEQ_PAIR's concern -/

/-- Expected costs 20 vs 16 (gap 4) are the half–half sums 40 vs 32. -/
theorem misspec_sum_gap :
    cost TaskId.bag ScreenId.q_stab0 + cost TaskId.pair_eq ScreenId.q_stab0 =
      cost TaskId.bag ScreenId.q_id + cost TaskId.pair_eq ScreenId.q_id + 8 := by
  decide

theorem misspec_expected_gap :
    (cost TaskId.bag ScreenId.q_stab0 + cost TaskId.pair_eq ScreenId.q_stab0) / 2 =
      (cost TaskId.bag ScreenId.q_id + cost TaskId.pair_eq ScreenId.q_id) / 2 + 4 := by
  decide

/-! ## Combined registered headline -/

/-- **CONC-EST.**  Frequency counting recovers the oracle choice at
    the registered minimal prefixes 1 / 2 / 6 and stays through
    n = 24; holding the wrong sequence's screen costs the recorded
    gap 4. -/
theorem conc_est_registered_steps :
    (∀ n ∈ prefixes24, pluginChoose seqBag n = some ScreenId.q_perm) ∧
    pluginChoose seqMix 1 = some ScreenId.q_perm ∧
    (∀ n ∈ from2, pluginChoose seqMix n = some ScreenId.q_stab0) ∧
    pluginChoose seqPair 5 = some ScreenId.q_perm ∧
    (∀ n ∈ from6, pluginChoose seqPair n = some ScreenId.q_id) ∧
    (cost TaskId.bag ScreenId.q_stab0 + cost TaskId.pair_eq ScreenId.q_stab0) / 2 =
      (cost TaskId.bag ScreenId.q_id + cost TaskId.pair_eq ScreenId.q_id) / 2 + 4 := by
  decide

#print axioms bag_stays
#print axioms mix_stays
#print axioms pair_stays
#print axioms misspec_expected_gap
#print axioms conc_est_registered_steps

end ConcernEst
end StructuralIntelligence
