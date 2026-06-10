# Paraphrase Substitution Group Discovery

Date: 2026-06-09

## Question

Does the rotation-group discovery procedure from learned-symmetry-discovery
translate to language? Specifically: can we infer the set of
meaning-preserving single-word substitutions from a paraphrase corpus,
and does that "learned substitution group" produce a behavioral
invariance signal on a small language model?

## Setup

24 concepts × 3 paraphrase variants from
`experiments/concept_geometry/concept_paraphrases.json`. Model:
Pythia-70m-deduped.

Procedure:

1. Enumerate one-word substitutions (w_a → w_b) from observed word
   deltas between paraphrase variants of the same concept.
2. Score each substitution by averaging centered Pythia-70M layer-5
   hidden-state cosine similarity between substituted sentence and the
   closest same-concept variant.
3. Keep substitutions with score ≥ τ.
4. Evaluate behavioral invariance: fraction of (base, substituted) pairs
   whose next-token argmax predictions agree.

Manifests:

- v1: `doppler run -- uvx modal run experiments/paraphrase_weakness/modal_learned_substitution.py --model-id EleutherAI/pythia-70m-deduped --sim-layer 5 --threshold 0.30 --out artifacts/paraphrase_weakness/learned_substitution_v1.json`
- v2: same but `--threshold 0.88`

## Gate

Acceptance:

- Learned-substitution behavioral invariance must exceed random by at
  least 5 pp at *some* threshold.

Withheld:

- No claim that the procedure works at LLM scale.
- No claim that it works for multi-word paraphrases.
- No claim that it transfers without threshold calibration.

## Result

| Run | Threshold τ | Kept / Candidates | Learned behavior | Random behavior | Gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| v1 | 0.30 | 8382 / 8392 (99.9%) | 0.861 | 0.861 | +0.000 |
| v2 | 0.88 | 98 / 8392 (1.2%) | 0.892 | 0.880 | +0.012 |

**Gate failed**: the largest gap is +1.2 pp, well below the 5 pp
acceptance threshold.

## Audit

Accepted:

- v2 *does* show a positive learned > random gap (0.892 vs 0.880). The
  procedure is not degenerate at high threshold.
- The procedure surfaces some legitimate paraphrase pairs (tendency ↔
  preference, set ↔ region, compact ↔ shorter) in the top-scored
  substitutions.

Rejected:

- v1 (τ = 0.3) is degenerate: 99.9% of candidates pass, no
  discrimination. This is the immediate methodology lesson.
- Even at v2's high threshold, the top-scored substitutions include
  clear errors (`high-dimensional → that`, `lower-dimensional → surface`,
  `high-dimensional → captures`) at near-identical scores to legitimate
  paraphrase pairs. The centered-cosine scoring is dominated by
  unchanged sentence content, not the substitution itself.
- The procedure fails the acceptance gate (gap +1.2 pp < 5 pp).

Residual content:

- The cyclic-rotation procedure works on vision because (a) the candidate
  set is small (24 angles) and (b) the rotation acts on all of the input
  simultaneously, so the similarity score reflects the rotation cleanly.
- Single-word substitution acts on a small fraction of the input
  (1 of ~10 tokens). Whole-sentence cosine smooths this out. A
  *substitution-local* score (e.g., per-token logit shift, or
  contrastive same-concept-vs-other-concept score) is the natural fix
  and is the obvious next experiment.

## Top 10 learned substitutions (v2, τ = 0.88)

| from | to | score |
| --- | --- | ---: |
| tendency | preference | 0.912 |
| surface | lower-dimensional | 0.904 |
| lower-dimensional | that | 0.901 |
| compact | shorter | 0.900 |
| tendency | shorter | 0.898 |
| high-dimensional | captures | 0.897 |
| set | region | 0.897 |
| preference | tendency | 0.897 |
| lower-dimensional | surface | 0.896 |
| surface | high-dimensional | 0.896 |

Note the mix of legitimate (tendency ↔ preference, set ↔ region) and
clearly wrong (lower-dimensional → that) at scores within 0.015 of each
other.

## Next moves

- Replace whole-sentence cosine with a substitution-local score:
  per-token logit shift, or contrastive same-concept vs other-concept.
- Try larger paraphrase corpora (1000+ pairs).
- Try larger language models (GPT-2 medium, Pythia-1.4B).
- Causal validation: retrain a small LM with the top-N learned
  substitutions as data augmentation; check whether downstream
  paraphrase-invariance improves.
