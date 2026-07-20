# Deterministic Counterfactual Harness Search Pilot

Frozen design date: 2026-07-20

## Question

On deterministic fixtures with one known injected fault per harness surface,
can paired single-component replay recover the responsible component and choose
more valid repairs than trace diagnosis at the same evaluation budget?

## Fixed cases

The pilot contains six synthetic-identifiable cases: context, tools,
generation, orchestration, memory, and output. Each case has one responsible
component, one deliberately plausible but incorrect trace suspect, a clean
reference, a faulted manifest, and a matched placebo intervention. The context
case is anchored to the committed Constraint Transport summary-loss family.

## Conditions and budget

1. `counterfactual_search`: evaluate one isolated repair for each of the six
   components plus one matched placebo, for seven harness evaluations per case.
2. `trace_diagnosis`: perform six exact no-op replays for passive trace evidence,
   then evaluate its top trace-based repair, also seven harness evaluations per
   case.

The task, faulted manifest, outcome vector, logical schedule, and total harness
evaluation count are held fixed. The deterministic trace baseline is narrow and
is not a proxy for a strong learned diagnostic model.

## Exit gates

- all six harness surfaces have one clean-pass/faulted-fail case;
- no-op replay reproduces every faulted outcome exactly;
- the responsible repair restores joint success in every case;
- non-responsible and placebo interventions receive zero accepted credit;
- top-1 component recovery is exact on all six cases;
- counterfactual repair success exceeds trace-diagnosis repair success at the
  equal seven-evaluation budget;
- public summary and replay rows regenerate byte-for-byte.

Any failed gate prevents publication of the pilot bundle.

## Claim boundary

Passing establishes a synthetic deterministic diagnostic only. It does not
show sealed-label, stochastic, model-level, interaction, OOD, or statistically
significant attribution; it does not satisfy CHS1–CHS6.

