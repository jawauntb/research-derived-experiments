# Theorem backlog — Lea formalization program

> Generated 2026-08-18 by a repo-wide audit (Claude Fable 5, session
> `4adbd42d-0e99-41df-b0be-7d9d5b7e3caa`), for the standing mandate in
> `AGENTS.md` ("Theorem proving with Lea"). Update rows as claims change
> state; never delete rows — move them. Status rule: **lean-verified** =
> SafeVerify receipt green; **lean-proved** = elaborates, no `sorry`, no
> receipt; **python-enumerated** = finite exact instrument without a Lean
> headline; **prose-only** = paper statement without machine check.

## Summary (counts)

| Axis | Count (distinct claim rows below) |
|---|---|
| **Status** | prose-only **26** · python-enumerated **7** · lean-proved **≈60 headlines** (plus Wave 7 `EmlCatalan` / `RepairTable` / `ObstructionTaxonomy`, proved-not-verified) · lean-verified **Wave 2–6 headlines** (receipts 2026-08-17 / 2026-08-18) |
| **Formalizability** | finite-decidable **≈70** · needs-mathlib **≈25** · analytic-open **11** · not-a-theorem/empirical **14** |
| **Priority** | P0 **≈35** · P1 **≈40** · P2 **≈25** |
| **Do-not-reprove** | **8** named cores + Paper 0 / Mathlib-into-cores bans |
| **Quarantined empirical** | Φ / GD 8–8 / extras 43–28 / swap empirical halves + related process rankings |

---

## Do not re-prove (repo bans)

From `.cursor/skills/lea/SKILL.md`, `docs/lea/instructions.md`, `docs/lea/memory.md`:

| Ban | Reason |
|---|---|
| `repair_paths_disagree` / `pathA` / `pathB` | Already Lean; cite |
| `CommonSuffScreen` / Theorem 4 algebraic core | Already Lean; κ_screen *uses* it |
| `eml_zero_identity*` | Already Lean; empty axiom footprint |
| `Compiler/SquaringSeparation` (US-2/US-3) | Already Lean |
| Paper 0 / `Complex.log 0` | Off-path; withheld |
| Import Mathlib into mathlib-free cores | Hard rule |
| Refit Paper E cheap signature to erase `pair_eq` miss | Forbidden |
| New scientific letter / Paper G / "new κ master object" | Not Lea's job |
| Lorentz ≅ Lamport ≅ PE as one functor | Killed on diamond |
| OpenAI 2026 writeups as theorems | Banned |

## Quarantined as empirical-only (not theorems)

| Item | Where | Why quarantined |
|---|---|---|
| Gibbs `Φ ≈ 2.015625` | `eml_us4_prime`, `sic_dynamics` | Process mass ranking |
| Matching-skeleton GD **8/8 vs 6/8** | `eml_us4_gradient` | Seeded GD counts |
| Unknown-skeleton GD **7 vs 7** | `eml_us4_search` | Ranking rejection |
| Frozen-leaf extras **43/28** | `eml_us4_discrete` | Extra-basin count |
| Neural bootstrap / "GD tracks Φ generally" | US-4′ withheld | Untested |
| `swap_typed_wins` empirical halves beyond finite cells | Paper B instrument | SGD/float halves |
| Phase 4 metaphysics gate table | `phase4_metaphysics` | Diagnostic suite |
| ICA/iVAE/CRL Instruments 8–11 Monte Carlo | `structural_intelligence` | Numerical witnesses |
| Valence/concern-as-agency slogans | Possibility 2 adjacent | Withheld |
| Text nomination / DR–DCR reopen | Door letters | Closed as method |

---

## Main backlog (work remaining first)

### A. Prose-only · P0

