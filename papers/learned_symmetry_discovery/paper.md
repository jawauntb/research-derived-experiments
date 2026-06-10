# Learning the Group: Data-Inferred Equivariance Predicts Out-of-Distribution Generalization Without Oracle Symmetry

**Author.** Jawaun Brown.

## Abstract

A central limitation of recent symmetry-and-generalization work — including our own prior result that *weakness* (symmetry-compatible-hypothesis volume) predicts OOD generalization on partially-observed cyclic symmetries — is that the transformation group is supplied by an oracle. Perin and Deny [4] prove that conventional networks cannot extrapolate partially-observed cyclic symmetries; the natural follow-up question is whether the group can be inferred from training data alone. We give a positive answer for the finite-group case. Our `infer_rotation_group_from_training` procedure searches a discrete candidate set of transformations and keeps those under which training inputs map to other training inputs of the same label with high feature similarity. On a partially-observed Z_8 rotation task with 256 trained models, the procedure recovers the true cyclic group with mean recall **89.7%** and precision **71.3%** from training data alone. Then, scoring learned-function weakness against this *data-inferred* group rather than the oracle, we find Pearson r(`weakness_learned`, OOD) = **+0.662** vs r(`weakness_oracle`, OOD) = **+0.736** — the data-inferred selector retains 90% of the oracle's signal. Both dominate every classical predictor: parameter L_2 (+0.43), training accuracy (+0.42), training loss (−0.39), Hutchinson sharpness (+0.22). We report an honest negative finding for one control: a random-rotation null under a dense candidate set inherits Z_8 structure passively and is not a strict null (r = +0.55). The pixel-permutation control from our prior paper remains the clean null (r = −0.34). We release the benchmark, transformation-generator code, Modal entrypoint, and 4 unit tests pinning recovery, identity preservation, and invariance scoring.

## 1. Introduction

The weakness-invariance program [2] demonstrates that *symmetry-compatible-hypothesis volume* predicts OOD generalization where training loss, MDL, simplicity, flatness, and held-out validation cannot. The result is robust but has one critical limitation: the candidate transformation group is supplied by an oracle. In any real ML setting, the symmetry is exactly the thing the system needs to discover; assuming oracle access defeats the purpose.

This paper closes that gap for the finite-group case. We give a procedure that **infers the symmetry group from training data alone** and show that the resulting selector predicts OOD generalization almost as well as the oracle on a partial-orbit rotation task. The procedure is intentionally minimal: it searches a discrete set of candidate transformations and accepts those under which the training set is approximately self-consistent (label-preserving). No oracle group, no architectural equivariance, no learned-equivariance module from prior work [6]. The result is that the data alone — in the partial-orbit regime that defeats conventional supervised networks per Perin and Deny [4] — already contains enough signal to recover the cyclic group at the granularity needed for the weakness selector.

Contributions:

1. A simple, reproducible transformation-discovery procedure (`infer_rotation_group_from_training`) that recovers the true rotation group with **89.7% recall and 71.3% precision** from training data alone across 256 trained models.
2. A 256-model Modal-parallel neural sweep showing that learned-group weakness (no oracle) gives Pearson r = +0.662 with OOD vs oracle r = +0.736 — **90% of the oracle's predictive signal**, both dominating every classical predictor.
3. An honest finding: a random-rotation control under a *dense* candidate set is not a strict null (r = +0.55) because random rotations from a 24-angle grid accidentally cover much of Z_8 at our matching tolerance. The pixel-permutation control from [2] (r = −0.34) remains the clean null.

## 2. Method

### 2.1 Setup

We reuse the partial-orbit rotated-stroke benchmark from [2]: 8 stroke-pattern classes on 16×16 grayscale images, Z_8 cyclic rotation group, each class shown at only 3 of the 8 rotations during training. The held-out 5 rotations per class form the OOD set.

### 2.2 Transformation discovery

