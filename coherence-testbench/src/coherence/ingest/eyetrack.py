"""BBBD eyetrack ingest — Branch D of the coherence test-bench.

Each BBBD recording carries three sibling eyetrack .tsv.gz files under
``sub-XX/ses-YY/eyetrack/``:

    *_pupil_eyetrack.tsv.gz              1 col  (pupilSize),      128 Hz
    *_gaze_visualangle_eyetrack.tsv.gz   4 cols (x, y, vdx, vdy), 128 Hz
    *_head_eyetrack.tsv.gz               3 cols (x, y, z),        128 Hz

We stitch them into a single (n_channels=8, n_samples) matrix per recording
that mirrors the EEG shape the decoders expect. Session-level attention
label comes from the same protocol as the EEG side (see
docs/bbbd_label_protocol.md): exp 2/3/4 ses-01 = 1 (attentive), ses-02 = 0
(distracted); exp 1/5 → None.
"""

from __future__ import annotations

import gzip
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np

from .bbbd import EXPERIMENTS_WITH_ATTENTION_LABEL


# Eyetrack sample rate is fixed at 128 Hz across BBBD (verified from
# `_eyetrack.json` for exp4/sub-08).
EYETRACK_SFREQ_HZ: int = 128

# Ordered channel spec — the same channel order every recording produces.
# Consumers rely on this order for feature extraction and z-scoring.
EYETRACK_CHANNELS: tuple[str, ...] = (
    "pupilSize",           # from _pupil_eyetrack.tsv.gz
    "gaze_x",              # from _gaze_visualangle_eyetrack.tsv.gz (screen pixels)
    "gaze_y",
    "gaze_vdx",            # visual-angle x, degrees
    "gaze_vdy",
    "head_x",              # from _head_eyetrack.tsv.gz (pixels)
    "head_y",
    "head_z",              # millimeters
)


@dataclass(frozen=True)
class EyetrackRecord:
    subject_id: str
    experiment: int
    session: int
    pupil_path: Path
    gaze_path: Path
    head_path: Path
    labels: Mapping[str, float | int | str]

    @property
    def attention_label(self) -> int | None:
        if self.experiment not in EXPERIMENTS_WITH_ATTENTION_LABEL:
            return None
        if self.session == 1:
            return 1
        if self.session == 2:
            return 0
        return None


def _cache_root() -> Path:
    root = os.environ.get("BBBD_CACHE_DIR")
    if not root:
        raise RuntimeError("BBBD_CACHE_DIR is not set.")
    return Path(root).expanduser().resolve()


def _read_tsv_gz(path: Path) -> np.ndarray:
    """Return (n_samples, n_cols) float32 from a headerless .tsv.gz."""
    with gzip.open(path, "rt") as f:
        # BBBD eyetrack .tsv.gz files have a header row per `_eyetrack.json`.
        first = f.readline().strip().split("\t")
        try:
            # If the header is actually numeric, treat it as the first row.
            _ = [float(x) for x in first]
            rows = [[float(x) for x in first]]
        except ValueError:
            rows = []
        for line in f:
            cells = line.strip().split("\t")
            if not cells or cells == [""]:
                continue
            try:
                rows.append([float(x) for x in cells])
            except ValueError:
                # 'NaN' string entries or partial lines — skip.
                continue
    if not rows:
        return np.zeros((0, 0), dtype=np.float32)
    return np.asarray(rows, dtype=np.float32)


class BBBDEyetrackLoader:
    """Enumerates BBBD eyetrack recordings across experiments.

    Iteration is lazy; nothing is loaded until ``load_signal`` is called
    on a record. Mirrors the shape of BBBDLoader (EEG side).
    """

    def __init__(self, root: Path | None = None,
                 experiments: list[int] | None = None):
        self.root = root or _cache_root()
        self.experiments = experiments or list(EXPERIMENTS_WITH_ATTENTION_LABEL)
        self._participants = self._read_participants()

    def _experiment_root(self, exp: int) -> Path:
        return self.root / f"experiment{exp}"

    def _read_participants(self) -> dict[str, dict[str, str]]:
        rows: dict[str, dict[str, str]] = {}
        for exp in self.experiments:
            tsv = self._experiment_root(exp) / "participants.tsv"
            if not tsv.exists():
                continue
            header, *lines = tsv.read_text().splitlines()
            keys = header.split("\t")
            for line in lines:
                cells = line.split("\t")
                row = dict(zip(keys, cells))
                rows[row.get("participant_id", "")] = row
        return rows

    def subjects(self) -> list[str]:
        ids: set[str] = set()
        for exp in self.experiments:
            exp_root = self._experiment_root(exp)
            if not exp_root.is_dir():
                continue
            for p in exp_root.glob("sub-*"):
                if p.is_dir():
                    ids.add(p.name)
        return sorted(ids)

    def records(self, subject_ids: list[str] | None = None) -> Iterator[EyetrackRecord]:
        wanted = set(subject_ids) if subject_ids else None
        for exp in self.experiments:
            exp_root = self._experiment_root(exp)
            if not exp_root.is_dir():
                continue
            for sub_dir in sorted(exp_root.glob("sub-*")):
                if not sub_dir.is_dir():
                    continue
                if wanted is not None and sub_dir.name not in wanted:
                    continue
                # Each session has one or more (task-stim0N) triplets;
                # yield one EyetrackRecord per (subject, session, stim).
                for pupil in sub_dir.rglob("*_pupil_eyetrack.tsv.gz"):
                    session = _parse_session(pupil)
                    if session is None:
                        continue
                    gaze = pupil.with_name(
                        pupil.name.replace("_pupil_", "_gaze_visualangle_")
                    )
                    head = pupil.with_name(
                        pupil.name.replace("_pupil_", "_head_")
                    )
                    if not (gaze.exists() and head.exists()):
                        continue
                    yield EyetrackRecord(
                        subject_id=sub_dir.name,
                        experiment=exp,
                        session=session,
                        pupil_path=pupil,
                        gaze_path=gaze,
                        head_path=head,
                        labels=self._participants.get(sub_dir.name, {}),
                    )

    def load_signal(self, record: EyetrackRecord) -> np.ndarray | None:
        """Return an (n_channels=8, n_samples) float32 matrix or None.

        None is returned if any of the three files can't be read or if
        the three signals disagree on length (rare, but the sample-count
        alignment matters for windowed features).
        """
        pupil = _read_tsv_gz(record.pupil_path)
        gaze = _read_tsv_gz(record.gaze_path)
        head = _read_tsv_gz(record.head_path)
        if pupil.size == 0 or gaze.size == 0 or head.size == 0:
            return None
        # Align to the shortest — the three signals share a clock but
        # sometimes lose one or two samples at the ends.
        n = min(pupil.shape[0], gaze.shape[0], head.shape[0])
        if n < EYETRACK_SFREQ_HZ * 4:  # need at least 4 s to form one epoch
            return None
        pupil = pupil[:n]
        gaze = gaze[:n]
        head = head[:n]
        # Assemble in the fixed EYETRACK_CHANNELS order.
        stacked = np.column_stack([
            pupil[:, 0],
            gaze[:, 0], gaze[:, 1], gaze[:, 2], gaze[:, 3],
            head[:, 0], head[:, 1], head[:, 2],
        ]).T.astype(np.float32)  # -> (8, n)
        return stacked


def _parse_session(bdf_or_tsv: Path) -> int | None:
    for part in bdf_or_tsv.parts:
        if part.startswith("ses-"):
            try:
                return int(part[len("ses-"):])
            except ValueError:
                return None
    return None
