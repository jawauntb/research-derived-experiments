from __future__ import annotations

import importlib.util
import random

import pytest

from experiments.structure_compatible_generalization.core import (
    DiagnosticRow,
    id_equivalent_rows,
    rows_from_records,
    rows_to_records,
    selection_analysis,
    summarize_rows,
)
from experiments.structure_compatible_generalization.modular_domain import (
    base_train_pairs,
    discovered_translation_compatibility,
    exact_accuracy,
    exact_rows,
    labels_for_pairs,
    ood_pairs,
    run_intervention_sweep,
    run_sweep,
    shortcut_table,
    true_table,
    true_translation_compatibility,
    wrong_permutation_compatibility,
)
from experiments.structure_compatible_generalization.transformation_discovery import (
    close_shift_family,
    infer_supported_shifts,
)


def test_summary_ranks_true_compatibility_when_it_tracks_ood() -> None:
    rows = [
        DiagnosticRow(
            domain="toy",
            model_id=f"m{i}",
            train_accuracy=1.0,
            id_validation_accuracy=1.0,
            ood_accuracy=float(i) / 4.0,
            compatibility_true=float(i) / 4.0,
            compatibility_wrong=1.0 - float(i) / 4.0,
            final_train_loss=0.01 * (5 - i),
        )
        for i in range(5)
    ]
    summary = summarize_rows(rows)
    ranking = summary["by_domain"]["toy"]["predictor_ranking"]
    assert ranking[0]["predictor"] == "compatibility_true"
    assert ranking[0]["pearson"] > 0.99


def test_selection_uses_id_equivalent_models_only() -> None:
    rows = [
        DiagnosticRow(
            domain="toy",
            model_id="shortcut",
            train_accuracy=1.0,
            id_validation_accuracy=1.0,
            ood_accuracy=0.0,
            compatibility_true=0.1,
            compatibility_wrong=1.0,
        ),
        DiagnosticRow(
            domain="toy",
            model_id="rule",
            train_accuracy=1.0,
            id_validation_accuracy=0.99,
            ood_accuracy=1.0,
            compatibility_true=1.0,
            compatibility_wrong=0.1,
        ),
        DiagnosticRow(
            domain="toy",
            model_id="bad-train",
            train_accuracy=0.5,
            id_validation_accuracy=1.0,
            ood_accuracy=1.0,
            compatibility_true=1.0,
            compatibility_wrong=1.0,
        ),
    ]
    eligible = id_equivalent_rows(rows)
    assert {row.model_id for row in eligible} == {"shortcut", "rule"}
    selected = selection_analysis(rows)["by_domain"]["toy"]
    assert selected["compatibility_true"]["model_id"] == "rule"
    assert selected["compatibility_wrong"]["model_id"] == "shortcut"


def test_rows_round_trip_records() -> None:
    row = DiagnosticRow(
        domain="toy",
        model_id="m",
        train_accuracy=1.0,
        id_validation_accuracy=0.99,
        ood_accuracy=0.75,
        compatibility_true=0.8,
        compatibility_wrong=0.2,
        compatibility_discovered=0.7,
        metadata={"k": "v"},
    )
    assert rows_from_records(rows_to_records([row])) == [row]


def test_modular_exact_rule_beats_shortcut_on_ood_and_compatibility() -> None:
    modulus = 11
    train_window = 4
    train = base_train_pairs(modulus, train_window)
    ood = ood_pairs(modulus, train_window)
    rule = true_table(modulus)
    shortcut = shortcut_table(modulus, train_window)

    assert exact_accuracy(rule, train, modulus) == 1.0
    assert exact_accuracy(shortcut, train, modulus) == 1.0
    assert exact_accuracy(rule, ood, modulus) == 1.0
    assert exact_accuracy(shortcut, ood, modulus) < 0.2
    assert true_translation_compatibility(rule, modulus) == 1.0
    assert true_translation_compatibility(shortcut, modulus) < 0.2
    assert wrong_permutation_compatibility(rule, modulus, rng=random.Random(7)) < 0.3


def test_supported_shift_inference_rejects_vacuous_non_identity() -> None:
    pairs = [(0, 0), (0, 1), (0, 2)]
    labels = [0, 1, 2]
    family = infer_supported_shifts(pairs, labels, modulus=7, min_support=2)
    assert family.admitted_shifts == (0,)


def test_supported_shift_inference_admits_observed_consistent_shift() -> None:
    modulus = 7
    train_window = 3
    train = base_train_pairs(modulus, train_window)
    labels = labels_for_pairs(train, modulus=modulus, train_window=train_window)
    family = infer_supported_shifts(train, labels, modulus=modulus, min_support=modulus)

    assert 0 in family.admitted_shifts
    assert 1 in family.admitted_shifts
    assert close_shift_family(family.admitted_shifts, modulus) == tuple(range(modulus))


def test_discovered_compatibility_separates_rule_from_shortcut() -> None:
    modulus = 11
    train_window = 4
    train = base_train_pairs(modulus, train_window)
    labels = labels_for_pairs(train, modulus=modulus, train_window=train_window)
    rule_score, rule_record = discovered_translation_compatibility(
        true_table(modulus),
        train,
        labels,
        modulus,
        min_support=modulus,
    )
    shortcut_score, shortcut_record = discovered_translation_compatibility(
        shortcut_table(modulus, train_window),
        train,
        labels,
        modulus,
        min_support=modulus,
    )

    assert rule_score == 1.0
    assert shortcut_score < 0.3
    assert rule_record["closed_count"] == modulus
    assert shortcut_record["closed_count"] == modulus


def test_modular_exact_rows_emit_common_schema() -> None:
    rows = exact_rows(modulus=7, train_window=3)
    assert {row.model_id for row in rows} == {"true_rule", "local_shortcut"}
    summary = summarize_rows(rows)
    assert summary["by_domain"]["modular_exact"]["n_rows"] == 2
    assert all(row.compatibility_discovered is not None for row in rows)


def test_tiny_modular_neural_sweep_emits_rows() -> None:
    if importlib.util.find_spec("torch") is None:
        pytest.skip("torch unavailable; neural training is exercised in Modal runs")
    rows = run_sweep(n_models=1, epochs=2, base_seed=123, device="cpu")
    assert len(rows) == 3
    assert {"modular_exact", "modular_neural"} == {row.domain for row in rows}
    for row in rows:
        assert 0.0 <= row.ood_accuracy <= 1.0
        assert 0.0 <= row.compatibility_true <= 1.0
        assert 0.0 <= row.compatibility_wrong <= 1.0


def test_tiny_intervention_sweep_records_regularizer_metadata() -> None:
    if importlib.util.find_spec("torch") is None:
        pytest.skip("torch unavailable; neural training is exercised in Modal runs")
    rows = run_intervention_sweep(
        n_configs=1,
        epochs=2,
        base_seed=456,
        regularization_values=(0.0, 0.05),
        device="cpu",
        include_exact=False,
    )
    assert len(rows) == 2
    strengths = {
        row.metadata["config"]["compatibility_regularization"] for row in rows
    }
    assert strengths == {0.0, 0.05}
    for row in rows:
        assert row.compatibility_discovered is not None
        assert "training_discovery" in row.metadata
        assert "regularizer_shifts" in row.metadata
