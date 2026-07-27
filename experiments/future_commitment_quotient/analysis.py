#!/usr/bin/env python3
"""Exact factorial summaries and noncompensatory gate evaluation."""

from __future__ import annotations

from collections import Counter
from typing import Any, Literal, Mapping, Sequence, TypedDict

import numpy as np

from .core import CONDITIONS, FAMILIES


GATE_ORDER = (
    "F0_CONSTRUCTION_PROVENANCE",
    "F1_FORMAL_IMPLEMENTATION",
    "G1_REPRESENTATION_NON_NECESSITY",
    "G2_REPRESENTATION_NON_SUFFICIENCY",
    "G3_FACTORIAL_PREDICTOR_SEPARATION",
    "G4_FAMILY_TRANSFER",
    "G5_CLAIM_CALIBRATION",
)


class ConstantPrediction(TypedDict):
    """A score-independent prediction rule."""

    kind: Literal["constant_prediction"]
    prediction: bool


class FiniteThreshold(TypedDict):
    """A finite higher-means-preserved threshold rule."""

    kind: Literal["finite_threshold"]
    threshold: float


ThresholdRule = ConstantPrediction | FiniteThreshold


def balanced_accuracy(labels: np.ndarray, predictions: np.ndarray) -> float:
    """Return the mean of positive and negative recall."""

    actual = np.asarray(labels, dtype=bool)
    predicted = np.asarray(predictions, dtype=bool)
    if actual.shape != predicted.shape or actual.ndim != 1:
        raise ValueError("labels and predictions must be matching vectors")
    if not np.any(actual) or not np.any(~actual):
        raise ValueError("balanced accuracy requires both classes")
    positive_recall = float(np.mean(predicted[actual]))
    negative_recall = float(np.mean(~predicted[~actual]))
    return (positive_recall + negative_recall) / 2.0


def best_threshold(
    scores: np.ndarray,
    labels: np.ndarray,
) -> tuple[ThresholdRule, float]:
    """Fit a higher-means-preserved threshold with deterministic tie breaking."""

    values = np.asarray(scores, dtype=np.float64)
    actual = np.asarray(labels, dtype=bool)
    if values.shape != actual.shape or values.ndim != 1:
        raise ValueError("scores and labels must be matching vectors")
    if not np.all(np.isfinite(values)):
        raise ValueError("scores must be finite")
    unique = np.unique(values)
    candidates: list[ThresholdRule] = [
        {
            "kind": "constant_prediction",
            "prediction": True,
        }
    ]
    candidates.extend(
        {
            "kind": "finite_threshold",
            "threshold": float(right),
        }
        for left, right in zip(unique[:-1], unique[1:], strict=True)
    )
    candidates.append(
        {
            "kind": "constant_prediction",
            "prediction": False,
        }
    )
    best = (candidates[0], -1.0)
    for rule in candidates:
        accuracy = balanced_accuracy(actual, _apply_threshold(values, rule))
        if accuracy > best[1] + 1e-12:
            best = (rule, accuracy)
    return best


def _apply_threshold(
    scores: np.ndarray,
    rule: ThresholdRule,
) -> np.ndarray:
    if rule["kind"] == "constant_prediction":
        return np.full(scores.shape, rule["prediction"], dtype=bool)
    return scores >= rule["threshold"]


def leave_one_family_out(
    rows: Sequence[Mapping[str, Any]],
    *,
    metric: str,
) -> dict[str, Any]:
    predictions: list[bool] = []
    labels: list[bool] = []
    folds: dict[str, dict[str, Any]] = {}
    for held_out in FAMILIES:
        train = [row for row in rows if row["family"] != held_out]
        test = [row for row in rows if row["family"] == held_out]
        train_scores = np.asarray([row[metric] for row in train], dtype=np.float64)
        train_labels = np.asarray(
            [row["constraint_preserved"] for row in train],
            dtype=bool,
        )
        rule, train_accuracy = best_threshold(train_scores, train_labels)
        test_scores = np.asarray([row[metric] for row in test], dtype=np.float64)
        test_labels = np.asarray(
            [row["constraint_preserved"] for row in test],
            dtype=bool,
        )
        test_predictions = _apply_threshold(test_scores, rule)
        folds[held_out] = {
            "prediction_rule": rule,
            "train_balanced_accuracy": train_accuracy,
            "test_balanced_accuracy": balanced_accuracy(
                test_labels,
                test_predictions,
            ),
        }
        predictions.extend(bool(value) for value in test_predictions)
        labels.extend(bool(value) for value in test_labels)
    return {
        "balanced_accuracy": balanced_accuracy(
            np.asarray(labels, dtype=bool),
            np.asarray(predictions, dtype=bool),
        ),
        "folds": folds,
    }


