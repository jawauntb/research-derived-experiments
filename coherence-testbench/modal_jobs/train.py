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
    # Ship the coherence package into the worker so the shard can import it.
    .add_local_dir(
        local_path=str(Path(__file__).resolve().parent.parent / "src"),
        remote_path="/root/src",
    )
    # Ship configs so kill_criterion.yaml is readable on the worker at a
    # stable path independent of the driver's local layout.
    .add_local_dir(
        local_path=str(Path(__file__).resolve().parent.parent / "config"),
        remote_path="/root/config",
    )
)

app = modal.App(name="coherence-testbench-phase0")

# Persistent volumes.
bbbd_volume = modal.Volume.from_name("bbbd-cache", create_if_missing=True)
results_volume = modal.Volume.from_name("phase0-results", create_if_missing=True)
BBBD_MOUNT = "/data/bbbd"
RESULTS_MOUNT = "/data/results"

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
    sys.path.insert(0, "/root/src")

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

    from coherence.ingest.bbbd import read_events_bounds  # noqa: PLC0415
    import numpy as _np  # noqa: PLC0415

    def _make_labeler(label: int, start_s: float, end_s: float):
        def _get(t0: float, t1: float) -> int | None:
            if t0 < start_s or t1 > end_s or t1 <= t0:
                return None
            return label
        return _get

    by_subject: dict[str, tuple[Any, Any]] = {}
    for record in loader.records(subject_ids=subject_ids):
        label = record.attention_label
        if label is None:
            continue
        bounds = read_events_bounds(record.events_path)
        if bounds is None:
            continue
        start_s, end_s = bounds

        raw = loader.load_signal(record)
        raw = preprocess_raw(raw, pcfg, experiment=record.experiment)
        X, y = epoch_to_arrays(raw, pcfg,
                               label_getter=_make_labeler(label, start_s, end_s))
        if len(y) == 0:
            continue

        prior = by_subject.get(record.subject_id)
        if prior is None:
            by_subject[record.subject_id] = (X, y)
        else:
            by_subject[record.subject_id] = (
                _np.concatenate([prior[0], X], axis=0),
                _np.concatenate([prior[1], y], axis=0),
            )

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


@app.function(
    image=IMAGE,
    timeout=8 * 60 * 60,
    cpu=2,
    memory=4 * 1024,
    volumes={BBBD_MOUNT: bbbd_volume, RESULTS_MOUNT: results_volume},
    secrets=[env_secret],
)
def phase0_end_to_end(config_yaml: str, run_id: str) -> dict[str, Any]:
    """Fully-Modal Phase-0 run. No local CPU needed.

    Reads the config from a YAML string (embedded from the driver), fans out
    per-experiment shards, merges outputs, writes the report + JSON + JSONL
    into ``phase0-results:/<run_id>/``, and returns the verdict + paths.

    Disconnect-safe: once submitted (e.g. via ``Function.spawn``), completes
    regardless of the CLI. Fetch results later via
    ``modal volume get phase0-results /<run_id>``.
    """
    import sys as _sys
    _sys.path.insert(0, "/root/src")
    import yaml as _yaml
    import numpy as _np
    from pathlib import Path as _Path

    from coherence.config import load_kill_criterion
    from coherence.evaluate import LSOFoldResult
    from coherence.report import build_report

    cfg = _yaml.safe_load(config_yaml)
    kc_name = _Path(cfg["kill_criterion"]).name
    kc_path = _Path("/root/config") / kc_name
    kc = load_kill_criterion(kc_path)

    experiments = list(cfg["data"]["experiments"])
    args_list = [
        {"experiment": e, "config": cfg, "kill_criterion_path": str(kc_path)}
        for e in experiments
    ]

    shard_outputs = list(run_experiment_shard.map(args_list))

    fold_results: list[LSOFoldResult] = []
    all_per_subject: list[float] = []
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
    baseline_bacc = float(_np.mean(all_per_subject)) if all_per_subject else 0.5

    out_dir = _Path(RESULTS_MOUNT) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "shard_outputs.json").write_text(
        json.dumps(shard_outputs, indent=2, default=list)
    )
    build_report(
        kc=kc, fold_results=fold_results,
        per_subject_baseline_bacc=baseline_bacc,
        confound_ablations={}, out_dir=out_dir,
    )
    results_volume.commit()

    report_json = json.loads((out_dir / "report.json").read_text())
    return {
        "run_id": run_id,
        "verdict": report_json.get("verdict"),
        "results_volume_path": str(out_dir),
        "report_md_path": str(out_dir / "report.md"),
    }


@app.local_entrypoint()
def main(config: str = "coherence-testbench/config/phase0.yaml",
         out: str = "coherence-testbench/artifacts/phase0") -> None:
    """Driver: fan out per experiment, merge results, call the local report writer."""
    import yaml
    config_path = Path(config).resolve()
    cfg_dict = yaml.safe_load(config_path.read_text())
    # kill_criterion in phase0.yaml is relative to the coherence-testbench root,
    # matching how coherence.config.load_phase0 resolves it.
    kc_raw = cfg_dict["kill_criterion"]
    if Path(kc_raw).is_absolute():
        kc_path = Path(kc_raw)
    else:
        kc_path = (config_path.parent.parent / kc_raw).resolve()

    experiments = list(cfg_dict["data"]["experiments"])
    # The worker reads the config from the Modal-mounted /root/config path,
    # not the driver's laptop-side kc_path. Local kc_path stays for the
    # report writer at the end (which runs on the driver).
    worker_kc_path = f"/root/config/{Path(kc_raw).name}"
    args_list = [
        {"experiment": e, "config": cfg_dict, "kill_criterion_path": worker_kc_path}
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
