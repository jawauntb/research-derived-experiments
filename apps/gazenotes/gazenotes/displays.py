"""Which physical screen a point, a window, or a calibration belongs to.

macOS lays every attached display out in **one** global coordinate space of
quartz logical points (see :mod:`gazenotes.geometry`), with the *main* display's
top-left pinned at ``(0, 0)``. Every other display is placed relative to that
origin — which means a monitor sitting to the **left of** or **above** the
built-in screen has a **negative** origin. A 2560x1440 external to the left of a
1728x1117 laptop is ``Rect(-2560, 0, 2560, 1440)``; stacked above it, it is
``Rect(0, -1440, 2560, 1440)``.

That is the trap this module exists to contain. Nothing here may assume a
non-negative origin, and nothing may assume the desktop starts at ``(0, 0)``:
the desktop is whatever :func:`global_bounds` says it is. The arrangement need
not even be rectangular — displays that meet at a corner, or are offset
vertically, leave gaps that belong to no screen at all, so the lookups return
``None`` there rather than guessing at the nearest display.

Two more facts the rest of the app must not paper over:

* **Scale is per display.** A Retina laptop beside a non-Retina external has two
  different backing scale factors at once, so :attr:`Display.scale` is carried
  per display; it is the only correct factor for cropping *that* display's
  screenshot.
* **Calibration is per display.** A gaze fit maps eye features to screen
  coordinates, so it is valid only for the screen it was taken on.
  :attr:`Display.key` is that model's key inside ``calibration.json``, and
  :func:`uncalibrated_displays` is what ``doctor`` should nag about.

Containment is half-open throughout, consistent with :meth:`Rect.contains`: a
point on the seam between two displays belongs to exactly one of them, never to
both and never to neither.

Quartz comes in through a lazy import, so this module imports and is fully
testable anywhere. Off macOS — or when Quartz misbehaves —
:func:`enumerate_displays` reports one nominal display instead of raising or
handing back an empty list, matching :class:`~gazenotes.screen.NullScreen`.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from .gaze.regress import load_calibration_entry
from .geometry import Point, Rect

log = logging.getLogger(__name__)

__all__ = [
    "Display",
    "FALLBACK_BOUNDS",
    "enumerate_displays",
    "display_for_point",
    "display_for_rect",
    "global_bounds",
    "calibrated_displays",
    "uncalibrated_displays",
]

FALLBACK_BOUNDS = Rect(0, 0, 1440, 900)
"""Nominal display used when there is no windowing system to ask.

