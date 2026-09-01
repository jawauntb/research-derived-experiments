"""The data that moves between components. All plain, all serialisable."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

__all__ = ["NoteEvent", "GazeSample", "Fixation", "AppContext", "BrowserContext", "Capture"]


@dataclass(frozen=True)
class NoteEvent:
    """One thing the user said, as recovered from Superwhisper's output."""

    transcript: str
    t_start: float
    """Monotonic-comparable epoch seconds when speech began (estimated)."""
    t_end: float
    """Epoch seconds when the recording finished."""
    timestamp: datetime
    """Wall-clock time of ``t_end``, used for filenames and headings."""
    source_dir: Path | None = None
    audio_path: Path | None = None


@dataclass(frozen=True)
class GazeSample:
    """One webcam frame's gaze estimate, in quartz logical screen points."""

    t: float
    x: float
    y: float
    confidence: float


@dataclass(frozen=True)
class Fixation:
    """Where the user was dominantly looking over a time window."""

    x: float
    y: float
    confidence: float
    sample_count: int
    display_id: int = 0
    method: str = "webcam"


@dataclass(frozen=True)
class AppContext:
    """The frontmost application and window at capture time."""

    name: str
    bundle_id: str = ""
    window_title: str = ""
    window_bounds: tuple[float, float, float, float] | None = None

    @property
    def is_chrome(self) -> bool:
        return self.bundle_id == "com.google.Chrome" or "chrome" in self.name.lower()


@dataclass(frozen=True)
class BrowserContext:
    """What the DOM says was under the gaze point."""

    url: str
    title: str
    text: str
    selector: str = ""
    scroll_y: float = 0.0
    fragment_url: str = ""
    bbox: tuple[float, float, float, float] | None = None


@dataclass
class Capture:
    """Everything gathered for one note, before it is written down."""

    event: NoteEvent
    app: AppContext | None = None
    fixation: Fixation | None = None
    browser: BrowserContext | None = None
    screenshot: Path | None = None
    screenshot_full: Path | None = None
    crop: tuple[float, float, float, float] | None = None
    extra: dict[str, Any] = field(default_factory=dict)
