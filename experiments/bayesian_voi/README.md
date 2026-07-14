# Exact Bayesian value of information (M-208)

This local-CPU benchmark tests the primer's warning that current prediction
error and `error²/(K+1)` are not the definition of value of information.  A
two-state conjugate-style binary estimation model permits exact enumeration of
both probe outcomes.  It reports current error, posterior variance, the
printed heuristic, mutual information, learner-assumed EVSI, true expected
regret reduction, and oracle EVSI.

Three preregistered regimes are preserved:

- `learnable_uncertainty`: informative probes reduce decision error.
- `irreducible_noise`: current error is high, but all probes are independent of
  the latent state and exact EVSI is zero.
- `model_misspecification`: a high-information assumed signal is actually
  uninformative, while a weaker correctly specified signal is useful.

Run deterministically from the repository root:

```bash
python experiments/bayesian_voi/experiment.py
```

The public-safe summary is written to
`results/bayesian_voi_summary.json`; it contains no sampled rows, timestamps,
host paths, or secrets.
