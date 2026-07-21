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
name-free natural-language memory-sensitivity probe over 3 of the 9 cases
(one tool-schema case, one environment-policy case, and the
model/version-identical-semantics negative control), under
observed/target-suppressed/placebo-suppressed prompt conditions. It is a
mechanics smoke, not a pre-registered pilot: it is not budget-matched against
a baseline and does not perform the mechanistic `evaluate_causal_use`
intervention — suppression there is a prompt edit, not an intervention on a
retrieval mechanism.

The smoke additionally derives a prompt-level, causal-use-shaped signal
(`_live_quarantine_signal`: target-specific recovery with the placebo
unaffected) from the three conditions and applies two explicit kill
criteria before any result is read as encouraging:

1. **Identical-semantics kill:** the model/version-identical-semantics case
   must never show the quarantine-worthy pattern. If it does, that is
   recorded as a false-forgetting risk signature, not a useful signal.
2. **Specificity-before-quarantine kill:** the pattern is only ever raised
   when suppressing the target memory helps *and* suppressing the placebo
   memory does not; a generic "any suppression helps" effect never counts
   as quarantine-worthy by itself.

Cases with a provider failure on any of the three conditions are excluded
from both criteria as `insufficient_data`, not silently scored as a pass.

## Claim boundary and next best test

Passing produces only deterministic multi-shift scaffolding plus (opt-in)
evidence that the live-adapter mechanics work for this probe shape and that
neither live-smoke kill criterion fired on one credentialed run. Neither
authorizes evidence of neural unlearning, OOD generalization, real
live-provider unlearning behavior, or HU1–HU7 — do not claim HU1–HU7 from
this design at any tier. A clean kill-criteria pass on 3 cases x 1 repeat
means the mechanics and the derived signal did not misfire on this run; it
does not authorize promoting the probe shape into a pilot. Next, pre-register
a matched live pilot over the full 9-case bank with a no-memory and
full-reset baseline, budget-matched calls, task-clustered bootstrap CIs, and
frozen false-forgetting/recovery thresholds before any HU1–HU7 claim.

## Live smoke observation (2026-07-20)

Path: `artifacts/grounded_statecharts/unlearning_multishift_live_smoke/` (9/9
publishable; `gpt-4.1-mini`).

- `kill_triggered`: false (no identical-semantics false-forgetting; no
  placebo-only quarantine pattern).
- Per-case `target_effect` was 0 for all three cases in this run: the prompt-
  level causal-use-shaped signal did **not** appear. This is a clean
  mechanics/kill-criteria smoke, not evidence of useful live unlearning.

Do not escalate HU from this observation.

