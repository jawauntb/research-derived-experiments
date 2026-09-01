"""``gazenotes doctor`` — check every permission and dependency, honestly.

macOS TCC prompts are attached to the *process* that asks, so each check
actually attempts the access rather than reading a database. That means the
first ``doctor`` run is also what triggers the permission dialogs.
"""

from __future__ import annotations

import shutil
import socket
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from .config import Config

__all__ = ["Check", "run_checks", "format_report"]

OK, WARN, FAIL = "ok", "warn", "fail"


@dataclass
class Check:
    """One diagnostic result. ``fix`` is what the user should actually do."""

    name: str
    status: str
    detail: str = ""
    fix: str = ""

    @property
    def symbol(self) -> str:
        return {OK: "✓", WARN: "!", FAIL: "✗"}.get(self.status, "?")


def _import_check(name: str, module: str, fix: str) -> Check:
    try:
        __import__(module)
    except ImportError as exc:
        return Check(name, FAIL, str(exc), fix)
    return Check(name, OK, f"{module} importable")


def check_camera() -> Check:
    """Open the camera once. This is what triggers the TCC camera prompt."""
    try:
        import cv2
    except ImportError:
        return Check("Camera", FAIL, "opencv-python not installed", "pip install 'gazenotes[gaze]'")
    capture = cv2.VideoCapture(0)
    try:
        if not capture.isOpened():
            return Check(
                "Camera",
                FAIL,
                "could not open camera 0",
                "System Settings → Privacy & Security → Camera → enable for your terminal/app",
            )
        ok, frame = capture.read()
        if not ok or frame is None:
            return Check("Camera", WARN, "camera opened but returned no frame", "Check the lens cover")
        return Check("Camera", OK, f"frame {frame.shape[1]}x{frame.shape[0]}")
    finally:
        capture.release()


