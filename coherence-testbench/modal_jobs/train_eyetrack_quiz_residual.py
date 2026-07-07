#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Residualized quiz-score regression.

Same task as `train_eyetrack_quiz.py` but the regression target is the
**residual** of quiz score after regressing out demographic predictors
(Age, Sex from `participants.tsv`). Concretely:

    1. On each train fold, fit a Ridge model:  quiz_score = f(demographics)
    2. Compute residuals for BOTH train and test:  r = quiz - f(demographics)
    3. Train the eyetrack MLP to predict r from eyetrack features.
    4. Spearman ρ between predicted-r and true-r on held-out subjects
       is the "eyetrack signal above demographics" metric.

This is a proper Frisch-Waugh-Lovell control for the demographic
confound identified during the 02:35 verification of the original
quiz-score GO. It answers a distinct question from the pre-registered
gate — it does NOT re-litigate the retracted GO, it clarifies how much
of the observed signal is eyetrack-specific vs demographic.

Reports Spearman ρ on residuals + a comparison to the raw-quiz
Spearman ρ using the same folds.
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

app = modal.App(name="coherence-testbench-eyetrack-quiz-residual")

bbbd_volume = modal.Volume.from_name("bbbd-cache", create_if_missing=True)
results_volume = modal.Volume.from_name("phase0-results", create_if_missing=True)
BBBD_MOUNT = "/data/bbbd"
RESULTS_MOUNT = "/data/results"

env_secret = modal.Secret.from_dict({"BBBD_CACHE_DIR": BBBD_MOUNT})


def _parse_num(x) -> float:
    try:
        return float(x)
    except Exception:
        import math
        return math.nan


def _parse_sex(x) -> float:
    return {"male": 0.0, "female": 1.0}.get(str(x).strip().lower(), float("nan"))


def _read_participants_demographics(root, exp: int) -> dict[str, tuple[float, float]]:
    """Return {subject_id: (age, sex)} for the experiment. NaN if missing."""
    import csv
    tsv = root / f"experiment{exp}" / "participants.tsv"
    out: dict[str, tuple[float, float]] = {}
    if not tsv.exists():
        return out
    with open(tsv) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            sid = row.get("participant_id", "")
            age = _parse_num(row.get("Age", ""))
            sex = _parse_sex(row.get("Sex", ""))
            out[sid] = (age, sex)
    return out


