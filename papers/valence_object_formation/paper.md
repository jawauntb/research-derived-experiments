# Objects Form from Concern: Valence-Coupled Encoders Cluster the World by Causal Role, Not Sensory Similarity

**Author.** Jawaun Brown.

## Abstract

The five prior empirical papers in this program established that weakness predicts OOD generalization [1], that the relevant symmetry group can be inferred from data [2], that pixel-cosine and learned-encoder methods occupy different operating regimes [3], that paraphrase clusters become causally load-bearing under action coupling [4], and that the same active geometry preserves a viability buffer, repairs itself under viability breach, and obeys the Law of the Stack [5]. The conceptual paper [6] argues that the deepest test of the framework is *valence-induced object formation*: do agents whose objective is coupled to their viability carve the world into objects according to causal-valence role, rather than sensory similarity?

We give the first empirical test on a minimal bandit environment. Each item has a 16-dim observation: 4 visual ("color") classes encoded in 8 dims and 2 ("label") classes encoded in 8 dims, with Gaussian sensor noise σ=0.15. The reward function is a *crossed* function of (color, label) — under XOR, *neither* color *nor* label alone determines reward. We train three encoders, all 16 → 64 → 32, on the same observations:

- **reconstruct**: autoencoder objective (`MSE(x̂, x)`)
- **sensory**: predict color (the most prominent visual feature)
- **valence-coupled**: predict the optimal action (consume iff reward > 0)

After 1,500 training steps on 64 samples per step, we extract embeddings for 512 held-out items per cell and compute cluster gaps along three axes (color, label, reward). The result is unambiguous across 3 seeds × 2 reward structures = 6 cells per condition:

| Condition | Color gap | Label gap | **Reward gap** | Task acc |
| --- | ---: | ---: | ---: | ---: |
| reconstruct | +0.53 | +0.43 | +0.14 | — |
| sensory | **+1.28** | 0.00 | +0.05 | 1.000 |
| valence-coupled | +0.12 | +0.57 | **+1.96** | 1.000 |

Both the sensory and valence-coupled encoders reach 100% task accuracy on their respective tasks, so the comparison holds task competence constant. But the encoders organize the same observations into radically different geometries. Under XOR specifically — where neither color nor label alone can predict reward — the valence-coupled encoder collapses *both* sensory axes (color gap +0.005, label gap +0.008) and represents *only* the reward axis (+1.96). The same observations, the same architecture, the same training compute. What the encoder represents is the agent's *causal-valence axis*, not the sensory feature soup.

This is the first direct empirical evidence in the program for the conceptual paper's strongest Layer-3/Layer-4 claim: *meaning is not sensory resemblance; meaning is action-relevant, valenced causal structure*. Objects can form from concern.

## 1. Introduction

The conceptual spine [6] argues that valence-induced object formation is the most philosophically important experiment in this program, because it directly tests whether agents carve the world into objects by causal relevance for self-maintenance rather than mere sensory resemblance. Paper [4] established that paraphrase clusters can become causally load-bearing under action coupling, and paper [5] established that the same active geometry survives viability breach via Ashby ultrastability and obeys the Law of the Stack. But in both, the *objects* the model represented (paraphrases of dynamical-systems concepts) were not in tension with the model's viability — they were just classification labels.

The deeper test is to set up an environment where sensory features and causal-valence role are *crossed*, so that the encoder must choose what to represent. If the encoder is trained to do something whose payoff depends on the causal-valence axis, does it abandon the sensory axis when the two are in tension?

We give the cleanest possible version of that test on a minimal bandit env.

## 2. Method

### 2.1 Environment

Each item has a 16-dim observation. Four "color" classes are encoded as one-hot in obs[0:4]; two "label" classes are encoded as one-hot in obs[8:10]; the remaining dims start at zero. Gaussian noise σ=0.15 is added to every dim. A random per-cell permutation is applied to the 16 dims so the encoder cannot exploit positional ordering.

The reward function maps (color, label) → ±1 via one of:

