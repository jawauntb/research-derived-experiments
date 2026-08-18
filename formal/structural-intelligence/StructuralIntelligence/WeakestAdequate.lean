/-!
# Structural Intelligence — D13 repaired: no largest adequate region (Wave 6)

Review item 1 on "Intention Is All You Need" v3: Definition D13 asks
for "the largest region whose compliant set stays within tolerance."
That object need not exist, and this file makes the failure a
kernel-checked fact rather than a referee's remark.

On the registered three-point world with values `0, 1, 2` and
tolerance `1`:

* `{a, b}` and `{b, c}` are both adequate (spread ≤ 1) and both
  maximal under inclusion (each breaks when the missing point joins);
* their union `{a, b, c}` is **not** adequate (spread 2);
* therefore **no largest adequate region exists** — nothing adequate
  contains every adequate region (`no_largest_adequate`, proved for
  arbitrary candidate regions, not by enumeration);
* maximality does not pin a unique object
  (`maximal_not_unique`);
* and the constructive repair is the program's own κ-lesson: a greedy
  completion is adequate and maximal (`greedy_repair_works`), but it
  is scan-order-dependent (`greedy_depends_on_order`) — so D13 is
  well-posed only with a **disclosed selection rule**, exactly as
  Paper F's κ_screen needed its named total order and exactly as the
  door-1 tie-break naturality failure warned.

Repair wording the essay should adopt: "a maximal adequate region
under a disclosed completion order," or an explicit optimization
criterion.  No Mathlib.  No `native_decide`.  Kernel `decide` plus
one general argument.
-/

namespace StructuralIntelligence
namespace WeakestAdequate

/-- The registered three-point world. -/
inductive X3 where
  | a
  | b
  | c
deriving DecidableEq, Repr

def univ3 : List X3 := [.a, .b, .c]

def value : X3 → Nat
  | .a => 0
  | .b => 1
  | .c => 2

/-- Adequacy of a region at tolerance `τ`: every pairwise value gap is
    at most `τ` (stated without subtraction: `u x ≤ u y + τ` both
    ways via the double quantifier). -/
def adequate (τ : Nat) (S : List X3) : Bool :=
  S.all fun x => S.all fun y => decide (value x ≤ value y + τ)

/-- Membership-preserving containment for regions-as-lists. -/
def subsetOf (S T : List X3) : Prop := ∀ x ∈ S, x ∈ T

/-- The two incomparable adequate regions. -/
theorem both_adequate :
    adequate 1 [.a, .b] = true ∧ adequate 1 [.b, .c] = true := by
  decide

/-- Their union is not adequate: the spread doubles. -/
theorem union_not_adequate : adequate 1 [.a, .b, .c] = false := by
  decide

/-- Each is maximal under inclusion: adjoining the missing point
    breaks adequacy. -/
theorem both_maximal :
    adequate 1 (.c :: [.a, .b]) = false ∧
      adequate 1 (.a :: [.b, .c]) = false := by
  decide

/-- **D13's "largest region" does not exist.**  No adequate region
    contains every adequate region: any candidate would contain both
    `a` (from `{a}`) and `c` (from `{c}`), and any region containing
    both violates the tolerance.  General over all candidate lists —
    this is not an enumeration. -/
theorem no_largest_adequate :
    ¬ ∃ S : List X3, adequate 1 S = true ∧
      ∀ T : List X3, adequate 1 T = true → subsetOf T S := by
  intro h
  obtain ⟨S, hS, hall⟩ := h
  have ha : X3.a ∈ S := by
    have h1 := hall [X3.a] (by decide)
    exact h1 X3.a (by simp)
  have hc : X3.c ∈ S := by
    have h1 := hall [X3.c] (by decide)
    exact h1 X3.c (by simp)
  have hpair := List.all_eq_true.mp hS X3.c hc
  have hgap := List.all_eq_true.mp hpair X3.a ha
  exact absurd (of_decide_eq_true hgap) (by decide)

/-- Maximal-under-inclusion is not unique: two distinct maximal
    adequate regions exist. -/
theorem maximal_not_unique :
    adequate 1 [.a, .b] = true ∧ adequate 1 [.b, .c] = true ∧
      adequate 1 (.c :: [.a, .b]) = false ∧
      adequate 1 (.a :: [.b, .c]) = false ∧
      ([X3.a, X3.b] ≠ [X3.b, X3.c]) := by
  decide

/-- Greedy completion in a disclosed scan order: adjoin each point
    when adequacy survives. -/
def greedy (τ : Nat) (order : List X3) : List X3 :=
  order.foldl (fun acc x =>
    if adequate τ (x :: acc) then x :: acc else acc) []

/-- **The repair works**: greedy output under the registered order is
    adequate and maximal (no remaining point can join). -/
theorem greedy_repair_works :
    adequate 1 (greedy 1 univ3) = true ∧
      (univ3.all fun x =>
        decide (x ∈ greedy 1 univ3) ||
          !(adequate 1 (x :: greedy 1 univ3))) = true := by
  decide

/-- **And the repair needs its disclosed order**: two scan orders,
    two different maximal regions.  Selection without a named rule is
    not a function — the κ_screen lesson, transported to D13. -/
theorem greedy_depends_on_order :
    greedy 1 [X3.a, X3.b, X3.c] ≠ greedy 1 [X3.c, X3.b, X3.a] := by
  decide

#print axioms no_largest_adequate
#print axioms maximal_not_unique
#print axioms greedy_repair_works
#print axioms greedy_depends_on_order

end WeakestAdequate
end StructuralIntelligence
