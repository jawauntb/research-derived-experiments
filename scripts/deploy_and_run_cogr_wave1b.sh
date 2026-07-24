#!/usr/bin/env bash
# Deploy and run the Concern-Gated Retrieval Wave 1b E2b confirmatory
# crossed-factorial sweep on Modal L4.
#
# Wave 1b operating rules (see
# docs/concern_gated_retrieval_research_program.md and
# experiments/concern_gated_retrieval_e2/wave1b/PREREGISTRATION.md):
#
#   * L4 GPU only. Modal H100 is explicitly forbidden by the wave rule.
#   * Deploy the image before spawning, so ``Function.from_name/spawn`` and
#     ``.map`` use the deployed image and not a stale one (memory:
#     ``feedback_modal_deploy_before_spawn``).
#   * Doppler scope is ``/Users/jawaun/superoptimizers`` for auth. Never
#     export the token; the wrapper passes it through per-invocation.
#   * ``max_containers`` up to 64 — Wave 1b explicit authorization (build
#     brief).
#   * Confirmatory seed range is ``200000..201999``. The Modal spawn sets
#     ``COGR_WAVE0_CONFIRMATORY_RUN=1`` so the Wave 0 template-split
#     guard admits the confirmatory seeds; calibration seeds
#     ``100000..100999`` remain inaccessible under any confirmatory
#     invocation.  (The aggregator step runs the leakage audit against
#     the calibration slice; it does not touch the sealed evaluator on
#     confirmatory episodes and so does not need the env flag.)
#   * Cost hard cap is ``$30``. The local entrypoint refuses to dispatch
#     when the conservative timeout-based estimate exceeds the cap.
#
# Usage:
#
#   scripts/deploy_and_run_cogr_wave1b.sh
#     -> deploys the app and runs the ``confirmatory`` preset, writing
#        the raw Modal receipt to ``artifacts/cogr_wave1b/rows.json``,
#        then aggregates the receipt into the L1 and L2 verdicts at
#        ``experiments/concern_gated_retrieval_e2/wave1b/results/verdict_L1.json``
#        and ``.../results/verdict_L2.json``.
#
#   scripts/deploy_and_run_cogr_wave1b.sh --dry-run
#     -> deploys the app and only prints the plan+cost estimate.
#
#   scripts/deploy_and_run_cogr_wave1b.sh --smoke
#     -> deploys and runs the tiny smoke preset (one cell, 4 seeds).
#        Useful for verifying the container image + spawn path without
#        burning the full confirmatory budget.
#
#   scripts/deploy_and_run_cogr_wave1b.sh --no-aggregate
#     -> skip the local aggregation step (raw receipt only).
#
# The committed public verdicts at
# ``experiments/concern_gated_retrieval_e2/wave1b/results/verdict_L1.json``
# and ``.../results/verdict_L2.json`` are produced by the aggregator
# step; the raw Modal receipt at ``artifacts/cogr_wave1b/rows.json`` is
# gitignored per ``AGENTS.md``.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

DOPPLER_SCOPE="/Users/jawaun/superoptimizers"
MODAL_FILE="experiments/concern_gated_retrieval_e2/wave1b/modal_l4_sweep.py"
OUT_PATH="artifacts/cogr_wave1b/rows.json"
L1_VERDICT_PATH="experiments/concern_gated_retrieval_e2/wave1b/results/verdict_L1.json"
L2_VERDICT_PATH="experiments/concern_gated_retrieval_e2/wave1b/results/verdict_L2.json"

PRESET="confirmatory"
DRY_RUN_BUDGET=""
RUN_AGGREGATE="1"
AGGREGATE_EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --preset)
            PRESET="$2"; shift 2 ;;
        --out)
            OUT_PATH="$2"; shift 2 ;;
        --l1-verdict)
            L1_VERDICT_PATH="$2"; shift 2 ;;
        --l2-verdict)
            L2_VERDICT_PATH="$2"; shift 2 ;;
        --dry-run)
            DRY_RUN_BUDGET="--dry-run-budget"; shift ;;
        --smoke)
            PRESET="smoke"
            # A smoke preset with 4 seeds can't sustain the leakage
            # audit's default calibration slice; skip the audit so the
            # smoke path still produces a verdict receipt.
            AGGREGATE_EXTRA_ARGS+=("--skip-leakage-audit")
            shift ;;
        --no-aggregate)
            RUN_AGGREGATE="0"; shift ;;
        *)
            echo "Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

mkdir -p "$(dirname "${OUT_PATH}")"
mkdir -p "$(dirname "${L1_VERDICT_PATH}")"
mkdir -p "$(dirname "${L2_VERDICT_PATH}")"

echo "[cogr-wave1b] Deploying Modal app from ${MODAL_FILE}"
doppler --scope "${DOPPLER_SCOPE}" run -- \
    uvx --python 3.12 --with numpy --from modal modal deploy \
    "${MODAL_FILE}"

echo "[cogr-wave1b] Running preset=${PRESET} out=${OUT_PATH} ${DRY_RUN_BUDGET}"
# COGR_WAVE0_CONFIRMATORY_RUN=1 licenses the confirmatory pool per
# PREREGISTRATION.md §5.  Calibration seeds 100000..100999 are still
# refused by the Wave 0 template-split guard on the sweep workers; the
# aggregator's leakage audit runs the calibration slice locally against
# the wave1b family generators (which validate their own buckets).
COGR_WAVE0_CONFIRMATORY_RUN=1 \
doppler --scope "${DOPPLER_SCOPE}" run -- \
    uvx --python 3.12 --with numpy --from modal modal run \
    "${MODAL_FILE}" \
    --preset "${PRESET}" \
    --out "${OUT_PATH}" \
    ${DRY_RUN_BUDGET}

if [[ -n "${DRY_RUN_BUDGET}" ]]; then
    echo "[cogr-wave1b] Dry-run complete; aggregator skipped."
    exit 0
fi

if [[ "${RUN_AGGREGATE}" != "1" ]]; then
    echo "[cogr-wave1b] --no-aggregate set; skipping aggregator."
    exit 0
fi

echo "[cogr-wave1b] Aggregating raw receipt into verdicts at"
echo "  L1: ${L1_VERDICT_PATH}"
echo "  L2: ${L2_VERDICT_PATH}"
uv run --no-sync python -m experiments.concern_gated_retrieval_e2.wave1b.run_confirmatory \
    --in "${OUT_PATH}" \
    --out-l1 "${L1_VERDICT_PATH}" \
    --out-l2 "${L2_VERDICT_PATH}" \
    "${AGGREGATE_EXTRA_ARGS[@]}"
