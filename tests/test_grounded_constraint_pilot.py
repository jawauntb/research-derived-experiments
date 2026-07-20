from __future__ import annotations

import json

from experiments.grounded_statecharts.constraint_pilot import generate_results


def test_constraint_pilot_reuses_deterministic_diagonal(tmp_path) -> None:
    summary = generate_results(tmp_path)

    rows = [json.loads(line) for line in (tmp_path / "rows.jsonl").read_text().splitlines()]

    assert summary["gates"] == {
        "two_fixture_families": True,
        "depths_one_through_four": True,
        "deterministic_source_reused": True,
        "no_provider_calls": True,
    }
    assert len(rows) == 16
    assert summary["factorial_design"]["unobserved_cells"] == [
        "prose_guard_present",
        "typed_guard_absent",
    ]
    assert {row["source_condition"] for row in rows} == {"lossy_prompt", "typed_guarded"}
