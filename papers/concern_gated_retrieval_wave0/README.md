# Concern-Gated Retrieval Wave 0 — Paper Directory

**Program:** Concern-Gated Retrieval (COGR) — Wave 0
**Deliverable:** technical report (`paper.md`) accompanying the Wave 0
preregistration, promotion contract, and calibration receipt at
`experiments/concern_gated_retrieval_e2/wave0/`.
**Wave-boundary reminder:** Wave 0 is **calibration-only**. It does not test
learned memory geometry, does not claim concern recovery from experience,
does not demonstrate semantic meaning, and does not support any
interpretation of selfhood. Any restatement of the Wave 0 paper as a
mechanism, meaning, or self-model result is inconsistent with the promotion
contract at
[`../../experiments/concern_gated_retrieval_e2/wave0/PROMOTION_CONTRACT.md`](../../experiments/concern_gated_retrieval_e2/wave0/PROMOTION_CONTRACT.md).

## Summary

This directory contains the Wave 0 technical report for the Concern-Gated
Retrieval E2 program. The paper (`paper.md`) motivates and documents a
calibration-only, scaffolding-only step whose purpose is to make the Wave 1
confirmatory experiments (COGR-E2a concern-recovery screening, COGR-E2b
learned-geometry confirmation) *rejectable*. It describes the sealed
environment interface, the three procedurally distinct calibration families
(delayed commitments; maintenance and fault response; resource-constrained
planning), the adversarially misspecified concern prior (a plausible alarm
region is inflated and at least one true commitment region is suppressed),
the fourteen-baseline slate the calibration sweep scores, the anti-leakage
contract (enumerated evaluator-only fields, sealed environment, static
`IntegrityAudit`, template-split runtime tripwire), the Modal L4 calibration
sweep (`≤ 35%` of the equivalent H100 rate; deploy before spawn; $10 hard
cap), and the seven non-compensatory promotion gates (G0-G6) that Wave 0
must clear to freeze the threshold row Wave 1 will be scored against. The
paper explicitly documents Wave 0's honest limitations — synthetic-only
evaluation, no premise audit against governed real-world traces (stub
receipt only), no concern update at evaluation time, no graph learning, no
multiplicative-vs-additive adjudication — and points forward to COGR-E2a
and COGR-E2b as the confirmatory experiments the Wave 0 freeze enables.

## Files

- `paper.md` — the Wave 0 technical report (~3500 words, plain Markdown).
- `README.md` — this file.
- `figures/fig1.png` … `figures/fig6.png` — figures produced by a parallel
  build task. Captions in `paper.md`:
  - Fig. 1 — two-flashlight intuition on a small synthetic graph;
  - Fig. 2 — three-family scaffolding, shared abstract retrieval problem
    with per-family surface variation;
  - Fig. 3 — anti-leakage boundaries (data-flow: solid = policy-visible,
    dashed = evaluator-only);
  - Fig. 4 — calibration sweep matrix of `(family, density, budget)` cells
    with per-cell wall-time and `n_rows` overlaid;
  - Fig. 5 — per-family sealed-outcome distributions across the
    fourteen-baseline slate, with wrong-prior and oracle-ceiling arms
    flagged;
  - Fig. 6 — promotion-contract gate diagram (G0-G6 in parallel with the
    non-compensatory promotion rule and demotion rule).

## Reproduction

Wave 0 is reproduced end-to-end by the wrapper script
[`../../scripts/deploy_and_run_cogr_wave0.sh`](../../scripts/deploy_and_run_cogr_wave0.sh),
which deploys the Modal app *before* spawning workers (a hard requirement of
this repo's Modal contract) and then runs the calibration preset. The wrapper
scopes secrets through Doppler at `/Users/jawaun/superoptimizers` and never
exports the token to the shell.

```bash
# From the repository root:

# 1. Dry-run the plan and print the conservative cost estimate.
#    Refuses to dispatch if the estimate exceeds $10.00 (build brief cap).
scripts/deploy_and_run_cogr_wave0.sh --dry-run

# 2. Deploy the Modal app and run the calibration preset. Writes the raw
#    Modal receipt to artifacts/cogr_wave0/calibration.json (gitignored)
#    and the slim public summary to
#    experiments/concern_gated_retrieval_e2/wave0/results/calibration_summary.json.
scripts/deploy_and_run_cogr_wave0.sh
```

Operational requirements (see `AGENTS.md` and the roadmap [1]):

- **L4 only.** Modal H100 is explicitly forbidden by the Wave 0 operating
  rule. The Modal function is pinned to `gpu="L4"` in
  `experiments/concern_gated_retrieval_e2/wave0/modal_l4_sweep.py` and the
  local entrypoint refuses to fan out at a cost above the $10.00 hard cap.
- **Deploy before spawn.** `modal deploy` runs before the fan-out step so
  `Function.from_name/spawn` and `.map` use the deployed image and not a
  stale one. The wrapper script enforces this ordering.
- **Doppler scope.** `/Users/jawaun/superoptimizers`. The wrapper injects
  the token per-invocation; no `.env` file is committed anywhere in this
  subtree.
- **Deterministic seeds.** Calibration seed range `100000..100999`
  (verified disjoint from the reserved confirmatory range
  `200000..201999`). The generator's seed-range guard refuses seeds outside
  the declared range for its declared mode.
- **No confirmatory rows.** Wave 0 code never touches templates in the
  `CONFIRMATION` bucket. The template-split runtime tripwire raises
  `LeakageError` on any attempted crossing.

After the Modal run completes, `PROVENANCE.md` §3-§6 is populated from the
Modal receipt (Modal deploy hash, seed-range receipt, per-family variance
receipt mirroring `PREREGISTRATION.md` §8, gate receipts G0-G6, and
`WAVE0_ANALYSIS_HASH`). The signed preregistration is the sole channel that
turns the `TBD` numeric rows in `PREREGISTRATION.md` §8 and the `TBD` code
freeze hash in `PREREGISTRATION.md` §11 into numeric or hash values. No
manual edit is permitted. When every G0-G6 gate reports `PASS` and every
`TBD` is populated, Wave 0 promotes to `frozen` and Wave 1 (COGR-E2a and
COGR-E2b) may open against the frozen threshold shape.

## References

[1] Jawaun Brown. *Concern-Gated Retrieval: Theory, Evidence, and Research
Program.* `../../docs/concern_gated_retrieval_research_program.md` in this
repository (2026-07-23).

[2] Zhang, S. and Levin, M. *Intelligence from Learnable Novelty.* arXiv
preprint arXiv:2607.18433v1, 2026.
