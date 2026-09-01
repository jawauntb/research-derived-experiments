"""Local OCR enrichment for everything that is not Chrome.

When the frontmost app is Chrome the DOM gives us the real prose under the
gaze point (:mod:`gazenotes.browser`). Everywhere else — a PDF in Preview, a
Slack thread, Mail, a terminal — the pipeline has only pixels: a cropped PNG of
the gaze band and no text at all. Apple's Vision framework recognises text in
that crop **on device, in tens of milliseconds, with no network**, which is
exactly the trade this app wants: it fills the gap Chrome's DOM covers, without
breaking the local-only rule or slowing a capture down.

Like every enrichment here, it is optional and it cannot fail a note:
:func:`recognise_text` returns ``None`` rather than raising when Vision is
missing or unhappy, and the caller simply writes an entry with no
``**Looking at:**`` line.

The coordinate trap
-------------------
Vision reports bounding boxes **normalised (0..1) with the origin at the
bottom-left** — ``y = 1.0`` is the *top* of the image. The rest of gazenotes
uses quartz logical points with the origin at the **top-left** (see
:mod:`gazenotes.geometry`). So the first line of a paragraph has the *largest*
y, and sorting ascending by y — the obvious thing — reads the passage from the
bottom up. :func:`reading_order` sorts descending by the box's top edge; the
tests pin that orientation deliberately.

What is verified where
----------------------
:func:`passage_from_lines` and :func:`reading_order` are pure and fully covered
by ``tests/test_ocr.py`` on any platform. The Vision call itself
(:func:`recognise_text`) can only be exercised on macOS with
``pyobjc-framework-Vision`` installed; off macOS the tests pin the contract
that matters here — it returns ``None`` and never raises. The pyobjc call
sequence (``VNImageRequestHandler`` → ``VNRecognizeTextRequest`` →
``topCandidates_``) and the accuracy of the recognition levels therefore need a
real macOS machine to confirm.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

__all__ = [
    "TextLine",
    "recognise_text",
    "reading_order",
    "passage_from_lines",
    "looking_at",
    "vision_available",
]

MIN_CONFIDENCE = 0.3
"""Vision's per-candidate confidence below which a line is treated as noise.

Icons, window furniture and antialiased UI chrome come back with low
confidence; real prose in a screenshot is routinely above 0.5.
"""

MIN_PASSAGE_CHARS = 40
"""Same floor as :data:`gazenotes.browser.MIN_BLOCK_CHARS`: shorter than this
and the "passage" is a button label, not something worth quoting."""

MAX_PASSAGE_CHARS = 2000

_ROW_OVERLAP = 0.5
"""Fraction of the shorter box two lines must share vertically to count as one
visual row (side-by-side columns, a drop cap, a marginal note)."""

_ROW_TOLERANCE = 0.01
"""Fallback row test in normalised units, for degenerate zero-height boxes."""


@dataclass(frozen=True)
class TextLine:
    """One recognised line, in **Vision's** coordinate system.

    ``bbox`` is ``(x, y, width, height)``, normalised to 0..1 against the image,
    origin **bottom-left** — so ``y`` is the line's *bottom* edge and larger
    values are further up the page.
    """

    text: str
    confidence: float
    bbox: tuple[float, float, float, float]

    @property
    def left(self) -> float:
        return self.bbox[0]

    @property
    def right(self) -> float:
        return self.bbox[0] + self.bbox[2]

    @property
    def bottom(self) -> float:
        """Lower edge, in Vision's bottom-left space (smaller = further down)."""
        return self.bbox[1]

    @property
    def top(self) -> float:
        """Upper edge. Sorting *descending* on this reads top-to-bottom."""
        return self.bbox[1] + self.bbox[3]

    @property
    def height(self) -> float:
        return self.bbox[3]

    @property
    def centre_y(self) -> float:
        return self.bbox[1] + self.bbox[3] / 2.0


