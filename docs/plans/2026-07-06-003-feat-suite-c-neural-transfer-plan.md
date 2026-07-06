---
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
title: "feat: Suite C Neural Probe Transfer"
created: 2026-07-06
---

# feat: Suite C Neural Probe Transfer

## Goal Capsule

Move Suite C one step beyond a hand-specified finite probe policy by training a
small learned probe head, evaluating it on held-out seeds, and requiring the same
C1-C6 re-engagement gates with stale-signal, wrong-signal, and signal-suppression
controls.

The claim is deliberately bounded: this is a learned-policy transfer pilot inside
the Suite C simulator, not evidence for consciousness, broad autonomy, or open
world robustness.

## Discovery-Regime Audit

Current regime:
- Artifact types: Suite C rows, summaries, benchmark cards, paper PDFs, critical
  reviews, and local-only raw payloads.
- Operations: deterministic two-shift world-change harness, hand-specified
  decision-layer policies, matched-random controls, Modal L4 artifact generation.
- Gates/verifiers: C1-C6 terminal Suite C gates, false-calm rejection, cost
  coupling, publication guard, lint/type/test checks.
- Known limitations: finite controlled simulator; no neural policy transfer yet.

Action class:
- Search/discovery: search if the learned head only imitates the old policy;
  discovery-level only if the repo gains a durable learned-policy artifact type
  with controls that the hand-specified result did not previously require.

Pre-registered gate:
- Acceptance rule: the learned head must pass C1-C6 on held-out evaluation seeds,
  and all three learned-policy controls must fail in their intended way.
- Withheld/rejected rule: do not claim neural transfer if recovery requires high
  scheduled/oracle probing, if matched-random budget matches selectivity, if
  signal suppression creates false calm, or if stale/wrong signals pass.

## Implementation Units

### U1. Preregistration and learned-head benchmark

Create `experiments/world_responds/suite_c_neural_transfer.py` with a
dependency-light NumPy MLP probe head. It should collect teacher traces from
`burst_then_refractory`, train on training seeds, calibrate a threshold on
calibration seeds, and evaluate held-out seeds.

Controls:
- `stale_signal_head`: affected-bucket perceived error/surprise stay near the
  pre-shift baseline after world change.
- `wrong_signal_head`: perceived error/surprise are rotated to the wrong source
  bucket.
- `signal_suppression_head`: the policy receives suppressed perceived stress
  signals while actual attribution error remains high.
- `matched_random_learned_budget`: random inquiry at the learned head's per-seed
  probe budget.

### U2. Artifacts and paper

Add a summarizer that writes:
- `experiments/world_responds/results/suite_c_neural_transfer_2026_07_06.md`
- `experiments/world_responds/results/suite_c_neural_transfer_2026_07_06.json`
- `papers/habituated_reengagement/suite_c_neural_probe_transfer.md`
- `papers/habituated_reengagement/suite_c_neural_probe_transfer.pdf`
- `docs/paper_reviews/suite_c_neural_probe_transfer_critical_review.md`
- `papers/habituated_reengagement/figures/suite_c_neural_*.png`

### U3. Modal L4 runner and tests

Add `experiments/world_responds/modal_suite_c_neural_transfer.py` with budget
guards, benchmark dispatch, artifact generation, and a quality cell. Add focused
tests in `tests/test_world_responds_suite_c_neural_transfer.py`.

### U4. Verification, archive, PR, merge

Run benchmark and quality gates on Modal L4 only, archive paper/report artifacts
to a descriptive external folder under `/Users/jawaun/Metaphysics of
Intelligence`, rebase on fresh main, commit, push, open a PR, and merge if green.
