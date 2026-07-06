# Experiment Design: Teacher-Free Suite C Inquiry

## Policy Interface

Use the same observable feature surface as the current learned probe head where
possible:

- perceived error;
- perceived surprise;
- error jump;
- surprise jump;
- effort;
- improvement;
- time since probe;
- recent probe rate;
- source-is-affected proxy or learned source estimate;
- bucket index or learned bucket embedding.

The teacher-free condition must not consume teacher actions or teacher
probabilities.

## Reward-Trained Policy Search

Episode reward:

```text
R =
  + 2.0 * recovery_pass
  + 1.0 * min(first_selectivity_ratio / 5, 1)
  + 1.0 * min(second_reopen_ratio / 2, 1)
  + 0.5 * no_false_calm
  - 0.004 * total_probes
  - 1.5 * false_calm_failure
  - 1.0 * stale_or_wrong_control_pass
```

Training options:

- evolutionary strategy over small MLP parameters;
- REINFORCE with Bernoulli probe actions;
- cross-entropy method over policy parameters;
- fitted Q/value-of-information head from intervention outcomes.

Recommended first implementation: cross-entropy method. It is dependency-light,
deterministic with fixed seeds, and compatible with the current NumPy harness.

## Self-Supervised Value-of-Information Policy

For each probe event, record:

- pre-probe attribution error;
- post-probe attribution error after a fixed lag;
- probe cost;
- whether the bucket is affected after shift;
- whether later recovery occurs.

Train a value head to predict:

```text
VOI = error_reduction_after_lag - lambda_cost * probe_cost
```

Policy fires when predicted VOI exceeds threshold. Controls corrupt the input
signal, not the outcome labels.

## Public Row Schema

Every row should include:

- training regime;
- seed;
- condition;
- total probes;
- final affected MAE;
- first-shift selectivity;
- second-shift reopenability;
- no-false-calm;
- recovery pass;
- control pass/fail labels;
- training loss fields that prove no teacher label was used.

## Figure Plan

Main figures for the eventual paper:

1. C1-C6 gate status for teacher-free policy and controls.
2. Recovery vs probe cost scatter, with scheduled/oracle references.
3. Selectivity and reopenability bars.
4. Control failure reasons: stale, wrong, suppressed, matched random.
5. Training curve: held-out reward and gate pass rate over search iterations.

## Expected Reviewer Questions

- Is the policy just rediscovering the hand-coded teacher?
  - Answer with T1 audit, different policy shape, and training objective.
- Does reward training exploit the gates?
  - Answer with held-out seeds, controls, and false-calm audits.
- Is source-is-affected too privileged?
  - Run an ablation with learned/noisy source estimate.
- Does this transfer to long-horizon agents?
  - This remains the next benchmark after teacher-free Suite C.

