"""Gaze buffering, fixation detection, and the calibration fit."""

from __future__ import annotations

import random

import pytest

from gazenotes.events import GazeSample
from gazenotes.gaze.calibrate import (
    CalibrationPlan,
    collect_samples,
    fit_calibration,
    grid_targets,
    run_calibration,
)
from gazenotes.gaze.model import (
    GazeRingBuffer,
    OneEuroFilter,
    dominant_fixation,
    hold_through_blinks,
    sample_confidence,
)
from gazenotes.gaze.regress import RidgeModel, load_calibration, poly2, save_calibration
from gazenotes.geometry import Rect

SCREEN = Rect(0, 0, 1728, 1117)


def samples_at(x, y, count, t0=0.0, confidence=0.9, jitter=0.0, rng=None):
    rng = rng or random.Random(0)
    return [
        GazeSample(
            t0 + i / 30.0,
            x + (rng.uniform(-jitter, jitter) if jitter else 0.0),
            y + (rng.uniform(-jitter, jitter) if jitter else 0.0),
            confidence,
        )
        for i in range(count)
    ]


# -- ring buffer --------------------------------------------------------
def test_ring_buffer_drops_samples_older_than_its_window():
    buffer = GazeRingBuffer(seconds=1.0)
    for i in range(90):  # 3 seconds at 30 Hz
        buffer.add(GazeSample(i / 30.0, 100, 100, 1.0))
    kept = buffer.snapshot()
    assert kept[0].t >= kept[-1].t - 1.0
    assert len(kept) < 90


def test_ring_buffer_window_is_inclusive():
    buffer = GazeRingBuffer(seconds=10.0)
    for sample in samples_at(10, 10, 30):
        buffer.add(sample)
    window = buffer.window(0.0, 0.5)
    assert window[0].t == 0.0
    assert window[-1].t == pytest.approx(0.5)


# -- fixation -----------------------------------------------------------
def test_dominant_fixation_finds_the_busiest_region():
    scatter = samples_at(200, 200, 5)
    cluster = samples_at(900, 700, 40, t0=1.0, jitter=20, rng=random.Random(1))
    fixation = dominant_fixation(scatter + cluster)
    assert fixation is not None
    assert fixation.x == pytest.approx(900, abs=30)
    assert fixation.y == pytest.approx(700, abs=30)
    assert fixation.sample_count == 40


def test_scattered_gaze_scores_lower_than_a_steady_one():
    rng = random.Random(7)
    steady = dominant_fixation(samples_at(800, 500, 60, jitter=10, rng=rng))
    scattered = dominant_fixation(
        [GazeSample(i / 30.0, rng.uniform(0, 1728), rng.uniform(0, 1117), 0.9) for i in range(60)]
    )
    assert steady is not None and scattered is not None
    assert steady.confidence > 0.7
    assert scattered.confidence < steady.confidence


def test_fixation_is_none_when_every_sample_is_low_confidence():
    assert dominant_fixation(samples_at(500, 500, 30, confidence=0.0)) is None


def test_fixation_is_none_for_an_empty_window():
    assert dominant_fixation([]) is None


def test_low_confidence_samples_do_not_drag_the_centroid():
    good = samples_at(900, 700, 30, jitter=5, rng=random.Random(2))
    junk = [GazeSample(2.0 + i / 30.0, 940, 740, 0.01) for i in range(200)]
    fixation = dominant_fixation(good + junk)
    assert fixation is not None
    assert fixation.y == pytest.approx(700, abs=25)


def test_the_screen_thirds_are_separable_at_the_default_cell_size():
    # The acceptance criterion for Phase 2 is picking the right third of the
    # screen; 120pt cells must not merge two thirds of a 1117pt display.
    top = dominant_fixation(samples_at(864, 180, 40, jitter=30, rng=random.Random(3)))
    bottom = dominant_fixation(samples_at(864, 930, 40, jitter=30, rng=random.Random(4)))
    assert top is not None and bottom is not None
    assert top.y < SCREEN.h / 3
    assert bottom.y > 2 * SCREEN.h / 3


# -- confidence ---------------------------------------------------------
def test_confidence_is_zero_without_a_face_or_with_closed_eyes():
    assert sample_confidence(face_found=False, eyes_open=True, head_pose_ok=True, on_screen=True) == 0.0
    assert sample_confidence(face_found=True, eyes_open=False, head_pose_ok=True, on_screen=True) == 0.0


def test_confidence_is_penalised_off_screen_and_out_of_pose():
    full = sample_confidence(face_found=True, eyes_open=True, head_pose_ok=True, on_screen=True)
    off = sample_confidence(face_found=True, eyes_open=True, head_pose_ok=True, on_screen=False)
    posed = sample_confidence(face_found=True, eyes_open=True, head_pose_ok=False, on_screen=True)
    assert full == 1.0
    assert 0.0 < off < full
    assert 0.0 < posed < full


# -- blinks -------------------------------------------------------------
def test_a_short_blink_holds_the_last_good_point():
    before = samples_at(800, 600, 10)
    blink = [GazeSample(1.0 + i / 30.0, 0, 0, 0.0) for i in range(6)]  # 0.2 s
    after = samples_at(810, 610, 10, t0=2.0)
    held = hold_through_blinks(before + blink + after)
    filled = [s for s in held if 1.0 <= s.t < 1.3]
    assert filled
    assert all(s.x == 800 and s.y == 600 for s in filled)
    assert all(0 < s.confidence < 0.9 for s in filled)


