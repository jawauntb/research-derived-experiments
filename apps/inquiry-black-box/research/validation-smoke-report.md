# Inquiry Validation Smoke Report

Run ID: `fixture-smoke`
Generated from fixture timestamp: `2026-07-07T14:00:07.300Z`

This artifact is a smoke validation report for R15 / AE7. It does not make state-prediction claims.

## Export To Validation Rows

| Row kind | Count |
| --- | ---: |
| behavior_marker | 9 |
| camera_quality_flag | 1 |
| label | 2 |
| probe | 2 |
| repair_outcome | 2 |
| stimulus_segment | 3 |

## G0 Reliability Ceiling

Status: `smoke`
Repeated targets: 3
Mean agreement: 1.00

Fixture repeats are internally consistent, but this is only a smoke ceiling; collect real repeated labels, probes, and outcomes before modeling.

## G1 Stimulus-Only Baseline

Status: `smoke`
Top segment: `demo-article:2`
Hit@1: yes

| Segment | Score | Density | Term novelty | Transitions | Quiz checkpoint |
| --- | ---: | ---: | ---: | ---: | --- |
| demo-article:2 | 0.82 | 0.82 | 0.74 | 4 | yes |
| demo-article:1 | 0.39 | 0.42 | 0.38 | 1 | no |
| demo-article:3 | 0.33 | 0.35 | 0.31 | 1 | no |

| Negative control | Top segment | Hit@1 | Note |
| --- | --- | --- | --- |
| shuffled-segment-order | demo-article:3 | no | Deterministic one-step rotation assigns feature scores to the wrong segment IDs. |
| shifted-boundaries | demo-article:2 | yes | Targets are re-associated after shifting segment windows by half a segment. |

## G2-G4 Residual Gates

G2 browser residual: `insufficient-data` - Do not claim browser-behavior residual value from fixture smoke; collect held-out sessions and compare against G1.
G3 camera residual: `insufficient-data` - Camera features remain weak auxiliary metadata; fixture smoke only proves quality flags can be tabulated.
G4 repair utility: `insufficient-data` - Repair outcomes are present as smoke rows, but utility needs a comparison group before keep/drop decisions.

## Privacy Checks

Uses raw camera frames: false
Uses raw typed content: false
