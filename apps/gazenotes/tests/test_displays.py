"""Multi-display geometry. A monitor to the left of the laptop has a negative
origin, and every sign error in this file is a note filed against the wrong
screen or cropped out of the wrong screenshot — so the negative layouts get as
much attention as the easy one."""

from __future__ import annotations

import sys
import types

import pytest

from gazenotes.displays import (
    FALLBACK_BOUNDS,
    Display,
    calibrated_displays,
    display_for_point,
    display_for_rect,
    enumerate_displays,
    global_bounds,
    uncalibrated_displays,
)
from gazenotes.gaze.regress import RidgeModel, save_calibration
from gazenotes.geometry import Point, Rect

# The built-in screen: main, therefore anchored at the origin, and Retina.
LAPTOP = Display(display_id=1, bounds=Rect(0, 0, 1728, 1117), scale=2.0, is_main=True)
# Same physical external monitor, placed on three different sides of it.
RIGHT = Display(display_id=7, bounds=Rect(1728, 0, 2560, 1440), scale=1.0, is_main=False)
LEFT = Display(display_id=7, bounds=Rect(-2560, 0, 2560, 1440), scale=1.0, is_main=False)
ABOVE = Display(display_id=7, bounds=Rect(0, -1440, 2560, 1440), scale=1.0, is_main=False)


def _model() -> RidgeModel:
    """A trivially small stand-in fit; only its round-tripping matters here."""
    return RidgeModel(coef_x=[0.0, 1.0], coef_y=[0.0, 1.0], feature_names=["f"], residual_px=42.0)


# -- keys ---------------------------------------------------------------


def test_main_display_keeps_the_historical_calibration_key():
    # daemon.display_key() has always written "main-WxH"; existing
    # calibration.json files must keep resolving after this module lands.
    assert LAPTOP.key == "main-1728x1117"


def test_secondary_display_is_keyed_by_display_id_and_size():
    assert RIGHT.key == "display7-2560x1440"


def test_the_key_survives_rearranging_the_same_monitor():
    # Dragging the external from the right of the laptop to the left of it is
    # not a new monitor: the calibration must follow it, negative origin and all.
    assert LEFT.key == RIGHT.key == ABOVE.key


def test_a_resolution_change_earns_a_new_key():
    # A fit taken at 2560x1440 does not transfer to 1920x1080, so the key has to
    # change rather than silently reusing a stale model.
    scaled_down = Display(display_id=7, bounds=Rect(1728, 0, 1920, 1080), scale=1.0, is_main=False)
    assert scaled_down.key != RIGHT.key


def test_key_rounds_fractional_bounds_to_whole_points():
    odd = Display(display_id=3, bounds=Rect(0, 0, 1727.6, 1117.4), scale=2.0, is_main=False)
    assert odd.key == "display3-1728x1117"


# -- enumeration --------------------------------------------------------


def test_enumerate_falls_back_to_one_display_without_quartz(monkeypatch):
    # Linux, or macOS without PyObjC: a single nominal display beats an empty
    # list, which every caller would then have to special-case.
    monkeypatch.setitem(sys.modules, "Quartz", None)  # import Quartz -> ImportError
    displays = enumerate_displays()
    assert len(displays) == 1
    assert displays[0].is_main
    assert displays[0].bounds == FALLBACK_BOUNDS
    assert displays[0].scale == 1.0


def _fake_quartz(layout, *, main_id, list_error=0, mode_raises=False):
    """A stand-in Quartz exposing only the five calls enumeration makes.

    ``layout`` maps display id -> (Rect, logical width, pixel width).
    """
    module = types.ModuleType("Quartz")

    def bounds_for(display_id):
        rect = layout[display_id][0]
        return types.SimpleNamespace(
            origin=types.SimpleNamespace(x=rect.x, y=rect.y),
            size=types.SimpleNamespace(width=rect.w, height=rect.h),
        )

    def copy_mode(display_id):
        if mode_raises:
            raise RuntimeError("display reconfigured")
        return display_id

    module.CGGetActiveDisplayList = lambda cap, _a, _b: (list_error, list(layout)[:cap], len(layout))
    module.CGMainDisplayID = lambda: main_id
    module.CGDisplayBounds = bounds_for
    module.CGDisplayCopyDisplayMode = copy_mode
    module.CGDisplayModeGetWidth = lambda mode: layout[mode][1]
    module.CGDisplayModeGetPixelWidth = lambda mode: layout[mode][2]
    return module


