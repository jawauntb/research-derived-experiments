"""A rolling window of recent screenshots, held in memory and nowhere else.

By the time you say "note that", the thing you meant has often already
scrolled away — the screenshot the pipeline takes is of the *next* paragraph.
This module keeps the last minute of screen in RAM so a note can reach back to
the frame that was up when the sentence started.

That is a recording of your screen, so the constraint is the whole point:
frames exist only as :class:`bytes` inside this object, and the single way any
of them reaches disk is an explicit :meth:`ScreenBuffer.write_frame_at` call
made because a note actually fired. Nothing here opens a file otherwise, and
:meth:`ScreenBuffer.clear` makes the window disappear.

The buffer is bounded on two axes, because either one alone is a leak: a
minute of Retina PNGs is several hundred megabytes, so ``max_bytes`` is what
actually keeps the daemon's footprint flat, while ``seconds`` is what keeps the
privacy promise that nothing older than the window survives.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

__all__ = ["BufferedFrame", "ScreenBuffer"]


@dataclass(frozen=True)
class BufferedFrame:
    """One encoded screenshot and the epoch second it was taken."""

    t: float
    data: bytes

    @property
    def nbytes(self) -> int:
        return len(self.data)


class ScreenBuffer:
    """Thread-safe rolling window of encoded screenshots (default 60 s).

    A background thread writes; the capture path reads. Construction is inert:
    nothing is captured, no thread exists and no file is touched until
    :meth:`start` is called, so the daemon can hold one of these while the
    feature is switched off and pay nothing for it.
    """

    def __init__(
        self,
        *,
        capture: Callable[[], bytes | None],
        seconds: float = 60.0,
        interval: float = 2.0,
        max_bytes: int = 256 * 1024 * 1024,
        clock: Callable[[], float] = time.time,
    ) -> None:
        """``capture`` returns an encoded PNG of the current screen, or ``None``.

        It is injected rather than taken from :mod:`gazenotes.screen` so the
        buffer can be exercised without a display — and so the daemon can hand
        it a capture that already knows which screen to grab.
        """
        self.seconds = seconds
        self.interval = interval
        self.max_bytes = max_bytes
        self._capture = capture
        self._clock = clock
        self._frames: deque[BufferedFrame] = deque()
        self._bytes = 0
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    # -- lifecycle ------------------------------------------------------
    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> bool:
        """Start the capture thread. Never raises; returns whether it is running.

        Starting twice is a no-op, so the daemon can call this on resume
        without tracking state.
        """
        if self.running:
            return True
        self._stop.clear()
        thread = threading.Thread(target=self._run, name="gazenotes-screenbuffer", daemon=True)
        try:
            thread.start()
        except RuntimeError as exc:  # pragma: no cover - only at interpreter shutdown
            log.warning("screen buffer did not start: %s", exc)
            self._thread = None
            return False
        self._thread = thread
        return True

    def stop(self, timeout: float = 2.0) -> None:
        """Stop capturing. The frames already held stay in memory until cleared."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def _run(self) -> None:
        while not self._stop.is_set():
            self.poll_once()
            # wait() rather than sleep(): stop() gets an immediate exit instead
            # of one that lags by up to a whole capture interval.
            self._stop.wait(self.interval)

    def poll_once(self) -> bool:
        """One capture attempt. Returns whether a frame was stored.

        Swallows everything the capture callable can throw: a screenshot that
        fails because the display slept, or because permission was revoked
        mid-run, must downgrade the next note rather than kill the thread that
        feeds every note after it.
        """
        try:
            data = self._capture()
        except Exception as exc:  # any failure the screen backend can raise is survivable
            log.debug("screen buffer capture failed: %s", exc)
            return False
        if not data:
            return False
        self.add(bytes(data), self._clock())
        return True

    # -- the window -----------------------------------------------------
    def add(self, data: bytes, t: float | None = None) -> BufferedFrame:
        """Store one frame and evict whatever no longer fits.

        ``t`` is expected to be on this buffer's own clock; a frame stamped
        outside the window is evicted immediately, by the same rule as any
        other stale frame.
        """
        frame = BufferedFrame(self._clock() if t is None else t, data)
        with self._lock:
            self._frames.append(frame)
            self._bytes += frame.nbytes
            self._evict_locked()
        return frame

    def _evict_locked(self) -> None:
        """Oldest-first on both axes: age, then total bytes.

        Age is measured against the **clock**, not against the newest frame.
        Keying it off arrivals would mean a stalled capture — a slept display,
        a revoked permission — froze eviction too, leaving minutes of screen
        resident in a buffer documented as holding seconds. The window is a
        promise about what is in memory *now*, so it has to expire on its own.

        The byte cap is enforced strictly, even when that empties the buffer —
        a single frame larger than the whole budget is dropped rather than
        quietly held, because the cap is a promise about resident memory.
        """
        cutoff = self._clock() - self.seconds
        while self._frames and self._frames[0].t < cutoff:
            self._bytes -= self._frames.popleft().nbytes
        while self._frames and self._bytes > self.max_bytes:
            self._bytes -= self._frames.popleft().nbytes

    def frame_at(self, t: float) -> BufferedFrame | None:
        """The newest frame taken at or before ``t``, or ``None``.

        Never a later one: the point is the screen as it was when the user
        started speaking, and a frame from after that is exactly the wrong
        answer — it shows whatever they scrolled to next.
        """
        with self._lock:
            self._evict_locked()
            best: BufferedFrame | None = None
            for frame in self._frames:
                if frame.t <= t and (best is None or frame.t >= best.t):
                    best = frame
            return best

    def snapshot(self) -> list[BufferedFrame]:
        with self._lock:
            self._evict_locked()
            return list(self._frames)

    def clear(self) -> None:
        with self._lock:
            self._frames.clear()
            self._bytes = 0

    @property
    def bytes_held(self) -> int:
        with self._lock:
            self._evict_locked()
            return self._bytes

    def __len__(self) -> int:
        with self._lock:
            self._evict_locked()
            return len(self._frames)

    # -- the one way out ------------------------------------------------
    def write_frame_at(self, t: float, destination: Path) -> Path | None:
        """Write the frame for ``t`` to ``destination``; the only disk write here.

        Returns ``None`` when the buffer holds nothing from at or before ``t``,
        or when the write itself fails — the note is still written, just
        without the earlier screenshot.
        """
        frame = self.frame_at(t)
        if frame is None:
            return None
        destination = Path(destination)
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(frame.data)
        except OSError as exc:
            log.warning("could not write buffered frame: %s", exc)
            return None
        return destination