def _condition_rows(
    rows: Sequence[Mapping[str, Any]],
    condition: str,
    *,
    family: str | None = None,
) -> list[Mapping[str, Any]]:
    return [
        row
        for row in rows
        if row["condition"] == condition and (family is None or row["family"] == family)
    ]


def _all_formal_checks(rows: Sequence[Mapping[str, Any]]) -> bool:
    return bool(rows) and all(
        all(bool(value) for value in row["formal_checks"].values()) for row in rows
    )


def _non_necessity_pass(rows: Sequence[Mapping[str, Any]]) -> bool:
    target = _condition_rows(rows, "RD_CP")
    return bool(target) and all(
        row["behavioral_disagreement"] == 0.0
        and row["quotient_agreement"] == 1.0
        and all(row["scramble_integrity"].values())
        and row["formal_checks"]["conjugacy_when_constraint_preserved"]
        for row in target
    )


def _non_sufficiency_pass(rows: Sequence[Mapping[str, Any]]) -> bool:
    target = _condition_rows(rows, "RP_CA")
    return bool(target) and all(
        row["coordinate_equality"] == 1.0
        and row["current_output_agreement"] == 1.0
        and row["depth_one_agreement"] == 1.0
        and row["quotient_agreement"] < 1.0
        and row["behavioral_disagreement"] > 0.0
        and row["shortest_witness_length"] is not None
        and row["shortest_witness_length"] >= 2
        for row in target
    )