def test_enumerate_reads_bounds_scale_and_mainness_from_quartz(monkeypatch):
    layout = {
        1: (Rect(0, 0, 1728, 1117), 1728, 3456),  # Retina built-in
        7: (Rect(-2560, 0, 2560, 1440), 2560, 2560),  # 1x external, to the LEFT
    }
    monkeypatch.setitem(sys.modules, "Quartz", _fake_quartz(layout, main_id=1))
    built_in, external = enumerate_displays()
    assert (built_in.is_main, built_in.scale) == (True, 2.0)
    assert (external.is_main, external.scale) == (False, 1.0)
    assert external.bounds.x == -2560  # the negative origin survives the trip


def test_enumerate_falls_back_when_quartz_reports_an_error(monkeypatch):
    layout = {1: (Rect(0, 0, 1728, 1117), 1728, 3456)}
    monkeypatch.setitem(sys.modules, "Quartz", _fake_quartz(layout, main_id=1, list_error=1000))
    assert enumerate_displays() == [
        Display(display_id=0, bounds=FALLBACK_BOUNDS, scale=1.0, is_main=True)
    ]


def test_enumerate_assumes_1x_when_the_display_mode_is_unreadable(monkeypatch):
    # A display can be reconfigured mid-enumeration. Losing the scale factor
    # degrades a crop; raising would lose the whole note.
    layout = {1: (Rect(0, 0, 1728, 1117), 1728, 3456)}
    monkeypatch.setitem(sys.modules, "Quartz", _fake_quartz(layout, main_id=1, mode_raises=True))
    (display,) = enumerate_displays()
    assert display.scale == 1.0
    assert display.bounds.w == 1728


def test_enumerate_names_a_main_display_even_if_quartz_names_none(monkeypatch):
    # CGMainDisplayID pointing at a display that is no longer in the active list
    # must still leave exactly one main, or `key` stops being well defined.
    layout = {
        7: (Rect(0, 0, 2560, 1440), 2560, 2560),
        9: (Rect(2560, 0, 1920, 1080), 1920, 1920),
    }
    monkeypatch.setitem(sys.modules, "Quartz", _fake_quartz(layout, main_id=99))
    displays = enumerate_displays()
    assert [d.is_main for d in displays] == [True, False]  # the one at the origin


def test_enumerate_skips_a_display_with_no_area(monkeypatch):
    layout = {
        1: (Rect(0, 0, 1728, 1117), 1728, 3456),
        7: (Rect(1728, 0, 0, 0), 0, 0),  # mid-reconfiguration
    }
    monkeypatch.setitem(sys.modules, "Quartz", _fake_quartz(layout, main_id=1))
    assert [d.display_id for d in enumerate_displays()] == [1]


# -- display_for_point --------------------------------------------------


def test_point_lands_on_the_external_to_the_right():
    displays = [LAPTOP, RIGHT]
    assert display_for_point(Point(3000, 700), displays) is RIGHT
    assert display_for_point(Point(800, 500), displays) is LAPTOP


def test_a_point_on_the_shared_edge_belongs_to_exactly_one_display():
    # Half-open, like Rect.contains: x=1728 is the external's first column, not
    # the laptop's last. Never both, never neither.
    displays = [LAPTOP, RIGHT]
    assert display_for_point(Point(1728, 500), displays) is RIGHT
    assert display_for_point(Point(1727.5, 500), displays) is LAPTOP


def test_negative_x_resolves_to_the_display_on_the_left():
    # The single easiest thing to get wrong: everything left of the main display
    # has a negative x, and a naive `abs` or clamp would file it on the laptop.
    displays = [LAPTOP, LEFT]
    assert display_for_point(Point(-1, 500), displays) is LEFT
    assert display_for_point(Point(-2560, 0), displays) is LEFT  # inclusive left edge
    assert display_for_point(Point(0, 0), displays) is LAPTOP  # exclusive right edge


def test_negative_y_resolves_to_the_display_above():
    displays = [LAPTOP, ABOVE]
    assert display_for_point(Point(400, -1), displays) is ABOVE
    assert display_for_point(Point(400, -1440), displays) is ABOVE  # inclusive top edge
    assert display_for_point(Point(400, -1441), displays) is None  # above the desktop
    assert display_for_point(Point(400, 0), displays) is LAPTOP


