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
from .eyetrack import (
    BBBDEyetrackLoader,
    EyetrackRecord,
    read_quiz_scores,
)

__all__ = [
    "BBBDLoader",
    "BBBDEyetrackLoader",
    "EXPERIMENTS_WITH_ATTENTION_LABEL",
    "EXPERIMENTS_WITH_EEG",
    "EyetrackRecord",
    "SubjectRecord",
    "download_bbbd",
    "load_subject",
    "read_events_bounds",
    "read_quiz_scores",
]
