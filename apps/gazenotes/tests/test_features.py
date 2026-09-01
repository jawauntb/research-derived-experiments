"""Landmark → feature maths, and the frame → sample path of the gaze engine."""

from __future__ import annotations

import pytest

from gazenotes.gaze import features as feat
from gazenotes.gaze.capture import GazeEngine, landmarks_from_result
from gazenotes.gaze.regress import RidgeModel
from gazenotes.geometry import Rect

SCREEN = Rect(0, 0, 1728, 1117)


def synthetic_face(
    *,
    iris_x=0.5,
    iris_y=0.5,
    yaw=0.0,
    lid_gap=0.03,
    face_cx=0.5,
    face_cy=0.5,
    face_w=0.3,
):
    """A face-mesh landmark array with only the indices we read filled in.

    Everything else is a placeholder; the feature code must not depend on it.
    """
    points = [(0.0, 0.0, 0.0)] * 478

    def put(index, x, y):
        points[index] = (x, y, 0.0)

    half = face_w / 2
    put(feat.LEFT_CHEEK, face_cx - half, face_cy)
    put(feat.RIGHT_CHEEK, face_cx + half, face_cy)
    put(feat.FOREHEAD, face_cx, face_cy - face_w)
    put(feat.CHIN, face_cx, face_cy + face_w)
    put(feat.NOSE_TIP, face_cx + yaw * face_w, face_cy)

    for corners, lids, iris in (
        (feat.LEFT_EYE_CORNERS, feat.LEFT_EYE_LIDS, feat.LEFT_IRIS),
        (feat.RIGHT_EYE_CORNERS, feat.RIGHT_EYE_LIDS, feat.RIGHT_IRIS),
    ):
        eye_w = face_w / 4
        eye_cx = face_cx + (-face_w / 4 if corners is feat.LEFT_EYE_CORNERS else face_w / 4)
        eye_cy = face_cy - face_w / 3
        put(corners[0], eye_cx - eye_w / 2, eye_cy)
        put(corners[1], eye_cx + eye_w / 2, eye_cy)
        put(lids[0], eye_cx, eye_cy - lid_gap / 2)
        put(lids[1], eye_cx, eye_cy + lid_gap / 2)
        cx = eye_cx - eye_w / 2 + iris_x * eye_w
        cy = eye_cy - lid_gap / 2 + iris_y * lid_gap
        for index in iris:
            put(index, cx, cy)
    return points


# -- iris ---------------------------------------------------------------
def test_a_centred_iris_reads_as_the_middle_of_the_eye():
    rx, ry = feat.iris_ratios(synthetic_face(iris_x=0.5, iris_y=0.5))
    assert rx == pytest.approx(0.5)
    assert ry == pytest.approx(0.5)


@pytest.mark.parametrize("iris_x", [0.1, 0.3, 0.7, 0.9])
def test_horizontal_iris_position_is_monotone(iris_x):
    rx, _ = feat.iris_ratios(synthetic_face(iris_x=iris_x))
    assert rx == pytest.approx(iris_x, abs=1e-6)


def test_iris_ratios_are_invariant_to_how_close_the_user_sits():
    near = feat.iris_ratios(synthetic_face(iris_x=0.3, face_w=0.5))
    far = feat.iris_ratios(synthetic_face(iris_x=0.3, face_w=0.15))
    assert near == pytest.approx(far)


def test_a_degenerate_eye_does_not_divide_by_zero():
    points = synthetic_face()
    points[feat.LEFT_EYE_CORNERS[0]] = points[feat.LEFT_EYE_CORNERS[1]]
    assert feat.iris_ratios(points, left=True) == (0.5, pytest.approx(0.5))


# -- blinks -------------------------------------------------------------
def test_eyes_open_tracks_lid_separation():
    assert feat.eyes_open(synthetic_face(lid_gap=0.03))
    assert not feat.eyes_open(synthetic_face(lid_gap=0.001))


def test_eye_aspect_ratio_falls_as_the_lids_close():
    wide = feat.eye_aspect_ratio(synthetic_face(lid_gap=0.04))
    narrow = feat.eye_aspect_ratio(synthetic_face(lid_gap=0.005))
    assert wide > narrow


# -- head pose ----------------------------------------------------------
def test_yaw_is_signed_and_zero_when_facing_forward():
    assert feat.head_pose_proxy(synthetic_face(yaw=0.0))[0] == pytest.approx(0.0)
    assert feat.head_pose_proxy(synthetic_face(yaw=0.2))[0] > 0
    assert feat.head_pose_proxy(synthetic_face(yaw=-0.2))[0] < 0


def test_pose_of_a_collapsed_face_is_zero_rather_than_a_crash():
    points = [(0.0, 0.0, 0.0)] * 478
    assert feat.head_pose_proxy(points) == (0.0, 0.0, 0.0)


def test_head_pose_range_check_flags_a_turned_head():
    reference = feat.feature_vector(synthetic_face(yaw=0.0))
    assert feat.head_pose_in_range(feat.feature_vector(synthetic_face(yaw=0.02)), reference)
    assert not feat.head_pose_in_range(feat.feature_vector(synthetic_face(yaw=0.9)), reference)


# -- vector -------------------------------------------------------------
def test_the_feature_vector_matches_its_names():
    vector = feat.feature_vector(synthetic_face())
    assert len(vector) == len(feat.FEATURE_NAMES) == 10
    assert all(isinstance(value, float) for value in vector)


