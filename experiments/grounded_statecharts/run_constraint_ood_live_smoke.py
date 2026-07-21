"""Opt-in credentialed live smoke for the held-out paraphrase OOD probe.

Reruns the frozen D2 `recursive_constrained_tool_use` held-out task bank
under paraphrased (held-out, still name-free) instruction wording through
the harness-v2 name-free contract: default prompts stay instruction-only,
`condition_policy.py` enforces external capability narrowing from harness
code (not the prompt), and the primary metric is the task-clustered
joint_success paired effect between `envelope_external_guards` and
`envelope_only`.

Requires GROUNDED_HARNESS_LIVE=1. Rejects GROUNDED_HARNESS_LABELED_PROMPT=1
-- this probe is name-free by design and must stay that way to test the
harness-v2 contract, not the labeled-prompt diagnostic. Writes only under
gitignored artifacts/.

Kill criterion: if the live joint_success delta falls below
`OOD_KILL_THRESHOLD` (0.15, matching the D3 sample-size plan's escalation
threshold), this module records that collapse. It does not reinterpret a
small, absent, or negative delta as evidence of transport.

Example:

    GROUNDED_HARNESS_LIVE=1 \
    GROUNDED_HARNESS_PROVIDER=openai \
    GROUNDED_HARNESS_MODEL=gpt-4.1-mini \
    doppler run --config dev -- \
      python3 -m experiments.grounded_statecharts.run_constraint_ood_live_smoke
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.adapters.live import (
    LIVE_LABELED_PROMPT_ENV,
    LIVE_OPT_IN_ENV,
    LiveExecutor,
)
from experiments.grounded_statecharts.constraint_ood import (
    OOD_KILL_THRESHOLD,
    run_held_out_paraphrase_probe,
)
from experiments.grounded_statecharts.runtime import canonical_json

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    REPO_ROOT / "artifacts" / "grounded_statecharts" / "constraint_ood_live_smoke"
)


def generate_results(
    output_dir: Path, *, executor: LiveExecutor | None = None
) -> dict[str, Any]:
    if os.environ.get(LIVE_OPT_IN_ENV, "").strip() != "1":
        raise RuntimeError(f"set {LIVE_OPT_IN_ENV}=1 for credentialed OOD smoke")
    if os.environ.get(LIVE_LABELED_PROMPT_ENV, "").strip() == "1":
        raise RuntimeError(
            f"unset {LIVE_LABELED_PROMPT_ENV}; the held-out paraphrase probe "
            "requires name-free prompts"
        )
    if "results" in output_dir.parts:
        raise RuntimeError("refusing to write live OOD smoke under results/")

    active = executor or LiveExecutor.from_env()
    result = run_held_out_paraphrase_probe(
        executor=active,
        adapter_id="live",
        run_id="constraint-ood-paraphrase-live",
    )
    rows = result["rows"]
    effect = result["joint_success_effect"]
    point_estimate = effect["point_estimate"]
    kill_triggered = point_estimate is None or point_estimate < OOD_KILL_THRESHOLD

    summary: dict[str, Any] = {
        **{key: value for key, value in result.items() if key != "rows"},
        "kill_threshold": OOD_KILL_THRESHOLD,
        "kill_triggered": kill_triggered,
        "allowed_claim": (
            "Under the harness-v2 name-free contract, held-out paraphrased "
            "instructions for the recursive_constrained_tool_use family "
            "produced a live joint_success effect of "
            f"{point_estimate!r} for envelope_external_guards vs "
            "envelope_only across "
            f"{effect['task_count']} paired held-out tasks. This reports "
            "one credentialed run against one declared model; it is a "
            "smoke, not a powered D3 confirmatory result."
            if not kill_triggered
            else "KILL: under the harness-v2 name-free contract, the live "
            "joint_success delta for held-out paraphrased wording "
            f"({point_estimate!r}) fell below the {OOD_KILL_THRESHOLD} "
            "threshold (or no paired tasks were publishable). This is "
            "recorded as evidence against constraint transport surviving "
            "held-out wording for this model/run, not reinterpreted as a "
            "pass."
        ),
        "non_claims": [
            "Not a D3 confirmatory Constraint Transport result.",
            "Not powered: a single credentialed run over "
            f"{result['task_count_attempted']} held-out tasks x "
            f"{result['episode_count']} episodes, one repeat.",
            "Raw provider transcripts remain outside public results/ and "
            "outside this artifacts/ bundle's rows.",
            "Does not authorize any commercial or product-readiness claim.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "rows.jsonl").write_text(
        "\n".join(canonical_json(row) for row in rows) + ("\n" if rows else "")
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if "results" in args.output_dir.parts:
        raise SystemExit("refusing to write live OOD smoke under results/")
    summary = generate_results(args.output_dir)
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir),
                "provider_id": summary["provider_id"],
                "model_id": summary["model_id"],
                "joint_success_effect": summary["joint_success_effect"],
                "kill_triggered": summary["kill_triggered"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
