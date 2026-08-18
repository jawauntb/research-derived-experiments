import StructuralIntelligence.EmlZeroIdentity

/-!
# Structural Intelligence — EML Catalan censuses and the size-2 split (Wave 7)

Kernel-checks the three finite headlines of the EML spectrum
instruments (`experiments/eml_fiber_spectrum`,
`experiments/eml_variable_spectrum`):

* **EML-fib-Ck.**  The constant grammar `S → 1 | eml(S,S)` has exactly
  Catalan `C_k` trees with `k` internal nodes, for `k = 0..6`; the
  registered census bound holds `197` trees in total.
* **EML-var-Ck.**  The variable grammar `S → 1 | x | eml(S,S)` has
  exactly `2^(k+1) · C_k` trees with `k` internal nodes, for
  `k = 0..5` (`2, 4, 16, 80, 448, 2688`); `3238` trees in total.
* **EML-pair-diff.**  The two size-2 constant trees
  `eml(1, eml(1,1))` and `eml(eml(1,1), 1)` are distinct terms whose
  denotations derive, in any `ExpLn` carrier, to `exp(1) − 1` and
  `exp(exp(1))` respectively; the registered discrete model
  (`Nat` with `exp = succ`, `ln = pred`, truncated `sub`) separates
  them (`1 ≠ 3`).  Size is therefore not a denotation invariant:
  the fragment laws do not identify same-size trees.

Honesty.  The censuses are exhaustive enumeration facts at the
registered bounds and nothing more.  The pair split is symbolic: it
shows the `ExpLn` laws admit a model separating the two size-2
denotations, matching the paper's exact algebra `e−1` vs `e^e`.  The
real-number reading (`ℝ` with the usual `exp`/`ln`) is the intended
model and is *not* constructed here — no `Mathlib`, no `Real`.  The
numerical fiber statistics of the Python instruments (rounding grids,
Gibbs masses, cross-size collisions) stay Python; none are restated
here.

### Mathematical claim card

* Objects.  `CTree` (leaf `one`, binary `eml`); `VTree` (leaves
  `one`, `x`, binary `eml`); cumulative shells `shell n` / `vshell n`
  enumerating all trees with `≤ n` internal nodes;
  `catalan n = (2n choose n) / (n+1)`; the `ExpLn` fragment and its
  `Nat` model.
* Claims.  Census lists equal their closed-form lists (kernel
  `decide`); the size-2 pair is distinct, equal-size, and separated
  by the registered model; its two denotations rewrite to
  `sub (exp one) one` and `exp (exp one)` in any carrier.
* Assumptions.  None beyond the `ExpLn` class fields (explicit
  hypotheses, not environment axioms).
* Edge / null.  `ln` is applied only to `exp`-images or to `one` on
  the symbolic path; the `Nat` model totalizes `ln 0 = 0`, which the
  fragment laws never inspect.
-/

set_option maxRecDepth 4000000
set_option maxHeartbeats 16000000

namespace StructuralIntelligence
namespace EmlCatalan

/-- Constant grammar `S → 1 | eml(S,S)`: full binary trees, every
    leaf the constant `1`. -/
inductive CTree where
  | one
  | eml (a b : CTree)
deriving DecidableEq, Repr

/-- Internal-node count (`eml` nodes). -/
def internal : CTree → Nat
  | .one => 0
  | .eml a b => 1 + internal a + internal b

/-- All constant trees with at most `n` internal nodes, built as
    cumulative shells: step `n+1` adds exactly the trees
    `eml(a, b)` with `internal a + internal b = n`, each of which is
    new (its internal count is `n+1`) and appears once (a tree
    determines its children). -/
def shell : Nat → List CTree
  | 0 => [.one]
  | n + 1 =>
    let s := shell n
    s ++ s.flatMap (fun a =>
      let ia := internal a
      (s.filter (fun b => ia + internal b = n)).map (CTree.eml a))

/-- Binomial coefficient by the Pascal recurrence — structural, so
    kernel `decide` can unfold it (`Nat.choose` is not
    kernel-reducible in this toolchain). -/
def binom : Nat → Nat → Nat
  | _, 0 => 1
  | 0, _ + 1 => 0
  | n + 1, k + 1 => binom n k + binom n (k + 1)

/-- Catalan number, closed form `C_n = (2n choose n) / (n+1)`. -/
def catalan (n : Nat) : Nat := binom (2 * n) n / (n + 1)

/-- Census of the registered constant bound: trees with exactly `k`
    internal nodes inside `shell 6`, for `k = 0..6`.  The `let`
    shares one enumeration across all seven counts. -/
def census : List Nat :=
  let s := shell 6
  [0, 1, 2, 3, 4, 5, 6].map (fun k =>
    (s.filter (fun t => internal t = k)).length)

/-- **EML-fib-Ck.**  The constant-grammar shell counts are the first
    seven Catalan numbers. -/
theorem emlFib_counts :
    census = [0, 1, 2, 3, 4, 5, 6].map catalan := by decide

/-- The Catalan values behind `emlFib_counts`, pinned explicitly. -/
theorem catalan_values :
    [0, 1, 2, 3, 4, 5, 6].map catalan = [1, 1, 2, 5, 14, 42, 132] := by
  decide

/-- The registered constant census holds `197 = 1+1+2+5+14+42+132`
    trees in total. -/
theorem emlFib_total : (shell 6).length = 197 := by decide