def test_a_long_look_away_is_not_filled_in():
    before = samples_at(800, 600, 10)
    gone = [GazeSample(1.0 + i / 30.0, 0, 0, 0.0) for i in range(60)]  # 2 s
    held = hold_through_blinks(before + gone + samples_at(200, 200, 5, t0=4.0))
    assert all(s.confidence == 0.0 for s in held if 1.0 <= s.t < 3.0)


# -- smoothing ----------------------------------------------------------
def test_one_euro_filter_suppresses_jitter_while_holding_still():
    rng = random.Random(5)
    noisy = [500 + rng.uniform(-20, 20) for _ in range(60)]
    filt = OneEuroFilter()
    outputs = [filt(value, i / 30.0) for i, value in enumerate(noisy)]
    settled = outputs[30:]
    input_spread = max(noisy[30:]) - min(noisy[30:])
    assert max(settled) - min(settled) < input_spread / 2


def test_one_euro_filter_still_tracks_a_saccade_within_a_few_frames():
    filt = OneEuroFilter()
    for i in range(30):
        filt(200.0, i / 30.0)
    values = [filt(1000.0, i / 30.0) for i in range(30, 60)]
    assert values[4] > 900  # within five frames, ~170 ms at 30 fps
    assert values[-1] == pytest.approx(1000, abs=1)


# -- regression ---------------------------------------------------------
def test_poly2_has_the_expected_width():
    assert len(poly2([0.0] * 10)) == 1 + 10 + 55


def test_ridge_recovers_a_known_linear_mapping():
    rng = random.Random(11)
    rows, targets = [], []
    for _ in range(200):
        features = [rng.uniform(-1, 1) for _ in range(4)]
        rows.append(features)
        targets.append((300 * features[0] + 50, 400 * features[1] + 500))
    model = RidgeModel.fit(rows, targets, alpha=1e-6)
    px, py = model.predict([0.5, 0.25, 0.0, 0.0])
    assert px == pytest.approx(200, abs=15)
    assert py == pytest.approx(600, abs=15)
    assert model.residual_px < 15


def test_ridge_round_trips_through_calibration_json(tmp_path):
    rng = random.Random(12)
    rows = [[rng.uniform(-1, 1) for _ in range(4)] for _ in range(80)]
    targets = [(100 * r[0], 200 * r[1]) for r in rows]
    model = RidgeModel.fit(rows, targets)
    path = tmp_path / "calibration.json"
    save_calibration(path, "main-1728x1117", model, meta={"samples": 80})
    save_calibration(path, "external-2560x1440", model)

    loaded = load_calibration(path, "main-1728x1117")
    assert loaded is not None
    assert loaded.predict(rows[0]) == pytest.approx(model.predict(rows[0]))
    # A second display's calibration must not evict the first.
    assert load_calibration(path, "external-2560x1440") is not None
    assert load_calibration(path, "never-calibrated") is None


def test_degenerate_calibration_is_rejected_not_silently_fitted():
    # The user stared at one point the whole time: no information to fit.
    samples = [([0.5] * 4, (100.0, 100.0)) for _ in range(90)]
    result = fit_calibration(samples)
    assert not result.accepted or result.residual_px < 1e-6


# -- calibration flow ---------------------------------------------------
def test_grid_targets_are_inside_the_screen_and_alternate_direction():
    targets = grid_targets(SCREEN, 9)
    assert len(targets) == 9
    assert all(0 < x < SCREEN.w and 0 < y < SCREEN.h for x, y in targets)
    # Boustrophedon: the second row runs right-to-left.
    assert targets[3][0] > targets[5][0]


def test_grid_targets_rejects_a_non_square_count():
    with pytest.raises(ValueError):
        grid_targets(SCREEN, 10)


def test_collect_samples_skips_frames_with_no_face():
    calls = {"n": 0}

    def read():
        calls["n"] += 1
        return None if calls["n"] % 2 else [0.1] * 10

    plan = CalibrationPlan(samples_per_dot=4, points=4, dwell_seconds=0.01, settle_seconds=0.0)
    collected = collect_samples(grid_targets(SCREEN, 4), read, plan, sleep=lambda _s: None)
    assert len(collected) == 8  # half the frames had no face


def test_run_calibration_saves_a_good_fit_and_rejects_a_bad_one(tmp_path):
    path = tmp_path / "calibration.json"
    plan = CalibrationPlan(samples_per_dot=10, points=9, dwell_seconds=0.01, settle_seconds=0.0)
    state = {"target": (0.0, 0.0)}

    def show(target, index, total):
        state["target"] = target

    def read_good():
        # A perfectly informative "eye": features encode the target directly.
        x, y = state["target"]
        return [x / SCREEN.w, y / SCREEN.h] + [0.0] * 8

    result = run_calibration(
        SCREEN, read_good, calibration_path=path, plan=plan, show_dot=show, sleep=lambda _s: None
    )
    assert result.accepted, result.reason
    assert path.exists()
    assert load_calibration(path, "main") is not None

    rng = random.Random(13)

    def read_noise():
        return [rng.uniform(-1, 1) for _ in range(10)]

    bad_path = tmp_path / "bad.json"
    bad = run_calibration(
        SCREEN, read_noise, calibration_path=bad_path, plan=plan, show_dot=show, sleep=lambda _s: None
    )
    assert not bad.accepted
    assert "exceeds" in bad.reason
    assert not bad_path.exists()  # a rejected fit is never saved


def test_too_few_samples_is_a_rejection_not_a_crash():
    result = fit_calibration([([0.1] * 10, (5.0, 5.0))] * 4)
    assert not result.accepted
    assert result.reason == "too few samples"
