# Intention Is All You Need v3 — review resolutions (2026-08-18)

Working ledger for the eight review items on v3. Each row: the
reviewer's point, the program's resolution, and the wording the
rewrite must adopt. The rewrite is deferred until every resolution
below is landed (user order); this file is its marching orders.

| # | Item | Resolution | Status |
|---|---|---|---|
| 1 | **D13 existence/uniqueness bug** — "the largest region" with spread ≤ τ need not exist; incomparable maximal regions can have an inadequate union | Kernel-checked in `formal/structural-intelligence/StructuralIntelligence/WeakestAdequate.lean`: `no_largest_adequate` (general over candidate regions, not enumeration), `maximal_not_unique`, plus the constructive repair `greedy_repair_works` / `greedy_depends_on_order` — a maximal adequate region exists via greedy completion but is scan-order-dependent, so D13 is well-posed only with a **disclosed selection rule** (the κ_screen lesson transported). Rewrite: define the weakest adequate specification as "a region maximal under inclusion among those within tolerance, selected by a disclosed completion order or optimization criterion"; kill the definite article. | **Lean landed (Wave 6)** |
| 2 | **Theorem B nestedness overclaim** — "as D grows the cells coarsen" implies a nested chain of optima that rate-distortion does not guarantee | Two-part: (a) the safe general claim — the optimal description rate is weakly decreasing in the budget (feasible sets nest) — goes in the rewrite verbatim: "the optimal description rate falls as the distortion budget grows"; (b) the nestedness question becomes an exact instrument (`dial_nestedness`, queued): enumerate all partitions of a small registered world under the task-relative distortion, compute the optimum per budget, and check chain nestedness — banked either as verified-here or as a counterexample. The D = 0 clause stays as stated (level-set partition); its Lean core is a queued Wave 6 item (`DialZero.lean`). | **Wording fixed; instrument queued** |
| 3 | **P14 too strong** — mutual quotient legibility is not necessary for communication simpliciter (accidental/conventional success exists) | Rewrite adopts the reviewer's narrowing verbatim in spirit: "robust preservation of intended meaning under representational mismatch and distribution shift requires sufficiently accurate two-sided legibility." Gate 4 already tests the narrowed claim; no experiment change needed. | **Wording fix for rewrite** |
| 4 | **P7 status ambiguity** — labeled a proposition, used as a definition | Decision: P7 becomes a **definition** (meaning := concern-relevant invariance under re-instantiation), and the empirical residue is restated as a hypothesis: "this definition captures ordinary semantic competence and predicts breakdowns better than resemblance or co-occurrence accounts" — testable, with Gate 5 as its first instrument. The essay's §2 vocabulary demands the split; make it. | **Wording fix for rewrite** |
| 5 | **P6/P9 over-inference** — interventions show valuation shapes selectivity; they do not exclude a value-neutral substrate underneath | Rewrite sharpens the thesis to the reviewer's harder-to-refute form: "there is no empirically warranted requirement for a value-neutral core, and learned representation need not factor into neutral representation followed by valuation." The two experiments stay cited at exactly that strength. | **Wording fix for rewrite** |
| 6 | **Break-invariance ≠ all of causal inference** — interventions sometimes separate causal models compatible with one observational distribution, not points within an object-level fiber | Adopt the reviewer's reformulation: "observation induces an equivalence class of admissible mechanisms; intervention refines that equivalence class." Note this is already machine-checked structure in this program: `formal/relative-identifiability/` (`factorsThrough_iff_fiberConstant`, `obstruction_iff_not_factors`, `indistinguishable_of_richer` — richer experiment families refine indistinguishability). The rewrite should cite those files rather than re-arguing. | **Wording fix + existing Lean citation** |
| 7 | **A4 relation vs effective coupling** — mathematical/representational relations need not tilt anything | Rewrite splits the axiom's vocabulary: A2 keeps "relation" in the broad structural sense; A4 is restated over **effective couplings** (relations that enter some mechanism), with one sentence naming the split so the ontology does not get causal power by definition. | **Wording fix for rewrite** |
| 8 | **Two beautiful overstatements** — "a specification whose compliant set is a single point … is the thing itself"; "nothing to be intelligent about" on singleton regions | Keep the punch, scope the claim: (a) "…is not doing a specification's work: nothing is left open" (unique specification ≠ identity); (b) "no **selection dividend** remains — execution may still be arbitrarily hard." The second is also what the `choice_dividend` instrument (Gate 1, in flight) makes exact: the dividend is zero on singletons; execution cost is out of scope by construction. | **Wording fix; instrument in flight** |

## Standing epistemology (adopted for all future experiments and proofs)

The v3 discipline now governs the program's own artifacts:

1. Every claim carries its kind (axiom / definition / theorem /
   proposition / model / hypothesis / thesis / conjecture / bet) and
   every cross-domain identification names its grade on the sameness
   ladder (shared diagram shape < bisimulation < functor < adjunction
   < isomorphism). Categorical readings are welcome at the grade they
   earn: Kleisli-section and congruence-lattice facts are provable
   here; equivariance-as-naturality and dividend-as-adjunction-defect
   remain conjectures owing their forgetful maps.
2. Kernel and bridge are stated separately, always: experiments kill
   bridges, not kernels; a theorem that "fails in the lab" had absent
   premises.
3. Preregistered gates precede runs; a verdict that kills a claim
   still passes CI; exposure/selection decompositions are labeled
   analytic where they are analytic.
4. Every theorem-level claim goes through the Lea pipeline (AGENTS.md
   law): proved, then SafeVerify-verified, receipts on file, no
   `native_decide`, statement hygiene for the splitter.
