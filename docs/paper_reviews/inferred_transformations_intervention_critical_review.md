# Critical Review: Inferred Transformations for Structure-Compatible Generalization

Date: 2026-07-06

## Verdict

Important regime transition. The paper weakens the oracle in the
structure-compatible result by inferring supported modular shifts from training
evidence and then using that discovered family as a compatibility regularizer.
The high-ID OOD lift from 0.178 to 0.573 is the first control-style result in
this line, not just another correlation table.

## Main Issues

1. **Lead with intervention, not selector trivia.** The one-domain selector
   table is a sanity check; the intervention table is the evidence-bearing
   result.
2. **Bound discovery carefully.** The discovered family is enumerated and
   overlap-supported in a finite modular domain. It is not yet a learned
   transformation generator.
3. **Show the virtual-governor connection as an operational analogy.** The
   useful bridge is global deployment stress converted into local training
   pressure. Do not cite the preprint as empirical support for the run.
4. **Require transfer next.** The result becomes a major contribution if the
   same protocol works for vision rotations, template substitutions, or
   long-horizon action surfaces.
5. **Guard against regularizer confounds.** Future sweeps should include
   wrong-family regularization and matched-strength smoothness controls.

## Rewrite Applied

- Added an architecture-lesson section to the generated paper Markdown and PDF
  builder.
- Made the virtual-governor framing explicitly operational and bounded.
- Kept the next operation focused on learned generators and transfer, not broad
  deployment claims.

## Contribution Opportunity

This paper suggests the next simple architecture change:

> Infer the transformations the data actually supports, reject vacuous shifts,
> and make those transformations a local training pressure before OOD labels are
> ever used.

That is a plausible bridge between structure-compatible OOD work and the
virtual-governor idea: a global constraint becomes an inspectable local
incentive.
