# Obstruction-Aware Admission V0

**Verdict:** `ACCEPT_EXACT_FINITE_CONTROL`

## Claim boundary

The run validates an exact finite control contract. It does not validate a universal theory of agency, natural scientific discovery, or concern-gated retrieval.

## Exhaustive screen

| Quantity | Value |
|---|---:|
| Finite systems | 500,912 |
| Hidden-world episodes | 1,975,104 |
| Recoverable systems | 317,432 |
| Terminally obstructed systems | 183,480 |
| Greedy target-pair counterexamples | 26,304 |
| Mathematical disagreements | 0 |
| Recovery failures | 0 |
| Certificate failures | 0 |

## Minimal greedy counterexample

- Worlds: `['r0', 'r1', 'r2', 'r3']`
- Experiments: `['e0', 'e1']`
- Outcomes: `[[1, 1], [1, 0], [0, 0], [0, 0]]`
- Target: `[1, 0, 0, 0]`
- Costs: `[1, 2]`
- Exact versus greedy worst-case cost: `2` versus `3`
- First experiment: exact `e1`, greedy `e0`

The cheaper experiment separates more target-distinct pairs per unit cost immediately, but its hard branch still requires the expensive experiment. The exact policy buys the expensive experiment first and identifies the target in one step.

## Gate verdicts

| Gate | Status |
|---|---|
| G0_OBJECT_INTEGRITY | PASS |
| G1_MATHEMATICAL_AGREEMENT | PASS |
| G2_RECOVERY_SOUNDNESS | PASS |
| G3_CERTIFICATE_SOUNDNESS | PASS |
| G4_ORACLE_DOMINANCE | PASS |
| G5_TERMINATION_SEPARATION | PASS |
| G6_INVARIANCE | PASS |
| G7_GREEDY_FALSIFIER | PASS |
| G8_LEGACY_EVIDENCE_INTEGRITY | PASS |
| G9_PROVENANCE | PASS |

## Reproduce

```bash
uv run --no-sync python -m experiments.obstruction_aware_admission.run_benchmark
```

Source digest: `ec7902ae10f8097536b52779205263bad1ed78a19809a860c0a1c5a36b2c425b`
