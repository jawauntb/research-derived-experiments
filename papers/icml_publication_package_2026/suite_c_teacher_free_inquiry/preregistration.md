# Preregistration: Suite C Teacher-Free Inquiry

Date: 2026-07-06

## Question

Can an inquiry policy learn Suite C re-engagement without direct teacher labels?

## Current Baseline

The current learned transfer result uses teacher traces from
`burst_then_refractory`. It passes C1-C6 in held-out finite simulator seeds, but
the teacher-dependence remains a reviewer-facing limitation.

## Training Regimes

Evaluate at least three teacher-free regimes:

1. **Reward-trained policy search**
   - Objective: maximize downstream recovery plus selectivity and reopenability,
     penalize probe cost and false calm.
   - No direct labels from the hand policy.

2. **Self-supervised value-of-information policy**
   - Estimate probe value from post-probe attribution error reduction and
     future recovery.
   - Train the head to fire when estimated value exceeds cost.

3. **Contrastive stress policy**
   - Train a policy to distinguish fresh affected stress from stale, wrong, and
     suppressed stress using intervention outcomes rather than teacher labels.

## Required Controls

The accepted policy must be compared to:

- P22 learned current-replay silence baseline;
- scheduled null anchor;
- oracle source reference;
- matched random budget;
- stale signal head;
- wrong signal head;
- signal suppression head;
- reward-only or cost-only proxy policy if applicable.

## Gates

Use the existing Suite C C1-C6 gates:

- C1: silence replication by baseline;
- C2: selective first-shift re-engagement;
- C3: affected-component recovery;
- C4: no false calm;
- C5: cost-aware inquiry;
- C6: second-shift reopenability.

Add a teacher-free gate:

- T1: no direct teacher labels, teacher actions, or teacher probabilities appear
  in the training loss.

Add learned-signal gates:

- N1: stale, wrong, suppressed, and matched-random controls fail in their
  intended ways.

## Acceptance Rule

Call the result positive only if:

1. C1-C6 pass on held-out seeds;
2. T1 passes by construction and audit;
3. N1 passes;
4. total probes are below scheduled and oracle controls;
5. matched-random at the same budget fails recovery or selectivity;
6. all run artifacts are emitted as public-safe JSONL rows and summary JSON.

## Stop Conditions

Treat these as findings, not reasons to hide the run:

- recovery passes only with scheduled/oracle-like probe cost;
- policy gets quiet by suppressing stress;
- first-shift re-engagement passes but second-shift reopenability fails;
- stale or wrong signal controls pass;
- reward-only proxy policy matches the accepted policy.

