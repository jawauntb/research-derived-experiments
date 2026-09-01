"""Voice-command parsing and routing."""

from __future__ import annotations

import pytest

from gazenotes.commands import Command, CommandRouter, parse_command, word_to_int


# -- prefix -------------------------------------------------------------
def test_a_plain_sentence_is_a_note_not_a_command():
    assert parse_command("This paragraph is doing the same work as the earlier one.") is None


def test_a_sentence_merely_containing_the_prefix_is_still_a_note():
    assert parse_command("The computer scrolls faster than I can read.") is None


def test_the_prefix_is_configurable():
    assert parse_command("jarvis scroll down", prefix="jarvis") == Command("scroll_down")
    assert parse_command("computer scroll down", prefix="jarvis") is None


def test_the_prefix_alone_is_an_unknown_command_not_a_note():
    assert parse_command("Computer.") == Command("unknown", "")


# -- scrolling ----------------------------------------------------------
@pytest.mark.parametrize(
    "transcript,expected",
    [
        ("computer scroll down", "scroll_down"),
        ("Computer, scroll down.", "scroll_down"),
        ("computer scroll up", "scroll_up"),
        ("computer page down", "page_down"),
        ("computer page up", "page_up"),
        ("computer scroll top", "scroll_top"),
        ("computer scroll bottom", "scroll_bottom"),
        ("computer scroll", "scroll_down"),
    ],
)
def test_scroll_phrasings(transcript, expected):
    assert parse_command(transcript).name == expected


# -- clicking -----------------------------------------------------------
@pytest.mark.parametrize(
    "transcript,number",
    [
        ("computer click seven", 7),
        ("computer click 7", 7),
        ("computer click twenty three", 23),
        ("computer click twenty-three", 23),
        ("computer press nine", 9),
        ("computer click ate", 8),  # dictation homophone
    ],
)
def test_click_by_number(transcript, number):
    command = parse_command(transcript)
    assert command.name == "click"
    assert command.number == number


def test_click_by_text_when_no_number_is_heard():
    command = parse_command("computer click sign in")
    assert command == Command("click_text", argument="sign in")


def test_show_and_hide_numbers():
    assert parse_command("computer show numbers").name == "show_numbers"
    assert parse_command("computer hide numbers").name == "hide_numbers"
    assert parse_command("computer show number").name == "show_numbers"


# -- app commands -------------------------------------------------------
def test_recalibrate_and_new_section():
    assert parse_command("computer recalibrate").name == "recalibrate"
    assert parse_command("computer new section Arendt reading") == Command(
        "new_section", argument="arendt reading"
    )


def test_new_section_without_a_title():
    assert parse_command("computer new section") == Command("new_section", argument="")


def test_an_unrecognised_phrase_reports_itself_rather_than_becoming_a_note():
    command = parse_command("computer do a barrel roll")
    assert command.name == "unknown"
    assert command.argument == "do a barrel roll"


# -- number words -------------------------------------------------------
@pytest.mark.parametrize(
    "text,value",
    [("0", 0), ("zero", 0), ("fifteen", 15), ("forty two", 42), ("one hundred", None), ("", None)],
)
def test_word_to_int(text, value):
    assert word_to_int(text) == value


# -- routing ------------------------------------------------------------
class FakePage:
    def __init__(self):
        self.wheel = []
        self.evaluated = []
        self.closed = False

    class _Mouse:
        def __init__(self, page):
            self.page = page

        def wheel(self, dx, dy):
            self.page.wheel.append((dx, dy))

    @property
    def mouse(self):
        return self._Mouse(self)

    def evaluate(self, script, arg=None):
        self.evaluated.append((script, arg))
        if "__gazenotes_badges" in script:  # the overlay script
            return 12
        if "data-gazenotes-badge" in script:  # the click script
            return arg == 7
        return None

    def is_closed(self):
        return self.closed


class FakeBridge:
    def __init__(self, page=None):
        self.page = page

    def active_page(self, window_title=""):
        return self.page


