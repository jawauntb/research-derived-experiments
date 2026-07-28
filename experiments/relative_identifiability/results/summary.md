# Relative Identifiability Regression Summary

**Python fixture verdict:** `PASS`

**Fixture SHA-256:** `800c76501a2b810779c13741d3820e446fd4dfd2b300c697c845dcea4f9b35c7`

## Target-identification cases

| Case | Expected | Observed | Pass |
|---|---|---|---|
| behavior_from_external_readout | identifiable | identifiable | yes |
| mechanism_obstructed_externally | obstructed | obstructed | yes |
| mechanism_identified_by_internal_patch | identifiable | identifiable | yes |
| coordinate_gauge_obstructed_externally | obstructed | obstructed | yes |
| constant_target_needs_no_experiments | identifiable | identifiable | yes |

## Experiment-family refinements

| Case | Expected strict | Observed strict | Pass |
|---|---:|---:|---|
| internal_patch_strictly_refines_external_behavior | true | true | yes |
| duplicate_readout_is_redundant | false | false | yes |

The external-only mechanism and coordinate cases are expected
obstructions. Their `PASS` status means the engine produced the
registered counterexample; it does not mean those targets were
identified.
