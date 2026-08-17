/-!
# Structural Intelligence — squaring-basis separation (US-2 / US-3 core)

Finite combinatorics behind the four-seam separation in
*EML as a Universal Substrate*
(`papers/eml_universal_substrate/paper.md`, §3–§4).

The analytic Gibbs masses and Catalan generating functions live in the
Python instrument ``experiments/squaring_separation``.  This file
isolates the **zero-analysis** kernel:

* a `MulTree` is a full binary tree (`x` or `×`);
* a `SqTree` adds a unary `sq` node, the definable macro `y ↦ y × y`;
* degree is leaf-count after expanding `sq`;
* every `MulTree` of degree `2^n` has node-count `2^{n+1} − 1`;
* the tower `sq^n(x)` has degree `2^n` and size `n+1`;
* a sharing circuit of `k` mul/sq steps has max degree `≤ 2^k`, so
  degree `2^n` needs `n` steps, and repeated squaring achieves `n`.

No branch cuts, no `Complex.log`, no new axioms.  Structural induction
on finite trees and lists.
-/

namespace StructuralIntelligence
namespace Compiler
namespace SquaringSeparation

theorem two_mul_pow (n : Nat) : 2 * 2 ^ n = 2 ^ (n + 1) := by
  rw [Nat.pow_succ, Nat.mul_comm (2 ^ n)]

theorem two_pow_add (n : Nat) : 2 ^ n + 2 ^ n = 2 ^ (n + 1) := by
  rw [← Nat.two_mul, two_mul_pow]

/-! ## Multiplication trees -/

inductive MulTree where
  | leaf : MulTree
  | mul : MulTree → MulTree → MulTree
  deriving Repr, DecidableEq, Inhabited

namespace MulTree

def size : MulTree → Nat
  | leaf => 1
  | mul l r => l.size + r.size + 1

def degree : MulTree → Nat
  | leaf => 1
  | mul l r => l.degree + r.degree

theorem degree_pos : ∀ t : MulTree, 1 ≤ t.degree
  | leaf => Nat.le_refl 1
  | mul l r => Nat.le_trans (degree_pos l) (Nat.le_add_right l.degree r.degree)

/-- Node count and leaf count are tied: `size + 1 = 2 * degree`. -/
theorem size_succ_eq_two_mul_degree : ∀ t : MulTree, t.size + 1 = 2 * t.degree
  | leaf => by simp [size, degree]
  | mul l r => by
      have hl := size_succ_eq_two_mul_degree l
      have hr := size_succ_eq_two_mul_degree r
      simp [size, degree]
      omega

theorem size_of_pow2_degree (n : Nat) (t : MulTree)
    (h : t.degree = 2 ^ n) : t.size + 1 = 2 ^ (n + 1) := by
  have ht := size_succ_eq_two_mul_degree t
  rw [h] at ht
  exact ht.trans (two_mul_pow n)

def pow2Tree : Nat → MulTree
  | 0 => leaf
  | n + 1 => mul (pow2Tree n) (pow2Tree n)

theorem pow2Tree_degree : ∀ n : Nat, (pow2Tree n).degree = 2 ^ n
  | 0 => rfl
  | n + 1 => by
      simp [pow2Tree, degree, pow2Tree_degree n]
      exact two_pow_add n

theorem pow2Tree_size (n : Nat) : (pow2Tree n).size + 1 = 2 ^ (n + 1) :=
  size_of_pow2_degree n (pow2Tree n) (pow2Tree_degree n)

end MulTree

/-! ## Squaring-extended trees -/

inductive SqTree where
  | leaf : SqTree
  | mul : SqTree → SqTree → SqTree
  | sq : SqTree → SqTree
  deriving Repr, DecidableEq, Inhabited

namespace SqTree

def size : SqTree → Nat
  | leaf => 1
  | mul l r => l.size + r.size + 1
  | sq t => t.size + 1

def degree : SqTree → Nat
  | leaf => 1
  | mul l r => l.degree + r.degree
  | sq t => t.degree + t.degree

def sqTower : Nat → SqTree
  | 0 => leaf
  | n + 1 => sq (sqTower n)

theorem sqTower_size : ∀ n : Nat, (sqTower n).size = n + 1
  | 0 => rfl
  | n + 1 => by
      simp [sqTower, size, sqTower_size n]

