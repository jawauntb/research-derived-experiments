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
    exact_accuracy,
    exact_rows,
    ood_pairs,
    run_sweep,
    shortcut_table,
    true_table,
    true_translation_compatibility,
    wrong_permutation_compatibility,
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


def test_modular_exact_rows_emit_common_schema() -> None:
    rows = exact_rows(modulus=7, train_window=3)
    assert {row.model_id for row in rows} == {"true_rule", "local_shortcut"}
    summary = summarize_rows(rows)
    assert summary["by_domain"]["modular_exact"]["n_rows"] == 2


def test_tiny_modular_neural_sweep_emits_rows() -> None:
    if importlib.util.find_spec("torch") is None:
        pytest.skip()
    rows = run_sweep(n_models=1, epochs=2, base_seed=123, device="cpu")
    assert len(rows) == 3
    assert {"modular_exact", "modular_neural"} == {row.domain for row in rows}
    for row in rows:
        assert 0.0 <= row.ood_accuracy <= 1.0
        assert 0.0 <= row.compatibility_true <= 1.0
        assert 0.0 <= row.compatibility_wrong <= 1.0
