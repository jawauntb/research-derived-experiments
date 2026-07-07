"""Smoke test: the LSO + report pipeline runs end-to-end on synthetic data.

Confirms the plumbing (config -> decoders -> eval -> report) without needing
BBBD or torch installed at test time. Torch and pyRiemann ARE required at
run time; skip if unavailable.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

try:
    import torch  # noqa: F401
    import pyriemann  # noqa: F401
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


@unittest.skipUnless(HAS_DEPS, "torch + pyriemann required")
class TestSmokePipeline(unittest.TestCase):
    def test_smoke_run_produces_report(self):
        import numpy as np
        from coherence.config import load_kill_criterion
        from coherence.decoders import (
            CrossSubjectAdversarialDecoder,
            PerSubjectRiemannDecoder,
        )
        from coherence.evaluate import LeaveSubjectsOut
        from coherence.report import build_report

        rng = np.random.default_rng(0)
        n_subjects, n_ch, n_samp, n_epochs = 8, 16, 128, 30
        by_subject = {}
        for i in range(n_subjects):
            X = rng.standard_normal((n_epochs, n_ch, n_samp)).astype("float32")
            y = (X[:, 0].mean(axis=1) > 0).astype("int64")
            by_subject[f"sub-{i:03d}"] = (X, y)

        baseline = PerSubjectRiemannDecoder(n_folds=3)
        per_subject_baccs = []
        for _, (X, y) in by_subject.items():
            per_subject_baccs.append(
                baseline.fit_predict_within_subject(X, y)["balanced_accuracy"]
            )
        baseline_bacc = float(np.nanmean(per_subject_baccs))

        def factory():
            return CrossSubjectAdversarialDecoder(
                alignment="riemann", epochs=2, batch_size=16, lr=1e-3,
            )

        lso = LeaveSubjectsOut(
            epoch_seconds=4.0, n_lso_seeds=2, train_subject_sweep=(4, 6),
        )
        results = lso.run(by_subject, factory)
        self.assertGreater(len(results), 0)

        kc = load_kill_criterion(HERE.parent / "config" / "kill_criterion.yaml")
        with tempfile.TemporaryDirectory() as td:
            report_path = build_report(
                kc=kc, fold_results=results,
                per_subject_baseline_bacc=baseline_bacc,
                confound_ablations={},
                out_dir=Path(td),
            )
            self.assertTrue(report_path.exists())
            self.assertIn("Verdict", report_path.read_text())


if __name__ == "__main__":
    unittest.main()
