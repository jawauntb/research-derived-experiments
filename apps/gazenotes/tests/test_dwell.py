"""Dwell scrolling: what earns a scroll, and — mostly — what must not."""

from __future__ import annotations

import pytest

from gazenotes.dwell import DwellConfig, DwellDriver, DwellScroller
from gazenotes.events import GazeSample
from gazenotes.geometry import Rect

SCREEN = Rect(0, 0, 1728, 1117)
BAND = SCREEN.h * DwellConfig().zone_fraction  # 167.55 pt
TOP_Y = 40.0
MIDDLE_Y = 550.0
BOTTOM_Y = 1050.0


def gaze(t0: float, seconds: float, y: float, *, x: float = 864.0, confidence: float = 0.9, hz: float = 30.0):
    """A run of samples at 30 Hz, the rate the camera thread actually produces."""
    count = max(1, int(round(seconds * hz)))
    return [GazeSample(t0 + i / hz, x, y, confidence) for i in range(count)]


def blind(t0: float, seconds: float, hz: float = 30.0):
    """Frames where the face was lost: present in the buffer, confidence zero."""
    return [GazeSample(t0 + i / hz, 0.0, 0.0, 0.0) for i in range(max(1, int(round(seconds * hz))))]


def last_t(samples) -> float:
    return samples[-1].t


# -- the basic gesture --------------------------------------------------
def test_a_sustained_dwell_in_the_bottom_zone_scrolls_forward():
    samples = gaze(0.0, 0.5, BOTTOM_Y)
    decision = DwellScroller().decide(samples, SCREEN, last_t(samples))
    assert decision is not None
    assert decision.scroll == 400.0  # positive = content up, like page.mouse.wheel
    assert "bottom" in decision.reason


def test_a_sustained_dwell_in_the_top_zone_scrolls_back():
    samples = gaze(0.0, 0.5, TOP_Y)
    decision = DwellScroller().decide(samples, SCREEN, last_t(samples))
    assert decision is not None
    assert decision.scroll == -400.0


def test_gaze_resting_in_the_middle_of_the_screen_never_scrolls():
    samples = gaze(0.0, 3.0, MIDDLE_Y)
    assert DwellScroller().decide(samples, SCREEN, last_t(samples)) is None


# -- what must NOT fire -------------------------------------------------
def test_one_stray_sample_in_the_bottom_band_does_not_scroll():
    # The difference between usable and infuriating: a saccade to the bottom of
    # the window lasts a frame or two, and webcam gaze puts stray points there
    # on its own. Requiring a *sustained* dwell is the whole point.
    samples = gaze(0.0, 1.0, MIDDLE_Y) + [GazeSample(1.0, 864.0, BOTTOM_Y, 0.9)]
    assert DwellScroller().decide(samples, SCREEN, 1.0) is None


def test_an_excursion_shorter_than_the_dwell_does_not_scroll():
    samples = gaze(0.0, 1.0, MIDDLE_Y) + gaze(1.0, 0.3, BOTTOM_Y)
    assert DwellScroller().decide(samples, SCREEN, last_t(samples)) is None


def test_a_dwell_interrupted_by_a_look_away_restarts_the_clock():
    scroller = DwellScroller()
    # 0.3 s down, a glance back at the text, 0.3 s down again: 0.7 s in the band
    # in total, but never 0.4 s continuously.
    samples = gaze(0.0, 0.3, BOTTOM_Y) + gaze(0.3, 0.1, MIDDLE_Y) + gaze(0.4, 0.3, BOTTOM_Y)
    assert scroller.decide(samples, SCREEN, last_t(samples)) is None
    # Keep looking, and the restarted clock does eventually run out.
    samples += gaze(0.7, 0.3, BOTTOM_Y)
    assert scroller.decide(samples, SCREEN, last_t(samples)) is not None


def test_an_empty_sample_window_is_not_a_dwell():
    assert DwellScroller().decide([], SCREEN, 12.0) is None


def test_a_stale_buffer_does_not_scroll():
    # The camera thread stopped (paused, crashed, machine slept). The last
    # second of samples still sits in the ring buffer and is all in the zone;
    # firing off frozen history would scroll the page minutes later.
    samples = gaze(0.0, 1.0, BOTTOM_Y)
    assert DwellScroller().decide(samples, SCREEN, last_t(samples) + 5.0) is None


# -- confidence ---------------------------------------------------------
def test_low_confidence_samples_never_scroll():
    # A lost face reads as a plausible-looking point; if it lands in the band it
    # must not move the page.
    samples = gaze(0.0, 2.0, BOTTOM_Y, confidence=0.2)
    assert DwellScroller().decide(samples, SCREEN, last_t(samples)) is None


def test_confidence_exactly_at_the_threshold_counts():
    config = DwellConfig()
    samples = gaze(0.0, 0.5, BOTTOM_Y, confidence=config.min_confidence)
    assert DwellScroller(config).decide(samples, SCREEN, last_t(samples)) is not None