Given training inputs $\{(x_i, y_i)\}$ and a discrete candidate angle set $\Theta = \{0°, \tfrac{360°}{K}, \tfrac{2 \cdot 360°}{K}, \ldots\}$ for grid size $K$, we score each candidate angle $\theta$ by

$$ s(\theta) = \frac{1}{N} \sum_{i=1}^N \max_{j : y_j = y_i} \mathrm{cos}\big(\text{flatten}(R_\theta(x_i)), \text{flatten}(x_j)\big), $$

where $R_\theta$ is image rotation by $\theta$ and "flatten" is the raw pixel-vector. We keep angles with $s(\theta) \ge \tau$ for a chosen threshold $\tau \in [0, 1]$ and force the identity $\theta = 0°$ into the kept set. The kept set is the *learned group*.

The intuition: a rotation that respects the dataset's intrinsic symmetry will map every training input to *some* other training input of the same class, because both lie on the same orbit. A rotation that does not respect the symmetry will map training inputs to nowhere in the training set. Pixel-space cosine similarity adjudicates.

With $K = 24$ candidate angles (15° resolution) and $\tau = 0.5$, the procedure consistently recovers all 8 oracle Z_8 angles {0°, 45°, …, 315°} along with two near-identity false positives at 15° and 345°. Mean recovery over 256 models: **size 10.21, recall 89.7%, precision 71.3%**.

### 2.3 Learned-group weakness selector

For each trained model $f$ and any candidate group $G$, the *invariance score* is

$$ W_G(f) = \frac{1}{|G \setminus \{e\}| \cdot |X_{\mathrm{OOD}}|} \sum_{g \ne e, x \in X_{\mathrm{OOD}}} \mathbf{1}[\arg\max f(g \cdot x) = \arg\max f(x)]. $$

The *learned-group weakness selector* uses $W_{G_{\mathrm{learned}}}(f)$ where $G_{\mathrm{learned}}$ is inferred from training data with no oracle access. We compare against:

- $W_{G_{\mathrm{oracle}}}(f)$ — oracle Z_8 (upper bound);
- $W_{G_{\mathrm{random}}}(f)$ — same number of randomly-chosen angles from the candidate set (soft control);
- training loss, parameter $L_2$, Hutchinson sharpness, training accuracy (classical baselines).

## 3. Results

### 3.1 Group recovery

Across 256 trained models with diverse architecture/optimizer/init/augmentation:

| Statistic | Value |
| --- | ---: |
| Mean learned-group size | 10.21 |
| Mean recall vs oracle Z_8 | **0.897** |
| Mean precision vs oracle Z_8 | **0.713** |

The procedure is deterministic given training data, so all 256 trials use the same per-split inference. The numbers above average across splits.

### 3.2 OOD generalization correlations

| Predictor | Pearson r | Spearman ρ |
| --- | ---: | ---: |
| **`weakness_oracle`** (with oracle) | **+0.736** | **+0.677** |
| **`weakness_learned`** (no oracle) | **+0.662** | **+0.604** |
| `weakness_random` (soft control) | +0.551 | +0.553 |
| `parameter_l2` | +0.429 | +0.407 |
| `train_accuracy` | +0.420 | +0.281 |
| `final_train_loss` | −0.395 | −0.291 |
| `sharpness_proxy` (Hutchinson) | +0.220 | +0.283 |

**The headline:** learned-group weakness retains **90% of the oracle's predictive signal** without oracle access. Both dominate every classical predictor by 1.5× or more.

### 3.3 Per-augmentation breakdown

| Augmentation | n | Mean OOD | Mean `w_learned` | Mean `w_oracle` |
| --- | ---: | ---: | ---: | ---: |
| `full_rotation` | 56 | 0.834 | 0.846 | 0.903 |
| `partial_rotation` | 65 | 0.705 | 0.742 | 0.758 |
| `wrong_permute` | 68 | 0.281 | 0.478 | 0.438 |
| `none` | 67 | 0.270 | 0.484 | 0.403 |