- **XOR**: reward = +1 iff (color ∈ {0, 1}) XOR (label == 0)
- **additive_thresh**: reward = +1 iff (color + signed_label) > 0, where signed_label ∈ {-2, +1}

In both, neither color nor label alone fully determines reward; in XOR, *the conjunction* is necessary.

### 2.2 Training conditions

All three conditions share an encoder MLP `16 → 64 → ReLU → 32`. They differ in the objective:

| Condition | Head | Loss |
| --- | --- | --- |
| `reconstruct` | decoder `32 → 64 → ReLU → 16` | `MSE(decoder(encoder(x)), x)` |
| `sensory` | classifier `32 → 4` | `CE(head(encoder(x)), color)` |
| `valence-coupled` | classifier `32 → 2` | `CE(head(encoder(x)), optimal_action)` where `optimal_action = 1` iff `reward(color, label) > 0` |

Optimization: Adam, lr 2×10⁻³, 1,500 steps × 64 samples/step. Seeds {20260610, 1729, 4242}.

### 2.3 Measurements

After training, we extract embeddings for 512 held-out items (sampled uniformly over (color, label)). For each axis a ∈ {color, label, reward}, we compute the centered-cosine cluster gap:

`gap_a = mean(cos(z_i, z_j) | a_i == a_j) − mean(cos(z_i, z_j) | a_i ≠ a_j)`

A high gap on axis a means the encoder organizes its representation by a.

### 2.4 Pre-registered acceptance gates

- **Sensory dominance gate**: in the `sensory` condition, color_gap > reward_gap by ≥ +0.5 in all 6 cells.
- **Valence dominance gate**: in the `valence-coupled` condition, reward_gap > color_gap by ≥ +0.5 in all 6 cells.
- **Task parity gate**: task accuracy on `sensory` and `valence-coupled` should both reach ≥ 0.95 (so we are not comparing a competent encoder to an incompetent one).

## 3. Results

### 3.1 Encoders cluster by their objective's causal axis

![Figure 1: per-condition cluster gap by axis. The sensory-trained encoder has a huge color gap (+1.28) and near-zero label/reward gaps. The valence-coupled encoder has the opposite — reward gap dominates at +1.96, color and label gaps are small. The reconstruct encoder uses both color and label moderately, reward marginally.](figures/fig1_axis_dominance.png)

The pre-registered gates are met by wide margins:

- **Sensory dominance**: in all 6 sensory cells, color_gap − reward_gap ≥ +1.16 (mean +1.22).
- **Valence dominance**: in all 6 valence-coupled cells, reward_gap − color_gap ≥ +1.65 (mean +1.84).
- **Task parity**: sensory task accuracy 1.000 (color classification); valence-coupled task accuracy 1.000 (optimal-action classification).

The most surprising column of Table 3.1 is the *label gap* for the valence-coupled condition: it splits sharply by reward structure. Under XOR (where label alone is uninformative), the label gap is +0.008. Under additive_thresh (where label is the heaviest contributor to reward), the label gap is +1.13. The valence-coupled encoder uses the label axis *exactly when it is causally diagnostic*, and discards it otherwise. The reward gap stays near +1.96 under both structures.

### 3.2 The geometry is visible in 2D

![Figure 2: 2D PCA of held-out embeddings, faceted by condition (columns) × reward structure (rows), colored by REWARD. The valence-coupled column (right) shows two cleanly separated reward clusters. The sensory column (middle) shows a perfect color-clustered scatter that is randomly intermixed in reward space. The reconstruct column (left) shows partial separation by both.](figures/fig2_pca_projection.png)

![Figure 3: same 2D PCA, now colored by COLOR. The sensory column shows four cleanly separated color clusters; the valence-coupled column shows colors fully intermixed (under XOR) or partially mixed (under additive). The reconstruct column shows moderate color separation.](figures/fig3_pca_colored_by_color.png)

Figures 2 and 3 are paired. The sensory encoder *separates colors* (Fig 3 middle) but does not separate rewards (Fig 2 middle). The valence-coupled encoder *separates rewards* (Fig 2 right) but does not separate colors (Fig 3 right, XOR row). Same observations, same architecture, same compute — different organization.

