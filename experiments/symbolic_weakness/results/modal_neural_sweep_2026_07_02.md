# Neural Symbolic Weakness Sweep Summary

Runner: `experiments/symbolic_weakness/modal_neural_sweep.py`. Backend: Modal
CPU workers. Raw JSON is gitignored at
`artifacts/symbolic_weakness/modal_neural_sweep_2026_07_02.json`.

Total models: 4096
Mean OOD accuracy: 0.3328
Fraction with perfect OOD (>0.99): 0.2349
Manifest: `{"base_seed": 20260702, "epochs": 2000, "models_per_shard": 128, "modulus": 11, "n_shards": 32, "total_models": 4096, "train_window": 3}`

## Reading

This 4096-model Modal rescale confirms the flagship neural result with tighter
sampling than the prior 1024-model run. True-group weakness remains the strongest
predictor of OOD accuracy (Pearson r = **+0.8085**, Spearman ρ = **+0.5417**).
Classical predictors remain much weaker: parameter L2 reaches r = +0.2533, held-out
validation r = +0.0924, sharpness r = +0.0848, and final train loss r = −0.0249.
Wrong-group weakness is correctly negative/null (Pearson r = **−0.1040**).

## Predictors of OOD accuracy

| Predictor | Mean | Stdev | Pearson w/ OOD | Spearman w/ OOD |
| --- | ---: | ---: | ---: | ---: |
| weakness_oracle_norm | 0.3348 | 0.3938 | +0.8085 | +0.5417 |
| weakness_partial_cyclic_norm | 0.1913 | 0.1523 | +0.7940 | +0.5343 |
| parameter_l2 | 10.0035 | 5.1376 | +0.2533 | +0.3313 |
| weakness_wrong_group_norm | 0.1312 | 0.1448 | -0.1040 | -0.0218 |
| held_out_validation_accuracy | 0.9685 | 0.1747 | +0.0924 | +0.0427 |
| sharpness_proxy | 2.9483 | 12.9705 | +0.0848 | +0.1617 |
| abs_sharpness_proxy | 2.9578 | 12.9683 | +0.0847 | +0.1596 |
| final_train_loss | 0.1260 | 0.4250 | -0.0249 | +0.1200 |

## Per-augmentation breakdown

| Augmentation | n | Mean OOD | Mean weakness (norm) |
| --- | ---: | ---: | ---: |
| full_cyclic | 805 | 0.9434 | 0.9545 |
| none | 821 | 0.0000 | 0.1157 |
| partial_cyclic | 806 | 0.6438 | 0.3678 |
| wrong_random | 841 | 0.0877 | 0.1230 |
| wrong_reflection | 823 | 0.0135 | 0.1315 |
