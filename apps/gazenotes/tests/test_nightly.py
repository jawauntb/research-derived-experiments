"""The nightly summary pass: heuristics, idempotency, and cross-links."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from gazenotes.config import Config
from gazenotes.events import Capture, NoteEvent
from gazenotes.nightly import (
    apply_summary,
    extract_todos,
    keywords,
    related_days,
    render_summary,
    run_nightly,
    summarise_day,
)
from gazenotes.notes import SUMMARY_END, SUMMARY_START, DailyNotes

DAY = date(2026, 9, 1)


def sidecar(text, url="", app="Google Chrome"):
    data = {"transcript": text, "app": {"name": app}}
    if url:
        data["browser"] = {"url": url, "text": text, "title": "T"}
    return data


def seed_day(root, day, notes_text, urls=None):
    notes = DailyNotes(root)
    urls = urls or [""] * len(notes_text)
    for index, (text, url) in enumerate(zip(notes_text, urls, strict=True)):
        stamp = datetime(day.year, day.month, day.day, 9 + index, 0, 0)
        capture = Capture(event=NoteEvent(text, 0, 0, stamp))
        if url:
            from gazenotes.events import BrowserContext

            capture.browser = BrowserContext(url=url, title="T", text=text)
        notes.append(capture)
    return notes


# -- heuristics ---------------------------------------------------------
def test_todos_are_pulled_from_intention_phrasing():
    todos = extract_todos(
        [
            "This is just an observation about the argument.",
            "I should reread the Arendt chapter before Thursday.",
            "Need to check whether the benchmark controls for length.",
        ]
    )
    assert len(todos) == 2
    assert todos[0].startswith("I should reread")


def test_todos_are_deduplicated_across_notes():
    todos = extract_todos(["I should reread this.", "I should reread this", "different note"])
    assert todos == ["I should reread this"]


def test_a_todo_inside_a_longer_note_is_extracted_as_its_own_sentence():
    todos = extract_todos(["The framing is interesting. I need to find the original source."])
    assert todos == ["I need to find the original source"]


def test_keywords_skip_stopwords_and_short_words():
    words = keywords("The model constrains the model outputs because the model was asked to")
    assert "model" in words
    assert "the" not in words and "was" not in words


def test_summary_bullets_favour_substantial_notes_but_keep_chronology():
    sidecars = [
        sidecar("ok"),
        sidecar("This is a much longer and more substantive observation about the argument."),
        sidecar("Another reasonably long remark that carries some actual content here."),
    ]
    summary = summarise_day(sidecars, max_bullets=2)
    assert summary["count"] == 3
    assert summary["bullets"][0].startswith("This is a much longer")
    assert summary["bullets"][1].startswith("Another reasonably long")


def test_bullets_name_their_source():
    summary = summarise_day([sidecar("a note", url="https://arxiv.org/abs/1")])
    assert "(arxiv.org)" in summary["bullets"][0]


def test_a_very_long_note_is_truncated_in_its_bullet():
    summary = summarise_day([sidecar("word " * 100)])
    assert "… (Google Chrome)" in summary["bullets"][0]
    assert len(summary["bullets"][0]) < 220


# -- rendering ----------------------------------------------------------
def test_render_includes_todos_and_related_days():
    summary = summarise_day([sidecar("I should reread the chapter about natality.")])
    block = render_summary(DAY, summary, [(date(2026, 8, 30), "arendt, natality")])
    assert "## Summary" in block
    assert "### To-dos" in block
    assert "- [ ] I should reread the chapter about natality" in block
    assert "[2026-08-30](2026-08-30.md) — arendt, natality" in block
    assert block.startswith(SUMMARY_START)
    assert SUMMARY_END in block


def test_render_omits_empty_sections():
    block = render_summary(DAY, summarise_day([sidecar("just an observation")]))
    assert "### To-dos" not in block
    assert "### Related" not in block


def test_a_day_with_no_notes_says_so():
    assert "_No notes captured._" in render_summary(DAY, summarise_day([]))


# -- placement and idempotency -----------------------------------------
def test_summary_is_inserted_under_the_day_header():
    document = "# 2026-09-01\n\n## 09:00:00 — Chrome\n\n> \"a note\"\n\n---\n"
    block = render_summary(DAY, summarise_day([sidecar("a note")]))
    result = apply_summary(document, block)
    assert result.startswith("# 2026-09-01\n")
    assert result.index(SUMMARY_START) < result.index("## 09:00:00")


def test_rerunning_replaces_the_block_instead_of_stacking_it():
    document = "# 2026-09-01\n\n## 09:00:00 — Chrome\n\n---\n"
    first = apply_summary(document, render_summary(DAY, summarise_day([sidecar("one note")])))
    second = apply_summary(first, render_summary(DAY, summarise_day([sidecar("one note"), sidecar("two")])))
    assert second.count(SUMMARY_START) == 1
    assert second.count(SUMMARY_END) == 1
    assert "2 notes" in second
    assert "## 09:00:00" in second


def test_applying_the_same_summary_twice_is_a_fixed_point():
    document = "# 2026-09-01\n\n## 09:00:00 — Chrome\n\n---\n"
    block = render_summary(DAY, summarise_day([sidecar("one note")]))
    once = apply_summary(document, block)
    assert apply_summary(once, block) == once


def test_entries_are_never_rewritten_by_the_pass(tmp_path):
    notes = seed_day(tmp_path, DAY, ["I should reread the Arendt chapter.", "A second remark."])
    before = notes.read_day(DAY)
    run_nightly(Config(notes_dir=tmp_path), DAY)
    after = notes.read_day(DAY)
    for line in before.splitlines():
        if line.startswith(("## ", "> ")):
            assert line in after


# -- end to end ---------------------------------------------------------
def test_run_nightly_writes_a_summary_for_a_real_day(tmp_path):
    seed_day(
        tmp_path,
        DAY,
        [
            "The constraint framing here matches the earlier attractor argument.",
            "I should reread the Arendt chapter before Thursday.",
            "This paragraph is doing the same work as the intention sheet.",
            "Worth pairing with the geometry of constraints note.",
            "Need to check whether the benchmark controls for length.",
        ],
    )
    path = run_nightly(Config(notes_dir=tmp_path), DAY)
    assert path is not None
    text = path.read_text()
    assert "## Summary" in text
    assert "_5 notes._" in text
    assert "- [ ] I should reread the Arendt chapter before Thursday" in text
    assert "- [ ] Need to check whether the benchmark controls for length" in text


def test_run_nightly_on_an_empty_day_does_nothing(tmp_path):
    assert run_nightly(Config(notes_dir=tmp_path), DAY) is None


def test_related_days_link_on_a_shared_url(tmp_path):
    url = "https://arxiv.org/abs/2401.00001"
    seed_day(tmp_path, DAY - timedelta(days=2), ["An earlier note on this paper."], [url])
    notes = seed_day(tmp_path, DAY, ["A later note on the same paper."], [url])
    summary = summarise_day(notes.sidecars(DAY))
    related = related_days(notes, DAY, summary)
    assert related and related[0][0] == DAY - timedelta(days=2)
    assert "same source" in related[0][1]


def test_related_days_link_on_shared_keywords(tmp_path):
    seed_day(tmp_path, DAY - timedelta(days=1), ["Constraints and geometry keep recurring in constraints work on geometry."])
    notes = seed_day(tmp_path, DAY, ["More constraints, more geometry: constraints shape geometry everywhere."])
    related = related_days(notes, DAY, summarise_day(notes.sidecars(DAY)))
    assert related and related[0][0] == DAY - timedelta(days=1)


def test_unrelated_days_are_not_linked(tmp_path):
    seed_day(tmp_path, DAY - timedelta(days=1), ["Sourdough hydration percentages confuse me."])
    notes = seed_day(tmp_path, DAY, ["Attractor dynamics in recurrent policy networks."])
    assert related_days(notes, DAY, summarise_day(notes.sidecars(DAY))) == []


def test_the_default_backend_makes_no_network_call(tmp_path, monkeypatch):
    import socket

    def forbidden(*_args, **_kwargs):
        raise AssertionError("the nightly pass must not touch the network by default")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    seed_day(tmp_path, DAY, ["A note that should never leave this machine."])
    assert run_nightly(Config(notes_dir=tmp_path), DAY) is not None


def test_an_unknown_backend_falls_back_to_heuristics(tmp_path):
    from gazenotes.config import NightlyConfig
    from gazenotes.nightly import llm_summary

    summary = summarise_day([sidecar("a note")])
    assert llm_summary(summary, NightlyConfig(backend="nonsense")) == summary
