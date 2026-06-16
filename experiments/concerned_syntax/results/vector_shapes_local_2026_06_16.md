# Vector Concerned-Syntax Agents

Date: 2026-06-16

Question: can learned agents pass concerned-syntax gates from generated vector surfaces without visible candidate parse features?

Manifest: 1200 train trials, 500 test trials, seed 20260616, 60 SGD epochs.

## Gate Summary

| Agent | Parse high | Action | Subtree | Ambiguity | High probe | Low probe | Regret | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| concerned_vector_probe | 1.000 | 1.000 | 0.788 | 1.000 | 1.000 | 0.190 | 0.000 | PASS |
| passive_vector | 0.532 | 0.866 | 0.494 | 1.000 | 0.000 | 0.000 | 0.047 | fail |
| restless_vector_probe | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | fail |
| surface_shortcut | 0.532 | 0.868 | 0.494 | 1.000 | 0.000 | 0.000 | 0.047 | fail |

## Interpretation

The vector surface is deliberately parse-invariant: coordinates, roles, and pair salience do not encode which hidden tree is true. The accepted agent therefore cannot win by reading candidate parse descriptors. It must learn a concern-gated pair probe and use the returned binding bit. Surface shortcuts keep action priors but fail parse. Passive vector inference fails because the same surface supports multiple hidden parses. Restless vector probing recovers syntax while failing the low-concern guard.

Raw JSON remains local under `artifacts/concerned_syntax/vector_shapes_modal_sweep.json`.
