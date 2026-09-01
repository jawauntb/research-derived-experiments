"""Watch Superwhisper's recordings folder and turn new transcripts into events.

Superwhisper writes one timestamped folder per recording containing a
``meta.json`` and the audio. The schema has shifted across versions, so
:func:`parse_meta` accepts the keys seen in the wild rather than one exact
shape — and the folder itself is configurable, because the default location
moves too.

Watchdog is used when it is installed (lower latency); otherwise the watcher
polls. Both paths share the same stability check and parsing, so behaviour does
not depend on which one is active.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable, Iterable, Iterator
from datetime import datetime
from pathlib import Path

from .events import NoteEvent

log = logging.getLogger(__name__)

__all__ = ["parse_meta", "file_is_stable", "iter_meta_files", "SuperwhisperWatcher"]

_TEXT_KEYS = ("result", "text", "transcript", "llmResult", "processedResult")
_DURATION_KEYS = ("duration", "durationSeconds", "audioDuration", "length")
_AUDIO_NAMES = ("input.wav", "audio.wav", "recording.wav", "input.m4a", "audio.m4a")
_DEFAULT_SPEECH_SECONDS = 5.0


def _first_key(data: dict, keys: Iterable[str]) -> object | None:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def _parse_timestamp(data: dict) -> datetime | None:
    """Read Superwhisper's own timestamp: ISO string or epoch (s or ms)."""
    raw = _first_key(data, ("datetime", "date", "timestamp", "createdAt"))
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        seconds = float(raw)
        if seconds > 1e11:  # milliseconds
            seconds /= 1000.0
        return datetime.fromtimestamp(seconds).astimezone()
    text = str(raw).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed.astimezone() if parsed.tzinfo else parsed.astimezone()


def _duration_seconds(data: dict) -> float | None:
    raw = _first_key(data, _DURATION_KEYS)
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value > 600:  # milliseconds; nobody dictates a ten-minute note
        value /= 1000.0
    return value if value > 0 else None


def _find_audio(folder: Path) -> Path | None:
    for name in _AUDIO_NAMES:
        candidate = folder / name
        if candidate.exists():
            return candidate
    for candidate in sorted(folder.glob("*")):
        if candidate.suffix.lower() in {".wav", ".m4a", ".mp3", ".flac"}:
            return candidate
    return None


def parse_meta(path: Path | str, *, now: float | None = None) -> NoteEvent | None:
    """Parse one ``meta.json`` into a :class:`NoteEvent`.

    Returns ``None`` for a recording with no usable transcript — an empty
    result, a cancelled dictation — rather than writing an empty note.
    ``t_start`` comes from the audio duration when Superwhisper reports one, so
    the gaze window covers the whole utterance; otherwise it falls back to a
    five-second guess.
    """
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("unreadable meta %s: %s", path, exc)
        return None
    if not isinstance(data, dict):
        return None

    text = _first_key(data, _TEXT_KEYS)
    if not isinstance(text, str) or not text.strip():
        return None

    stamp = _parse_timestamp(data)
    if stamp is None:
        mtime = path.stat().st_mtime if path.exists() else (now or time.time())
        stamp = datetime.fromtimestamp(mtime).astimezone()

    t_end = stamp.timestamp()
    duration = _duration_seconds(data) or _DEFAULT_SPEECH_SECONDS
    audio = _find_audio(path.parent)
    return NoteEvent(
        transcript=text.strip(),
        t_start=t_end - duration,
        t_end=t_end,
        timestamp=stamp,
        source_dir=path.parent,
        audio_path=audio,
    )


def file_is_stable(path: Path | str, *, quiet_ms: float = 300.0, sleep=time.sleep) -> bool:
    """Wait until a file's size stops changing, so we never parse a half-write."""
    path = Path(path)
    try:
        size = path.stat().st_size
    except OSError:
        return False
    sleep(quiet_ms / 1000.0)
    try:
        return path.stat().st_size == size
    except OSError:
        return False


def iter_meta_files(root: Path | str) -> Iterator[Path]:
    """Every ``meta.json`` under a recordings folder, oldest first."""
    root = Path(root).expanduser()
    if not root.is_dir():
        return iter(())
    return iter(sorted(root.glob("*/meta.json"), key=lambda p: p.stat().st_mtime))


class SuperwhisperWatcher:
    """Emit a :class:`NoteEvent` for each new recording.

    Recordings that already exist when the watcher starts are marked as seen,
    not replayed: starting the daemon should not dump this morning's dictation
    into this afternoon's note.
    """

    def __init__(
        self,
        folder: Path | str,
        on_event: Callable[[NoteEvent], None],
        *,
        poll_interval: float = 0.25,
        replay_existing: bool = False,
    ) -> None:
        self.folder = Path(folder).expanduser()
        self.on_event = on_event
        self.poll_interval = poll_interval
        self._seen: set[Path] = set()
        self._stop = False
        if not replay_existing:
            self._seen.update(iter_meta_files(self.folder))

    def handle_path(self, path: Path) -> NoteEvent | None:
        """Process one candidate ``meta.json``; idempotent per path."""
        path = Path(path)
        if path.name != "meta.json" or path in self._seen:
            return None
        self._seen.add(path)
        if not file_is_stable(path):
            return None
        event = parse_meta(path)
        if event is None:
            return None
        try:
            self.on_event(event)
        except Exception:  # noqa: BLE001 - one bad note must not kill the daemon
            log.exception("note handler failed for %s", path)
        return event

    def poll_once(self) -> list[NoteEvent]:
        """One sweep of the folder. The whole watcher, minus the loop."""
        events = []
        for path in iter_meta_files(self.folder):
            event = self.handle_path(path)
            if event is not None:
                events.append(event)
        return events

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:  # pragma: no cover - long-running loop
        """Block, watching the folder. Uses watchdog when available."""
        if not self.folder.is_dir():
            log.error(
                "Superwhisper folder %s does not exist; set superwhisper_dir in config.toml",
                self.folder,
            )
            return
        observer = self._start_watchdog()
        try:
            while not self._stop:
                if observer is None:
                    self.poll_once()
                time.sleep(self.poll_interval)
        finally:
            if observer is not None:
                observer.stop()
                observer.join(timeout=2)

    def _start_watchdog(self):  # pragma: no cover - optional dependency
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError:
            log.info("watchdog not installed; polling %s every %.2fs", self.folder, self.poll_interval)
            return None

        watcher = self

        class _Handler(FileSystemEventHandler):
            def on_created(self, event):
                if not event.is_directory:
                    watcher.handle_path(Path(event.src_path))

            def on_modified(self, event):
                if not event.is_directory:
                    watcher.handle_path(Path(event.src_path))

        observer = Observer()
        observer.schedule(_Handler(), str(self.folder), recursive=True)
        observer.start()
        return observer
