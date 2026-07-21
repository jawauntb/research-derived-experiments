# Grounded Harness Deterministic Fixture Release

This package is the first executable slice of the grounded-harness portfolio.
It records a typed append-only event stream, captures a pre-commit checkpoint,
proves exact no-op replay, and changes only the completion guard in a paired
counterfactual replay.

The committed fixture intentionally reports tool success without creating its
required artifact. A G0 self-report guard falsely authorizes `commit`. The
paired replay substitutes one G3 artifact-digest guard, routes the same run to
`repair`, creates the artifact, verifies it, and then commits.

The same dependency-free package now includes the first Constraint Transport
diagnostic. It carries immutable approval and evidence constraints through one
to four delegation levels, checks hash-linked envelope lineage, rejects
constraint removal and capability widening, and reports raw task success
separately from zero-violation joint success.

The Counterfactual Harness Search pilot adds one injected fault on each of six
harness surfaces. It evaluates isolated repairs and a placebo, recovers the
responsible surface, and compares repair selection with passive trace diagnosis
at the same deterministic evaluation budget.

The functional Harness Unlearning fixture then proves that a stale tool-pattern
memory and its descendant change commitment before allowing lifecycle changes.
It quarantines and retires that family under a v3 shift, preserves the audit
record, and revalidates/reactivates it when v2 recurs.

## Run

From the repository root:

```bash
python3 -m experiments.grounded_statecharts.run_fixture
python3 -m experiments.grounded_statecharts.run_constraint_transport
python3 -m experiments.grounded_statecharts.run_counterfactual_search
python3 -m experiments.grounded_statecharts.run_harness_unlearning
python3 -m experiments.grounded_statecharts.run_unlearning_multishift_smoke
python3 -m experiments.grounded_statecharts.run_constraint_ood_smoke
python3 -m experiments.grounded_statecharts.run_unified_replay
python3 -m experiments.grounded_statecharts.run_statechart_pilot_smoke
python3 -m experiments.grounded_statecharts.run_constraint_pilot_smoke
python3 -m experiments.grounded_statecharts.run_chs_sealed_smoke
python3 -m experiments.grounded_statecharts.run_live_failure_replay --rows /path/to/rows.jsonl
python3 -m experiments.grounded_statecharts.run_chs_from_live_smoke --rows /path/to/rows.jsonl
```

The command has no third-party or provider dependency. It regenerates the
public-safe replay bundle under `results/`:

- `summary.json`: exit gates, compact metrics, manifest/checkpoint hashes, and
  the allowed claim;
- `checkpoint.json`: the serialized pre-verification checkpoint;
- `original.jsonl`, `noop_replay.jsonl`, `guarded_replay.jsonl`: typed event
  streams;
- `replay.html`: static side-by-side visual explanation of false-completion
  prevention.

The transport command writes `results/constraint_transport/`:

- `summary.json`: depth-wise survival, violation, raw utility, and joint-success
  metrics plus the exact allowed claim;
- `episodes.jsonl`: one final outcome per condition, family, and depth;
- `lineage.jsonl`: per-delegation envelope lineage and known fault locations;
- `replay.html`: compact depth-wise comparison, not a general dashboard.

The counterfactual command writes `results/counterfactual_search/` with a gate
summary, six case rows, 42 component/placebo intervention rows, and one compact
static replay.

The unlearning command writes `results/harness_unlearning/` with the paired
causal-use receipt, typed lifecycle ledger/events, phase outcomes, summary, and
static shift/recurrence replay.

The multi-shift unlearning smoke command writes
`results/unlearning_multishift/`. It registers deterministic tool-schema and
environment-policy semantic shifts plus a model/version-identical-semantics
negative control, reusing the causal-use and ledger mechanics without live
calls. The Constraint Transport OOD smoke command writes
`results/constraint_ood/` with planned held-out-wording and depth-5/6 contracts;
it executes neither probe and makes no OOD claim.

