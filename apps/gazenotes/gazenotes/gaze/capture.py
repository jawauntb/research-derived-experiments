"""The webcam gaze engine: a background thread that fills a ring buffer.

OpenCV and MediaPipe are imported lazily inside :meth:`GazeEngine.start`. If
either is missing — or the camera is covered, or the display is uncalibrated —
the engine reports itself unavailable and every fixation query returns ``None``.
Captures still happen; they just fall back to a full-screen screenshot.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from ..events import Fixation, GazeSample
from ..geometry import Point, Rect
from . import features as feat
from .model import GazeRingBuffer, OneEuroFilter, dominant_fixation, sample_confidence
from .regress import RidgeModel, load_calibration_entry

log = logging.getLogger(__name__)

__all__ = ["GazeEngine", "GazeStatus", "landmarks_from_result"]


@dataclass
class GazeStatus:
    """Why gaze is or is not working, for ``doctor`` and the menu bar."""

    available: bool
    reason: str = ""
    calibrated: bool = False
    frames: int = 0
    fps: float = 0.0


def landmarks_from_result(result) -> list[tuple[float, float, float]] | None:
    """Extract the first face's landmarks from a MediaPipe result.

    Split out so the frame → feature path can be exercised with a stub result
    object in tests.
    """
    faces = getattr(result, "multi_face_landmarks", None)
    if not faces:
        return None
    return [(lm.x, lm.y, lm.z) for lm in faces[0].landmark]


class GazeEngine:
    """Owns the camera thread, the calibration model, and the ring buffer."""

    def __init__(
        self,
        *,
        screen: Rect,
        calibration_path: Path | str | None = None,
        display_key: str = "main",
        camera_index: int = 0,
        frame_size: tuple[int, int] = (640, 480),
        target_fps: float = 30.0,
        buffer_seconds: float = 5.0,
    ) -> None:
        self.screen = screen
        self.calibration_path = Path(calibration_path).expanduser() if calibration_path else None
        self.display_key = display_key
        self.camera_index = camera_index
        self.frame_size = frame_size
        self.target_fps = target_fps
        self.buffer = GazeRingBuffer(seconds=buffer_seconds)

        self.model: RidgeModel | None = None
        self._reference_features: list[float] | None = None
        self._latest_features: list[float] | None = None
        self._filter_x = OneEuroFilter()
        self._filter_y = OneEuroFilter()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._status = GazeStatus(available=False, reason="not started")
        self._frames = 0
        self._started_at = 0.0

    # -- lifecycle ------------------------------------------------------
    @property
    def status(self) -> GazeStatus:
        elapsed = max(1e-6, time.time() - self._started_at) if self._started_at else 0.0
        return GazeStatus(
            available=self._status.available,
            reason=self._status.reason,
            calibrated=self.model is not None,
            frames=self._frames,
            fps=(self._frames / elapsed) if elapsed else 0.0,
        )

    def load_calibration(self) -> bool:
        """Load this display's model and the head pose it was fitted at.

        Also resets the smoothing filters: predictions from the old model are
        not on the same scale as the new one, and carrying that state across a
        recalibration drags the first second of gaze toward the old fit.
        """
        if self.calibration_path is None:
            return False
        entry = load_calibration_entry(self.calibration_path, self.display_key)
        if entry is None:
            self.model = None
            return False
        self.model = RidgeModel.from_dict(entry)
        reference = entry.get("reference_features")
        self.set_reference_features(reference if isinstance(reference, list) else None)
        self._filter_x.reset()
        self._filter_y.reset()
        self.buffer.clear()
        return True

    def start(
        self,
        on_sample: Callable[[GazeSample], None] | None = None,
        *,
        require_calibration: bool = True,
    ) -> GazeStatus:
        """Start the camera thread. Never raises: failures land in ``status``.

        ``require_calibration=False`` is for calibration itself, which needs
        raw feature vectors before any model exists.
        """
        if self._thread is not None and self._thread.is_alive():
            return self.status
        try:
            import cv2  # noqa: F401
            import mediapipe  # noqa: F401
        except ImportError as exc:  # pragma: no cover - depends on host
            self._status = GazeStatus(available=False, reason=f"missing dependency: {exc.name}")
            return self._status

        self.load_calibration()
        if self.model is None and require_calibration:
            self._status = GazeStatus(
                available=False,
                reason="no calibration for this display; run `gazenotes calibrate`",
            )
            return self._status

        self._stop.clear()
        self._started_at = time.time()
        self._frames = 0  # so the reported fps is for this run, not all of them
        self._thread = threading.Thread(
            target=self._run, args=(on_sample,), name="gazenotes-camera", daemon=True
        )
        self._thread.start()
        self._status = GazeStatus(
            available=True, reason="running", calibrated=self.model is not None
        )
        return self._status

    def stop(self, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None
        self._status = GazeStatus(available=False, reason="stopped")

    # -- the loop -------------------------------------------------------
    def _run(self, on_sample: Callable[[GazeSample], None] | None) -> None:  # pragma: no cover - hardware
        import cv2
        import mediapipe as mp

        capture = cv2.VideoCapture(self.camera_index)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_size[0])
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_size[1])
        if not capture.isOpened():
            self._status = GazeStatus(available=False, reason="camera did not open")
            return

        mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        frame_interval = 1.0 / self.target_fps
        try:
            while not self._stop.is_set():
                loop_start = time.time()
                ok, frame = capture.read()
                if not ok:
                    time.sleep(frame_interval)
                    continue
                result = mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                landmarks = landmarks_from_result(result)
                self._store_features(landmarks)
                sample = self.sample_from_landmarks(landmarks, time.time())
                if sample is not None:
                    self.buffer.add(sample)
                    self._frames += 1
                    if on_sample is not None:
                        on_sample(sample)
                slack = frame_interval - (time.time() - loop_start)
                if slack > 0:
                    time.sleep(slack)
        finally:
            capture.release()
            mesh.close()

    # -- frame → sample -------------------------------------------------
    def sample_from_landmarks(
        self, landmarks: Sequence[Sequence[float]] | None, t: float
    ) -> GazeSample | None:
        """Turn one frame's landmarks into a screen-space sample.

        Returns a zero-confidence sample (rather than ``None``) when a face is
        present but unusable, so blink runs stay visible to
        :func:`~gazenotes.gaze.model.hold_through_blinks`.
        """
        if self.model is None:
            return None
        if landmarks is None:
            return GazeSample(t, 0.0, 0.0, 0.0)

        try:
            vector = feat.feature_vector(landmarks)
        except (IndexError, ValueError):
            return GazeSample(t, 0.0, 0.0, 0.0)

        open_eyes = feat.eyes_open(landmarks)
        raw_x, raw_y = self.model.predict(vector)
        x = self._filter_x(raw_x, t)
        y = self._filter_y(raw_y, t)

        on_screen = self.screen.contains(Point(x, y))
        pose_ok = (
            self._reference_features is None
            or feat.head_pose_in_range(vector, self._reference_features)
        )
        confidence = sample_confidence(
            face_found=True,
            eyes_open=open_eyes,
            head_pose_ok=pose_ok,
            on_screen=on_screen,
        )
        return GazeSample(t, x, y, confidence)

    def _store_features(self, landmarks: Sequence[Sequence[float]] | None) -> None:
        """Keep the most recent feature vector so calibration can sample it."""
        if landmarks is None or not feat.eyes_open(landmarks):
            self._latest_features = None
            return
        try:
            self._latest_features = feat.feature_vector(landmarks)
        except (IndexError, ValueError):
            self._latest_features = None

    def current_features(self) -> list[float] | None:
        """The latest usable feature vector, or ``None`` if the face is lost."""
        return list(self._latest_features) if self._latest_features is not None else None

    def set_reference_features(self, vector: Sequence[float] | None) -> None:
        """Record the head pose seen during calibration, for drift detection."""
        self._reference_features = list(vector) if vector is not None else None

    # -- queries --------------------------------------------------------
    def dominant_fixation(self, t0: float, t1: float, *, cell: float = 120.0) -> Fixation | None:
        """Where the user was looking over ``[t0, t1]``, or ``None``."""
        from .model import hold_through_blinks

        samples = hold_through_blinks(self.buffer.window(t0, t1))
        return dominant_fixation(samples, cell=cell)