def test_scroll_goes_through_chrome_when_a_page_is_available():
    page = FakePage()
    router = CommandRouter(bridge=FakeBridge(page))
    assert "scrolled" in router.dispatch(parse_command("computer scroll down"))
    assert page.wheel == [(0, 400)]


def test_scroll_falls_back_to_the_system_when_there_is_no_page():
    class FakeScreen:
        def __init__(self):
            self.scrolled = []

        def scroll(self, amount):
            self.scrolled.append(amount)

    screen = FakeScreen()
    router = CommandRouter(bridge=FakeBridge(None), screen=screen)
    assert "system" in router.dispatch(parse_command("computer scroll up"))
    assert screen.scrolled == [-400]


def test_scroll_reports_when_there_is_nothing_to_scroll():
    router = CommandRouter(bridge=FakeBridge(None))
    assert router.dispatch(parse_command("computer scroll down")) == "no scrollable target"


def test_click_reports_a_missing_badge_rather_than_clicking_something_else():
    router = CommandRouter(bridge=FakeBridge(FakePage()))
    assert router.dispatch(parse_command("computer click seven")) == "clicked 7"
    assert router.dispatch(parse_command("computer click nine")) == "no target numbered 9"


def test_show_numbers_reports_how_many_targets_it_badged():
    router = CommandRouter(bridge=FakeBridge(FakePage()))
    assert router.dispatch(parse_command("computer show numbers")) == "numbered 12 targets"


def test_a_failing_handler_is_reported_not_raised():
    class Exploding(FakePage):
        def evaluate(self, script, arg=None):
            raise RuntimeError("page crashed")

    router = CommandRouter(bridge=FakeBridge(Exploding()))
    assert "failed" in router.dispatch(parse_command("computer show numbers"))


def test_recalibrate_and_new_section_are_delegated():
    router = CommandRouter(
        recalibrate=lambda: "calibrated",
        new_section=lambda title: f"section {title}",
    )
    assert router.dispatch(parse_command("computer recalibrate")) == "calibrated"
    assert router.dispatch(parse_command("computer new section notes")) == "section notes"


def test_unavailable_delegates_report_instead_of_crashing():
    router = CommandRouter()
    assert router.dispatch(parse_command("computer recalibrate")) == "calibration not available"


# -- gaze control -------------------------------------------------------
def test_pause_and_resume_control_the_camera():
    class FakeGaze:
        def __init__(self):
            self.running = True

        def stop(self):
            self.running = False

        def start(self):
            self.running = True
            return type("S", (), {"reason": "running"})()

    gaze = FakeGaze()
    router = CommandRouter(gaze=gaze)
    assert router.dispatch(parse_command("computer pause")) == "gaze paused"
    assert not gaze.running
    assert router.dispatch(parse_command("computer resume")) == "running"
    assert gaze.running


def test_pause_without_a_gaze_engine_reports_rather_than_crashing():
    assert CommandRouter().dispatch(parse_command("computer pause")) == "gaze engine unavailable"


# -- dwell scrolling ----------------------------------------------------
def test_dwell_can_be_toggled_by_voice():
    class FakeDwell:
        def __init__(self):
            self.enabled = False

        def set_enabled(self, on):
            self.enabled = on
            return f"dwell scrolling {'on' if on else 'off'}"

    dwell = FakeDwell()
    router = CommandRouter(dwell=dwell)
    assert parse_command("computer dwell on").name == "dwell_on"
    assert router.dispatch(parse_command("computer dwell on")) == "dwell scrolling on"
    assert dwell.enabled
    assert router.dispatch(parse_command("computer dwell off")) == "dwell scrolling off"
    assert not dwell.enabled


def test_dwell_commands_report_when_the_driver_is_absent():
    assert CommandRouter().dispatch(parse_command("computer dwell on")) == "dwell scrolling unavailable"


def test_the_public_scroll_helper_is_what_dwell_uses():
    page = FakePage()
    router = CommandRouter(bridge=FakeBridge(page))
    assert "scrolled" in router.scroll(400.0)
    assert page.wheel == [(0, 400)]