def test_a_point_in_the_gap_of_a_staggered_layout_belongs_to_no_display():
    # Displays offset vertically leave a real hole in the global space. Guessing
    # the nearest screen would attribute a note to a monitor the user was not
    # looking at, so the answer is None and the caller degrades.
    offset = Display(display_id=7, bounds=Rect(1728, 600, 2560, 1440), scale=1.0, is_main=False)
    assert display_for_point(Point(2000, 100), [LAPTOP, offset]) is None


def test_a_point_off_the_desktop_entirely_is_none():
    assert display_for_point(Point(99999, 99999), [LAPTOP, RIGHT]) is None


def test_no_displays_means_no_answer_rather_than_an_exception():
    assert display_for_point(Point(0, 0), []) is None
    assert display_for_rect(Rect(0, 0, 10, 10), []) is None


def test_mirrored_displays_resolve_to_the_main_one():
    # Mirroring gives two displays identical bounds; without a rule the answer
    # would depend on enumeration order, and so would the calibration key used.
    mirror = Display(display_id=7, bounds=LAPTOP.bounds, scale=1.0, is_main=False)
    assert display_for_point(Point(10, 10), [mirror, LAPTOP]) is LAPTOP
    assert display_for_point(Point(10, 10), [LAPTOP, mirror]) is LAPTOP


def test_scale_stays_attached_to_its_own_display():
    # Retina laptop + 1x external: the lookup must hand back the external's 1.0,
    # or every crop taken over there is half the intended region.
    displays = [LAPTOP, RIGHT]
    assert display_for_point(Point(3000, 700), displays).scale == 1.0
    assert display_for_point(Point(800, 500), displays).scale == 2.0


# -- display_for_rect ---------------------------------------------------


def test_a_window_wholly_on_one_display_is_attributed_to_it():
    window = Rect(2000, 200, 800, 600)
    assert display_for_rect(window, [LAPTOP, RIGHT]) is RIGHT


def test_a_straddling_window_goes_to_the_display_showing_most_of_it():
    # 300pt of the window on the laptop, 700pt on the external.
    window = Rect(1428, 300, 1000, 600)
    assert display_for_rect(window, [LAPTOP, RIGHT]) is RIGHT


def test_a_straddling_window_mostly_on_the_laptop_stays_on_the_laptop():
    window = Rect(1028, 300, 1000, 600)  # 700pt laptop, 300pt external
    assert display_for_rect(window, [LAPTOP, RIGHT]) is LAPTOP


def test_a_window_straddling_the_seam_at_a_negative_origin():
    # Same test mirrored across x=0: 700pt on the LEFT-hand external, 300 on the
    # laptop. A sign error in the overlap maths shows up here and nowhere else.
    window = Rect(-700, 300, 1000, 600)
    assert display_for_rect(window, [LAPTOP, LEFT]) is LEFT


def test_an_evenly_split_window_resolves_to_the_main_display():
    # Exactly 50/50 on the seam. The tie has to break the same way every time,
    # whatever order the displays were enumerated in, or a window nudged one
    # pixel would flip which screen's calibration is credited.
    window = Rect(1228, 300, 1000, 600)
    assert display_for_rect(window, [LAPTOP, RIGHT]) is LAPTOP
    assert display_for_rect(window, [RIGHT, LAPTOP]) is LAPTOP


def test_an_evenly_split_window_between_two_externals_breaks_on_display_id():
    # No main display involved: fall back to the lowest id, which is at least
    # stable across enumerations.
    left = Display(display_id=9, bounds=Rect(-2560, 0, 2560, 1440), scale=1.0, is_main=False)
    right = Display(display_id=7, bounds=Rect(0, 0, 2560, 1440), scale=1.0, is_main=False)
    window = Rect(-500, 100, 1000, 600)
    assert display_for_rect(window, [left, right]) is right
    assert display_for_rect(window, [right, left]) is right


def test_a_window_that_touches_no_display_is_none():
    assert display_for_rect(Rect(9000, 9000, 400, 300), [LAPTOP, RIGHT]) is None


def test_a_window_only_touching_an_edge_does_not_count_as_overlap():
    # Zero-area intersection is not presence on that screen.
    assert display_for_rect(Rect(1728, 0, 400, 300), [LAPTOP]) is None


