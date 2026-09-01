"""MediaPipe face-mesh landmarks → the feature vector the calibration fits.

Everything here takes plain ``(x, y, z)`` sequences in normalised image
coordinates, so the feature maths is testable without MediaPipe installed.

Landmark indices are MediaPipe Face Mesh with ``refine_landmarks=True``
(iris landmarks 468-477).
"""

from __future__ import annotations

from collections.abc import Sequence

__all__ = [
    "FEATURE_NAMES",
    "Landmarks",
    "eye_aspect_ratio",
    "iris_ratios",
    "head_pose_proxy",
    "feature_vector",
    "eyes_open",
]

# MediaPipe Face Mesh indices.
LEFT_IRIS = (468, 469, 470, 471, 472)
RIGHT_IRIS = (473, 474, 475, 476, 477)
LEFT_EYE_CORNERS = (33, 133)      # outer, inner
RIGHT_EYE_CORNERS = (362, 263)    # inner, outer
LEFT_EYE_LIDS = (159, 145)        # upper, lower
RIGHT_EYE_LIDS = (386, 374)
NOSE_TIP = 1
CHIN = 152
FOREHEAD = 10
LEFT_CHEEK = 234
RIGHT_CHEEK = 454

FEATURE_NAMES = [
    "iris_x_l",
    "iris_y_l",
    "iris_x_r",
    "iris_y_r",
    "yaw",
    "pitch",
    "roll",
    "face_cx",
    "face_cy",
    "face_w",
]

Landmarks = Sequence[Sequence[float]]


def _pt(landmarks: Landmarks, index: int) -> tuple[float, float]:
    point = landmarks[index]
    return float(point[0]), float(point[1])


def _centroid(landmarks: Landmarks, indices: Sequence[int]) -> tuple[float, float]:
    xs = [float(landmarks[i][0]) for i in indices]
    ys = [float(landmarks[i][1]) for i in indices]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def eye_aspect_ratio(landmarks: Landmarks, *, left: bool = True) -> float:
    """Lid separation over eye width. Drops sharply during a blink."""
    corners = LEFT_EYE_CORNERS if left else RIGHT_EYE_CORNERS
    lids = LEFT_EYE_LIDS if left else RIGHT_EYE_LIDS
    width = _dist(_pt(landmarks, corners[0]), _pt(landmarks, corners[1]))
    if width <= 1e-9:
        return 0.0
    height = _dist(_pt(landmarks, lids[0]), _pt(landmarks, lids[1]))
    return height / width


def eyes_open(landmarks: Landmarks, *, threshold: float = 0.16) -> bool:
    """True when at least one eye is open enough to trust its iris centre."""
    return max(eye_aspect_ratio(landmarks, left=True), eye_aspect_ratio(landmarks, left=False)) >= threshold


def iris_ratios(landmarks: Landmarks, *, left: bool = True) -> tuple[float, float]:
    """Iris centre as a fraction of the eye box, in [0, 1]-ish.

    Normalising against the eye's own corners and lids makes the feature
    largely invariant to how far the user is sitting from the camera; head
    rotation is handled separately by the pose features.
    """
    iris = LEFT_IRIS if left else RIGHT_IRIS
    corners = LEFT_EYE_CORNERS if left else RIGHT_EYE_CORNERS
    lids = LEFT_EYE_LIDS if left else RIGHT_EYE_LIDS

    cx, cy = _centroid(landmarks, iris)
    x0, _ = _pt(landmarks, corners[0])
    x1, _ = _pt(landmarks, corners[1])
    _, y0 = _pt(landmarks, lids[0])
    _, y1 = _pt(landmarks, lids[1])

    span_x = x1 - x0
    span_y = y1 - y0
    rx = (cx - x0) / span_x if abs(span_x) > 1e-9 else 0.5
    ry = (cy - y0) / span_y if abs(span_y) > 1e-9 else 0.5
    return rx, ry


def head_pose_proxy(landmarks: Landmarks) -> tuple[float, float, float]:
    """Cheap yaw/pitch/roll proxies from face-mesh geometry alone.

    Not a calibrated ``solvePnP`` pose: these are unitless, monotone-in-angle
    quantities. That is all the regression needs — it learns the mapping from
    these to screen position during calibration — and it keeps OpenCV out of
    the feature path.

    - **yaw**: nose offset between the cheeks, signed left/right.
    - **pitch**: nose height between forehead and chin, recentred.
    - **roll**: cheek-line tilt relative to the face width.
    """
    nose = _pt(landmarks, NOSE_TIP)
    left_cheek = _pt(landmarks, LEFT_CHEEK)
    right_cheek = _pt(landmarks, RIGHT_CHEEK)
    forehead = _pt(landmarks, FOREHEAD)
    chin = _pt(landmarks, CHIN)

    face_w = _dist(left_cheek, right_cheek)
    face_h = _dist(forehead, chin)
    if face_w <= 1e-9 or face_h <= 1e-9:
        return 0.0, 0.0, 0.0

    mid_x = 0.5 * (left_cheek[0] + right_cheek[0])
    yaw = (nose[0] - mid_x) / face_w
    pitch = (nose[1] - forehead[1]) / face_h - 0.5
    roll = (right_cheek[1] - left_cheek[1]) / face_w
    return yaw, pitch, roll


def face_box(landmarks: Landmarks) -> tuple[float, float, float]:
    """Face centre and width in normalised image units — a head-translation proxy."""
    left_cheek = _pt(landmarks, LEFT_CHEEK)
    right_cheek = _pt(landmarks, RIGHT_CHEEK)
    forehead = _pt(landmarks, FOREHEAD)
    chin = _pt(landmarks, CHIN)
    cx = 0.5 * (left_cheek[0] + right_cheek[0])
    cy = 0.5 * (forehead[1] + chin[1])
    return cx, cy, _dist(left_cheek, right_cheek)


def feature_vector(landmarks: Landmarks) -> list[float]:
    """The 10-dimensional vector named by :data:`FEATURE_NAMES`."""
    lx, ly = iris_ratios(landmarks, left=True)
    rx, ry = iris_ratios(landmarks, left=False)
    yaw, pitch, roll = head_pose_proxy(landmarks)
    cx, cy, width = face_box(landmarks)
    return [lx, ly, rx, ry, yaw, pitch, roll, cx, cy, width]


def head_pose_in_range(
    features: Sequence[float],
    reference: Sequence[float],
    *,
    tolerance: float = 0.25,
) -> bool:
    """Whether head pose is close enough to the calibration range to trust.

    Outside it the polynomial fit is extrapolating, which is exactly where
    webcam gaze goes quietly wrong — so the sample's confidence is halved
    rather than the prediction being thrown away.
    """
    for index in (4, 5, 6):
        if abs(features[index] - reference[index]) > tolerance:
            return False
    return True
