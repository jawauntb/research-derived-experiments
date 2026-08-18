# SafeVerify receipt — Wave 5 (2026-08-18)

Kernel replay against Lea's pre-built SafeVerify
(`leanprover/lean4:v4.29.0`, binary at
`prover/third_party/SafeVerify/.lake/build/bin/safe_verify`). The repo
package pin is 4.31.0; the whole `formal/structural-intelligence`
package was rebuilt on 4.29.0 in a scratch copy so oleans matched the
checker. For each file the sorry-target was generated with Lea's
splitter (`lea/safeverify.py::sorry_target`) and compiled at the same
`StructuralIntelligence/<File>.lean` module path as the submission so
generated hygiene names lined up. Replay ran
`safe_verify -v target.olean submission.olean --disallow-partial`.

A green `lake build` is not this receipt.

| Node(s) | File | SafeVerify | Axioms of headlines |
|---|---|---|---|
| `gold_flip_pair_eq`, `gold_flip_pair23`, `menu_blind_kappa_impossible`, `base_gold_consistent`, `screen_exact_on_flip_rows` | `MenuBlind.lean` | **passed** | `propext` |
| `base_subset_ext7`, `sq_min_*`, `sq_mass_*`, `cube_min_*`, `cube_mass_*`, `generator_border_sq`, `generator_border_cube`, `min_size_not_shared_function` | `GeneratorBorder.lean` | **passed** | `propext` or none (`sq_min_base`, `generator_border_sq`, `min_size_not_shared_function` use no axioms) |
| `choice_*` (six concerns), `unweighted_strictly_beaten`, `boundary_base`, `boundary_ext`, `mirrored_dual_ext`, `boundary_menu_relative` | `ConcernChoice.lean` | **passed** | `propext` |
| `crossing_unique` | `CrossingUnique.lean` | **passed twice** — via Lea `/verify` (session `5aa1ef48…`; proved by an autonomous Lea run in 52 s) and via the same 4.29 scratch replay as the door files | `propext, Quot.sound` (`omega` normalizes through `Int`, a quotient; both axioms are Lean-kernel core and SafeVerify-whitelisted) |

## Wave 6 (same day, later): essay-driven files

Same method (4.29 scratch, sorry-targets at matching module paths,
`safe_verify --disallow-partial`).

| Node(s) | File | SafeVerify | Axioms of headlines |
|---|---|---|---|
| `meaning_quotient_is_registered`, `company_quotient_is_parity`, `neither_partition_refines_the_other`, `company_does_not_refine_meaning`, `meaning_does_not_refine_company` | `MeaningVsCompany.lean` | **passed** | none for the three enumerations; `propext, Quot.sound` for the two transported forms |
| `no_largest_adequate`, `maximal_not_unique`, `greedy_repair_works`, `greedy_depends_on_order` | `WeakestAdequate.lean` | **passed** | `propext, Quot.sound` / none / `propext` / none |
| `sections_spec_indistinguishable`, `section_swap`, `four_sections_distinct`, `four_sections_one_shadow` | `KleisliSection.lean` | **passed** | none / `propext` / none / none |
| `levelCells_zero_distortion`, `zero_distortion_cell_in_level`, `no_coarser_on_witness` | `DialZero.lean` | **passed** | `propext` / `propext` / none |

Still open in Lean: the silent-substitution general lemmas
(`ChebyshevTilt`: `rearrange`, `tilt_pointwise`, `tilt_monotone`) are
running through Lea; the registered witness half of
`SilentSubstitution.lean` is drafted and waits on them.

Statement hygiene held by construction: no structure literals in any
theorem statement (the Wave 2 splitter workaround was not needed), all
quantifiers over explicit lists, kernel `decide` only (plus `omega` in
`CrossingUnique`).

Axiom whitelist, stated precisely: `propext` and `Quot.sound` are
kernel-core and accepted; `Classical.choice`, `sorryAx`, and
`Lean.ofReduceBool` / `Lean.ofReduceNat` (`native_decide`) are not.

Environment notes for reproducers: the headless adapter is the
reliable entry point (`adapter/.venv/bin/python run_api.py`);
`config/lea.local.toml` must exist (restore from the example if a
cleanup script removed it); the Vite web UI's rollup crash is
irrelevant to proving.

Still Python (quarantined, per the backlog): empirical Φ ratios,
GD 8/8, extras 43/28, and the estimation instrument's sequence traces.
