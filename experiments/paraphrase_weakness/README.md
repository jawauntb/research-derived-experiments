# Paraphrase Weakness

Tests whether **per-concept paraphrase-invariance of a model's hidden states**
predicts **per-concept behavioral consistency** under paraphrase substitution.
This is the language-domain follow-on to the cyclic-symmetry result in
`experiments/symbolic_weakness`.

## Setup

We reuse the 24 concepts × 3 paraphrase variants in
`experiments/concept_geometry/concept_paraphrases.json`. For each concept we
treat the three variants as an approximate "paraphrase orbit." For a small
open-source language model (Pythia-70M or GPT-2), we extract:

- per-layer mean-pooled hidden states for each variant;
- next-token argmax logits for each variant.

We then compute:

- **paraphrase weakness** = mean pairwise cosine similarity between hidden
  states of the same concept's variants (analogous to in-orbit invariance);
- **control cosine** = mean cosine similarity between a variant of concept
  *c* and variants of *other* concepts (a wrong-orbit control);
- **behavioral consistency** = fraction of variant-pairs whose next-token
  argmax predictions agree.

The headline question is whether per-concept layer-level weakness predicts
per-concept behavioral consistency.

## Run

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/paraphrase_weakness/modal_paraphrase_probe.py \
    --model-id EleutherAI/pythia-70m-deduped \
    --out artifacts/paraphrase_weakness/pythia_70m.json

python3 -m experiments.paraphrase_weakness.summarize \
    --in artifacts/paraphrase_weakness/pythia_70m.json \
    --out experiments/paraphrase_weakness/results/pythia_70m_summary.md
```

## Files

| File | Purpose |
| --- | --- |
| `modal_paraphrase_probe.py` | Modal entrypoint; loads model, extracts per-layer hidden states for every variant, returns weakness/control/behavior summaries. |
| `summarize.py` | Reads the probe JSON and emits a markdown table of per-layer paraphrase weakness, wrong-orbit control, and Pearson/Spearman correlations with behavior. |
| `results/` | Result reports (gated, pre-registered). |
