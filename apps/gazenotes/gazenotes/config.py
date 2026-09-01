"""Configuration loading for gazenotes.

Config lives at ``~/GazeNotes/config.toml``. Everything has a default, so a
missing file is not an error — ``gazenotes doctor`` reports it and
``gazenotes config --init`` writes one.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

DEFAULT_NOTES_DIR = "~/GazeNotes"
DEFAULT_SUPERWHISPER_DIR = "~/Documents/superwhisper/recordings"

DEFAULT_CONFIG_TOML = """\
# gazenotes configuration. Paths may use ~.
notes_dir = "~/GazeNotes"

# Superwhisper writes one folder per recording, each with a meta.json.
# VERIFY THIS PATH on your machine (Superwhisper > Settings > Advanced) and
# make sure transcript/recording retention is enabled.
superwhisper_dir = "~/Documents/superwhisper/recordings"

# Transcripts starting with this word are treated as commands, not notes.
command_prefix = "computer"

# Gaze crop: full screen width by this fraction of screen height.
crop_height_fraction = 0.35

# Keep the untouched full-screen PNG alongside every crop.
keep_full_screenshot = true

chrome_cdp_url = "http://localhost:9222"

# Gaze-driven scrolling. Off by default: it fights some reading styles.
dwell_scroll = false

# Ignore a gaze fixation weaker than this; the note still gets written, just
# with a full-screen capture instead of a crop.
min_gaze_confidence = 0.35

# Seconds of gaze history before the transcript start that count as "what the
# user was looking at when they began speaking".
gaze_lookback_seconds = 2.0

# OCR the gaze crop when the frontmost app is not Chrome, so PDFs and native
# apps get a "Looking at" line too. Local (Apple Vision), and it only reads a
# screenshot that was going to be saved anyway.
ocr_enabled = true

# Rolling in-memory screen buffer, so a note can capture what just scrolled
# off. OFF by default (0 seconds): this is the one part of gazenotes that
# records before you speak, so it is opt-in. Frames never touch disk unless a
# note fires, and the buffer is capped by both age and total size.
screen_buffer_seconds = 0.0
screen_buffer_interval = 2.0
screen_buffer_max_mb = 256.0

[dwell]
# Only used when dwell_scroll = true.
zone_fraction = 0.15       # top/bottom band of the screen that triggers
dwell_seconds = 0.4        # how long gaze must rest there
cooldown_seconds = 1.5     # quiet period after each scroll
scroll_amount = 400.0

[nightly]
backend = "none"   # none | local | api
model = ""
"""


@dataclass(frozen=True)
class DwellSettings:
    """Tuning for gaze-driven scrolling. Inert unless ``dwell_scroll`` is on."""

    zone_fraction: float = 0.15
    dwell_seconds: float = 0.4
    cooldown_seconds: float = 1.5
    scroll_amount: float = 400.0
    min_confidence: float = 0.5


@dataclass(frozen=True)
class NightlyConfig:
    """Nightly-pass settings. ``backend = "none"`` never touches the network."""

    backend: str = "none"
    model: str = ""
    endpoint: str = ""
    api_key_env: str = "GAZENOTES_API_KEY"


@dataclass(frozen=True)
class Config:
    """Resolved runtime configuration. Paths are expanded, not created."""

    notes_dir: Path = Path(DEFAULT_NOTES_DIR).expanduser()
    superwhisper_dir: Path = Path(DEFAULT_SUPERWHISPER_DIR).expanduser()
    command_prefix: str = "computer"
    crop_height_fraction: float = 0.35
    keep_full_screenshot: bool = True
    chrome_cdp_url: str = "http://localhost:9222"
    dwell_scroll: bool = False
    min_gaze_confidence: float = 0.35
    gaze_lookback_seconds: float = 2.0
    ocr_enabled: bool = True
    screen_buffer_seconds: float = 0.0
    """0 disables the pre-note screen buffer. It is the only thing here that
    records before the user speaks, so it stays opt-in."""
    screen_buffer_interval: float = 2.0
    screen_buffer_max_mb: float = 256.0
    dwell: DwellSettings = field(default_factory=DwellSettings)
    nightly: NightlyConfig = field(default_factory=NightlyConfig)

    @property
    def screen_buffer_enabled(self) -> bool:
        return self.screen_buffer_seconds > 0.0

    @property
    def captures_dir(self) -> Path:
        return self.notes_dir / "captures"

    @property
    def calibration_path(self) -> Path:
        return self.notes_dir / "calibration.json"

    @property
    def config_path(self) -> Path:
        return self.notes_dir / "config.toml"


def _coerce(name: str, value: Any, default: Any) -> Any:
    """Coerce a TOML value to the type of the dataclass default."""
    if isinstance(default, Path):
        return Path(str(value)).expanduser()
    if isinstance(default, bool):
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)
    if isinstance(default, float):
        return float(value)
    if isinstance(default, str):
        return str(value)
    raise TypeError(f"unsupported config field {name!r}")


SECTIONS: dict[str, type] = {"dwell": DwellSettings, "nightly": NightlyConfig}
"""TOML table name → the dataclass it populates."""


def _section_from_mapping(section: type, data: dict[str, Any]):
    """Build one nested settings dataclass, coercing to each field's type."""
    defaults = section()
    kwargs = {
        f.name: _coerce(f.name, data[f.name], getattr(defaults, f.name))
        for f in fields(section)
        if f.name in data
    }
    return section(**kwargs)


def config_from_mapping(data: dict[str, Any]) -> Config:
    """Build a :class:`Config` from a parsed TOML mapping, ignoring unknowns."""
    defaults = Config()
    kwargs: dict[str, Any] = {}
    for f in fields(Config):
        if f.name in SECTIONS:
            continue
        if f.name in data:
            kwargs[f.name] = _coerce(f.name, data[f.name], getattr(defaults, f.name))

    for name, section in SECTIONS.items():
        kwargs[name] = _section_from_mapping(section, data.get(name) or {})
    return Config(**kwargs)


def load_config(path: Path | str | None = None) -> Config:
    """Load config from ``path`` (default ``~/GazeNotes/config.toml``).

    A missing file yields defaults; a malformed file raises so the user finds
    out at start-up rather than silently losing a setting.
    """
    if path is None:
        path = Config().config_path
    path = Path(path).expanduser()
    if not path.is_file():
        return Config()
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    return config_from_mapping(data)


def write_default_config(path: Path | str) -> Path:
    """Write the annotated default config, refusing to clobber an existing one."""
    path = Path(path).expanduser()
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_CONFIG_TOML, encoding="utf-8")
    return path