# -- engine -------------------------------------------------------------
class StubLandmark:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z


class StubResult:
    def __init__(self, points=None):
        if points is None:
            self.multi_face_landmarks = None
        else:
            face = type("F", (), {"landmark": [StubLandmark(*p) for p in points]})()
            self.multi_face_landmarks = [face]


def test_landmarks_are_extracted_from_a_mediapipe_result():
    assert landmarks_from_result(StubResult()) is None
    points = landmarks_from_result(StubResult([(0.1, 0.2, 0.3)]))
    assert points == [(0.1, 0.2, 0.3)]


def linear_model():
    """A model whose prediction is a simple function of the first two features."""
    width = len(feat.FEATURE_NAMES)
    from gazenotes.gaze.regress import poly2

    size = len(poly2([0.0] * width))
    coef_x = [0.0] * size
    coef_y = [0.0] * size
    coef_x[1] = 1728.0  # iris_x_l → screen x
    coef_y[2] = 1117.0  # iris_y_l → screen y
    return RidgeModel(coef_x=coef_x, coef_y=coef_y, feature_names=list(feat.FEATURE_NAMES))


def make_engine():
    engine = GazeEngine(screen=SCREEN)
    engine.model = linear_model()
    return engine


def test_an_open_eyed_frame_becomes_a_confident_sample():
    engine = make_engine()
    sample = engine.sample_from_landmarks(synthetic_face(iris_x=0.5, iris_y=0.5), 1.0)
    assert sample is not None
    assert sample.confidence > 0.5
    assert 0 <= sample.x <= SCREEN.w


def test_a_lost_face_is_a_zero_confidence_sample_not_a_dropped_frame():
    sample = make_engine().sample_from_landmarks(None, 1.0)
    assert sample is not None and sample.confidence == 0.0


def test_a_blink_is_a_zero_confidence_sample():
    engine = make_engine()
    sample = engine.sample_from_landmarks(synthetic_face(lid_gap=0.001), 1.0)
    assert sample.confidence == 0.0


def test_a_prediction_off_the_screen_is_penalised():
    engine = make_engine()
    on = engine.sample_from_landmarks(synthetic_face(iris_x=0.5, iris_y=0.5), 1.0)
    off = engine.sample_from_landmarks(synthetic_face(iris_x=5.0, iris_y=0.5), 2.0)
    assert off.confidence < on.confidence


def test_an_out_of_range_head_pose_halves_confidence():
    engine = make_engine()
    engine.set_reference_features(feat.feature_vector(synthetic_face(yaw=0.0)))
    straight = engine.sample_from_landmarks(synthetic_face(yaw=0.0), 1.0)
    turned = engine.sample_from_landmarks(synthetic_face(yaw=0.9), 2.0)
    assert turned.confidence == pytest.approx(straight.confidence / 2)


def test_without_a_calibration_the_engine_produces_nothing():
    engine = GazeEngine(screen=SCREEN)
    assert engine.sample_from_landmarks(synthetic_face(), 1.0) is None


def test_a_malformed_landmark_array_is_survivable():
    engine = make_engine()
    assert engine.sample_from_landmarks([(0.0, 0.0, 0.0)], 1.0).confidence == 0.0


def test_current_features_tracks_the_latest_usable_frame():
    engine = make_engine()
    engine._store_features(synthetic_face(iris_x=0.4))
    assert engine.current_features() is not None
    engine._store_features(synthetic_face(lid_gap=0.001))  # blink
    assert engine.current_features() is None


def test_the_engine_reports_why_it_is_unavailable_without_calibration(tmp_path):
    engine = GazeEngine(screen=SCREEN, calibration_path=tmp_path / "calibration.json")
    status = engine.start()
    assert not status.available
    assert "calibrat" in status.reason or "missing dependency" in status.reason


def test_dominant_fixation_reads_through_the_ring_buffer():
    from gazenotes.events import GazeSample

    engine = make_engine()
    for i in range(40):
        engine.buffer.add(GazeSample(i / 30.0, 900, 700, 0.9))
    fixation = engine.dominant_fixation(0.0, 2.0)
    assert fixation is not None
    assert fixation.x == pytest.approx(900)


def test_loading_a_calibration_restores_the_reference_pose_and_clears_state(tmp_path):
    from gazenotes.events import GazeSample
    from gazenotes.gaze.regress import save_calibration

    path = tmp_path / "calibration.json"
    reference = feat.feature_vector(synthetic_face(yaw=0.1))
    save_calibration(path, "main", linear_model(), meta={"reference_features": reference})

    engine = GazeEngine(screen=SCREEN, calibration_path=path, display_key="main")
    engine.buffer.add(GazeSample(0.0, 1, 1, 1.0))
    assert engine.load_calibration()
    assert engine.model is not None
    # Stale samples from the previous fit must not survive into the new one.
    assert len(engine.buffer) == 0
    # And the stored head pose is what out-of-range detection compares against.
    straight = engine.sample_from_landmarks(synthetic_face(yaw=0.1), 1.0)
    turned = engine.sample_from_landmarks(synthetic_face(yaw=0.9), 2.0)
    assert turned.confidence < straight.confidence


def test_an_uncalibrated_display_clears_any_previously_loaded_model(tmp_path):
    engine = GazeEngine(screen=SCREEN, calibration_path=tmp_path / "none.json")
    engine.model = linear_model()
    assert engine.load_calibration() is False
    assert engine.model is None
