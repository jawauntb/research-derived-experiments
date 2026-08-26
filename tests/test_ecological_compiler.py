from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest
from scipy.special import expit

from scripts import regen
from experiments.ecological_compiler.analysis import (
    DPLACE_COMMIT,
    EA_COMMIT,
    EXPECTED_INPUT_SHA256,
    GATE_IDS,
    _initial_ordered_parameters,
    _binary_nll,
    _binary_nll_and_gradient,
    _glottolog_labels,
    _is_europe_region,
    _ordered_nll,
    _ordered_nll_and_gradient,
    fit_ordered_logit,
    ordered_probabilities,
    provenance_gate_passes,
    read_cldf_values,
    registered_verdict,
    strictly_increasing_cutpoints,
)


@pytest.mark.parametrize(
    ("region", "expected"),
    [
        ("Eastern Europe", True),
        ("Northern Europe", True),
        ("Southwestern Europe", True),
        ("Western Asia", False),
        ("Europe", True),
    ],
)
def test_europe_region_classification(region: str, expected: bool) -> None:
    assert _is_europe_region(region) is expected


def test_missing_language_families_form_singleton_clusters() -> None:
    glottolog = {"known": ("Atlantic-Congo", "Africa")}

    first = _glottolog_labels("S1", "missing", glottolog)
    second = _glottolog_labels("S2", "missing", glottolog)
    known = _glottolog_labels("S3", "known", glottolog)

    assert first == ("Unknown:S1", "Unknown")
    assert second == ("Unknown:S2", "Unknown")
    assert first[0] != second[0]
    assert known == ("Atlantic-Congo", "Africa")


def test_registered_verdict_requires_every_gate_to_pass() -> None:
    passing = {gate: "PASS" for gate in GATE_IDS}

    assert registered_verdict(passing) == "accepted"
    for gate in GATE_IDS:
        failing = {**passing, gate: "FAIL"}
        assert registered_verdict(failing) == "rejected"

    with pytest.raises(ValueError, match="every registered gate"):
        registered_verdict(dict(list(passing.items())[:-1]))


def test_provenance_gate_checks_exact_bytes_and_clean_sources() -> None:
    provenance = {
        "ea_commit": EA_COMMIT,
        "dplace_support_commit": DPLACE_COMMIT,
        "ea_worktree_clean": True,
        "dplace_support_worktree_clean": True,
        "input_sha256": EXPECTED_INPUT_SHA256.copy(),
    }

    assert provenance_gate_passes(provenance)

    changed = {**provenance, "input_sha256": {**EXPECTED_INPUT_SHA256}}
    first_path = next(iter(EXPECTED_INPUT_SHA256))
    changed["input_sha256"][first_path] = "0" * 64
    assert not provenance_gate_passes(changed)
    assert not provenance_gate_passes({**provenance, "ea_worktree_clean": False})


def test_regen_recipe_runs_analysis_and_pdf_builder() -> None:
    commands = regen.LOCAL["ecological_compiler"]

    assert len(commands) == 2
    assert "experiments.ecological_compiler.analysis" in commands[0]
    assert "scripts/build_ecological_compiler_pdf.py" in commands[1]


def test_ordered_logit_analytic_gradient_matches_finite_difference() -> None:
    rng = np.random.default_rng(42)
    x = rng.normal(size=(40, 5))
    y = np.tile(np.arange(5), 8)
    parameters = _initial_ordered_parameters(x, y) + rng.normal(scale=0.1, size=9)

    _, analytic = _ordered_nll_and_gradient(parameters, x, y)
    epsilon = 1e-6
    numerical = np.empty_like(parameters)
    for index in range(len(parameters)):
        offset = np.zeros_like(parameters)
        offset[index] = epsilon
        numerical[index] = (
            _ordered_nll(parameters + offset, x, y)
            - _ordered_nll(parameters - offset, x, y)
        ) / (2 * epsilon)

    assert analytic == pytest.approx(numerical, abs=1e-5)


def test_binary_logit_analytic_gradient_matches_finite_difference() -> None:
    rng = np.random.default_rng(7)
    x = rng.normal(size=(40, 6))
    y = np.tile(np.array([0, 1]), 20)
    parameters = rng.normal(scale=0.2, size=7)

    _, analytic = _binary_nll_and_gradient(parameters, x, y)
    epsilon = 1e-6
    numerical = np.empty_like(parameters)
    for index in range(len(parameters)):
        offset = np.zeros_like(parameters)
        offset[index] = epsilon
        numerical[index] = (
            _binary_nll(parameters + offset, x, y)
            - _binary_nll(parameters - offset, x, y)
        ) / (2 * epsilon)

    assert analytic == pytest.approx(numerical, abs=1e-5)


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


def test_read_cldf_values_ignores_missing_code_sentinel(tmp_path: Path) -> None:
    data_path = tmp_path / "data.csv"
    codes_path = tmp_path / "codes.csv"
    with codes_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["ID", "Var_ID", "ord"])
        writer.writeheader()
        writer.writerow({"ID": "EA033-NA", "Var_ID": "EA033", "ord": "99"})
    with data_path.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["Soc_ID", "Var_ID", "Value", "Code_ID"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "Soc_ID": "S1",
                "Var_ID": "EA033",
                "Value": "Missing data",
                "Code_ID": "EA033-NA",
            }
        )

    values, _ = read_cldf_values(data_path, codes_path, {"EA033"})

    assert values["EA033"] == {}


def test_synthetic_probabilities_match_logistic_cumulative_form() -> None:
    eta = np.array([0.25])
    cutpoints = np.array([-1.0, 0.0, 1.0, 2.0])

    probabilities = ordered_probabilities(eta, cutpoints)[0]

    assert probabilities[0] == pytest.approx(expit(-1.0 - 0.25))
    assert probabilities[-1] == pytest.approx(1.0 - expit(2.0 - 0.25))
