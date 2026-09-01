"""The long-running daemon: wire the components together and watch the folder."""

from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path

from .browser import ChromeBridge
from .commands import CommandRouter, parse_command
from .config import Config
from .displays import Display, enumerate_displays, uncalibrated_displays
from .dwell import DwellConfig, DwellDriver
from .events import NoteEvent
from .geometry import Rect
from .notes import DailyNotes
from .pipeline import NoteProcessor
from .screen import get_screen
from .screenbuffer import ScreenBuffer

log = logging.getLogger(__name__)

__all__ = ["Daemon"]


class Daemon:
    """Owns the screen, gaze, browser and notes for one session."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.screen = get_screen()
        self.notes = DailyNotes(config.notes_dir)
        self.bridge = ChromeBridge(config.chrome_cdp_url)
        self.displays: list[Display] = enumerate_displays()
        self.gaze = self._build_gaze()
        self.buffer = self._build_buffer()
        self.processor = NoteProcessor(
            config,
            screen=self.screen,
            notes=self.notes,
            gaze=self.gaze,
            bridge=self.bridge,
            buffer=self.buffer,
            displays=lambda: self.displays,
        )
        self.dwell = DwellDriver(
            gaze=self.gaze,
            screen=self.display_rect,
            scroll=self._dwell_scroll,
            config=DwellConfig(
                zone_fraction=config.dwell.zone_fraction,
                dwell_seconds=config.dwell.dwell_seconds,
                cooldown_seconds=config.dwell.cooldown_seconds,
                scroll_amount=config.dwell.scroll_amount,
                min_confidence=config.dwell.min_confidence,
            ),
            enabled=config.dwell_scroll,
        )
        self.router = CommandRouter(
            bridge=self.bridge,
            screen=self.screen,
            gaze=self.gaze,
            recalibrate=self.recalibrate,
            new_section=self.new_section,
            dwell=self.dwell,
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

    def _build_buffer(self) -> ScreenBuffer | None:
        """The pre-note buffer, or ``None`` when it is switched off.

        Off is the default: this is the only component that records before the
        user speaks, so it is opt-in rather than opt-out.
        """
        if not self.config.screen_buffer_enabled:
            return None
        return ScreenBuffer(
            capture=self._capture_bytes,
            seconds=self.config.screen_buffer_seconds,
            interval=self.config.screen_buffer_interval,
            max_bytes=int(self.config.screen_buffer_max_mb * 1024 * 1024),
        )

    def _capture_bytes(self) -> bytes | None:
        """One screenshot as PNG bytes, never touching the notes directory."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "frame.png"
            if self.screen.capture_full(path) is None:
                return None
            return path.read_bytes()

    def _dwell_scroll(self, amount: float) -> str:
        """Route a dwell scroll through the same path as a spoken one."""
        app = self._guarded_frontmost()
        return self.router.scroll(amount, window_title=app.window_title if app is not None else "")

    def display_rect(self) -> Rect:
        try:
            return self.screen.main_display()
        except Exception as exc:  # noqa: BLE001
            log.warning("could not read display bounds: %s", exc)
            return Rect(0, 0, 1440, 900)

    def display_key(self) -> str:
        """Calibration key for the display being calibrated or tracked."""
        for display in self.displays:
            if display.is_main:
                return display.key
        rect = self.display_rect()
        return f"main-{int(rect.w)}x{int(rect.h)}"

    def uncalibrated(self) -> list[Display]:
        """Displays still needing ``gazenotes calibrate``."""
        return uncalibrated_displays(self.config.calibration_path, self.displays)

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
        """Start gaze, the pre-note buffer and dwell scrolling, as configured.

        Each is independent: none of them failing stops the others, and none of
        them is required for a note to be captured.
        """
        if self.gaze is not None:
            status = self.gaze.start()
            log.info("gaze: %s", status.reason)
        if self.buffer is not None:
            log.info(
                "pre-note screen buffer: %.0f s at %.1f s intervals, cap %.0f MB",
                self.config.screen_buffer_seconds,
                self.config.screen_buffer_interval,
                self.config.screen_buffer_max_mb,
            )
            self.buffer.start()
        if self.config.dwell_scroll:
            log.info("dwell scrolling: %s", self.dwell.start())
        for display in self.uncalibrated():
            log.warning("display %s is uncalibrated; run `gazenotes calibrate`", display.key)
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
        self.dwell.stop()
        if self.buffer is not None:
            self.buffer.stop()
            self.buffer.clear()  # buffered frames never outlive the daemon
        if self.gaze is not None:
            self.gaze.stop()
        self.bridge.close()
