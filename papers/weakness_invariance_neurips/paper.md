# Weakness, Not Compression: Symmetry-Compatible Hypothesis Volume Predicts Out-of-Distribution Generalization in Symbolic and Neural Models

**Author.** Jawaun Brown.

## Abstract

When training data is consistent with both a local shortcut and a globally invariant rule, classical model-selection heuristics — minimum training loss, shortest description, MDL-style compression, parameter-space flatness, held-out validation — choose the shortcut and fail to generalize. We give a clean empirical separation showing that **weakness**, defined as the cardinality of the transformation set under which a hypothesis remains equivariant, predicts out-of-distribution generalization where none of these classical heuristics do. We construct a multi-family symbolic benchmark (cyclic, dihedral, parity, symmetric) in which the truth and the shortcut are both train-perfect. On the two families where the candidate group has the right granularity (cyclic Z_n, dihedral D_n; n=500 trials each), weakness selects the invariant rule with Wilson 95% lower-bound 0.992 and the classical baselines all select the local shortcut with Wilson 95% upper-bound 0.008. We extend the result to trained MLPs: across 256 small models with diverse architecture, init, optimizer, and data-augmentation regime, learned-function weakness under the true group is the strongest correlate of OOD accuracy (Pearson r = +0.82, Spearman ρ = +0.55) — far outperforming training loss (r = −0.03), held-out validation (r = +0.10), parameter L_2 (r = +0.10), and a Hutchinson sharpness proxy (r = +0.13). Wrong-group and random-label controls correctly fail to predict OOD (|r| ≤ 0.13). Parity (|G|=2) and S_n (|G|=n!) are presented as honest negative cases where weakness fails predictably, delineating its operating regime. All code, benchmarks, and artifacts are released publicly.

## 1. Introduction

The dominant paradigm for model selection rests on a small set of heuristics: minimize training loss, prefer short descriptions (Solomonoff/MDL [11, 12]), prefer flat minima [5, 8], minimize parameter norm. Recent work has challenged each. Dinh et al. [4] first showed that Hessian-based sharpness measures are not reparameterization-invariant. Bennett [1, 2] sharpens this argument: function-preserving reparameterization inflates Hessian-based sharpness without changing predictions, so parameter-space flatness cannot be the fundamental cause of generalization. Perin and Deny [10] prove that conventional networks lack a mechanism to learn symmetries that are not built into the architecture or sufficiently represented in the data. Bennett's stack theory [1] argues that the relevant quantity is *weakness* — the volume of completions compatible with the learned function — rather than the parameter-space geometry that hosts it.

This paper makes the weakness conjecture experimentally concrete. We construct a benchmark where (i) multiple hypotheses fit the training data perfectly, (ii) only the symmetry-equivariant hypothesis generalizes OOD, and (iii) every hypothesis can be scored by its weakness — the number of group elements under which it remains equivariant. We then test:

1. Whether **symbolic weakness** — equivariance count under the true transformation group — selects the OOD-generalizing rule when training loss, simplicity, MDL, compression, flatness, and held-out validation cannot.
2. Whether **neural weakness** — equivariance count of the learned function table under the same group — predicts OOD accuracy across diverse trained MLPs.
3. Where weakness *fails* (wrong group, group too small or too large).

Headline results:

- Cyclic and dihedral symbolic families (n=500 trials each): weakness selects the invariant in 100% of trials (Wilson 95% lower bound 0.992); every classical baseline selects the shortcut in 100% of trials (Wilson 95% upper bound 0.008).
- Neural sweep (256 MLPs locally + 1024 MLPs on Modal, diverse architecture/init/optimizer/augmentation): weakness_oracle_norm Pearson r with OOD = **+0.81–0.82** (Spearman ρ = +0.55–0.58) in both runs. Training loss, held-out validation, and Hutchinson sharpness all have |r| ≤ 0.14; parameter L_2 has |r| ≤ 0.27.
- Wrong-group, random-label, and noisy-group controls behave as expected, ruling out the hypothesis that "any equivariance count works."

## 2. Definitions

Let $f: \mathcal{X} \to \mathcal{X}$ be a candidate function on a finite domain $\mathcal{X}$ of size $n$. Let $G$ be a group acting on $\mathcal{X}$.