### 3.3 No condition dominates both axes

![Figure 4: per-cell scatter in (color_gap, reward_gap) space. The three conditions live in distinct quadrants: sensory bottom-right (high color, near-zero reward); valence-coupled top-left (low color, high reward); reconstruct middle. The diagonal y = x is the "represents both equally" line; nothing on it.](figures/fig4_pareto.png)

The Pareto plot in Fig 4 makes the trade-off explicit. The three training conditions occupy three different regions of (color_gap, reward_gap) space:

- `sensory` cells cluster near (+1.27, +0.05) — high color, near-zero reward
- `valence-coupled` cells cluster near (+0.12, +1.96) — low color, very high reward
- `reconstruct` cells cluster near (+0.53, +0.14) — moderate color, marginal reward

The encoder's organization is determined by its objective; the observations are identical across conditions.

## 4. Discussion

The conceptual paper [6] argues that *meaning is geometry under concern*. The empirical question is whether agents whose objective is coupled to their causal-valence axis form representations that organize around that axis rather than around sensory features. This paper gives a clean yes.

The most informative cell is *valence-coupled under XOR*. Color alone cannot predict reward. Label alone cannot predict reward. Their conjunction (XOR) determines reward. The valence-coupled encoder has color_gap +0.005 and label_gap +0.008 — *neither sensory feature is individually represented* — but reward_gap +1.96. The encoder has not learned to read either feature individually; it has learned to read the *function* of both that determines its outcome.

This is the geometric content of the philosophical claim "meaning is action-relevant valenced causal structure" [6, p. 7]. The encoder does not encode "what the world looks like" (color is the most prominent visual feature; it is fully discarded). It encodes "what matters for what I care about" — reward, the conjoint function that controls the optimal action.

The same architecture, trained on the same observations with a sensory objective, produces the opposite geometry: color is represented in its sharpest possible form (+1.27 gap, near the empirical ceiling) and reward is not represented at all (+0.05 gap). The 32-dim embedding space *can* represent any of these axes; it represents the one its objective pushes it to represent. The observation that current pretrained language models cluster paraphrases [4] is the analogue of the *reconstruct* condition here — they organize their representations by surface co-occurrence, not by what would matter for an agent embedded in a viability loop.

