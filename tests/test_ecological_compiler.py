from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest
from scipy.special import expit

from experiments.ecological_compiler.analysis import (
    fit_ordered_logit,
    ordered_probabilities,
    read_cldf_values,
    strictly_increasing_cutpoints,
)


def test_cutpoint_parameterization_is_strictly_increasing() -> None:
    cutpoints = strictly_increasing_cutpoints(np.array([-0.5, -2.0, 0.0, 1.0]))

    assert np.all(np.diff(cutpoints) > 0)


def test_ordered_probabilities_are_finite_and_sum_to_one() -> None:
    eta = np.array([-2.0, 0.0, 2.0])
    cutpoints = np.array([-1.0, 0.0, 1.0, 2.0])

    probabilities = ordered_probabilities(eta, cutpoints)

    assert probabilities.shape == (3, 5)
    assert np.all(probabilities > 0)
    assert np.allclose(probabilities.sum(axis=1), 1.0)


def test_ordered_logit_recovers_positive_synthetic_effect() -> None:
    rng = np.random.default_rng(20260826)
    x = rng.normal(size=(1_200, 1))
    eta = 0.9 * x[:, 0]
    cutpoints = np.array([-1.2, -0.3, 0.5, 1.4])
    probabilities = ordered_probabilities(eta, cutpoints)
    draws = rng.random(len(x))
    y = (draws[:, None] > np.cumsum(probabilities, axis=1)).sum(axis=1)

    fit = fit_ordered_logit(x, y)

    assert fit.success
    assert fit.coefficients[0] == pytest.approx(0.9, abs=0.2)
    assert np.all(np.diff(fit.cutpoints) > 0)


def test_read_cldf_values_rejects_conflicting_duplicates(tmp_path: Path) -> None:
    data_path = tmp_path / "data.csv"
    codes_path = tmp_path / "codes.csv"
    with codes_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["ID", "Var_ID", "ord"])
        writer.writeheader()
        writer.writerows(
            [
                {"ID": "EA003-0", "Var_ID": "EA003", "ord": "0"},
                {"ID": "EA003-1", "Var_ID": "EA003", "ord": "1"},
            ]
        )
    with data_path.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["Soc_ID", "Var_ID", "Value", "Code_ID"],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "Soc_ID": "S1",
                    "Var_ID": "EA003",
                    "Value": "0-5%",
                    "Code_ID": "EA003-0",
                },
                {
                    "Soc_ID": "S1",
                    "Var_ID": "EA003",
                    "Value": "6-15%",
                    "Code_ID": "EA003-1",
                },
            ]
        )

    with pytest.raises(ValueError, match="conflicting duplicate"):
        read_cldf_values(data_path, codes_path, {"EA003"})


def test_synthetic_probabilities_match_logistic_cumulative_form() -> None:
    eta = np.array([0.25])
    cutpoints = np.array([-1.0, 0.0, 1.0, 2.0])

    probabilities = ordered_probabilities(eta, cutpoints)[0]

    assert probabilities[0] == pytest.approx(expit(-1.0 - 0.25))
    assert probabilities[-1] == pytest.approx(1.0 - expit(2.0 - 0.25))
