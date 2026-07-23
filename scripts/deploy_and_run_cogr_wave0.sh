#!/usr/bin/env bash
# Deploy and run the Concern-Gated Retrieval Wave 0 calibration on Modal L4.
#
# Wave 0 operating rules (see docs/concern_gated_retrieval_research_program.md
# and experiments/concern_gated_retrieval_e2/wave0/PREREGISTRATION.md):
#
#   * L4 GPU only. Modal H100 is explicitly forbidden by the wave rule.
#   * Deploy the image before spawning, so ``Function.from_name/spawn`` and
#     ``.map`` use the deployed image and not a stale one.
#   * Doppler scope is ``/Users/jawaun/superoptimizers`` for auth. Never
#     export the token; the wrapper passes it through per-invocation.
#   * Cost hard cap is $10.0 (build brief). The local entrypoint refuses to
#     dispatch when the conservative timeout-based estimate exceeds the cap.
#
# Usage:
#
#   scripts/deploy_and_run_cogr_wave0.sh
#     -> deploys the app and runs the ``calibration`` preset, writing
#        the raw Modal receipt to ``artifacts/cogr_wave0/calibration.json``.
#
#   scripts/deploy_and_run_cogr_wave0.sh --dry-run
#     -> deploys the app and only prints the plan+cost estimate.
#
# The committed public receipt at
# ``experiments/concern_gated_retrieval_e2/wave0/results/calibration_summary.json``
# is produced separately by the local ``calibrate.py`` CLI; Modal writes
# only the raw artifact.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

DOPPLER_SCOPE="/Users/jawaun/superoptimizers"
MODAL_FILE="experiments/concern_gated_retrieval_e2/wave0/modal_l4_sweep.py"
OUT_PATH="artifacts/cogr_wave0/calibration.json"

PRESET="calibration"
DRY_RUN_BUDGET=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --preset)
            PRESET="$2"; shift 2 ;;
        --out)
            OUT_PATH="$2"; shift 2 ;;
        --dry-run)
            DRY_RUN_BUDGET="--dry-run-budget"; shift ;;
        *)
            echo "Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

mkdir -p "$(dirname "${OUT_PATH}")"

echo "[cogr-wave0] Deploying Modal app from ${MODAL_FILE}"
doppler --scope "${DOPPLER_SCOPE}" run -- \
    uvx --python 3.12 --with numpy --from modal modal deploy \
    "${MODAL_FILE}"

echo "[cogr-wave0] Running preset=${PRESET} out=${OUT_PATH} ${DRY_RUN_BUDGET}"
doppler --scope "${DOPPLER_SCOPE}" run -- \
    uvx --python 3.12 --with numpy --from modal modal run \
    "${MODAL_FILE}" \
    --preset "${PRESET}" \
    --out "${OUT_PATH}" \
    ${DRY_RUN_BUDGET}