The same size :class:`~gazenotes.screen.NullScreen` reports, so a headless run
tells one consistent story about the desktop.
"""

_MAX_DISPLAYS = 16


@dataclass(frozen=True)
class Display:
    """One attached screen, in the global quartz coordinate space."""

    display_id: int
    """``CGDirectDisplayID``. Opaque; only useful for talking back to Quartz."""

    bounds: Rect
    """Position and size in global logical points. The origin may be negative."""

    scale: float
    """Backing scale factor: pixels per logical point, 2.0 on Retina."""

    is_main: bool
    """True for the display holding the menu bar, whose top-left is ``(0, 0)``."""

    @property
    def key(self) -> str:
        """Calibration key for this screen: ``main-1728x1117``, ``display7-2560x1440``.

        The main display keeps the historical ``main-WxH`` spelling, so existing
        ``calibration.json`` files keep working. Others are keyed by their
        ``CGDirectDisplayID``, which macOS derives from the monitor's EDID
        (vendor, model, serial number) when it has one — so unplugging and
        replugging the same external, or rebooting with it attached, lands back
        on the same key and keeps its calibration. That is as stable as Quartz
        gets: the serial-number APIs are no better, since a display that reports
        no EDID (a capture dongle, some KVMs) has no stable identity at all, and
        a key whose *shape* depends on whether EDID was readable would lose
        calibrations more often than the id does.

        The resolution suffix is deliberate on both branches: a fit taken at one
        resolution does not transfer to another, so a mode change earns a fresh
        key instead of silently reusing a stale model. Rearranging displays does
        *not* change the key — the same physical screen keeps its model when you
        drag it to the other side of the desktop.
        """
        size = f"{int(round(self.bounds.w))}x{int(round(self.bounds.h))}"
        return f"main-{size}" if self.is_main else f"display{self.display_id}-{size}"


# -- enumeration --------------------------------------------------------


def enumerate_displays() -> list[Display]:
    """Every active display, main display first-class, never empty.

    Quartz is imported here rather than at module scope. Any failure —
    PyObjC missing, the display list call erroring, a display vanishing
    mid-enumeration — degrades to a single :data:`FALLBACK_BOUNDS` display, in
    keeping with the "degrade, never block" rule.
    """
    try:
        import Quartz
    except ImportError as exc:
        log.info("Quartz unavailable (%s); assuming a single nominal display", exc)
        return [_fallback_display()]
    try:
        return _enumerate_via_quartz(Quartz)
    except Exception as exc:  # noqa: BLE001 - a display query must never kill a capture
        log.warning("could not enumerate displays (%s); assuming one", exc)
        return [_fallback_display()]


def _fallback_display() -> Display:
    return Display(display_id=0, bounds=FALLBACK_BOUNDS, scale=1.0, is_main=True)


def _enumerate_via_quartz(Quartz) -> list[Display]:
    error, ids, count = Quartz.CGGetActiveDisplayList(_MAX_DISPLAYS, None, None)
    if error or not ids:
        return [_fallback_display()]
    main_id = int(Quartz.CGMainDisplayID())
    displays: list[Display] = []
    for raw in list(ids)[: int(count)]:
        display_id = int(raw)
        bounds = Quartz.CGDisplayBounds(display_id)
        rect = Rect(
            float(bounds.origin.x),
            float(bounds.origin.y),
            float(bounds.size.width),
            float(bounds.size.height),
        )
        if rect.w <= 0 or rect.h <= 0:
            continue  # a display being reconfigured while we look at it
        displays.append(
            Display(
                display_id=display_id,
                bounds=rect,
                scale=_scale_for(Quartz, display_id),
                is_main=display_id == main_id,
            )
        )
    if not displays:
        return [_fallback_display()]
    return _ensure_one_main(displays)


def _scale_for(Quartz, display_id: int) -> float:
    """Pixels per logical point for one display, 1.0 when Quartz will not say.

    Per display on purpose: a Retina laptop and a 1x external are both normal,
    and cropping either with the other's factor produces a plausible-looking
    crop of the wrong region.
    """
    try:
        mode = Quartz.CGDisplayCopyDisplayMode(display_id)
        if mode is None:
            return 1.0
        logical = float(Quartz.CGDisplayModeGetWidth(mode))
        pixels = float(Quartz.CGDisplayModeGetPixelWidth(mode))
    except Exception as exc:  # noqa: BLE001 - unknown scale is survivable, a crash is not
        log.debug("no display mode for %s (%s); assuming 1x", display_id, exc)
        return 1.0
    if logical <= 0 or pixels <= 0:
        return 1.0
    return pixels / logical


def _ensure_one_main(displays: list[Display]) -> list[Display]:
    """Guarantee exactly one main display, even if Quartz disagreed with itself."""
    mains = [d for d in displays if d.is_main]
    if len(mains) == 1:
        return displays
    if mains:
        keep = mains[0]
        return [d if d is keep else replace(d, is_main=False) for d in displays]
    # No main at all: the display anchored at the origin is the main one by
    # definition; failing that, the first one, so `key` stays well-defined.
    at_origin = next((d for d in displays if d.bounds.x == 0 and d.bounds.y == 0), displays[0])
    return [replace(d, is_main=True) if d is at_origin else d for d in displays]


# -- pure lookups -------------------------------------------------------


def display_for_point(point: Point, displays: Sequence[Display]) -> Display | None:
    """The display containing ``point``, or ``None`` if it falls in a gap.

    Half-open, so a point on a seam lands on exactly one screen. Mirrored
    displays share bounds; the main one wins so the answer stays stable.
    """
    hit: Display | None = None
    for display in displays:
        if not display.bounds.contains(point):
            continue
        if display.is_main:
            return display
        if hit is None:
            hit = display
    return hit


def display_for_rect(rect: Rect, displays: Sequence[Display]) -> Display | None:
    """The display holding the largest share of ``rect``, or ``None``.

    A window dragged across a seam lives on two screens at once; the note is
    attributed to the one showing most of it, which is the one the reader was
    almost certainly reading. Ties — a window centred exactly on the seam — go
    to the main display, then to the lowest display id, so the same layout
    always gives the same answer regardless of enumeration order.

    A degenerate (zero-area) rect has no share to compare, so it is resolved by
    its top-left corner instead.
    """
    if rect.w <= 0 or rect.h <= 0:
        return display_for_point(Point(rect.x, rect.y), displays)
    best: Display | None = None
    best_area = 0.0
    for display in displays:
        area = _overlap_area(rect, display.bounds)
        if area <= 0.0:
            continue
        if best is None or area > best_area or (area == best_area and _outranks(display, best)):
            best, best_area = display, area
    return best


def _outranks(candidate: Display, incumbent: Display) -> bool:
    """Tie-break between two displays showing equal shares of a window."""
    if candidate.is_main != incumbent.is_main:
        return candidate.is_main
    return candidate.display_id < incumbent.display_id


def _overlap_area(a: Rect, b: Rect) -> float:
    """Area of the intersection of two rects; 0.0 when they do not overlap.

    Written with min/max on the absolute edges rather than on widths, because
    negative origins make any width-relative shortcut wrong.
    """
    width = min(a.right, b.right) - max(a.x, b.x)
    height = min(a.bottom, b.bottom) - max(a.y, b.y)
    if width <= 0.0 or height <= 0.0:
        return 0.0
    return width * height


def global_bounds(displays: Sequence[Display]) -> Rect:
    """The union rectangle of the whole desktop.

    Its origin is negative whenever a display sits left of or above the main
    one, and it covers gaps in a non-rectangular arrangement — it is a bounding
    box, not the set of visible pixels. Use it to clamp things that must stay
    somewhere on the desktop, not to decide whether a point is on a screen
    (that is :func:`display_for_point`).
    """
    rects = [d.bounds for d in displays]
    if not rects:
        return FALLBACK_BOUNDS
    left = min(r.x for r in rects)
    top = min(r.y for r in rects)
    right = max(r.right for r in rects)
    bottom = max(r.bottom for r in rects)
    return Rect(left, top, right - left, bottom - top)


# -- calibration coverage -----------------------------------------------


def calibrated_displays(
    calibration_path: Path | str | None,
    displays: Sequence[Display],
) -> list[Display]:
    """Displays that already have a gaze model stored under their :attr:`Display.key`."""
    return [d for d in displays if _has_calibration(calibration_path, d)]


def uncalibrated_displays(
    calibration_path: Path | str | None,
    displays: Sequence[Display],
) -> list[Display]:
    """Displays still needing ``gazenotes calibrate``.

    A missing, unreadable or corrupt calibration file is not an error here: it
    means nothing is calibrated yet, which is exactly what a first run looks
    like.
    """
    return [d for d in displays if not _has_calibration(calibration_path, d)]


def _has_calibration(calibration_path: Path | str | None, display: Display) -> bool:
    if calibration_path is None:
        return False
    try:
        return load_calibration_entry(calibration_path, display.key) is not None
    except Exception as exc:  # noqa: BLE001 - an odd path must not break `doctor`
        log.warning("could not read calibration %s (%s)", calibration_path, exc)
        return False
