# Harness Unlearning Multi-Shift Draft Pre-registration

## Current frame

The committed Harness Unlearning fixture establishes commitment-level causal use
for one tool-regime shift. It does not establish that the ledger distinguishes
semantic change from irrelevant version churn across shift families.

## Assumption ledger and anomaly map

- All cases reuse one deterministic memory family, not independent live traces.
- A changed required action operationalizes a semantic shift; wording alone is
  not treated as evidence of semantic change.
- The model/version control keeps the required action identical, so lifecycle
  action there would be false forgetting.
- Reusing the same fixture can expose lifecycle mechanics, but cannot estimate
  real-agent shift prevalence or recovery rates.

## Candidate reframe and discriminating predictions

The relevant object is the commitment semantics, not a surface version label.
For tool-schema and environment-policy shifts, append-only use should fail,
target-family suppression should repair commitment, and quarantine should stop
the stale influence. For model/version-identical-semantics, append-only use
should remain correct and no lifecycle transition should occur.

## Severe experiment and kill criteria

The draft runner registers three cases: `tool-schema`,
`environment-policy`, and `model/version-identical-semantics`. It reuses
`MemoryLedger` and the paired `evaluate_causal_use` gate only for cases whose
required action changes. Kill the semantic-control interpretation if a changed
case lacks the target-family/placebo contrast, fails to recover after
quarantine, or if the identical-semantics control is quarantined.

## Claim boundary and next best test

Passing produces only deterministic multi-shift scaffolding. It is not evidence
of neural unlearning, OOD generalization, live-provider behavior, or HU1–HU7.
Next, freeze independently generated shift instances and run matched,
pre-registered live evaluation with false-forgetting and recurrence gates.
