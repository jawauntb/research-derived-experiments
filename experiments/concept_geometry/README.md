# Concept Geometry

This track tests whether independently named concepts from mathematics, cognitive science, linguistics, AI interpretability, and agency/self-boundary research occupy related neighborhoods in model embedding spaces.

The first probe uses OpenAI text embeddings over a small curated concept set. Raw embeddings stay local in `artifacts/`; committed files should contain only manifests, summary metrics, nearest-neighbor summaries, and audit cards.

Run under Doppler:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- python3 experiments/concept_geometry/openai_embedding_probe.py --concepts experiments/concept_geometry/concept_set.json --out artifacts/concept_geometry/openai_embedding_probe.json
```

Dry-run without API access:

```bash
python3 experiments/concept_geometry/openai_embedding_probe.py --concepts experiments/concept_geometry/concept_set.json --dry-run --out artifacts/concept_geometry/dry_run.json
```
