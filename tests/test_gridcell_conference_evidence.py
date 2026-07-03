from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_gridcell_conference_evidence.py"


def load_module():
    spec = importlib.util.spec_from_file_location("gridcell_conference_evidence", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_cell(condition: str, idx: int, *, toroidal: bool) -> dict:
    base = 0.1 * idx
    return {
        "augment": condition,
        "arch": "rnn" if idx % 2 == 0 else "gru",
        "seed": 20260628 + idx,
        "weakness_translation": 0.7 + base if condition == "full_translation" else 0.3 + base / 10,
        "weakness_wrong_group": 0.02 + base / 20,
        "toroidal_score": 0.30 + base / 5 if toroidal else base / 100,
        "betti_match_torus": toroidal,
        "betti1_estimate": 2 if toroidal else 0,
        "h1_top2": [0.4 + base / 10, 0.3 + base / 10],
        "h2_top": 0.3 if toroidal else 0.0,
        "fourier_pr": 4.0 + idx if condition == "full_translation" else 8.0 + idx,
        "id_accuracy": 0.95 - base / 20,
        "ood_accuracy": 0.90 - base / 10 if condition == "full_translation" else 0.55 - base / 20,
        "ood_by_arena": {
            "1": 0.95 - base / 20,
            "1.25": 0.92 - base / 20,
            "2": 0.90 - base / 10 if condition == "full_translation" else 0.55 - base / 20,
        },
        "final_loss": 0.1 + base / 10,
        "coverage": 1.0,
        "topology_robustness": [
            {
                "bin_count": 16,
                "edge_percentile": 45.0,
                "empty_policy": "global_mean",
                "max_points": 200,
                "coverage": 1.0,
                "toroidal_score": 0.30 + base / 5 if toroidal else base / 100,
                "betti_match_torus": toroidal,
            }
        ],
    }


class GridCellConferenceEvidenceTests(unittest.TestCase):
    def test_conference_evidence_exports_csvs_and_report(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cells = [make_cell("full_translation", i, toroidal=i < 5) for i in range(6)]
            cells += [make_cell("none", i + 6, toroidal=False) for i in range(6)]
            raw = tmp_path / "sweep.json"
            raw.write_text(json.dumps({
                "kind": "test sweep",
                "manifest": {
                    "conditions": ["full_translation", "none"],
                    "archs": ["rnn", "gru"],
                    "seeds": list(range(6)),
                    "steps": 10,
                    "decode_arenas": [1.0, 1.25, 2.0],
                },
                "analysis": {},
                "cells": cells,
            }))

            out_dir = tmp_path / "out"
            paths = module.run_analysis(raw, out_dir, date="test", bootstrap_samples=100)

            self.assertTrue(paths.raw_cells.exists())
            self.assertTrue(paths.aggregate.exists())
            self.assertTrue(paths.ood.exists())
            self.assertTrue(paths.within_toroidal.exists())
            self.assertTrue(paths.robustness.exists())
            self.assertTrue(paths.report.exists())

            with paths.raw_cells.open() as f:
                raw_rows = list(csv.DictReader(f))
            self.assertEqual(len(raw_rows), 12)
            self.assertIn("ood_arena_2", raw_rows[0])

            with paths.aggregate.open() as f:
                aggregate_rows = list(csv.DictReader(f))
            self.assertTrue(any(
                r["condition"] == "full_translation" and r["metric"] == "weakness_translation"
                for r in aggregate_rows
            ))
            self.assertTrue(any(r["metric"] == "torus_match" and r["ci_method"] == "wilson" for r in aggregate_rows))

            with paths.within_toroidal.open() as f:
                within_rows = list(csv.DictReader(f))
            self.assertTrue(any(
                r["subset"] == "full_translation" and r["comparison"] == "rho_weakness_ood"
                for r in within_rows
            ))

            with paths.robustness.open() as f:
                robustness_rows = list(csv.DictReader(f))
            self.assertTrue(any(r["status"] == "computed" and r["bin_count"] == "16" for r in robustness_rows))

            report = paths.report.read_text()
            self.assertIn("Condition Metrics With 95% Intervals", report)
            self.assertIn("Topology robustness rows were computed", report)


if __name__ == "__main__":
    unittest.main()
