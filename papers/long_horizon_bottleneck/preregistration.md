# Preregistration: Long-Horizon Moved Bottleneck

Frozen intent: test whether future control relevance moves finite memory
geometry in a long-horizon agent.

## Question

When one early clue slot is made future-critical for a delayed decision, does
the agent's final memory-state sensitivity become specifically larger for that
slot, and does the peak move when the critical slot is moved?

## Intervention

Four early clue slots are shown with matched frequency and salience. The
critical slot is moved across registered values `{0, 1, 2, 3}`.

Conditions:

- `bottleneck`: final action must recover the bit shown at the critical early slot.
- `visible_control`: final action is visible at the query token; early bits are
  matched distractors.

Architectures:

- `gru`
- `transformer`

## Primary Metric

For each slot `s`, create paired evaluation sequences that differ only in the
bit at slot `s`. Measure the mean L2 displacement of the final hidden state.
Z-score the four slot densities within model. Primary specificity is:

```text
z_density(critical_slot) - mean z_density(noncritical_slots)
```

## Gates

- **G1 behavior:** bottleneck mean accuracy >= 0.90.
- **G2 metric transport:** bottleneck memory-specificity 95% bootstrap CI lower bound > 0.
- **G3 rank:** critical-slot memory-density rank percentile > 0.50.
- **G4 visible-control null:** visible-control mean specificity < 0.50.

## Cost Guard

The default runner uses Modal `L4`, not H100/H200. It refuses to dispatch when
the conservative timeout-based GPU-cost estimate exceeds `--budget-usd`.

## Allowed Claim

If G1-G3 pass and G4 holds, the allowed claim is a synthetic neural-agent result:
future control relevance can move final memory-state metric sensitivity in a
finite long-horizon sequence agent.

It is not a human-behavior, production-agent, or consciousness claim.
