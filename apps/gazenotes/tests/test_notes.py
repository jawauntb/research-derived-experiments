"""Daily file management, entry rendering, and sidecar contents."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from gazenotes.events import AppContext, BrowserContext, Capture, Fixation, NoteEvent
from gazenotes.notes import DailyNotes, format_entry, sidecar_dict

WHEN = datetime(2026, 9, 1, 14, 30, 22)


def make_event(text="This is the same move Arendt makes about natality."):
    return NoteEvent(
        transcript=text,
        t_start=WHEN.timestamp() - 5,
        t_end=WHEN.timestamp(),
        timestamp=WHEN,
        audio_path=Path("/tmp/superwhisper/143022/audio.wav"),
    )


def full_capture(notes_dir: Path) -> Capture:
    return Capture(
        event=make_event(),
        app=AppContext("Google Chrome", "com.google.Chrome", "Constraints of the Political"),
        fixation=Fixation(812, 540, 0.82, 44),
        browser=BrowserContext(
            url="https://arxiv.org/abs/2401.00001",
            title="Constraints of the Political",
            text="the model's outputs are constrained not by what it knows but by what it has been asked to be",
            selector="main > article > p:nth-of-type(7)",
            scroll_y=2140,
            fragment_url="https://arxiv.org/abs/2401.00001#:~:text=the%20model",
        ),
        screenshot=notes_dir / "captures/2026-09-01/143022.png",
        screenshot_full=notes_dir / "captures/2026-09-01/143022.full.png",
        crop=(0, 380, 1728, 380),
    )


# -- formatting ---------------------------------------------------------
def test_full_entry_has_every_line(tmp_path):
    entry = format_entry(full_capture(tmp_path), capture_rel=tmp_path)
    assert entry.startswith("## 14:30:22 — Google Chrome · arxiv.org")
    assert '> "This is the same move Arendt makes about natality."' in entry
    assert "**Looking at:**" in entry
    assert "**Source:** [Constraints of the Political](https://arxiv.org/abs/2401.00001#:~:text=" in entry
    assert "**Capture:** ![](captures/2026-09-01/143022.png)" in entry
    assert "Gaze confidence: 0.82" in entry
    assert entry.rstrip().endswith("---")


def test_entry_omits_lines_whose_data_is_missing():
    capture = Capture(event=make_event(), app=AppContext("Preview", "com.apple.Preview"))
    entry = format_entry(capture)
    assert "**Looking at:**" not in entry
    assert "**Source:**" not in entry
    assert "**Capture:**" not in entry
    assert "Gaze confidence" not in entry
    assert entry.startswith("## 14:30:22 — Preview")


def test_a_non_browser_entry_falls_back_to_the_window_title():
    capture = Capture(
        event=make_event(),
        app=AppContext("Preview", "com.apple.Preview", window_title="arendt-1958.pdf"),
    )
    assert "**Window:** arendt-1958.pdf" in format_entry(capture)


def test_transcript_whitespace_is_normalised():
    capture = Capture(event=make_event("line one\n  line   two\t"))
    assert '> "line one line two"' in format_entry(capture)


def test_a_long_looked_at_passage_is_truncated(tmp_path):
    capture = full_capture(tmp_path)
    capture.browser = BrowserContext(url="https://example.com", title="T", text="word " * 300)
    entry = format_entry(capture, capture_rel=tmp_path)
    looking = [line for line in entry.splitlines() if line.startswith("**Looking at:**")][0]
    assert "…" in looking
    assert len(looking) < 300


def test_a_page_title_cannot_break_out_of_its_markdown_link():
    capture = Capture(
        event=make_event(),
        browser=BrowserContext(url="https://example.com", title="Weird [title] here", text="x" * 50),
    )
    source = [line for line in format_entry(capture).splitlines() if line.startswith("**Source:**")][0]
    assert source.count("](") == 1


def test_www_is_stripped_from_the_heading_host():
    capture = Capture(
        event=make_event(),
        app=AppContext("Google Chrome", "com.google.Chrome"),
        browser=BrowserContext(url="https://www.nytimes.com/x", title="T", text="y" * 50),
    )
    assert format_entry(capture).startswith("## 14:30:22 — Google Chrome · nytimes.com")


# -- file management ----------------------------------------------------
def test_append_creates_the_day_file_with_a_header(tmp_path):
    notes = DailyNotes(tmp_path)
    notes.append(Capture(event=make_event()))
    text = notes.read_day(date(2026, 9, 1))
    assert text.startswith("# 2026-09-01\n")
    assert "## 14:30:22" in text


def test_appending_twice_keeps_both_entries_in_order(tmp_path):
    notes = DailyNotes(tmp_path)
    notes.append(Capture(event=make_event("first")))
    second = make_event("second")
    second = NoteEvent(
        transcript="second",
        t_start=second.t_start,
        t_end=second.t_end,
        timestamp=datetime(2026, 9, 1, 15, 0, 0),
    )
    notes.append(Capture(event=second))
    text = notes.read_day(date(2026, 9, 1))
    assert text.index('"first"') < text.index('"second"')
    assert text.count("# 2026-09-01") == 1


def test_sidecar_is_written_next_to_the_capture(tmp_path):
    notes = DailyNotes(tmp_path)
    notes.append(full_capture(tmp_path))
    sidecar = tmp_path / "captures" / "2026-09-01" / "143022.json"
    assert sidecar.exists()
    data = json.loads(sidecar.read_text())
    assert data["gaze"]["confidence"] == 0.82
    assert data["browser"]["selector"] == "main > article > p:nth-of-type(7)"
    assert data["screenshot"] == "captures/2026-09-01/143022.png"
    assert data["crop"] == {"x": 0, "y": 380, "w": 1728, "h": 380}


def test_sidecar_omits_branches_that_have_no_data():
    data = sidecar_dict(Capture(event=NoteEvent("hi", 0, 5, WHEN)))
    assert set(data) == {"ts", "transcript"}


def test_sidecars_are_returned_in_capture_order(tmp_path):
    notes = DailyNotes(tmp_path)
    for hour in (9, 14, 11):
        stamp = datetime(2026, 9, 1, hour, 0, 0)
        notes.append(Capture(event=NoteEvent(f"note {hour}", 0, 0, stamp)))
    transcripts = [s["transcript"] for s in notes.sidecars(date(2026, 9, 1))]
    assert transcripts == ["note 9", "note 11", "note 14"]


def test_an_unreadable_sidecar_is_skipped_not_fatal(tmp_path):
    notes = DailyNotes(tmp_path)
    notes.append(Capture(event=make_event()))
    (tmp_path / "captures" / "2026-09-01" / "broken.json").write_text("{not json")
    assert len(notes.sidecars(date(2026, 9, 1))) == 1


def test_purge_removes_the_note_and_its_captures(tmp_path):
    notes = DailyNotes(tmp_path)
    notes.append(full_capture(tmp_path))
    removed = notes.purge(date(2026, 9, 1))
    assert len(removed) == 2
    assert not notes.path_for(date(2026, 9, 1)).exists()
    assert not notes.capture_dir(date(2026, 9, 1)).exists()
    assert notes.purge(date(2026, 9, 1)) == []


def test_a_capture_path_outside_the_notes_dir_stays_absolute(tmp_path):
    capture = Capture(event=make_event(), screenshot=Path("/elsewhere/shot.png"))
    assert "](/elsewhere/shot.png)" in format_entry(capture, capture_rel=tmp_path)
