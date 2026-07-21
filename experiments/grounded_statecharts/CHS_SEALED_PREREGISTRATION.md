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

## Model-mediated harvest

Sanitized live D2 rows may be harvested into an artifact-only candidate ledger
before adjudication. The declared mapping is a heuristic: artifact false
completion under G0/direct self-report and constraint joint failure without
external guards map to orchestration; wrong-edge transitions map to output;
budget exhaustion maps to tools; and otherwise unexplained refusal maps to
generation. These are surface hypotheses, not oracle labels or causal
attributions. The harvest must abstain on unmatched patterns, preserve the
source result digest, and remain unsealed until an independent scorer commits
labels. Kill any stronger claim if the mapping changes after label access, if
raw provider material enters the ledger, or if heuristic agreement is reported
as a CHS score without independently sealed labels.

## Paired-contrast live seal (narrow bridge)

Independently of the heuristic harvest, public-row matched condition contrasts
may seal a subset of failures under `artifacts/.../chs_sealed_live/`:

- envelope_only joint failure recovered by envelope_external_guards →
  `orchestration`
- statechart_g0 false completion recovered by statechart_g3 → `orchestration`
- wrong_edge_guard invalid transition → `output`

The protocol (`chs_adjudication.py`, version `paired-contrast-seal-1`) never
reads harvest `predicted_component`, never writes labels into episode rows, and
explicitly refuses a six-surface CHS1 claim from orchestration/output-only
coverage.

## Claim boundary and next test

Synthetic-to-sealed plumbing and paired-contrast live seals support a narrow
bridge only. Publishable six-surface CHS1 still requires withheld labels across
all surfaces, matched repair/placebo search, and pre-specified abstention
handling.
