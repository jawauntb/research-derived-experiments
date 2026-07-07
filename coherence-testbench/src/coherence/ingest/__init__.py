"""BBBD ingestion and BIDS loading."""

from .bbbd import (
    BBBDLoader,
    EXPERIMENTS_WITH_ATTENTION_LABEL,
    EXPERIMENTS_WITH_EEG,
    SubjectRecord,
    download_bbbd,
    load_subject,
    read_events_bounds,
)

__all__ = [
    "BBBDLoader",
    "EXPERIMENTS_WITH_ATTENTION_LABEL",
    "EXPERIMENTS_WITH_EEG",
    "SubjectRecord",
    "download_bbbd",
    "load_subject",
    "read_events_bounds",
]
