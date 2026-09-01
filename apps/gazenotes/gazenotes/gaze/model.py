"""Gaze smoothing, the sample ring buffer, and fixation detection.

Pure Python and pure logic: everything here works on ``GazeSample`` values, so
the interesting behaviour (blink holds, fixation binning, confidence) is
testable without a camera.
"""

from __future__ import annotations

import math
import threading
from collections import deque
from collections.abc import Iterable, Sequence

from ..events import Fixation, GazeSample

__all__ = ["OneEuroFilter", "GazeRingBuffer", "dominant_fixation", "sample_confidence"]


class OneEuroFilter:
    """One-euro filter: heavy smoothing when still, light when moving fast.

    Chosen over a fixed EMA because reading alternates between long fixations
    (where jitter is the enemy) and fast saccades (where lag is the enemy).
    """

    def __init__(self, min_cutoff: float = 0.8, beta: float = 0.0005, d_cutoff: float = 1.0) -> None:
        """``beta`` is per screen-point-per-second: reading jitter runs at a few
        hundred pt/s and saccades at tens of thousands, so a small beta is what
        separates them. These defaults cut jitter by ~two thirds while reaching
        90% of a saccade within five frames at 30 fps."""
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self._t: float | None = None
        self._x: float | None = None
        self._dx: float = 0.0

    @staticmethod
    def _alpha(cutoff: float, dt: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def reset(self) -> None:
        self._t = self._x = None
        self._dx = 0.0

    def __call__(self, value: float, t: float) -> float:
        if self._t is None or self._x is None or t <= self._t:
            self._t, self._x, self._dx = t, value, 0.0
            return value
        dt = t - self._t
        dx = (value - self._x) / dt
        self._dx += self._alpha(self.d_cutoff, dt) * (dx - self._dx)
        cutoff = self.min_cutoff + self.beta * abs(self._dx)
        self._x += self._alpha(cutoff, dt) * (value - self._x)
        self._t = t
        return self._x


class GazeRingBuffer:
    """Thread-safe rolling window of gaze samples (default 5 s at 30 Hz).

    The camera thread writes; the capture path reads. Nothing here touches
    disk — gaze history is never persisted.
    """

    def __init__(self, seconds: float = 5.0, max_rate_hz: float = 60.0) -> None:
        self.seconds = seconds
        self._samples: deque[GazeSample] = deque(maxlen=int(seconds * max_rate_hz) + 1)
        self._lock = threading.Lock()

    def add(self, sample: GazeSample) -> None:
        with self._lock:
            self._samples.append(sample)
            cutoff = sample.t - self.seconds
            while self._samples and self._samples[0].t < cutoff:
                self._samples.popleft()

    def clear(self) -> None:
        with self._lock:
            self._samples.clear()

    def snapshot(self) -> list[GazeSample]:
        with self._lock:
            return list(self._samples)

    def window(self, t0: float, t1: float) -> list[GazeSample]:
        """Samples with ``t0 <= t <= t1``."""
        return [s for s in self.snapshot() if t0 <= s.t <= t1]

    def __len__(self) -> int:
        with self._lock:
            return len(self._samples)


def sample_confidence(
    *,
    face_found: bool,
    eyes_open: bool,
    head_pose_ok: bool,
    on_screen: bool,
    landmark_quality: float = 1.0,
) -> float:
    """Per-frame confidence in [0, 1].

    Multiplicative: any hard failure (no face, closed eyes) drives the sample to
    zero rather than letting a good head pose average it back up.
    """
    if not face_found or not eyes_open:
        return 0.0
    score = max(0.0, min(1.0, landmark_quality))
    if not head_pose_ok:
        score *= 0.5
    if not on_screen:
        score *= 0.3
    return score


def dominant_fixation(
    samples: Iterable[GazeSample],
    *,
    cell: float = 120.0,
    min_confidence: float = 0.05,
    display_id: int = 0,
) -> Fixation | None:
    """The busiest ~``cell``-sized region of the gaze window.

    Bins samples into a grid, takes the most-populated cell, and returns its
    confidence-weighted centroid. Fixation confidence is the share of samples
    landing in that cell times their mean per-sample confidence, so a scattered
    window (the user scanned the whole page) scores low even when every
    individual frame was clean.
    """
    usable = [s for s in samples if s.confidence > min_confidence]
    if not usable:
        return None

    bins: dict[tuple[int, int], list[GazeSample]] = {}
    for sample in usable:
        key = (int(math.floor(sample.x / cell)), int(math.floor(sample.y / cell)))
        bins.setdefault(key, []).append(sample)

    best = max(bins.values(), key=lambda group: (sum(s.confidence for s in group), len(group)))
    weight = sum(s.confidence for s in best)
    if weight <= 0.0:
        return None
    cx = sum(s.x * s.confidence for s in best) / weight
    cy = sum(s.y * s.confidence for s in best) / weight
    share = len(best) / len(usable)
    mean_conf = weight / len(best)
    return Fixation(
        x=cx,
        y=cy,
        confidence=max(0.0, min(1.0, share * mean_conf)),
        sample_count=len(best),
        display_id=display_id,
    )


def hold_through_blinks(samples: Sequence[GazeSample], *, gap: float = 0.4) -> list[GazeSample]:
    """Replace short zero-confidence runs with the last good sample.

    A blink is not a look-away: dropping those frames biases the fixation
    toward whatever the eyes did on reopening.
    """
    out: list[GazeSample] = []
    pending: list[GazeSample] = []
    last_good: GazeSample | None = None
    for sample in samples:
        if sample.confidence > 0.0:
            if pending and last_good is not None and pending[-1].t - pending[0].t <= gap:
                out.extend(
                    GazeSample(p.t, last_good.x, last_good.y, last_good.confidence * 0.5)
                    for p in pending
                )
            pending = []
            last_good = sample
            out.append(sample)
        else:
            pending.append(sample)
    out.extend(pending)
    return out
