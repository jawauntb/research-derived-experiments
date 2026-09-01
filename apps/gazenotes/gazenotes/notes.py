"""Daily markdown file management, entry formatting, and capture layout.

Output is a folder of plain files — markdown, PNG, JSON — so Obsidian (or
``grep``) can read it and nothing is locked in a database.

Entries are **append-only**. The only writer allowed to touch existing text is
the nightly pass, and only the summary block above the first entry.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path

from .events import Capture

__all__ = [
    "SUMMARY_START",
    "SUMMARY_END",
    "DailyNotes",
    "format_entry",
    "capture_stem",
    "sidecar_dict",
]

SUMMARY_START = "<!-- gazenotes:summary -->"
SUMMARY_END = "<!-- /gazenotes:summary -->"

_MAX_LOOKING_AT = 240


def capture_stem(when: datetime) -> str:
    """Filename stem for a capture: ``HHMMSS``."""
    return when.strftime("%H%M%S")


def _ellipsis(text: str, limit: int = _MAX_LOOKING_AT) -> str:
    """Middle-truncate a quoted passage so entries stay skimmable."""
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1].rstrip() + "…"


def format_entry(capture: Capture, capture_rel: Path | None = None) -> str:
    """Render one capture as a markdown entry.

    Any line whose data is missing is omitted entirely — no empty
    ``**Looking at:**`` placeholders.
    """
    when = capture.event.timestamp
    app_name = capture.app.name if capture.app else "Unknown app"
    heading_bits = [when.strftime("%H:%M:%S"), "—", app_name]
    if capture.browser and capture.browser.url:
        host = _host(capture.browser.url)
        if host:
            heading_bits.append(f"· {host}")
    lines = ["## " + " ".join(heading_bits), ""]

    transcript = " ".join(capture.event.transcript.split())
    lines.append(f'> "{transcript}"')
    lines.append("")

    if capture.browser and capture.browser.text.strip():
        lines.append(f'**Looking at:** "…{_ellipsis(capture.browser.text)}…"')
    if capture.browser and capture.browser.url:
        title = capture.browser.title.strip() or _host(capture.browser.url) or "source"
        link = capture.browser.fragment_url or capture.browser.url
        lines.append(f"**Source:** [{_escape_link_text(title)}]({link})")
    elif capture.app and capture.app.window_title:
        lines.append(f"**Window:** {capture.app.window_title}")

    if capture.screenshot is not None:
        rel = _relative(capture.screenshot, capture_rel)
        lines.append(f"**Capture:** ![]({rel})")

    trailer: list[str] = []
    if capture.fixation is not None:
        trailer.append(f"Gaze confidence: {capture.fixation.confidence:.2f}")
    if capture.screenshot_full is not None:
        trailer.append(f"[full screen]({_relative(capture.screenshot_full, capture_rel)})")
    meta = capture.extra.get("sidecar")
    if meta is not None:
        trailer.append(f"[meta]({_relative(Path(meta), capture_rel)})")
    if trailer:
        lines.append(" · ".join(trailer))

    lines += ["", "---", ""]
    return "\n".join(lines)


def _escape_link_text(text: str) -> str:
    """Keep a page title from breaking out of its markdown link."""
    return text.replace("[", "(").replace("]", ")")


def _host(url: str) -> str:
    """Bare hostname for a heading, empty if the URL is not http(s)."""
    from urllib.parse import urlsplit

    try:
        netloc = urlsplit(url).netloc
    except ValueError:
        return ""
    return netloc[4:] if netloc.startswith("www.") else netloc


def _relative(path: Path, base: Path | None) -> str:
    """Path as written into markdown: relative to the notes dir when possible."""
    if base is None:
        return path.as_posix()
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def sidecar_dict(capture: Capture, notes_dir: Path | None = None) -> dict:
    """The JSON sidecar for one capture, with ``None`` branches dropped."""
    event = capture.event
    data: dict = {
        "ts": event.timestamp.astimezone().isoformat(timespec="seconds"),
        "transcript": " ".join(event.transcript.split()),
    }
    if event.audio_path is not None:
        data["audio_path"] = str(event.audio_path)
    if capture.app is not None:
        data["app"] = {
            "name": capture.app.name,
            "bundle_id": capture.app.bundle_id,
            "window_title": capture.app.window_title,
        }
        if capture.app.window_bounds is not None:
            data["app"]["window_bounds"] = list(capture.app.window_bounds)
    if capture.fixation is not None:
        fix = asdict(capture.fixation)
        data["gaze"] = {
            "x": round(fix["x"], 1),
            "y": round(fix["y"], 1),
            "confidence": round(fix["confidence"], 3),
            "display_id": fix["display_id"],
            "method": fix["method"],
            "samples": fix["sample_count"],
        }
    if capture.crop is not None:
        x, y, w, h = capture.crop
        data["crop"] = {"x": round(x), "y": round(y), "w": round(w), "h": round(h)}
    if capture.browser is not None:
        data["browser"] = {
            "url": capture.browser.url,
            "title": capture.browser.title,
            "text": capture.browser.text,
            "selector": capture.browser.selector,
            "scroll_y": capture.browser.scroll_y,
            "fragment_url": capture.browser.fragment_url,
        }
        if capture.browser.bbox is not None:
            x, y, w, h = capture.browser.bbox
            data["browser"]["bbox"] = {"x": x, "y": y, "width": w, "height": h}
    if capture.screenshot is not None:
        data["screenshot"] = _relative(capture.screenshot, notes_dir)
    if capture.screenshot_full is not None:
        data["screenshot_full"] = _relative(capture.screenshot_full, notes_dir)
    return data


class DailyNotes:
    """Reads and writes ``<notes_dir>/YYYY-MM-DD.md`` and its capture folder."""

    def __init__(self, notes_dir: Path | str) -> None:
        self.notes_dir = Path(notes_dir).expanduser()

    # -- layout ---------------------------------------------------------
    def path_for(self, day: date) -> Path:
        return self.notes_dir / f"{day.isoformat()}.md"

    def capture_dir(self, day: date) -> Path:
        return self.notes_dir / "captures" / day.isoformat()

    def reserve_stem(self, when: datetime) -> str:
        """A capture stem that no existing file in the day's folder uses.

        Two recordings can finish inside the same second; without this the
        second one would silently overwrite the first one's screenshots.
        """
        base = capture_stem(when)
        directory = self.capture_dir(when.date())
        if not directory.exists() or not any(directory.glob(f"{base}.*")):
            return base
        # "_02" rather than "-2": underscore sorts after ".", so a collision
        # suffix keeps the capture folder in chronological filename order.
        for suffix in range(2, 100):
            candidate = f"{base}_{suffix:02d}"
            if not any(directory.glob(f"{candidate}.*")):
                return candidate
        return f"{base}_{when.microsecond:06d}"

    def ensure_day(self, day: date) -> Path:
        """Create the day's file with a header if it does not exist yet."""
        path = self.path_for(day)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {day.isoformat()}\n\n", encoding="utf-8")
        return path

    # -- writing --------------------------------------------------------
    def append(self, capture: Capture) -> Path:
        """Append one entry plus its sidecar; returns the day's markdown path."""
        day = capture.event.timestamp.date()
        path = self.ensure_day(day)
        capture.extra.setdefault("stem", self.reserve_stem(capture.event.timestamp))
        sidecar = self.write_sidecar(capture)
        capture.extra["sidecar"] = sidecar
        text = format_entry(capture, capture_rel=self.notes_dir)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(text)
        return path

    def write_sidecar(self, capture: Capture) -> Path:
        """Write ``<captures>/<day>/<HHMMSS>.json`` next to the screenshots."""
        day = capture.event.timestamp.date()
        directory = self.capture_dir(day)
        directory.mkdir(parents=True, exist_ok=True)
        stem = capture.extra.get("stem") or capture_stem(capture.event.timestamp)
        path = directory / f"{stem}.json"
        payload = sidecar_dict(capture, notes_dir=self.notes_dir)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def read_day(self, day: date) -> str:
        path = self.path_for(day)
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def sidecars(self, day: date) -> list[dict]:
        """Every sidecar for a day, in capture order, skipping unreadable ones."""
        directory = self.capture_dir(day)
        if not directory.is_dir():
            return []
        out = []
        for path in sorted(directory.glob("*.json")):
            try:
                out.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return out

    def purge(self, day: date) -> list[Path]:
        """Delete a day's note and captures. Returns what was removed."""
        removed: list[Path] = []
        note = self.path_for(day)
        if note.exists():
            note.unlink()
            removed.append(note)
        directory = self.capture_dir(day)
        if directory.is_dir():
            shutil.rmtree(directory)
            removed.append(directory)
        return removed
