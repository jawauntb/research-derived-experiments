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

## Equal-budget repair search scored against sealed labels

`chs_repair_search.py`'s `score_equal_budget_repair_search`
(`run_chs_repair_search.py`) adds an explicit scoring pass over the same six
committed single-fault fixtures. It re-runs the unmodified equal-budget
search (`CounterfactualHarnessPilot.run` — every repair candidate and the
placebo control cost exactly one evaluation, so no arm gets a budget
advantage) fresh, never reusing the `evidence` already stored in a sealed
label row, and checks the fresh result against two independently produced
label sources: the adjudicated injected-fault seal tier
(`results/chs_injected_faults/labels.jsonl`) and the hand-authored
`fixtures/chs_sealed_labels.json` fixture that `chs_sealed.py` already scores
against.

It gates on: exact per-arm cost parity (`equal_budget_repair_vs_placebo`) on
every case; zero placebo credit across all six cases; the fresh search
matching both label sources on every surface; and both label sources
agreeing with each other. `results/chs_repair_search/` is written only when
every gate passes, so a mismatched attribution, a credited placebo, or an
unequal per-arm budget fails the run rather than silently publishing a
passing summary.

Kill criteria specific to this tier: do not treat agreement between the
injected-fault seal tier and the fixture label file as independent
triangulation across data sources — both trace back to the same committed
fixture bank; do not claim CHS1 from this tier; do not report
`equal_budget_repair_vs_placebo: true` if any repair or placebo arm's cost
ever diverges.

## Withheld-at-score-time seal (structurally blind search)

The tier above still hands `CounterfactualHarnessPilot.run` the full
`FaultCase`, including `responsible_component`; the search's *decision*
logic never branches on that field, but the deterministic evaluator inside
the search still reads it to simulate physics. `chs_repair_search.py` adds a
strictly stronger tier that removes that field from the search entirely:

- `seal_withheld_labels` reads `case.responsible_component` exactly once,
  at seal-authoring time, and writes it to a separate file
  (`results/chs_withheld_seals/labels.jsonl`, `generate_withheld_seals`,
  `run_chs_withheld_seal_search.py`). Public-safe: every label traces back
  to the same committed synthetic fixture bank as every other tier here.
- `BlindFaultCase` (`counterfactual_search.py`) is built from a `FaultCase`
  via `BlindFaultCase.from_fault_case`, but has **no**
  `responsible_component` attribute at all — the label is used only to
  place the fault in a `HarnessConfig` and is then discarded.
- `BlindCounterfactualHarnessPilot.run` performs the identical equal-budget
  repair/placebo search (every repair candidate and the placebo control
  still cost exactly one evaluation) using `_evaluate_faulted_config`,
  which reads only `HarnessConfig` state — never a label — to determine
  which component is broken. Its output, `BlindSearchResult`, likewise has
  no `responsible_component` or `attribution_correct` field.
- `score_withheld_repair_search` (`generate_withheld_results`,
  `--sealed-labels` on `run_chs_withheld_seal_search.py`) loads
  `WithheldSealedLabel` rows from the separate store and joins them to
  `BlindSearchResult.recovered_component` by `fault_id` only, after the
  blind search has already returned. Both `BlindFaultCase.__dataclass_fields__`
  and `BlindSearchResult.__dataclass_fields__` are asserted to omit
  `responsible_component` as an explicit gate, so a future edit that
  reintroduces the label on either type fails the run instead of silently
  weakening the claim.

Kill criteria specific to this tier: do not reuse `CounterfactualHarnessPilot`
or `FaultCase` directly inside the withheld-tier search path — only
`BlindCounterfactualHarnessPilot` / `BlindFaultCase` may run there; do not
add a `responsible_component` attribute to `BlindFaultCase` or
`BlindSearchResult`; do not claim CHS1 from this tier — it remains
synthetic, repository-visible fixture construction, and "withheld" here
names a structural property of the types, not labels withheld from a
diagnosis author on real failures.

## Live withheld-at-score-time bridge (harvest vs. paired-contrast seal)

`chs_from_live.harvest_candidates` and `chs_adjudication.seal_from_paired_contrasts`
were already independently blind to each other by construction: the harvest
reads only sanitized public rows, which never carry a `responsible_component`
field, and the sealer never reads `predicted_component`. `chs_live_withheld_score.py`
adds the missing third step — joining the two by `source_result_digest`
only, after both have already run, using a sealed-label file it writes and
then re-reads from disk (`run_chs_live_withheld_score_smoke.py`, output
under `artifacts/grounded_statecharts/chs_live_withheld_score/`, never under
`results/`, since it is derived from real D2 episodes).

Applied to `artifacts/grounded_statecharts/d2_pilot_harness_v2/rows.jsonl`
(144 real live rows, harness-v2), this seals 12 orchestration labels and the
heuristic harvest covers all 12 with 100% top-1 agreement — but this is a
narrow, honest result, not CHS1: the paired-contrast seal covers only
orchestration/output on matched real episodes, so joint coverage is 12 of
144 rows; and the heuristic harvest is a symptom-pattern classifier, not an
equal-budget repair/placebo search — it has no placebo arm and no
evaluation-budget notion, so "agreement" here means
predicted-component-matches-seal, not a placebo arm receiving spurious
`joint_success` credit.

Kill criteria specific to this tier: do not treat harvest/seal agreement as
CHS1 or as author-blind human adjudication; do not report
`six_surface_chs1_claim: true`; do not claim this join is an equal-budget
repair/placebo search; do not write `responsible_component` into a public
live episode row.

## Claim boundary and next test

Synthetic-to-sealed plumbing, paired-contrast live seals, the injected-fault
seal tier, the equal-budget repair-search scorer, the withheld-at-score-time
structurally-blind search, and the live harvest-vs-seal bridge together are
still a narrow bridge, not CHS1. Live paired-contrast seals cover only
orchestration and output on real D2 episodes. The injected-fault tier, the
equal-budget scorer, and the withheld-at-score-time tier now cover all six
surfaces, but on constructed, repository-visible fixtures rather than
withheld real-failure labels — the withheld tier's structural guarantee
(the search's case/result types have no `responsible_component` attribute)
strengthens *how* the search is blind, not *what* the labels are. The live
bridge shows the harvest-vs-seal join mechanics work on 144 real rows, but
only for the 12-of-144 rows the orchestration/output-only seal covers, and
with a symptom-pattern classifier standing in for the equal-budget search.
Publishable six-surface CHS1 still requires labels withheld from the
diagnosis author across all six surfaces **on real failures**, matched
repair/placebo search over those real failures at equal budget, and
pre-specified abstention handling — none of which any tier here provides on
its own. This is CHS1-bridge / withheld-at-score-time work, not author-blind
human adjudication CHS1. The next best test is extending live-episode
surface coverage itself (context, tools, generation, memory conditions in
the live D2/D3 harness) so that the withheld-label seal, not only the
constructed-fixture seal, can eventually reach all six surfaces and be
scored by this same equal-budget repair/placebo search — run, as the
withheld tier now demonstrates is possible, over a case/result
representation with no label attribute for the search to read.
