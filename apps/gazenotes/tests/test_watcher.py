"""Superwhisper meta parsing and new-recording detection."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from gazenotes.watcher import SuperwhisperWatcher, file_is_stable, iter_meta_files, parse_meta


def write_recording(root: Path, name: str, meta: dict, audio: str | None = "input.wav") -> Path:
    folder = root / name
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "meta.json"
    path.write_text(json.dumps(meta), encoding="utf-8")
    if audio:
        (folder / audio).write_bytes(b"RIFF")
    return path


# -- parsing ------------------------------------------------------------
def test_parses_the_documented_schema(tmp_path):
    path = write_recording(
        tmp_path,
        "2026-09-01-143022",
        {"result": "Worth pairing with the intention sheet.", "datetime": "2026-09-01T14:30:22Z", "duration": 4.2},
    )
    event = parse_meta(path)
    assert event is not None
    assert event.transcript == "Worth pairing with the intention sheet."
    assert event.t_end - event.t_start == pytest.approx(4.2)
    assert event.audio_path is not None and event.audio_path.name == "input.wav"


@pytest.mark.parametrize("key", ["result", "text", "transcript", "llmResult", "processedResult"])
def test_accepts_every_transcript_key_seen_in_the_wild(tmp_path, key):
    path = write_recording(tmp_path, f"rec-{key}", {key: "hello", "datetime": "2026-09-01T10:00:00Z"})
    event = parse_meta(path)
    assert event is not None and event.transcript == "hello"


def test_prefers_the_raw_result_over_a_post_processed_one(tmp_path):
    path = write_recording(
        tmp_path, "rec", {"result": "raw", "llmResult": "cleaned", "datetime": "2026-09-01T10:00:00Z"}
    )
    assert parse_meta(path).transcript == "raw"


def test_an_empty_transcript_is_not_a_note(tmp_path):
    assert parse_meta(write_recording(tmp_path, "empty", {"result": "   "})) is None
    assert parse_meta(write_recording(tmp_path, "none", {"datetime": "2026-09-01T10:00:00Z"})) is None


def test_unreadable_or_non_object_json_returns_none(tmp_path):
    broken = tmp_path / "broken" / "meta.json"
    broken.parent.mkdir()
    broken.write_text("{not json")
    assert parse_meta(broken) is None

    listy = tmp_path / "listy" / "meta.json"
    listy.parent.mkdir()
    listy.write_text("[1, 2]")
    assert parse_meta(listy) is None


def test_epoch_timestamps_in_seconds_and_milliseconds(tmp_path):
    seconds = datetime(2026, 9, 1, 14, 30, 22).astimezone().timestamp()
    a = parse_meta(write_recording(tmp_path, "a", {"result": "x", "timestamp": seconds}))
    b = parse_meta(write_recording(tmp_path, "b", {"result": "x", "timestamp": seconds * 1000}))
    assert a.timestamp.hour == 14 and a.timestamp.minute == 30
    assert b.timestamp == a.timestamp


def test_a_millisecond_duration_is_recognised(tmp_path):
    path = write_recording(tmp_path, "ms", {"result": "x", "duration": 4200, "datetime": "2026-09-01T10:00:00Z"})
    assert parse_meta(path).t_end - parse_meta(path).t_start == pytest.approx(4.2)


def test_a_missing_duration_falls_back_to_a_five_second_window(tmp_path):
    path = write_recording(tmp_path, "nodur", {"result": "x", "datetime": "2026-09-01T10:00:00Z"})
    event = parse_meta(path)
    assert event.t_end - event.t_start == pytest.approx(5.0)


def test_a_missing_timestamp_falls_back_to_the_file_mtime(tmp_path):
    path = write_recording(tmp_path, "nots", {"result": "x"})
    event = parse_meta(path)
    assert event is not None
    assert event.timestamp.timestamp() == pytest.approx(path.stat().st_mtime, abs=1)


def test_audio_is_found_by_extension_when_the_name_is_unexpected(tmp_path):
    path = write_recording(tmp_path, "odd", {"result": "x"}, audio="capture-001.m4a")
    assert parse_meta(path).audio_path.name == "capture-001.m4a"


def test_a_recording_with_no_audio_still_parses(tmp_path):
    path = write_recording(tmp_path, "silent", {"result": "x"}, audio=None)
    assert parse_meta(path).audio_path is None


# -- discovery ----------------------------------------------------------
def test_iter_meta_files_is_oldest_first(tmp_path):
    import os
    import time

    for index, name in enumerate(["c", "a", "b"]):
        path = write_recording(tmp_path, name, {"result": name})
        os.utime(path, (time.time() + index, time.time() + index))
    assert [p.parent.name for p in iter_meta_files(tmp_path)] == ["c", "a", "b"]


def test_iter_meta_files_on_a_missing_folder_is_empty(tmp_path):
    assert list(iter_meta_files(tmp_path / "nope")) == []


def test_file_is_stable_detects_a_growing_file(tmp_path):
    path = tmp_path / "growing.json"
    path.write_text("{")
    state = {"n": 0}

    def fake_sleep(_seconds):
        state["n"] += 1
        path.write_text("{" + "x" * 100)

    assert file_is_stable(path, sleep=fake_sleep) is False
    assert file_is_stable(path, sleep=lambda _s: None) is True


def test_file_is_stable_on_a_vanished_file():
    assert file_is_stable("/nonexistent/meta.json", sleep=lambda _s: None) is False


# -- watcher ------------------------------------------------------------
def test_existing_recordings_are_not_replayed_on_start(tmp_path):
    write_recording(tmp_path, "old", {"result": "yesterday"})
    seen = []
    watcher = SuperwhisperWatcher(tmp_path, seen.append)
    assert watcher.poll_once() == []

    write_recording(tmp_path, "new", {"result": "today"})
    events = watcher.poll_once()
    assert [e.transcript for e in events] == ["today"]
    assert [e.transcript for e in seen] == ["today"]


def test_replay_existing_is_available_for_backfill(tmp_path):
    write_recording(tmp_path, "old", {"result": "yesterday"})
    watcher = SuperwhisperWatcher(tmp_path, lambda _e: None, replay_existing=True)
    assert [e.transcript for e in watcher.poll_once()] == ["yesterday"]


def test_the_same_recording_is_never_emitted_twice(tmp_path):
    watcher = SuperwhisperWatcher(tmp_path, lambda _e: None)
    write_recording(tmp_path, "one", {"result": "hello"})
    assert len(watcher.poll_once()) == 1
    assert watcher.poll_once() == []


def test_a_handler_that_raises_does_not_kill_the_watcher(tmp_path):
    def explode(_event):
        raise RuntimeError("handler bug")

    watcher = SuperwhisperWatcher(tmp_path, explode)
    write_recording(tmp_path, "one", {"result": "hello"})
    assert len(watcher.poll_once()) == 1  # the event was still parsed and reported
    write_recording(tmp_path, "two", {"result": "again"})
    assert len(watcher.poll_once()) == 1  # and the watcher survived


def test_non_meta_files_are_ignored(tmp_path):
    watcher = SuperwhisperWatcher(tmp_path, lambda _e: None)
    assert watcher.handle_path(tmp_path / "input.wav") is None
