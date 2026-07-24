# Concern-Gated Retrieval Wave 1b (COGR-E2b) — Paper Directory

**Program:** Concern-Gated Retrieval (COGR) — Wave 1b (COGR-E2b)
**Deliverable:** technical report (`paper.md`) accompanying the Wave 1b
preregistration, the two non-compensatory promotion contracts (L1 and L2),
and the crossed-factorial confirmatory receipt at
`experiments/concern_gated_retrieval_e2/wave1b/`.
**Wave-boundary reminder:** Wave 1b is a **crossed learned-geometry ×
concern confirmatory** step that issues **two** verdicts **separately**:
**L1 (representation contribution)** and **L2 (concern recovery +
specificity)**. Wave 1b **can KILL** either claim independently. Wave 1b
**cannot** establish substrate transfer (L3), external-agent applicability
(L4), a cognitive/self-model interpretation (L5), or semantic meaning.
Those remain Wave 2+ objects. Any restatement of this paper as an L3,
L4, L5, substrate-transfer, or selfhood claim is inconsistent with the
two promotion contracts at
[`../../experiments/concern_gated_retrieval_e2/wave1b/PROMOTION_CONTRACT_L1.md`](../../experiments/concern_gated_retrieval_e2/wave1b/PROMOTION_CONTRACT_L1.md)
and
[`../../experiments/concern_gated_retrieval_e2/wave1b/PROMOTION_CONTRACT_L2.md`](../../experiments/concern_gated_retrieval_e2/wave1b/PROMOTION_CONTRACT_L2.md).

## Summary

This directory contains the Wave 1b (COGR-E2b) technical report for the
Concern-Gated Retrieval E2 program. The paper (`paper.md`) motivates and
documents a **3 × 3 × 3 crossed-factorial confirmatory experiment** whose
purpose is to adjudicate the L1 dual-source-retrieval mechanism claim and
the L2 history-derived concern-recovery mechanism claim, **separately**,
under learned memory geometry, on redesigned procedural families that
close the two failure modes Wave 1a's KILL surfaced (coverage collapse
on `delayed_commitments`; `info_matched_recency` reproducing the oracle
ceiling byte-for-byte on all three families).

The design crosses `Geometry ∈ {LEARNED, FREQ_MATCHED_RANDOM,
ORACLE_WITHHELD}` × `Concern ∈ {FROZEN_WRONG, ONLINE_LEARNED_IPS,
ONLINE_LEARNED_DR, ORACLE}` × `Family ∈ {delayed_commitments_v2,
maintenance_fault_v2, resource_constrained_v2}` for **36 cells × 300
paired seeds per cell** on the Wave 0 confirmatory seed range
`200000..201999`. L1 rows use the FROZEN_WRONG concern axis crossed with
non-ceiling geometry (LEARNED, FREQ_MATCHED_RANDOM). L2 rows use the
LEARNED geometry crossed with the ONLINE_LEARNED_{IPS,DR} concern axis,
blocked-by the §4.4 pre-run recency-decoupling assertion AND L1 PASS on
the corresponding family. Utility is task-based (`Δ_task`); epiplexity
`S^φ` is a dependent variable and optional bonus (`β = 0` in the L1 and
L2 gates), never the verifier.

Ten non-compensatory fatal gates (G0-G9) govern promotion. Decisive
metrics are SET-level: `oracle_recall_at_k` against the exhaustive
oracle top-k over singletons, pairs, and feasibility-gated triples;
`simple_regret_set = max_S Δ_task(S) − Δ_task(selected_set)`;
`cumulative_regret`; and `interaction_recovery` (fraction of episodes
where the policy retrieves both members of a planted complementary pair
AND avoids all three members of a planted dangerous conjunction). Hit@1
is diagnostic only. A statistical leakage audit (label-permutation +
randomized-generator controls) replaces Wave 1a's AST-only integrity
guard. Epiplexity is the exact Zhang-Levin log-det form; no Rademacher,
Nyström, MMD, or LZ "approximations" are claimed as epiplexity
estimators.

The paper explicitly documents Wave 1b's honest limitations — no
substrate transfer, no live agent, no premise audit, one rule
composition, one family axis, synthetic bundle types, epiplexity is not
the verifier, Modal budget ceiling of `$30` — and points forward to a
Wave 2 live-agent beachhead as a continuation gate (only if L1 PASSes),
Wave 3 substrate transfer, and a final Wave 4 round of safety, scaling,
and independent replication.

