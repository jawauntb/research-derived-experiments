# E5 generator-vs-coverage smoke

Status: **harness validation passed; confirmatory experiment pending**.

This is the preregistered minimum smoke only: Pythia-70m, `n=13`, one seed,
20 epochs, arms G-reg/Cov/A-ref. It is not scientific evidence for generator
learning or coverage.

## Exact run

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/commitment_surface/modal_e5_generator_vs_coverage.py \
  --sizes 70m --ns 13 --seeds 1 --arms G-reg,Cov,A-ref --epochs 20 \
  --out artifacts/commitment_surface/e5_smoke.json
```

- Modal run: <https://modal.com/apps/generalintelligencecompany/main/ap-rAVMHKT67O8E4MbdQYJNOm>
- Exit: 0
- Raw output: `artifacts/commitment_surface/e5_smoke.json` (gitignored)
- Frozen seed: 20260709

## Integrity evidence

- Split: 6 original train inputs and 7 disjoint held-out inputs.
- `K_train={9,10,12}`; `K_novel={1,2,3,4,5,6,7,8,11}`; intersection empty.
- G-reg: 6 supervised original-support events, **0 held-out truth-label
  events**, 27 consistency events, and 0 consistency endpoints outside train
  support.
- The complete precomputed ledger gives B-ref and Cov 27 held-out supervised
  events over 6 unique held-out inputs each.
- Every evaluated arm passed exposure integrity.
- Every nonzero LoRA matrix had target spectral-mass removal 0.50 realized
  within the preregistered ±0.02 tolerance; every evaluated arm passed patch
  integrity.
- Aggregate smoke gate: **PASS** (`integrity_pass=true`,
  `smoke_pass=true`, `confirmatory_ready=false`).

## Descriptive smoke metrics

| Arm | Canonical OOD acc. | Paraphrase OOD acc. | Novel-k equivariance | Canonical normalized patch-CE | Paraphrase normalized patch-CE |
|---|---:|---:|---:|---:|---:|
| G-reg | 0.000 | 0.000 | 0.111 | -0.141 | -0.012 |
| Cov | 0.286 | 0.000 | 0.094 | -0.017 | -0.042 |
| A-ref | 0.000 | 0.000 | 0.009 | -1.288 | -0.949 |

The analysis layer marks `verdict=pending_confirmatory_grid`. Although its
point-estimate coverage gate is true in this undertrained single-seed smoke,
the preregistration explicitly forbids promoting a smoke to a mechanism
verdict. W-reg and B-ref were not run, so group specificity and the B-ref/Cov
comparison are untested.

## Claim boundary and next test

Supported: the executable harness enforces the no-held-out-label contract,
coverage matching, novel-shift separation, paraphrase evaluation, and
spectral-mass-normalized patch audit on a real Modal/Pythia run.

Not supported: generator learning, coverage causality, group specificity,
transport, or a revision of the E4 scientific interpretation.

Next: before any expensive full grid, run a development calibration with all
five arms (still clearly non-confirmatory) to ensure 20–160 epochs can produce
non-floor canonical and paraphrase behavior, then cost the frozen three-seed
grid. Do not tune gates from that calibration.
