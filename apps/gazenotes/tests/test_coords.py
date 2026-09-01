"""Coordinate-system conversions. These are the bugs that silently misplace
every crop, so they get exhaustive tests."""

from __future__ import annotations

import pytest

from gazenotes.geometry import (
    Point,
    Rect,
    cocoa_to_quartz_y,
    gaze_crop_rect,
    logical_rect_to_pixels,
    quartz_to_cocoa_y,
    screen_to_window,
    window_to_viewport,
)

SCREEN = Rect(0, 0, 1728, 1117)


def test_cocoa_quartz_round_trip():
    display_height = 1117.0
    for y, h in [(0, 100), (500, 300), (1017, 100)]:
        flipped = cocoa_to_quartz_y(y, h, display_height)
        assert quartz_to_cocoa_y(flipped, h, display_height) == pytest.approx(y)


def test_cocoa_bottom_left_window_maps_to_quartz_bottom():
    # A 100pt-tall window sitting on the bottom edge in Cocoa (y=0) has its
    # Quartz top edge one window-height above the bottom of the display.
    assert cocoa_to_quartz_y(0, 100, 1117) == 1017


def test_logical_rect_to_pixels_retina():
    rect = logical_rect_to_pixels(Rect(10, 20, 100, 50), 2.0)
    assert (rect.x, rect.y, rect.w, rect.h) == (20, 40, 200, 100)


def test_screen_to_window_subtracts_origin():
    local = screen_to_window(Point(500, 400), Rect(100, 60, 800, 600))
    assert (local.x, local.y) == (400, 340)


def test_window_to_viewport_removes_browser_chrome():
    viewport = window_to_viewport(Point(500, 400), Rect(100, 60, 1200, 900), chrome_height=87)
    assert (viewport.x, viewport.y) == (400, 253)


def test_window_to_viewport_can_report_a_point_in_the_chrome():
    # Looking at the omnibox yields a negative viewport y; the caller rejects it
    # rather than clamping it into the page.
    viewport = window_to_viewport(Point(500, 80), Rect(100, 60, 1200, 900), chrome_height=87)
    assert viewport.y < 0


def test_gaze_crop_is_full_width_and_the_requested_fraction():
    crop = gaze_crop_rect(Point(864, 558), SCREEN, 0.35)
    assert crop.w == SCREEN.w
    assert crop.h == pytest.approx(SCREEN.h * 0.35)
    assert crop.y + crop.h / 2 == pytest.approx(558)


@pytest.mark.parametrize("gaze_y", [0, 5, 1100, 1117])
def test_gaze_crop_stays_on_screen_at_the_edges(gaze_y):
    crop = gaze_crop_rect(Point(864, gaze_y), SCREEN, 0.35)
    assert crop.y >= SCREEN.y
    assert crop.bottom <= SCREEN.bottom + 1e-9
    assert crop.h == pytest.approx(SCREEN.h * 0.35)


def test_gaze_crop_of_the_whole_screen_is_the_screen():
    crop = gaze_crop_rect(Point(0, 0), SCREEN, 1.0)
    assert (crop.x, crop.y, crop.w, crop.h) == (0, 0, 1728, 1117)


def test_gaze_crop_rejects_a_nonsense_fraction():
    for fraction in (0.0, -0.2, 1.5):
        with pytest.raises(ValueError):
            gaze_crop_rect(Point(10, 10), SCREEN, fraction)


def test_rect_contains_is_half_open():
    rect = Rect(0, 0, 10, 10)
    assert rect.contains(Point(0, 0))
    assert not rect.contains(Point(10, 5))
    assert not rect.contains(Point(5, 10))


def test_clamp_shrinks_a_rect_larger_than_its_container():
    clamped = Rect(-50, -50, 3000, 3000).clamped_to(SCREEN)
    assert (clamped.x, clamped.y, clamped.w, clamped.h) == (0, 0, 1728, 1117)


def test_secondary_display_origin_is_respected():
    # An external monitor to the right of the built-in one has a non-zero origin.
    external = Rect(1728, 0, 2560, 1440)
    crop = gaze_crop_rect(Point(3000, 700), external, 0.35)
    assert crop.x == 1728
    assert crop.y >= 0
    assert crop.bottom <= external.bottom
