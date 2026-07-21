# Harness Unlearning Multi-Shift Draft Pre-registration

## Current frame

The committed Harness Unlearning fixture establishes commitment-level causal use
for one tool-regime shift. It does not establish that the ledger distinguishes
semantic change from irrelevant version churn across shift families.

## Assumption ledger and anomaly map

- The bank now holds nine independently authored shift instances (distinct
  memory ids, content actions, provenance tags, and regime ids per instance),
  not one deterministic memory family replayed under relabeled case ids; see
  `unlearning_multishift.py`. They are still deterministic, hand-authored
  fixtures, not independent live traces.
- A changed required action operationalizes a semantic shift; wording alone is
  not treated as evidence of semantic change.
- The model/version control keeps the required action identical, so lifecycle
  action there would be false forgetting.
- Nine independent instances reduce (but do not eliminate) the risk that
  passing gates reflect one fixture's quirks; they still cannot estimate
  real-agent shift prevalence or recovery rates, which requires live traces.

## Candidate reframe and discriminating predictions

The relevant object is the commitment semantics, not a surface version label.
For tool-schema and environment-policy shifts, append-only use should fail,
target-family suppression should repair commitment, and quarantine should stop
the stale influence. For model/version-identical-semantics, append-only use
should remain correct and no lifecycle transition should occur.

## Severe experiment and kill criteria

The draft runner registers nine cases across three families — `tool-schema`,
`environment-policy`, and `model/version-identical-semantics` — three
independently authored variants each. It reuses `MemoryLedger` and the paired
`evaluate_causal_use` gate only for cases whose required action changes. Kill
the semantic-control interpretation if a changed case lacks the
target-family/placebo contrast, fails to recover after quarantine, if the
identical-semantics control is quarantined, or if any two instances share a
memory id or a regime-id pair (independence gates in
`test_grounded_unlearning_multishift.py`).

An opt-in credentialed smoke, `run_unlearning_multishift_live_smoke.py`,
additionally exercises the live adapter's prompt/parse/budget mechanics for a
natural-language memory-sensitivity probe over 3 of the 9 cases. It is a
mechanics smoke, not a pre-registered pilot: it is not budget-matched against
a baseline and does not perform the mechanistic `evaluate_causal_use`
intervention.

## Claim boundary and next best test

Passing produces only deterministic multi-shift scaffolding plus (opt-in)
evidence that the live-adapter mechanics work for this probe shape. Neither
authorizes evidence of neural unlearning, OOD generalization, real
live-provider unlearning behavior, or HU1–HU7. Next, pre-register a matched
live pilot over the full 9-case bank with a no-memory and full-reset
baseline, budget-matched calls, task-clustered bootstrap CIs, and frozen
false-forgetting/recovery thresholds before any HU1–HU7 claim.
