"""Preprocess pipeline for BBBD, following the dataset methods.

Non-negotiables from `config/kill_criterion.yaml`:
- 0.05 Hz highpass, 60 Hz notch, resample to 128 Hz.
- Notch the 16 Hz electrical artifact in Exp 4-5 so no decoder cheats on it.
- All train-only stats are fit on the train split, never on test folds — the
  cross-subject-decoder side guarantees this at fold time; here we just make
  the transforms per-recording so leakage isn't structurally possible.

The output is (X, y, meta) tensors ready for the decoder heads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class PreprocessConfig:
    highpass_hz: float = 0.05
    notch_hz: tuple[float, ...] = (60.0,)
    resample_hz: int = 128
    notch_16hz_experiments: tuple[int, ...] = (4, 5)
    epoch_seconds: float = 4.0
    epoch_overlap: float = 0.5
    reject_peak_to_peak_uv: float = 150.0


def preprocess_raw(raw: Any, cfg: PreprocessConfig, experiment: int) -> Any:
    """Apply the fixed preprocess chain to an mne.Raw.

    Returns the modified Raw (mutated + preloaded). Kept as ``Any`` in the
    signature so this module remains importable without MNE at import time.
    """
    raw.load_data()
    raw.filter(l_freq=cfg.highpass_hz, h_freq=None, verbose="ERROR")
    for f in cfg.notch_hz:
        raw.notch_filter(freqs=f, verbose="ERROR")
    if experiment in cfg.notch_16hz_experiments:
        raw.notch_filter(freqs=16.0, verbose="ERROR")
    if raw.info["sfreq"] != cfg.resample_hz:
        raw.resample(sfreq=cfg.resample_hz, verbose="ERROR")
    return raw


def epoch_to_arrays(
    raw: Any,
    cfg: PreprocessConfig,
    label_getter,
) -> tuple[np.ndarray, np.ndarray]:
    """Slide fixed-length epochs across the recording and label each.

    ``label_getter`` maps (start_sec, stop_sec) -> int label (0/1 for the
    binary attentive-vs-distracted primary task). Epochs whose peak-to-peak
    amplitude exceeds the reject threshold are dropped.

    Returns:
        X: (n_epochs, n_channels, n_samples) float32
        y: (n_epochs,) int64
    """
    sfreq = int(raw.info["sfreq"])
    win = int(cfg.epoch_seconds * sfreq)
    step = max(1, int(win * (1 - cfg.epoch_overlap)))
    data = raw.get_data(picks="eeg")  # (n_ch, n_samp), Volts
    n_ch, n_samp = data.shape

    xs: list[np.ndarray] = []
    ys: list[int] = []
    reject_v = cfg.reject_peak_to_peak_uv * 1e-6
    for start in range(0, n_samp - win + 1, step):
        stop = start + win
        seg = data[:, start:stop]
        if np.ptp(seg, axis=1).max() > reject_v:
            continue
        label = label_getter(start / sfreq, stop / sfreq)
        if label is None:
            continue
        xs.append(seg.astype(np.float32))
        ys.append(int(label))

    if not xs:
        return (np.zeros((0, n_ch, win), dtype=np.float32),
                np.zeros((0,), dtype=np.int64))
    return np.stack(xs), np.asarray(ys, dtype=np.int64)
