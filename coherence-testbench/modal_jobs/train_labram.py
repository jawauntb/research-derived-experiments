#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal entrypoint for the LaBraM EEG rescue attempt.

Foundation-model encoder swap for phase0.v1's KILLED bench. LaBraM-Base
(5.8M params, ICLR 2024, MIT license) is loaded from HF, frozen, and
used to extract 200-D epoch embeddings from BBBD recordings at 200 Hz.
A small MLP head is trained cross-subject with LSO. Same task, same
metrics, same thresholds as phase0.v1 — but different decoder.

Pre-registration: `config/kill_criterion_eeg_labram.yaml`
(`phase0.eeg.labram.v1`).
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
        "numpy>=2.0,<3.0",
        "scipy>=1.13",
        "scikit-learn>=1.5",
        "mne>=1.8",
        "pyEDFlib>=0.1.36",
        "braindecode>=0.9",
        "huggingface_hub>=0.24",
        "einops>=0.7",
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

app = modal.App(name="coherence-testbench-labram")

bbbd_volume = modal.Volume.from_name("bbbd-cache", create_if_missing=True)
results_volume = modal.Volume.from_name("phase0-results", create_if_missing=True)
hf_volume = modal.Volume.from_name("huggingface-cache", create_if_missing=True)

BBBD_MOUNT = "/data/bbbd"
RESULTS_MOUNT = "/data/results"
HF_MOUNT = "/root/.cache/huggingface"

env_secret = modal.Secret.from_dict({
    "BBBD_CACHE_DIR": BBBD_MOUNT,
    "HF_HOME": HF_MOUNT,
})


