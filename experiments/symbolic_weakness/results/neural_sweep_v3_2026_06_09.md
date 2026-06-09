# Neural Symbolic Weakness Sweep Summary

Total models: 256
Mean OOD accuracy: 0.3335
Fraction with perfect OOD (>0.99): 0.2383
Manifest: `{"base_seed": 20260609, "epochs": 2000, "modulus": 11, "n_models": 256, "train_window": 3}`

## Predictors of OOD accuracy

| Predictor | Mean | Stdev | Pearson w/ OOD | Spearman w/ OOD |
| --- | ---: | ---: | ---: | ---: |
| weakness_oracle_norm | 0.3406 | 0.3981 | +0.8169 | +0.5523 |
| weakness_partial_cyclic_norm | 0.1936 | 0.1546 | +0.8035 | +0.5404 |
| sharpness_proxy | 1.9823 | 3.9199 | +0.1294 | +0.1419 |
| weakness_wrong_group_norm | 0.1363 | 0.1576 | -0.1293 | -0.0572 |
| abs_sharpness_proxy | 1.9837 | 3.9193 | +0.1291 | +0.1353 |
| parameter_l2 | 10.9965 | 12.9634 | +0.0991 | +0.3082 |
| held_out_validation_accuracy | 0.9609 | 0.1941 | +0.0960 | +0.0577 |
| final_train_loss | 0.1331 | 0.4408 | -0.0306 | +0.1357 |

## Per-augmentation breakdown

| Augmentation | n | Mean OOD | Mean weakness (norm) |
| --- | ---: | ---: | ---: |
| full_cyclic | 54 | 0.9390 | 0.9514 |
| none | 54 | 0.0000 | 0.1409 |
| partial_cyclic | 48 | 0.6176 | 0.3195 |
| wrong_random | 50 | 0.0843 | 0.1400 |
| wrong_reflection | 50 | 0.0165 | 0.1173 |