| id | claim (≤20 words) | source path | status | lean file+theorem | formalizability | priority |
|---|---|---|---|---|---|---|
| SIC-A-gen | Master fibration `(q,K)` exists on general topological/measure spaces | `papers/structural_intelligence_foundations/paper.md` | prose-only | — (finite case: `sic_a_finite_discrete`) | analytic-open | P0 |
| SIC-Cc-uncond | Unconditional poly-in-`d_Z` learnability without covering hypothesis | `papers/structural_intelligence/paper.md` §2.5c | prose-only | — (conditional: `sicc_covering_meta`) | analytic-open | P0 |
| T4-prob | Measure-theoretic Theorem 4: tasks CI given common latent screen | `papers/structural_intelligence/paper.md` §2.4 | prose-only | algebraic core only | needs-mathlib | P0 |
| T7-ICA | Classical linear-ICA unmixing identifiable up to perm/sign | `papers/structural_intelligence/paper.md` Thm 7 | prose-only | — | needs-mathlib | P0 |
| TA-2 | Cocycle failure rank/support classifies obstruction type | `papers/theory_atlas/paper.md` TA-2 | discrete core lean-proved (Wave 7) | `ObstructionTaxonomy.lean` (+ TA-1 halves) | done (discrete); enlargement analytic-open | P0 |
| TA-2-cover | Smallest enlarged alphabet closing the cocycle (universal-cover analogue) | `papers/theory_atlas/paper.md` TA-2 | prose-only | discrete taxonomy is Lean (`ta2_taxonomy_classifies`); enlargement withheld | analytic-open | P0 |
| RR-1 | Eight canonical failure rows each admit a repairing lift on a toy | `papers/representation_repair_calculus/paper.md` RR-1 | lean-proved (Wave 7) | `RepairTable.lean` (+ RR-2) | done | P0 |
| RR-1-unique | Repairing lifts are unique / exist on a continuum | `papers/representation_repair_calculus/paper.md` RR-1 | prose-only | eight-row table is Lean (`rr1_table_well_defined`); uniqueness withheld | analytic-open | P0 |
| CT-1-MDL | Full MDL consistency under identifiability (probabilistic) | `papers/compiler_tomography/paper.md` CT-1 | prose-only | combinatorial core only | needs-mathlib | P0 |
| T2-converse | Shannon 1959 KKT converse for uniform-Hamming RD | mathlib package axiom | prose-only (axiomatized) | `Shannon1959_converse_uniform_hamming` (axiom) | needs-mathlib | P0 |
| T1-HS-pack | Halmos–Savage minimality `h`-extension packaging | mathlib package axiom | prose-only (axiomatized) | `HalmosSavage_minimality_h_extension` (axiom) | needs-mathlib | P0 |
| TA-1-naked | Naked cocycle ↔ gluing without injectivity hypothesis | `papers/theory_atlas/paper.md` | prose-only | Lean needs injectivity | analytic-open | P0 |
| US-4-law | Gibbs fiber mass is the access law for EML search generally | `papers/eml_universal_substrate/paper.md` US-4 | prose-only | — | analytic-open / not-a-theorem | P0 |

### B. Python-enumerated · P0 (finite leftovers after Wave 7)

| id | claim (≤20 words) | source path | status | formalizability | priority |
|---|---|---|---|---|---|
| EML-fib-Ck | Enumerated size-k fiber counts equal Catalan `C_k` for k=0..6 | `experiments/eml_fiber_spectrum/` | lean-proved (Wave 7, `EmlCatalan.lean` `emlFib_counts`, 197 trees) | done | P0 |
| EML-var-Ck | Variable-x size-k counts equal `2^{k+1} C_k` for k=0..5 | `experiments/eml_variable_spectrum/` | lean-proved (Wave 7, `EmlCatalan.lean` `emlVar_counts`, 3238 trees) | done | P0 |
| EML-pair-diff | Two same-size trees differ in denotation (symbolic form) | `eml_fiber_spectrum` | lean-proved (Wave 7, `EmlCatalan.lean` `eml_pair_diff`: derivations in any `ExpLn` carrier + registered `Nat` model separation) | done | P0 |
| CONC-EST | Plug-in frequency estimator converges at registered steps 1/2/6 | `experiments/delete_repair_concern_estimation/` | python-enumerated (sequence traces quarantined Python per 2026-08-18 receipt) | finite-decidable | P0 |
| RR-1-table | Eight-row lift table on registered toys | `papers/representation_repair_calculus/` | lean-proved (Wave 7, `RepairTable.lean` `rr1_table_well_defined`) | done | P0 |
| TA-2-discrete | Discrete obstruction taxonomy on registered charts | `papers/theory_atlas/` | lean-proved (Wave 7, `ObstructionTaxonomy.lean` `ta2_taxonomy_classifies` + general `classify_conditions`) | done | P0 |

### C. P1 (supporting)

| id | claim | source | status | formalizability |
|---|---|---|---|---|
| WI-P1 | Group-completed coverage increases with weakness | `weakness_invariance_neurips` Prop 1 | prose-only | finite-decidable (toy) |
| WI-PB | PAC-Bayes–kl bridge for overlapping mixture prior | same §2.1 | prose-only | needs-mathlib |
| CWW-1..3 | Concern-weighted Bennett weakness | `concern_weighted_weakness` | prose-only | needs-mathlib |
| GFT-1..5 | Gauge-fixed concern transport ladder | `gauge_fixed_concern_transport` | prose-only | needs-mathlib |
| FCQ-1..4 | Future-commitment completeness / gauge / Markov / bound | `future_commitment_quotient` | prose-only | needs-mathlib |
| DR5 / DR7-1 / DR7-2 | Realisation-spectrum; soundness–completeness gap; Spencer collapse | `dr5_*`, `dr7_*` papers | prose-only | analytic-open |
| IDENT-bench | Passive transcript cannot beat 1/m on held-out nonconstant label | `papers/ident/paper.md` | prose-only | finite-decidable |

### D. P2 (nice-to-have)

| id | claim | source | status |
|---|---|---|---|
| M201+ | Assumption-matrix executable bridges | `experiments/mathematical_claims/` | python-enumerated |
| Locatello-lb | Superpoly covering ⇒ SIC-C-c fails (Fano) | covering-learnability §5 | prose-only |
| CT-1-cont | Continuous-alphabet MDL consistency | `compiler_tomography` | prose-only |
| CS-ε | ε-relaxation of Ψ-equivalence | `causal_semantics` | prose-only |
| AA-wellspec | Well-specified prior consistency half of AA-1 | `autocatalytic_artwork` | prose-only |

