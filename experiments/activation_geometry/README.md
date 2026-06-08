# Activation Geometry

This track tests whether the concept-geometry bridges that appeared in text embeddings also appear in hidden-state geometry for open language models.

The first probe pools hidden states for paraphrased concept prompts, builds one centroid per concept, and checks whether bridge pairs such as `attractor` - `attractor_network` and `conceptual_space` - `representation_manifold` have lift over unrelated cross-category pairs.

Dry-run without model dependencies:

```bash
python3 experiments/activation_geometry/activation_geometry_probe.py --concepts experiments/concept_geometry/concept_set.json --paraphrases experiments/concept_geometry/concept_paraphrases.json --dry-run --pooling mean --out artifacts/activation_geometry/dry_run.json
```

Run locally with Transformers, when Torch and Transformers are installed:

```bash
python3 experiments/activation_geometry/activation_geometry_probe.py --concepts experiments/concept_geometry/concept_set.json --paraphrases experiments/concept_geometry/concept_paraphrases.json --model-id EleutherAI/pythia-70m-deduped --layer -1 --pooling mean --out artifacts/activation_geometry/pythia_70m_layer_last.json
```

Run on Modal through the Doppler-managed Modal token:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_activation_probe.py --model-id EleutherAI/pythia-70m-deduped --layer -1 --out artifacts/activation_geometry/modal_pythia_70m_layer_last.json
```

Run a multi-layer sweep on Modal:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_layer_sweep.py --model-id EleutherAI/pythia-70m-deduped --layers 0,1,2,3,4,5,6 --batch-size 8 --max-length 96 --pooling mean --out artifacts/activation_geometry/modal_pythia_70m_layer_sweep.json
```

For Pythia-70M, layer `0` is the embedding hidden state and layers `1..6` are transformer block outputs. Public reports should keep both raw and mean-centered metrics so anisotropy does not get hidden by a single headline score.

Run the same sweep on GPT-2 as a second-model replication:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_layer_sweep.py --model-id gpt2 --layers 0,1,2,3,4,5,6,7,8,9,10,11,12 --batch-size 8 --max-length 96 --pooling mean --out artifacts/activation_geometry/modal_gpt2_layer_sweep.json
```

Final-token pooling ablation runs:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_layer_sweep.py --model-id EleutherAI/pythia-70m-deduped --layers 0,1,2,3,4,5,6 --batch-size 8 --max-length 96 --pooling final-token --out artifacts/activation_geometry/modal_pythia_70m_layer_sweep_final_token.json
```

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_layer_sweep.py --model-id gpt2 --layers 0,1,2,3,4,5,6,7,8,9,10,11,12 --batch-size 8 --max-length 96 --pooling final-token --out artifacts/activation_geometry/modal_gpt2_layer_sweep_final_token.json
```
