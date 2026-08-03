# Autocatalytic-Artwork Pair (Theorems AA-1, AA-2 witness)

Companion instrument for
[`papers/autocatalytic_artwork/paper.md`](../../papers/autocatalytic_artwork/paper.md).

Hypothesis: Theorem AA-1 (Monotone competence under Bayesian update)
says that if the audience updates its compiler-belief `mu_t` on
observed `(s_t, e_t)` pairs by Bayes' rule and the true compiler lies
in the candidate family, the expected one-step predictive
log-likelihood
`LL_t = E_{s,e ~ P_S x K_a}[log K̄_mu_t(e | s)]`
is monotone non-decreasing in `t`. Theorem AA-2 says the Bayesian
update is literally the Boltzmann compiler-ecology update of Theorem
CT-2 with reward `r_t(theta) = log K_theta(e_t | s_t)` and inverse
temperature `beta = 1`.

Method: build a 6-step, 3-compiler world (`|S| = |E| = 4`; `K_a`
diagonal 0.85/0.05, `K_b` shifted 0.85/0.05, `K_c` uniform 0.25; true
compiler `K_a`; uniform prior). For 200 seeded Mulberry32 runs, draw a
trajectory, run the Bayesian update in lockstep with the equivalent
Boltzmann update, and compute the analytical per-posterior expected LL
in closed form over the 16 `(s, e)` pairs at every `t in {0..6}`. Also
compute a frozen-uniform-prior baseline LL for every `t`.

Pre-registered gates (all four pass):

- `aa1_predictive_log_likelihood_non_decreasing_in_expectation`: mean
  over runs of `LL_t` non-decreasing in `t = 0..6` (tolerance `1e-6`).
- `aa1_posterior_concentrates_on_true_compiler`: mean of `mu_6(K_a)`
  over runs `>= 0.9`.
- `aa2_reduces_to_compiler_ecology`: max per-theta gap between the
  Bayesian and Boltzmann posteriors across all 200 runs and 7 belief
  snapshots `<= 1e-12`.
- `aa_audience_beats_uniform_baseline`: at `t = 6`, mean
  Bayesian-audience LL exceeds frozen-uniform baseline by `>= 0.1` nats.

Result: all four gates pass. The seven-point mean LL sequence is
`(-1.0778, -0.7907, -0.7086, -0.6584, -0.6510, -0.6280, -0.6169)`
(monotone); mean `mu_6(K_a) = 0.9263`; max Bayes-Boltzmann posterior
gap `<= 3e-16`; baseline gap at `t = 6` is `0.461` nats. The
analytical asymptote (`-H(K_a) = -0.5875` nats) is `~0.03` nats below
the `t = 6` audience LL, consistent with AA-1's convergence corollary.

Run:

```bash
python3 experiments/autocatalytic_artwork_pair/experiment.py
```
