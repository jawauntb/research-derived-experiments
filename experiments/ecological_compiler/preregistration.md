# Ecological Compiler Study I Preregistration

## Discovery-Regime Audit

Question:
Does dependence on fishing covary with political complexity across the
preindustrial societies in the Ethnographic Atlas, and does any association
survive controls for subsistence alternatives, ecology, geography, shared
cultural history, settlement, and population scale?

Current regime:
- Artifact types: D-PLACE CLDF records, society-level analysis tables,
  ordered-logit estimates, block-bootstrap intervals, permutation nulls,
  transport checks, figures, and a public result summary.
- Operations: deterministic CLDF parsing, documented joins, ordinal maximum
  likelihood, family and spatial block resampling, within-region permutation,
  and leave-one-region-out refits.
- Gates/verifiers: EC_G0 through EC_G7 below, unit tests, the root quality
  check, and an explicit causal-claim ceiling.
- Store: raw external data remain under `artifacts/ecological_compiler/`;
  reduced public results live under `experiments/ecological_compiler/results/`.
- Known limitations: the Ethnographic Atlas is observational, societies are
  not independent draws, focal dates vary, and fishing dependence conflates
  marine and freshwater subsistence with technologies and exchange networks.

Action class:
- Retrieval/search/discovery: **search**.
- Why: this study tests a new path through existing data and estimators. It
  does not add a new artifact type or establish a new causal mechanism.

Experiment:
- Manifest/report paths: `experiments/ecological_compiler/experiment_manifest.json`,
  `experiments/ecological_compiler/results/summary.json`.
- Positive target: a stable positive EA003 coefficient for EA033 after the
  pre-registered pre-treatment controls.
- Negative controls: within-region permutation of EA003; matched models that
  substitute hunting or gathering for fishing; direct control for distance to
  coast.
- Stress tests: family-block and spatial-block intervals, non-European
  transport, leave-one-region-out refits, exclusion of the three largest
  language families, and binary-cutpoint sensitivity.

Gate:
- Acceptance rule: only the bounded descriptive association clears if EC_G0,
  EC_G1, EC_G2, EC_G3, and EC_G7 all pass. EC_G4 through EC_G6 determine
  specificity, transport, and whether the compiler interpretation remains
  plausible.
- Withheld/rejected rule: a failed or unknown fatal gate rejects the strong
  fishing-complexity association. No result from this design licenses a causal,
  nutritional, neurobiological, genetic, or Europe-specific superiority claim.

Results:
- Accepted artifacts: pending execution.
- Rejected or withheld artifacts: pending execution; failed alternatives will
  remain in the public summary.
- Key metrics: ordered-logit log-odds coefficient, family-block 95% interval,
  within-region permutation p-value, attenuation after potential mediators,
  AIC change, and transport sign stability.
- Variance or ablation: family, spatial, regional, and cutpoint sensitivities.

Residual content:
- Explained by old regime: the literature already establishes that aquatic
  subsistence varies with ecology and that political complexity covaries with
  settlement and population scale.
- New content outside old regime: whether fishing has a distinctive residual
  association with EA033 after those factors are separated.
- Retractions or supersessions: the direct chain from fish to dopamine to
  European civilization is treated as rejected before this run because its
  biochemical links are false or unsupported. This study cannot restore it.

Next move:
Run the smallest global cross-cultural test. A maritime-network study is
warranted only if the residual is stable enough to require separation of food
from connectivity.

## Target object and decision

- Target object: the society-level relation between EA003, ordinal dependence
  on fishing, and EA033, jurisdictional hierarchy beyond the local community.
- Decision: retain a descriptive fishing-complexity residual, with its stated
  limits, or reject it and treat ecology, settlement, population, and
  connectivity as the better-supported paths.
- Unit of analysis: one D-PLACE Ethnographic Atlas society at its coded focal
  place and focal year.
- Data clock: D-PLACE EA v3.2.1, released 2025-11-13, Git commit
  `5aa46eea62815daa283ac67cc757065a1b3be16e`; D-PLACE environmental support
  data at Git commit `9bfed2c8c206be00f55f71516f262bbca2234e5a`.

## Representation and variables

- Outcome EA033: ordered support `{1, 2, 3, 4, 5}`, from no authority beyond
  the local community through four jurisdictional levels.
- Exposure EA003: ordered support `{0, ..., 9}`, from 0-5% through 86-100%
  dependence on fishing, shellfishing, or large aquatic animals.
