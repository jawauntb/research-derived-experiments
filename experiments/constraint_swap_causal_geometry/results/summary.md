# Constraint-Swap Causal Geometry - Registered Result

- **Decision:** `REJECT_CONSTRAINT_SPECIFIC_DEFORMATION`
- **All gates pass:** `False`
- **Independent confirmatory seeds:** `32`
- **Bootstrap resamples:** `10000`
- **Claim scope:** frozen meta-GRU, registered parity constraints, query-surface rank-4 affine transports, one torus and one cylinder.

## Noncompensatory Gates

| Gate | Status | Registered rule / failure |
| --- | --- | --- |
| `F0_integrity_identifiability` | **PASS** | registered component tests |
| `F1_competence_measurement_sensitivity` | **PASS** | registered component tests |
| `G1_constraint_specific_geometry` | **FAIL** | both active-specific lower bounds > 0.05, 28/32 positive directions, and all comparator lower bounds > 0 |
| `G2_swap_tracking` | **FAIL** | both swap lower bounds > 0.05 and no-swap drift < 0.05 |
| `G3_selective_impairment` | **FAIL** | both selective-impairment directions and preservation controls |
| `G4_selective_rescue` | **FAIL** | both selective-rescue directions and preservation controls |
| `G5_topology_transport` | **FAIL** | all transfer competence, geometry, swap, impairment, and rescue gates |

## Primary Topology Metrics

| Metric | Mean | 90% bootstrap interval |
| --- | ---: | ---: |
| Mature A accuracy | 1.000 | [1.000, 1.000] |
| Mature B accuracy | 1.000 | [1.000, 1.000] |
| Deterministic-control accuracy | 1.000 | [1.000, 1.000] |
| Randomized-sham accuracy | 0.509 | [0.500, 0.518] |
| Injected-geometry recovery lift | 0.907 | [0.864, 0.947] |
| A-specific geometry | -0.363 | [-0.436, -0.281] |
| B-specific geometry | -0.237 | [-0.315, -0.157] |
| A-to-B swap tracking | -0.594 | [-0.682, -0.504] |
| B-to-A swap tracking | -0.593 | [-0.680, -0.508] |
| Undo B selective impairment | -0.187 | [-0.222, -0.153] |
| Undo A selective impairment | -0.225 | [-0.282, -0.168] |
| Impose B selective rescue | -0.057 | [-0.096, -0.014] |
| Impose A selective rescue | -0.014 | [-0.051, 0.024] |

## Transfer Topology Metrics

| Metric | Mean | 90% bootstrap interval |
| --- | ---: | ---: |
| Mature A accuracy | 1.000 | [1.000, 1.000] |
| Mature B accuracy | 1.000 | [1.000, 1.000] |
| Deterministic-control accuracy | 1.000 | [1.000, 1.000] |
| Randomized-sham accuracy | 0.499 | [0.491, 0.508] |
| Injected-geometry recovery lift | 0.559 | [0.535, 0.583] |
| A-specific geometry | -0.222 | [-0.261, -0.178] |
| B-specific geometry | -0.079 | [-0.125, -0.032] |
| A-to-B swap tracking | -0.305 | [-0.354, -0.256] |
| B-to-A swap tracking | -0.297 | [-0.346, -0.248] |
| Undo B selective impairment | -0.204 | [-0.243, -0.164] |
| Undo A selective impairment | -0.247 | [-0.295, -0.199] |
| Impose B selective rescue | -0.034 | [-0.072, 0.006] |
| Impose A selective rescue | -0.000 | [-0.028, 0.027] |

## Discovery-Regime Audit

- **Accepted artifacts:** exact future-language enumerator, balanced constraint schedules, seed rows, nuisance audit, and positive-control measurement check where their gates pass.
- **Rejected or withheld artifacts:** every failed gate remains visible; no pooled score rescues a failed direction or topology.
- **Transported evidence:** prior task/context geometry and causal intervention literature motivated the controls but does not count as evidence that this run passed.
- **Residual content:** the final paper states the strongest surviving descriptive, swap, causal, and topology claims separately.

## Provenance

- Raw run: `artifacts/constraint_swap_causal_geometry/registered_run.json`
- Public seed rows: `experiments/constraint_swap_causal_geometry/results/registered_seed_rows.jsonl`
- Frozen manifest: `experiments/constraint_swap_causal_geometry/experiment_manifest.json`
- Preregistration: `experiments/constraint_swap_causal_geometry/PREREGISTRATION.md`
