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

The current ledger is [TODO.md](TODO.md). Audit cards live in [docs/discovery_regime_audit.md](docs/discovery_regime_audit.md).

## Experiments

Current experiment families:

- [experiments/weakness_vs_simplicity](experiments/weakness_vs_simplicity): synthetic tests for the claim that generalization is driven by weak compatible constraints rather than shortest forms.
- [experiments/symbolic_weakness](experiments/symbolic_weakness): cyclic-symbol symmetry benchmark where training loss, simplicity, compression, and a flatness proxy tie or fail, while invariant weakness predicts OOD generalization.
- [experiments/concept_geometry](experiments/concept_geometry): model-backed probes for whether attractors, conceptual spaces, activation geometry, constraints, and agency terms occupy related embedding neighborhoods.
- [experiments/activation_geometry](experiments/activation_geometry): open-model hidden-state probes for whether the same bridge geometry appears beyond embedding-only language space.

Run the first pilot:

```bash
python3 experiments/weakness_vs_simplicity/experiment.py --trials 500 --seed 7 --out artifacts/weakness_vs_simplicity/pilot.json
python3 experiments/weakness_vs_simplicity/experiment.py --trials 500 --seed 7 --no-memorizer --out artifacts/weakness_vs_simplicity/no_memorizer_control.json
python3 experiments/weakness_vs_simplicity/experiment.py --trials 500 --seed 7 --no-memorizer --include-broad-negative-excluder --out artifacts/weakness_vs_simplicity/broad_negative_excluder_stress.json
python3 experiments/weakness_vs_simplicity/experiment.py --trials 500 --seed 7 --no-memorizer --include-broad-negative-excluder --validation-negatives 6 --out artifacts/weakness_vs_simplicity/validated_weakness_stress.json
python3 experiments/symbolic_weakness/experiment.py --trials 300 --seed 11 --out artifacts/symbolic_weakness/prefix_shift_pilot.json
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
python3 -m unittest discover -s tests
python3 -m compileall scripts experiments tests
python3 scripts/publication_guard.py
```

When available, also run:

```bash
uvx ruff check .
uvx ty check scripts experiments tests
```