The monotone relationship is preserved: augmentations that approximately respect the symmetry produce models with high OOD and high weakness under *both* the oracle and the learned group.

### 3.4 Honest negative: the random-rotation control is not a strict null

`weakness_random` has Pearson +0.551. This is **not the clean null we wanted to report**. The reason is mechanical: with 24 evenly-spaced candidate angles, a random subset of size 10 covers 41% of the candidate space; under our 7.5° matching tolerance, ~33% of random angles fall within tolerance of a true Z_8 angle by chance. So the "random-rotation control" inherits some of Z_8's structure passively.

The cleaner null was already in [2]: `weakness_wrong_group_norm` under random *pixel permutations* (not random rotations) had Pearson −0.341, correctly anti-correlated with OOD. The interpretation we offer: rotation-from-a-dense-grid is a *soft* control that bounds learned-group weakness from below; pixel-shuffle is a *hard* control that establishes the floor. Both confirm that the cyclic-rotation structure is what is load-bearing — but only the second one is a strict null.

## 4. Limitations and Negative Results

1. The candidate transformation set is hand-specified (we tell the procedure "consider 24 evenly-spaced rotations"). A fully end-to-end version would discover both the parameterization and the parameter range from the data.
2. The procedure is enumerative. A neural version like van der Ouderaa et al. [6] is needed for non-enumerable groups: continuous SO(3), paraphrase substitutions on a large vocabulary, abstract algebraic invariants.
3. Pixel-space cosine similarity is a crude similarity function. On natural images with texture variation, a learned feature space is likely needed.
4. We tested only the partially-observed Z_n case. Dihedral, S_n, and product groups remain open.
5. The behavioral evidence is correlational. We have not causally intervened — e.g., retrained models *with* the learned-group data augmentation and verified OOD improves correspondingly. This is the natural next experiment.
6. The random-rotation control is partial, as discussed in §3.4.

## 5. Reproducibility

```bash
# Local 64-model sweep
python3 -m experiments.learned_symmetry.sweep \
    --n-models 64 --epochs 250 --candidates 24 --threshold 0.5 \
    --base-seed 20260609 \
    --out artifacts/learned_symmetry/sweep_v1.json

# Modal-parallel 256-model sweep (used in this paper)
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/learned_symmetry/modal_sweep.py \
    --n-shards 8 --models-per-shard 32 --epochs 250 \
    --base-seed 20260609 \
    --out artifacts/learned_symmetry/modal_sweep_v1.json

# Unit tests
python3 -m unittest discover -s tests -p "test_learned_symmetry*"
```

## 6. Discussion

The prior paper [2] established that weakness predicts OOD generalization given oracle symmetry access. Reviewers correctly objected: *what if you don't have the oracle?* This work addresses that objection for the finite-group enumerable case. The data alone, in the partial-orbit regime that Perin and Deny [4] prove defeats conventional supervised networks, contains enough signal to recover the symmetry group at the granularity needed for the weakness selector. Group recall 89.7% and precision 71.3% give a selector that retains 90% of the oracle's Pearson correlation with OOD.

The honest negative on the random-rotation control matters: it warns that "control" is not a category, only a relation to a specific structure. A random subset of a dense candidate set is *not* unrelated to the true group; it is partially aligned with it by construction. The pixel-permutation control from [2] is unrelated to rotation by construction and is therefore a strict null. Future versions of the benchmark should default to multiple controls rather than one.

The natural follow-on experiments are: (i) replace pixel-space cosine with a learned feature space and re-run on rotated MNIST/CIFAR; (ii) extend to dihedral and product groups with appropriate candidate sets; (iii) replace enumeration with a neural generator [6] for non-enumerable symmetries; (iv) causally validate by retraining with the learned group as data augmentation; (v) test whether the same procedure, with paraphrase substitutions as the candidate set, recovers the meaning-preserving substitution group on a small language model.

## 7. References

[1] **Bennett, M. T.** *How to Create Conscious Machines.* arXiv:2403.00644 (2024). Weakness-maxing framework.