## Result posture

At the time of this report, the confirmatory Modal L4 run has not yet
executed; the verdict receipt at
`experiments/concern_gated_retrieval_e2/wave1b/results/verdict.json`
(gitignored under `artifacts/concern_gated_retrieval_e2/wave1b/`) is
still a placeholder. Every numerical row in §5 of the paper that
depends on the confirmatory receipt is marked **PLACEHOLDER**. The paper
is intentionally built so that the writing of the receipt — not the
writing of the report — becomes the load-bearing step. Once the receipt
lands, the placeholder rows in §5 are populated directly from
`verdict.json` and the L1 and L2 aggregate `PASS`/`KILL`/`WITHHELD`
verdicts propagate into §6 (interpretation) verbatim; §6 is
pre-written for all four combinations of L1 × L2 verdicts so no
restatement of the paper needs to invent language after the receipt
lands.

Per the honor-the-preregistration rule
(`feedback-honor-pre-registration` in the human director's memory),
only the two knobs the preregistration §11 explicitly names as
replayable — `LoggedProbePolicy.epsilon` within `[0.05, 0.10]`,
`update_concern.eta` within `[0.05, 0.20]` — may be rerun after a
fatal gate rejection, and only on the reserved replay range
`200900..201999` capped at 30% of an affected cell. Every other knob
(family definitions, condition definitions, Wave 0 prior weights,
poisoning-guard bounds, template split, seed range, per-family L1
thresholds in `PREREGISTRATION.md` §11, per-family L2 thresholds
calibrated at signature time from the crossed cells' frozen-wrong arm,
the `IntegrityAudit` guard list, the four decisive SET-level metrics,
the bundle-planting contract, the leakage audit tolerances, the
epiplexity implementation) is frozen; any change is a redesign
requiring a new preregistration hash.

## Files

- `paper.md` — the Wave 1b (COGR-E2b) technical report (~6000 words,
  plain Markdown). Structure: title, abstract, background (roadmap +
  L0 pilot + Wave 0 + Wave 1a summaries), design (3 × 3 × 3 factorial;
  L1 vs L2 rows; bundle planting; SET-level oracle; family redesigns;
  statistical leakage audit; propensity accounting; interventional
  edge-ablation; split-budget ablation; epiplexity; ten fatal gates;
  Modal budget), results (per-family PLACEHOLDER tables for the L1
  contribution rows, L2 recovery rows, bundle-awareness receipts,
  statistical leakage audit, non-ceiling headroom, epiplexity regime,
  and aggregate L1/L2 decisions), interpretation (pre-written for all
  four L1 × L2 verdict combinations), limitations, next (Wave 2
  beachhead), references.
- `README.md` — this file.

Figures are not required by this build; the paper is intentionally
text-and-table only so that the placeholder verdict rows are
unambiguous. If figures are added by a follow-up build task, they
should mirror the Wave 0 and Wave 1a figure conventions
(`figures/fig1.png` two-flashlight intuition, `figures/fig2.png`
three-family scaffolding, `figures/fig3.png` anti-leakage boundaries,
`figures/fig4.png` sweep matrix, `figures/fig5.png` per-family
sealed-outcome distributions, `figures/fig6.png` promotion-contract
gate diagram) and should never be substituted for the tables in §5.

## Reproduction

Wave 1b is reproduced end-to-end by the confirmatory Modal L4 run
driven from
`experiments/concern_gated_retrieval_e2/wave1b/run_confirmatory.py`
or `experiments/concern_gated_retrieval_e2/wave1b/modal_l4_sweep.py`
(one-shot wrapper: `scripts/deploy_and_run_cogr_wave1b.sh`).
Operational requirements (see `AGENTS.md` and the roadmap [1]):

- **L4 only.** Modal H100 is explicitly forbidden by the wave-wide
  operating rule. The Wave 1b Modal function is pinned to `gpu="L4"`
  and the local entrypoint refuses to fan out if the conservative
  cost estimate exceeds the wave-wide `$30.00` hard cap (still
  comfortably under the 35% H100 rate).
- **Modal app:** `research-derived-cogr-wave1b-e2b`.
- **`max_containers`:** up to 64 (explicitly authorized by the human
  director for Wave 1b above the Wave 1a default of 32).
- **Deploy before spawn.** `modal deploy` runs *before* the fan-out
  step so `Function.from_name/spawn` uses the deployed image and not
  a stale one.
- **Doppler scope.** `/Users/jawaun/superoptimizers`. The token is
  injected per-invocation; no `.env` file is committed anywhere in
  this subtree.
- **Deterministic seeds.** Confirmatory seed range `200000..201999`
  (verified disjoint from calibration range `100000..100999`). The
  template-split guard raises `LeakageError` on any calibration seed
  touched by a confirmatory code path. Wave 1b runs with
  `COGR_WAVE0_CONFIRMATORY_RUN=1` set at Modal spawn time.
- **No calibration templates.** Wave 1b code never touches templates
  in the `CALIBRATION` bucket. The template-split runtime tripwire
  raises `LeakageError` on any attempted crossing.
- **Deploy-time ignore list.** `add_local_dir` uses
  `ignore=[".git", ".worktrees", ".venv", "__pycache__", "*.pyc",
  "artifacts", "references/papers", "references/text",
  "references/html", "tmp", "output", "papers/*/paper.pdf",
  "papers/pdf", "**/*.png"]` to avoid uploading the 7.4 GB worktrees
  tree that got Wave 0 stuck.

After the Modal run completes,
`experiments/concern_gated_retrieval_e2/wave1b/PROVENANCE.md` §3-§10
is populated from the Modal receipt (Modal deploy hash, seed-range
receipt, per-family pre-run assertion receipt, per-family L1 and L2
gate receipts G0-G9, aggregate L1 verdict, aggregate L2 verdict,
epiplexity regime and measured wall-time speedup, and
`WAVE1B_ANALYSIS_HASH` mirrored between `PREREGISTRATION.md` §13 and
`PROVENANCE.md` §6). The signed preregistration is the sole channel
that turns the `TBD` numeric rows in `PROVENANCE.md` and the `TBD`
code freeze hash in `PREREGISTRATION.md` §13 into numeric or hash
values. No manual edit is permitted. When every G0-G9 gate reports
`PASS` on every family and every `TBD` is populated, Wave 1b promotes
L1 to `PASS` (and L2 to `PASS` iff the L2 preconditions in
`PROMOTION_CONTRACT_L2.md` are also satisfied). Wave 2's live-agent
beachhead may open against Wave 1b's L1 receipt (L1 path) or the L1
AND L2 conjunction receipt (L2 path).

## Wave-boundary claim

Wave 1b is a **crossed-factorial confirmation** on synthetic families
under sealed evaluation. Its two verdicts (L1 and L2) are issued
**separately** and are non-compensatory. Even a full L1 + L2 PASS is
only permission to open a Wave 2 live-agent beachhead as a
*continuation gate* — not an L3, L4, or L5 promotion. Every downstream
claim ladder step is gated on its own preregistration and its own
promotion contract; Wave 1b's receipts are inherited by Wave 2 for
the specific slot named in each Wave 2 preregistration and for
nothing else.

If Wave 1b's confirmatory receipt is a KILL on either L1 or L2, the
KILL paper is written honestly. No post-hoc threshold swaps to escape
a bad verdict.

## References

[1] Jawaun Brown. *Concern-Gated Retrieval: Theory, Evidence, and
Research Program.* `../../docs/concern_gated_retrieval_research_program.md`
in this repository (2026-07-23).

[2] Jawaun Brown. *Concern Recovery from an Adversarially Misspecified
Prior on Fixed Withheld Geometry: The COGR-E2a Screen.* Wave 1a
technical report.
[`../concern_gated_retrieval_e2a/paper.md`](../concern_gated_retrieval_e2a/paper.md)
in this repository (2026-07-23).

[3] Jawaun Brown. *Concern-Gated Retrieval Wave 0: Preregistered
Calibration and Wrong-Prior Scaffolding for Learned-Geometry
Confirmation.* Wave 0 technical report.
[`../concern_gated_retrieval_wave0/paper.md`](../concern_gated_retrieval_wave0/paper.md)
in this repository (2026-07-23).

[4] Zhang, S. and Levin, M. *Intelligence from Learnable Novelty.*
arXiv preprint arXiv:2607.18433v1, 2026.