@app.function(
    image=IMAGE,
    timeout=4 * 60 * 60,
    gpu="T4",
    cpu=4,
    memory=16 * 1024,
    volumes={
        BBBD_MOUNT: bbbd_volume,
        HF_MOUNT: hf_volume,
    },
    secrets=[env_secret],
)
def run_labram_shard(arg: dict[str, Any]) -> dict[str, Any]:
    """Preprocess + LaBraM-encode + LSO for one BBBD experiment."""
    import sys as _sys
    _sys.path.insert(0, "/root/src")
    import numpy as _np
    import torch

    from coherence.ingest.bbbd import BBBDLoader, read_events_bounds

    experiment = int(arg["experiment"])
    config = arg["config"]
    dst_sfreq = int(config["preprocess"]["target_sfreq_hz"])
    hp = float(config["preprocess"]["highpass_hz"])
    lp = float(config["preprocess"]["lowpass_hz"])
    notches = tuple(float(f) for f in config["preprocess"]["notch_hz"])
    epoch_s = float(config["preprocess"]["epoch_seconds"])
    amp_scale = float(config["preprocess"]["amplitude_scale"])

    win = int(epoch_s * dst_sfreq)   # 800 samples

    # Load LaBraM-Base once per worker.
    from braindecode.models import Labram
    encoder = Labram.from_pretrained(config["decoders"]["encoder"]["hf_repo"])
    encoder = encoder.eval().cuda()
    for p in encoder.parameters():
        p.requires_grad = False

    loader = BBBDLoader(root=Path(BBBD_MOUNT), experiments=[experiment])
    subject_limit = config["data"].get("subject_limit")
    subject_ids = loader.subjects()
    if subject_limit:
        subject_ids = subject_ids[: int(subject_limit)]

    def _make_labeler(label, start_s, end_s):
        def _get(t0, t1):
            if t0 < start_s or t1 > end_s or t1 <= t0:
                return None
            return label
        return _get

    # Preprocess + embed each recording, aggregating by subject.
    by_subject: dict[str, tuple[_np.ndarray, _np.ndarray]] = {}
    for record in loader.records(subject_ids=subject_ids):
        label = record.attention_label
        if label is None:
            continue
        bounds = read_events_bounds(record.events_path)
        if bounds is None:
            continue
        start_s, end_s = bounds

        raw = loader.load_signal(record)
        raw.load_data()
        raw.filter(l_freq=hp, h_freq=lp, verbose="ERROR")
        for f in notches:
            raw.notch_filter(freqs=f, verbose="ERROR")
        # BBBD is 128 Hz. Resample to 200.
        if int(raw.info["sfreq"]) != dst_sfreq:
            raw.resample(sfreq=dst_sfreq, verbose="ERROR")

        # LaBraM channel-order: pass ch_names in the standard 10-20 order the
        # model was trained on. Use whatever BBBD's EEG channels look like;
        # LaBraM's channel-aware embedding will handle the mapping (unmatched
        # names get an "unknown" embedding).
        data = raw.get_data(picks="eeg") * amp_scale  # (n_ch, n_samp)
        n_samp = data.shape[-1]
        # Slice into non-overlapping 4-s epochs.
        n_ep = n_samp // win
        if n_ep == 0:
            continue
        eps = _np.stack([data[:, i * win:(i + 1) * win] for i in range(n_ep)])  # (E, C, T)

        # Time-window validity: reject epochs whose (t0, t1) exits the events window.
        starts = _np.arange(n_ep) * epoch_s
        valid = _np.array([_make_labeler(label, start_s, end_s)(s, s + epoch_s) is not None
                           for s in starts])
        if not valid.any():
            continue
        eps = eps[valid]

        # Encode in batches on GPU.
        embs = []
        batch = 32
        with torch.no_grad():
            for i in range(0, len(eps), batch):
                x = torch.from_numpy(eps[i:i + batch]).float().cuda()
                out = encoder(x, return_features=True)
                cls = out["cls_token"]  # (B, 200)
                embs.append(cls.detach().cpu().numpy())
        E = _np.concatenate(embs, axis=0)  # (N_epochs, 200)
        y = _np.full(len(E), label, dtype=_np.int64)

        prior = by_subject.get(record.subject_id)
        if prior is None:
            by_subject[record.subject_id] = (E, y)
        else:
            by_subject[record.subject_id] = (
                _np.concatenate([prior[0], E], axis=0),
                _np.concatenate([prior[1], y], axis=0),
            )

    # Drop single-class subjects.
    n_before = len(by_subject)
    by_subject = {sid: (X, y) for sid, (X, y) in by_subject.items()
                  if len(_np.unique(y)) >= 2}
    print(f"[exp{experiment}] {n_before - len(by_subject)} single-class dropped, "
          f"{len(by_subject)} usable")

    # Per-subject baseline (LR on LaBraM embeddings, within-subject k-fold).
    per_subject_baccs: list[float] = []
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import balanced_accuracy_score
    from sklearn.model_selection import StratifiedKFold
    from sklearn.preprocessing import StandardScaler

    for _, (X, y) in by_subject.items():
        try:
            uniq, cnts = _np.unique(y, return_counts=True)
            if len(uniq) < 2 or cnts.min() < 5 or len(y) < 10:
                continue
            skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
            baccs = []
            for tr, te in skf.split(X, y):
                sc = StandardScaler().fit(X[tr])
                lr = LogisticRegression(max_iter=1000)
                lr.fit(sc.transform(X[tr]), y[tr])
                baccs.append(float(balanced_accuracy_score(
                    y[te], lr.predict(sc.transform(X[te]))
                )))
            if baccs:
                per_subject_baccs.append(float(_np.mean(baccs)))
        except Exception:
            continue

    # Cross-subject MLP head.
    from coherence.evaluate import LeaveSubjectsOut
    from coherence.decoders.eyetrack import CrossSubjectEyetrackDecoder

    def factory():
        return CrossSubjectEyetrackDecoder(
            adversary_weight=0.0,     # no adversary; frozen encoder handles subj-invariance
            ssl_pretrain=False,
            epochs=int(config["decoders"]["head"]["epochs"]),
            batch_size=int(config["decoders"]["head"]["batch_size"]),
            lr=float(config["decoders"]["head"]["lr"]),
        )

    lso = LeaveSubjectsOut(
        epoch_seconds=epoch_s,
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
    volumes={BBBD_MOUNT: bbbd_volume, RESULTS_MOUNT: results_volume, HF_MOUNT: hf_volume},
    secrets=[env_secret],
)
def labram_phase0_end_to_end(config_yaml: str, run_id: str) -> dict[str, Any]:
    """Fully-Modal orchestrator: fan out shards, merge, write report."""
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
    args_list = [{"experiment": e, "config": cfg} for e in experiments]
    shard_outputs = list(run_labram_shard.map(args_list))

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
