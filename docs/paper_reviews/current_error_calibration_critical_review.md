# Critical Review: Current-Error Calibration

Date: 2026-07-06

## Verdict

Strong positive, publication-worthy after sharpening. This paper contains one of
the program's simplest architecture changes with a dramatic outcome: preserve raw
recent evidence and recompute residuals against the present model before using
them as a probe target.

## Main Issues

1. **Name the law.** The paper should foreground current-memory revaluation as a
   reusable agent architecture rule, not only as a V_probe implementation trick.
2. **Separate lag from staleness.** The strongest intellectual move is the
   hypothesis split: faster EMA made things worse, while current replay solved
   the calibration problem.
3. **Make the memory lesson explicit.** A scalar residual token is too lossy.
   Long-horizon agents need replayable evidence that can be reinterpreted after
   their model changes.
4. **Keep the consciousness language bounded.** The result is about autonomous
   boundary maintenance and action attribution, not consciousness itself.
5. **Treat the audit-floor result carefully.** No-audit passing is a strength in
   this stationary setting, not a proof that audit floors are unnecessary in
   changing worlds.

## Rewrite Applied

- Added an abstract-level architecture-law paragraph.
- Added Section 5.6, "Architecture law: current-memory revaluation."
- Reframed the main contribution as a memory/planning/action rule: raw evidence
  should be re-scored by the current model before it controls intervention.

## Contribution Opportunity

The major contribution is a compact agent-design principle:

> Useful memory is not just retained experience; it is experience re-entered
> through the current model before it controls action.

That principle links machine agency, planning, self/world attribution, and
long-horizon repair loops without overclaiming about consciousness.
