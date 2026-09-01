"""The capture pipeline: one spoken note in, one written entry out.

Ordering here is deliberate and load-bearing:

1. **Screenshot first.** The screen can change within 100 ms of the user
   finishing a sentence; everything else is recoverable, a lost frame is not.
2. Gaze is queried for the window ``[t_start - lookback, t_end]``.
3. Chrome enrichment is attempted only when Chrome is frontmost.
4. The crop is chosen from the best evidence available, falling back to the
   full screenshot.

Every enrichment step is wrapped: a failure downgrades the entry, it never
loses the note. Collaborators are injected, so the whole pipeline is testable
with fakes and no macOS.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .config import Config
from .events import AppContext, Capture, NoteEvent, OcrContext
from .geometry import Point, Rect, gaze_crop_rect
from .lock import notes_lock
from .notes import DailyNotes

log = logging.getLogger(__name__)

__all__ = ["NoteProcessor"]


class NoteProcessor:
    """Turns :class:`NoteEvent` values into written entries."""

    def __init__(
        self,
        config: Config,
        *,
        screen,
        notes: DailyNotes | None = None,
        gaze=None,
        bridge=None,
        buffer=None,
        displays=None,
    ) -> None:
        self.config = config
        self.screen = screen
        self.notes = notes or DailyNotes(config.notes_dir)
        self.gaze = gaze
        self.bridge = bridge
        self.buffer = buffer
        """Optional rolling pre-note screen buffer; ``None`` when disabled."""
        self.displays = displays
        """Optional zero-arg callable returning the current display list."""

    # -- public ---------------------------------------------------------
    def process(self, event: NoteEvent) -> Capture:
        """Run the full pipeline and write the entry. Always writes something."""
        capture = Capture(event=event)
        directory = self.notes.capture_dir(event.timestamp.date())
        directory.mkdir(parents=True, exist_ok=True)
        stem = self.notes.reserve_stem(event.timestamp)
        capture.extra["stem"] = stem

        full_path = directory / f"{stem}.full.png"
        shot = self._guard("screenshot", lambda: self.screen.capture_full(full_path))
        capture.screenshot_full = shot
        capture.screenshot = shot

        # Second, before any enrichment: the screen as it was when they began
        # speaking. "Note that" is usually about something already scrolling
        # away, and this is the only record of it.
        if self.buffer is not None:
            before = self._guard(
                "pre-note frame",
                lambda: self.buffer.write_frame_at(event.t_start, directory / f"{stem}.before.png"),
            )
            capture.screenshot_before = before

        capture.app = self._guard("frontmost app", self.screen.frontmost)
        capture.fixation = self._guard("gaze", lambda: self._fixation(event))
        capture.display = self._guard("display", lambda: self._display_key(capture.fixation)) or ""

        window = self._window_rect(capture.app)
        if (
            capture.app is not None
            and capture.app.is_chrome
            and capture.fixation is not None
            and window is not None
            and self.bridge is not None
        ):
            capture.browser = self._guard(
                "chrome enrichment",
                lambda: self.bridge.extract_at(
                    Point(capture.fixation.x, capture.fixation.y),
                    window,
                    window_title=capture.app.window_title if capture.app else "",
                ),
            )

        self._attach_image(capture, directory, stem)

        # OCR is the non-browser fallback for "Looking at", so it only runs
        # when the DOM gave us nothing.
        if self.config.ocr_enabled and capture.browser is None and capture.screenshot is not None:
            capture.ocr = self._guard("ocr", lambda: self._ocr(capture.screenshot))

        if not self.config.keep_full_screenshot and capture.screenshot_full is not None:
            if capture.screenshot != capture.screenshot_full:
                self._guard("discard full screenshot", capture.screenshot_full.unlink)
                capture.screenshot_full = None

        # Held only across the write, so the nightly pass can never rewrite a
        # day file between the sidecar and the markdown entry.
        with notes_lock(self.config.notes_dir):
            self.notes.append(capture)
        return capture

    # -- steps ----------------------------------------------------------
    def _fixation(self, event: NoteEvent):
        """Dominant fixation over the utterance, gated on confidence.

        The window reaches back before speech began: people look at the thing,
        *then* start talking about it.
        """
        if self.gaze is None:
            return None
        t0 = event.t_start - self.config.gaze_lookback_seconds
        fixation = self.gaze.dominant_fixation(t0, event.t_end)
        if fixation is None:
            return None
        if fixation.confidence < self.config.min_gaze_confidence:
            log.debug(
                "discarding fixation at confidence %.2f (floor %.2f)",
                fixation.confidence,
                self.config.min_gaze_confidence,
            )
            return None
        return fixation

    def _display_key(self, fixation) -> str:
        """Which display the gaze landed on, for the sidecar and calibration."""
        if fixation is None or self.displays is None:
            return ""
        from .displays import display_for_point

        display = display_for_point(Point(fixation.x, fixation.y), self.displays())
        return display.key if display is not None else ""

    @staticmethod
    def _ocr(image: Path) -> OcrContext | None:
        """Read the capture with Apple Vision. Absent on any other platform."""
        from .ocr import looking_at

        text = looking_at(image)
        return OcrContext(text=text) if text else None

    @staticmethod
    def _window_rect(app: AppContext | None) -> Rect | None:
        if app is None or app.window_bounds is None:
            return None
        x, y, w, h = app.window_bounds
        return Rect(x, y, w, h)

    def _attach_image(self, capture: Capture, directory: Path, stem: str) -> None:
        """Pick the tightest evidence available: element shot, crop, or full."""
        target = directory / f"{stem}.png"

        if capture.browser is not None and self.bridge is not None:
            shot = self._guard(
                "element screenshot",
                lambda: self.bridge.screenshot_element(
                    capture.browser,
                    target,
                    window_title=capture.app.window_title if capture.app else "",
                ),
            )
            if shot is not None:
                # No `crop` is recorded here: the element bbox is in viewport
                # coordinates and lives under `browser.bbox` in the sidecar,
                # while `crop` always means a screen-space rect.
                capture.screenshot = shot
                return

        if capture.fixation is not None and capture.screenshot_full is not None:
            display = self._guard("display bounds", self.screen.main_display)
            if display is not None:
                rect = gaze_crop_rect(
                    Point(capture.fixation.x, capture.fixation.y),
                    display,
                    self.config.crop_height_fraction,
                )
                cropped = self._guard(
                    "crop",
                    lambda: self.screen.crop(capture.screenshot_full, rect, target),
                )
                if cropped is not None:
                    capture.screenshot = cropped
                    capture.crop = (rect.x, rect.y, rect.w, rect.h)
                    return

        capture.screenshot = capture.screenshot_full

    @staticmethod
    def _guard(label: str, call):
        """Run an enrichment step; log and return ``None`` if it fails."""
        try:
            return call()
        except Exception as exc:  # noqa: BLE001 - enrichment is always optional
            log.warning("%s failed: %s", label, exc)
            return None
