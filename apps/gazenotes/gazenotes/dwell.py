"""Dwell scrolling: look at the bottom of the screen for a while, page moves.

Off by default, and it should stay that way for most people. Dwell is the one
place in gazenotes where *looking* causes an action, which walks straight into
the Midas touch problem: the eyes are an input device you cannot switch off, so
every naive implementation eventually scrolls the page while you are still
reading it. Three things make a naive version infuriating, and each has an
answer here:

* **A single stray sample fires it.** Webcam gaze is noisy and a saccade to the
  bottom of the window costs 30 ms. :class:`DwellScroller` requires the gaze to
  be *continuously* in the zone for ``dwell_seconds``; one frame in the band is
  not a dwell, and a look away restarts the clock.
* **It repeats while you think.** People park their eyes at the end of a
  paragraph while thinking, which under a plain "dwell then re-dwell" rule is a
  runaway scroll. After firing, this scroller latches: the same zone cannot
  fire again until a confident sample is seen *outside* it. Deliberate paging
  costs a glance away and back, resting your eyes costs nothing.
* **It fires when it cannot see you.** A lost face, a blink misread as a stare,
  a stale buffer after the camera thread died — all of them must mean "no
  signal", never "scroll". Samples below ``min_confidence`` never start or
  extend a dwell, though a *short* dropout is treated as a blink rather than as
  a look away, because a 400 ms dwell that any blink resets can never be
  completed.

Everything above lives in :class:`DwellScroller`, which is pure apart from its
own cooldown clock: it takes samples, a screen rect and ``now``, and returns a
decision. :class:`DwellDriver` is the thin, untested-by-design layer that polls
the gaze ring buffer on a thread and calls a scroll callable.

Zone membership uses :meth:`gazenotes.geometry.Rect.contains`, so the bands are
half-open in the same way as every other rectangle in the app, and a screen
whose origin is not ``(0, 0)`` (an external display) works without special
casing.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .events import GazeSample
from .geometry import Point, Rect

log = logging.getLogger(__name__)

__all__ = ["DwellConfig", "DwellDecision", "DwellScroller", "DwellDriver"]

TOP = "top"
BOTTOM = "bottom"
ELSEWHERE = "elsewhere"


@dataclass(frozen=True)
class DwellConfig:
    """Tuning for dwell scrolling. The defaults are the ones from the design.

    ``zone_fraction`` is deliberately large (15% of screen height, ~170 pt on a
    laptop) because webcam gaze is only trustworthy at about a sixth of screen
    height — a smaller band would be below the noise floor.
    """

    zone_fraction: float = 0.15
    dwell_seconds: float = 0.4
    cooldown_seconds: float = 1.5
    scroll_amount: float = 400.0
    min_confidence: float = 0.5
    blink_seconds: float = 0.2
    """Longest confidence dropout treated as a blink rather than a look away.

    Blinks last 100–200 ms and land inside almost every 400 ms dwell; without
    this tolerance the feature would essentially never fire. Anything longer is
    a lost face, and a lost face must not scroll.
    """

    def __post_init__(self) -> None:
        if not 0.0 < self.zone_fraction <= 0.5:
            raise ValueError("zone_fraction must be in (0, 0.5]; larger and the bands overlap")
        if self.dwell_seconds <= 0.0:
            raise ValueError("dwell_seconds must be positive; a zero dwell is a hair trigger")


@dataclass(frozen=True)
class DwellDecision:
    """One scroll the dwell logic decided to perform.

    ``scroll`` is signed the way ``page.mouse.wheel`` is: positive moves the
    content up (reading onward), negative moves it back.
    """

    scroll: float
    reason: str


class DwellScroller:
    """Decides whether a window of gaze samples has earned a scroll.

    Pure apart from its own state — the cooldown deadline and the latched zone.
    No I/O, no threads, no clock of its own: the caller passes ``now``.
    """

    def __init__(self, config: DwellConfig | None = None) -> None:
        self.config = config or DwellConfig()
        self._cooldown_until = 0.0
        self._latched_zone: str | None = None
        self._latched_t = 0.0

    def reset(self) -> None:
        """Forget the cooldown and the latch (on enable, or after a pause)."""
        self._cooldown_until = 0.0
        self._latched_zone = None
        self._latched_t = 0.0

    def cooldown_remaining(self, now: float) -> float:
        return max(0.0, self._cooldown_until - now)

    # -- zones ----------------------------------------------------------
    def zones(self, screen: Rect) -> tuple[Rect, Rect]:
        """The top and bottom bands of ``screen``, in the screen's own units."""
        band = screen.h * self.config.zone_fraction
        return (
            Rect(screen.x, screen.y, screen.w, band),
            Rect(screen.x, screen.bottom - band, screen.w, band),
        )

    def _classify(self, sample: GazeSample, screen: Rect) -> str | None:
        """``TOP`` / ``BOTTOM`` / ``ELSEWHERE``, or ``None`` for "cannot see"."""
        if sample.confidence < self.config.min_confidence:
            return None
        top, bottom = self.zones(screen)
        point = Point(sample.x, sample.y)
        if top.contains(point):
            return TOP
        if bottom.contains(point):
            return BOTTOM
        return ELSEWHERE

    # -- the decision ---------------------------------------------------
    def decide(
        self, samples: Sequence[GazeSample], screen: Rect, now: float
    ) -> DwellDecision | None:
        """Return a scroll to perform, or ``None``, given ``samples`` (oldest first)."""
        if not samples:
            return None

        latest = samples[-1]
        if now - latest.t > self.config.dwell_seconds:
            # The buffer stopped filling: camera paused, thread dead, machine
            # asleep. A frozen window of samples is not a sustained dwell.
            return None

        self._clear_latch_if_left(samples, screen)

        if now < self._cooldown_until:
            return None

        zone = self._classify(latest, screen)
        if zone not in (TOP, BOTTOM):
            return None

        held_since = self._run_start(samples, screen, zone)
        if latest.t - held_since < self.config.dwell_seconds:
            return None

        if zone == self._latched_zone:
            # Already scrolled for this stare. Resting your eyes at the end of a
            # paragraph must not page the document out from under you; the user
            # has to look away and back to ask for another one.
            return None

        self._cooldown_until = now + self.config.cooldown_seconds
        self._latched_zone = zone
        self._latched_t = latest.t
        amount = self.config.scroll_amount if zone == BOTTOM else -self.config.scroll_amount
        return DwellDecision(
            scroll=amount,
            reason=f"{zone} dwell {latest.t - held_since:.2f} s → scroll {amount:+.0f}",
        )

    def _run_start(self, samples: Sequence[GazeSample], screen: Rect, zone: str) -> float:
        """Timestamp of the oldest sample in the unbroken run ending at the newest.

        Walks backwards and stops at the first confident sample that is not in
        ``zone``. Dropouts shorter than ``blink_seconds`` are stepped over.
        """
        start = last_good = samples[-1].t
        hole_edge: float | None = None
        for sample in reversed(samples[:-1]):
            kind = self._classify(sample, screen)
            if kind is None:
                if hole_edge is None:
                    hole_edge = last_good
                if hole_edge - sample.t > self.config.blink_seconds:
                    break  # long enough to be a lost face, not a blink
                continue
            if kind != zone:
                break
            hole_edge = None
            last_good = start = sample.t
        return start

    def _clear_latch_if_left(self, samples: Sequence[GazeSample], screen: Rect) -> None:
        """Unlatch once we actually observe the gaze leaving the fired zone.

        Only samples newer than the fire count, and only an *observed* exit
        clears the latch — inferring one from a gap would let the ring buffer
        ageing out the old samples fake it, and that is the runaway case.
        """
        if self._latched_zone is None:
            return
        for sample in reversed(samples):
            if sample.t <= self._latched_t:
                return
            kind = self._classify(sample, screen)
            if kind is None:
                continue
            if kind != self._latched_zone:
                self._latched_zone = None
                self._latched_t = 0.0
                return