- Pre-treatment controls: EA002 hunting, EA004 husbandry, EA005 agriculture
  (gathering is the omitted compositional reference), absolute latitude,
  `log1p(distance to coast in km)`, annual mean temperature, temperature
  variance, precipitation predictability, net primary production, focal year,
  and D-PLACE macroregion fixed effects.
- Potential mediators/compiler traces: EA030 settlement pattern, EA031 mean
  local-community size, and `log1p(EA202 population)`.
- Dependence controls: Glottolog language family and 20-degree latitude by
  longitude spatial cells.
- Coordinates: geographic coordinates are WGS84-like latitude/longitude
  fields supplied by D-PLACE; no Euclidean distance claim is made from raw
  degrees.

## Estimands and models

The primary estimand is the EA003 coefficient in a proportional-odds ordered
logit. One exposure step is one D-PLACE fishing-dependence category. All
continuous non-indicator covariates are standardized on the complete-case
analysis sample.

1. M0: EA033 on EA003 only.
2. M1: M0 plus the pre-treatment controls above.
3. M2: M1 plus EA030, EA031, and log population as potential mediators.

Because the five subsistence shares are compositional, M1 includes hunting,
husbandry, and agriculture while leaving gathering as the reference. The EA003
coefficient therefore describes a shift toward fishing conditional on those
three alternatives, not an absolute calorie effect.

The ordered-logit likelihood uses strictly increasing cutpoints. Report the
maximum-likelihood coefficient, model AIC, a language-family block-bootstrap
95% percentile interval, and a 500-draw within-region permutation p-value.
Use seed 20260826. Family and spatial block bootstraps use 300 successful draws
each. Failed optimizations are counted and reported, never silently replaced.

## Material assumptions and identification boundary

1. EA003 and EA033 codes preserve their intended order across societies.
2. The chosen covariates capture major measured ecological and subsistence
   alternatives, but unmeasured confounding remains possible.
3. Language family is an imperfect proxy for shared cultural ancestry; the
   family bootstrap does not equal phylogenetic generalized least squares.
4. Settlement and population variables may be mediators, so M1 and M2 answer
   different descriptive questions.
5. Proportional odds is a working model. Binary-cutpoint refits test whether
   one coefficient hides threshold-specific sign reversals.
6. The design identifies association, not a causal effect. It contains no
   nutrient biomarkers, individual cognition, dopamine measure, or maritime
   network measure.

## Fatal gates (noncompensatory)

- **EC_G0_PROVENANCE:** exact source commits, input hashes, join counts, and the
  deterministic run command are recorded.
- **EC_G1_DATA_INTEGRITY:** EA003 and EA033 stay within registered support,
  society-variable duplicates are absent after deterministic resolution, every
  model matrix is finite, all outcome levels remain represented, and M1 has at
  least 600 complete societies.
- **EC_G2_ADJUSTED_ASSOCIATION:** M1 EA003 is positive, its family-block 95%
  interval excludes zero, and its within-region permutation p-value is at most
  0.05.
- **EC_G3_COASTAL_SEPARATION:** EC_G2 still holds with logged distance to coast
  included. This gate prevents coastline proximity from standing in for the
  registered exposure.
- **EC_G4_SUBSISTENCE_SPECIFICITY:** the standardized M1 EA003 coefficient is
  larger than the corresponding hunting and gathering substitute coefficients.
- **EC_G5_COMPILER_PATTERN:** adding settlement, local-community size, and
  population improves AIC and reduces the absolute EA003 coefficient by at
  least 25%, without a sign reversal. Passing is consistent with mediation or
  overcontrol; it is not proof of either.
- **EC_G6_TRANSPORT:** the M1 fishing coefficient remains positive outside
  Europe, after excluding the three largest language families, and in at least
  six leave-one-region-out refits.
- **EC_G7_ORDINAL_STABILITY:** all four binary-cutpoint fishing coefficients
  share the M1 sign and no coefficient differs from the ordinal estimate by
  more than three pooled standard errors.

## Edge, null, and failure cases

- If a category or region disappears in a resample, use the registered global
  design columns and report a failed fit if the likelihood cannot be optimized.
- If fewer than 240 of 300 block-bootstrap fits succeed, the corresponding
  interval is unknown and its gate fails.
- If family metadata are missing, those societies remain in point estimates
  under an explicit `Unknown` family but form their own singleton bootstrap
  clusters.
- If environmental joins reduce M1 below 600 societies, EC_G1 fails; no simpler
  post hoc model replaces it as the primary analysis.
