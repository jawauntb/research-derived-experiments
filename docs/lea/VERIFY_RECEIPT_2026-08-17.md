# SafeVerify receipt — Wave 2 (2026-08-17)

Kernel replay against Lea's pre-built SafeVerify (`leanprover/lean4:v4.29.0`,
binary at the local Lea install). The repo package pin is 4.31.0; files were
rebuilt on 4.29.0 in a scratch copy so oleans matched the checker. Target and
submission were compiled from matching `StructuralIntelligence/<File>.lean`
paths so generated `noConfusion` hygiene names lined up.

A green `lake build` is not this receipt.

| Node | File | SafeVerify | Axioms of headline |
|---|---|---|---|
| `kappa_cheap_not_function` | `KappaCheap.lean` | **passed** | `propext` |
| `kappa_screen_hits_suite` | `KappaScreen.lean` | **failed** (`native_decide`) | `propext`, `native_decide` |
| `bag_not_unique` | `KappaUnique.lean` | **passed** | none |
| `kappa_relabel_natural` | `KappaRelabel.lean` | **passed** | none |
| `affine_escapes_kirchhoff` | `Aff13.lean` | **passed** | none |
| `poset_not_determine_interval` | `DiamondInterval.lean` | **passed** | none |
| `surgery_miss_pair_eq` | `SurgeryMiss.lean` | **passed** | `propext` |

`KappaScreen` was **proved-not-verified** on the first pass (`native_decide`).
A later pass replaced `native_decide` with kernel `decide` (high
`maxRecDepth`) and SafeVerify **passed**. Do not start Paper G.

Relabel/Surgery targets needed a brace-aware `sorry` split because several
theorem *types* contain `{ action := ... }`; Lea's first-`:=` splitter
broke those two files. The proofs themselves were not edited.

Still Python: empirical Φ ratios, GD 8/8, extras 43/28, `dta_n4_representable_iff`,
`swap_typed_wins`.

## Wave 4 + KappaScreen kernel decide (same day, later)

| Node | File | SafeVerify | Axioms |
|---|---|---|---|
| `kappa_screen_hits_suite` | `KappaScreen.lean` | **passed** (kernel `decide`) | `propext` |
| `dta_n4_representable_iff` | `DtaN4.lean` | **passed** | none |
| `swap_typed_wins` | `SwapTyped.lean` | **passed** | `propext` |

Haskell independently computed the 16-cell n=4 matrix (representability
equals `G_q ⊆ G_Y` on every registered cell) and the Paper B swap cell
before the Lean files were written.
