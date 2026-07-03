# Modal Result: Transformer L4 Horizon Stress

Run date: 2026-07-02

Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-OmnjVT3ijNCUik7k98HeVn

## Configuration

- GPU: Modal `L4`
- Cells: 96 (`transformer` only, 2 conditions, 4 moved critical slots, 4 seeds, 3 sequence lengths)
- Sequence lengths: 128, 256, 384
- Train steps: 700
- Batch size: 256
- Hidden size: 64
- Max containers: 32
- Timeout guard: 900 seconds per cell
- Conservative timeout-based budget cap: `$25.89`
- User budget supplied to runner: `$50.00`
- Mean remote cell runtime: 25.15 seconds
- Mean runtime by sequence length: 128 -> 9.17s, 256 -> 24.49s, 384 -> 41.80s

## Gate Summary

| Group | Accuracy | Memory specificity z | 95% CI | Rank | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| bottleneck/transformer | 1.000 | +2.309 | [+2.309, +2.309] | 0.875 | pass |
| visible_control/transformer | 1.000 | -0.000 | [-0.389, +0.361] | 0.500 | pass |

## Horizon Gates

| Horizon | Condition | Accuracy | Memory specificity z | 95% CI | Rank | Gate |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 128 | bottleneck | 1.000 | +2.309 | [+2.309, +2.309] | 0.875 | pass |
| 256 | bottleneck | 1.000 | +2.309 | [+2.309, +2.309] | 0.875 | pass |
| 384 | bottleneck | 1.000 | +2.309 | [+2.309, +2.309] | 0.875 | pass |
| 128 | visible_control | 1.000 | -0.000 | [-0.691, +0.637] | 0.500 | pass |
| 256 | visible_control | 1.000 | -0.000 | [-0.648, +0.613] | 0.500 | pass |
| 384 | visible_control | 1.000 | +0.000 | [-0.670, +0.630] | 0.500 | pass |

## Regime Audit

- Old regime: single-horizon synthetic sequence task at length 128, with moved critical slot, visible-control null, and final hidden-state sensitivity gates.
- Transition: horizon-stressed delay lengths while preserving the same early clue geometry, moved-slot intervention, model class, and gate set.
- Transported evidence: the original transformer gates still pass, and the visible-control null remains the negative control.
- Rejected alternative: spending on the GRU path is still not the fastest route; the 700-step GRU calibration remained at chance in the prior report.
- Residual finding: the moved-bottleneck signal is not just a 128-token artifact; it survives longer post-clue delays through length 384.
- Readiness: synthetic transformer long-horizon result is ready; architecture generality and naturalistic tool-use remain untested.
- Allowed claim: future control relevance can move final memory-state metric sensitivity in a finite transformer sequence agent across tested horizon lengths.
- Next operation: move from synthetic sequence memory to tool/API agents where the future-critical constraint is a delayed tool, commitment, or external state variable.

## Interpretation Boundary

This strengthens the synthetic-agent claim from a single-length result to a
short horizon family. It is still not a production-agent, human-behavior, GRU,
or consciousness claim.