def summarize_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    expected_rows: int | None = None,
    expected_seeds: Sequence[int] | None = None,
    claim_calibration_pass: bool = True,
) -> dict[str, Any]:
    """Summarize registered exact rows without pooling failed family gates."""

    if not rows:
        raise ValueError("rows must be nonempty")
    normalized_expected_seeds = (
        tuple(sorted({int(row["seed"]) for row in rows}))
        if expected_seeds is None
        else tuple(int(seed) for seed in expected_seeds)
    )
    if not normalized_expected_seeds:
        raise ValueError("expected_seeds must be nonempty")
    if len(set(normalized_expected_seeds)) != len(normalized_expected_seeds):
        raise ValueError("expected_seeds must not contain duplicates")
    expected_cells = Counter(
        {
            (family, seed, condition): 1
            for family in FAMILIES
            for seed in normalized_expected_seeds
            for condition in CONDITIONS
        }
    )
    actual_cells = Counter(
        (
            str(row["family"]),
            int(row["seed"]),
            str(row["condition"]),
        )
        for row in rows
    )
    expected = len(expected_cells) if expected_rows is None else expected_rows
    condition_counts = Counter(str(row["condition"]) for row in rows)
    family_counts = Counter(str(row["family"]) for row in rows)
    seed_sets = {
        family: sorted({int(row["seed"]) for row in rows if row["family"] == family})
        for family in FAMILIES
    }
    predictors = {
        "coordinate_geometry": leave_one_family_out(
            rows,
            metric="coordinate_geometry_correlation",
        ),
        "current_output_agreement": leave_one_family_out(
            rows,
            metric="current_output_agreement",
        ),
        "depth_one_agreement": leave_one_family_out(
            rows,
            metric="depth_one_agreement",
        ),
        "quotient_agreement": leave_one_family_out(
            rows,
            metric="quotient_agreement",
        ),
    }
    f0_pass = (
        len(rows) == expected
        and actual_cells == expected_cells
        and all(
            all(row["scramble_integrity"].values())
            for row in rows
            if str(row["condition"]).startswith("RD")
        )
    )
    f1_pass = _all_formal_checks(rows)
    g1_pass = _non_necessity_pass(rows)
    g2_pass = _non_sufficiency_pass(rows)
    g3_pass = predictors["quotient_agreement"]["balanced_accuracy"] == 1.0 and all(
        predictors[name]["balanced_accuracy"] <= 0.5
        for name in (
            "coordinate_geometry",
            "current_output_agreement",
            "depth_one_agreement",
        )
    )
    per_family: dict[str, dict[str, bool]] = {}
    for family in FAMILIES:
        family_rows = [row for row in rows if row["family"] == family]
        per_family[family] = {
            "representation_non_necessity": _non_necessity_pass(family_rows),
            "representation_non_sufficiency": _non_sufficiency_pass(family_rows),
            "predictor_separation": (
                predictors["quotient_agreement"]["folds"][family][
                    "test_balanced_accuracy"
                ]
                == 1.0
                and all(
                    predictors[name]["folds"][family]["test_balanced_accuracy"] <= 0.5
                    for name in (
                        "coordinate_geometry",
                        "current_output_agreement",
                        "depth_one_agreement",
                    )
                )
            ),
        }
    g4_pass = all(all(results.values()) for results in per_family.values())
    gates = {
        "F0_CONSTRUCTION_PROVENANCE": {
            "pass": f0_pass,
            "observed": {
                "rows": len(rows),
                "expected_rows": expected,
                "expected_seeds": list(normalized_expected_seeds),
                "expected_seeds_supplied": expected_seeds is not None,
                "factorial_cells_exact": actual_cells == expected_cells,
                "condition_counts": dict(condition_counts),
                "family_counts": dict(family_counts),
                "seed_sets": seed_sets,
            },
        },
        "F1_FORMAL_IMPLEMENTATION": {
            "pass": f1_pass,
            "observed": "all per-row exhaustive checks pass",
        },
        "G1_REPRESENTATION_NON_NECESSITY": {
            "pass": g1_pass,
            "observed": "all RD-CP rows preserve quotient and behavior",
        },
        "G2_REPRESENTATION_NON_SUFFICIENCY": {
            "pass": g2_pass,
            "observed": "all RP-CA rows preserve local observations and diverge later",
        },
        "G3_FACTORIAL_PREDICTOR_SEPARATION": {
            "pass": g3_pass,
            "observed": predictors,
        },
        "G4_FAMILY_TRANSFER": {
            "pass": g4_pass,
            "observed": per_family,
        },
        "G5_CLAIM_CALIBRATION": {
            "pass": claim_calibration_pass,
            "observed": (
                "paper calibration audit passed"
                if claim_calibration_pass
                else "paper calibration audit not yet passed"
            ),
        },
    }
    return {
        "artifact_contract": "future-commitment-quotient-summary/v1",
        "n_rows": len(rows),
        "predictors": predictors,
        "condition_metrics": _condition_metrics(rows),
        "per_family": per_family,
        "gates": gates,
        "verdict": evaluate_gates(gates),
    }


def _condition_metrics(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, float | int | None]]:
    result: dict[str, dict[str, float | int | None]] = {}
    metrics = (
        "coordinate_equality",
        "coordinate_geometry_correlation",
        "current_output_agreement",
        "depth_one_agreement",
        "quotient_agreement",
        "behavioral_disagreement",
        "shortest_witness_length",
    )
    for condition in CONDITIONS:
        condition_rows = _condition_rows(rows, condition)
        summary: dict[str, float | int | None] = {"n": len(condition_rows)}
        for metric in metrics:
            values = [
                float(row[metric]) for row in condition_rows if row[metric] is not None
            ]
            summary[f"{metric}_mean"] = float(np.mean(values)) if values else None
            summary[f"{metric}_min"] = min(values) if values else None
            summary[f"{metric}_max"] = max(values) if values else None
        result[condition] = summary
    return result


def evaluate_gates(gates: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    missing = [gate for gate in GATE_ORDER if gate not in gates]
    if missing:
        raise ValueError(f"Missing gates: {missing}")
    failed = [gate for gate in GATE_ORDER if not bool(gates[gate]["pass"])]
    return {
        "decision": (
            "ACCEPT_SCOPED_FINITE_QUOTIENT_CLAIM"
            if not failed
            else "WITHHOLD_SCOPED_FINITE_QUOTIENT_CLAIM"
        ),
        "all_gates_pass": not failed,
        "failed_gates": failed,
    }
