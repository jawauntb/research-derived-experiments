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

[nightly]
backend = "none"   # none | local | api
model = ""
"""


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
    nightly: NightlyConfig = field(default_factory=NightlyConfig)

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


def config_from_mapping(data: dict[str, Any]) -> Config:
    """Build a :class:`Config` from a parsed TOML mapping, ignoring unknowns."""
    defaults = Config()
    kwargs: dict[str, Any] = {}
    for f in fields(Config):
        if f.name == "nightly":
            continue
        if f.name in data:
            kwargs[f.name] = _coerce(f.name, data[f.name], getattr(defaults, f.name))

    nightly_data = data.get("nightly") or {}
    nightly_defaults = NightlyConfig()
    nightly_kwargs = {
        f.name: str(nightly_data[f.name])
        for f in fields(NightlyConfig)
        if f.name in nightly_data
    }
    kwargs["nightly"] = NightlyConfig(**{**vars(nightly_defaults), **nightly_kwargs})
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
