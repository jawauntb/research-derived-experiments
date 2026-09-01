"""The rolling in-memory screen buffer: bounds, ordering, and staying off disk."""

from __future__ import annotations

import threading

from gazenotes.screenbuffer import BufferedFrame, ScreenBuffer

PNG = b"\x89PNG\r\n\x1a\n"


class FakeClock:
    """A hand-cranked clock, so nothing in these tests waits on real time."""

    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> float:
        self.t += dt
        return self.t


def buffer_of(frames, **kwargs) -> ScreenBuffer:
    """A buffer pre-filled with ``(t, data)`` pairs and no live capture."""
    buffer = ScreenBuffer(capture=lambda: None, **kwargs)
    for t, data in frames:
        buffer.add(data, t)
    return buffer


# -- bounds -------------------------------------------------------------
def test_frames_older_than_the_window_are_dropped():
    buffer = buffer_of([(i, PNG + bytes([i])) for i in range(120)], seconds=60.0)
    kept = buffer.snapshot()
    assert kept[0].t >= kept[-1].t - 60.0
    assert len(kept) < 120


def test_the_byte_cap_evicts_the_oldest_frames_first():
    # Age alone would keep all of these; the cap is what stops a minute of
    # Retina PNGs from becoming hundreds of megabytes of resident memory.
    buffer = buffer_of([(float(i), b"x" * 100) for i in range(10)], seconds=1000.0, max_bytes=450)
    assert buffer.bytes_held <= 450
    assert [frame.t for frame in buffer.snapshot()] == [6.0, 7.0, 8.0, 9.0]


def test_a_frame_larger_than_the_whole_budget_is_not_held():
    # The cap is a promise about memory, so an oversized frame is dropped
    # rather than quietly blowing through it.
    buffer = buffer_of([(1.0, b"x" * 5000)], max_bytes=1000)
    assert len(buffer) == 0
    assert buffer.bytes_held == 0


def test_bytes_held_tracks_evictions_not_just_additions():
    buffer = buffer_of([(float(i), b"x" * 100) for i in range(5)], seconds=2.5)
    assert buffer.bytes_held == len(buffer) * 100
    buffer.clear()
    assert buffer.bytes_held == 0 and len(buffer) == 0


# -- selection ----------------------------------------------------------
def test_frame_at_never_returns_a_frame_from_after_the_moment_asked_for():
    # The user spoke at t=5; the frame from t=6 shows whatever they scrolled
    # to next, which is exactly the wrong screenshot to attach.
    buffer = buffer_of([(4.0, b"before"), (6.0, b"after")])
    frame = buffer.frame_at(5.0)
    assert frame is not None
    assert frame.data == b"before"


def test_frame_at_picks_the_nearest_earlier_frame():
    buffer = buffer_of([(1.0, b"a"), (3.0, b"b"), (4.9, b"c"), (9.0, b"d")])
    assert buffer.frame_at(5.0).data == b"c"
    assert buffer.frame_at(4.9).data == b"c"  # at-or-before includes exact hits
    assert buffer.frame_at(100.0).data == b"d"


def test_frame_at_is_none_when_every_frame_is_too_late():
    buffer = buffer_of([(10.0, PNG)])
    assert buffer.frame_at(9.0) is None


def test_frame_at_is_none_on_an_empty_buffer():
    assert ScreenBuffer(capture=lambda: None).frame_at(123.0) is None


# -- capture ------------------------------------------------------------
def test_a_capture_that_returns_none_stores_nothing():
    buffer = ScreenBuffer(capture=lambda: None)
    assert buffer.poll_once() is False
    assert len(buffer) == 0


def test_a_capture_that_raises_is_swallowed():
    # Screen recording permission can be revoked mid-run; that must downgrade
    # the next note, not kill the thread every later note depends on.
    def explode():
        raise OSError("screen recording not permitted")

    buffer = ScreenBuffer(capture=explode)
    assert buffer.poll_once() is False
    assert len(buffer) == 0