/-- Variable grammar `S → 1 | x | eml(S,S)`: leaves carry one of two
    labels. -/
inductive VTree where
  | one
  | x
  | eml (a b : VTree)
deriving DecidableEq, Repr

/-- Internal-node count for the variable grammar. -/
def vinternal : VTree → Nat
  | .one => 0
  | .x => 0
  | .eml a b => 1 + vinternal a + vinternal b

/-- Cumulative shells for the variable grammar. -/
def vshell : Nat → List VTree
  | 0 => [.one, .x]
  | n + 1 =>
    let s := vshell n
    s ++ s.flatMap (fun a =>
      let ia := vinternal a
      (s.filter (fun b => ia + vinternal b = n)).map (VTree.eml a))

/-- Increment bucket `k` of a count vector. -/
def bump (v : List Nat) (k : Nat) : List Nat :=
  v.set k (v.getD k 0 + 1)

/-- Single-pass size histogram of a variable-tree list over buckets
    `0..bound`.  One fold, one traversal — the enumeration is
    evaluated exactly once, which keeps kernel `decide` tractable at
    the 3238-tree bound. -/
def vbuckets (bound : Nat) (l : List VTree) : List Nat :=
  l.foldl (fun acc t => bump acc (vinternal t)) (List.replicate (bound + 1) 0)

/-- **EML-var-Ck.**  The variable-grammar census at the registered
    bound: exactly `2, 4, 16, 80, 448, 2688` trees with
    `k = 0..5` internal nodes. -/
theorem emlVar_counts :
    vbuckets 5 (vshell 5) = [2, 4, 16, 80, 448, 2688] := by decide

/-- The census values are `2^(k+1) · C_k` — the labeled-count formula
    of `experiments/eml_variable_spectrum`. -/
theorem emlVar_formula :
    [0, 1, 2, 3, 4, 5].map (fun k => 2 ^ (k + 1) * catalan k)
      = [2, 4, 16, 80, 448, 2688] := by decide

/-- The registered variable census holds
    `3238 = 2+4+16+80+448+2688` trees in total. -/
theorem emlVar_total : (vshell 5).length = 3238 := by decide

/-! ## The size-2 split, in symbolic form

The two constant trees with two internal nodes.  Their real closed
forms are `e − 1` and `e^e`; here they are separated inside the
`ExpLn` fragment of `EmlZeroIdentity`. -/

/-- `eml(1, eml(1,1))` — real closed form `e − 1`. -/
def leftTree : CTree := .eml .one (.eml .one .one)

/-- `eml(eml(1,1), 1)` — real closed form `e^e`. -/
def rightTree : CTree := .eml (.eml .one .one) .one

/-- The pair is distinct as terms and shares internal count 2. -/
theorem pair_same_size_distinct :
    internal leftTree = 2 ∧ internal rightTree = 2 ∧ leftTree ≠ rightTree := by
  decide

open EmlZeroIdentity in
/-- Denotation of a constant tree in any `ExpLn` carrier. -/
def den {α : Type} [ExpLn α] : CTree → α
  | .one => ExpLn.one
  | .eml a b => ExpLn.eml (den a) (den b)

section Symbolic

open EmlZeroIdentity ExpLn

variable {α : Type} [ExpLn α]

/-- The left size-2 tree denotes `exp(1) − 1` in any carrier:
    `eml(1, eml(1,1)) = exp(1) − ln(exp(1)) = exp(1) − 1`. -/
theorem left_denotes : (den leftTree : α) = sub (exp one) one := by
  show eml (one : α) (eml one one) = sub (exp one) one
  calc eml (one : α) (eml one one)
      = eml one (exp one) := by rw [eml_right_one]
    _ = sub (exp one) (ln (exp one)) := rfl
    _ = sub (exp one) one := by rw [ln_exp]

/-- The right size-2 tree denotes `exp(exp(1))` in any carrier:
    `eml(eml(1,1), 1) = exp(eml(1,1)) = exp(exp(1))`. -/
theorem right_denotes : (den rightTree : α) = exp (exp one) := by
  show eml (eml (one : α) one) one = exp (exp one)
  rw [eml_right_one, eml_right_one]

end Symbolic

open EmlZeroIdentity in
/-- Registered discrete model of the `ExpLn` fragment:
    `exp = succ`, `ln = pred`, truncated subtraction, `Pos n = 1 ≤ n`.
    Every field law holds; `ln 0 = 0` is never inspected by them. -/
instance natExpLn : ExpLn Nat where
  exp := Nat.succ
  ln := Nat.pred
  sub := Nat.sub
  zero := 0
  one := 1
  Pos := fun n => 1 ≤ n
  ln_exp := fun _ => rfl
  exp_ln := fun _ h => Nat.succ_pred_eq_of_pos h
  exp_zero := rfl
  exp_pos := fun n => Nat.succ_le_succ (Nat.zero_le n)
  sub_zero := fun _ => rfl
  sub_self := fun n => Nat.sub_self n

/-- **EML-pair-diff.**  Size is not a denotation invariant: the two
    size-2 trees have equal internal count and the registered model
    separates their denotations (`1 ≠ 3` under
    `exp = succ, ln = pred`). -/
theorem eml_pair_diff :
    internal leftTree = internal rightTree ∧
      (den leftTree : Nat) ≠ (den rightTree : Nat) := by
  decide

end EmlCatalan
end StructuralIntelligence
