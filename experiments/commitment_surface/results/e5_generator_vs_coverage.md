# E5 — Generator Learning vs Labeled Orbit Coverage

**Strict verdict: `coverage`.**

The E4 lift is best explained by correctly labeled deployment-support coverage; the transportable-generator interpretation is materially weakened.

## Per-arm confirmatory means

| Arm | Canonical OOD | Paraphrase OOD | Novel-k equivariance | Canonical patch-CE | Paraphrase patch-CE |
|---|---:|---:|---:|---:|---:|
| G-reg | 0.063 | 0.000 | 0.268 | -0.660 | -0.554 |
| B-ref | 0.741 | 0.044 | 0.741 | -0.078 | -0.841 |
| W-reg | 0.030 | 0.011 | 0.215 | -0.393 | -0.284 |
| Cov | 0.741 | 0.055 | 0.755 | 0.004 | -0.798 |
| A-ref | 0.069 | 0.000 | 0.272 | -2.637 | -2.954 |

## Frozen gates

- Exact 135-cell grid and integrity: **PASS**.
- Generator-learning gate: **FAIL**.
- Coverage gate: **PASS**.
- Mixed-mechanism gate: **FAIL**.
- Group-specificity gate: **FAIL**.
- Transport gate: **FAIL**.

## Key contrasts

- G-reg − A-ref canonical OOD: `-0.006`.
- G-reg − Cov canonical OOD: `-0.678`.
- G-reg − A-ref novel-k equivariance: `-0.004`.
- Paraphrase lift retained: `not evaluated`.

## Claim boundary

This result adjudicates the frozen Pythia modular-addition E5 mechanism contrast. It does not establish the same mechanism in language, vision, other groups, or open-world deployment.

Source manifest: `f7af4f65f5a402886002dac9a65faaefd8e6ffc845efe6ebce8a20c9bc710e9e`.
