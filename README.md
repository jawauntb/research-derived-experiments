# Research Derived Experiments

This repository tracks a research program around a recurring pattern:

> adaptive systems keep rediscovering geometric language because geometry is the portable language of constraints.

The first synthesis is in [notes/geometric_convergence_research_synthesis.md](notes/geometric_convergence_research_synthesis.md). The working question:

**Why do independently developed systems of thought and computation keep converging on geometric descriptions of meaning, agency, and intelligence, and can we predict when that geometry is merely a passive representation versus when it becomes an active, self-maintaining attractor regime?**

## Public Artifact Policy

The repo is public-safe by design:

- Published: notes, source manifests, experiment code, result reports, audit cards, and rejected alternatives.
- Local only: downloaded PDFs, extracted full text, HTML snapshots, secrets, and raw model outputs unless intentionally summarized.

The local archive lives under ignored folders:

- `references/papers/`
- `references/text/`
- `references/html/`

Use [references/SOURCES.md](references/SOURCES.md) to recreate or inspect the source list.

## Research Loop

We use the `scientific-discovery-regime-audit` skill as the process wrapper:

1. Define the current representational regime.
2. Pre-register the gate before an experiment.
3. Preserve accepted and rejected artifacts.
4. Distinguish retrieval, search, and discovery.
5. Record residual content that the current regime cannot explain.

The current ledger is [TODO.md](TODO.md). Audit cards live in [docs/discovery_regime_audit.md](docs/discovery_regime_audit.md). The Phase 2 breakthrough trajectory is [docs/phase2_breakthrough_trajectory.md](docs/phase2_breakthrough_trajectory.md). The latest start-here handoff for next breakthrough work is [docs/phase2_next_breakthrough_handoff.md](docs/phase2_next_breakthrough_handoff.md), with the longer historical continuation brief at [docs/phase2_next_agent_handoff.md](docs/phase2_next_agent_handoff.md).

## Experiments

Current experiment families:

- [experiments/weakness_vs_simplicity](experiments/weakness_vs_simplicity): synthetic tests for the claim that generalization is driven by weak compatible constraints rather than shortest forms.
- [experiments/symbolic_weakness](experiments/symbolic_weakness): flagship multi-family symbolic + neural benchmark for the claim that **symmetry-compatible-hypothesis weakness predicts OOD generalization** where simplicity, MDL, compression, sharpness, parameter norm, and held-out validation do not. Paper draft at [papers/weakness_invariance_neurips/paper.md](papers/weakness_invariance_neurips/paper.md).
- [experiments/concept_geometry](experiments/concept_geometry): model-backed probes for whether attractors, conceptual spaces, activation geometry, constraints, and agency terms occupy related embedding neighborhoods.
- [experiments/activation_geometry](experiments/activation_geometry): open-model hidden-state probes for whether the same bridge geometry appears beyond embedding-only language space.
- [experiments/concerned_syntax](experiments/concerned_syntax): Arc 2A benchmark for causal constituency and concern-gated intervention invention. Paper draft at [papers/concerned_syntax/paper.md](papers/concerned_syntax/paper.md).
- [experiments/viable_computational_bodies](experiments/viable_computational_bodies): Arc 2B typed architecture/body evolution under viability, formal, and concerned-syntax gates. Paper draft at [papers/viable_computational_bodies/paper.md](papers/viable_computational_bodies/paper.md).

Run the first pilot:

```bash
python3 experiments/weakness_vs_simplicity/experiment.py --trials 500 --seed 7 --out artifacts/weakness_vs_simplicity/pilot.json
python3 experiments/weakness_vs_simplicity/experiment.py --trials 500 --seed 7 --no-memorizer --out artifacts/weakness_vs_simplicity/no_memorizer_control.json
python3 experiments/weakness_vs_simplicity/experiment.py --trials 500 --seed 7 --no-memorizer --include-broad-negative-excluder --out artifacts/weakness_vs_simplicity/broad_negative_excluder_stress.json
python3 experiments/weakness_vs_simplicity/experiment.py --trials 500 --seed 7 --no-memorizer --include-broad-negative-excluder --validation-negatives 6 --out artifacts/weakness_vs_simplicity/validated_weakness_stress.json
python3 experiments/symbolic_weakness/experiment.py --trials 300 --seed 11 --out artifacts/symbolic_weakness/prefix_shift_pilot.json
```

Flagship multi-family symbolic + neural benchmark:

```bash
# Multi-family symbolic benchmark (4 families × 500 trials × 11 selectors)
python3 -m experiments.symbolic_weakness.benchmark \
    --trials-per-family 500 --seed 20260609 \
    --out artifacts/symbolic_weakness/multi_family_500.json

# 256-model neural sweep
python3 -m experiments.symbolic_weakness.neural \
    --n-models 256 --epochs 2000 --base-seed 20260609 \
    --out artifacts/symbolic_weakness/neural_sweep_v3.json

# Modal-parallel neural sweep (Doppler-scoped Modal credentials)
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/symbolic_weakness/modal_neural_sweep.py \
    --n-shards 8 --models-per-shard 64 --epochs 2000 \
    --out artifacts/symbolic_weakness/modal_neural_sweep.json

# Phase / Arc 2A concerned-syntax benchmark
python3 -m experiments.concerned_syntax.benchmark \
    --trials 200 --seed 20260616 \
    --out artifacts/concerned_syntax/pilot.json \
    --report experiments/concerned_syntax/results/pilot_2026_06_16.md

doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/concerned_syntax/modal_concerned_syntax_sweep.py \
    --trials 1000

doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/concerned_syntax/modal_learned_agents_sweep.py \
    --train-trials 3000 --test-trials 1200 --epochs 90

doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/concerned_syntax/modal_vector_shapes_sweep.py \
    --train-trials 3000 --test-trials 1200 --epochs 90

python3 -m experiments.concerned_syntax.pixel_shapes \
    --train-trials 1200 --test-trials 500 --seed 20260616 --epochs 60 \
    --out artifacts/concerned_syntax/pixel_shapes_local.json \
    --agent-report experiments/concerned_syntax/results/pixel_shapes_local_2026_06_16.md

python3 -m experiments.concerned_syntax.intervention_invention \
    --train-trials 1200 --test-trials 500 --seed 20260616 --epochs 60 \
    --out artifacts/concerned_syntax/intervention_invention_local.json \
    --agent-report experiments/concerned_syntax/results/intervention_invention_local_2026_06_16.md

doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/concerned_syntax/modal_intervention_invention_sweep.py \
    --train-trials 3000 --test-trials 1200 --epochs 90

python3 -m experiments.concerned_syntax.mechanism_trace \
    --train-trials 1200 --test-trials 500 --seed 20260617 --epochs 60 \
    --out artifacts/concerned_syntax/mechanism_trace_local.json \
    --trace-report experiments/concerned_syntax/results/mechanism_trace_local_2026_06_17.md

doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/concerned_syntax/modal_mechanism_trace_sweep.py \
    --train-trials 3000 --test-trials 1200 --epochs 90

python3 -m experiments.concerned_syntax.searched_program_policy \
    --train-trials 1200 --test-trials 500 --seed 20260617 --epochs 60 \
    --search-trials 600 \
    --out artifacts/concerned_syntax/searched_program_policy_local.json \
    --agent-report experiments/concerned_syntax/results/searched_program_policy_local_2026_06_17.md

doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/concerned_syntax/modal_searched_program_policy_sweep.py \
    --train-trials 3000 --test-trials 1200 --epochs 90 \
    --search-trials 600

python3 -m experiments.concerned_syntax.rich_program_language \
    --train-trials 1200 --test-trials 500 --seed 20260617 --epochs 60 \
    --out artifacts/concerned_syntax/rich_program_language_local.json \
    --agent-report experiments/concerned_syntax/results/rich_program_language_local_2026_06_17.md

doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/concerned_syntax/modal_rich_program_language_sweep.py \
    --train-trials 3000 --test-trials 1200 --epochs 90

doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/concerned_syntax/modal_intervention_transfer_sweep.py \
    --train-trials 3000 --test-trials 1200 --epochs 90

doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/concerned_syntax/modal_pixel_shapes_sweep.py \
    --train-trials 3000 --test-trials 1200 --epochs 90

python3 -m experiments.concerned_syntax.learned_pixel_extractor \
    --train-trials 1200 --test-trials 500 --seed 20260617 --epochs 60 \
    --extractor-samples-per-image 96 \
    --out artifacts/concerned_syntax/learned_pixel_extractor_local.json \
    --agent-report experiments/concerned_syntax/results/learned_pixel_extractor_local_2026_06_17.md

doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/concerned_syntax/modal_learned_pixel_extractor_sweep.py \
    --train-trials 3000 --test-trials 1200 --epochs 90 \
    --extractor-samples-per-image 96

# Phase / Arc 2B viable computational bodies benchmark
python3 -m experiments.viable_computational_bodies.search \
    --seeds 12 --generations 18 --population 18 --base-seed 20260616 \
    --out artifacts/viable_computational_bodies/pilot.json \
    --report experiments/viable_computational_bodies/results/pilot_2026_06_16.md

doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/viable_computational_bodies/modal_body_evolution_sweep.py \
    --generations 32 --population 32

doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/viable_computational_bodies/modal_program_body_search.py \
    --generations 24 --population 24 \
    --train-trials 3000 --test-trials 1200 --epochs 90

python3 -m experiments.viable_computational_bodies.program_body_search \
    --seed-list 20260616,1729,4242,8675309,314159 \
    --generations 18 --population 18 \
    --train-trials 1200 --test-trials 500 --epochs 60 \
    --formal-mode haskell \
    --out artifacts/viable_computational_bodies/program_body_search_haskell_local.json \
    --report experiments/viable_computational_bodies/results/program_body_search_haskell_local_2026_06_16.md

# Phase / Arc 2B executable body validation is produced by the learned 2A sweep:
# experiments/viable_computational_bodies/results/executable_bodies_modal_2026_06_16.md

# Phase / Arc 2B vector module validation is produced by the vector 2A sweep:
# experiments/viable_computational_bodies/results/vector_module_bodies_modal_2026_06_16.md

# Haskell typed ontology gate prototype
(
  cd formal/ontology-hs && cabal test all && cabal run ontology-check
)
```

## Environment

Do not commit secrets. To check whether an environment context has the needed keys:

```bash
python3 scripts/env_probe.py
```

When running under Doppler:

```bash
doppler run -- python3 scripts/env_probe.py
```

Expected useful variables include `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and Modal-related keys such as `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, or a preconfigured local Modal profile.

## Checks

Before committing:

```bash
python3 scripts/run_quality_checks.py
```

The wrapper runs the full test suite under Python 3.12 via `uvx` with the
ephemeral scientific dependencies required by tests, then runs compile checks,
the publication guard, ruff, and ty. To run the individual checks manually:

```bash
uvx --python 3.12 --with torch --with numpy --with scikit-learn python -m unittest discover -s tests
uvx --python 3.12 python -m compileall scripts experiments tests
python3 scripts/publication_guard.py
uvx ruff check .
uvx ty check scripts experiments tests
```