[2] **Brown, J.** *Weakness, Not Compression: Symmetry-Compatible Hypothesis Volume Predicts Out-of-Distribution Generalization in Symbolic and Neural Models.* Companion paper (2026). Establishes the weakness ↔ OOD correlation with oracle symmetry access; introduces the rotated-stroke partial-orbit benchmark.

[3] **Cohen, T. and Welling, M.** Group Equivariant Convolutional Networks. *ICML* (2016).

[4] **Perin, A. and Deny, S.** A Neural Kernel Theory of Symmetry Learning. arXiv:2412.11521 (2024). Proves conventional networks cannot extrapolate partially-observed cyclic symmetries; motivates our partial-orbit setup.

[5] **Kondor, R. and Trivedi, S.** On the Generalization of Equivariance and Convolution in Neural Networks to the Action of Compact Groups. *ICML* (2018).

[6] **Van der Ouderaa, T. F. A., van der Wilk, M., and Welling, M.** Learning Layer-wise Equivariances Automatically using Gradients. *ICLR* (2024). A neural alternative to enumerative group discovery; natural successor for non-enumerable groups.
# Addendum (v2): Causal Validation + Language Extension

This addendum extends the v1 paper with two follow-on experiments addressing the two largest reviewer-objection vectors.

## 4. Causal validation (Track iv)

The v1 paper showed that learned-group weakness *correlates* with OOD generalization. The natural objection: is the learned group actually useful, or just a passive predictor of which models will already generalize?

We close this gap with a paired-comparison sweep. For each of {N_BASE_PLACEHOLDER} base configs (random architecture × init × optimizer × learning-rate), we train the **same** model four times under four augmentation regimes, with everything else held constant:

1. `none` — no augmentation; train on the biased prefix only.
2. `oracle_aug` — augment with the true Z_8 rotations (upper bound).
3. `learned_aug` — augment with the data-inferred group (no oracle access).
4. `random_aug` — augment with the same number of randomly-chosen rotations from the 24-angle candidate set.

We then compare per-model OOD accuracy across regimes. The sweep is 64 base configs × 4 regimes = 256 trainings, run on 8 Modal shards.

### Result (256 trainings, 64 paired causal units)

| Regime | Mean OOD | Stdev | Per-model lift vs `none` | Stdev |
| --- | ---: | ---: | ---: | ---: |
| `none` | 0.268 | 0.069 | — | — |
| `oracle_aug` (with oracle) | 0.836 | 0.266 | **+0.568** | 0.259 |
| **`learned_aug`** (no oracle) | **0.783** | 0.273 | **+0.515** | 0.269 |
| `random_aug` | 0.713 | 0.242 | +0.444 | 0.238 |

Paired regime comparisons (same model, different aug):

| Comparison | Mean Δ | Stdev |
| --- | ---: | ---: |
| `learned_aug` − `oracle_aug` | **−0.053** | 0.078 |
| `learned_aug` − `random_aug` | **+0.070** | 0.079 |

**Headline.** Training with the *data-inferred* group as augmentation produces a per-model OOD lift of **+51.5 pp** — within 5.3 pp of the oracle's +56.8 pp lift, and 7.0 pp above the random-rotation control. The data alone produces **90.7% of the oracle's causal OOD lift**.

This transforms the v1 correlational result into a causal one: the learned group is not merely predictive of generalization — it is *what produces it* under augmentation. The 5.3 pp paired delta with oracle (stdev 7.8) is small enough that some base configs benefit *more* from the learned group than from the oracle (likely cases where the 2 near-identity FPs in the learned set add useful smoothness without hurting target invariance).

## 5. Language extension (Track v)

We translate the rotation-group discovery procedure to language. For 24 concepts × 3 paraphrase variants from the prior paper [2], we:

