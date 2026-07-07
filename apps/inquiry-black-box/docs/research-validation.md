# Research Validation

The MVP validates usefulness through user-specific outcomes, not cognitive-state
certainty.

## Accepted Evidence

- Session replay markers point to source events.
- Labels attach to nearby time windows.
- Recall probes become verifier events.
- Notification outcomes record accepted, snoozed, dismissed, or ignored.
- Reports include limitations and provenance.

## Rejected Evidence

- Camera-only certainty claims.
- Medical, diagnostic, lie-detection, or workplace-surveillance claims.
- Raw video or raw typed content as routine model input.
- Personalized predictions before calibration beats heuristic baselines on held
  out user sessions.

## Calibration Path

Start with conservative heuristics. Modal calibration jobs can later train toy
or personalized models from redacted session features, labels, and probe
outcomes. A model result is publishable in the UI only when it has a model card,
feature importances or limitations, and held-out performance above the heuristic
baseline.