This is the simplest empirical experiment we know of that distinguishes "passive geometric structure" (sensory clustering) from "active geometric structure" (clustering around the axis the system's stakes select). Paper [4] showed action coupling can install causal load-bearing on a specific axis. Paper [5] showed the active system preserves a buffer and repairs itself. This paper shows that *the axis itself is selected by the system's objective*, and when sensory and causal axes are crossed, valence-coupled systems pick causal over sensory.

## 5. Connection to the program

| Layer | Claim | Evidence |
| --- | --- | --- |
| 1 | Weakness > compression/flatness/loss for OOD | [1] r ≈ +0.81 |
| 2 | Symmetry group inferable from data | [2] Z₈ recovered, +51.5 pp causal lift |
| 3a | Action coupling makes geometry causally load-bearing | [4] +7× ratio, 6/6 replication |
| 3b | Active geometry preserves buffer, repairs, obeys LoS | [5] full_ft recovers to 0.965 |
| 4a | Valence-coupled objective selects the causal-role axis | **This paper** — reward gap +1.96 vs +0.05 |
| 4b | Homeostatic agent forms objects by causal-valence role in episodic RL | Open — homeostatic-RL extension |

## 6. Limitations

1. **Supervised optimal-action stand-in.** The valence-coupled condition trains the encoder to predict the optimal action under the reward function, rather than learning the reward through interaction. This is the supervised analogue of the fixed-point that a fully-trained RL agent would converge to in this bandit. The next paper should replace this with policy-gradient RL on episodes where the agent maintains an internal energy state.
2. **No temporal viability dynamic.** Bennett & Suzuki [5] are explicit that autopoiesis requires *self-maintenance over time* through homeostatic and homeodynamic regulation. This paper has no temporal dimension; it tests only the static-objective version of the claim. Adding an energy variable that decays, ends the episode when zero, and is restored by consuming food (and depleted by poison) is the natural v2.
3. **Linear reward structure.** Two reward structures (XOR and additive_thresh) are tested. Both are still simple Boolean functions of two features. The next test should use richer reward structures, including ones that require multi-step planning (which forces a temporal credit-assignment dimension into the representation).
4. **Single-modality observations.** Real agents form objects from cross-modal sensory streams. This paper uses synthetic 16-dim observations; extending to pixels (small images) would test whether the same geometry emerges from richer sensory data.
5. **No interference between objects.** Each item is encountered in isolation. A more challenging test would involve scenes with multiple items where the agent must compositionally combine reward predictions.
6. **The encoder's "discarding" of color under XOR is not literal information loss.** The reconstruction baseline (which preserves color +0.53 and label +0.43) demonstrates that 16-dim observations contain both. The valence-coupled encoder still computes color and label internally; it just does not *organize its 32-dim embedding* by them. The deeper question of whether the information remains decodable is left open.

## 7. Reproducibility

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/valence_object_formation/modal_object_formation_sweep.py \
    --seeds "20260610,1729,4242" \
    --out artifacts/valence_object_formation/sweep_v1.json
```

Modal run: `ap-qs6VT7QfwJbA4cKtZQV2As`. Wall clock: ~2 min for 18 cells. Raw: `artifacts/valence_object_formation/sweep_v1.json`. Figures: `papers/valence_object_formation/figures/fig1`...`fig4`.

## 8. Next paper

The natural v2 extends this to **homeostatic RL**:

- Episode-based gridworld with an explicit energy variable E ∈ [0, 1].
- Per-step decay δ; episode ends when E hits 0 (penalty) or after T steps.
- Items spawn randomly with the same (color × label) → role structure.
- Agent learns via policy gradient on cumulative return.
- Compare against (a) supervised-optimal-policy and (b) reconstruction-pretrained-then-RL agents.
- Predict: the from-scratch RL agent's representation clusters by reward gap (≥ +1.5), the reconstruction-pretrained agent's representation retains color structure even after RL fine-tuning (the Law of the Stack again — pretrained representation caps adaptive reorganization).

That paper turns the static-objective demonstration here into a temporal-viability demonstration, and explicitly tests whether the autopoietic-control results from [5] survive in the setting the conceptual paper [6] cares most about.

## 9. References

[1] **Brown, J.** *Weakness, Not Compression: Symmetry-Compatible Hypothesis Volume Predicts Out-of-Distribution Generalization in Symbolic and Neural Models.* Companion paper (2026).

[2] **Brown, J.** *Learning the Group: Data-Inferred Equivariance Predicts Out-of-Distribution Generalization Without Oracle Symmetry.* Companion paper (2026).

[3] **Brown, J.** *When Pixels Beat Embeddings: Three Failed Neural Approaches to Symmetry Group Discovery, with a Selection-Rule Caveat.* Companion paper (2026).

[4] **Brown, J.** *From Passive Cluster to Active Controller: Action Coupling Makes Latent Geometry Causally Load-Bearing.* Companion paper (2026).

[5] **Brown, J.** *From Active Geometry to Autopoietic Control: Viability Slack as the Bottleneck for Adaptive Generalization.* Companion paper (2026).

[6] **Brown, J.** *Towards a Theory of Geometric Meaning, Active Agency, and Weakly Constrained Intelligence.* Conceptual companion paper (2026).

[7] **Bennett, M. T., & Suzuki, K.** *The Autopoietic Theorem.* Preprint, https://doi.org/10.22541/au.177575355.56499869/v1 (2026).

[8] **Di Paolo, E.** *Homeostatic adaptation to inversion of the visual field and other sensorimotor disruptions.* SAB (2000). Source of the temporal-viability dynamic that motivates §8.
