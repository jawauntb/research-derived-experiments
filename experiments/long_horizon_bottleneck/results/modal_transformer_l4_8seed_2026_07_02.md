# Modal Result: Transformer L4 8-Seed Moved Bottleneck

Run date: 2026-07-02

Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-i0kidQLaUrPkUNMBLiG7Nf

## Configuration

- GPU: Modal `L4`
- Cells: 64 (`transformer` only, 2 conditions, 4 moved critical slots, 8 seeds)
- Sequence length: 128
- Train steps: 700
- Batch size: 256
- Hidden size: 64
- Max containers: 32
- Timeout guard: 900 seconds per cell
- Conservative timeout-based budget cap: `$17.26`
- User budget supplied to runner: `$25.00`
- Mean remote cell runtime: 9.07 seconds
- Max remote cell runtime: 9.45 seconds

## Gate Summary

| Group | Accuracy | Memory specificity z | 95% CI | Rank | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| bottleneck/transformer | 1.000 | +2.309 | [+2.309, +2.309] | 0.875 | pass |
| visible_control/transformer | 1.000 | +0.000 | [-0.466, +0.471] | 0.500 | pass |

Pooled bottleneck passes all registered gates:

- G1 behavior: pass, mean accuracy 1.000
- G2 metric transport: pass, specificity CI lower bound > 0
- G3 rank: pass, rank percentile 0.875 > 0.50
- G4 visible-control null: pass, visible-control mean specificity < 0.50

## Interpretation Boundary

This is a positive synthetic-agent result for the transformer setting: final
memory-state sensitivity follows the moved future-critical slot while staying
near zero when the final answer is visible at the query token.

It is not yet a claim about GRUs, production LLM agents, natural tool use, or
consciousness. A same-cost GRU calibration at 700 steps stayed at chance, so the
fastest cheap path is transformer-only first, followed by GRU/curriculum
diagnostics if the architecture contrast becomes scientifically important.

## Calibration Runs

- Smoke run, 8 GRU cells at 120 steps: https://modal.com/apps/generalintelligencecompany/main/ap-VKRJFP2uuTh0l9URjNfNV1
- GRU bottleneck slot-0 calibration, 700 steps: https://modal.com/apps/generalintelligencecompany/main/ap-qBzbECRpMLLgqSVVMEPqYw
- Transformer bottleneck slot-0 calibration, 700 steps: https://modal.com/apps/generalintelligencecompany/main/ap-hVQTHkpAdEhSVzM0OW9Hlg