The unified replay command writes `results/unified_replay/`. It renders a
compact public failure replay from the committed false-completion summary and
paired event rows, separately labeling observed events, intervention, inferred
causal credit, uncertainty, cost/budget, and the claim boundary. It has no
provider or network path.

## Verify

```bash
python3 -m pytest -q tests/test_grounded_statecharts.py
```

## Live-evaluation contract (Tranche 1)

The package now freezes the shared live-evaluation substrate used by later D2
pilots:

- `schemas/task.schema.json`, `episode.schema.json`, `intervention.schema.json`,
  and `result.schema.json`
- `adapters/` provider-neutral boundary with a deterministic `fixture` executor
  and an opt-in `live` OpenAI/Anthropic backend (`GROUNDED_HARNESS_LIVE=1`)
- `budgets.py`, `sanitization.py`, and `evaluation.py` for matched ceilings,
  fail-closed public rows, integrity receipts, and task-clustered bootstrap

```bash
python3 -m experiments.grounded_statecharts.run_live_smoke
python3 -m pytest -q tests/test_grounded_live_evaluation.py tests/test_grounded_live_provider.py
```

The default smoke path never imports a provider SDK, reads an API key, or
writes raw transcripts into `results/`.

Credentialed mechanics smoke (writes only under gitignored `artifacts/`):

```bash
GROUNDED_HARNESS_LIVE=1 \
GROUNDED_HARNESS_PROVIDER=openai \
GROUNDED_HARNESS_MODEL=gpt-4.1-mini \
doppler run --config dev -- \
  python3 -m experiments.grounded_statecharts.run_live_credentialed_smoke
```

Smoke outcomes are discarded from held-out D2 pilots.

## Frozen D2 held-out task bank

`fixtures/d2_held_out_tasks.json` freezes 24 public task contracts: 12
artifact-completion tasks requiring fresh local verification and 12 recursive
delegation tasks requiring an approval, evidence, or capability constraint to
survive. `d2_tasks.py` validates their closed task-schema shape, constructs
`LiveTask` records, verifies frozen task digests, and rejects smoke rows. The
fixture contains no answer keys or hidden fault labels; execution guards must
use declared artifact and capability receipts.

## Statechart D2 pilot mechanics bridge

`statechart_pilot.py` routes artifact-completion smoke conditions through the
existing deterministic `ReplayEngine`, the committed false-success fixture, and
the existing G0/G3 manifests. `direct_self_report` and `statechart_g0` retain
the false completion; `statechart_g3` routes through repair before a grounded
commit; `wrong_edge_guard` is an explicit no-credit control. Constraint-family
conditions remain delegated to the fixture executor until their transport pilot
is frozen. All smoke rows use the matched `DEFAULT_PILOT_BUDGET`, are
sanitized, and are discarded from held-out D2 analysis.

The draft two-family gate is
[`STATECHART_D2_PREREGISTRATION.md`](STATECHART_D2_PREREGISTRATION.md).

## Constraint and attribution bridge smoke paths

`run_constraint_pilot_smoke` writes `results/constraint_pilot/` by reusing the
committed Constraint Transport outcomes. It maps the observed deterministic
diagonal to prose/no external guard and typed/external guard, while marking the
two crossed 2x2 cells as unobserved; it makes no factorial-effect claim.

`run_chs_sealed_smoke` writes `results/chs_sealed/` by loading a separate
synthetic label artifact for one clean reference and six single-fault surfaces,
then scoring top-1 attribution from the existing counterfactual pilot. It is
synthetic-to-sealed plumbing only: real failures with genuinely withheld labels
remain required for publishable CHS1. Both runners are credential-free and
never call a live provider.

`run_chs_repair_search` writes `results/chs_repair_search/`. It re-runs the
equal-budget counterfactual repair/placebo search (`counterfactual_search.py`,
unchanged: every repair candidate and the placebo control cost exactly one
evaluation) fresh against the six committed single-fault fixtures, then scores
it against two independently produced label sources -- the adjudicated
injected-fault seal tier (`chs_adjudication.seal_from_injected_faults`,
`results/chs_injected_faults/labels.jsonl`) and the hand-authored
`fixtures/chs_sealed_labels.json` used by `chs_sealed.py`. It gates on zero
placebo credit, exact per-arm budget parity, and agreement between both label
sources, and its `allowed_claim`/`non_claims` are explicit that this is still a
constructed, repository-visible fixture bridge, not CHS1 on naturalistic live
failures.

