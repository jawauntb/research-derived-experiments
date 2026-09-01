"""Passage building from OCR lines, and the Vision-absent contract.

Everything here runs headless. The interesting risk is the coordinate system:
Vision hands back **normalised, bottom-left** boxes, so ``y = 1.0`` is the
*top* of the crop and the first line of a paragraph has the *largest* y — the
opposite of the quartz top-left convention used everywhere else in the app.
Several tests below fail loudly if that sort is inverted.
"""

from __future__ import annotations

import pytest

from gazenotes.ocr import (
    TextLine,
    looking_at,
    passage_from_lines,
    reading_order,
    recognise_text,
    vision_available,
)

NO_VISION = not vision_available()


def line(
    text: str,
    *,
    top: float,
    height: float = 0.04,
    left: float = 0.1,
    width: float = 0.8,
    confidence: float = 0.9,
) -> TextLine:
    """Build a :class:`TextLine` from its *top* edge, Vision-style.

    ``top`` is in Vision's normalised bottom-left space: 1.0 is the top of the
    image, 0.0 the bottom. The bbox stored is ``(x, bottom, width, height)``,
    exactly as ``VNRecognizedTextObservation.boundingBox`` reports it.
    """
    return TextLine(text=text, confidence=confidence, bbox=(left, top - height, width, height))


# -- the coordinate trap ------------------------------------------------
def test_lines_read_top_of_image_first_even_though_y_grows_upward():
    # The whole point: sorting *ascending* by Vision's y reads the crop upside
    # down. First line of the paragraph sits highest, i.e. at the largest y.
    lines = [
        line("first line of the paragraph", top=0.90),
        line("second line of the paragraph", top=0.80),
        line("third line of the paragraph", top=0.70),
    ]
    assert [item.text for item in reading_order(lines)] == [
        "first line of the paragraph",
        "second line of the paragraph",
        "third line of the paragraph",
    ]
    passage = passage_from_lines(lines)
    assert passage.startswith("first line")
    assert passage.endswith("paragraph")
    # An inverted sort would produce exactly this, so name it and rule it out.
    assert not passage.startswith("third line")


def test_input_order_does_not_matter_only_geometry_does():
    # Vision returns observations in no guaranteed order; the passage must not
    # depend on it.
    ordered = [line("alpha beta", top=0.9), line("gamma delta", top=0.8), line("epsilon zeta", top=0.7)]
    shuffled = [ordered[2], ordered[0], ordered[1]]
    assert passage_from_lines(shuffled, min_chars=0) == passage_from_lines(ordered, min_chars=0)
    assert passage_from_lines(shuffled, min_chars=0) == "alpha beta gamma delta epsilon zeta"


def test_a_lower_line_never_precedes_a_higher_one_however_far_left_it_starts():
    # Guards against sorting by x before y: the indented continuation is lower
    # on the page and must still come second.
    lines = [
        line("the argument begins here", top=0.60, left=0.30),
        line("and continues", top=0.90, left=0.05),
    ]
    assert [item.text for item in reading_order(lines)] == [
        "and continues",
        "the argument begins here",
    ]


# -- reading order across a row -----------------------------------------
def test_fragments_sharing_a_row_are_ordered_left_to_right():
    # A table row or a two-column layout: same band, ordered by left edge.
    lines = [
        line("right column text", top=0.80, left=0.55, width=0.4),
        line("left column text", top=0.80, left=0.05, width=0.4),
    ]
    assert [item.text for item in reading_order(lines)] == ["left column text", "right column text"]


def test_rows_are_grouped_before_left_to_right_ordering_is_applied():
    # Two rows of two fragments each: row order wins, then x within the row.
    lines = [
        line("B", top=0.90, left=0.55, width=0.4),
        line("D", top=0.80, left=0.55, width=0.4),
        line("A", top=0.90, left=0.05, width=0.4),
        line("C", top=0.80, left=0.05, width=0.4),
    ]
    assert [item.text for item in reading_order(lines)] == ["A", "B", "C", "D"]


def test_slightly_misaligned_boxes_still_count_as_one_row():
    # Vision's boxes for text of different sizes on the same visual line do not
    # align exactly; overlapping most of their height is enough.
    lines = [
        line("second", top=0.803, height=0.030, left=0.5, width=0.3),
        line("first", top=0.800, height=0.040, left=0.1, width=0.3),
    ]
    assert [item.text for item in reading_order(lines)] == ["first", "second"]


def test_no_lines_gives_an_empty_order_and_an_empty_passage():
    assert reading_order([]) == []
    assert reading_order(None) == []
    assert passage_from_lines([]) == ""
    assert passage_from_lines(None) == ""


# -- noise ---------------------------------------------------------------
def test_low_confidence_lines_are_dropped_as_noise():
    # Window furniture and icons come back from Vision with low confidence;
    # they must not end up inside a quoted passage.
    lines = [
        line("the real sentence that we actually want to quote here", top=0.9),
        line("|||", top=0.8, confidence=0.05),
        line("garbled ocr guess", top=0.7, confidence=0.1),
    ]
    passage = passage_from_lines(lines)
    assert passage == "the real sentence that we actually want to quote here"