**With-action equivariance.** We say $f$ is *compatible* with $g \in G$ if there exists $h \in G$ such that $f(g \cdot x) = h \cdot f(x)$ for all $x \in \mathcal{X}$. This generalizes strict equivariance ($h = g$, in the sense of Cohen and Welling [3] and Kondor and Trivedi [7]) and is the relevant notion for non-abelian and conjugation-style symmetries.

**Weakness.**
$$ W_G(f) = \big| \{ g \in G : \exists h \in G, \; \forall x, \; f(g \cdot x) = h \cdot f(x) \} \big|. $$
A function with $W_G(f) = |G|$ is fully $G$-equivariant; $W_G(f) = 1$ means only the identity commutes with $f$.

**Weakness selector.** Given a finite candidate pool $\{f_1, \ldots, f_K\}$ and a candidate group $\hat G$, the *weakness selector* returns $f_{i^*}$ with $i^* \in \arg\max_i W_{\hat G}(f_i)$, ties broken by an MDL-style compression score.

The conjecture: given the correct symmetry group $\hat G = G$, the weakness selector generalizes better than train-loss, simplicity, compression, flatness, validation, or random selection.

## 3. Symbolic Benchmark

### 3.1 Task families

We build four task families, each with a known transformation group:

- **`cyclic_prefix_shift`**: domain $\mathbb{Z}_n$, truth $f(x) = (x + b) \bmod n$. Training set is a biased prefix $\{0, \ldots, w-1\}$. Group: $\mathbb{Z}_n$.
- **`dihedral_reflection`**: truth $f(x) = (b - x) \bmod n$ (reflection with shift). Training prefix only covers indices $\{0, \ldots, w-1\}$, where rotation shortcuts fit but reflections do not. Group: $D_n$.
- **`parity_coset`**: domain $\{0, \ldots, n-1\}$ with $n$ even; truth $f(x) = x \oplus 1$. Training only sees one parity coset. Group: $\mathbb{Z}_2$.
- **`color_permutation`**: truth is a fixed-point-free involution $\pi \in S_n$. Training sees a sparse random input subset. Group: $S_n$.

In each family the candidate pool always includes a *local prefix patch* (observed outputs on training inputs, identity elsewhere), a memorizer, the true invariant, and a set of wrong invariants.

### 3.2 Selectors

We compare eleven selectors, including six classical baselines, the oracle weakness selector, three weakness ablations (wrong group, noisy group, data-inferred group), and random selection.

| Selector | Definition |
| --- | --- |
| `train_loss` | best training accuracy (ties broken by simplicity) |
| `validation` | leave-one-out training pair accuracy |
| `simplicity` | shortest hypothesis form length |
| `compression` | form_length + 20 · train errors (MDL-style proxy) |
| `mdl_program` | $2^{-\text{form\_length}}$ Solomonoff-style weight |
| `flatness_proxy` | count of unconstrained domain positions |
| `weakness_oracle` | maximum weakness under the true group |
| `weakness_wrong_group` | weakness under a random-permutation group (control) |
| `weakness_noisy_group` | weakness under a 50%-corrupted true group |
| `weakness_data_inferred` | weakness under a group inferred only from training data |
| `random` | uniform random train-consistent candidate |

### 3.3 Results

500 independent trials per family with mixed domain configurations. Wilson 95% CIs in brackets.

**`cyclic_prefix_shift`**

| Selector | Invariant rate | Wilson 95% CI | Mean OOD |
| --- | ---: | --- | ---: |
| `weakness_oracle` | **1.000** | (0.992, 1.000) | **1.000** |
| `weakness_data_inferred` | 1.000 | (0.992, 1.000) | 1.000 |
| `weakness_noisy_group` | 1.000 | (0.992, 1.000) | 1.000 |
| `random` | 0.346 | (0.306, 0.389) | 0.380 |
| `weakness_wrong_group` | 0.002 | (0.000, 0.011) | 0.003 |
| `train_loss`, `simplicity`, `compression`, `mdl_program`, `flatness_proxy`, `validation` | 0.000 | (0.000, 0.008) | 0.000 |

**`dihedral_reflection`**