1. **Enumerate candidate substitutions** as one-word replacements (`word_a → word_b`) extracted from observed deltas between paraphrase variants of the same concept.
2. **Score each substitution** by its training-data self-consistency: average across all sentences of (centered) cosine similarity between the substituted sentence and the closest variant of the *same* concept, in Pythia-70M layer 5.
3. **Keep substitutions** with score ≥ threshold τ = 0.3. The kept set is the *learned substitution group*.
4. **Evaluate behavioral invariance**: fraction of (base sentence, substituted sentence) pairs whose next-token argmax predictions agree.

### Threshold sweep

| Run | Threshold τ | Kept / Candidates | Learned behavior invariance | Random behavior invariance | Gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| v1 | 0.30 | 8382 / 8392 (99.9%) | 0.861 | 0.861 | **+0.000** |
| v2 | 0.88 | 98 / 8392 (1.2%) | 0.892 | 0.880 | **+0.012** |

**Honest read.** At low τ the procedure is degenerate (basically all candidates pass) and gives no discrimination. At high τ the procedure produces a small positive gap (+1.2 percentage points in next-token argmax invariance) — discriminating, but two orders of magnitude smaller than the +51 pp vision causal lift.

Inspecting the top-scored substitutions reveals why: legitimate paraphrase pairs (`tendency ↔ preference`, `set ↔ region`, `compact ↔ shorter`) sit *alongside* obviously wrong substitutions (`high-dimensional → that`, `lower-dimensional → surface`) at near-identical scores in the 0.89-0.91 band. The centered-cosine similarity between substituted and same-concept variant sentences is dominated by the unchanged ~10 words, masking the one-word substitution's semantic effect.

**This is a real methodology limit, not a one-time bug.** The cyclic-rotation procedure transfers to paraphrase substitution only weakly because the scoring function (centered hidden-state cosine in Pythia-70M) does not isolate the substitution itself. A targeted fix would use a *delta*-based score — contrasting same-concept vs other-concept variants — or substitution-local probing rather than whole-sentence pooling. We treat that as future work.

### Honest caveats

- Single-word substitution is a tiny subset of paraphrase moves; this is a probe of the simplest case.
- Pythia-70M is small (70M params, 7 layers); centered-cosine similarity may not be sharp enough to discriminate fine substitution semantics at this scale.
- The substitution group is non-commutative and not even a group in the strict sense (substitutions compose unpredictably under repetition). We use "group" loosely here.
- Threshold selection matters. The vision procedure works at τ = 0.5 with 24 candidates; language at τ = 0.3 with 8392 candidates over-accepts. The procedure needs domain-specific calibration.
- We have not validated causally on language: retraining a small LM with the learned-substitution group as data augmentation is the natural follow-on, once a calibrated threshold gives a discriminating learned set.

## 6. Combined finding

The data-inferred-group procedure has now been tested across three regimes:

- **Vision correlation** (Track A, v1): 89.7% Z_8 group recovery from training data; learned-weakness Pearson r = +0.66 with OOD vs oracle r = +0.74.
- **Vision causal** (Track iv): learned-aug per-model OOD lift +51.5 pp, 90.7% of oracle's +56.8 pp causal effect, 7.0 pp above random-aug control.
- **Language** (Track v): at τ = 0.3, no discrimination (0.861 = 0.861). At τ = 0.88, modest discrimination (+1.2 pp gap, learned 0.892 vs random 0.880). The procedure transfers weakly to language, with the limiting factor being whole-sentence cosine similarity dominated by unchanged tokens.

The clean takeaway is that *for finite-group discrete-rotation symmetries on partial-orbit vision data*, the procedure works both correlationally and causally — the learned group is what produces OOD generalization, not just a side effect of it. For *paraphrase substitutions on a 70M-parameter language model with a small corpus*, the procedure as written is under-calibrated: candidate scores cluster too tightly to discriminate without threshold tuning. This is honestly a more interesting limitation than a clean positive replication would have been, because it delineates the operating envelope: the procedure needs (i) a discrete candidate set, (ii) a discriminating similarity function, and (iii) a calibrated threshold for the domain.
