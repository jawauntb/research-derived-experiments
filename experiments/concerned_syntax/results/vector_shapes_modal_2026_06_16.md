# Vector Concerned-Syntax Agents

Date: 2026-06-16

Question: can learned agents pass concerned-syntax gates from generated vector surfaces without visible candidate parse features?

Manifest: 5 seeds, 3000 train trials per seed, 1200 test trials per seed, 90 SGD epochs.

## Gate Summary

| Agent | Parse high | Action | Subtree | Ambiguity | High probe | Low probe | Regret | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| concerned_vector_probe | 1.000 | 1.000 | 0.804 | 1.000 | 1.000 | 0.189 | 0.004 | PASS |
| passive_vector | 0.492 | 0.873 | 0.500 | 1.000 | 0.000 | 0.000 | 0.056 | fail |
| restless_vector_probe | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | fail |
| surface_shortcut | 0.492 | 0.876 | 0.500 | 1.000 | 0.000 | 0.000 | 0.056 | fail |

## Interpretation

The vector surface is deliberately parse-invariant: coordinates, roles, and pair salience do not encode which hidden tree is true. The accepted agent therefore cannot win by reading candidate parse descriptors. It must learn a concern-gated pair probe and use the returned binding bit. Surface shortcuts keep action priors but fail parse. Passive vector inference fails because the same surface supports multiple hidden parses. Restless vector probing recovers syntax while failing the low-concern guard.

Raw JSON remains local under `artifacts/concerned_syntax/vector_shapes_modal_sweep.json`.
