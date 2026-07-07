#!/usr/bin/env python3
"""End-to-end Phase-0 driver.

Loads the pre-registered kill-criterion + phase-0 config, ingests BBBD,
preprocesses each subject, runs the baseline (per-subject) + target
(cross-subject) decoders, evaluates leave-subjects-out, and dumps the
GO/KILL report.

Usage:

    python3 scripts/run_phase0.py \\
        --config config/phase0.yaml \\
        --out artifacts/phase0

    # Fast dry-run to validate the pipeline plumbing (does not require BBBD).
    python3 scripts/run_phase0.py --smoke
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from coherence.config import load_kill_criterion, load_phase0  # noqa: E402
from coherence.decoders import (  # noqa: E402
    CrossSubjectAdversarialDecoder,
    PerSubjectRiemannDecoder,
)
from coherence.evaluate import LeaveSubjectsOut  # noqa: E402
from coherence.report import build_report  # noqa: E402


def _smoke_by_subject(rng: np.random.Generator, n_subjects: int = 12,
                      n_channels: int = 32, n_samples: int = 128,
                      per_subject_epochs: int = 40
                      ) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Synthetic data that respects the API — the decoders + eval must run,
    but the numbers are meaningless. Confirms the plumbing without needing
    BBBD on disk."""
    out: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for i in range(n_subjects):
        X = rng.standard_normal((per_subject_epochs, n_channels, n_samples)).astype(np.float32)
        # Weak per-channel signal to keep something learnable.
        y = (X[:, 0].mean(axis=1) > 0).astype(np.int64)
        out[f"sub-{i:03d}"] = (X, y)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/phase0.yaml")
    parser.add_argument("--out", default="artifacts/phase0")
    parser.add_argument("--smoke", action="store_true",
                        help="Synthetic data — validates plumbing without BBBD.")
    args = parser.parse_args()

    cfg = load_phase0(args.config)
    kc = load_kill_criterion(cfg.kill_criterion_path)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    manifest: dict[str, object] = {
        "kill_criterion_version": kc.version,
        "kill_criterion_sha256": kc.content_hash,
        "phase0_config": str(Path(args.config).resolve()),
        "smoke": bool(args.smoke),
        "started_at_unix": int(started),
    }

    if args.smoke:
        rng = np.random.default_rng(0)
        by_subject = _smoke_by_subject(rng)
    else:
        by_subject = _real_ingest(cfg)

    manifest["n_subjects"] = len(by_subject)

    baseline = PerSubjectRiemannDecoder(
        n_folds=int(cfg.decoders["baseline"]["n_folds"]),
    )
    per_subject_baccs = []
    for _, (X, y) in by_subject.items():
        stats = baseline.fit_predict_within_subject(X, y)
        if not np.isnan(stats["balanced_accuracy"]):
            per_subject_baccs.append(stats["balanced_accuracy"])
    per_subject_baseline = float(np.mean(per_subject_baccs)) if per_subject_baccs else 0.5
    manifest["per_subject_baseline_balanced_accuracy"] = per_subject_baseline

    def factory():
        return CrossSubjectAdversarialDecoder(
            alignment=cfg.decoders["target"]["alignment"],
            adversary_weight=float(cfg.decoders["target"]["adversary_weight"]),
            ssl_pretrain=bool(cfg.decoders["target"]["ssl_pretrain"]),
            epochs=int(cfg.decoders["target"]["epochs"]),
            batch_size=int(cfg.decoders["target"]["batch_size"]),
            lr=float(cfg.decoders["target"]["lr"]),
        )

    lso = LeaveSubjectsOut(
        epoch_seconds=float(cfg.preprocess["epoch_seconds"]),
        n_lso_seeds=int(cfg.evaluate["n_lso_seeds"]),
        train_subject_sweep=tuple(int(n) for n in cfg.evaluate["train_subject_sweep"]),
    )
    fold_results = lso.run(by_subject, factory)

    confound_ablations = _run_confound_ablations(kc, by_subject, factory, lso)

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    with (out_dir / "run.jsonl").open("w") as jl:
        for r in fold_results:
            jl.write(json.dumps({k: (list(v) if isinstance(v, tuple) else v)
                                 for k, v in asdict(r).items()}) + "\n")

    build_report(
        kc=kc,
        fold_results=fold_results,
        per_subject_baseline_bacc=per_subject_baseline,
        confound_ablations=confound_ablations,
        out_dir=out_dir,
    )
    print(f"Wrote report to {out_dir / 'report.md'}")
    return 0


def _real_ingest(cfg) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Ingest BBBD + preprocess into per-subject (X, y) arrays.

    Kept in a helper so `--smoke` doesn't import mne (which is optional in
    dev environments). This side is deliberately the thin wiring — the heavy
    lifting is in coherence.ingest and coherence.preprocess.
    """
    from coherence.ingest.bbbd import BBBDLoader  # noqa: PLC0415
    from coherence.preprocess import PreprocessConfig, epoch_to_arrays, preprocess_raw  # noqa: PLC0415

    pcfg = PreprocessConfig(
        highpass_hz=float(cfg.preprocess["highpass_hz"]),
        notch_hz=tuple(float(f) for f in cfg.preprocess["notch_hz"]),
        resample_hz=int(cfg.preprocess["resample_hz"]),
        notch_16hz_experiments=tuple(int(e) for e in cfg.preprocess["notch_16hz_experiments"]),
        epoch_seconds=float(cfg.preprocess["epoch_seconds"]),
        epoch_overlap=float(cfg.preprocess["epoch_overlap"]),
        reject_peak_to_peak_uv=float(cfg.preprocess["reject_peak_to_peak_uv"]),
    )
    loader = BBBDLoader(experiments=list(cfg.data["experiments"]))
    subject_limit = cfg.data.get("subject_limit")
    subject_ids = loader.subjects()
    if subject_limit:
        subject_ids = subject_ids[: int(subject_limit)]

    by_subject: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for record in loader.records(subject_ids=subject_ids):
        raw = loader.load_signal(record)
        raw = preprocess_raw(raw, pcfg, experiment=record.experiment)
        X, y = epoch_to_arrays(raw, pcfg, label_getter=_bbbd_attention_labeler(record))
        if len(y) == 0:
            continue
        prior = by_subject.get(record.subject_id)
        if prior is None:
            by_subject[record.subject_id] = (X, y)
        else:
            by_subject[record.subject_id] = (
                np.concatenate([prior[0], X], axis=0),
                np.concatenate([prior[1], y], axis=0),
            )
    return by_subject


def _bbbd_attention_labeler(record):
    """Return a callable that maps (t0, t1) -> attentive(1)/distracted(0)/None.

    Placeholder until BBBD event tsv parsing lands. Uses the recording label
    if the participant table carries one; otherwise leaves epochs unlabeled
    so they're dropped rather than mis-labeled.
    """
    label = record.labels.get("attention_label")
    if label in (0, 1, "0", "1"):
        binary = int(label)
        return lambda _t0, _t1: binary
    return lambda _t0, _t1: None


def _run_confound_ablations(_kc, _by_subject, _factory, _lso):
    """Currently: reports 'NOT RUN' for every declared confound. Wire the
    real ablations in as they land (16 Hz band-zero, train/test stat isolation
    unit test, prior-only baseline). The report writer surfaces the gap
    honestly rather than pretending the confound passed."""
    return {}


if __name__ == "__main__":
    raise SystemExit(main())
