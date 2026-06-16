# Concerned Intervention Invention

Date: 2026-06-16

Question: can a pixel-level concerned-syntax agent learn both when to intervene and which object-pair probe program makes the viability-relevant hidden binding observable?

Manifest: 1200 train trials, 500 test trials, seed 20260616, 60 SGD epochs, 16 probe programs, 48x48 RGB images.

## Gate Summary

| Agent | Parse high | Action | Subtree | Objects | High probe | Low probe | Target high | Useful high | Regret | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| concern_without_target | 0.566 | 0.876 | 0.540 | 1.000 | 1.000 | 0.135 | 0.105 | 0.105 | 0.062 | fail |
| concerned_program_inventor | 1.000 | 0.982 | 0.790 | 1.000 | 1.000 | 0.135 | 1.000 | 1.000 | 0.006 | PASS |
| random_program_probe | 0.527 | 0.860 | 0.530 | 1.000 | 1.000 | 1.000 | 0.047 | 0.047 | 0.063 | fail |
| surface_program_shortcut | 0.516 | 0.844 | 0.514 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.066 | fail |
| target_without_concern | 1.000 | 0.982 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | fail |

## Interpretation

This gate makes probe target selection part of the task. The agent does not receive the causal pair as metadata; it sees extracted pixel-object features and scores candidate `observe_pair(a,b)` programs. The accepted agent must choose a useful target under a concern gate. Surface shortcuts fail hidden binding, random program probes waste budget, concern without target probes at the right time but asks the wrong question, and target without concern violates the low-concern cap.

Raw JSON remains local under `artifacts/concerned_syntax/`.
