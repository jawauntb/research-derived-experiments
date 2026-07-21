from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.grounded_statecharts.evaluation import run_smoke_matrix
from experiments.grounded_statecharts.publish_public_dataset import generate_results


def test_publish_public_dataset_from_fixture_smoke(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    rows = []
    for result in run_smoke_matrix(run_id="pub", repeats=1):
        rows.append(result.public_row)
    source.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    out = tmp_path / "public"
    summary = generate_results(source_rows=source, output_dir=out)
    assert summary["row_count"] == len(rows)
    assert (out / "rows.jsonl").is_file()
    assert (out / "checksums.json").is_file()
    assert (out / "DATASET.md").is_file()
    published = json.loads((out / "rows.jsonl").read_text().splitlines()[0])
    assert "raw" not in published
    assert "responsible_component" not in published
    assert "predicted_component" not in published


def test_publish_rejects_raw_fields(tmp_path: Path) -> None:
    source = tmp_path / "dirty.jsonl"
    result = run_smoke_matrix(run_id="dirty", repeats=1)[0]
    dirty = dict(result.public_row)
    dirty["raw"] = {"x": 1}
    source.write_text(json.dumps(dirty) + "\n")
    with pytest.raises(ValueError, match="unsanitized|raw"):
        generate_results(source_rows=source, output_dir=tmp_path / "out")