## Scope boundary

These are deterministic fixture results, not estimates over live agents or
confirmatory CT/CHS benchmarks. The prompt and trace baselines are controlled
diagnostics, not optimized learned competitors. Counterfactual search has not
yet been tested with sealed labels, stochastic replays, interactions, or OOD
faults. Functional unlearning is demonstrated on one deterministic regime
shift plus draft multi-shift scaffolding only; it is not neural unlearning,
erasure, OOD evidence, or an HU1–HU7 result. The
live-evaluation smoke bundle validates the shared contract only; it is not a
D2 pilot, commercial demo, or publishable population claim.


## Held-out D2 pilot runner

```bash
python3 -m experiments.grounded_statecharts.run_d2_pilot --adapter fixture
```

Live held-out runs require `GROUNDED_HARNESS_LIVE=1` and write under
`artifacts/grounded_statecharts/d2_pilot/` only.

## Live failure replay and CHS harvest

`run_live_failure_replay` selects one authentic matched failure/contrast pair
from D2 rows, preferring artifact-family G0 false completion versus G3 joint
success, and writes a metadata-only static replay to
`artifacts/grounded_statecharts/live_failure_replay/`. It never renders prompts,
transcripts, or provider payloads. `--publish-public` writes instead under
`results/live_failure_replay/`, but fails closed unless every input row already
matches the exact sanitized public-row schema.

`run_chs_from_live_smoke` consumes only those sanitized public rows and writes
an unsealed, outcome-pattern heuristic candidate ledger to
`artifacts/grounded_statecharts/chs_from_live/`. Its component mapping is a
triage aid for independent future adjudication, not an oracle, causal
attribution, or a CHS1 score.


## Public dataset and paired-contrast CHS seals

```bash
# After a live harness-v2 D2 matrix lands under artifacts/:
python3 -m experiments.grounded_statecharts.publish_public_dataset \
  --source-rows artifacts/grounded_statecharts/d2_pilot_harness_v2/rows.jsonl

python3 -m experiments.grounded_statecharts.run_chs_adjudication \
  --rows artifacts/grounded_statecharts/d2_pilot_harness_v2/rows.jsonl \
  --output-dir artifacts/grounded_statecharts/chs_sealed_live
```

Public export writes `results/d2_pilot_public/` (rows, summary, checksums,
DATASET.md) and refuses raw/label fields. CHS seals stay under `artifacts/`.

## Harness-enforced conditions (default live contract)

Live prompts are name-free by default. Condition identity is applied in
`condition_policy.py` after the provider returns an action:

- `statechart_g3`: repair missing artifacts before scoring
- `envelope_external_guards` / constrained `statechart_g3`: strip forbidden
  capabilities and force a constrained delegate action
- self-report / `envelope_only`: leave model claims unchanged

Labeled prompts (`GROUNDED_HARNESS_LABELED_PROMPT=1`) are diagnostic-only and
must not be used for escalation gates.

## Weak-prompt ablation and live harvest

```bash
GROUNDED_HARNESS_LIVE=1 GROUNDED_HARNESS_WEAK_PROMPT=1 \
GROUNDED_HARNESS_PROVIDER=openai GROUNDED_HARNESS_MODEL=gpt-4.1-mini \
doppler run --config dev -- \
  python3 -m experiments.grounded_statecharts.run_weak_prompt_ablation \
  --output-dir artifacts/grounded_statecharts/weak_prompt_ablation_harness_v2

python3 -m experiments.grounded_statecharts.run_live_failure_replay
python3 -m experiments.grounded_statecharts.run_chs_from_live_smoke
```

Live harvest/replay tools default to `artifacts/` and never require a provider
call when sanitized rows already exist.
