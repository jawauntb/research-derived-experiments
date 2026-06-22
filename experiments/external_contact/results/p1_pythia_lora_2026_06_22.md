# External Contact P1 -- Pythia LoRA Weakness -> OOD

Date: 2026-06-22
Code: `experiments/external_contact/modal_p1_pythia_lora.py`
Metrics: `experiments/external_contact/p1_lora_metrics.py`
Pre-registration: `docs/external_contact_preregistration.md` (Prediction 1, frozen 2026-06-18)
Runbook: `docs/external_contact_runbook.md`
Artifact: `artifacts/external_contact/p1_pythia_lora.json` (gitignored)
Modal run: 3 size-sharded A10G workers, one worker per Pythia size.

## Question

Does the lab's learned-function weakness signal transfer to an external open-weights model family when the model is allowed to adapt through LoRA, rather than being frozen behind a linear probe?

The earlier Tier-B linear-probe run (`p1_pythia_2026_06_22.md`) was degenerate: all 27 cells had OOD accuracy 0.0. This run is the promised non-degenerate repair. It fine-tunes public Pythia checkpoints with LoRA adapters on a strict-subset modular-shift task, extracts the model's argmax function table over `{0..n-1}` by answer-token NLL, and applies the same P1 weakness, wrong-group, and classical-predictor gate.

## Command

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
        experiments/external_contact/modal_p1_pythia_lora.py \
        --sizes 70m,160m,410m --ns 13,17,23 --seeds 3 \
        --train-frac 0.5 --epochs 160 --objective lm \
        --base-seed 20260618 \
        --out artifacts/external_contact/p1_pythia_lora.json
