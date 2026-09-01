"""Menu-bar status item (``rumps``), with a headless fallback.

Without rumps the daemon still runs — it just prints its status instead of
showing a menu — so the daemon never depends on a GUI being available.
"""

from __future__ import annotations

import logging
import subprocess
from collections.abc import Callable

log = logging.getLogger(__name__)

__all__ = ["MenuBar", "HeadlessMenu", "build_menu"]


class HeadlessMenu:
    """Runs the daemon loop directly and logs status changes."""

    def __init__(self, title: str = "gazenotes", **actions: Callable[[], None]) -> None:
        self.title = title
        self.actions = actions
        self._runner: Callable[[], None] | None = None

    def set_runner(self, runner: Callable[[], None]) -> None:
        self._runner = runner

    def set_status(self, text: str) -> None:
        log.info("status: %s", text)

    def run(self) -> None:
        if self._runner is None:
            raise RuntimeError("no runner set")
        self._runner()


class MenuBar:  # pragma: no cover - GUI
    """rumps status item: gaze on/off, recalibrate, open today's note, quit."""

    def __init__(self, title: str = "👁", **actions: Callable[[], None]) -> None:
        import rumps

        self._rumps = rumps
        self._actions = actions
        self._runner: Callable[[], None] | None = None

        app = rumps.App(title, quit_button=None)
        app.menu = [
            rumps.MenuItem("Open today's note", callback=self._wrap("open_today")),
            rumps.MenuItem("Recalibrate gaze", callback=self._wrap("recalibrate")),
            rumps.MenuItem("Pause gaze", callback=self._wrap("toggle_gaze")),
            None,
            rumps.MenuItem("Status: starting…"),
            None,
            rumps.MenuItem("Quit", callback=self._wrap("quit")),
        ]
        self.app = app

    def _wrap(self, name: str):
        def handler(_sender):
            action = self._actions.get(name)
            if action is None:
                return
            try:
                action()
            except Exception:  # noqa: BLE001 - a menu click must not crash the app
                log.exception("menu action %s failed", name)

        return handler

    def set_runner(self, runner: Callable[[], None]) -> None:
        self._runner = runner

    def set_status(self, text: str) -> None:
        self.app.menu["Status: starting…"].title = f"Status: {text}"

    def run(self) -> None:
        if self._runner is not None:
            import threading

            threading.Thread(target=self._runner, name="gazenotes-daemon", daemon=True).start()
        self.app.run()


def build_menu(**actions: Callable[[], None]):
    """A real menu bar when rumps is installed, a headless one otherwise."""
    try:
        return MenuBar(**actions)
    except ImportError as exc:
        log.info("rumps unavailable (%s); running headless", exc)
        return HeadlessMenu(**actions)


def open_path(path) -> None:
    """Open a file with the user's default app (``open`` on macOS)."""
    try:
        subprocess.run(["open", str(path)], check=False, timeout=5)
    except (OSError, subprocess.SubprocessError) as exc:
        log.warning("could not open %s: %s", path, exc)
