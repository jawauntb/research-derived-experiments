"""Run the deterministic two-family Grounded Statecharts D2 mechanics smoke."""

from __future__ import annotations

import json

from experiments.grounded_statecharts.budgets import DEFAULT_PILOT_BUDGET
from experiments.grounded_statecharts.statechart_pilot import run_statechart_pilot_smoke


def main() -> None:
    results = run_statechart_pilot_smoke()
    print(
        json.dumps(
            {
                "episode_count": len(results),
                "all_publishable": all(result.integrity.publishable for result in results),
                "all_default_budget": all(
                    result.budget_receipt.spec == DEFAULT_PILOT_BUDGET
                    for result in results
                ),
                "held_out_outcomes": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