def test_a_blink_in_the_middle_of_a_dwell_does_not_reset_it():
    # Blinks are 100–200 ms and land inside most 400 ms dwells. If every blink
    # restarted the clock the feature could essentially never fire.
    samples = gaze(0.0, 0.3, BOTTOM_Y) + blind(0.3, 0.1) + gaze(0.4, 0.3, BOTTOM_Y)
    decision = DwellScroller().decide(samples, SCREEN, last_t(samples))
    assert decision is not None
    assert decision.scroll > 0


def test_a_long_dropout_resets_the_dwell_like_a_look_away():
    # Half a second with no face is not a blink; it is someone turning to talk
    # to a colleague, and what happened during it is unknown.
    samples = gaze(0.0, 0.5, BOTTOM_Y) + blind(0.5, 0.5) + gaze(1.0, 0.3, BOTTOM_Y)
    assert DwellScroller().decide(samples, SCREEN, last_t(samples)) is None


def test_a_dwell_ending_on_a_lost_face_does_not_scroll():
    samples = gaze(0.0, 1.0, BOTTOM_Y) + blind(1.0, 0.1)
    assert DwellScroller().decide(samples, SCREEN, last_t(samples)) is None


# -- cooldown and the anti-runaway latch --------------------------------
def test_the_cooldown_blocks_a_second_scroll_and_then_expires():
    scroller = DwellScroller()
    first = gaze(0.0, 0.5, BOTTOM_Y)
    assert scroller.decide(first, SCREEN, last_t(first)) is not None
    assert scroller.cooldown_remaining(last_t(first)) > 1.0

    # Glance back at the text, then dwell again — a legitimate second request,
    # but it arrives 0.8 s in, inside the 1.5 s cooldown.
    samples = first + gaze(0.5, 0.2, MIDDLE_Y) + gaze(0.7, 0.6, BOTTOM_Y)
    assert scroller.decide(samples, SCREEN, last_t(samples)) is None

    # Still looking once the cooldown has run out: now it fires.
    samples += gaze(1.3, 0.9, BOTTOM_Y)
    assert last_t(samples) > 2.0  # past cooldown_seconds
    assert scroller.decide(samples, SCREEN, last_t(samples)) is not None


def test_a_continuous_stare_scrolls_once_and_then_stops():
    # Someone resting their eyes at the end of a paragraph while thinking. The
    # dwell is genuine and never breaks, so a plain "dwell, cool down, dwell
    # again" rule would page the document away under them every 1.9 s.
    scroller = DwellScroller()
    samples = gaze(0.0, 0.5, BOTTOM_Y)
    assert scroller.decide(samples, SCREEN, last_t(samples)) is not None
    for extra in range(1, 20):  # ~7 s of unbroken staring, well past the cooldown
        samples += gaze(0.5 * extra, 0.5, BOTTOM_Y)
        assert scroller.decide(samples, SCREEN, last_t(samples)) is None


def test_looking_away_and_back_re_arms_the_same_zone():
    scroller = DwellScroller()
    samples = gaze(0.0, 0.5, BOTTOM_Y)
    assert scroller.decide(samples, SCREEN, last_t(samples)) is not None
    samples += gaze(0.5, 1.7, MIDDLE_Y)  # reading again; also outlasts the cooldown
    assert scroller.decide(samples, SCREEN, last_t(samples)) is None
    samples += gaze(2.2, 0.5, BOTTOM_Y)
    assert scroller.decide(samples, SCREEN, last_t(samples)) is not None


def test_the_other_zone_is_not_latched_by_a_scroll():
    # Scrolling down then wanting to go back is a normal correction; only the
    # zone that fired is held.
    scroller = DwellScroller()
    samples = gaze(0.0, 0.5, BOTTOM_Y)
    assert scroller.decide(samples, SCREEN, last_t(samples)) is not None
    samples += gaze(0.5, 1.6, TOP_Y)  # past the 1.5 s cooldown
    decision = scroller.decide(samples, SCREEN, last_t(samples))
    assert decision is not None
    assert decision.scroll < 0


def test_reset_clears_the_cooldown_and_the_latch():
    scroller = DwellScroller()
    samples = gaze(0.0, 0.5, BOTTOM_Y)
    assert scroller.decide(samples, SCREEN, last_t(samples)) is not None
    scroller.reset()
    assert scroller.cooldown_remaining(last_t(samples)) == 0.0
    assert scroller.decide(samples, SCREEN, last_t(samples)) is not None


# -- zone geometry ------------------------------------------------------
def test_the_bottom_zone_includes_its_top_edge_and_excludes_the_screen_edge():
    # Rect.contains is half-open, so the band owns its upper edge and the screen
    # bottom belongs to the neighbour. Dwell must not invent its own convention.
    scroller = DwellScroller()
    on_edge = gaze(0.0, 0.5, SCREEN.bottom - BAND)
    assert scroller.decide(on_edge, SCREEN, last_t(on_edge)) is not None
    past_edge = gaze(0.0, 0.5, SCREEN.bottom)
    assert DwellScroller().decide(past_edge, SCREEN, last_t(past_edge)) is None


