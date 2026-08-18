/-!
# Structural Intelligence — the dial's unique tie point (Lea-proved)

Provenance.  This lemma was proved by an **autonomous Lea run**
(project `sic-dynamics`, session `5aa1ef48-ae18-4a9b-b879-97c574866b89`,
run `1c9cab0d-ad41-44cb-8dc7-1ce70eb5da2a`, model
gemini-3.1-pro-preview, 52 seconds) and passed SafeVerify through
Lea's `/verify` endpoint before being ported here verbatim (statement
and tactics unchanged; only the namespace differs, `Lea.SicDynamics`
→ `StructuralIntelligence.CrossingUnique`).

Content.  `ConcernChoice.boundary_base` shows the door-3 dial picks
`q_perm` up to `k = 22` and `q_id` above.  This lemma pins the tie
itself: on the scaled grid, `cost(q_perm) = 270 + 27k` meets
`cost(q_id) = 864` at exactly one `k ≤ 54`, namely `k = 22`
(ε = 11/27).  The dial has one crossing, not several.

No Mathlib.  No `native_decide`.  No `sorry`.
-/

namespace StructuralIntelligence
namespace CrossingUnique

theorem crossing_unique :
    (270 + 27 * 22 = 864) ∧
      ∀ k : Nat, k ≤ 54 → 270 + 27 * k = 864 → k = 22 := by
  constructor
  · decide
  · intro k _ h
    omega

#print axioms crossing_unique

end CrossingUnique
end StructuralIntelligence
