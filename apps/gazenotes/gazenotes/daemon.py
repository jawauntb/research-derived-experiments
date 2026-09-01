"""The long-running daemon: wire the components together and watch the folder."""

from __future__ import annotations

import logging
from datetime import date, datetime

from .browser import ChromeBridge
from .commands import CommandRouter, parse_command
from .config import Config
from .events import NoteEvent
from .geometry import Rect
from .notes import DailyNotes
from .pipeline import NoteProcessor
from .screen import get_screen

log = logging.getLogger(__name__)

__all__ = ["Daemon"]


class Daemon:
    """Owns the screen, gaze, browser and notes for one session."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.screen = get_screen()
        self.notes = DailyNotes(config.notes_dir)
        self.bridge = ChromeBridge(config.chrome_cdp_url)
        self.gaze = self._build_gaze()
        self.processor = NoteProcessor(
            config,
            screen=self.screen,
            notes=self.notes,
            gaze=self.gaze,
            bridge=self.bridge,
        )
        self.router = CommandRouter(
            bridge=self.bridge,
            screen=self.screen,
            gaze=self.gaze,
            recalibrate=self.recalibrate,
            new_section=self.new_section,
        )
        self.watcher = None
        self.last_status = "starting"

    # -- setup ----------------------------------------------------------
    def _build_gaze(self):
        """Construct the gaze engine; ``None`` if its dependencies are missing."""
        try:
            from .gaze.capture import GazeEngine
        except ImportError as exc:  # pragma: no cover - defensive
            log.info("gaze engine unavailable: %s", exc)
            return None
        return GazeEngine(
            screen=self.display_rect(),
            calibration_path=self.config.calibration_path,
            display_key=self.display_key(),
        )

    def display_rect(self) -> Rect:
        try:
            return self.screen.main_display()
        except Exception as exc:  # noqa: BLE001
            log.warning("could not read display bounds: %s", exc)
            return Rect(0, 0, 1440, 900)

    def display_key(self) -> str:
        """Calibration key: one model per display geometry."""
        rect = self.display_rect()
        return f"main-{int(rect.w)}x{int(rect.h)}"

    # -- events ---------------------------------------------------------
    def handle_event(self, event: NoteEvent) -> None:
        """Route one transcript: command, or note."""
        command = parse_command(event.transcript, self.config.command_prefix)
        if command is not None:
            app = self._guarded_frontmost()
            title = app.window_title if app is not None else ""
            result = self.router.dispatch(command, window_title=title)
            log.info("command %s → %s", command.name, result)
            self.set_status(result)
            return

        capture = self.processor.process(event)
        where = capture.app.name if capture.app else "unknown app"
        confidence = f"{capture.fixation.confidence:.2f}" if capture.fixation else "no gaze"
        log.info("note captured (%s, %s)", where, confidence)
        self.set_status(f"{event.timestamp:%H:%M:%S} · {where} · {confidence}")

    def _guarded_frontmost(self):
        try:
            return self.screen.frontmost()
        except Exception:  # noqa: BLE001
            return None

    # -- menu actions ---------------------------------------------------
    def open_today(self) -> None:
        from .menubar import open_path

        open_path(self.notes.ensure_day(date.today()))

    def recalibrate(self) -> str:
        """Run calibration in the foreground; the watcher keeps running."""
        if self.gaze is None:
            return "gaze engine unavailable"
        from .gaze.calibrate import show_calibration_ui

        self.gaze.start(require_calibration=False)
        result = show_calibration_ui(
            self.display_rect(),
            self.gaze.current_features,
            calibration_path=self.config.calibration_path,
            display_key=self.display_key(),
        )
        if result.accepted:
            # Reloading also picks up the head pose the fit was taken at.
            self.gaze.load_calibration()
            return f"calibrated, median error {result.residual_px:.0f} pt"
        return f"calibration rejected: {result.reason}"

    def new_section(self, title: str) -> str:
        """Append a heading to today's file, so a session can be divided by voice."""
        today = date.today()
        path = self.notes.ensure_day(today)
        heading = title.strip() or datetime.now().strftime("%H:%M")
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"\n# {heading}\n\n")
        return f"new section: {heading}"

    def toggle_gaze(self) -> None:
        if self.gaze is None:
            return
        if self.gaze.status.available:
            self.gaze.stop()
            self.set_status("gaze paused")
        else:
            self.set_status(self.gaze.start().reason)

    def set_status(self, text: str) -> None:
        self.last_status = text

    # -- lifecycle ------------------------------------------------------
    def start_background(self) -> None:
        """Start gaze; log rather than fail when it is unavailable."""
        if self.gaze is not None:
            status = self.gaze.start()
            log.info("gaze: %s", status.reason)
        if not self.config.superwhisper_dir.is_dir():
            log.error(
                "Superwhisper folder %s not found — run `gazenotes doctor`",
                self.config.superwhisper_dir,
            )

    def run(self) -> None:  # pragma: no cover - long-running loop
        from .watcher import SuperwhisperWatcher

        self.start_background()
        self.watcher = SuperwhisperWatcher(self.config.superwhisper_dir, self.handle_event)
        log.info("watching %s", self.config.superwhisper_dir)
        try:
            self.watcher.run()
        finally:
            self.stop()

    def stop(self) -> None:
        if self.watcher is not None:
            self.watcher.stop()
        if self.gaze is not None:
            self.gaze.stop()
        self.bridge.close()
