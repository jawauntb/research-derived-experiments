from __future__ import annotations

import json

from experiments.structure_compatible_generalization.publish_phase_row_ledgers import (
    build_phase_payloads,
    write_ledgers,
)


def test_phase_row_ledgers_smoke_profile_writes_all_phases(tmp_path) -> None:
    payloads = build_phase_payloads(profile="smoke", semantic_fixture=True)
    paths = write_ledgers(payloads, out_root=tmp_path)

    manifest_path = tmp_path / "experiments/structure_compatible_generalization/results/phase_row_ledgers_manifest_2026_07_06.json"
    manifest = json.loads(manifest_path.read_text())
    row_paths = [path for path in paths if path.suffix == ".jsonl"]

    assert len(payloads) == 5
    assert len(row_paths) == 5
    assert len(manifest["artifacts"]) == 5
    assert all(meta["rows"] > 0 for meta in manifest["artifacts"].values())
