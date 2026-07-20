from __future__ import annotations

import json

from experiments.grounded_statecharts.constraint_ood import generate_results


def test_constraint_ood_stubs_register_two_unobserved_probes(tmp_path) -> None:
    summary = generate_results(tmp_path)
    rows = [json.loads(line) for line in (tmp_path / "rows.jsonl").read_text().splitlines()]

    assert all(summary["gates"].values())
    assert [row["probe_id"] for row in rows] == [
        "held_out_wording",
        "deeper_delegation_depth",
    ]
    assert all(row["execution_status"] == "planned" for row in rows)
    assert not any(row["observed"] for row in rows)
    assert rows[0]["planned_depths"] == [1, 2, 3, 4]
    assert rows[1]["planned_depths"] == [5, 6]