def test_poll_stamps_frames_with_the_clock():
    clock = FakeClock()
    buffer = ScreenBuffer(capture=lambda: PNG, clock=clock)
    buffer.poll_once()
    clock.advance(2.0)
    buffer.poll_once()
    assert [frame.t for frame in buffer.snapshot()] == [1000.0, 1002.0]


def test_an_unstarted_buffer_never_calls_its_capture():
    calls = {"n": 0}

    def counted():
        calls["n"] += 1
        return PNG

    buffer = ScreenBuffer(capture=counted)
    assert calls["n"] == 0  # default-off must cost nothing
    assert len(buffer) == 0 and not buffer.running


# -- the thread ---------------------------------------------------------
def test_the_thread_captures_until_stopped_and_survives_failures():
    captured = threading.Event()
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("first capture failed")
        captured.set()
        return PNG

    buffer = ScreenBuffer(capture=flaky, interval=0.01)
    assert buffer.start() is True
    assert buffer.start() is True  # idempotent: resume need not track state
    try:
        assert captured.wait(5.0)
        assert buffer.running
    finally:
        buffer.stop(timeout=5.0)
    assert not buffer.running
    assert len(buffer) >= 1  # frames outlive the thread until cleared
    assert calls["n"] >= 2  # it kept going after the first capture blew up


# -- disk ---------------------------------------------------------------
def test_nothing_reaches_disk_without_an_explicit_write(tmp_path, monkeypatch):
    # The whole justification for the module: a rolling screen recording is
    # only acceptable while it stays in memory.
    monkeypatch.chdir(tmp_path)  # catches a stray relative-path write too
    buffer = ScreenBuffer(capture=lambda: PNG * 100, interval=0.01)
    buffer.start()
    try:
        for _ in range(5):
            buffer.poll_once()
    finally:
        buffer.stop(timeout=5.0)
    buffer.clear()
    assert list(tmp_path.iterdir()) == []


def test_write_frame_at_writes_the_buffered_bytes_verbatim(tmp_path):
    buffer = buffer_of([(4.0, PNG + b"before"), (6.0, PNG + b"after")])
    destination = tmp_path / "captures" / "2026-09-01" / "143022.pre.png"
    written = buffer.write_frame_at(5.0, destination)
    assert written == destination
    assert destination.read_bytes() == PNG + b"before"  # parent dirs made on demand


def test_write_frame_at_returns_none_and_creates_nothing_when_empty(tmp_path):
    buffer = ScreenBuffer(capture=lambda: None)
    destination = tmp_path / "captures" / "143022.pre.png"
    assert buffer.write_frame_at(5.0, destination) is None
    assert not destination.exists()
    assert not destination.parent.exists()


def test_write_frame_at_returns_none_when_only_later_frames_exist(tmp_path):
    buffer = buffer_of([(10.0, PNG)])
    assert buffer.write_frame_at(9.0, tmp_path / "shot.png") is None
    assert list(tmp_path.iterdir()) == []


# -- concurrency --------------------------------------------------------
def test_reads_and_writes_can_race_without_corrupting_the_window():
    buffer = ScreenBuffer(capture=lambda: None, seconds=5.0)
    stop = threading.Event()

    def writer():
        t = 0.0
        while not stop.is_set():
            t += 0.1
            buffer.add(b"x" * 64, t)

    thread = threading.Thread(target=writer, daemon=True)
    thread.start()
    try:
        for _ in range(500):
            # Any snapshot taken mid-flight must be a coherent, ordered window,
            # never a half-evicted one.
            frames = buffer.snapshot()
            assert all(isinstance(f, BufferedFrame) for f in frames)
            assert [f.t for f in frames] == sorted(f.t for f in frames)
            assert not frames or frames[-1].t - frames[0].t <= 5.0
    finally:
        stop.set()
        thread.join(timeout=5.0)

    # Quiescent again: the byte count must match what survived, not what was added.
    assert buffer.bytes_held == len(buffer) * 64