---

## Appendix — already-Lean inventory

### A1. SafeVerify-verified headlines (receipts: `docs/lea/VERIFY_RECEIPT_2026-08-17.md`, `docs/lea/VERIFY_RECEIPT_2026-08-18.md`)

Wave 2 + Wave 4 (2026-08-17): `kappa_cheap_not_function`,
`kappa_screen_hits_suite`, `bag_not_unique`, `kappa_relabel_natural`,
`affine_escapes_kirchhoff`, `poset_not_determine_interval`,
`surgery_miss_pair_eq`, `dta_n4_representable_iff`, `swap_typed_wins`.

Wave 5 (2026-08-18): `MenuBlind` (door 1), `GeneratorBorder` (door 2 +
2b), `ConcernChoice` (door 3 + 3b) — all **SafeVerify-passed**, see
the 2026-08-18 receipt.

Wave 6 (2026-08-18, essay-driven): `CrossingUnique` (Lea-proved,
verified twice), `MeaningVsCompany` (§7 incomparability sting),
`WeakestAdequate` (review item 1: D13 counterexample + disclosed-order
repair), `KleisliSection` (categorical read at its earned grade),
`DialZero` (Theorem B D = 0 clause) — all **SafeVerify-passed**, same
receipt.

Wave 6b (2026-08-18): `SilentSubstitution` — the essay's P10 kernel,
complete and **SafeVerify-passed**: `tilt_monotone` (Theorem D finite
core; `rearrange`/`tilt_pointwise` beneath it Lea-proved),
`monitor_constant` and the opposed-reward witness axiom-free. No Lean
work remains open from Waves 5–6.

Wave 7 (2026-08-18): `EmlCatalan` (`emlFib_counts`, `emlVar_counts`,
`eml_pair_diff`), `RepairTable` (`rr1_table_well_defined`),
`ObstructionTaxonomy` (`ta2_taxonomy_classifies`) — **lean-proved,
not verified**. Files landed in #523–#525; aggregator bank is this
INT. Do not call `lake lean` “verified.”

### A2. Mathlib-free cores (`formal/structural-intelligence/`) — lean-proved

Paper A five finite facts (`DeleteRepair.*`); Theorem 4 core
(`CommonSuffScreen.*`, **do not re-prove**); Theorem 5 combinatorics
(`UnionBound`, `Pigeonhole`, `CouponCollector`); Theorem 6 core
(`Refinement`); CT-1 core (`CompilerTomography`); CS-1/2
(`CausalSemantics`); SA-1 (`Antecedents`); AF-1/2
(`AbstractionFrontier`); AG-2 (`AlignmentGovernance`); TA-1 both halves
(`TheoryAtlas`); RR-2 (`RepresentationRepair`); AA-2
(`AutocatalyticArtwork`); US-2/3 (`Compiler/SquaringSeparation`,
**do not re-prove**); EML zero identity (`EmlZeroIdentity`,
**do not re-prove**); Wave 5 door files (`MenuBlind`,
`GeneratorBorder`, `ConcernChoice`); Wave 7 finite leftovers
(`EmlCatalan`, `RepairTable`, `ObstructionTaxonomy`).

### A3. Mathlib companion (`formal/structural-intelligence-mathlib/`) — lean-proved

T1 (`exists_minimal_sufficient_finite_discrete`, 1 axiom), T2
(`R_D_uniform_hamming`, 1 axiom), P3 (`proposition3_adjunction`),
T5-rate (`theorem5_rate_bound`), AG-1 (`ag1_*`), CT-2
(`ct2_boltzmann_raises_expected_reward`), CG-1/CG-2 (`cg1_*`, `cg2_*`),
AA-1 (`aa1_*`), SIC-A finite (`sic_a_finite_discrete`), SIC-C-c
conditional (`sicc_covering_meta`, `sicc_covering_poly`).

### A4. Relative identifiability (`formal/relative-identifiability/`)

`indistinguishable_{refl,symm,trans}`,
`factorsThrough_iff_fiberConstant`, `obstruction_iff_not_factors`,
`indistinguishable_of_richer`.

---

## Suggested Lea wave order (operational)

1. **SafeVerify Wave 7** — replay `EmlCatalan`, `RepairTable`,
   `ObstructionTaxonomy` on the 4.29 scratch; then relabel
   proved → verified. Do not call the current bank verified.
2. **Wave 8, last finite leftover:** `CONC-EST` plug-in frequency
   estimator at registered prefixes 1 / 2 / 6. Sequence traces stay
   Python per the 2026-08-18 receipt until a kernel-decidable core
   is carved out.
3. **Axiom discharge (mathlib lane):** replace or isolate
   `HalmosSavage_minimality_h_extension` and
   `Shannon1959_converse_uniform_hamming`.
4. **Mathlib analytics:** T4 probabilistic, CT-1 MDL, T7 ICA,
   unconditional SIC-C-c (likely reframe as covering necessity).
5. **Never:** empirical Φ/GD/extras; Paper 0; re-proving the banned
   cores.
