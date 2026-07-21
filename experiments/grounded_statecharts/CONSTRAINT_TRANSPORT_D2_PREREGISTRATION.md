# Constraint Transport D2 Bridge — Draft Pre-registration

## Current frame

The committed transport fixture jointly changes lossy prose transport and the
presence of a typed external guard. It supports a deterministic diagonal
comparison, not a factorial decomposition.

## Assumption ledger

- The two committed task families are deterministic diagnostics, not a live-agent
  population.
- The fixture's known summary-drop fault is an intervention, not evidence that
  all prose delegation fails.
- A representation effect, external-guard effect, and their interaction require
  all four matched cells.

## Registered bridge and anomaly map

The bridge republishes `lossy_prompt` as prose/no external guard and
`typed_guarded` as typed/external guard. The crossed prose/guard and
typed/no-guard cells are deliberately recorded as unobserved. No provider,
credential, raw transcript, or live model is used.

## Discriminating prediction and severe test

The next D2 run must populate all four cells with matched task families,
delegation depths, budgets, and commitment scoring. The typed-envelope account
predicts constraint survival under typed transport even without a guard; the
guard account predicts lower violations when the guard is present; an interaction
would require the guard benefit to depend on representation.

Kill the factorial interpretation if any cell lacks matched task/depth coverage,
if the crossed cells use non-equivalent guards or prompts, or if the observed
contrast is explained by a known injected summary fault alone.

## Claim boundary and next test

This bridge may claim only deterministic reuse and explicit non-identification
of factorial effects. The next best test is the matched four-cell pilot above.

## Draft OOD addendum

Two credential-free probe contracts are now frozen without execution:

1. **Held-out wording:** rephrase instructions while retaining the exact typed
   constraint identity, task scorer, two source families, and depth 1–4 matrix.
2. **Deeper delegation depth:** extend matched prose and typed chains to depth 5
   and 6 with the same lineage and capability-narrowing checks.

The current frame predicts typed constraint survival and valid lineage should
not depend on wording or the committed depth-1–4 ceiling. Kill either transport
interpretation if a wording change changes the scorer/constraint identity, or a
typed depth-5/6 chain drops lineage or a required constraint.

## Execution update (harness-v2 name-free contract)

Both probes now execute rather than staying planned-only. The held-out
wording probe runs through the harness-v2 name-free contract instead of the
deterministic prose/typed diagonal above: it reruns 4 frozen D2
`recursive_constrained_tool_use` tasks with paraphrased instructions through
`condition_policy.py`-enforced `envelope_only` vs `envelope_external_guards`
episodes. Under the deterministic fixture adapter (required, credential-free)
this is mechanics-only, because `FixtureExecutor` never reads instruction
text; `run_constraint_ood_live_smoke.py` (opt-in, `GROUNDED_HARNESS_LIVE=1`)
reruns the same probe against a live model and reports the joint_success
delta against the 0.15 kill threshold from `D3_SAMPLE_SIZE_PLAN.md`, honestly
recording a collapse rather than a pass. The deeper-delegation-depth probe
still runs the deterministic prose/typed diagonal above, extended to depths 5
and 6 via `ConstraintTransportBenchmark.run_ood_depth`; it has no live
variant. See `experiments/grounded_statecharts/constraint_ood.py` and
`results/constraint_ood/summary.json` for the executed contract and current
(fixture-only) outcome.

## Live OOD paraphrase smoke (2026-07-20)

Path: `artifacts/grounded_statecharts/constraint_ood_live_smoke/` (8/8 publishable;
`gpt-4.1-mini`; name-free harness-v2).

| Contrast | Point estimate | Bootstrap CI | Kill (<0.15) |
|---|---|---|---|
| joint_success: external − envelope_only | **+1.000** | **[1.0, 1.0]** | not triggered |

Claim boundary: one credentialed smoke on 4 held-out paraphrased tasks — not
powered D3 confirmatory. Effect survived rewording under the same harness-
enforced contract.

