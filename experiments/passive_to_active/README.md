# Passive → Active Geometry

The Layer-3 question. The three companion papers established:

- **Layer 1 (technical):** weakness predicts OOD generalization where loss, sharpness, MDL, and parameter norm do not [Weakness Predicts OOD].
- **Layer 2 (representational):** the symmetry group can be inferred from training data alone for finite enumerable groups [Learning the Group; When Pixels Beat Embeddings].

This program tests the next jump:

> **Does invariant latent geometry become *causally load-bearing* when a model is coupled to action?**

In the prior paper [Pythia paraphrase probe], we found that paraphrase orbits cluster strongly in Pythia-70M's centered latent space (gap +0.79 at layer 5), but per-concept latent weakness does **not** predict per-concept next-token behavioral consistency. The honest read was: passive geometry exists, but it's not yet load-bearing for behavior.

The hypothesis here is sharper: the same latent geometry should become *causally* load-bearing for behavior **after the model is fine-tuned on a paraphrase-invariant task**. Action coupling — the model getting reward/loss based on the right answer regardless of paraphrase — should reshape the geometry from a passive cluster into an active controller.

## Falsifiable claim

For a small LM:

1. **Pre-FT (passive):** Centered latent paraphrase clustering exists (replicates prior result). Causal interventions on the paraphrase direction (patching, ablation) do *not* materially change classification/behavior on a paraphrase-invariant downstream task. The geometry is *correlational with concept identity* but not *causal for the task*.

2. **Post-FT (active):** After supervised fine-tuning on a paraphrase-invariant classification task, the same latent geometry exists AND causal interventions on the paraphrase direction now **predictably change** behavior. Output now flows *through* the latent geometry, not around it.

If we observe (1) → (2) with the geometry the same level of cluster-tightness but the causal-interventional response qualitatively different, that supports the passive→active framing.

If the geometry doesn't change OR causal interventions affect behavior even pre-FT, the framing is weaker than the claim.

## Concrete experiment

- **Model:** Pythia-70M (same as prior paraphrase track for continuity).
- **Data:** 24 concepts × 3 variants from `concept_paraphrases.json`. Build a paraphrase-invariant classification task: predict the concept id from the variant text.
- **Phase 1 (passive measure):**
  - For each variant, extract layer-5 mean-pooled hidden state.
  - Compute centered paraphrase weakness (in-orbit cosine vs wrong-orbit cosine).
  - Apply causal intervention: add a perturbation along the *paraphrase direction* (defined as the within-concept mean − overall mean) and measure how much the model's downstream behavior changes.
  - Baseline: same intervention on a random direction.
- **Phase 2 (active training):**
  - Add a small classification head; fine-tune the encoder + head on the concept-id task. Critically: all 3 variants of each concept get the same label.
  - Loss reaches near-zero — the model has now *used* its paraphrase clustering for action.
- **Phase 3 (active measure):**
  - Re-extract centered paraphrase weakness.
  - Re-do the causal intervention. Now does perturbing the paraphrase direction change behavior?
  - Compare passive vs active intervention effects.

## Pre-registered hypothesis

The **causal effect of perturbing the paraphrase direction** should:
- Be **small** pre-FT (paraphrase direction is not load-bearing for any task)
- Be **substantially larger** post-FT (paraphrase direction now controls the classifier's output)
- The random-direction control should change little pre or post

A 3–5× larger causal effect post-FT is the threshold for the active-geometry claim.

## Files (planned)

- `geometry_probe.py` — extract hidden states + measure paraphrase clustering (reusable for pre and post)
- `causal_intervention.py` — add direction-perturbation; measure output change
- `active_finetune.py` — small classification head + supervised fine-tune loop
- `modal_passive_to_active.py` — Modal entrypoint that runs the full pre→FT→post pipeline
- `results/passive_vs_active_<date>.md` — pre-registered gate + result report

## Why this matters

This is the empirical version of the philosophical Layer-3 claim: meaning is not just structure, it is **structure-coupled-to-action**. If a passive cluster becomes a causal controller through action coupling, that's evidence the framework's central claim has bite. If it doesn't, the philosophy needs revising or weakening.

## What this is not

- Not a proof of consciousness. The hypothesis test is "does intervention effect grow after action coupling," not "does the model now care."
- Not a claim about RL specifically. Supervised fine-tuning is the simplest action-coupling proxy. RL is the natural follow-on.
- Not a claim about LLMs as agents. The experiment tests a representational property under task coupling, nothing more.
