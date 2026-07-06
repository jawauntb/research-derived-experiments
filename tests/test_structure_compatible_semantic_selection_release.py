from __future__ import annotations

import json

from experiments.structure_compatible_generalization.publish_semantic_selection_rows import (
    build_release,
    write_release,
)
from experiments.structure_compatible_generalization.semantic_selection_control import (
    run_fixture_selection_control_sweep,
    semantic_selection_payload,
)
from experiments.structure_compatible_generalization.semantic_selection_tiebreak_stress import (
    build_tiebreak_report,
)


def _fixture_payload() -> dict:
    rows = run_fixture_selection_control_sweep(n_zoos=4, configs_per_zoo=8)
    return semantic_selection_payload(rows=rows, manifest={"fixture": True})


def test_phase6_row_release_writes_jsonl(tmp_path) -> None:
    release = build_release(_fixture_payload())
    paths = write_release(release, tmp_path)
    rel_paths = {path.relative_to(tmp_path).as_posix() for path in paths}

    assert "experiments/structure_compatible_generalization/results/semantic_selection_rows_2026_07_06.jsonl" in rel_paths
    assert "experiments/structure_compatible_generalization/results/semantic_selection_records_2026_07_06.jsonl" in rel_paths
    rows_path = tmp_path / "experiments/structure_compatible_generalization/results/semantic_selection_rows_2026_07_06.jsonl"
    first_row = json.loads(rows_path.read_text().splitlines()[0])
    assert first_row["domain"] == "semantic_retrieval_frozen_encoder"
    assert "selection_zoo" in first_row["metadata"]


def test_tiebreak_report_covers_registered_modes() -> None:
    report = build_tiebreak_report(_fixture_payload(), reps=25, seed=123)

    assert report["bootstrap_unit"] == "selection_zoo"
    assert set(report["tie_modes"]) == {"mean_ties", "random_tie", "worst_tie"}
    assert report["modes"]["mean_ties"]["point_metrics"]["learned_lift_vs_random"] > 0.0
    assert "learned_lift_vs_wrong" in report["modes"]["random_tie"]["bootstrap_ci95"]