# -- recognition (macOS only) -------------------------------------------
def recognise_text(
    image_path: Path,
    *,
    languages: Sequence[str] = ("en-US",),
    fast: bool = False,
) -> list[TextLine] | None:
    """Run Apple Vision over ``image_path``; ``None`` if it cannot be done.

    ``fast`` picks Vision's fast recognition level, which is roughly an order
    of magnitude quicker and noticeably worse on small type — accurate is the
    default because a capture already tolerates a few tens of milliseconds.

    Returns ``None`` — never raises — when the framework is absent (any
    non-macOS host, or macOS without ``pyobjc-framework-Vision``), when the
    file is missing, or when the request fails. An image with no text in it
    returns an empty list, which is a different thing and worth distinguishing:
    OCR ran, there was simply nothing to read.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        log.debug("OCR skipped: %s does not exist", image_path)
        return None

    try:
        import Vision
        from CoreFoundation import CFURLCreateWithFileSystemPath, kCFURLPOSIXPathStyle
    except ImportError as exc:
        log.debug("Vision unavailable (%s); OCR enrichment disabled", exc)
        return None

    try:
        url = CFURLCreateWithFileSystemPath(None, str(image_path), kCFURLPOSIXPathStyle, False)
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, {})
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(
            Vision.VNRequestTextRecognitionLevelFast if fast else Vision.VNRequestTextRecognitionLevelAccurate
        )
        request.setUsesLanguageCorrection_(True)
        if languages:
            request.setRecognitionLanguages_(list(languages))
        ok, error = handler.performRequests_error_([request], None)
        if not ok:
            log.warning("Vision text request failed: %s", error)
            return None
        observations = request.results() or []
    except Exception as exc:  # noqa: BLE001 - any failure means "no OCR"
        log.warning("Vision text recognition failed for %s: %s", image_path, exc)
        return None

    return _lines_from_observations(observations)


def _lines_from_observations(observations: Iterable[object]) -> list[TextLine]:
    """Convert ``VNRecognizedTextObservation`` objects into :class:`TextLine`.

    Kept separate from the request plumbing so the shape of the conversion is
    obvious, and so a single malformed observation cannot lose the rest.
    """
    lines: list[TextLine] = []
    for observation in observations:
        try:
            candidates = observation.topCandidates_(1) or []  # type: ignore[attr-defined]
            if not candidates:
                continue
            candidate = candidates[0]
            text = str(candidate.string() or "")
            if not text.strip():
                continue
            box = observation.boundingBox()  # type: ignore[attr-defined]
            lines.append(
                TextLine(
                    text=text,
                    confidence=float(candidate.confidence()),
                    bbox=(
                        float(box.origin.x),
                        float(box.origin.y),
                        float(box.size.width),
                        float(box.size.height),
                    ),
                )
            )
        except Exception as exc:  # noqa: BLE001
            log.debug("skipping unreadable observation: %s", exc)
    return lines


def vision_available() -> bool:
    """Whether Apple Vision text recognition can be used here — for ``doctor``."""
    try:
        import Vision
    except ImportError:
        return False
    return hasattr(Vision, "VNRecognizeTextRequest")


# -- the pure core ------------------------------------------------------
def reading_order(lines: Iterable[TextLine] | None) -> list[TextLine]:
    """Sort recognised lines the way a person reads them.

    Top to bottom, then left to right *within* a visual row. Because Vision's
    origin is bottom-left, "top to bottom" is **descending** ``top``. Lines
    that overlap vertically (two columns, a figure caption beside a paragraph)
    form one row and are ordered by their left edge.
    """
    remaining = sorted(
        (line for line in (lines or [])),
        key=lambda line: (-line.top, line.left),
    )
    ordered: list[TextLine] = []
    row: list[TextLine] = []
    row_top = row_bottom = 0.0
    for line in remaining:
        if row and not _joins_row(row_top, row_bottom, line):
            ordered.extend(sorted(row, key=lambda item: item.left))
            row = []
        if not row:
            row_top, row_bottom = line.top, line.bottom
        else:
            row_top, row_bottom = max(row_top, line.top), min(row_bottom, line.bottom)
        row.append(line)
    ordered.extend(sorted(row, key=lambda item: item.left))
    return ordered


def _joins_row(row_top: float, row_bottom: float, line: TextLine) -> bool:
    """Does ``line`` sit on the same visual row as the run built so far?"""
    overlap = min(row_top, line.top) - max(row_bottom, line.bottom)
    shorter = min(row_top - row_bottom, line.height)
    if shorter <= 0.0:  # zero-height boxes: fall back to centre proximity
        return abs((row_top + row_bottom) / 2.0 - line.centre_y) <= _ROW_TOLERANCE
    return overlap >= _ROW_OVERLAP * shorter


def passage_from_lines(
    lines: Iterable[TextLine] | None,
    *,
    min_chars: int = MIN_PASSAGE_CHARS,
    max_chars: int = MAX_PASSAGE_CHARS,
    min_confidence: float = MIN_CONFIDENCE,
) -> str:
    """Join recognised lines into one quotable passage, or ``""``.

    Low-confidence lines and lines with no word characters at all (rules,
    bullets, box drawing) are dropped as noise, whitespace is collapsed, words
    hyphenated across a line break are rejoined, and the result is truncated at
    a word boundary to ``max_chars``. A passage shorter than ``min_chars`` is
    returned as ``""``: that is a toolbar label, not something worth quoting.

    Pure: no I/O, no platform, no state. This is the part that decides whether
    the note reads well, so it is the part the tests lean on hardest.
    """
    kept = [
        line
        for line in reading_order(lines)
        if line.confidence >= min_confidence and _is_wordy(line.text)
    ]
    if not kept:
        return ""

    passage = ""
    for line in kept:
        text = " ".join(line.text.split())
        if not passage:
            passage = text
        elif _hyphenated(passage, text):
            passage = passage[:-1] + text
        else:
            passage = f"{passage} {text}"

    if len(passage) < max(0, min_chars):
        return ""
    return _truncate(passage, max_chars)


def _is_wordy(text: str) -> bool:
    """At least one alphanumeric character — otherwise it is decoration."""
    return any(char.isalnum() for char in text)


def _hyphenated(passage: str, nxt: str) -> bool:
    """Was a word split across the line break (``consti-`` / ``tution``)?

    Only when a letter precedes the hyphen and the next line starts lowercase,
    so real dashes and hyphenated compounds at a line end survive intact.
    """
    return (
        len(passage) >= 2
        and passage.endswith("-")
        and passage[-2].isalpha()
        and bool(nxt)
        and nxt[0].islower()
    )


def _truncate(passage: str, max_chars: int) -> str:
    """Clip to ``max_chars`` *including* the ellipsis, at a word boundary."""
    if max_chars <= 0:
        return ""
    if len(passage) <= max_chars:
        return passage
    head = passage[: max_chars - 1]
    cut = head.rfind(" ")
    if cut > max_chars // 2:  # only honour a word boundary that keeps most of it
        head = head[:cut]
    return head.rstrip() + "…"


# -- convenience --------------------------------------------------------
def looking_at(
    image_path: Path,
    *,
    languages: Sequence[str] = ("en-US",),
    fast: bool = False,
    min_chars: int = MIN_PASSAGE_CHARS,
    max_chars: int = MAX_PASSAGE_CHARS,
    min_confidence: float = MIN_CONFIDENCE,
) -> str | None:
    """OCR a gaze crop and return a quotable passage, or ``None``.

    ``None`` covers both "OCR was not possible here" and "nothing usable was
    read", because the caller does the same thing with either: omit the
    ``**Looking at:**`` line and keep the note.
    """
    lines = recognise_text(image_path, languages=languages, fast=fast)
    if not lines:
        return None
    passage = passage_from_lines(
        lines,
        min_chars=min_chars,
        max_chars=max_chars,
        min_confidence=min_confidence,
    )
    return passage or None