def test_a_zero_area_window_is_resolved_by_its_origin():
    # Some apps report a collapsed window rect; falling back to the corner beats
    # returning None and losing the app context.
    assert display_for_rect(Rect(3000, 700, 0, 0), [LAPTOP, RIGHT]) is RIGHT
    assert display_for_rect(Rect(-10, 700, 0, 0), [LAPTOP, LEFT]) is LEFT


# -- global_bounds ------------------------------------------------------


def test_global_bounds_of_a_single_display_is_that_display():
    assert global_bounds([LAPTOP]) == LAPTOP.bounds


def test_global_bounds_spans_a_laptop_and_an_external_to_the_right():
    union = global_bounds([LAPTOP, RIGHT])
    assert (union.x, union.y) == (0, 0)
    assert (union.w, union.h) == (4288, 1440)


def test_global_bounds_has_a_negative_origin_when_a_display_is_left_or_above():
    # The desktop does NOT start at (0, 0): the main display's top-left does.
    union = global_bounds([LAPTOP, LEFT, ABOVE])
    assert (union.x, union.y) == (-2560, -1440)
    assert union.right == 2560
    assert union.bottom == 1440


def test_global_bounds_covers_every_display_it_was_given():
    displays = [LAPTOP, LEFT, ABOVE]
    union = global_bounds(displays)
    for display in displays:
        assert union.x <= display.bounds.x and union.right >= display.bounds.right
        assert union.y <= display.bounds.y and union.bottom >= display.bounds.bottom


def test_global_bounds_of_nothing_degrades_instead_of_raising():
    assert global_bounds([]) == FALLBACK_BOUNDS


# -- calibration coverage -----------------------------------------------


def test_calibrated_and_uncalibrated_split_a_real_calibration_file(tmp_path):
    path = tmp_path / "calibration.json"
    save_calibration(path, LAPTOP.key, _model())
    displays = [LAPTOP, RIGHT]
    assert calibrated_displays(path, displays) == [LAPTOP]
    assert uncalibrated_displays(path, displays) == [RIGHT]


def test_calibrating_the_external_does_not_disturb_the_laptop(tmp_path):
    path = tmp_path / "calibration.json"
    save_calibration(path, LAPTOP.key, _model())
    save_calibration(path, RIGHT.key, _model())
    assert calibrated_displays(path, [LAPTOP, RIGHT]) == [LAPTOP, RIGHT]
    assert uncalibrated_displays(path, [LAPTOP, RIGHT]) == []


def test_a_rearranged_monitor_keeps_its_calibration(tmp_path):
    # Calibrated while on the right; still calibrated after being dragged to the
    # left, where its origin turns negative.
    path = tmp_path / "calibration.json"
    save_calibration(path, RIGHT.key, _model())
    assert calibrated_displays(path, [LEFT]) == [LEFT]


def test_every_display_is_uncalibrated_before_the_file_exists(tmp_path):
    path = tmp_path / "calibration.json"
    assert calibrated_displays(path, [LAPTOP, RIGHT]) == []
    assert uncalibrated_displays(path, [LAPTOP, RIGHT]) == [LAPTOP, RIGHT]


def test_a_corrupt_calibration_file_reads_as_uncalibrated(tmp_path):
    # Truncated by a crash mid-write. `doctor` should say "run calibrate",
    # not traceback.
    path = tmp_path / "calibration.json"
    path.write_text('{"main-1728x1117": {"coef_x": [1.0]', encoding="utf-8")
    assert calibrated_displays(path, [LAPTOP]) == []


def test_no_calibration_path_configured_means_nothing_is_calibrated():
    assert calibrated_displays(None, [LAPTOP, RIGHT]) == []
    assert uncalibrated_displays(None, [LAPTOP, RIGHT]) == [LAPTOP, RIGHT]


@pytest.mark.parametrize("displays", [[], [LAPTOP], [LAPTOP, RIGHT], [LAPTOP, LEFT, ABOVE]])
def test_the_two_coverage_lists_always_partition_the_displays(tmp_path, displays):
    path = tmp_path / "calibration.json"
    save_calibration(path, LAPTOP.key, _model())
    covered = calibrated_displays(path, displays)
    missing = uncalibrated_displays(path, displays)
    assert len(covered) + len(missing) == len(displays)
    assert not set(map(id, covered)) & set(map(id, missing))