def test_everything_below_the_confidence_floor_yields_no_passage():
    lines = [line("a very long but very unconvincing recognition result", top=0.9, confidence=0.01)]
    assert passage_from_lines(lines) == ""


def test_the_confidence_floor_is_adjustable():
    lines = [line("a passage recognised with middling confidence indeed", top=0.9, confidence=0.2)]
    assert passage_from_lines(lines) == ""
    assert passage_from_lines(lines, min_confidence=0.1).startswith("a passage recognised")


def test_decoration_only_lines_are_dropped():
    # Rules, bullets and box drawing carry no words; keeping them would put
    # "———" in the middle of a quote.
    lines = [
        line("————", top=0.95),
        line("a genuine sentence worth keeping in the note", top=0.90),
        line("•", top=0.85),
    ]
    assert passage_from_lines(lines) == "a genuine sentence worth keeping in the note"


# -- text shaping --------------------------------------------------------
def test_whitespace_inside_and_between_lines_is_normalised():
    lines = [
        line("  the\tmodel's   outputs  ", top=0.9),
        line("are\n\nconstrained   by what it was asked to be", top=0.8),
    ]
    assert passage_from_lines(lines) == (
        "the model's outputs are constrained by what it was asked to be"
    )


def test_a_word_hyphenated_across_a_line_break_is_rejoined():
    # PDFs hyphenate constantly; "consti- tution" reads badly in a note.
    lines = [
        line("the argument turns on the consti-", top=0.9),
        line("tution of the political subject", top=0.8),
    ]
    assert passage_from_lines(lines) == "the argument turns on the constitution of the political subject"


def test_a_real_dash_or_compound_at_a_line_end_is_not_swallowed():
    # Only a lowercase continuation counts as hyphenation; a following capital
    # means the hyphen was doing its own work.
    lines = [
        line("a well-known counter-", top=0.9),
        line("Example from the literature on this", top=0.8),
    ]
    assert passage_from_lines(lines) == "a well-known counter- Example from the literature on this"


# -- length gates --------------------------------------------------------
def test_a_passage_shorter_than_min_chars_is_rejected():
    # A button label or a tab title is not something to quote in a note.
    assert passage_from_lines([line("Send", top=0.9)]) == ""
    assert passage_from_lines([line("Send", top=0.9)], min_chars=0) == "Send"


def test_min_chars_counts_the_joined_passage_not_each_line():
    lines = [line("four words per", top=0.9), line("line but plenty overall in total", top=0.8)]
    assert passage_from_lines(lines) == "four words per line but plenty overall in total"


def test_a_long_passage_is_truncated_at_a_word_boundary_within_max_chars():
    lines = [line(" ".join(["word"] * 200), top=0.9)]
    passage = passage_from_lines(lines, max_chars=60)
    assert len(passage) <= 60
    assert passage.endswith("…")
    assert "wor…" not in passage  # never cut mid-word when a boundary is near
    assert passage.startswith("word word")


def test_a_passage_at_the_limit_is_left_alone():
    text = "x" * 50
    assert passage_from_lines([line(text, top=0.9)], max_chars=50) == text


def test_an_unbreakable_run_longer_than_max_chars_is_still_clipped():
    # No word boundary to honour: hard clip rather than blowing the limit.
    passage = passage_from_lines([line("y" * 300, top=0.9)], max_chars=40)
    assert len(passage) == 40
    assert passage.endswith("…")


# -- geometry helpers ----------------------------------------------------
def test_text_line_edges_follow_visions_bottom_left_convention():
    item = TextLine(text="x", confidence=1.0, bbox=(0.10, 0.70, 0.50, 0.05))
    assert item.left == pytest.approx(0.10)
    assert item.right == pytest.approx(0.60)
    assert item.bottom == pytest.approx(0.70)
    assert item.top == pytest.approx(0.75)
    assert item.centre_y == pytest.approx(0.725)


# -- the Vision-absent contract -----------------------------------------
@pytest.mark.skipif(not NO_VISION, reason="pins behaviour on hosts without Apple Vision")
def test_vision_is_reported_unavailable_off_macos():
    assert vision_available() is False


@pytest.mark.skipif(not NO_VISION, reason="pins behaviour on hosts without Apple Vision")
def test_recognise_text_returns_none_rather_than_raising_without_vision(tmp_path):
    crop = tmp_path / "143022.png"
    crop.write_bytes(b"\x89PNG\r\n\x1a\n not really a png")
    assert recognise_text(crop) is None


@pytest.mark.skipif(not NO_VISION, reason="pins behaviour on hosts without Apple Vision")
def test_looking_at_returns_none_rather_than_raising_without_vision(tmp_path):
    crop = tmp_path / "143022.png"
    crop.write_bytes(b"\x89PNG\r\n\x1a\n")
    assert looking_at(crop) is None


def test_a_missing_crop_is_none_on_every_platform():
    # The pipeline may hand us a path the crop step failed to write.
    assert recognise_text("/nonexistent/gazenotes/143022.png") is None
    assert looking_at("/nonexistent/gazenotes/143022.png") is None
