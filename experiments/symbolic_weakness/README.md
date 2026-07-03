# Symbolic Weakness Benchmark

This is the flagship benchmark for the claim:

> In shortcut-compatible symmetry tasks, out-of-distribution generalization is
> better predicted by *symmetry-compatible-hypothesis weakness* than by the
> tested training-loss, MDL/compression, parameter-space flatness/sharpness,
> parameter-norm, or held-out-validation proxies.

The benchmark has two arms.

## Arm 1 — Symbolic Multi-Family Benchmark

Four task families with biased training support that admit a local shortcut, a
memorizer, the true invariant rule, and wrong invariants:

- `cyclic_prefix_shift` — Z_n cyclic shift truth, identity-on-suffix shortcut.
- `dihedral_reflection` — D_n reflection truth, rotation shortcut.
- `parity_coset` — Z_2 parity-swap truth (negative case: |G|=2 too small).
- `color_permutation` — S_n permutation truth (partial case).

Eleven selectors are scored, including `train_loss`, `validation`, `simplicity`,
`compression`, `mdl_program`, `flatness_proxy`, `weakness_oracle`,
`weakness_wrong_group` (control), `weakness_noisy_group`,
`weakness_data_inferred`, and `random`.

`flatness_proxy` is a symbolic completion-volume proxy: it counts how many
domain positions remain unconstrained by training. It is not a Hessian or
weight-space flatness measure.

Run:

```bash
python3 -m experiments.symbolic_weakness.benchmark \
    --trials-per-family 500 --seed 20260609 \
    --out artifacts/symbolic_weakness/multi_family_500.json
```

Result report:
[results/multi_family_500_2026_06_09.md](results/multi_family_500_2026_06_09.md).

Headline:

| Family | Selector | Invariant rate | Wilson 95% CI |
| --- | --- | ---: | --- |
| cyclic | weakness_oracle / data_inferred / noisy_group | 1.000 | (0.992, 1.000) |
| cyclic | every classical baseline (loss/simplicity/compression/MDL/flatness/validation) | 0.000 | (0.000, 0.008) |
| dihedral | weakness_oracle / data_inferred | 1.000 | (0.992, 1.000) |
| color_permutation | weakness_oracle / noisy_group | 0.82–0.86 | partial |
| parity_coset | weakness_oracle | 0.000 | negative case |

## Arm 2 — Neural Sweep

Train 256+ small MLPs with diverse architecture, init scale, optimizer, learning
rate, weight decay, and data-augmentation regime. For each model compute the
full function table and measure several candidate predictors of OOD accuracy:

- training loss after the last step;
- parameter L2 norm;
- Hutchinson sharpness proxy;
- held-out (leave-one-out) validation accuracy;
- weakness under the *true* cyclic group;
- weakness under a *wrong* random-permutation group of equal size;
- weakness under a *random-label* control group;
- weakness under a *partial cyclic* (half-shift) prior.

Run locally:

```bash
python3 -m experiments.symbolic_weakness.neural \
    --n-models 256 --epochs 2000 --base-seed 20260609 \
    --out artifacts/symbolic_weakness/neural_sweep_v3.json
```

Run on Modal (Doppler-scoped credentials):

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/symbolic_weakness/modal_neural_sweep.py \
    --n-shards 8 --models-per-shard 128 --epochs 2000 \
    --base-seed 20260609 \
    --out artifacts/symbolic_weakness/modal_neural_sweep_v1.json
```

Summarize:

```bash
python3 -m experiments.symbolic_weakness.summarize_neural_sweep \
    --in artifacts/symbolic_weakness/neural_sweep_v3.json \
    --out experiments/symbolic_weakness/results/neural_sweep_summary.md
```

Result report (post-augmentation-fix, 256 models):
[results/neural_sweep_v3_2026_06_09.md](results/neural_sweep_v3_2026_06_09.md).

Larger Modal reports:
[results/modal_neural_sweep_v1_2026_06_09.md](results/modal_neural_sweep_v1_2026_06_09.md)
and
[results/modal_neural_sweep_2026_07_02.md](results/modal_neural_sweep_2026_07_02.md).
Correlation intervals and augmentation fixed-effect checks:
[results/neural_correlation_checks_2026_07_02.md](results/neural_correlation_checks_2026_07_02.md).

## Paper

Full draft: [`papers/weakness_invariance_neurips/paper.md`](../../papers/weakness_invariance_neurips/paper.md).

## Files

| File | Purpose |
| --- | --- |
| `experiment.py` | Original PR #35 pilot (cyclic prefix shift, kept for reproducibility) |
| `families.py` | Multi-family task generators and group actions |
| `selectors.py` | 11 selectors plus equivariance-count primitives |
| `benchmark.py` | Multi-family runner with Wilson 95% CIs |
| `neural.py` | Train small MLPs and compute weakness/sharpness/etc. |
| `modal_neural_sweep.py` | Modal entrypoint for parallelized neural sweeps |
| `summarize_neural_sweep.py` | Produce a markdown summary from a sweep JSON |
| `results/` | Pre-registered acceptance gates and result reports |