| Selector | Invariant rate | Wilson 95% CI | Mean OOD |
| --- | ---: | --- | ---: |
| `weakness_oracle` | **1.000** | (0.992, 1.000) | **1.000** |
| `weakness_data_inferred` | 1.000 | (0.992, 1.000) | 1.000 |
| `weakness_noisy_group` | 0.972 | (0.954, 0.983) | 0.976 |
| `weakness_wrong_group` | 0.018 | (0.009, 0.034) | 0.119 |
| classical baselines | 0.000 | (0.000, 0.008) | 0.107 |

**`color_permutation`** (partial positive)

| Selector | Invariant rate | Wilson 95% CI | Mean OOD |
| --- | ---: | --- | ---: |
| `weakness_noisy_group` | 0.858 | (0.825, 0.886) | 0.890 |
| `weakness_oracle` | 0.824 | (0.788, 0.855) | 0.875 |
| `weakness_data_inferred` | 0.138 | (0.111, 0.171) | 0.325 |
| classical baselines, `weakness_wrong_group` | 0.000 | (0.000, 0.008) | 0.210 |

**`parity_coset`** (negative case)

| Selector | Invariant rate | Mean OOD |
| --- | ---: | ---: |
| `random` | 0.298 | 0.341 |
| `weakness_wrong_group` | 0.038 | 0.038 |
| `weakness_noisy_group` | 0.022 | 0.022 |
| `weakness_oracle`, `weakness_data_inferred`, classical baselines | 0.000 | 0.000 |

Cyclic and dihedral exhibit a perfect separation: only weakness-based selectors recover the invariant rule. The CIs do not overlap. The color-permutation result is a partial win — $S_n$ is so large that wrong involutions have comparable centralizer-orbit sizes. Parity is a clean negative: $|G| = 2$ is too small to disambiguate truth from local patches that are also $\mathbb{Z}_2$-equivariant. Both negative cases delineate the operating regime of weakness.

## 4. Neural Weakness as a Predictor of OOD Accuracy

### 4.1 Setup

We train 256 small MLPs on cyclic-prefix-shift tasks with $n \in \{7, 11, 13\}$ and varying train_window. For each model we sample independently:

- depth $\in \{1, 2, 3\}$, hidden width $\in \{16, 32, 64, 128\}$, init scale $\in \{0.3, 0.7, 1.0, 1.5\}$,
- optimizer $\in \{\text{Adam}, \text{SGD+momentum}\}$, learning rate $\in \{10^{-3}, 3\cdot 10^{-3}, 10^{-2}, 3\cdot 10^{-2}\}$, weight decay $\in \{0, 10^{-4}, 10^{-2}\}$,
- data-augmentation regime $\in \{$ none, partial cyclic, full cyclic, wrong reflection, wrong random $\}$.

After 2000 training steps we extract the full function table $\hat f$ by `argmax` over logits and compute:

- training loss after the last step,
- parameter $L_2$ norm,
- Hutchinson sharpness proxy ($\mathbb{E}_v [v^\top H v]$ with Rademacher $v$),
- leave-one-out validation accuracy,
- weakness under the *true* cyclic group $\mathbb{Z}_n$, normalized to $[0,1]$ by $|G| = n$,
- weakness under a *wrong-random-permutation* group of equal size (negative control),
- weakness under a *random-label* control group (negative control),
- weakness under a *partial cyclic* (half-shift) prior,
- OOD accuracy on the held-out suffix.

### 4.2 Results — local 256-MLP sweep

Across 256 trained MLPs, mean OOD = 0.334 (23.8% with perfect OOD). Pearson and Spearman correlations with OOD accuracy:

| Predictor | Pearson r | Spearman ρ |
| --- | ---: | ---: |
| **`weakness_oracle_norm`** | **+0.817** | **+0.552** |
| `weakness_partial_cyclic_norm` | +0.804 | +0.540 |
| `weakness_oracle` (raw) | +0.763 | +0.715 |
| Hutchinson sharpness proxy | +0.129 | +0.142 |
| parameter $L_2$ | +0.099 | +0.308 |
| held-out validation accuracy | +0.096 | +0.058 |
| training loss | −0.031 | +0.136 |
| `weakness_wrong_group_norm` | **−0.129** | −0.057 |
| `weakness_random_label_norm` | **−0.116** | −0.051 |

Weakness under the true group is the single strongest predictor of OOD accuracy across the sweep, both in raw and normalized form. The wrong-group and random-label controls are correctly close to zero or negative, ruling out the trivial hypothesis that "any equivariance count works." Training loss, validation accuracy, parameter norm, and sharpness are all weak predictors in this regime.