def test_the_top_zone_includes_the_screen_origin_and_excludes_its_lower_edge():
    at_origin = gaze(0.0, 0.5, SCREEN.y)
    assert DwellScroller().decide(at_origin, SCREEN, last_t(at_origin)) is not None
    below = gaze(0.0, 0.5, SCREEN.y + BAND)
    assert DwellScroller().decide(below, SCREEN, last_t(below)) is None


def test_gaze_beside_the_screen_is_not_in_a_zone():
    # x is checked as well as y: a point off to the side of the display sits at
    # the right height but is not on the page.
    samples = gaze(0.0, 1.0, BOTTOM_Y, x=SCREEN.right + 50)
    assert DwellScroller().decide(samples, SCREEN, last_t(samples)) is None


def test_zones_follow_a_screen_with_a_non_zero_origin():
    # An external display: quartz puts it beside (and often above) the main one,
    # so both origin coordinates are non-zero and one is negative.
    external = Rect(1728, -300, 2560, 1440)
    band = external.h * DwellConfig().zone_fraction
    scroller = DwellScroller()
    inside = gaze(0.0, 0.5, external.bottom - band / 2, x=external.x + 100)
    decision = scroller.decide(inside, external, last_t(inside))
    assert decision is not None
    assert decision.scroll > 0
    # The main display's bottom band is nowhere near the external screen's.
    main_bottom = gaze(2.0, 0.5, BOTTOM_Y)
    assert DwellScroller().decide(main_bottom, external, last_t(main_bottom)) is None


def test_a_taller_zone_fraction_catches_gaze_a_plain_band_would_miss():
    samples = gaze(0.0, 0.5, SCREEN.h * 0.7)
    assert DwellScroller().decide(samples, SCREEN, last_t(samples)) is None
    generous = DwellScroller(DwellConfig(zone_fraction=0.4))
    assert generous.decide(samples, SCREEN, last_t(samples)) is not None


# -- config -------------------------------------------------------------
def test_config_rejects_zones_that_would_overlap():
    with pytest.raises(ValueError):
        DwellConfig(zone_fraction=0.75)
    with pytest.raises(ValueError):
        DwellConfig(zone_fraction=0.0)


def test_config_rejects_a_zero_dwell():
    with pytest.raises(ValueError):
        DwellConfig(dwell_seconds=0.0)


# -- the driver ---------------------------------------------------------
class FakeBuffer:
    def __init__(self, samples=()):
        self.samples = list(samples)

    def snapshot(self):
        return list(self.samples)


class FakeGaze:
    def __init__(self, samples=()):
        self.buffer = FakeBuffer(samples)


def test_a_default_driver_is_inert():
    # Off by default: constructing one, and even calling start(), must not
    # scroll anything. The user has to ask for this feature.
    scrolls: list[float] = []
    driver = DwellDriver(gaze=FakeGaze(gaze(0.0, 1.0, BOTTOM_Y)), screen=SCREEN, scroll=scrolls.append)
    assert driver.enabled is False
    assert driver.start() == "dwell scrolling is off"
    assert driver.running is False
    assert driver.poll(now=1.0) is None
    assert scrolls == []


def test_an_enabled_driver_scrolls_through_the_injected_callable():
    scrolls: list[float] = []
    samples = gaze(0.0, 0.5, BOTTOM_Y)
    driver = DwellDriver(
        gaze=FakeGaze(samples), screen=SCREEN, scroll=scrolls.append, enabled=True
    )
    assert driver.poll(now=last_t(samples)) is not None
    assert scrolls == [400.0]
    # The cooldown lives in the scroller, so a second poll changes nothing.
    assert driver.poll(now=last_t(samples)) is None
    assert scrolls == [400.0]


def test_the_toggle_starts_and_stops_the_thread():
    driver = DwellDriver(gaze=FakeGaze(), screen=SCREEN, scroll=lambda _amount: None, interval=0.01)
    assert driver.toggle() == "dwell scrolling on"
    assert driver.running is True
    assert driver.toggle() == "dwell scrolling off"
    assert driver.running is False


def test_the_driver_never_raises_when_the_gaze_engine_misbehaves():
    # Degrade, never block: a broken camera path must not kill the daemon.
    class Exploding:
        def __init__(self):
            self.buffer = self

        def snapshot(self):
            raise RuntimeError("camera went away")

    scrolls: list[float] = []
    driver = DwellDriver(gaze=Exploding(), screen=SCREEN, scroll=scrolls.append, enabled=True)
    assert driver.poll(now=1.0) is None
    assert scrolls == []
    # No gaze engine at all, and no scroll target, are both quiet no-ops.
    assert DwellDriver(screen=SCREEN, enabled=True).poll(now=1.0) is None
    assert DwellDriver(gaze=FakeGaze(), enabled=True).start() == "dwell scrolling has nothing to scroll"


def test_stopping_a_driver_that_never_started_is_harmless():
    driver = DwellDriver()
    assert driver.stop() == "dwell scrolling off"
    assert driver.running is False
