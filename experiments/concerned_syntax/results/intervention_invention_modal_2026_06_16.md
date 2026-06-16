# Concerned Intervention Invention

Date: 2026-06-16

Question: can a pixel-level concerned-syntax agent learn both when to intervene and which object-pair probe program makes the viability-relevant hidden binding observable?

Manifest: 5 seeds, 3000 train trials per seed, 1200 test trials per seed, 90 SGD epochs, 16 probe programs, 48x48 RGB images.

## Gate Summary

| Agent | Parse high | Action | Subtree | Objects | High probe | Low probe | Target high | Useful high | Regret | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| concern_without_target | 0.534 | 0.883 | 0.522 | 1.000 | 1.000 | 0.156 | 0.088 | 0.088 | 0.054 | fail |
| concerned_program_inventor | 1.000 | 1.000 | 0.796 | 1.000 | 1.000 | 0.156 | 1.000 | 1.000 | 0.003 | PASS |
| random_program_probe | 0.519 | 0.879 | 0.530 | 1.000 | 1.000 | 1.000 | 0.060 | 0.060 | 0.056 | fail |
| surface_program_shortcut | 0.486 | 0.876 | 0.494 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.060 | fail |
| target_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | fail |

## Interpretation

This gate makes probe target selection part of the task. The agent does not receive the causal pair as metadata; it sees extracted pixel-object features and scores candidate `observe_pair(a,b)` programs. The accepted agent must choose a useful target under a concern gate. Surface shortcuts fail hidden binding, random program probes waste budget, concern without target probes at the right time but asks the wrong question, and target without concern violates the low-concern cap.

Raw JSON remains local under `artifacts/concerned_syntax/`.