Per-augmentation breakdown (local sweep):

| Augmentation | n | Mean OOD | Mean weakness (norm) |
| --- | ---: | ---: | ---: |
| `full_cyclic` (orbit completion) | 54 | 0.939 | 0.951 |
| `partial_cyclic` (partial orbit) | 48 | 0.618 | 0.320 |
| `wrong_random` | 50 | 0.084 | 0.140 |
| `wrong_reflection` | 50 | 0.017 | 0.117 |
| `none` | 54 | 0.000 | 0.141 |

This confirms the directional story: augmentations that approximately respect the symmetry produce models with high weakness and high OOD. Wrong/random augmentation neither raises weakness nor OOD.

### 4.3 Modal-parallel replication on 1024 MLPs

We re-run the sweep at 4× scale on Modal (8 shards × 128 models = 1024 MLPs, identical hyperparameter space and seed protocol). The result is consistent with the local run and tightens the correlation estimates:

| Predictor | Pearson r | Spearman ρ |
| --- | ---: | ---: |
| **`weakness_oracle_norm`** | **+0.813** | **+0.580** |
| `weakness_partial_cyclic_norm` | +0.804 | +0.575 |
| parameter $L_2$ | +0.273 | +0.353 |
| Hutchinson sharpness proxy | +0.134 | +0.145 |
| `weakness_wrong_group_norm` (control) | **−0.116** | −0.050 |
| held-out validation accuracy | +0.089 | +0.043 |
| training loss | −0.048 | +0.119 |

Per-augmentation OOD/weakness (1024 models):

| Augmentation | n | Mean OOD | Mean weakness (norm) |
| --- | ---: | ---: | ---: |
| `full_cyclic` | 218 | 0.967 | 0.963 |
| `partial_cyclic` | 179 | 0.621 | 0.358 |
| `wrong_random` | 194 | 0.100 | 0.137 |
| `wrong_reflection` | 217 | 0.012 | 0.129 |
| `none` | 216 | 0.000 | 0.118 |

The 1024-model replication confirms the headline: `weakness_oracle_norm` is the dominant predictor (Pearson r = +0.81), wrong-group and validation/loss controls are correctly null or weakly negative, parameter L₂ and sharpness contribute only secondary signal. Across both sweeps the per-augmentation gradient is monotone in mean weakness, with `full_cyclic` saturating at 97% OOD and `none` / `wrong_reflection` at ≤ 1% OOD.

## 5. Wrong-, Noisy-, and Data-Inferred-Group Ablations

The benchmark exposes a precise operating regime for weakness.

- **Wrong group** (random non-cyclic permutations of equal size): selects local shortcut in $\ge 99.8\%$ of cyclic trials and $\ge 98.2\%$ of dihedral trials. The expected failure.
- **Noisy group** (half the true group plus one random element): still recovers the invariant in 100% of cyclic and 97.2% of dihedral trials. Weakness is robust under moderate group degradation.
- **Data-inferred group** (translations pairwise-consistent with the training pairs; no oracle access): recovers the truth in 100% of cyclic and 100% of dihedral trials. **This is the critical result for practicality: weakness recovers the invariant without oracle knowledge of the symmetry group, using only the training data.**

For color permutation ($S_n$), the data-inferred group reduces to a coarse cyclic prior and weakness drops to 13.8%. For parity ($\mathbb{Z}_2$), no group is rich enough to separate truth from identity-on-coset. These two negative results delineate the operating regime of weakness as a selector.

## 6. Related Work

