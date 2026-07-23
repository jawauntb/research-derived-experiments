#!/usr/bin/env bash
# Deploy and run the Concern-Gated Retrieval Wave 1a E2a confirmatory sweep
# on Modal L4.
#
# Wave 1a operating rules (see
# docs/concern_gated_retrieval_research_program.md and
# experiments/concern_gated_retrieval_e2/wave1a/PREREGISTRATION.md):
#
#   * L4 GPU only. Modal H100 is explicitly forbidden by the wave rule.
#   * Deploy the image before spawning, so ``Function.from_name/spawn`` and
#     ``.map`` use the deployed image and not a stale one.
#   * Doppler scope is ``/Users/jawaun/superoptimizers`` for auth. Never
#     export the token; the wrapper passes it through per-invocation.
#   * ``max_containers`` up to 32 — Wave 1a explicit authorization
#     (PREREGISTRATION.md §7).
#   * Confirmatory seed range is ``200000..201999``. The Modal spawn sets
#     ``COGR_WAVE0_CONFIRMATORY_RUN=1`` so the Wave 0 template-split
#     guard admits the confirmatory seeds; calibration seeds
#     ``100000..100999`` remain inaccessible under any invocation.
#   * Cost hard cap is ``$20``. The local entrypoint refuses to dispatch
#     when the conservative timeout-based estimate exceeds the cap.
#
# Usage:
#
#   scripts/deploy_and_run_cogr_wave1a.sh
#     -> deploys the app and runs the ``confirmatory`` preset, writing
#        the raw Modal receipt to ``artifacts/cogr_wave1a/e2a_rows.json``,
#        then aggregates the receipt into the screen verdict at
#        ``experiments/concern_gated_retrieval_e2/wave1a/results/verdict.json``.
#
#   scripts/deploy_and_run_cogr_wave1a.sh --dry-run
#     -> deploys the app and only prints the plan+cost estimate.
#
#   scripts/deploy_and_run_cogr_wave1a.sh --smoke
#     -> deploys and runs the tiny smoke preset (one family, 4 seeds).
#        Useful for verifying the container image + spawn path without
#        burning the full confirmatory budget.
#
#   scripts/deploy_and_run_cogr_wave1a.sh --no-aggregate
#     -> skip the local aggregation step (raw receipt only).
#
# The committed public verdict at
# ``experiments/concern_gated_retrieval_e2/wave1a/results/verdict.json``
# is produced by the aggregator step; the raw Modal receipt at
# ``artifacts/cogr_wave1a/e2a_rows.json`` is gitignored per ``AGENTS.md``.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

DOPPLER_SCOPE="/Users/jawaun/superoptimizers"
MODAL_FILE="experiments/concern_gated_retrieval_e2/wave1a/modal_l4_sweep.py"
OUT_PATH="artifacts/cogr_wave1a/e2a_rows.json"
VERDICT_PATH="experiments/concern_gated_retrieval_e2/wave1a/results/verdict.json"

PRESET="confirmatory"
DRY_RUN_BUDGET=""
RUN_AGGREGATE="1"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --preset)
            PRESET="$2"; shift 2 ;;
        --out)
            OUT_PATH="$2"; shift 2 ;;
        --verdict)
            VERDICT_PATH="$2"; shift 2 ;;
        --dry-run)
            DRY_RUN_BUDGET="--dry-run-budget"; shift ;;
        --smoke)
            PRESET="smoke"; shift ;;
        --no-aggregate)
            RUN_AGGREGATE="0"; shift ;;
        *)
            echo "Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

mkdir -p "$(dirname "${OUT_PATH}")"
mkdir -p "$(dirname "${VERDICT_PATH}")"

echo "[cogr-wave1a] Deploying Modal app from ${MODAL_FILE}"
doppler --scope "${DOPPLER_SCOPE}" run -- \
    uvx --python 3.12 --with numpy --from modal modal deploy \
    "${MODAL_FILE}"

echo "[cogr-wave1a] Running preset=${PRESET} out=${OUT_PATH} ${DRY_RUN_BUDGET}"
# COGR_WAVE0_CONFIRMATORY_RUN=1 licenses the confirmatory pool per
# PREREGISTRATION.md §7. Calibration seeds 100000..100999 are still
# refused by the Wave 0 template-split guard.
COGR_WAVE0_CONFIRMATORY_RUN=1 \
doppler --scope "${DOPPLER_SCOPE}" run -- \
    uvx --python 3.12 --with numpy --from modal modal run \
    "${MODAL_FILE}" \
    --preset "${PRESET}" \
    --out "${OUT_PATH}" \
    ${DRY_RUN_BUDGET}

if [[ -n "${DRY_RUN_BUDGET}" ]]; then
    echo "[cogr-wave1a] Dry-run complete; aggregator skipped."
    exit 0
fi

if [[ "${RUN_AGGREGATE}" != "1" ]]; then
    echo "[cogr-wave1a] --no-aggregate set; skipping aggregator."
    exit 0
fi

echo "[cogr-wave1a] Aggregating raw receipt into verdict at ${VERDICT_PATH}"
uv run --no-sync python -m experiments.concern_gated_retrieval_e2.wave1a.run_confirmatory \
    --in "${OUT_PATH}" \
    --out "${VERDICT_PATH}"
