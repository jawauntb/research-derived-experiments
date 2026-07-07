"""BBBD (Big Brain-Behavior Dataset) ingest — Zenodo record 19241964.

The full corpus is 26.97 GB, packaged as one zip per experiment:
    experiment1.zip  0.89 GB   eyetrack-only (no EEG)
    experiment2.zip  5.60 GB
    experiment3.zip  7.97 GB
    experiment4.zip  5.47 GB
    experiment5.zip  7.04 GB

Unpacked layout (after ``modal_jobs/prepare_bbbd.py`` extracts them into
``$BBBD_CACHE_DIR``):

    <root>/experiment<N>/sub-<ID>/ses-<S>/eeg/sub-<ID>_ses-<S>_task-stim<K>_eeg.bdf
    <root>/experiment<N>/participants.tsv
    <root>/experiment<N>/README.md

The BIDS task naming is ``task-stim0K`` (K=1..5, stimulus block), NOT
``task-exp<N>``. Experiment identity lives in the parent directory.

We expose one function per Phase-0 need: enumerate subjects, load a
(signal, labels) pair, and stream all records for the LSO loop.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

ZENODO_RECORD = "19241964"
ZENODO_URL = f"https://zenodo.org/records/{ZENODO_RECORD}"

# One archive per experiment on Zenodo.
EXPERIMENT_ARCHIVES: Mapping[int, str] = {
    1: "experiment1.zip",
    2: "experiment2.zip",
    3: "experiment3.zip",
    4: "experiment4.zip",
    5: "experiment5.zip",
}
# Experiment 1 is eyetrack-only (no EEG); skip it in EEG decoders.
EXPERIMENTS_WITH_EEG: tuple[int, ...] = (2, 3, 4, 5)

# Experiments that expose a session-level attentive-vs-distracted contrast
# (ses-01 = attentive, ses-02 = distracted / counting-back). Experiment 5
# is intentionally excluded — its ses-02 is a monetary-incentive intervention,
# not a distraction manipulation, so both sessions are attentive.
# See docs/bbbd_label_protocol.md for the reasoning.
EXPERIMENTS_WITH_ATTENTION_LABEL: tuple[int, ...] = (2, 3, 4)


def _parse_session(bdf_path: Path) -> int | None:
    """Extract the BIDS session number from a .bdf path.

    BBBD paths follow ``.../sub-XX/ses-YY/eeg/sub-XX_ses-YY_task-….bdf``.
    Returns the integer session number or None if the path doesn't match.
    """
    for part in bdf_path.parts:
        if part.startswith("ses-"):
            try:
                return int(part[len("ses-"):])
            except ValueError:
                return None
    return None


def read_events_bounds(events_tsv: Path) -> tuple[float, float] | None:
    """Return (start_onset, end_onset) in seconds from a BBBD events.tsv.

    BBBD events.tsv files only carry start/end markers — no per-trial rows.
    Returns None if the file is missing, malformed, or lacks either marker.
    """
    if not events_tsv.exists():
        return None
    lines = events_tsv.read_text().splitlines()
    if len(lines) < 3:
        return None
    header = lines[0].split("\t")
    try:
        i_onset = header.index("onset")
        i_event = header.index("event")
    except ValueError:
        return None
    start: float | None = None
    end: float | None = None
    for row in lines[1:]:
        cells = row.split("\t")
        if len(cells) <= max(i_onset, i_event):
            continue
        tag = cells[i_event].strip().lower()
        try:
            onset = float(cells[i_onset])
        except ValueError:
            continue
        if tag == "start":
            start = onset
        elif tag == "end":
            end = onset
    if start is None or end is None or end <= start:
        return None
    return (start, end)


def _cache_root() -> Path:
    root = os.environ.get("BBBD_CACHE_DIR")
    if not root:
        raise RuntimeError(
            "BBBD_CACHE_DIR is not set. Point it at a directory outside the repo "
            "(the dataset is large). Example: "
            "export BBBD_CACHE_DIR=$HOME/data/bbbd"
        )
    return Path(root).expanduser().resolve()


@dataclass(frozen=True)
class SubjectRecord:
    subject_id: str
    experiment: int          # 1..5
    session: int             # 1 or 2 (BIDS `ses-01` / `ses-02`)
    signal_path: Path        # .bdf
    events_path: Path        # BIDS events tsv (start/end markers only in BBBD)
    labels: Mapping[str, float | int | str]

    @property
    def attention_label(self) -> int | None:
        """Session-level binary label per BBBD's protocol.

        Returns 1 (attentive), 0 (distracted), or None (no valid contrast for
        this experiment). Exp 2/3/4: ses-01 attentive, ses-02 distracted.
        Exp 1/5: None. See docs/bbbd_label_protocol.md.
        """
        if self.experiment not in EXPERIMENTS_WITH_ATTENTION_LABEL:
            return None
        if self.session == 1:
            return 1
        if self.session == 2:
            return 0
        return None


class BBBDLoader:
    """Enumerates BBBD subjects across the 5 experiments.

    Each experiment lives under its own directory: ``<root>/experiment<N>/``.
    Iteration is lazy; nothing is loaded into memory until ``load_signal`` is
    called on a record. This keeps the LSO loop memory-flat.
    """

    def __init__(self, root: Path | None = None, experiments: list[int] | None = None):
        self.root = root or _cache_root()
        # Default to EEG-carrying experiments; a caller can still ask for exp1
        # explicitly (for eyetrack-only work), but decoder code should stick
        # with EXPERIMENTS_WITH_EEG.
        self.experiments = experiments or list(EXPERIMENTS_WITH_EEG)
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
                # Same subject can appear across experiments; last write wins
                # for the participant-wide labels (demographics, ASRS).
                rows[row.get("participant_id", "")] = row
        return rows

    def subjects(self) -> list[str]:
        """Union of all subjects across the enabled experiments."""
        ids: set[str] = set()
        for exp in self.experiments:
            exp_root = self._experiment_root(exp)
            if not exp_root.is_dir():
                continue
            for p in exp_root.glob("sub-*"):
                if p.is_dir():
                    ids.add(p.name)
        return sorted(ids)

    def records(self, subject_ids: list[str] | None = None) -> Iterator[SubjectRecord]:
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
                for bdf in sub_dir.rglob("*_eeg.bdf"):
                    events = bdf.with_name(bdf.name.replace("_eeg.bdf", "_events.tsv"))
                    session = _parse_session(bdf)
                    if session is None:
                        continue
                    yield SubjectRecord(
                        subject_id=sub_dir.name,
                        experiment=exp,
                        session=session,
                        signal_path=bdf,
                        events_path=events,
                        labels=self._participants.get(sub_dir.name, {}),
                    )

    def load_signal(self, record: SubjectRecord):
        """Return an mne.io.Raw for the recording. Imported lazily so the
        loader itself is importable even in environments where MNE is not yet
        installed (e.g. Modal image build)."""
        import mne  # noqa: PLC0415

        raw = mne.io.read_raw_bdf(str(record.signal_path), preload=False, verbose="ERROR")
        return raw


def load_subject(record: SubjectRecord):
    """Compat one-shot: return the mne.Raw for a record."""
    root = record.signal_path
    # Walk up until we hit `experiment<N>`, then one more parent for the cache root.
    while root.parent != root and not root.name.startswith("experiment"):
        root = root.parent
    return BBBDLoader(root=root.parent).load_signal(record)


def zenodo_download_url(experiment: int) -> str:
    """Direct-download URL for one experiment archive on Zenodo."""
    return f"https://zenodo.org/api/records/{ZENODO_RECORD}/files/{EXPERIMENT_ARCHIVES[experiment]}/content"


def download_bbbd(dest: Path | None = None) -> Path:
    """Fetch BBBD from Zenodo if not already present.

    Deliberately not implemented as a full downloader — the record is 26.97 GB
    and the operator should decide bandwidth + storage. See
    ``modal_jobs/prepare_bbbd.py`` for the Modal-side version that runs
    server-side against the ``bbbd-cache`` Volume.
    """
    root = dest or _cache_root()
    root.mkdir(parents=True, exist_ok=True)
    marker = root / ".bbbd_downloaded"
    if marker.exists():
        return root

    raise RuntimeError(
        "BBBD is not present at "
        f"{root}. The full record is 26.97 GB across 5 experiment archives; "
        "use `modal_jobs/prepare_bbbd.py` to download + unzip server-side "
        f"into the bbbd-cache Volume. Zenodo record: {ZENODO_URL}."
    )
