# S-022 Seed and Bootstrap Calibration Preregistration

Frozen: 2026-07-14, before generating `results/summary.*`.

## Question

How do independent seed count, paired-episode noise, and seed-level treatment-effect heterogeneity change the coverage, width, power, false-positive rate, and sign stability of percentile intervals?

This is the local synthetic tranche of science-primer backlog item S-022. It compares the specifically requested naive percentile procedure with the resampling procedure appropriate to this paired hierarchy. It does not claim to finish S-022's future empirical-variance, BCa, bootstrap-t, or randomization-interval tranches.

## Estimand and independent unit

The estimand is the population mean paired treatment-control difference. A seed is the independent unit. Four paired episode differences are nested within each seed:

`difference = effect + seed_heterogeneity + paired_episode_noise`

The naive procedure pools the nested differences and resamples them as independent rows. The appropriate procedure first retains each treatment-control pair as a difference, averages within seed, and resamples seed clusters.

## Frozen grid

- Seed counts: 3, 5, 8, 10, 16, and 64.
- Monte Carlo repetitions: 200 per regime/seed cell.
- Percentile-bootstrap repetitions: 300 per interval.
- Interval confidence: 95%.
- Root deterministic seed: 20260714.
- Methods: `naive_row_percentile` and `paired_seed_cluster_percentile`.
- The same simulated datasets are evaluated by both methods within each regime/seed cell.

| Regime | True effect | Episode noise SD | Seed hierarchy SD | Width target | Claim type |
| --- | ---: | ---: | ---: | ---: | --- |
| `null_iid` | 0.0 | 1.0 | 0.0 | 0.50 | null calibration |
| `moderate_iid` | 0.5 | 1.0 | 0.0 | 0.50 | directional effect |
| `moderate_hierarchy` | 0.5 | 0.7 | 0.8 | 0.75 | directional effect |
| `null_hierarchy` | 0.0 | 0.7 | 1.0 | 0.75 | null calibration |
| `weak_high_noise_hierarchy` | 0.2 | 1.5 | 1.2 | 0.80 | directional effect |

## Metrics

Every method/regime/seed cell reports interval coverage and mean width. Non-null cells also report rejection power and estimate-sign stability. Null cells report false-positive rate. No regime or cell may be suppressed because it performs poorly.

Raw estimate-sign stability is not Gelman-Carlin conditional Type-S error, and this design does not compute Type-M exaggeration conditional on statistical significance. Those metrics require a separately frozen follow-up; they must not be inferred from this decision table after the fact.

## Promotion and pilot decisions

Only `paired_seed_cluster_percentile` is eligible for a decision. A cell is `promotion_ready` when all applicable conditions pass:

- coverage is at least 0.90;
- mean interval width is at most the regime's frozen target;
- for a non-null regime, power is at least 0.80 and sign stability is at least 0.90; or
- for a null regime, false-positive rate is at most 0.10.

A non-promotion cell is `pilot_only` when coverage is at least 0.80 and either sign stability is at least 0.70 (non-null) or false-positive rate is at most 0.20 (null). It is otherwise `insufficient`.

## Experiment-level gates

- Every frozen regime/seed/method cell is present.
- At least one hierarchical cell shows seed-cluster coverage at least 0.05 higher than naive row coverage.
- No promotion-ready decision has coverage below 0.90.
- No promotion-ready decision exceeds its frozen width target.
- The 64-seed null-hierarchy cell has false-positive rate at most 0.10.
- The weak/high-noise/hierarchy regime is never promotion-ready at any tested seed count.

Failed gates and negative regimes remain in the public aggregate summary. A failure is evidence against the proposed policy in that regime, not a prompt to retune the thresholds or remove the cell.

## Interpretation matrix

| Outcome | Interpretation |
| --- | --- |
| Naive coverage is materially lower under hierarchy | Nested rows create false precision; seed-cluster resampling is required for this design. |
| Both methods miss coverage | The seed count/bootstrap budget or percentile procedure is inadequate; neither may support promotion. |
| Coverage passes but power/precision fails | The cell remains pilot-only; valid uncertainty does not make the claim informative. |
| All promotion conditions pass | That synthetic cell supports its stated policy only; it does not validate a real experiment. |
| Weak regime passes unexpectedly | Report it, but do not redefine or remove the frozen negative-regime gate. |

## Claim boundary

This simulation may diagnose consequences of the stated hierarchy. It cannot establish a universal seed floor, substitute synthetic variance for representative public-safe empirical variance, or support mechanism/field claims.