class DwellDriver:
    """Polls a gaze engine's ring buffer and performs the scrolls it earns.

    Off unless ``enabled`` is set *and* :meth:`start` is called, because dwell
    scrolling is exactly the kind of feature that some reading styles hate. All
    the logic worth testing is in :class:`DwellScroller`; this layer only owns
    the thread and swallows failures, so a dead camera or a closed page never
    takes the daemon down with it.
    """

    def __init__(
        self,
        *,
        gaze=None,
        screen: Rect | None = None,
        scroll: Callable[[float], object] | None = None,
        config: DwellConfig | None = None,
        enabled: bool = False,
        interval: float = 0.05,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.gaze = gaze
        self.screen = screen if screen is not None else getattr(gaze, "screen", None)
        self.scroll = scroll
        self.scroller = DwellScroller(config)
        self.enabled = enabled
        self.interval = interval
        self.clock = clock
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # -- lifecycle ------------------------------------------------------
    def start(self) -> str:
        """Start polling. Never raises; returns a line for the log or menu bar."""
        if not self.enabled:
            return "dwell scrolling is off"
        if self.running:
            return "dwell scrolling already on"
        if self.scroll is None or self.screen is None:
            return "dwell scrolling has nothing to scroll"
        self.scroller.reset()
        self._stop.clear()
        try:
            self._thread = threading.Thread(target=self._run, name="gazenotes-dwell", daemon=True)
            self._thread.start()
        except Exception as exc:  # noqa: BLE001 - a missing thread is not fatal
            log.warning("dwell scrolling could not start: %s", exc)
            self._thread = None
            return f"dwell scrolling failed to start: {exc}"
        return "dwell scrolling on"

    def stop(self, timeout: float = 2.0) -> str:
        """Stop polling. Never raises, and is safe to call when not running."""
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.join(timeout=timeout)
        self.scroller.reset()
        return "dwell scrolling off"

    def set_enabled(self, on: bool) -> str:
        """The toggle: flips the flag and starts or stops to match."""
        self.enabled = on
        return self.start() if on else self.stop()

    def toggle(self) -> str:
        return self.set_enabled(not self.enabled)

    # -- one tick -------------------------------------------------------
    def poll(self, now: float | None = None) -> DwellDecision | None:
        """One decision cycle. Never raises; returns what it did, if anything."""
        if not self.enabled or self.scroll is None or self.screen is None:
            return None
        buffer = getattr(self.gaze, "buffer", None)
        if buffer is None:
            return None
        try:
            samples = buffer.snapshot()
            decision = self.scroller.decide(samples, self.screen, self.clock() if now is None else now)
            if decision is None:
                return None
            self.scroll(decision.scroll)
            log.debug("dwell: %s", decision.reason)
            return decision
        except Exception:  # noqa: BLE001 - degrade, never block
            log.exception("dwell poll failed")
            return None

    def _run(self) -> None:
        while not self._stop.is_set():
            self.poll()
            self._stop.wait(self.interval)