@app.function(
    image=IMAGE,
    timeout=4 * 60 * 60,
    cpu=4,
    memory=16 * 1024,
    volumes={BBBD_MOUNT: bbbd_volume},
    secrets=[env_secret],
)
def run_residual_shard(arg: dict[str, Any]) -> dict[str, Any]:
    """Ingest + featurize + LSO residualized regression for one experiment."""
    import sys as _sys
    _sys.path.insert(0, "/root/src")
    import numpy as _np

    from coherence.decoders.eyetrack_regression import (
        CrossSubjectEyetrackRegressor,
        aggregate_epochs,
        spearman_r,
    )
    from coherence.ingest.eyetrack import (
        BBBDEyetrackLoader,
        EYETRACK_SFREQ_HZ,
        _parse_stimulus,
        read_quiz_scores,
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
    root = Path(BBBD_MOUNT)
    loader = BBBDEyetrackLoader(root=root, experiments=[experiment])
    quiz_scores = read_quiz_scores(root, [experiment])
    demographics = _read_participants_demographics(root, experiment)
    subject_ids = loader.subjects()
    subject_limit = config["data"].get("subject_limit")
    if subject_limit:
        subject_ids = subject_ids[: int(subject_limit)]

    # Collect per-recording (X, y, subject, demographic_vector).
    # We only use attentive-session recordings (session=1) as targets.
    records: list[dict[str, Any]] = []
    for record in loader.records(subject_ids=subject_ids):
        if record.session != 1:
            continue
        stim = _parse_stimulus(record.pupil_path)
        if stim is None:
            continue
        key = (record.subject_id, experiment, stim)
        score = quiz_scores.get(key)
        if score is None:
            continue
        demo = demographics.get(record.subject_id)
        if demo is None:
            continue
        age, sex = demo
        if _np.isnan(age) or _np.isnan(sex):
            continue
        sig = loader.load_signal(record)
        if sig is None:
            continue
        X, _ = epoch_to_features(sig, fcfg, lambda _t0, _t1: 1)
        if len(X) == 0:
            continue
        vec = aggregate_epochs(X)
        if vec.size == 0 or not _np.isfinite(vec).all():
            continue
        records.append({
            "subject": record.subject_id,
            "stim": stim,
            "features": vec,
            "quiz": float(score),
            "age": float(age),
            "sex": float(sex),
        })

    if not records:
        return {"experiment": experiment, "n_subjects": 0, "folds": []}

    subjects = sorted({r["subject"] for r in records})
    n_features = int(records[0]["features"].shape[0])
    print(f"[exp{experiment}] {len(records)} records, {len(subjects)} subjects, "
          f"feature_dim={n_features}")

    def _stack(subs: list[str]):
        rs = [r for r in records if r["subject"] in subs]
        if not rs:
            return None
        X = _np.stack([r["features"] for r in rs]).astype(_np.float32)
        D = _np.stack([[r["age"], r["sex"]] for r in rs]).astype(_np.float32)
        y = _np.asarray([r["quiz"] for r in rs], dtype=_np.float32)
        subj = _np.asarray([r["subject"] for r in rs])
        return X, D, y, subj

    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler

    fold_results: list[dict[str, Any]] = []
    for seed in range(int(config["evaluate"]["n_lso_seeds"])):
        rng = _np.random.default_rng(seed)
        shuffled = list(subjects)
        rng.shuffle(shuffled)
        n_test = max(1, int(len(shuffled) * 0.2))
        test_subs = shuffled[:n_test]
        train_pool = shuffled[n_test:]
        for n_train in config["evaluate"]["train_subject_sweep"]:
            if int(n_train) > len(train_pool):
                continue
            train_subs = train_pool[: int(n_train)]
            tr = _stack(train_subs)
            te = _stack(list(test_subs))
            if tr is None or te is None:
                continue
            X_tr, D_tr, y_tr, _ = tr
            X_te, D_te, y_te, _ = te
            if len(y_tr) < 4 or len(y_te) < 4:
                continue

            # 1. Fit demographic-only predictor on train.
            demo_scaler = StandardScaler().fit(D_tr)
            demo_reg = Ridge(alpha=1.0)
            demo_reg.fit(demo_scaler.transform(D_tr), y_tr)
            demo_pred_tr = demo_reg.predict(demo_scaler.transform(D_tr))
            demo_pred_te = demo_reg.predict(demo_scaler.transform(D_te))

            # 2. Residuals.
            r_tr = y_tr - demo_pred_tr
            r_te = y_te - demo_pred_te

            # 3. Train eyetrack MLP to predict residual.
            dec = CrossSubjectEyetrackRegressor(
                ssl_pretrain=bool(config["decoders"]["target"].get("ssl_pretrain", False)),
                epochs=int(config["decoders"]["target"]["epochs"]),
                batch_size=int(config["decoders"]["target"]["batch_size"]),
                lr=float(config["decoders"]["target"]["lr"]),
                seed=seed,
            )
            dec.fit(X_tr, r_tr)
            preds_r = dec.predict(X_te)

            # 4. Metrics.
            rho_residual = spearman_r(r_te, preds_r)
            rho_raw_demo = spearman_r(y_te, demo_pred_te)
            # For a fair "eyetrack raw ρ on same folds" comparison, also run
            # the eyetrack MLP on the raw quiz target with the same seed.
            dec2 = CrossSubjectEyetrackRegressor(
                epochs=int(config["decoders"]["target"]["epochs"]),
                batch_size=int(config["decoders"]["target"]["batch_size"]),
                lr=float(config["decoders"]["target"]["lr"]),
                seed=seed,
            )
            dec2.fit(X_tr, y_tr)
            preds_raw = dec2.predict(X_te)
            rho_eyetrack_raw = spearman_r(y_te, preds_raw)

            fold_results.append({
                "seed": int(seed),
                "n_train_subjects": int(n_train),
                "held_out_subjects": list(test_subs),
                "spearman_r_residual": float(rho_residual),
                "spearman_r_demographic_only": float(rho_raw_demo),
                "spearman_r_eyetrack_raw": float(rho_eyetrack_raw),
                "n_test_records": int(len(y_te)),
            })

    return {
        "experiment": experiment,
        "n_subjects": len(subjects),
        "n_records": len(records),
        "folds": fold_results,
    }


@app.function(
    image=IMAGE,
    timeout=8 * 60 * 60,
    cpu=2,
    memory=4 * 1024,
    volumes={BBBD_MOUNT: bbbd_volume, RESULTS_MOUNT: results_volume},
    secrets=[env_secret],
)
def residual_end_to_end(config_yaml: str, run_id: str) -> dict[str, Any]:
    """Fan out shards, merge, write report."""
    import sys as _sys
    _sys.path.insert(0, "/root/src")
    import yaml as _yaml
    import numpy as _np
    from pathlib import Path as _Path

    cfg = _yaml.safe_load(config_yaml)
    experiments = list(cfg["data"]["experiments"])
    args_list = [{"experiment": e, "config": cfg} for e in experiments]
    shard_outputs = list(run_residual_shard.map(args_list))

    all_folds: list[dict[str, Any]] = []
    for shard in shard_outputs:
        all_folds.extend(shard.get("folds", []))

    def curve(metric: str) -> list[dict[str, Any]]:
        by_n: dict[int, list[float]] = {}
        for f in all_folds:
            by_n.setdefault(int(f["n_train_subjects"]), []).append(float(f[metric]))
        return [
            {"n_train_subjects": n, f"mean_{metric}": float(_np.mean(rs)),
             "n_folds": len(rs)}
            for n, rs in sorted(by_n.items())
        ]

    curve_residual = curve("spearman_r_residual")
    curve_demo = curve("spearman_r_demographic_only")
    curve_raw = curve("spearman_r_eyetrack_raw")

    out_dir = _Path(RESULTS_MOUNT) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "shard_outputs.json").write_text(
        json.dumps(shard_outputs, indent=2, default=list)
    )

    lines = [
        "# Residualized quiz-score regression report",
        "",
        "Frisch-Waugh-Lovell control for the demographic confound found",
        "during the 02:35 verification of the original quiz-score GO. Target",
        "is quiz-score minus demographic-predicted quiz-score (train-fold-",
        "only demo fit). ρ_residual measures the eyetrack signal above",
        "and beyond demographics.",
        "",
        "## LSO Spearman-ρ curves",
        "",
        "| n_train | ρ_eyetrack_raw | ρ_demographic_only | ρ_residual (eyetrack-above-demo) |",
        "|---:|---:|---:|---:|",
    ]
    by_n_all = {}
    for c in curve_residual:
        by_n_all[c["n_train_subjects"]] = {"res": c["mean_spearman_r_residual"], "n": c["n_folds"]}
    for c in curve_demo:
        by_n_all.setdefault(c["n_train_subjects"], {})["demo"] = c["mean_spearman_r_demographic_only"]
    for c in curve_raw:
        by_n_all.setdefault(c["n_train_subjects"], {})["raw"] = c["mean_spearman_r_eyetrack_raw"]
    for n in sorted(by_n_all.keys()):
        row = by_n_all[n]
        lines.append(
            f"| {n} | {row.get('raw', float('nan')):+.3f} | "
            f"{row.get('demo', float('nan')):+.3f} | "
            f"{row.get('res', float('nan')):+.3f} |"
        )

    # Per-experiment breakdown
    lines += ["", "## Per-experiment ρ_residual", ""]
    lines += ["| exp | subjects | records | mean ρ_residual (all folds) |",
              "|---:|---:|---:|---:|"]
    for shard in shard_outputs:
        exp = shard["experiment"]
        n_subj = shard.get("n_subjects", 0)
        n_rec = shard.get("n_records", 0)
        rhos = [f["spearman_r_residual"] for f in shard.get("folds", [])]
        mean = float(_np.mean(rhos)) if rhos else float("nan")
        lines.append(f"| {exp} | {n_subj} | {n_rec} | {mean:+.3f} |")

    # Verdict
    top_n = max(by_n_all.keys()) if by_n_all else 0
    top_row = by_n_all.get(top_n, {})
    if top_row:
        residual_at_top = top_row.get("res", float("nan"))
    else:
        residual_at_top = float("nan")
    lines += [
        "",
        "## Interpretation",
        "",
        f"- eyetrack raw ρ at n={top_n}: {top_row.get('raw', float('nan')):+.3f}",
        f"- demographic-only ρ at n={top_n}: {top_row.get('demo', float('nan')):+.3f}",
        f"- residual ρ (eyetrack above demo) at n={top_n}: **{residual_at_top:+.3f}**",
        "",
        "This is NOT a pre-registered gate; it's a confound-controlled",
        "supplement to the retracted quiz-score GO. The residual ρ is",
        "what should be quoted in any narrative claiming 'eyetrack captures",
        "cognitive signal beyond static demographics'.",
    ]
    (out_dir / "report.md").write_text("\n".join(lines))
    (out_dir / "report.json").write_text(json.dumps({
        "residual_at_max_n": residual_at_top,
        "curves": {
            "residual": curve_residual,
            "demographic_only": curve_demo,
            "eyetrack_raw": curve_raw,
        },
    }, indent=2))
    results_volume.commit()

    return {
        "run_id": run_id,
        "residual_at_max_n": residual_at_top,
        "results_volume_path": str(out_dir),
        "report_md_path": str(out_dir / "report.md"),
    }
