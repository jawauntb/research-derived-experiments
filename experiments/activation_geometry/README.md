# Activation Geometry

This track tests whether the concept-geometry bridges that appeared in text embeddings also appear in hidden-state geometry for open language models.

The first probe pools hidden states for paraphrased concept prompts, builds one centroid per concept, and checks whether bridge pairs such as `attractor` - `attractor_network` and `conceptual_space` - `representation_manifold` have lift over unrelated cross-category pairs.

Dry-run without model dependencies:

```bash
python3 experiments/activation_geometry/activation_geometry_probe.py --concepts experiments/concept_geometry/concept_set.json --paraphrases experiments/concept_geometry/concept_paraphrases.json --dry-run --out artifacts/activation_geometry/dry_run.json
```

Run locally with Transformers, when Torch and Transformers are installed:

```bash
python3 experiments/activation_geometry/activation_geometry_probe.py --concepts experiments/concept_geometry/concept_set.json --paraphrases experiments/concept_geometry/concept_paraphrases.json --model-id EleutherAI/pythia-70m-deduped --layer -1 --out artifacts/activation_geometry/pythia_70m_layer_last.json
```

Run on Modal through the Doppler-managed Modal token:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_activation_probe.py --model-id EleutherAI/pythia-70m-deduped --layer -1 --out artifacts/activation_geometry/modal_pythia_70m_layer_last.json
```
