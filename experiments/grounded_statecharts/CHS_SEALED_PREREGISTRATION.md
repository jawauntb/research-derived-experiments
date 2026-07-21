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

## Injected-fault seal (six-surface constructed bridge)

Independently of both the live paired-contrast rules above and the heuristic
harvest (`chs_from_live.py`), `chs_adjudication.py`'s
`seal_from_injected_faults` seals one label per surface directly from the
committed single-fault fixtures in `fixtures/counterfactual_faults.json`
(context, tools, generation, orchestration, memory, output — the same bank
`counterfactual_search.py` and `chs_sealed.py` already use).

The rule is: run the isolated counterfactual search
(`CounterfactualHarnessPilot.run`, unchanged from `counterfactual_search.py`)
against the injected fixture; seal `responsible_component` — the fixture's
declared ground truth, fixed at construction time — only when the search
recovers exactly one credited repair, that repair restores joint success, and
it matches the declared component. Ambiguous, unrepaired, or
placebo-credited cases abstain rather than seal a guessed label. Output is a
public-safe synthetic summary/label ledger written under
`results/chs_injected_faults/` (`run_chs_injected_faults_smoke.py`), never
under `artifacts/`, since no live episode or provider call is involved.

This closes the "orchestration/output-only" gap in surface coverage of the
*sealing protocol*: `seal_from_paired_contrasts` (live D2 rows) plus
`seal_from_injected_faults` (injected fixtures) together seal at least one
label for every one of the six surfaces. It does **not** close the CHS1 gap
itself. The injected-fault labels remain repository-visible constructions
authored alongside the code that scores them — the same limitation already
flagged for `chs_sealed.py` — not labels withheld from the diagnosis author
on real failures. `chs_adjudication.summarize_combined_coverage` reports both
tiers separately and always sets `six_surface_live_withheld_chs1: False`.

Kill criteria specific to this tier: do not seal a label when the search
finds zero or more than one credited repair, or when the placebo receives
credit; do not treat heuristic-harvest agreement as this tier's seal; do not
report `six_surface_any_tier_protocol_coverage: True` as if it were a
six-surface CHS1 result.

## Claim boundary and next test

Synthetic-to-sealed plumbing, paired-contrast live seals, and the injected-fault
seal tier together are still a narrow bridge, not CHS1. Live paired-contrast
seals cover only orchestration and output on real D2 episodes. The
injected-fault tier now covers all six surfaces, but on constructed,
repository-visible fixtures rather than withheld real-failure labels.
Publishable six-surface CHS1 still requires labels withheld from the
diagnosis author across all six surfaces **on real failures**, matched
repair/placebo search over those real failures, and pre-specified abstention
handling — none of which the injected-fault tier provides on its own. The
next best test is extending live-episode surface coverage itself (context,
tools, generation, memory conditions in the live D2/D3 harness) so that the
withheld-label seal, not only the constructed-fixture seal, can eventually
reach all six surfaces.
