# Intervention Mechanism Trace Gate

Date: 2026-06-17

Question: does the accepted 2A-v1 intervention policy expose a faithful program -> observation -> belief update -> action trace, while shortcuts fail for visible trace reasons?

Manifest: 5 seeds, 3000 train trials per seed, 1200 test trials per seed, 90 SGD epochs.

## Trace Gate Summary

| Agent | Trace high | Useful obs high | Posterior high | Action | Low trace violation | Target high | Regret | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| concern_without_target | 0.087 | 0.087 | 0.541 | 0.890 | 0.151 | 0.087 | 0.058 | fail |
| concerned_program_inventor | 1.000 | 1.000 | 1.000 | 1.000 | 0.151 | 1.000 | 0.004 | PASS |
| random_program_probe | 0.062 | 0.062 | 0.526 | 0.886 | 1.000 | 0.062 | 0.059 | fail |
| surface_program_shortcut | 0.000 | 0.000 | 0.496 | 0.878 | 0.000 | 0.000 | 0.063 | fail |
| target_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | fail |

## Interpretation

This is a verifier upgrade over the aggregate intervention-invention table. A passing trace must select a useful program on high-concern trials, receive an observation tied to that program, update the hidden-binding belief correctly, and act from the posterior while keeping low-concern trace violations under the no-restless cap.

`target_without_concern` can produce high-quality high-concern traces but fails by tracing/probing low-concern cases. `concern_without_target` has the concern gate but asks the wrong question. Surface and random controls fail before a faithful observation -> belief -> action chain exists.

Raw JSON remains local under `artifacts/concerned_syntax/`.
