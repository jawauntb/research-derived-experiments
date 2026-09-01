"""Coordinate systems, in one place, with one internal convention.

Three coordinate systems collide in this app:

``quartz``
    Logical points, origin **top-left** of the main display, y grows down.
    ``CGWindowListCopyWindowInfo`` bounds live here.
``cocoa``
    Logical points, origin **bottom-left** of the main display, y grows up.
    ``NSScreen``/``NSWindow`` frames live here.
``pixels``
    Device pixels — ``scale`` times the logical size (2.0 on Retina).
    Screenshot files live here.

**Internally gazenotes uses quartz logical points everywhere.** Conversion
happens only at the edges: reading a Cocoa frame, or slicing a screenshot.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "Point",
    "Rect",
    "cocoa_to_quartz_y",
    "quartz_to_cocoa_y",
    "logical_rect_to_pixels",
    "screen_to_window",
    "window_to_viewport",
    "gaze_crop_rect",
]


@dataclass(frozen=True)
class Point:
    """A point in logical points, quartz orientation unless stated otherwise."""

    x: float
    y: float


@dataclass(frozen=True)
class Rect:
    """An axis-aligned rectangle: origin plus size, same units as its source."""

    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def contains(self, point: Point) -> bool:
        """Half-open containment: the right/bottom edges belong to the neighbour."""
        return self.x <= point.x < self.right and self.y <= point.y < self.bottom

    def clamped_to(self, outer: Rect) -> Rect:
        """Shift, then shrink, so the result fits inside ``outer``."""
        w = min(self.w, outer.w)
        h = min(self.h, outer.h)
        x = min(max(self.x, outer.x), outer.right - w)
        y = min(max(self.y, outer.y), outer.bottom - h)
        return Rect(x, y, w, h)

    def as_int_tuple(self) -> tuple[int, int, int, int]:
        """Round to whole units for image slicing (``x, y, w, h``)."""
        return (round(self.x), round(self.y), round(self.w), round(self.h))


def cocoa_to_quartz_y(y: float, height: float, display_height: float) -> float:
    """Convert a Cocoa (bottom-left) rect's y to Quartz (top-left).

    ``height`` is the rect's own height: Cocoa's y is its *bottom* edge, Quartz
    wants its *top* edge.
    """
    return display_height - (y + height)


def quartz_to_cocoa_y(y: float, height: float, display_height: float) -> float:
    """Inverse of :func:`cocoa_to_quartz_y` (it is its own inverse)."""
    return display_height - (y + height)


def logical_rect_to_pixels(rect: Rect, scale: float) -> Rect:
    """Scale a logical-point rect into device pixels for image slicing."""
    return Rect(rect.x * scale, rect.y * scale, rect.w * scale, rect.h * scale)


def screen_to_window(point: Point, window: Rect) -> Point:
    """Screen point → window-local point (both quartz logical points)."""
    return Point(point.x - window.x, point.y - window.y)


def window_to_viewport(point: Point, window: Rect, chrome_height: float) -> Point:
    """Screen point → browser viewport point.

    ``chrome_height`` is ``window.outerHeight - window.innerHeight``: tab strip,
    omnibox and bookmark bar. Horizontal chrome is assumed zero, which holds for
    Chrome on macOS. The result may fall outside the viewport (the user looked
    at the omnibox); the caller decides what to do about that.
    """
    local = screen_to_window(point, window)
    return Point(local.x, local.y - chrome_height)


def gaze_crop_rect(
    gaze: Point,
    screen: Rect,
    height_fraction: float = 0.35,
) -> Rect:
    """Full-width band of the screen, centred on the gaze y, clamped to screen.

    Coarse by design: webcam gaze is trustworthy at roughly a sixth of screen
    height, so the crop is a reading band rather than a box around a word.
    """
    if not 0.0 < height_fraction <= 1.0:
        raise ValueError("height_fraction must be in (0, 1]")
    band_h = screen.h * height_fraction
    band = Rect(screen.x, gaze.y - band_h / 2.0, screen.w, band_h)
    return band.clamped_to(screen)
