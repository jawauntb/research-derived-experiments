# Neural Correlation Checks

Date: 2026-07-02

This note adds confidence intervals and an augmentation fixed-effect check for
the cyclic-prefix MLP sweeps reported in the weakness/OOD paper.

## Inputs

- 256 local sweep summary:
  `experiments/symbolic_weakness/results/neural_sweep_v3_2026_06_09.md`
- 1024 Modal sweep summary:
  `experiments/symbolic_weakness/results/modal_neural_sweep_v1_2026_06_09.md`
- 4096 Modal raw JSON:
  `artifacts/symbolic_weakness/modal_neural_sweep_2026_07_02.json`
  (gitignored; retained locally with the Modal run)

## Fisher Intervals

Intervals use

`z = atanh(r)`, `SE(z) = 1 / sqrt(n - 3)`, and
`CI_95 = tanh(z +/- 1.959963984540054 * SE)`.

| Run | Predictor | Pearson r | Fisher 95% CI |
| --- | --- | ---: | --- |
| 256 local | `weakness_oracle_norm` | +0.8169 | (+0.7716, +0.8540) |
| 256 local | `weakness_partial_cyclic_norm` | +0.8035 | (+0.7553, +0.8431) |
| 256 local | Hutchinson sharpness | +0.1294 | (+0.0069, +0.2481) |
| 256 local | parameter L2 | +0.0991 | (-0.0238, +0.2190) |
| 256 local | held-out validation | +0.0960 | (-0.0269, +0.2161) |
| 256 local | final train loss | -0.0306 | (-0.1526, +0.0923) |
| 256 local | wrong-group weakness | -0.1293 | (-0.2480, -0.0068) |
| 1024 Modal | `weakness_oracle_norm` | +0.8132 | (+0.7914, +0.8330) |
| 1024 Modal | `weakness_partial_cyclic_norm` | +0.8042 | (+0.7814, +0.8248) |
| 1024 Modal | parameter L2 | +0.2731 | (+0.2154, +0.3289) |
| 1024 Modal | Hutchinson sharpness | +0.1339 | (+0.0732, +0.1936) |
| 1024 Modal | held-out validation | +0.0887 | (+0.0276, +0.1492) |
| 1024 Modal | final train loss | -0.0475 | (-0.1084, +0.0138) |
| 1024 Modal | wrong-group weakness | -0.1158 | (-0.1758, -0.0549) |
| 4096 Modal | `weakness_oracle_norm` | +0.8085 | (+0.7976, +0.8189) |
| 4096 Modal | `weakness_partial_cyclic_norm` | +0.7940 | (+0.7824, +0.8051) |
| 4096 Modal | parameter L2 | +0.2533 | (+0.2244, +0.2818) |
| 4096 Modal | held-out validation | +0.0924 | (+0.0620, +0.1227) |
| 4096 Modal | Hutchinson sharpness | +0.0848 | (+0.0543, +0.1151) |
| 4096 Modal | final train loss | -0.0249 | (-0.0555, +0.0057) |
| 4096 Modal | wrong-group weakness | -0.1040 | (-0.1342, -0.0736) |

## Augmentation Fixed-Effect Check

The main confound risk is that augmentation condition raises both weakness and
OOD accuracy. On the 4096-model raw records, residualize both OOD accuracy and
`weakness_oracle_norm` by subtracting their augmentation-condition means.

Residual correlation:

- Pearson r = +0.4883
- Fisher 95% CI = (+0.4647, +0.5113)

Equivalent fixed-effect regression:

`OOD_i = alpha_augmentation(i) + beta * weakness_oracle_norm_i + epsilon_i`

- beta = +0.3652
- standard error = 0.0102
- 95% CI = (+0.3452, +0.3853)

Within-condition correlations:

| Augmentation | n | Pearson r | Fisher 95% CI |
| --- | ---: | ---: | --- |
| `full_cyclic` | 805 | +0.4716 | (+0.4160, +0.5236) |
| `partial_cyclic` | 806 | +0.6242 | (+0.5802, +0.6647) |
| `wrong_reflection` | 823 | +0.0202 | (-0.0482, +0.0884) |
| `wrong_random` | 841 | +0.0093 | (-0.0583, +0.0769) |
| `none` | 821 | +0.0000 | (-0.0684, +0.0684) |

Interpretation: the headline weakness/OOD correlation is partly
augmentation-mediated, but a substantial learned-function signal remains after
controlling for augmentation condition. The within-condition signal is visible
where OOD accuracy has real variance (`partial_cyclic` and `full_cyclic`) and
near zero where OOD is almost degenerate (`none`, `wrong_random`,
`wrong_reflection`).
