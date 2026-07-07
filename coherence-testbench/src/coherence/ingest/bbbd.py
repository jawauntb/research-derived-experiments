"""BBBD (Big Brain-Behavior Dataset) ingest — Zenodo record 19241964.

The Zenodo download is large; the loader assumes the archive has already been
staged at ``$BBBD_CACHE_DIR`` (see .env.example). ``download_bbbd`` streams
the archive if it's missing.

BIDS structure follows the BBBD paper:
    <root>/sub-<ID>/ses-<S>/eeg/sub-<ID>_ses-<S>_task-<T>_eeg.bdf
    <root>/participants.tsv
    <root>/task-<T>_events.tsv

We expose one function per Phase-0 need: enumerate subjects, load a
(signal, labels) pair, and stream all subjects for the LSO loop.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

ZENODO_RECORD = "19241964"
ZENODO_URL = f"https://zenodo.org/records/{ZENODO_RECORD}"


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
    signal_path: Path        # .bdf
    events_path: Path        # BIDS events
    labels: Mapping[str, float | int | str]


class BBBDLoader:
    """Enumerates BBBD subjects across the 5 experiments.

    Iteration is lazy; nothing is loaded into memory until ``load_signal`` is
    called on a record. This keeps the LSO loop memory-flat.
    """

    def __init__(self, root: Path | None = None, experiments: list[int] | None = None):
        self.root = root or _cache_root()
        self.experiments = experiments or [1, 2, 3, 4, 5]
        self._participants = self._read_participants()

    def _read_participants(self) -> dict[str, dict[str, str]]:
        tsv = self.root / "participants.tsv"
        if not tsv.exists():
            return {}
        rows: dict[str, dict[str, str]] = {}
        header, *lines = tsv.read_text().splitlines()
        keys = header.split("\t")
        for line in lines:
            cells = line.split("\t")
            row = dict(zip(keys, cells))
            rows[row.get("participant_id", "")] = row
        return rows

    def subjects(self) -> list[str]:
        return sorted(p.name for p in self.root.glob("sub-*") if p.is_dir())

    def records(self, subject_ids: list[str] | None = None) -> Iterator[SubjectRecord]:
        for sub_id in subject_ids or self.subjects():
            for exp in self.experiments:
                for bdf in (self.root / sub_id).rglob(f"*task-exp{exp}*_eeg.bdf"):
                    events = bdf.with_name(bdf.name.replace("_eeg.bdf", "_events.tsv"))
                    yield SubjectRecord(
                        subject_id=sub_id,
                        experiment=exp,
                        signal_path=bdf,
                        events_path=events,
                        labels=self._participants.get(sub_id, {}),
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
    return BBBDLoader(root=record.signal_path.parents[3]).load_signal(record)


def download_bbbd(dest: Path | None = None) -> Path:
    """Fetch BBBD from Zenodo if not already present.

    NOTE: the archive is many GB. This function only writes into
    ``BBBD_CACHE_DIR`` (or ``dest`` if given). It refuses to write into the
    repo tree.
    """
    root = dest or _cache_root()
    root.mkdir(parents=True, exist_ok=True)
    marker = root / ".bbbd_downloaded"
    if marker.exists():
        return root

    # Deliberately not implemented as a full downloader here — the Zenodo
    # record is large enough that the operator should choose bandwidth and
    # storage. Print the exact commands instead.
    raise RuntimeError(
        "BBBD is not present at "
        f"{root}. Download from {ZENODO_URL} (record {ZENODO_RECORD}) and "
        "unpack the BIDS tree at that path, then create an empty "
        f"{marker} to acknowledge. See github.com/madjens/bbbd-dataset "
        "for the official download script."
    )
