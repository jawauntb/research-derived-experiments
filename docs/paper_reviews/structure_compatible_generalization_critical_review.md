# Critical Review: Structure-Compatible Generalization

Date: 2026-07-06

## Verdict

Strong scoped contribution. The paper advances the earlier weakness/OOD line by
putting symbolic, vision, and modular tasks under one row schema and showing
that transformation compatibility can outperform loss, ID validation, norm, and
sharpness proxies when train evidence underdetermines shortcut and rule-like
solutions.

## Main Issues

1. **Keep the claim finite and conditional.** The evidence supports structured
   domains with a candidate deployment transformation family. It does not prove
   open-world OOD certification.
2. **Do not overread `compatibility_true`.** The strongest selector still uses
   an oracle transformation family in phase one; the result motivates phase two
   rather than replacing it.
3. **Separate predictor and intervention evidence.** Phase one is mainly a
   diagnostic/model-selection result. The control result belongs to the
   inferred-transformations paper.
4. **Name the architecture change.** The simple practical move is to add a
   compatibility selection surface before deployment.
5. **Improve future figure polish from payloads.** The existing figures are
   readable, but the next generated pass should use a consistent synthesis
   palette and annotate the allowed claim directly in captions.

## Rewrite Applied

- Added an architecture-lesson section to the generated paper Markdown and PDF
  builder.
- Preserved the bounded OOD-certification caveat.
- Kept the phase-two discovery/intervention claim out of the phase-one result.
- Updated the archive script so figures remain embedded in papers rather than
  copied into the Metaphysics folder as standalone PNGs.

## Contribution Opportunity

This paper gives a simple architecture rule for agents and neural systems:

> When ID behavior cannot distinguish shortcut and rule, expose the expected
> deployment transformation as an auditable selection surface.

The next major contribution is to replace the oracle transformation family with
learned discovery while preserving this clean selection and ablation protocol.