theorem sqTower_degree : ∀ n : Nat, (sqTower n).degree = 2 ^ n
  | 0 => rfl
  | n + 1 => by
      simp [sqTower, degree, sqTower_degree n]
      exact two_pow_add n

/-- Expanding the definable macro `sq(t) = t × t` recovers a mul-tree. -/
def expand : SqTree → MulTree
  | leaf => MulTree.leaf
  | mul l r => MulTree.mul (expand l) (expand r)
  | sq t => MulTree.mul (expand t) (expand t)

theorem expand_degree : ∀ t : SqTree, (expand t).degree = t.degree
  | leaf => rfl
  | mul l r => by
      simp [expand, MulTree.degree, degree, expand_degree l, expand_degree r]
  | sq t => by
      simp [expand, MulTree.degree, degree, expand_degree t]

/-- A sq-tree is never larger than its expanded mul-tree. -/
theorem size_le_expand_size : ∀ t : SqTree, t.size ≤ (expand t).size
  | leaf => Nat.le_refl _
  | mul l r => by
      simp [size, expand, MulTree.size]
      exact Nat.add_le_add (size_le_expand_size l) (size_le_expand_size r)
  | sq t => by
      have h := size_le_expand_size t
      -- `simp` would cancel the trailing `+ 1` and leave a mismatched goal.
      simp only [size, expand, MulTree.size]
      omega

end SqTree

/-! ## Sharing circuits -/

inductive CircStep where
  | mul (i j : Nat)
  | sq (i : Nat)
  deriving Repr, DecidableEq

def applyStep (ds : List Nat) : CircStep → Nat
  | CircStep.mul i j => ds.getD i 0 + ds.getD j 0
  | CircStep.sq i => ds.getD i 0 * 2

def listMax : List Nat → Nat
  | [] => 0
  | x :: xs => Nat.max x (listMax xs)

theorem getD_le_listMax : ∀ (ds : List Nat) (i : Nat), ds.getD i 0 ≤ listMax ds
  | [], i => by
      simp [listMax]
  | x :: xs, 0 => by
      simp [listMax]
      exact Nat.le_max_left x (listMax xs)
  | x :: xs, i + 1 => by
      have ih := getD_le_listMax xs i
      have hget : (x :: xs).getD (i + 1) 0 = xs.getD i 0 := by
        simp
      rw [hget]
      exact Nat.le_trans ih (Nat.le_max_right x (listMax xs))

theorem applyStep_le_two_max (ds : List Nat) (s : CircStep) :
    applyStep ds s ≤ 2 * listMax ds := by
  cases s with
  | mul i j =>
      have hi := getD_le_listMax ds i
      have hj := getD_le_listMax ds j
      simp [applyStep]
      have hsum : ds.getD i 0 + ds.getD j 0 ≤ listMax ds + listMax ds :=
        Nat.add_le_add hi hj
      have htwo : listMax ds + listMax ds = 2 * listMax ds := (Nat.two_mul _).symm
      exact htwo ▸ hsum
  | sq i =>
      have hi := getD_le_listMax ds i
      simp [applyStep]
      have hmul : ds.getD i 0 * 2 ≤ listMax ds * 2 :=
        Nat.mul_le_mul_right 2 hi
      have hcomm : listMax ds * 2 = 2 * listMax ds := Nat.mul_comm _ _
      exact hcomm ▸ hmul

theorem listMax_append_singleton :
    ∀ (ds : List Nat) (x : Nat), listMax (ds ++ [x]) = Nat.max (listMax ds) x
  | [], x => by
      simp [listMax]
  | y :: ys, x => by
      have ih := listMax_append_singleton ys x
      simp [listMax, ih, Nat.max_assoc]

theorem listMax_append_le_two (ds : List Nat) (x : Nat)
    (hx : x ≤ 2 * listMax ds) :
    listMax (ds ++ [x]) ≤ 2 * listMax ds := by
  rw [listMax_append_singleton]
  have hself : listMax ds ≤ 2 * listMax ds :=
    Nat.le_mul_of_pos_left (listMax ds) (by decide : (0 : Nat) < 2)
  exact Nat.max_le.mpr ⟨hself, hx⟩

def degreesFrom (ds : List Nat) : List CircStep → List Nat
  | [] => ds
  | s :: rest => degreesFrom (ds ++ [applyStep ds s]) rest

def circuitDegrees (steps : List CircStep) : List Nat :=
  degreesFrom [1] steps

