#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal entrypoint for Branch-D quiz-score regression.

Predicts per-recording quiz score from eyetrack features. Cross-subject
LSO with Spearman rank correlation as the metric. Pre-registration:
`config/kill_criterion_eyetrack_quiz.yaml`.
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

app = modal.App(name="coherence-testbench-eyetrack-quiz")

bbbd_volume = modal.Volume.from_name("bbbd-cache", create_if_missing=True)
results_volume = modal.Volume.from_name("phase0-results", create_if_missing=True)
BBBD_MOUNT = "/data/bbbd"
RESULTS_MOUNT = "/data/results"

env_secret = modal.Secret.from_dict({"BBBD_CACHE_DIR": BBBD_MOUNT})


@app.function(
    image=IMAGE,
    timeout=4 * 60 * 60,
    cpu=4,
    memory=16 * 1024,
    volumes={BBBD_MOUNT: bbbd_volume},
    secrets=[env_secret],
)
def run_quiz_shard(arg: dict[str, Any]) -> dict[str, Any]:
    """Ingest + featurize + LSO regression for one BBBD experiment."""
    import sys as _sys
    _sys.path.insert(0, "/root/src")
    import numpy as _np

    from coherence.decoders.eyetrack_regression import (
        CrossSubjectEyetrackRegressor,
        aggregate_epochs,
        lso_regression,
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
    target_session = int(config["data"].get("target_session", 1))

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
    subject_ids = loader.subjects()
    subject_limit = config["data"].get("subject_limit")
    if subject_limit:
        subject_ids = subject_ids[: int(subject_limit)]

    # Build a per-recording (X_vec, quiz_score) mapping keyed by subject.
    # Attentive-session records ARE labeled. Distracted-session records
    # for the same (subject, stimulus) are captured separately for the
    # reporting-only "distracted-predicts-attentive" analysis.
    by_subject_attn: dict[str, list[tuple[_np.ndarray, float]]] = {}
    by_subject_dist: dict[str, list[tuple[_np.ndarray, float]]] = {}
    n_records_seen = 0
    for record in loader.records(subject_ids=subject_ids):
        stim = _parse_stimulus(record.pupil_path)
        if stim is None:
            continue
        key = (record.subject_id, experiment, stim)
        score = quiz_scores.get(key)
        if score is None:
            continue
        sig = loader.load_signal(record)
        if sig is None:
            continue

        # Everything gets labeled with the attentive-condition score for
        # this (subject, stimulus). session=1 lands in attn bucket;
        # session=2 lands in dist bucket for the secondary analysis.
        X, _ = epoch_to_features(sig, fcfg, lambda _t0, _t1: 1)
        if len(X) == 0:
            continue
        vec = aggregate_epochs(X)
        if vec.size == 0 or not _np.isfinite(vec).all():
            continue
        entry = (vec, float(score))
        n_records_seen += 1
        if record.session == target_session:
            by_subject_attn.setdefault(record.subject_id, []).append(entry)
        elif record.session == 2:
            by_subject_dist.setdefault(record.subject_id, []).append(entry)

    def _pack(mapping: dict[str, list[tuple[_np.ndarray, float]]]
              ) -> dict[str, tuple[_np.ndarray, _np.ndarray]]:
        out: dict[str, tuple[_np.ndarray, _np.ndarray]] = {}
        for sid, items in mapping.items():
            if not items:
                continue
            X = _np.stack([v for v, _ in items]).astype(_np.float32)
            y = _np.asarray([s for _, s in items], dtype=_np.float32)
            if len(_np.unique(y)) < 2:
                continue
            out[sid] = (X, y)
        return out

    by_subject_attn_packed = _pack(by_subject_attn)
    by_subject_dist_packed = _pack(by_subject_dist)

    def factory():
        return CrossSubjectEyetrackRegressor(
            ssl_pretrain=bool(config["decoders"]["target"].get("ssl_pretrain", False)),
            epochs=int(config["decoders"]["target"]["epochs"]),
            batch_size=int(config["decoders"]["target"]["batch_size"]),
            lr=float(config["decoders"]["target"]["lr"]),
        )

    fold_results = lso_regression(
        by_subject=by_subject_attn_packed,
        factory=factory,
        n_seeds=int(config["evaluate"]["n_lso_seeds"]),
        train_subject_sweep=tuple(int(n) for n in config["evaluate"]["train_subject_sweep"]),
    )

    # ------------------------------------------------------------------
    # Ablations
    # ------------------------------------------------------------------
    ablations: dict[str, Any] = {}

    # Prior-only regressor: predict the train-set mean quiz score.
    try:
        subjects_sorted = sorted(by_subject_attn_packed.keys())
        prior_rhos: list[float] = []
        for seed in range(int(config["evaluate"]["n_lso_seeds"])):
            rng = _np.random.default_rng(seed)
            shuffled = list(subjects_sorted)
            rng.shuffle(shuffled)
            n_test = max(1, int(len(shuffled) * 0.2))
            test_subjects = shuffled[:n_test]
            train_subjects = shuffled[n_test:]
            y_train = _np.concatenate(
                [by_subject_attn_packed[s][1] for s in train_subjects]
            )
            y_test = _np.concatenate(
                [by_subject_attn_packed[s][1] for s in test_subjects]
            )
            mean_pred = float(_np.mean(y_train))
            preds = _np.full_like(y_test, mean_pred)
            prior_rhos.append(float(spearman_r(y_test, preds)))
        ablations["hallucinated_fidelity"] = {
            "lso_spearman_r": float(_np.mean(prior_rhos)) if prior_rhos else float("nan"),
            "n_folds": len(prior_rhos),
            "notes": "prior-only (train-mean) regressor; should be ~0",
        }
    except Exception as e:
        ablations["hallucinated_fidelity"] = {
            "lso_spearman_r": float("nan"),
            "n_folds": 0,
            "error": str(e)[:200],
        }

    # Secondary (reporting-only): distracted-predicts-attentive-score.
    secondary: dict[str, Any] = {}
    try:
        if by_subject_dist_packed:
            secondary_folds = lso_regression(
                by_subject=by_subject_dist_packed,
                factory=factory,
                n_seeds=int(config["evaluate"]["n_lso_seeds"]),
                train_subject_sweep=tuple(
                    int(n) for n in config["evaluate"]["train_subject_sweep"]
                ),
            )
            secondary["distracted_predicts_attentive_score"] = {
                "folds": secondary_folds,
                "n_subjects": len(by_subject_dist_packed),
                "notes": (
                    "regressor trained on distracted-session eyetrack, targets "
                    "attentive-session quiz score (same subject, same stimulus)"
                ),
            }
        else:
            secondary["distracted_predicts_attentive_score"] = {
                "folds": [], "notes": "no distracted-session recordings found"
            }
    except Exception as e:
        secondary["distracted_predicts_attentive_score"] = {
            "folds": [], "error": str(e)[:200]
        }

    # Subject-ID leak is structural: _fit_scaler(train_only).
    ablations["subject_id_leak"] = {
        "lso_spearman_r": float("nan"),
        "n_folds": 0,
        "notes": (
            "STRUCTURAL: train-only z-score in "
            "CrossSubjectEyetrackRegressor._fit_scaler; test-side transform "
            "uses stored (mu, sd) from fit."
        ),
    }

    return {
        "experiment": experiment,
        "n_subjects_attn": len(by_subject_attn_packed),
        "n_subjects_dist": len(by_subject_dist_packed),
        "n_records_seen": n_records_seen,
        "folds": fold_results,
        "ablations": ablations,
        "secondary": secondary,
    }


@app.function(
    image=IMAGE,
    timeout=8 * 60 * 60,
    cpu=2,
    memory=4 * 1024,
    volumes={BBBD_MOUNT: bbbd_volume, RESULTS_MOUNT: results_volume},
    secrets=[env_secret],
)
def eyetrack_quiz_end_to_end(config_yaml: str, run_id: str) -> dict[str, Any]:
    """Fan out shards, merge, write regression report to phase0-results."""
    import sys as _sys
    _sys.path.insert(0, "/root/src")
    import yaml as _yaml
    import numpy as _np
    from pathlib import Path as _Path

    cfg = _yaml.safe_load(config_yaml)
    kc_name = _Path(cfg["kill_criterion"]).name
    kc_path = _Path("/root/config") / kc_name
    kc_dict = _yaml.safe_load(kc_path.read_text())

    experiments = list(cfg["data"]["experiments"])
    args_list = [
        {"experiment": e, "config": cfg}
        for e in experiments
    ]
    shard_outputs = list(run_quiz_shard.map(args_list))

    # Merge fold Spearman ρ across shards (per (seed, n_train)).
    all_folds: list[dict[str, Any]] = []
    all_prior_rhos: list[float] = []
    n_subj_attn = 0
    for shard in shard_outputs:
        all_folds.extend(shard.get("folds", []))
        n_subj_attn += int(shard.get("n_subjects_attn", 0))
        ha = shard.get("ablations", {}).get("hallucinated_fidelity", {})
        if ha.get("lso_spearman_r", None) is not None and ha["lso_spearman_r"] == ha["lso_spearman_r"]:
            all_prior_rhos.append(float(ha["lso_spearman_r"]))

    # Aggregate curve
    by_n: dict[int, list[float]] = {}
    for f in all_folds:
        by_n.setdefault(int(f["n_train_subjects"]), []).append(float(f["spearman_r"]))
    curve = [
        {"n_train_subjects": n, "mean_spearman_r": float(_np.mean(rs)),
         "n_folds": len(rs)}
        for n, rs in sorted(by_n.items())
    ]
    largest_n = max(by_n.keys()) if by_n else 0
    top_rhos = by_n.get(largest_n, [])
    lso_rho = float(_np.mean(top_rhos)) if top_rhos else 0.0
    prior_rho = float(_np.mean(all_prior_rhos)) if all_prior_rhos else 0.0
    per_seed_ok = all(r >= float(kc_dict["thresholds"]["go"]["stability"]["seed_min_rho"])
                      for r in top_rhos) and len(top_rhos) >= int(
                          kc_dict["thresholds"]["go"]["stability"]["n_seeds"])

    go_min = float(kc_dict["thresholds"]["go"]["lso_spearman_r_min"])
    kill_max = float(kc_dict["thresholds"]["kill"]["lso_spearman_r_max"])
    if lso_rho >= go_min and per_seed_ok:
        verdict = "GO"
    elif lso_rho <= kill_max:
        verdict = "KILL"
    else:
        verdict = "INCONCLUSIVE"

    # Build a markdown report inline (report writer is for classification only).
    out_dir = _Path(RESULTS_MOUNT) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "shard_outputs.json").write_text(
        json.dumps(shard_outputs, indent=2, default=list)
    )

    lines = [
        "# Branch-D quiz-score regression report",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        f"- kill-criterion version: `{kc_dict['version']}`",
        f"- run subjects (attentive-session labeled): {n_subj_attn}",
        f"- primary target: {kc_dict['primary_task']['name']}",
        "",
        "## 1. Pre-registered thresholds",
        "",
        f"- GO: LSO Spearman ρ ≥ {go_min:.2f}, every seed ρ ≥ "
        f"{kc_dict['thresholds']['go']['stability']['seed_min_rho']:.2f} "
        f"across {kc_dict['thresholds']['go']['stability']['n_seeds']} seeds",
        f"- KILL: LSO Spearman ρ ≤ {kill_max:.2f}",
        "",
        "## 2. LSO Spearman-ρ curve",
        "",
        "| n_train_subjects | mean ρ | n folds |",
        "|---:|---:|---:|",
    ]
    for row in curve:
        lines.append(
            f"| {row['n_train_subjects']} | {row['mean_spearman_r']:+.3f} | {row['n_folds']} |"
        )
    lines += [
        "",
        "## 3. Per-seed stability at max n_train",
        "",
        f"- n_train_subjects = {largest_n}",
        f"- ρ per seed: {['%+.3f' % r for r in top_rhos]}",
        f"- floor pass? {per_seed_ok}",
        "",
        "## 4. Confound ablations",
        "",
        f"- **hallucinated_fidelity (prior-only train-mean regressor):** "
        f"ρ = {prior_rho:+.3f} (must be ≤ 0.05)",
        "- **subject_id_leak:** STRUCTURAL — train-only z-score fit",
        "",
        "## 5. Secondary (reporting-only): distracted → attentive-quiz-score",
        "",
    ]
    sec_folds: list[float] = []
    for shard in shard_outputs:
        for f in (
            shard.get("secondary", {})
            .get("distracted_predicts_attentive_score", {})
            .get("folds", [])
        ):
            sec_folds.append(float(f["spearman_r"]))
    if sec_folds:
        lines.append(
            f"- mean Spearman ρ (across all folds): {float(_np.mean(sec_folds)):+.3f} "
            f"({len(sec_folds)} folds)"
        )
    else:
        lines.append("- no distracted-session data reached the regressor")
    lines += [
        "",
        "## 6. Verdict",
        "",
        f"**{verdict}**",
        "",
    ]
    (out_dir / "report.md").write_text("\n".join(lines))
    (out_dir / "report.json").write_text(json.dumps({
        "verdict": verdict,
        "kill_criterion_version": kc_dict["version"],
        "lso_spearman_r_at_max_n": lso_rho,
        "prior_only_spearman_r": prior_rho,
        "per_seed_ok": per_seed_ok,
        "curve": curve,
    }, indent=2))
    results_volume.commit()

    return {
        "run_id": run_id,
        "verdict": verdict,
        "results_volume_path": str(out_dir),
        "report_md_path": str(out_dir / "report.md"),
    }
