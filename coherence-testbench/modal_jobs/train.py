#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal entrypoint for the Phase-0 gate run.

Mirrors the parent repo's Doppler-scoped invocation pattern
(experiments/symbolic_weakness/modal_neural_sweep.py). Run with:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
            coherence-testbench/modal_jobs/train.py \\
            --config config/phase0.yaml \\
            --out artifacts/phase0

Each experiment (1..5) fans out as an independent shard so ingest + preprocess
run in parallel. The driver merges results and calls the report generator on
the local side (so `report.md` lands in the repo artifacts, not on the worker).
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")


IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("libgl1", "libglib2.0-0")
    .pip_install(
        "torch>=2.5,<2.8",
        "numpy>=1.26,<2.0",
        "scipy>=1.11",
        "scikit-learn>=1.4",
        "mne>=1.7",
        "mne-bids>=0.15",
        "pyEDFlib>=0.1.36",
        "braindecode>=0.8",
        "pyriemann>=0.6",
        "pyyaml>=6.0",
        "pydantic>=2.6",
        "logfire>=0.30",
    )
)

app = modal.App(name="coherence-testbench-phase0")

# Persistent volume for the BBBD BIDS tree.
bbbd_volume = modal.Volume.from_name("bbbd-cache", create_if_missing=True)
BBBD_MOUNT = "/data/bbbd"

# Secrets pulled from Doppler at runtime (Modal reads them from the shell env).
env_secret = modal.Secret.from_dict({
    "BBBD_CACHE_DIR": BBBD_MOUNT,
})


@app.function(
    image=IMAGE,
    timeout=6 * 60 * 60,
    cpu=8,
    memory=32 * 1024,
    volumes={BBBD_MOUNT: bbbd_volume},
    secrets=[env_secret],
)
def run_experiment_shard(arg: dict[str, Any]) -> dict[str, Any]:
    """Ingest + preprocess + LSO for a single BBBD experiment."""
    import sys
    sys.path.insert(0, "/root/coherence-testbench/src")

    experiment = int(arg["experiment"])
    config = arg["config"]

    from coherence.config import load_kill_criterion
    from coherence.decoders import (
        CrossSubjectAdversarialDecoder,
        PerSubjectRiemannDecoder,
    )
    from coherence.evaluate import LeaveSubjectsOut
    from coherence.ingest.bbbd import BBBDLoader
    from coherence.preprocess import PreprocessConfig, epoch_to_arrays, preprocess_raw

    kc = load_kill_criterion(arg["kill_criterion_path"])
    _ = kc  # stamped into per-shard payload for cross-check on the driver

    pcfg = PreprocessConfig(
        highpass_hz=float(config["preprocess"]["highpass_hz"]),
        notch_hz=tuple(float(f) for f in config["preprocess"]["notch_hz"]),
        resample_hz=int(config["preprocess"]["resample_hz"]),
        notch_16hz_experiments=tuple(int(e) for e in config["preprocess"]["notch_16hz_experiments"]),
        epoch_seconds=float(config["preprocess"]["epoch_seconds"]),
        epoch_overlap=float(config["preprocess"]["epoch_overlap"]),
        reject_peak_to_peak_uv=float(config["preprocess"]["reject_peak_to_peak_uv"]),
    )

    loader = BBBDLoader(root=Path(BBBD_MOUNT), experiments=[experiment])
    subject_limit = config["data"].get("subject_limit")
    subject_ids = loader.subjects()
    if subject_limit:
        subject_ids = subject_ids[: int(subject_limit)]

    by_subject = {}
    for record in loader.records(subject_ids=subject_ids):
        raw = loader.load_signal(record)
        raw = preprocess_raw(raw, pcfg, experiment=record.experiment)
        X, y = epoch_to_arrays(raw, pcfg,
                               label_getter=lambda t0, t1: record.labels.get("attention_label"))
        if len(y) == 0:
            continue
        by_subject[record.subject_id] = (X, y)

    baseline = PerSubjectRiemannDecoder(n_folds=int(config["decoders"]["baseline"]["n_folds"]))
    per_subject_baccs = []
    for _, (X, y) in by_subject.items():
        stats = baseline.fit_predict_within_subject(X, y)
        if stats["balanced_accuracy"] == stats["balanced_accuracy"]:
            per_subject_baccs.append(stats["balanced_accuracy"])

    def factory():
        return CrossSubjectAdversarialDecoder(
            alignment=config["decoders"]["target"]["alignment"],
            adversary_weight=float(config["decoders"]["target"]["adversary_weight"]),
            ssl_pretrain=bool(config["decoders"]["target"]["ssl_pretrain"]),
            epochs=int(config["decoders"]["target"]["epochs"]),
            batch_size=int(config["decoders"]["target"]["batch_size"]),
            lr=float(config["decoders"]["target"]["lr"]),
        )

    lso = LeaveSubjectsOut(
        epoch_seconds=float(config["preprocess"]["epoch_seconds"]),
        n_lso_seeds=int(config["evaluate"]["n_lso_seeds"]),
        train_subject_sweep=tuple(int(n) for n in config["evaluate"]["train_subject_sweep"]),
    )
    fold_results = lso.run(by_subject, factory)
    return {
        "experiment": experiment,
        "n_subjects": len(by_subject),
        "per_subject_baccs": per_subject_baccs,
        "folds": [
            {
                "seed": r.seed,
                "n_train_subjects": r.n_train_subjects,
                "held_out_subjects": list(r.held_out_subjects),
                "balanced_accuracy": r.balanced_accuracy,
                "bits_per_second": r.bits_per_second,
                "n_test_epochs": r.n_test_epochs,
            }
            for r in fold_results
        ],
    }


@app.local_entrypoint()
def main(config: str = "coherence-testbench/config/phase0.yaml",
         out: str = "coherence-testbench/artifacts/phase0") -> None:
    """Driver: fan out per experiment, merge results, call the local report writer."""
    import yaml
    config_path = Path(config).resolve()
    cfg_dict = yaml.safe_load(config_path.read_text())
    kc_path = (config_path.parent / cfg_dict["kill_criterion"]).resolve()

    experiments = list(cfg_dict["data"]["experiments"])
    args_list = [
        {"experiment": e, "config": cfg_dict, "kill_criterion_path": str(kc_path)}
        for e in experiments
    ]

    shard_outputs = list(run_experiment_shard.map(args_list))
    out_dir = Path(out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "shard_outputs.json").write_text(
        json.dumps(shard_outputs, indent=2, default=list)
    )

    # Merge -> call the local report writer.
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    from coherence.config import load_kill_criterion  # noqa: PLC0415
    from coherence.evaluate import LSOFoldResult  # noqa: PLC0415
    from coherence.report import build_report  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    kc = load_kill_criterion(kc_path)
    fold_results: list[LSOFoldResult] = []
    all_per_subject = []
    for shard in shard_outputs:
        all_per_subject.extend(shard["per_subject_baccs"])
        for f in shard["folds"]:
            fold_results.append(LSOFoldResult(
                seed=f["seed"],
                n_train_subjects=f["n_train_subjects"],
                held_out_subjects=tuple(f["held_out_subjects"]),
                balanced_accuracy=f["balanced_accuracy"],
                bits_per_second=f["bits_per_second"],
                n_test_epochs=f["n_test_epochs"],
            ))
    baseline_bacc = float(np.mean(all_per_subject)) if all_per_subject else 0.5

    build_report(
        kc=kc,
        fold_results=fold_results,
        per_subject_baseline_bacc=baseline_bacc,
        confound_ablations={},
        out_dir=out_dir,
    )
    print(f"Wrote {out_dir / 'report.md'}")
