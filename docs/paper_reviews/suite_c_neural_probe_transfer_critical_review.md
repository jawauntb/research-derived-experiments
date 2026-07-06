# Critical Review: Suite C Neural Probe Transfer

Date: 2026-07-06

## Verdict

This is the right next step after the terminal hand-policy Suite C result. It moves the probe decision into a trained head while keeping the same anti-cheat structure. The result is still finite and simulator-local, but it is a stronger architecture test than another hand-tuned policy.

## Main Issues

1. **Do not call this open-ended agency.** The head is trained from a teacher inside the same simulator family.
2. **Controls are the contribution.** The stale, wrong, and suppressed signal controls are what prevent the result from being mere imitation.
3. **Teacher dependence remains.** The next stronger version should train from reward or intervention feedback rather than direct teacher labels.
4. **No model-scale claim.** This is a small NumPy MLP, not evidence about frontier agents or biological consciousness.
5. **Keep matched random.** The learned head uses 23.1 probes; budget alone must remain separated from selectivity.

## Rewrite Applied

- The paper names the learned head and reports final MAE 0.112.
- Stale control recovery rate is 0.500.
- Wrong-signal selectivity is 0.000.
- Suppressed-signal final MAE is 0.554.
- Scope text rejects consciousness, biology, and production autonomy claims.

## Contribution Opportunity

The next major step is policy learning without teacher labels: train inquiry from downstream recovery/cost rewards and require the same C1-C6 plus learned-signal controls.