def circuitMaxDegree (steps : List CircStep) : Nat :=
  listMax (circuitDegrees steps)

theorem degreesFrom_max_le (ds : List Nat) :
    ∀ steps : List CircStep,
      listMax (degreesFrom ds steps) ≤ listMax ds * 2 ^ steps.length
  | [] => by
      simp [degreesFrom]
  | s :: rest => by
      have hnew : applyStep ds s ≤ 2 * listMax ds := applyStep_le_two_max ds s
      have hmax : listMax (ds ++ [applyStep ds s]) ≤ 2 * listMax ds :=
        listMax_append_le_two ds _ hnew
      have ih := degreesFrom_max_le (ds ++ [applyStep ds s]) rest
      simp [degreesFrom]
      have h1 :
          listMax (degreesFrom (ds ++ [applyStep ds s]) rest)
            ≤ listMax (ds ++ [applyStep ds s]) * 2 ^ rest.length := ih
      have h2 :
          listMax (ds ++ [applyStep ds s]) * 2 ^ rest.length
            ≤ (2 * listMax ds) * 2 ^ rest.length :=
        Nat.mul_le_mul_right (2 ^ rest.length) hmax
      have h3 : (2 * listMax ds) * 2 ^ rest.length
          = listMax ds * 2 ^ (rest.length + 1) := by
        rw [Nat.pow_succ, Nat.mul_comm (2 ^ rest.length) 2]
        ac_rfl
      exact Nat.le_trans (Nat.le_trans h1 h2) (Nat.le_of_eq h3)

theorem listMax_singleton_one : listMax [1] = 1 := rfl

theorem circuitMaxDegree_le_pow2 (steps : List CircStep) :
    circuitMaxDegree steps ≤ 2 ^ steps.length := by
  have h := degreesFrom_max_le [1] steps
  simpa [circuitMaxDegree, circuitDegrees, listMax_singleton_one] using h

theorem pow2_le_pow2_imp_le {n m : Nat} (h : 2 ^ n ≤ 2 ^ m) : n ≤ m :=
  (Nat.pow_le_pow_iff_right (by decide : (1 : Nat) < 2)).mp h

theorem circuit_pow2_needs_n_steps (steps : List CircStep) (n : Nat)
    (h : 2 ^ n ≤ circuitMaxDegree steps) : n ≤ steps.length :=
  pow2_le_pow2_imp_le (Nat.le_trans h (circuitMaxDegree_le_pow2 steps))

def repeatedSquaring : Nat → List CircStep
  | 0 => []
  | n + 1 => repeatedSquaring n ++ [CircStep.sq n]

theorem repeatedSquaring_length : ∀ n : Nat, (repeatedSquaring n).length = n
  | 0 => rfl
  | n + 1 => by
      simp [repeatedSquaring, repeatedSquaring_length n]

theorem degreesFrom_length (ds : List Nat) :
    ∀ steps : List CircStep,
      (degreesFrom ds steps).length = ds.length + steps.length
  | [] => by simp [degreesFrom]
  | s :: rest => by
      have ih := degreesFrom_length (ds ++ [applyStep ds s]) rest
      have hds : (ds ++ [applyStep ds s]).length = ds.length + 1 := by simp
      simp [degreesFrom]
      rw [ih, hds]
      omega

theorem degreesFrom_append (ds : List Nat) :
    ∀ xs ys : List CircStep,
      degreesFrom ds (xs ++ ys) = degreesFrom (degreesFrom ds xs) ys
  | [], ys => by simp [degreesFrom]
  | s :: xs, ys => by
      simp [degreesFrom]
      exact degreesFrom_append (ds ++ [applyStep ds s]) xs ys

theorem circuitDegrees_append (xs ys : List CircStep) :
    circuitDegrees (xs ++ ys) = degreesFrom (circuitDegrees xs) ys :=
  degreesFrom_append [1] xs ys

