# Seed Bootstrap Calibration

This package implements the local synthetic tranche of science-primer TODO S-022. It measures how seed count and seed-level heterogeneity affect percentile-bootstrap coverage and turns the results into an explicit pilot-versus-promotion decision table.

The critical comparison is between:

- `naive_row_percentile`, which incorrectly treats paired episode differences nested under a seed as independent; and
- `paired_seed_cluster_percentile`, which preserves the treatment-control pairing and resamples independent seed means.

The frozen design and all gates are in [`PREREGISTRATION.md`](PREREGISTRATION.md). Negative regimes and failed gates are retained in the result rather than tuned away.

## Run

From the repository root:

```bash
python3 -m experiments.seed_bootstrap_calibration.simulation
```

The command deterministically regenerates only aggregate, public-safe artifacts:

- `results/summary.json` for machine use;
- `results/summary.md` for review.

No per-replicate simulated rows are written. The result's configuration hash binds the grid, regimes, thresholds, and random seed.

## Verify

```bash
python3 -m unittest tests.test_seed_bootstrap_calibration
```

## Scope boundary

The experiment provides synthetic evidence for choosing a resampling unit and for rejecting unsupported seed floors. It reports raw estimate-sign stability, not conditional Type-S/Type-M error; the latter requires a separately preregistered analysis before this can become a general promotion policy. It also does not yet use representative public-safe rows from existing experiments or compare BCa, bootstrap-t, or randomization intervals; those remain follow-up S-022 work.
