# Concern-Gated Retrieval Wave 1a — COGR-E2a Concern-Recovery Screen

**Package:** `experiments/concern_gated_retrieval_e2/wave1a/`
**Wave:** 1a (COGR-E2a concern-recovery screen)
**Predecessor (frozen, imported, never edited):**
`experiments/concern_gated_retrieval_e2/wave0/`
**Successor (not yet created):** `experiments/concern_gated_retrieval_e2/wave1b/`
(COGR-E2b learned-geometry confirmation and L1 gate)
**Human director:** Jawaun Brown
**Status:** preregistered; unsigned until the analysis-code freeze hash is
written into [`PREREGISTRATION.md`](PREREGISTRATION.md) §8 and mirrored into
[`PROVENANCE.md`](PROVENANCE.md).

## Scientific claim boundary

Wave 1a is a **screen for the concern-update rule** on fixed, withheld
geometry. The wave answers exactly one question:

> Under the Wave 0 adversarially wrong prior, does randomized-probe
> exploration plus the frozen off-policy concern-update rule recover
> useful priorities on the three procedural families?

Wave 1a **can reject** the update rule. Wave 1a **cannot** establish:

- learned memory geometry (Wave 1b / COGR-E2b);
- the L1 dual-source-retrieval mechanism claim (Wave 1b);
- the L2 history-derived-concern-recovery claim (also Wave 1b, gated on
  the E2b crossed design); or
- any semantic-meaning or selfhood interpretation.

A successful Wave 1a is a green light to run Wave 1b's crossed geometry
× concern design. A failed Wave 1a is a KILL of the update rule as
written; per the honor-the-preregistration rule, only the knobs this
preregistration explicitly names as replayable may be rerun.

## Reuse boundary

Every numerical primitive, sealed-environment interface, template-split
guard, and off-policy estimator is imported from Wave 0. Wave 1a
introduces:

1. the five-condition sweep runner (frozen-wrong / online-learned /
   oracle / shuffled / wrong-agent);
2. the coverage audit that rejects any confirmatory row whose
   propensity-weighted coverage of the true commitment region falls
   below the preregistered floor;
3. the pre-analysis specificity check against Wave 0's info-matched
   generic value / priority / recency baselines; and
4. the Modal L4 fan-out at `research-derived-cogr-wave1a-e2a` (up to 32
   containers, Doppler scope `/Users/jawaun/superoptimizers`).

Wave 0 objects Wave 1a imports and does not fork:

| Object | Source |
|---|---|
| `build_withheld_graph` | `wave0.graph_learn` |
| `LoggedProbePolicy` | `wave0.concern_update` |
| `update_concern` (IPS + DR + poisoning guard) | `wave0.concern_update` |
| `SealedEnvironment`, `EpisodeContext`, `SealedOutcome`, `IntegrityAudit` | `wave0.sealed_env` |
| `TemplateRegistry`, `assert_calibration_only` | `wave0.template_split` |
| Wave 0 baseline slate (info-matched value / priority / recency) | `wave0.baselines` |

## Layout

```
wave1a/
├── README.md                   # this file
├── PREREGISTRATION.md          # frozen design; unsigned until analysis-code hash lands
├── PROMOTION_CONTRACT.md       # non-compensatory promotion contract
├── PROVENANCE.md               # skeleton; Modal run receipts fill it in
└── __init__.py                 # scope-boundary docstring
```

Implementation modules (`conditions.py`, `coverage_audit.py`,
`modal_l4_sweep.py`, `results/`) are added by follow-up Wave 1a build
tasks and are governed by this preregistration.

## Anti-leakage contract inheritance

Wave 1a inherits the Wave 0 anti-leakage contract in
[`../wave0/PREREGISTRATION.md`](../wave0/PREREGISTRATION.md) §4:

- The eleven evaluator-only fields enumerated there remain unreachable
  from any Wave 1a policy-visible code path. The `IntegrityAudit` AST
  walker gates every callable that enters the confirmatory sweep.
- Retrieval, ranking, and concern-update code cannot read `role`,
  `utility`, `_answer_key`, `oracle_concern`, `wrong_agent_id`,
  `paraphrase_family`, `generator_seed_kind`, `epiplexity_future_target`,
  or `sealed_outcome_receipt`.
- The **oracle** and **wrong-agent** conditions are the sole permitted
  consumers of `oracle_concern` and `wrong_agent_id` respectively; they
  are executed by the evaluator, not by policy code, and their outputs
  enter the sweep as pre-computed condition tags.

Wave 1a runs with `COGR_WAVE0_CONFIRMATORY_RUN=1` set at Modal spawn
time; this is the first stage in the program licensed to read the
confirmatory template pool (`200000..201999`). Calibration seeds
(`100000..100999`) remain unreachable — the split guard raises
`LeakageError` on any attempt.

## Ownership and change control

This subtree is authoritative for the concern-update rule screen. Any
change to `PREREGISTRATION.md`, `PROMOTION_CONTRACT.md`, or the
analysis-code hash mirror in `PROVENANCE.md` must accompany a redesign
justification recorded in the change log. No post-hoc corpus swap,
threshold swap, seed-range swap, family swap, or condition swap is
permitted after the analysis-code hash is written. See the honor-the-
preregistration rule in the human director's memory (feedback-honor-pre-
registration).