theorem repeatedSquaring_reaches :
    ∀ n : Nat, (circuitDegrees (repeatedSquaring n)).getD n 0 = 2 ^ n
  | 0 => by
      simp [circuitDegrees, degreesFrom, repeatedSquaring]
  | n + 1 => by
      have ih := repeatedSquaring_reaches n
      have hlen : (circuitDegrees (repeatedSquaring n)).length = n + 1 := by
        simp [circuitDegrees, degreesFrom_length, repeatedSquaring_length]
        omega
      have hnew :
          applyStep (circuitDegrees (repeatedSquaring n)) (CircStep.sq n)
            = 2 ^ (n + 1) := by
        simp [applyStep]
        have ih' :
            (circuitDegrees (repeatedSquaring n))[n]?.getD 0 = 2 ^ n := by
          simpa using ih
        rw [ih', Nat.mul_comm, two_mul_pow]
      simp [repeatedSquaring, circuitDegrees_append]
      have hdeg :
          degreesFrom (circuitDegrees (repeatedSquaring n)) [CircStep.sq n]
            = circuitDegrees (repeatedSquaring n)
              ++ [applyStep (circuitDegrees (repeatedSquaring n)) (CircStep.sq n)] :=
        rfl
      rw [hdeg]
      have hget :
          (circuitDegrees (repeatedSquaring n)
              ++ [applyStep (circuitDegrees (repeatedSquaring n))
                (CircStep.sq n)])[n + 1]?.getD 0
            = applyStep (circuitDegrees (repeatedSquaring n)) (CircStep.sq n) := by
        calc
          (circuitDegrees (repeatedSquaring n)
              ++ [applyStep (circuitDegrees (repeatedSquaring n))
                (CircStep.sq n)])[n + 1]?.getD 0
              = (circuitDegrees (repeatedSquaring n)
                  ++ [applyStep (circuitDegrees (repeatedSquaring n))
                    (CircStep.sq n)])[(circuitDegrees (repeatedSquaring n)).length]?.getD 0 := by
                rw [hlen]
          _ = (some (applyStep (circuitDegrees (repeatedSquaring n))
                (CircStep.sq n))).getD 0 := by
                rw [List.getElem?_concat_length]
          _ = applyStep (circuitDegrees (repeatedSquaring n)) (CircStep.sq n) :=
                rfl
      rw [hget, hnew]

/-! ## Headlines -/

/-- Tree-size seam: same degree `2^n`, Mul size `2^{n+1}-1`, Sq size `n+1`. -/
theorem tree_size_separation (n : Nat) :
    (MulTree.pow2Tree n).degree = 2 ^ n ∧
    (SqTree.sqTower n).degree = 2 ^ n ∧
    (MulTree.pow2Tree n).size + 1 = 2 ^ (n + 1) ∧
    (SqTree.sqTower n).size = n + 1 :=
  ⟨MulTree.pow2Tree_degree n, SqTree.sqTower_degree n,
    MulTree.pow2Tree_size n, SqTree.sqTower_size n⟩

/-- Circuit-size seam: `n` sharing steps suffice and are necessary. -/
theorem circuit_size_of_pow2 (n : Nat) :
    (repeatedSquaring n).length = n ∧
    (circuitDegrees (repeatedSquaring n)).getD n 0 = 2 ^ n ∧
    ∀ steps : List CircStep,
      2 ^ n ≤ circuitMaxDegree steps → n ≤ steps.length :=
  ⟨repeatedSquaring_length n, repeatedSquaring_reaches n,
    fun steps => circuit_pow2_needs_n_steps steps n⟩

/-- Conservative extension of denotations: expanding `sq` preserves degree. -/
theorem conservative_extension (t : SqTree) :
    (SqTree.expand t).degree = t.degree :=
  SqTree.expand_degree t

/-- Combined kernel-checked headline for Lea. -/
theorem squaring_separation (n : Nat) :
    (MulTree.pow2Tree n).degree = 2 ^ n ∧
    (SqTree.sqTower n).degree = 2 ^ n ∧
    (MulTree.pow2Tree n).size + 1 = 2 ^ (n + 1) ∧
    (SqTree.sqTower n).size = n + 1 ∧
    (SqTree.expand (SqTree.sqTower n)).degree = 2 ^ n ∧
    (repeatedSquaring n).length = n ∧
    (circuitDegrees (repeatedSquaring n)).getD n 0 = 2 ^ n :=
  ⟨MulTree.pow2Tree_degree n, SqTree.sqTower_degree n,
    MulTree.pow2Tree_size n, SqTree.sqTower_size n,
    (SqTree.expand_degree (SqTree.sqTower n)).trans (SqTree.sqTower_degree n),
    repeatedSquaring_length n, repeatedSquaring_reaches n⟩

end SquaringSeparation
end Compiler
end StructuralIntelligence
