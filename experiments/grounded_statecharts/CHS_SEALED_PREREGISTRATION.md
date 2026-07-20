# CHS Sealed-label Bridge — Draft Pre-registration

## Current frame

Counterfactual repair can identify a responsible harness surface on committed
synthetic single-fault fixtures. It is not yet a test against labels withheld
from the diagnosis author on real failures.

## Assumption ledger

- The six fault fixtures each contain one injected responsible surface.
- The clean reference has no responsible surface and must receive no attribution.
- The separate label artifact is an interface test only: its synthetic labels
  remain visible to the fixture author.

## Bridge, prediction, and severe test

The bridge loads a clean case and one case for each of context, tools,
generation, orchestration, memory, and output, then scores top-1 attribution
against the separate label artifact. It predicts exact agreement on the
committed deterministic cases and no attribution for the clean reference.

For CHS1, labels must be committed or held by an independent scorer before
diagnosis on real failure episodes. Kill the CHS1 claim if attribution is
performed after label access, if faults are not independently verified, if
multi-fault cases are silently treated as single-fault, or if clean cases receive
spurious component credit.

## Claim boundary and next test

This result supports synthetic-to-sealed plumbing only. Publishable CHS1 still
requires real failures with genuinely withheld labels, matched interventions,
and pre-specified failure and abstention handling.