- **Flat minima.** Hochreiter and Schmidhuber [5] introduced flatness as a generalization predictor. Keskar et al. [8] formalized it for SGD-vs-large-batch training. Dinh et al. [4] showed that strict Hessian sharpness is not reparameterization-invariant. Bennett [2] strengthens this into a formal critique: parameter-space flatness can be inflated arbitrarily by function-preserving reparameterization. Our neural sweep is consistent with this finding; Hutchinson sharpness is a weak predictor of OOD (Pearson r ≤ +0.14) compared with weakness (r = +0.81).
- **Symmetries in deep learning.** Perin and Deny [10] prove that conventional supervised networks cannot extrapolate partially-observed cyclic symmetries; their NTK theory predicts the symbolic-level failure we observe in the cyclic and dihedral families.
- **MDL, Solomonoff induction.** Hutter [6] and Valle-Perez et al. [13] argue that simplicity-prior compressors approximate Solomonoff induction. MDL is closely related to but distinct from weakness — weakness counts compatibilities, not description lengths — and our `mdl_program` and `compression` selectors fail the symbolic benchmark while weakness succeeds.
- **Bennett's weakness.** Bennett [1] defines weakness as compatible-world volume and argues weakness, not simplicity, is the upper bound on adaptive intelligence. Our benchmark operationalizes this conjecture and measures it on symbolic and neural learners.
- **Implicit bias / grokking.** Power et al. [11] and Liu et al. [9] document the transition from memorization to generalization correlating with the emergence of structure in the learned function. Our observation that weakness rises monotonically with OOD across augmentation regimes is consistent with their framing.
- **Equivariant networks.** Cohen and Welling [3] and Kondor and Trivedi [7] introduced architectures that bake in equivariance — equivalent to upper-bounding weakness by construction. Our benchmark provides a *measurement* framework that does not require architectural priors and recovers the symmetry-generalization link from data.
- **Group inference from data.** Van der Ouderaa et al. [14] propose Bayesian model selection for learning data symmetries; our data-inferred-group selector is a simpler enumerative cousin that succeeds when the candidate group is enumerable and fails otherwise.

## 7. Limitations and Negative Results

1. The symbolic benchmark uses small finite domains ($n \le 13$). Scaling to larger groups requires sub-sampling the equivariance check or learning a transformation generator set.
2. Weakness fails on parity (|G| too small) and S_n (|G| too large for the candidate pool to separate). The benchmark inherits this limitation; we make it explicit.
3. The Hutchinson sharpness proxy is one of many flatness measures. A full study should include PAC-Bayes-style perturbation sensitivity and the Bennett reparameterization-invariant variant; we expect similar conclusions.
4. The neural sweep uses small MLPs on synthetic cyclic tasks. Scaling to image classification, language modeling, and reinforcement learning is future work and the natural next milestone.
5. Transformation discovery in this paper is heuristic; learning the group from data with neural infrastructures (cf. van der Ouderaa et al., 2024) is the natural next step.

## 8. Reproducibility

All code, benchmarks, and pilot artifacts are released. Run:

```bash
# Symbolic multi-family benchmark (4 families × 500 trials × 11 selectors)
python3 -m experiments.symbolic_weakness.benchmark \
    --trials-per-family 500 --seed 20260609 \
    --out artifacts/symbolic_weakness/multi_family_500.json

# Neural sweep (256 small MLPs)
python3 -m experiments.symbolic_weakness.neural \
    --n-models 256 --epochs 2000 --base-seed 20260609 \
    --out artifacts/symbolic_weakness/neural_sweep_v3.json

# Modal-parallel neural sweep (Doppler-scoped credentials)
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/symbolic_weakness/modal_neural_sweep.py \
    --n-shards 8 --models-per-shard 128 --epochs 2000 \
    --base-seed 20260609 \
    --out artifacts/symbolic_weakness/modal_neural_sweep_v1.json
```

Both produce JSON artifacts with per-trial records, per-(family, selector) Wilson confidence intervals, and per-model artefacts (function table, weakness scores, sharpness, OOD accuracy). Unit tests pin every separation gap and ablation:

```bash
python3 -m unittest discover -s tests -p "test_symbolic*"
```

## 9. Discussion

The discriminating quantity between local shortcut and globally invariant rule, on the families of tasks where they are simultaneously train-perfect, is *symmetry-compatible-hypothesis volume*. This is a measurable, intervention-friendly, reparameterization-invariant quantity, not a parameter-space artifact. It generalizes Bennett's weakness to neural function tables, and gives a concrete empirical bridge between (a) the manifold-hypothesis intuition that intelligence requires symmetry-preserving compression and (b) the practical question of "which heuristic should I trust when training loss is tied?"

When the candidate transformation group is too small (parity) or too large/uninformative (full symmetric group), weakness ceases to discriminate. This is not a defect — it is a precise statement of when symmetry-volume is, and is not, load-bearing. The data-inferred result shows that the right group can frequently be recovered from training data alone, without oracle access, which is the version of the result that matters for practical model selection.

