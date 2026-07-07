"""Windowed feature extraction for BBBD eyetrack signals.

Input shape: (n_channels=8, n_samples), 128 Hz, ordered per
``coherence.ingest.eyetrack.EYETRACK_CHANNELS``.

Output shape: (n_epochs, n_features), float32, plus (n_epochs,) int64 labels.

Feature set per 4-s epoch (kept small and interpretable so the decoder
doesn't have to learn a huge featurizer):

    Pupil (channel 0)
      * mean, std, min-max range, first-derivative RMS

    Gaze (channels 1-4: x, y, vdx, vdy in visual angle degrees + pixels)
      * mean radial dispersion of (vdx, vdy) around the epoch centroid
      * mean speed of gaze in visual-angle space  (||d(vdx,vdy)/dt||)
      * max speed of gaze
      * saccade rate: fraction of samples with speed > 30 deg/s

    Head (channels 5-7: x, y, z)
      * std of (x, y, z) each — postural drift proxy

Total = 4 pupil + 4 gaze + 3 head = 11 features per epoch.

NaN / non-finite handling: samples with NaN in ANY channel are removed
before feature extraction. Epochs with fewer than 50% of samples surviving
are dropped.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


FEATURE_NAMES: tuple[str, ...] = (
    "pupil_mean", "pupil_std", "pupil_range", "pupil_dRMS",
    "gaze_dispersion", "gaze_speed_mean", "gaze_speed_max", "gaze_saccade_rate",
    "head_x_std", "head_y_std", "head_z_std",
)


@dataclass(frozen=True)
class EyetrackFeatureConfig:
    sfreq_hz: int = 128
    epoch_seconds: float = 4.0
    epoch_overlap: float = 0.5
    saccade_speed_deg_s: float = 30.0  # standard velocity threshold


def _finite_mask(arr: np.ndarray) -> np.ndarray:
    return np.asarray(np.isfinite(arr).all(axis=0))


def epoch_to_features(
    signal: np.ndarray,
    cfg: EyetrackFeatureConfig,
    label_getter: Callable[[float, float], int | None],
) -> tuple[np.ndarray, np.ndarray]:
    """Slide fixed-length windows over the (8, n) signal and extract features.

    Returns ``(X, y)`` where X is (n_epochs, len(FEATURE_NAMES)) float32 and
    y is (n_epochs,) int64. Epochs that fail the finiteness check or return
    a None label are dropped.
    """
    sfreq = int(cfg.sfreq_hz)
    win = int(cfg.epoch_seconds * sfreq)
    step = max(1, int(win * (1 - cfg.epoch_overlap)))
    _, n_samp = signal.shape

    xs: list[np.ndarray] = []
    ys: list[int] = []
    dt = 1.0 / sfreq
    for start in range(0, n_samp - win + 1, step):
        stop = start + win
        seg = signal[:, start:stop]
        mask = _finite_mask(seg)
        if mask.sum() < 0.5 * win:
            continue
        seg = seg[:, mask]
        label = label_getter(start / sfreq, stop / sfreq)
        if label is None:
            continue
        feats = _features_from_epoch(seg, dt, cfg)
        if feats is None:
            continue
        xs.append(feats)
        ys.append(int(label))

    if not xs:
        return (np.zeros((0, len(FEATURE_NAMES)), dtype=np.float32),
                np.zeros((0,), dtype=np.int64))
    return np.stack(xs).astype(np.float32), np.asarray(ys, dtype=np.int64)


def _features_from_epoch(
    seg: np.ndarray, dt: float, cfg: EyetrackFeatureConfig
) -> np.ndarray | None:
    """Compute the 11 features from a (8, n_valid_samples) epoch."""
    # Channel indices (see EYETRACK_CHANNELS in coherence.ingest.eyetrack)
    pupil = seg[0]
    # gaze_x, gaze_y unused directly — visual-angle channels drive the
    # gaze features because they're calibrated to degrees.
    vdx = seg[3]
    vdy = seg[4]
    hx = seg[5]
    hy = seg[6]
    hz = seg[7]

    if pupil.size < 4:
        return None

    # Pupil
    pupil_mean = float(np.mean(pupil))
    pupil_std = float(np.std(pupil))
    pupil_range = float(np.ptp(pupil))
    dpupil = np.diff(pupil) / dt
    pupil_dRMS = float(np.sqrt(np.mean(dpupil ** 2)))

    # Gaze
    cx = float(np.mean(vdx))
    cy = float(np.mean(vdy))
    gaze_dispersion = float(np.mean(np.sqrt((vdx - cx) ** 2 + (vdy - cy) ** 2)))
    dvdx = np.diff(vdx) / dt
    dvdy = np.diff(vdy) / dt
    speed = np.sqrt(dvdx ** 2 + dvdy ** 2)
    gaze_speed_mean = float(np.mean(speed))
    gaze_speed_max = float(np.max(speed)) if speed.size else 0.0
    gaze_saccade_rate = float(
        np.mean(speed > cfg.saccade_speed_deg_s)
    ) if speed.size else 0.0

    # Head
    head_x_std = float(np.std(hx))
    head_y_std = float(np.std(hy))
    head_z_std = float(np.std(hz))

    out = np.array([
        pupil_mean, pupil_std, pupil_range, pupil_dRMS,
        gaze_dispersion, gaze_speed_mean, gaze_speed_max, gaze_saccade_rate,
        head_x_std, head_y_std, head_z_std,
    ], dtype=np.float32)
    if not np.isfinite(out).all():
        return None
    return out
