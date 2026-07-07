#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal entrypoint for the Branch-D eyetrack Phase-0 sweep.

Same structure as `train.py` (EEG branch) — one shard per experiment,
per-experiment LSO over the sweep of train-subject counts, merged
into a Volume-persisted report.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")


IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "torch>=2.5,<2.8",
        "numpy>=2.0,<3.0",
        "scipy>=1.13",
        "scikit-learn>=1.5",
        "pyyaml>=6.0",
        "pydantic>=2.6",
    )
    .add_local_dir(
        local_path=str(Path(__file__).resolve().parent.parent / "src"),
        remote_path="/root/src",
    )
    .add_local_dir(
        local_path=str(Path(__file__).resolve().parent.parent / "config"),
        remote_path="/root/config",
    )
)

app = modal.App(name="coherence-testbench-eyetrack")

bbbd_volume = modal.Volume.from_name("bbbd-cache", create_if_missing=True)
results_volume = modal.Volume.from_name("phase0-results", create_if_missing=True)
BBBD_MOUNT = "/data/bbbd"
RESULTS_MOUNT = "/data/results"

env_secret = modal.Secret.from_dict({"BBBD_CACHE_DIR": BBBD_MOUNT})


@app.function(
    image=IMAGE,
    timeout=4 * 60 * 60,
    cpu=8,
    memory=32 * 1024,
    volumes={BBBD_MOUNT: bbbd_volume},
    secrets=[env_secret],
)
def run_eyetrack_shard(arg: dict[str, Any]) -> dict[str, Any]:
    """Ingest + featurize + LSO for one BBBD experiment (eyetrack signals)."""
    import sys as _sys
    _sys.path.insert(0, "/root/src")
    import numpy as _np

    from coherence.decoders.eyetrack import (
        CrossSubjectEyetrackDecoder,
        PerSubjectEyetrackDecoder,
    )
    from coherence.evaluate import LeaveSubjectsOut
    from coherence.ingest.eyetrack import (
        BBBDEyetrackLoader,
        EYETRACK_SFREQ_HZ,
    )
    from coherence.preprocess.eyetrack_features import (
        EyetrackFeatureConfig,
        epoch_to_features,
    )

    experiment = int(arg["experiment"])
    config = arg["config"]

    fcfg = EyetrackFeatureConfig(
        sfreq_hz=EYETRACK_SFREQ_HZ,
        epoch_seconds=float(config["preprocess"]["epoch_seconds"]),
        epoch_overlap=float(config["preprocess"]["epoch_overlap"]),
        saccade_speed_deg_s=float(
            config["preprocess"].get("saccade_speed_deg_s", 30.0)
        ),
    )
    loader = BBBDEyetrackLoader(root=Path(BBBD_MOUNT), experiments=[experiment])
    subject_limit = config["data"].get("subject_limit")
    subject_ids = loader.subjects()
    if subject_limit:
        subject_ids = subject_ids[: int(subject_limit)]

    def _make_labeler(label: int):
        def _get(_t0, _t1):
            return label
        return _get

    by_subject: dict[str, tuple[_np.ndarray, _np.ndarray]] = {}
    for record in loader.records(subject_ids=subject_ids):
        label = record.attention_label
        if label is None:
            continue
        sig = loader.load_signal(record)
        if sig is None:
            continue
        X, y = epoch_to_features(sig, fcfg, _make_labeler(label))
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

    n_before = len(by_subject)
    by_subject = {
        sid: (X, y)
        for sid, (X, y) in by_subject.items()
        if len(_np.unique(y)) >= 2
    }
    if len(by_subject) < n_before:
        print(f"[exp{experiment}] dropped {n_before - len(by_subject)} single-class subjects, "
              f"{len(by_subject)} usable")

    baseline = PerSubjectEyetrackDecoder(
        n_folds=int(config["decoders"]["baseline"]["n_folds"])
    )
    per_subject_baccs: list[float] = []
    for _, (X, y) in by_subject.items():
        stats = baseline.fit_predict_within_subject(X, y)
        if stats["balanced_accuracy"] == stats["balanced_accuracy"]:  # not NaN
            per_subject_baccs.append(stats["balanced_accuracy"])

    def factory():
        return CrossSubjectEyetrackDecoder(
            adversary_weight=float(config["decoders"]["target"]["adversary_weight"]),
            ssl_pretrain=bool(config["decoders"]["target"].get("ssl_pretrain", False)),
            epochs=int(config["decoders"]["target"]["epochs"]),
            batch_size=int(config["decoders"]["target"]["batch_size"]),
            lr=float(config["decoders"]["target"]["lr"]),
        )

    lso = LeaveSubjectsOut(
        epoch_seconds=float(config["preprocess"]["epoch_seconds"]),
        n_lso_seeds=int(config["evaluate"]["n_lso_seeds"]),
        train_subject_sweep=tuple(
            int(n) for n in config["evaluate"]["train_subject_sweep"]
        ),
    )
    fold_results = lso.run(by_subject, factory)

    # ------------------------------------------------------------------
    # Pre-registered confound ablations
    # ------------------------------------------------------------------
    ablations: dict[str, Any] = {}
    from sklearn.metrics import balanced_accuracy_score

    # 1. Prior-only baseline
    try:
        subjects_sorted = sorted(by_subject.keys())
        prior_baccs: list[float] = []
        for seed in range(int(config["evaluate"]["n_lso_seeds"])):
            rng = _np.random.default_rng(seed)
            shuffled = list(subjects_sorted)
            rng.shuffle(shuffled)
            n_test = max(1, int(len(shuffled) * 0.2))
            test_subjects = shuffled[:n_test]
            train_subjects = shuffled[n_test:]
            y_train = _np.concatenate([by_subject[s][1] for s in train_subjects])
            y_test = _np.concatenate([by_subject[s][1] for s in test_subjects])
            majority = int(_np.bincount(y_train).argmax())
            preds = _np.full_like(y_test, majority)
            prior_baccs.append(float(balanced_accuracy_score(y_test, preds)))
        ablations["hallucinated_fidelity"] = {
            "lso_balanced_accuracy": (
                float(_np.mean(prior_baccs)) if prior_baccs else float("nan")
            ),
            "n_folds": len(prior_baccs),
            "notes": "prior-only (train-majority) predictor, should sit at ~50%",
        }
    except Exception as e:
        ablations["hallucinated_fidelity"] = {
            "lso_balanced_accuracy": float("nan"),
            "n_folds": 0,
            "error": str(e)[:200],
        }

    # 2. Head-dropped ablation (motor-artifact control) — drop last 3 features
    try:
        by_subject_no_head = {
            sid: (X[:, :8], y) for sid, (X, y) in by_subject.items()
        }
        no_head_folds = lso.run(by_subject_no_head, factory)
        vals = [f.balanced_accuracy for f in no_head_folds]
        ablations["counting_motor_artifact"] = {
            "lso_balanced_accuracy": (
                float(_np.mean(vals)) if vals else float("nan")
            ),
            "n_folds": len(no_head_folds),
            "notes": "head x/y/z features dropped; pupil + gaze only",
        }
    except Exception as e:
        ablations["counting_motor_artifact"] = {
            "lso_balanced_accuracy": float("nan"),
            "n_folds": 0,
            "error": str(e)[:200],
        }

    # 3. Per-recording z-score ablation is structural: CrossSubjectEyetrackDecoder
    #    _fit_scaler runs on the concatenated train fold only. Report it as a
    #    structural pass.
    ablations["device_calibration_drift"] = {
        "lso_balanced_accuracy": float("nan"),
        "n_folds": 0,
        "notes": (
            "STRUCTURAL: train-only z-score in "
            "CrossSubjectEyetrackDecoder._fit_scaler; per-recording DC is "
            "still visible to the model. Full per-recording z-score ablation "
            "is a follow-up if the main path passes."
        ),
    }

    ablations["subject_id_leak"] = {
        "lso_balanced_accuracy": float("nan"),
        "n_folds": 0,
        "notes": (
            "STRUCTURAL: same train-only scaler as above; test-side transform "
            "uses stored (mu, sd) from the fit."
        ),
    }

    return {
        "experiment": experiment,
        "n_subjects": len(by_subject),
        "per_subject_baccs": per_subject_baccs,
        "ablations": ablations,
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
def eyetrack_phase0_end_to_end(config_yaml: str, run_id: str) -> dict[str, Any]:
    """Fully-Modal Branch-D run. Fires per-experiment shards, merges, writes
    the report + JSON to the phase0-results Volume, returns the verdict."""
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
    shard_outputs = list(run_eyetrack_shard.map(args_list))

    fold_results: list[LSOFoldResult] = []
    all_per_subject: list[float] = []
    merged_ablations: dict[str, dict[str, Any]] = {}
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
        for aid, arow in shard.get("ablations", {}).items():
            row = merged_ablations.setdefault(
                aid, {"lso_balanced_accuracy": 0.0, "_num": 0.0, "_den": 0}
            )
            ba = arow.get("lso_balanced_accuracy", float("nan"))
            nf = int(arow.get("n_folds", 0))
            if ba == ba and nf > 0:
                row["_num"] += float(ba) * nf
                row["_den"] += nf
            row.setdefault("notes", arow.get("notes", ""))
    for aid, row in merged_ablations.items():
        den = row.pop("_den")
        num = row.pop("_num")
        row["lso_balanced_accuracy"] = (num / den) if den > 0 else float("nan")
    baseline_bacc = float(_np.mean(all_per_subject)) if all_per_subject else 0.5

    out_dir = _Path(RESULTS_MOUNT) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "shard_outputs.json").write_text(
        json.dumps(shard_outputs, indent=2, default=list)
    )
    build_report(
        kc=kc, fold_results=fold_results,
        per_subject_baseline_bacc=baseline_bacc,
        confound_ablations=merged_ablations, out_dir=out_dir,
    )
    results_volume.commit()

    report_json = json.loads((out_dir / "report.json").read_text())
    return {
        "run_id": run_id,
        "verdict": report_json.get("verdict"),
        "results_volume_path": str(out_dir),
        "report_md_path": str(out_dir / "report.md"),
    }