The path forward is to (i) learn the group from data using neural infrastructures, (ii) scale the candidate pool to neural-architecture search, and (iii) integrate weakness into training-time regularization. We invite the community to extend this benchmark to compositional symmetries ($\mathbb{Z}_n \times \mathbb{Z}_m$), natural-language paraphrase invariants, and image-classification tasks where partial-orbit training is the norm.

## Acknowledgements and Code

The benchmark, neural sweep, Modal entrypoint, summarization tools, and 21 unit tests are at <https://github.com/jawauntb/research-derived-experiments> under `experiments/symbolic_weakness/`.

## References

[1] **Bennett, M. T.** *How to Create Conscious Machines.* arXiv:2403.00644 (2024). Develops the stack-theoretic / weakness-maxing framework that motivates this paper. Key chapters: II (weakness as compatible-completion volume), V–VIII (stack of abstraction layers), XI–XII (self-repair and intelligence).

[2] **Bennett, M. T.** *Are Flat Minima an Illusion?* arXiv preprint (2024). Argues that function-preserving reparameterization inflates Hessian-based sharpness without changing predictions, so parameter-space flatness cannot be the fundamental cause of generalization. Introduces "weakness" as a reparameterization-invariant alternative.

[3] **Cohen, T. and Welling, M.** Group Equivariant Convolutional Networks. *ICML* (2016). Architectures that bake in group equivariance — equivalent to upper-bounding weakness by construction.

[4] **Dinh, L., Pascanu, R., Bengio, S., and Bengio, Y.** Sharp Minima Can Generalize for Deep Nets. *ICML* (2017). First explicit demonstration that strict Hessian sharpness is not reparameterization-invariant.

[5] **Hochreiter, S. and Schmidhuber, J.** Flat Minima. *Neural Computation* 9(1):1–42 (1997). Foundational flatness-as-generalization argument.

[6] **Hutter, M.** *Universal Artificial Intelligence: Sequential Decisions Based on Algorithmic Probability.* Springer (2005). Develops the formal Solomonoff–MDL framework that the `mdl_program` and `compression` baselines approximate.

[7] **Kondor, R. and Trivedi, S.** On the Generalization of Equivariance and Convolution in Neural Networks to the Action of Compact Groups. *ICML* (2018). Generalizes equivariance to arbitrary compact groups; the "with-action" formulation we use is a discrete-group special case.

[8] **Keskar, N. S., Mudigere, D., Nocedal, J., Smelyanskiy, M., and Tang, P. T. P.** On Large-Batch Training for Deep Learning: Generalization Gap and Sharp Minima. *ICLR* (2017). Formalized SGD's preference for flat minima.

[9] **Liu, Z., Michaud, E. J., and Tegmark, M.** Omnigrok: Grokking Beyond Algorithmic Data. *ICLR* (2023). Documents grokking as a phase transition from memorization to generalization in trained networks.

[10] **Perin, A. and Deny, S.** A Neural Kernel Theory of Symmetry Learning. arXiv:2412.11521 (2024). Proves that conventional supervised networks cannot extrapolate partially-observed cyclic symmetries; NTK analysis of generalization in symmetric datasets.

[11] **Power, A., Burda, Y., Edwards, H., Babuschkin, I., and Misra, V.** Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets. *ICLR Workshop* (2022). Documents the memorization → generalization transition on modular arithmetic; consistent with our observation that learned-function weakness rises before OOD accuracy.

[12] **Solomonoff, R. J.** A Formal Theory of Inductive Inference, Parts I and II. *Information and Control* 7(1):1–22, 7(2):224–254 (1964). The original universal-prior framework underlying the `mdl_program` selector.

[13] **Valle-Pérez, G., Camargo, C. Q., and Louis, A. A.** Deep Learning Generalizes Because the Parameter–Function Map is Biased Towards Simple Functions. *ICLR* (2019). Empirical/theoretical argument for a simplicity bias in over-parameterized networks; we show this simplicity bias is insufficient to recover the invariant on cyclic and dihedral families.

[14] **Van der Ouderaa, T. F. A., van der Wilk, M., and Welling, M.** Learning Layer-wise Equivariances Automatically using Gradients. *ICLR* (2024). Proposes neural mechanisms for inferring data symmetries; the natural successor to our enumerative `weakness_data_inferred` selector.
