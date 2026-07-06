# ICML/Benchmark-Style Package: Proxy-Resistant Finite-Agent Benchmarks

This folder turns the short causally grounded agents note into a standalone
paper package. It should be developed separately from the structure-compatible
model-selection paper.

## Working Title

Proxy-Resistant Benchmarks for Causally Grounded Finite Agents

## Core Claim

Final success is insufficient evidence that an agent is grounded. A suite should
pass only when all three are true:

1. the behavior gate passes,
2. a suite-specific causal/structure gate passes, and
3. anti-cheat controls pass.

## Current Scope

The package centers two hardened anchors:

- **Suite C:** re-engagement under world change, including the learned probe
  transfer.
- **Suite D/E:** long-horizon moved bottleneck, tool commitment, repair,
  generated action, causal patching, and API behavior surfaces.

Suites A/B/F appear as appendix/background, not as equal-weight main claims.

## Files

- `paper.tex`: standalone benchmark paper draft.
- `appendix.tex`: suite details, release schema, limitations, and reproducibility.
- `references.bib`: external bibliography for agent/eval/safety framing.
- `release_example.json`: minimal public summary schema example.
- `figures_manifest.md`: main and appendix figure plan.
- `release_checklist.md`: benchmark-package readiness checklist.

## Source Evidence

- `docs/causally_grounded_agents_benchmark.md`
- `docs/causally_grounded_agents_release_schema.md`
- `docs/causally_grounded_agents_release_schema.json`
- `experiments/world_responds/results/suite_c_reengagement_2026_07_06.md`
- `experiments/world_responds/results/suite_c_neural_transfer_2026_07_06.md`
- `experiments/long_horizon_bottleneck/BENCHMARK_CARD.md`

## Non-Claims

This benchmark package does not certify consciousness, production reliability,
human or biological validity, broad autonomy, or universal OOD robustness.

