/-!
# Structural Intelligence — IDENT passive bound (Wave 9)

Honesty.  Banks the combinatorial core of IDENT's Theorem
(benchmark form) from `papers/ident/paper.md` §2.4:

> If two distinct live hypotheses induce the same passive record,
> no function of that record can name both of them.  Hence a
> duplicate-free live class of size `m ≥ 2` has worst-case
> passive accuracy at most `1/m`.

Active sufficiency (a one-step separator exists) is a generator
property and is not restated.  Model scores stay Python.
No Mathlib.  No `native_decide`.

### Mathematical claim card

* Objects.  Response `R : H → G → Out`, passive family `G0`,
  record `G0.map (R h)`, live pair or list.
* Claims.  Equal records + distinct hypotheses ⇒ no transcript
  map hits both; on a `Nodup` constant-record list the hit count
  is ≤ 1; registered two-hypothesis witness with a separator.
* Withheld.  Frontier eval, language wrap, multi-step search.
-/

namespace StructuralIntelligence
namespace IdentImpossibility

set_option maxRecDepth 400000
set_option maxHeartbeats 4000000

def record {H G Out : Type} (R : H → G → Out) (G0 : List G) (h : H) :
    List Out :=
  G0.map (fun g => R h g)

theorem record_eq_of_pointwise
    {H G Out : Type}
    (R : H → G → Out) (G0 : List G) (h1 h2 : H)
    (hs : ∀ g ∈ G0, R h1 g = R h2 g) :
    record R G0 h1 = record R G0 h2 := by
  induction G0 with
  | nil => rfl
  | cons g gs ih =>
    have hg : R h1 g = R h2 g := hs g List.mem_cons_self
    have hgs : ∀ g' ∈ gs, R h1 g' = R h2 g' :=
      fun g' hg' => hs g' (List.mem_cons_of_mem g hg')
    simpa [record, hg] using ih hgs

/-- **IDENT core.**  A map from the passive record cannot recover
    two distinct hypotheses that share that record. -/
theorem no_transcript_map_hits_both
    {H Rec : Type}
    (rec : H → Rec) (a b : H) (hab : a ≠ b) (hrec : rec a = rec b)
    (guess : Rec → H) :
    ¬ (guess (rec a) = a ∧ guess (rec b) = b) := by
  intro ⟨ha, hb⟩
  apply hab
  calc a
      = guess (rec a) := ha.symm
    _ = guess (rec b) := by rw [hrec]
    _ = b := hb

/-- Number of listed hypotheses a transcript map names correctly. -/
def hitCount {H Rec : Type} [DecidableEq H]
    (rec : H → Rec) (guess : Rec → H) : List H → Nat
  | [] => 0
  | h :: hs => (if guess (rec h) = h then 1 else 0) + hitCount rec guess hs

theorem hitCount_eq_zero_of_none
    {H Rec : Type} [DecidableEq H]
    (rec : H → Rec) (guess : Rec → H) (S : List H)
    (hnone : ∀ h ∈ S, guess (rec h) ≠ h) :
    hitCount rec guess S = 0 := by
  induction S with
  | nil => rfl
  | cons h0 hs ih =>
    have h0n : guess (rec h0) ≠ h0 := hnone h0 List.mem_cons_self
    have hsn : ∀ h ∈ hs, guess (rec h) ≠ h :=
      fun h hh => hnone h (List.mem_cons_of_mem h0 hh)
    simp [hitCount, h0n, ih hsn]

/-- On a duplicate-free list whose records agree, a transcript map
    is correct for at most one member.  Combined with `|S| = m ≥ 2`
    this is the `1/m` worst-case bound. -/
theorem hits_le_one
    {H Rec : Type} [DecidableEq H]
    (rec : H → Rec) (S : List H) (hnd : S.Nodup)
    (hconst : ∀ h1 ∈ S, ∀ h2 ∈ S, rec h1 = rec h2)
    (guess : Rec → H) :
    hitCount rec guess S ≤ 1 := by
  induction S with
  | nil => simp [hitCount]
  | cons h0 hs ih =>
    have hnd' : h0 ∉ hs ∧ hs.Nodup := List.nodup_cons.mp hnd
    have ih' := ih hnd'.2 (fun h1 hh1 h2 hh2 =>
      hconst h1 (List.mem_cons_of_mem h0 hh1) h2 (List.mem_cons_of_mem h0 hh2))
    by_cases hhit : guess (rec h0) = h0
    · have hnone : ∀ h ∈ hs, guess (rec h) ≠ h := by
        intro h hh heq
        have hrec : rec h = rec h0 :=
          hconst h (List.mem_cons_of_mem h0 hh) h0 List.mem_cons_self
        have : h = h0 := by
          calc h
              = guess (rec h) := heq.symm
            _ = guess (rec h0) := by rw [hrec]
            _ = h0 := hhit
        exact hnd'.1 (this ▸ hh)
      simp [hitCount, hhit, hitCount_eq_zero_of_none rec guess hs hnone]
    · simp [hitCount, hhit]
      exact Nat.le_trans ih' (Nat.le_refl 1)

/-! ## Registered two-hypothesis witness -/

inductive Hyp where
  | a
  | b
deriving DecidableEq, Repr

inductive Exp where
  | passive
  | sep
deriving DecidableEq, Repr

inductive Ans where
  | yes
  | no
deriving DecidableEq, Repr

def R : Hyp → Exp → Ans
  | .a, .passive => .yes
  | .b, .passive => .yes
  | .a, .sep => .yes
  | .b, .sep => .no

def G0 : List Exp := [.passive]

def live : List Hyp := [.a, .b]

theorem registered_records_agree :
    record R G0 Hyp.a = record R G0 Hyp.b := by
  decide

theorem registered_separator_splits :
    R .a .sep ≠ R .b .sep := by
  decide

theorem registered_no_passive_map :
    ∀ guess : List Ans → Hyp,
      ¬ (guess (record R G0 .a) = .a ∧ guess (record R G0 .b) = .b) := by
  intro guess
  exact no_transcript_map_hits_both (record R G0) .a .b
    (by decide) registered_records_agree guess

theorem registered_hits_le_one :
    ∀ guess : List Ans → Hyp,
      hitCount (record R G0) guess live ≤ 1 := by
  intro guess
  exact hits_le_one (record R G0) live (by decide)
    (fun h1 _ h2 _ => by
      cases h1 <;> cases h2 <;> simp [record, R, G0])
    guess

#print axioms no_transcript_map_hits_both
#print axioms registered_no_passive_map
#print axioms registered_hits_le_one

end IdentImpossibility
end StructuralIntelligence