```

Implementation details:

- External checkpoints: `EleutherAI/pythia-70m`, `pythia-160m`, `pythia-410m`.
- Task: `f(x) = (x + offset) mod n`, `n in {13, 17, 23}`, strict random train subset at `train_frac=0.5`, held-out complement as OOD.
- Objective: LoRA causal-LM answer-token training. At evaluation, every candidate answer `0..n-1` is scored by mean answer-token NLL; argmin gives the function-table entry.
- LoRA: rank 8, alpha 16, dropout 0.05, target modules `query_key_value`, `dense_h_to_4h`, `dense_4h_to_h`, `dense`.
- Sharpness proxy: finite-difference Rademacher curvature proxy on the LoRA adapter LM loss.

Classifier-head diagnostics were also run before the LM objective: 70m / n=13 / 3 seeds at train_frac 0.5 and 0.75. Both were all-zero OOD and are treated as setup diagnostics, not the headline claim.

## Result

The LoRA run is no longer all-zero, but it **does not pass P1**. It hard-kills the literal external-transfer threshold.

| Statistic | Value |
|---|---:|
| Valid cells | 27 |
| OOD accuracy mean | 0.0285 |
| OOD accuracy max | 0.3333 |
| OOD unique values | 5 |
| Train accuracy | 1.000 in every cell |
| `rho(weakness_oracle_norm, OOD)` | **-0.0817** |
| `rho(weakness_wrong_group_norm, OOD)` | -0.0817 |
| `rho(final_train_loss, OOD)` | -0.0423 |
| `rho(ood_nll, OOD)` | **-0.4550** |
| `rho(param_count, OOD)` | +0.3610 |
| `rho(pythia_l2, OOD)` | -0.1418 |
| `rho(sharpness_proxy, OOD)` | -0.0104 |
| Best classical `|rho|` | **0.4550** (`ood_nll`) |
| Weakness margin over best classical | -0.3734 |
| P1 pass | **false** |
| P1 hard kill | **true** |
| Wrong-group soft kill | false |

By size and modulus:

| Size | n | OOD accuracies across seeds | Weakness values |
|---|---:|---|---|
| 70m | 13 | 0.000, 0.000, 0.000 | 0.077, 0.077, 0.077 |
| 70m | 17 | 0.000, 0.000, 0.000 | 0.059, 0.059, 0.059 |
| 70m | 23 | 0.000, 0.000, 0.000 | 0.043, 0.043, 0.043 |
| 160m | 13 | 0.000, 0.000, 0.000 | 0.077, 0.077, 0.077 |
| 160m | 17 | 0.111, 0.000, 0.000 | 0.059, 0.059, 0.059 |
| 160m | 23 | 0.000, 0.091, 0.000 | 0.043, 0.043, 0.043 |
| 410m | 13 | 0.143, 0.000, 0.000 | 0.077, 0.077, 0.077 |
| 410m | 17 | 0.333, 0.000, 0.000 | 0.059, 0.059, 0.059 |
| 410m | 23 | 0.091, 0.000, 0.000 | 0.043, 0.043, 0.043 |

## Interpretation

This is an honest negative external-contact result, not another tooling block. Unlike the frozen linear-probe run, the dependent variable is not constant: 5 cells get non-zero held-out accuracy, and the OOD column has five distinct values. The gate can therefore be evaluated.

The failure mode is specific:

- LoRA fits the training subset perfectly in every cell.
- Pythia-70m still gets zero OOD everywhere.
- Larger models sometimes recover a few held-out points, with the strongest cell at 410m / n=17 / seed 20260618 reaching OOD 0.333.
- The learned function tables remain at the identity-only equivariance floor: `weakness_oracle_norm = 1/n` for every cell at a given modulus.
- The wrong-group score equals the oracle score, because both only see the identity element. The wrong-group control does not soft-kill P1 by correlation magnitude, but it also provides no symmetry-specific rescue.
- Classical predictors are stronger than weakness. OOD NLL is the best predictor by absolute Spearman rho, and parameter count is also directionally stronger than weakness.

Therefore the literal pre-registered claim:

```text
weakness rho >= +0.5, beats every classical predictor by >= 0.25 in |rho|,
and wrong-group |rho| <= 0.15
```

does **not** survive this Pythia LoRA Tier-B contact.

## Allowed Claim

P1 should move from "unsettled because the linear probe degenerated" to:

```text
The Pythia LoRA Tier-B operationalization is evaluable and negative. On
pythia-70m/160m/410m, partial-orbit modular-shift LoRA training produces
perfect train fit and small but nonzero OOD behavior, but measured
learned-function weakness stays at the identity-only floor and does not
predict held-out OOD. The literal P1 external-transfer threshold is hard-killed
for this setup.
```

Do **not** overclaim:

- Do not say the original internal weakness result is false.
- Do not say no external model can show weakness->OOD transfer.
- Do not say Pythia cannot learn modular arithmetic under any fine-tuning regime.
- Do say that the highest-ceiling external field-claim candidate, as pre-registered for this LoRA Tier-B setup, failed.

## Discovery-Regime Audit

- **Old regime:** P1 was the program's cleanest potential external field claim, but the first Tier-B attempt used frozen Pythia features plus a linear head and all 27 cells had OOD 0.0. That left P1 unevaluable rather than falsified.
- **Transition:** This branch added a LoRA causal-LM objective and answer-token NLL function-table extraction. The external model now adapts its representation; the OOD column is no longer constant.
- **Transported evidence:** same Pythia sizes, same `n in {13,17,23}`, same seed schedule, same partial-orbit split, same cyclic-group weakness score, same wrong-group control, and the same classical-predictor acceptance gate.
- **Rejected alternatives:** "P1 only failed because Pythia was frozen behind a linear probe" is rejected for the tested LoRA objective. "Any nonzero Pythia OOD behavior will reveal the weakness signal" is rejected. "Scale alone is irrelevant" is also rejected directionally: param count has stronger positive rho than weakness in this panel.
- **Residual finding:** the LoRA models learn sparse held-out points without producing symmetry-compatible function tables. Behavior improves slightly with size, but the measured learned-function symmetry stays at the identity floor.
- **Claim boundary:** P1 is a hard-kill for this external LoRA Tier-B configuration; the broader internal weakness claim remains internally supported but externally narrowed.
- **Next operation:** either pursue a stronger external P1 variant that uses public grokking checkpoints or full fine-tuning with richer two-input modular addition, or stop optimizing P1 and move effort to the already stronger next internal routes: trainable neural 2B modules or open-ended intervention/apparatus discovery.
