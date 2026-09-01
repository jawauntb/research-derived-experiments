"""macOS screen access: frontmost app, window bounds, screenshots, cropping.

Quartz/Cocoa come in through lazy imports, so this module is importable
anywhere. :class:`MacScreen` is the real adapter; :class:`NullScreen` is the
inert one used when PyObjC is missing (and in tests).

Everything returned is in **quartz logical points** (see
:mod:`gazenotes.geometry`); pixels appear only when slicing an image file.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Protocol

from .events import AppContext
from .geometry import Rect, logical_rect_to_pixels

log = logging.getLogger(__name__)

__all__ = ["ScreenBackend", "MacScreen", "NullScreen", "get_screen"]


class ScreenBackend(Protocol):
    """What the capture pipeline needs from the windowing system."""

    def main_display(self) -> Rect: ...

    def backing_scale(self) -> float: ...

    def frontmost(self) -> AppContext | None: ...

    def capture_full(self, destination: Path) -> Path | None: ...

    def crop(self, source: Path, rect: Rect, destination: Path) -> Path | None: ...

    def scroll(self, amount: float) -> None: ...


class NullScreen:
    """No windowing system. Reports a nominal display and captures nothing."""

    def __init__(self, display: Rect | None = None, reason: str = "unavailable") -> None:
        self._display = display or Rect(0, 0, 1440, 900)
        self.reason = reason

    def main_display(self) -> Rect:
        return self._display

    def backing_scale(self) -> float:
        return 1.0

    def frontmost(self) -> AppContext | None:
        return None

    def capture_full(self, destination: Path) -> Path | None:
        return None

    def crop(self, source: Path, rect: Rect, destination: Path) -> Path | None:
        return None

    def scroll(self, amount: float) -> None:
        return None


class MacScreen:
    """Quartz-backed implementation. Import errors surface at construction."""

    def __init__(self) -> None:
        import Quartz  # noqa: F401  (raises ImportError when PyObjC is absent)

        self._quartz = Quartz

    # -- geometry -------------------------------------------------------
    def main_display(self) -> Rect:
        Quartz = self._quartz
        display = Quartz.CGMainDisplayID()
        bounds = Quartz.CGDisplayBounds(display)
        return Rect(
            float(bounds.origin.x),
            float(bounds.origin.y),
            float(bounds.size.width),
            float(bounds.size.height),
        )

    def backing_scale(self) -> float:
        """Pixels per logical point for the main display (2.0 on Retina)."""
        try:
            from AppKit import NSScreen

            screen = NSScreen.mainScreen()
            if screen is not None:
                return float(screen.backingScaleFactor())
        except ImportError:
            pass
        Quartz = self._quartz
        display = Quartz.CGMainDisplayID()
        mode = Quartz.CGDisplayCopyDisplayMode(display)
        if mode is None:
            return 1.0
        logical = float(Quartz.CGDisplayModeGetWidth(mode))
        pixels = float(Quartz.CGDisplayModeGetPixelWidth(mode))
        return pixels / logical if logical else 1.0

    # -- frontmost app --------------------------------------------------
    def frontmost(self) -> AppContext | None:
        """Frontmost app plus its front window's bounds and title.

        The window title needs screen-recording permission; without it the app
        name and bounds still come back, so the note keeps its context.
        """
        try:
            from AppKit import NSWorkspace
        except ImportError:  # pragma: no cover - depends on host
            return None

        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if app is None:
            return None
        name = str(app.localizedName() or "")
        bundle_id = str(app.bundleIdentifier() or "")
        pid = int(app.processIdentifier())
        title, bounds = self._front_window_for_pid(pid)
        return AppContext(
            name=name,
            bundle_id=bundle_id,
            window_title=title,
            window_bounds=(bounds.x, bounds.y, bounds.w, bounds.h) if bounds else None,
        )

    def _front_window_for_pid(self, pid: int) -> tuple[str, Rect | None]:
        Quartz = self._quartz
        options = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
        windows = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID) or []
        for info in windows:
            if int(info.get("kCGWindowOwnerPID", -1)) != pid:
                continue
            if int(info.get("kCGWindowLayer", 0)) != 0:
                continue  # menu bar, overlays, tooltips
            bounds = info.get("kCGWindowBounds") or {}
            rect = Rect(
                float(bounds.get("X", 0.0)),
                float(bounds.get("Y", 0.0)),
                float(bounds.get("Width", 0.0)),
                float(bounds.get("Height", 0.0)),
            )
            return str(info.get("kCGWindowName") or ""), rect
        return "", None

    # -- pixels ---------------------------------------------------------
    def capture_full(self, destination: Path) -> Path | None:
        """Full-screen PNG via ``screencapture -x`` (no shutter sound).

        Shelling out beats ``CGWindowListCreateImage`` here: it is one call,
        it honours the same screen-recording permission, and it writes the file
        atomically enough for our purposes.
        """
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["screencapture", "-x", "-t", "png", str(destination)],
                check=True,
                timeout=5,
                capture_output=True,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            log.warning("screenshot failed: %s", exc)
            return None
        return destination if destination.exists() else None

    def crop(self, source: Path, rect: Rect, destination: Path) -> Path | None:
        """Crop a logical-point rect out of a screenshot, honouring Retina scale."""
        return crop_image(source, rect, destination, scale=self.backing_scale())

    # -- input ----------------------------------------------------------
    def scroll(self, amount: float) -> None:
        """Synthesise a scroll wheel event at the cursor.

        Used only when there is no CDP page to scroll. Needs Accessibility
        permission; ``doctor`` checks for it. Quartz scroll units are lines,
        not points, and the sign is inverted relative to CSS: a positive
        ``amount`` means "move the content up", the same as
        ``page.mouse.wheel``.
        """
        Quartz = self._quartz
        lines = int(round(-amount / 40.0)) or (-1 if amount > 0 else 1)
        event = Quartz.CGEventCreateScrollWheelEvent(
            None, Quartz.kCGScrollEventUnitLine, 1, lines
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def crop_image(source: Path, rect: Rect, destination: Path, *, scale: float = 1.0) -> Path | None:
    """Crop ``rect`` (logical points) from ``source`` into ``destination``.

    Tries Quartz first (always present on the target platform), then Pillow.
    Returns ``None`` when neither is available — the caller keeps the full
    screenshot rather than failing the capture.
    """
    source, destination = Path(source), Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pixel_rect = logical_rect_to_pixels(rect, scale)

    try:
        import Quartz
        from CoreFoundation import CFURLCreateWithFileSystemPath, kCFURLPOSIXPathStyle

        url = CFURLCreateWithFileSystemPath(None, str(source), kCFURLPOSIXPathStyle, False)
        image_source = Quartz.CGImageSourceCreateWithURL(url, None)
        if image_source is None:
            return None
        image = Quartz.CGImageSourceCreateImageAtIndex(image_source, 0, None)
        if image is None:
            return None
        cropped = Quartz.CGImageCreateWithImageInRect(
            image,
            Quartz.CGRectMake(pixel_rect.x, pixel_rect.y, pixel_rect.w, pixel_rect.h),
        )
        if cropped is None:
            return None
        out_url = CFURLCreateWithFileSystemPath(None, str(destination), kCFURLPOSIXPathStyle, False)
        writer = Quartz.CGImageDestinationCreateWithURL(out_url, "public.png", 1, None)
        if writer is None:
            return None
        Quartz.CGImageDestinationAddImage(writer, cropped, None)
        return destination if Quartz.CGImageDestinationFinalize(writer) else None
    except ImportError:
        pass

    try:
        from PIL import Image
    except ImportError:
        return None
    with Image.open(source) as image:
        box = (
            max(0, round(pixel_rect.x)),
            max(0, round(pixel_rect.y)),
            min(image.width, round(pixel_rect.right)),
            min(image.height, round(pixel_rect.bottom)),
        )
        if box[2] <= box[0] or box[3] <= box[1]:
            return None
        image.crop(box).save(destination)
    return destination


def get_screen() -> ScreenBackend:
    """The real backend on macOS, an inert one everywhere else."""
    try:
        return MacScreen()
    except ImportError as exc:
        log.info("Quartz unavailable (%s); screen capture disabled", exc)
        return NullScreen(reason=f"Quartz unavailable: {exc}")
