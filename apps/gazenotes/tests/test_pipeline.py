"""End-to-end capture: a spoken note becomes a written entry.

Collaborators are fakes, so this exercises the real ordering, fallbacks and
degradation rules without macOS, a camera, or Chrome.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from gazenotes.config import Config
from gazenotes.events import AppContext, BrowserContext, Fixation, NoteEvent
from gazenotes.geometry import Rect
from gazenotes.notes import DailyNotes
from gazenotes.pipeline import NoteProcessor

SCREEN = Rect(0, 0, 1728, 1117)
WHEN = datetime(2026, 9, 1, 14, 30, 22)


class FakeScreen:
    """Records the order of calls: screenshot must come first."""

    def __init__(self, app=None, fail_capture=False, fail_crop=False):
        self.app = app or AppContext("Google Chrome", "com.google.Chrome", "Some Page", (0, 25, 1728, 1092))
        self.calls: list[str] = []
        self.fail_capture = fail_capture
        self.fail_crop = fail_crop

    def main_display(self):
        return SCREEN

    def backing_scale(self):
        return 2.0

    def frontmost(self):
        self.calls.append("frontmost")
        return self.app

    def capture_full(self, destination):
        self.calls.append("capture_full")
        if self.fail_capture:
            return None
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        Path(destination).write_bytes(b"PNG-full")
        return Path(destination)

    def crop(self, source, rect, destination):
        self.calls.append("crop")
        if self.fail_crop:
            return None
        Path(destination).write_bytes(b"PNG-crop")
        return Path(destination)


class FakeGaze:
    def __init__(self, fixation=None, raises=False):
        self.fixation = fixation
        self.raises = raises
        self.windows: list[tuple[float, float]] = []

    def dominant_fixation(self, t0, t1):
        self.windows.append((t0, t1))
        if self.raises:
            raise RuntimeError("camera died")
        return self.fixation


class FakeBridge:
    def __init__(self, context=None, element_shot=True, raises=False):
        self.context = context
        self.element_shot = element_shot
        self.raises = raises
        self.points = []

    def extract_at(self, point, window, window_title=""):
        self.points.append((point, window, window_title))
        if self.raises:
            raise RuntimeError("CDP dropped")
        return self.context

    def screenshot_element(self, context, destination, window_title="", margin=12.0):
        if not self.element_shot:
            return None
        Path(destination).write_bytes(b"PNG-element")
        return Path(destination)


def make_event(text="Worth pairing with the intention sheet."):
    return NoteEvent(text, WHEN.timestamp() - 4, WHEN.timestamp(), WHEN)


def build(tmp_path, *, screen=None, gaze=None, bridge=None, **overrides):
    config = Config(notes_dir=tmp_path, **overrides)
    return NoteProcessor(
        config,
        screen=screen or FakeScreen(),
        notes=DailyNotes(tmp_path),
        gaze=gaze,
        bridge=bridge,
    )


BROWSER = BrowserContext(
    url="https://arxiv.org/abs/2401.00001",
    title="Constraints of the Political",
    text="the model's outputs are constrained not by what it knows",
    selector="article > p:nth-of-type(7)",
    scroll_y=2140,
    fragment_url="https://arxiv.org/abs/2401.00001#:~:text=the%20model",
    bbox=(100, 200, 800, 120),
)


# -- the happy path -----------------------------------------------------
def test_full_pipeline_writes_the_richest_possible_entry(tmp_path):
    processor = build(
        tmp_path,
        gaze=FakeGaze(Fixation(812, 540, 0.82, 44)),
        bridge=FakeBridge(BROWSER),
    )
    capture = processor.process(make_event())

    text = (tmp_path / "2026-09-01.md").read_text()
    assert "## 14:30:22 — Google Chrome · arxiv.org" in text
    assert '> "Worth pairing with the intention sheet."' in text
    assert "**Looking at:**" in text
    assert "#:~:text=" in text
    assert capture.screenshot is not None and capture.screenshot.name == "143022.png"
    assert capture.screenshot.read_bytes() == b"PNG-element"

    sidecar = json.loads((tmp_path / "captures/2026-09-01/143022.json").read_text())
    assert sidecar["browser"]["scroll_y"] == 2140
    assert sidecar["gaze"]["confidence"] == 0.82


def test_the_screenshot_is_taken_before_anything_else(tmp_path):
    screen = FakeScreen()
    build(tmp_path, screen=screen, gaze=FakeGaze(Fixation(812, 540, 0.9, 30))).process(make_event())
    assert screen.calls[0] == "capture_full"


def test_the_gaze_window_reaches_back_before_speech_began(tmp_path):
    gaze = FakeGaze(Fixation(812, 540, 0.9, 30))
    build(tmp_path, gaze=gaze, gaze_lookback_seconds=2.0).process(make_event())
    (t0, t1), = gaze.windows
    event = make_event()
    assert t0 == pytest.approx(event.t_start - 2.0)
    assert t1 == pytest.approx(event.t_end)


# -- degradation --------------------------------------------------------
def test_no_gaze_means_a_full_screen_entry_not_a_lost_note(tmp_path):
    capture = build(tmp_path, gaze=None).process(make_event())
    text = (tmp_path / "2026-09-01.md").read_text()
    assert '> "Worth pairing' in text
    assert "Gaze confidence" not in text
    assert capture.screenshot == capture.screenshot_full
    assert capture.crop is None


def test_a_crashing_gaze_engine_still_writes_the_note(tmp_path):
    capture = build(tmp_path, gaze=FakeGaze(raises=True)).process(make_event())
    assert capture.fixation is None
    assert (tmp_path / "2026-09-01.md").exists()


def test_a_low_confidence_fixation_is_discarded(tmp_path):
    processor = build(tmp_path, gaze=FakeGaze(Fixation(812, 540, 0.2, 8)), min_gaze_confidence=0.35)
    capture = processor.process(make_event())
    assert capture.fixation is None
    assert capture.screenshot == capture.screenshot_full


def test_gaze_without_chrome_produces_a_cropped_band(tmp_path):
    screen = FakeScreen(app=AppContext("Preview", "com.apple.Preview", "paper.pdf", (0, 25, 1400, 1000)))
    capture = build(tmp_path, screen=screen, gaze=FakeGaze(Fixation(812, 540, 0.8, 40))).process(make_event())
    assert capture.crop is not None
    assert capture.crop[3] == pytest.approx(SCREEN.h * 0.35)
    assert capture.screenshot.read_bytes() == b"PNG-crop"
    assert "crop" in screen.calls


def test_a_failed_crop_falls_back_to_the_full_screenshot(tmp_path):
    screen = FakeScreen(fail_crop=True)
    capture = build(tmp_path, screen=screen, gaze=FakeGaze(Fixation(812, 540, 0.8, 40))).process(make_event())
    assert capture.screenshot == capture.screenshot_full
    assert capture.crop is None


def test_a_dead_cdp_connection_downgrades_to_a_crop(tmp_path):
    capture = build(
        tmp_path,
        gaze=FakeGaze(Fixation(812, 540, 0.8, 40)),
        bridge=FakeBridge(raises=True),
    ).process(make_event())
    assert capture.browser is None
    assert capture.crop is not None
    assert capture.screenshot.read_bytes() == b"PNG-crop"


def test_a_failed_element_screenshot_still_keeps_the_dom_text(tmp_path):
    capture = build(
        tmp_path,
        gaze=FakeGaze(Fixation(812, 540, 0.8, 40)),
        bridge=FakeBridge(BROWSER, element_shot=False),
    ).process(make_event())
    assert capture.browser is not None
    assert "**Looking at:**" in (tmp_path / "2026-09-01.md").read_text()
    assert capture.screenshot.read_bytes() == b"PNG-crop"


def test_a_failed_screenshot_still_writes_the_transcript(tmp_path):
    capture = build(tmp_path, screen=FakeScreen(fail_capture=True), gaze=FakeGaze(Fixation(1, 1, 0.9, 30)))
    result = capture.process(make_event())
    assert result.screenshot is None
    text = (tmp_path / "2026-09-01.md").read_text()
    assert '> "Worth pairing' in text
    assert "**Capture:**" not in text


def test_chrome_is_not_queried_when_it_is_not_frontmost(tmp_path):
    bridge = FakeBridge(BROWSER)
    screen = FakeScreen(app=AppContext("Slack", "com.tinyspeck.slackmacgap", "general", (0, 25, 1400, 1000)))
    build(tmp_path, screen=screen, gaze=FakeGaze(Fixation(812, 540, 0.8, 40)), bridge=bridge).process(make_event())
    assert bridge.points == []


def test_chrome_is_not_queried_without_a_fixation(tmp_path):
    bridge = FakeBridge(BROWSER)
    build(tmp_path, gaze=None, bridge=bridge).process(make_event())
    assert bridge.points == []


def test_the_gaze_point_is_passed_in_screen_coordinates_with_the_window(tmp_path):
    bridge = FakeBridge(BROWSER)
    build(tmp_path, gaze=FakeGaze(Fixation(812, 540, 0.8, 40)), bridge=bridge).process(make_event())
    (point, window, title), = bridge.points
    assert (point.x, point.y) == (812, 540)
    assert (window.x, window.y, window.w, window.h) == (0, 25, 1728, 1092)
    assert title == "Some Page"


# -- config behaviour ---------------------------------------------------
def test_keep_full_screenshot_false_discards_the_full_frame(tmp_path):
    capture = build(
        tmp_path,
        gaze=FakeGaze(Fixation(812, 540, 0.8, 40)),
        keep_full_screenshot=False,
    ).process(make_event())
    assert capture.screenshot_full is None
    assert capture.screenshot.exists()
    assert not (tmp_path / "captures/2026-09-01/143022.full.png").exists()
    assert "full screen" not in (tmp_path / "2026-09-01.md").read_text()


def test_keep_full_screenshot_false_keeps_the_only_image_when_there_is_no_crop(tmp_path):
    capture = build(tmp_path, gaze=None, keep_full_screenshot=False).process(make_event())
    assert capture.screenshot is not None
    assert capture.screenshot.exists()


def test_the_crop_fraction_is_configurable(tmp_path):
    capture = build(
        tmp_path,
        gaze=FakeGaze(Fixation(812, 540, 0.8, 40)),
        crop_height_fraction=0.2,
    ).process(make_event())
    assert capture.crop[3] == pytest.approx(SCREEN.h * 0.2)


def test_two_notes_in_the_same_second_do_not_clobber_each_other(tmp_path):
    processor = build(tmp_path, gaze=None)
    first = processor.process(make_event("first"))
    second = processor.process(make_event("second"))
    text = (tmp_path / "2026-09-01.md").read_text()
    assert '"first"' in text and '"second"' in text
    assert first.screenshot != second.screenshot
    sidecars = DailyNotes(tmp_path).sidecars(date(2026, 9, 1))
    assert [s["transcript"] for s in sidecars] == ["first", "second"]


# -- concurrency --------------------------------------------------------
def test_the_nightly_pass_cannot_rewrite_a_day_mid_capture(tmp_path):
    """A note appended while the summary is being written must survive."""
    import threading

    from gazenotes.lock import notes_lock
    from gazenotes.nightly import run_nightly

    processor = build(tmp_path, gaze=None)
    processor.process(make_event("first note, spoken before the pass"))

    started = threading.Event()
    release = threading.Event()

    def hold():
        with notes_lock(tmp_path):
            started.set()
            release.wait(timeout=5)

    holder = threading.Thread(target=hold)
    holder.start()
    started.wait(timeout=5)

    summariser = threading.Thread(target=run_nightly, args=(processor.config, date(2026, 9, 1)))
    summariser.start()
    summariser.join(timeout=0.3)
    assert summariser.is_alive()  # blocked on the lock rather than racing the write

    release.set()
    holder.join(timeout=5)
    summariser.join(timeout=5)

    text = (tmp_path / "2026-09-01.md").read_text()
    assert "## Summary" in text
    assert '"first note, spoken before the pass"' in text


def test_the_lock_reports_when_it_is_already_held(tmp_path):
    from gazenotes.lock import lock_is_free, notes_lock

    assert lock_is_free(tmp_path)
    with notes_lock(tmp_path) as acquired:
        assert acquired


def test_the_element_bbox_is_recorded_as_viewport_geometry_not_as_a_screen_crop(tmp_path):
    capture = build(
        tmp_path,
        gaze=FakeGaze(Fixation(812, 540, 0.8, 40)),
        bridge=FakeBridge(BROWSER),
    ).process(make_event())
    assert capture.crop is None
    sidecar = json.loads((tmp_path / "captures/2026-09-01/143022.json").read_text())
    assert "crop" not in sidecar
    assert sidecar["browser"]["bbox"] == {"x": 100.0, "y": 200.0, "width": 800.0, "height": 120.0}