def check_screen_recording() -> Check:
    """Take a throwaway screenshot; a black or failed grab means no permission."""
    if shutil.which("screencapture") is None:
        return Check("Screen recording", FAIL, "screencapture not found", "This check needs macOS")
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "probe.png"
        try:
            subprocess.run(
                ["screencapture", "-x", "-t", "png", str(target)],
                check=True,
                capture_output=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return Check(
                "Screen recording",
                FAIL,
                str(exc),
                "System Settings → Privacy & Security → Screen Recording",
            )
        if not target.exists() or target.stat().st_size < 1024:
            return Check(
                "Screen recording",
                FAIL,
                "screenshot was empty",
                "System Settings → Privacy & Security → Screen Recording",
            )
        return Check("Screen recording", OK, f"{target.stat().st_size // 1024} KB test capture")


def check_accessibility() -> Check:
    """Accessibility is what lets gazenotes synthesise scroll events."""
    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions
        from CoreFoundation import kCFBooleanTrue

        options = {"AXTrustedCheckOptionPrompt": kCFBooleanTrue}
        trusted = bool(AXIsProcessTrustedWithOptions(options))
    except ImportError as exc:
        return Check("Accessibility", WARN, str(exc), "pip install pyobjc-framework-ApplicationServices")
    if trusted:
        return Check("Accessibility", OK, "process is trusted")
    return Check(
        "Accessibility",
        WARN,
        "not trusted (voice scrolling outside Chrome will not work)",
        "System Settings → Privacy & Security → Accessibility",
    )


def check_superwhisper(config: Config) -> Check:
    """The folder must exist *and* contain recordings, or retention is off."""
    folder = config.superwhisper_dir
    if not folder.is_dir():
        return Check(
            "Superwhisper folder",
            FAIL,
            f"{folder} does not exist",
            "Set superwhisper_dir in config.toml to the real recordings path",
        )
    recordings = sorted(folder.glob("*/meta.json"))
    if not recordings:
        return Check(
            "Superwhisper folder",
            WARN,
            f"{folder} has no meta.json yet",
            "Dictate once, and enable recording/transcript retention in Superwhisper settings",
        )
    return Check("Superwhisper folder", OK, f"{len(recordings)} recordings, newest {recordings[-1].parent.name}")


def check_chrome_cdp(config: Config) -> Check:
    """A plain TCP probe: cheap, and it does not need Playwright installed."""
    parts = urlsplit(config.chrome_cdp_url)
    host, port = parts.hostname or "localhost", parts.port or 9222
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return Check("Chrome CDP", OK, f"{host}:{port} reachable")
    except OSError as exc:
        return Check(
            "Chrome CDP",
            WARN,
            f"{host}:{port} unreachable ({exc})",
            "Start Chrome with `gazenotes chrome` (notes still work without it)",
        )


def check_notes_dir(config: Config) -> Check:
    """The notes folder must be writable; captures can contain anything."""
    folder = config.notes_dir
    try:
        folder.mkdir(parents=True, exist_ok=True)
        probe = folder / ".gazenotes-write-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return Check("Notes folder", FAIL, str(exc), f"Create {folder} and make it writable")
    return Check("Notes folder", OK, str(folder))


def check_calibration(config: Config) -> Check:
    """Report per display: an external monitor needs its own fit."""
    from .displays import enumerate_displays, uncalibrated_displays

    path = config.calibration_path
    displays = enumerate_displays()
    if not path.is_file():
        return Check("Gaze calibration", WARN, "not calibrated", "Run `gazenotes calibrate`")
    pending = uncalibrated_displays(path, displays)
    if pending:
        names = ", ".join(display.key for display in pending)
        return Check(
            "Gaze calibration",
            WARN,
            f"{len(displays) - len(pending)}/{len(displays)} displays calibrated; missing {names}",
            "Run `gazenotes calibrate` on each display",
        )
    return Check("Gaze calibration", OK, f"{len(displays)} display(s) calibrated")


def check_displays() -> Check:
    """Enumerate displays, so a multi-monitor setup is visible in the report."""
    from .displays import enumerate_displays

    displays = enumerate_displays()
    described = ", ".join(
        f"{display.key}@{display.scale:g}x" + (" (main)" if display.is_main else "")
        for display in displays
    )
    return Check("Displays", OK, described or "none found")


def check_vision_ocr(config: Config) -> Check:
    """Apple Vision powers 'Looking at' outside Chrome."""
    from .ocr import vision_available

    if not config.ocr_enabled:
        return Check("Vision OCR", OK, "disabled in config")
    if vision_available():
        return Check("Vision OCR", OK, "available")
    return Check(
        "Vision OCR",
        WARN,
        "unavailable; notes outside Chrome will have no quoted passage",
        "pip install 'gazenotes[ocr]' (macOS only)",
    )


def run_checks(config: Config) -> list[Check]:
    """Every check, in the order a new user should read them."""
    return [
        check_notes_dir(config),
        check_superwhisper(config),
        check_screen_recording(),
        check_camera(),
        check_accessibility(),
        check_displays(),
        check_calibration(config),
        check_vision_ocr(config),
        check_chrome_cdp(config),
        _import_check("MediaPipe", "mediapipe", "pip install 'gazenotes[gaze]'"),
        _import_check("Playwright", "playwright", "pip install 'gazenotes[browser]' && playwright install"),
        _import_check("PyObjC (Quartz)", "Quartz", "pip install 'gazenotes[macos]'"),
    ]


def format_report(checks: list[Check]) -> str:
    """Human-readable report; fixes are printed only where something is wrong."""
    width = max((len(c.name) for c in checks), default=0)
    lines = []
    for check in checks:
        lines.append(f"{check.symbol} {check.name.ljust(width)}  {check.detail}")
        if check.status != OK and check.fix:
            lines.append(f"{' ' * (width + 4)}→ {check.fix}")
    failures = sum(1 for c in checks if c.status == FAIL)
    warnings = sum(1 for c in checks if c.status == WARN)
    lines.append("")
    lines.append(f"{len(checks) - failures - warnings} ok, {warnings} warnings, {failures} failures")
    return "\n".join(lines)
