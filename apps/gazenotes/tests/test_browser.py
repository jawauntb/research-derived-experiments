"""Text-fragment links, page selection, and DOM payload conversion."""

from __future__ import annotations

from urllib.parse import unquote

from gazenotes.browser import (
    EXTRACT_SCRIPT,
    browser_context_from_payload,
    pick_page_index,
    text_fragment_url,
)

PASSAGE = "the model's outputs are constrained not by what it knows but by what it has been asked to be"


# -- text fragments -----------------------------------------------------
def test_fragment_uses_the_first_few_words():
    url = text_fragment_url("https://arxiv.org/abs/2401.00001", PASSAGE)
    assert url.startswith("https://arxiv.org/abs/2401.00001#:~:text=")
    assert unquote(url.split("#:~:text=")[1]) == "the model's outputs are constrained not by what"


def test_fragment_percent_encodes_everything_risky():
    url = text_fragment_url("https://example.com", "a & b — c/d? e#f g h")
    fragment = url.split("#:~:text=")[1]
    for char in "&/?#":
        assert char not in fragment


def test_an_existing_fragment_is_replaced_not_appended():
    url = text_fragment_url("https://example.com/x#section-3", PASSAGE)
    assert url.count("#") == 1
    assert url.startswith("https://example.com/x#:~:text=")


def test_a_too_short_passage_yields_the_plain_url():
    assert text_fragment_url("https://example.com", "ok then") == "https://example.com"


def test_no_url_yields_no_link():
    assert text_fragment_url("", PASSAGE) == ""


def test_trailing_punctuation_words_are_dropped_from_the_fragment():
    url = text_fragment_url("https://example.com", "One two three — four", words=4)
    assert unquote(url.split("#:~:text=")[1]) == "One two three"


def test_newlines_and_runs_of_space_are_collapsed():
    url = text_fragment_url("https://example.com", "The\n\n  model   was\tasked to be")
    assert unquote(url.split("#:~:text=")[1]) == "The model was asked to be"


# -- page selection -----------------------------------------------------
def test_exact_title_match_wins():
    titles = ["Inbox", "Constraints of the Political", "Hacker News"]
    assert pick_page_index(titles, "Constraints of the Political") == 1


def test_the_chrome_suffix_is_stripped_from_the_window_title():
    titles = ["Inbox", "Constraints of the Political"]
    assert pick_page_index(titles, "Constraints of the Political - Google Chrome") == 1


def test_a_partial_match_is_accepted():
    titles = ["Constraints of the Political — arXiv"]
    assert pick_page_index(titles, "Constraints of the Political") == 0


def test_a_single_page_is_used_even_without_a_title_match():
    assert pick_page_index(["Something else"], "") == 0


def test_ambiguity_across_many_pages_returns_none():
    assert pick_page_index(["A", "B", "C"], "Nothing like these") is None


def test_no_pages_returns_none():
    assert pick_page_index([], "anything") is None


# -- payload ------------------------------------------------------------
def test_payload_becomes_a_typed_context_with_a_fragment_link():
    context = browser_context_from_payload(
        {
            "text": PASSAGE,
            "selector": "main > article > p:nth-of-type(7)",
            "url": "https://arxiv.org/abs/2401.00001",
            "title": "Constraints of the Political",
            "scrollY": 2140,
            "bbox": {"x": 100, "y": 200, "width": 800, "height": 120},
        }
    )
    assert context is not None
    assert context.scroll_y == 2140
    assert context.bbox == (100.0, 200.0, 800.0, 120.0)
    assert "#:~:text=" in context.fragment_url


def test_an_empty_or_missing_payload_is_none():
    assert browser_context_from_payload(None) is None
    assert browser_context_from_payload({}) is None
    assert browser_context_from_payload({"text": "", "url": ""}) is None


def test_a_url_with_no_text_still_gives_a_source_link():
    context = browser_context_from_payload({"text": "", "url": "https://example.com"})
    assert context is not None
    assert context.fragment_url == "https://example.com"


def test_the_extract_script_carries_the_configured_limits():
    assert "innerText" in EXTRACT_SCRIPT
    assert "elementFromPoint" in EXTRACT_SCRIPT
    assert "text.length >= 40" in EXTRACT_SCRIPT
    assert "slice(0, 2000)" in EXTRACT_SCRIPT


# -- bridge behaviour ---------------------------------------------------
def test_a_gaze_point_in_the_browser_chrome_is_rejected():
    from gazenotes.browser import ChromeBridge
    from gazenotes.geometry import Point, Rect

    class Bridge(ChromeBridge):
        def active_page(self, window_title=""):
            return object()

        def chrome_height(self, page):
            return 87.0

    bridge = Bridge()
    # A gaze point 40pt below the window top is inside the omnibox, not the page.
    assert bridge.extract_at(Point(500, 100), Rect(0, 60, 1200, 900)) is None


def test_no_page_means_no_enrichment_rather_than_an_error():
    from gazenotes.browser import ChromeBridge
    from gazenotes.geometry import Point, Rect

    class Bridge(ChromeBridge):
        def active_page(self, window_title=""):
            return None

    assert Bridge().extract_at(Point(500, 500), Rect(0, 0, 1200, 900)) is None
