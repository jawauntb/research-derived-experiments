# Neural Symbolic Weakness Sweep Summary

Total models: 1024
Mean OOD accuracy: 0.3360
Fraction with perfect OOD (>0.99): 0.2451
Manifest: `{"base_seed": 20260609, "epochs": 2000, "models_per_shard": 128, "modulus": 11, "n_shards": 8, "total_models": 1024, "train_window": 3}`

## Predictors of OOD accuracy

| Predictor | Mean | Stdev | Pearson w/ OOD | Spearman w/ OOD |
| --- | ---: | ---: | ---: | ---: |
| weakness_oracle_norm | 0.3457 | 0.4003 | +0.8132 | +0.5799 |
| weakness_partial_cyclic_norm | 0.1957 | 0.1557 | +0.8042 | +0.5746 |
| parameter_l2 | 10.1745 | 5.3477 | +0.2731 | +0.3532 |
| abs_sharpness_proxy | 2.4314 | 6.9531 | +0.1339 | +0.1453 |
| sharpness_proxy | 2.4296 | 6.9537 | +0.1339 | +0.1451 |
| weakness_wrong_group_norm | 0.1323 | 0.1532 | -0.1158 | -0.0501 |
| held_out_validation_accuracy | 0.9697 | 0.1714 | +0.0887 | +0.0434 |
| final_train_loss | 0.1161 | 0.4115 | -0.0475 | +0.1192 |

## Per-augmentation breakdown

| Augmentation | n | Mean OOD | Mean weakness (norm) |
| --- | ---: | ---: | ---: |
| full_cyclic | 218 | 0.9669 | 0.9630 |
| none | 216 | 0.0000 | 0.1178 |
| partial_cyclic | 179 | 0.6213 | 0.3585 |
| wrong_random | 194 | 0.1003 | 0.1369 |
| wrong_reflection | 217 | 0.0119 | 0.1286 |
