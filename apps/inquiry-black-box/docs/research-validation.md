# Research Validation

The MVP validates usefulness through user-specific outcomes, not cognitive-state
certainty. Inquiry Black Box should claim "learning-state instrumentation" only
when a signal changes a local action and that action can be checked by labels,
recall probes, or later usefulness ratings.

## Product Claim Boundary

Accepted claims:

- Replay markers point to source events.
- Heatmap segments show separate stimulus and behavior evidence.
- Repair prompts are hypotheses, not diagnoses.
- Labels, recall probes, and repair outcomes become verifier events.
- Reports include confidence, limitations, and provenance.

Rejected claims:

- Camera-only certainty.
- EEG, gaze, or browser behavior as mind reading.
- Medical, diagnostic, lie-detection, or workplace-surveillance claims.
- Raw video or raw typed content as routine model input.
- Personalized predictions before calibration beats heuristic and stimulus-only
  baselines on held-out user sessions.

## Validation Matrix

| Gate | Question | Minimum Evidence | Negative Controls | Exit Signal |
| --- | --- | --- | --- | --- |
| G0. Reliability ceiling | Are labels/probes stable enough to learn from? | Split-half agreement for self-labels, probe answers, repair usefulness, and session-level outcomes. | Randomly paired labels, shuffled probe answers, duplicate-session disagreement audit. | If reliability is low, improve prompts and labels before modeling. |
| G1. Stimulus-only baseline | How much can text/video structure explain without user traces? | Local features from stimulus density, term novelty, transitions, duration, and quiz checkpoint candidates. | Future-session target, within-document shuffled segment order, fake shifted segment boundaries. | Product model must beat this before claiming user-specific signal. |
| G2. Browser-behavior residual | Do scroll, dwell, revisit, copy, media seek, tab churn, labels, and probes add signal after stimulus? | Held-out session/user evaluation against G1, with confidence intervals and calibration plots. | Time-permuted browser events, cross-user session swap, future-participant score. | Keep only features that add stable residual value and map to repair actions. |
| G3. Camera/eyetrack residual | Do camera-derived quality/gaze proxies add signal after stimulus and browser behavior? | Residual lift on held-out sessions, stratified by camera quality flags. | Face-missing/low-light segments, shifted camera windows, camera-only ablation. | Use only as a weak auxiliary signal; never as standalone truth. |
| G4. Repair utility | Do suggested repairs improve recall or user-rated usefulness? | A/B or within-user comparison of repair prompt versus no prompt or generic prompt. | Random repair assignment, stale prompt, mismatched segment prompt. | Keep repair templates that improve outcomes without increasing annoyance. |
| G5. EEG-over-browser later | Does EEG add value beyond stimulus, browser, and camera/eyetrack traces? | Separate research PR in `coherence-testbench`; leave-subject/session-out residual tests. | Cross-subject shuffle, within-video permutation, fake shifted EEG windows, stimulus-only and browser-only baselines. | Only revisit product EEG if residual gates clear and privacy/UX costs are justified. |

## Measurement Plan

### G0. Reliability Ceiling

Before training anything personalized, estimate whether the target is learnable.
Use repeated labels, nearby recall probes, repair usefulness ratings, and
session-level outcomes. Report agreement and disagreement examples. If the user
cannot answer prompts consistently, the next product task is prompt design, not a
larger model.

Artifacts:

- Label/probe reliability table.
- Disagreement examples with event IDs.
- Decision: revise label language, revise probe language, or proceed.

### G1. Stimulus-Only Baseline

The current heatmap already computes deterministic stimulus features. Treat
these as the first baseline: density, term novelty, transition count, duration,
and quiz checkpoint candidates. A model that only sees stimulus should be able
to predict some difficult sections; the product should not attribute that signal
to the user's state.

Artifacts:

- Stimulus feature table by segment.
- Segment-level baseline performance for recall/probe difficulty.
- Negative-control results for shuffled segment order and shifted boundaries.

### G2. Browser-Behavior Residual

Add browser-derived behavior only after the stimulus-only baseline is measured.
Candidate features include scroll velocity, dwell, revisit loops, media rewind,
copy/highlight, tab churn, labels, probe timing, and repair outcomes. Evaluate
held-out sessions or held-out users, not within-session fit.

Artifacts:

- Stimulus-only versus stimulus-plus-browser comparison.
- Feature ablation table.
- Calibration plot and confidence intervals.
- Examples where behavior changes the suggested repair.

### G3. Camera/Eyetrack Residual

Camera-derived features are optional weak signals. They should be evaluated only
after browser behavior has a residual benchmark. Stratify every result by
quality flags such as face missing or low light. A camera-only model should not
be a product headline.

Artifacts:

- Quality-stratified lift table.
- Shifted-window negative control.
- Camera-only ablation that demonstrates why standalone claims are rejected.

### G4. Repair Utility

The product earns its keep if repair prompts improve recall or save review time.
Compare heatmap-specific repair prompts against no prompt, generic prompt, and
randomly mismatched prompt. Store accepted, answered, dismissed, snoozed, and
usefulness-rated outcomes as events.

Artifacts:

- Prompt template outcome table.
- Annoyance/dismissal rate.
- Recall or usefulness delta.
- Keep/drop decision for each repair template.

### G5. EEG-Over-Browser Later

The separate `coherence-testbench` status currently warns against broad EEG
claims: cross-subject EEG attention decoding is killed, and eyetrack/quiz paths
remain inconclusive on the full corpus. Inquiry should therefore treat EEG as a
later residual research question, not a prototype dependency.

Any EEG work should live in a dedicated research PR and answer: after controlling
for stimulus, browser behavior, and camera/eyetrack features, does EEG add stable
held-out value? If not, it stays out of the product path.

Artifacts:

- Pre-registered residual table.
- Negative-control report.
- GO/KILL decision with product implication.

## Research PR Rules

- Do not broaden `coherence-testbench` from prototype branches.
- Pre-register the target, split, baseline, negative controls, and GO/KILL rule
  before running a new benchmark.
- Keep stimulus-only and behavior-only baselines beside every multimodal result.
- Report uncertainty, calibration, and examples where the model changes an
  action.
- Prefer small reproducible notebooks or scripts over hidden exploratory runs.
- Keep product language probabilistic, local-first, non-medical, and
  non-surveillance.

## Immediate Next Research Tasks

1. Add a fixture-derived validation table for the current local demo events.
2. Define the first label/probe reliability export from local SQLite JSONL.
3. Create a stimulus-only baseline notebook or script that consumes heatmap
   segment features.
4. Define browser residual features from replay markers and repair outcomes.
5. Leave EEG and foundation-model rescue work frozen until G1-G4 produce a
   stable residual target.