- Exact-zero, sign-reversed, or wide-interval estimates count against the
  positive claim. Downstream fit cannot compensate for a failed fatal gate.

## Evidence and provenance paths

- Raw external data: `artifacts/ecological_compiler/` (gitignored).
- Preregistration: `experiments/ecological_compiler/preregistration.md`.
- Analysis code: `experiments/ecological_compiler/analysis.py`.
- Public results: `experiments/ecological_compiler/results/summary.{json,md}`.
- Figure: `experiments/ecological_compiler/results/model_coefficients.png`.
- Paper: `papers/ecological_compiler/paper.md`.

## Pre-execution amendment (2026-08-26)

The registered command originally used the repository's complete `quality`
dependency group. On this Intel macOS host, that group cannot resolve because
the pinned Torch build exposes an ARM-only macOS wheel. Before inspecting the
EA003-EA033 relationship, the execution command was narrowed to a clean Python
3.12 environment containing the same registered NumPy, SciPy, and Matplotlib
versions. The scientific question, variables, estimands, controls, seeds,
resampling counts, gates, and failure thresholds are unchanged. Lint and type
checks run separately through pinned standalone `ruff` and `ty` environments.

## Pre-result numerical amendment (2026-08-26)

The first two full-run attempts stopped before producing any model coefficient:
first at SciPy's default function-evaluation ceiling and then at the registered
300-iteration ceiling. The likelihood implementation now supplies an analytic
gradient, checked against central finite differences in the test suite. The
point-fit ceiling is 1,000 iterations and the warm-started resample ceiling is
600. Bounds, likelihood, starting values, sample, model specification, seeds,
draw counts, gates, and failure handling are unchanged.

After the analytic repair, a diagnostic point fit exposed the M1 coefficient
(`0.1603`) but no complete result set. Before the next full run, two late-stage
implementation defects were corrected: D-PLACE's European labels are matched
by the `* Europe` suffix rather than equality to a nonexistent `Europe` label,
and transport refits warm-start from the converged M1 parameters. These repairs
implement the already registered transport checks and do not alter a gate.

The first complete result artifact then showed that 195 family and 227 spatial
draws, plus all four binary-cutpoint fits, stopped at numerical limits. Those
gates were therefore unknown, not scientific failures. A 20-draw diagnostic in
each block design converged completely when allowed more than 600 iterations.
The final run raises the warm-started ordered-logit ceiling to 4,000 and gives
binary logit an analytic gradient checked by finite differences. No estimate,
sample rule, resampling draw, seed, threshold, or gate was changed.

One of four binary fits still stopped at the 1,000-iteration ceiling in the
next complete run, so the final binary ceiling is 3,000. The verdict code was
also corrected to require all eight gates, matching the section that registered
them as noncompensatory. This correction cannot rescue the hypothesis: the
family interval already crossed zero and the three-family exclusion reversed
the fishing coefficient.

## Post-result implementation audit and corrective rerun (2026-08-26)

Code review after the first complete result found that the fixed effects,
permutation blocks, and leave-one-out checks had used the Ethnographic Atlas
`region` field's 50 fine-grained values even though the registered
representation named D-PLACE macroregions. The corrected rerun uses the
pre-existing Glottolog `macroarea` field in the pinned D-PLACE support data:
Africa, Australia, Eurasia, North America, Papunesia, and South America. The
original result remains recoverable from the branch history. This is a
representation repair, not a post hoc attempt to clear a gate; all results and
the final verdict are regenerated whether they become more or less favorable.

The same audit enforced other rules that were already registered but not fully
implemented. Missing family labels now create society-specific singleton
clusters. EC_G0 now matches the exact SHA-256 digest of every registered input
and requires both pinned source-data worktrees to be clean. EC_G1 now fails on
any conflicting society-variable duplicate. Block intervals now collect 300
successful, outcome-support-preserving resamples while reporting optimizer
failures, outcome-level dropouts, and total attempts; permutation inference
likewise reports attempts needed to obtain 500 successful fits.

Two interpretive limitations are made explicit. EC_G3 is a redundant
implementation-presence check rather than evidence independent of EC_G2,
because EC_G2 is already evaluated in the distance-to-coast model. EC_G4 is a
limited compositional contrast, not an exact proof of marine specificity.
EC_G7's three-standard-error comparison uses optimizer inverse-Hessian
approximations as a sensitivity heuristic; the family-block interval remains
the registered primary uncertainty estimate. None of these gates can rescue a
failed necessary gate, and none upgrades the study beyond cross-sectional
description.
