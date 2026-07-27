#!/usr/bin/env python3
"""Registered analysis, intervention evaluation, and noncompensatory gates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Sequence

import numpy as np

from .core import (
    Constraint,
    DecisionUnit,
    ExperimentConfig,
    GridTopology,
    LowRankTransport,
    action_histogram,
    all_decision_units,
    crossnobis_rdm,
    evaluate_gates,
    fit_crossnobis_precision,
    fit_low_rank_transport,
    observation,
    oracle_action,
    paired_bootstrap_interval,
    partial_alignment,
    reachability_rdm,
    stable_unit_split,
)
from .model import (
    ContextProbe,
    MetaGRU,
    action_head_logits,
    collect_context,
    collect_random_context,
    matched_random_transport,
    select_probe_units,
)


@dataclass(frozen=True)
class TopologyBundle:
    topology: GridTopology
    units: tuple[DecisionUnit, ...]
    contexts: dict[str, ContextProbe]
    reachability_a: np.ndarray
    reachability_b: np.ndarray
    nuisance: np.ndarray
    nuisance_diagnostics: dict[str, Any]
    precision: np.ndarray
    calibration: np.ndarray
    test: np.ndarray


def _pairwise_squared(values: np.ndarray) -> np.ndarray:
    norms = np.sum(values * values, axis=1)
    distances = norms[:, None] + norms[None, :] - 2.0 * values @ values.T
    return np.maximum(distances, 0.0)


def _pairwise_absolute(values: np.ndarray) -> np.ndarray:
    vector = np.asarray(values, dtype=np.float64)
    return np.abs(vector[:, None] - vector[None, :])


def _action_rdm(
    topology: GridTopology,
    units: Sequence[DecisionUnit],
    constraint: Constraint,
) -> np.ndarray:
    labels = np.asarray(
        [oracle_action(unit, constraint) for unit in units]
    )
    return (labels[:, None] != labels[None, :]).astype(np.float64)


def _physical_rdm(
    topology: GridTopology,
    units: Sequence[DecisionUnit],
) -> np.ndarray:
    result = np.zeros((len(units), len(units)), dtype=np.float64)
    for left, (left_current, left_goal) in enumerate(units):
        for right in range(left + 1, len(units)):
            right_current, right_goal = units[right]
            distance = topology.physical_distance(left_current, right_current)
            distance += topology.physical_distance(left_goal, right_goal)
            result[left, right] = result[right, left] = distance
    return result


def _independent_columns(
    named_vectors: list[tuple[str, np.ndarray]],
) -> tuple[list[str], list[str], list[str], np.ndarray]:
    included: list[str] = []
    constants: list[str] = []
    collinear: list[str] = []
    vectors: list[np.ndarray] = []
    current = np.ones((len(named_vectors[0][1]), 1), dtype=np.float64)
    current_rank = 1
    for name, vector in named_vectors:
        values = np.asarray(vector, dtype=np.float64)
        if float(np.std(values)) < 1e-12:
            constants.append(name)
            continue
        candidate = np.column_stack([current, values])
        next_rank = int(np.linalg.matrix_rank(candidate))
        if next_rank == current_rank:
            collinear.append(name)
            continue
        included.append(name)
        vectors.append(values)
        current = candidate
        current_rank = next_rank
    return included, constants, collinear, np.column_stack(vectors)


def _max_vif(design: np.ndarray) -> float:
    values = np.asarray(design, dtype=np.float64)
    if values.shape[1] <= 1:
        return 1.0
    vifs: list[float] = []
    for index in range(values.shape[1]):
        target = values[:, index]
        others = np.delete(values, index, axis=1)
        fit = np.column_stack([np.ones(len(others)), others]) @ np.linalg.lstsq(
            np.column_stack([np.ones(len(others)), others]),
            target,
            rcond=None,
        )[0]
        residual = float(np.sum((target - fit) ** 2))
        total = float(np.sum((target - target.mean()) ** 2))
        r_squared = 1.0 - residual / max(total, 1e-12)
        vifs.append(1.0 / max(1.0 - r_squared, 1e-12))
    return max(vifs)


def build_nuisance_rdms(
    topology: GridTopology,
    units: Sequence[DecisionUnit],
    *,
    horizon: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Build a deterministic full-rank nuisance set.

    History identity and probe frequency are registered zero-variance controls:
    matched histories are averaged before the RDM and every unit is probed the
    same number of times. They are integrity checks, not design columns.
    """

    observations = np.stack([observation(topology, unit) for unit in units])
    sensory = _pairwise_squared(observations)
    physical = _physical_rdm(topology, units)
    _, volume_a = reachability_rdm(topology, units, "A", horizon=horizon)
    _, volume_b = reachability_rdm(topology, units, "B", horizon=horizon)
    named_rdms = [
        ("sensory_distance", sensory),
        ("physical_distance", physical),
        ("reachability_volume_A", _pairwise_absolute(volume_a)),
        ("reachability_volume_B", _pairwise_absolute(volume_b)),
        ("oracle_action_A", _action_rdm(topology, units, "A")),
        ("oracle_action_B", _action_rdm(topology, units, "B")),
        ("oracle_action_D", _action_rdm(topology, units, "D")),
        ("history_identity", np.zeros_like(sensory)),
        ("probe_frequency", np.zeros_like(sensory)),
    ]
    triangle = np.triu_indices(len(units), k=1)
    named_vectors = [(name, rdm[triangle]) for name, rdm in named_rdms]
    included, constants, collinear, design = _independent_columns(named_vectors)
    rdm_by_name = dict(named_rdms)
    nuisance = np.stack([rdm_by_name[name] for name in included], axis=-1)
    diagnostic_design = np.column_stack([np.ones(len(design)), design])
    return nuisance, {
        "included": included,
        "constant_controls": constants,
        "dropped_collinear": collinear,
        "rank": int(np.linalg.matrix_rank(diagnostic_design)),
        "columns": int(diagnostic_design.shape[1]),
        "full_rank": bool(
            np.linalg.matrix_rank(diagnostic_design) == diagnostic_design.shape[1]
        ),
        "max_vif": float(_max_vif(design)),
    }


def _subset_rdm(values: np.ndarray, indices: np.ndarray) -> np.ndarray:
    return values[np.ix_(indices, indices)]


def _subset_nuisance(values: np.ndarray, indices: np.ndarray) -> np.ndarray:
    return values[indices][:, indices]


def _rdm_correlation(left: np.ndarray, right: np.ndarray) -> float:
    triangle = np.triu_indices(left.shape[0], k=1)
    return float(np.corrcoef(left[triangle], right[triangle])[0, 1])


def _geometry(
    hidden: np.ndarray,
    reachability_a: np.ndarray,
    reachability_b: np.ndarray,
    nuisance: np.ndarray,
    precision: np.ndarray,
) -> dict[str, float]:
    hidden_rdm = crossnobis_rdm(hidden, precision=precision)
    align_a = partial_alignment(hidden_rdm, reachability_a, nuisance)
    align_b = partial_alignment(hidden_rdm, reachability_b, nuisance)
    return {
        "align_A": float(align_a["correlation"]),
        "align_B": float(align_b["correlation"]),
        "contrast_B_minus_A": float(
            align_b["correlation"] - align_a["correlation"]
        ),
        "target_norm_A": float(align_a["residual_target_norm"]),
        "target_norm_B": float(align_b["residual_target_norm"]),
        "full_rank": float(align_a["full_rank"] and align_b["full_rank"]),
    }


def _known_geometry_lift(
    context: ContextProbe,
    target_rdm: np.ndarray,
    nuisance: np.ndarray,
    *,
    baseline: float,
    precision: np.ndarray,
) -> float:
    n_units = len(context.units)
    centering = np.eye(n_units) - np.ones((n_units, n_units)) / n_units
    gram = -0.5 * centering @ target_rdm @ centering
    eigenvalues, eigenvectors = np.linalg.eigh(gram)
    order = np.argsort(eigenvalues)[::-1]
    keep = [index for index in order if eigenvalues[index] > 1e-10][:4]
    if not keep:
        return 0.0
    coordinates = eigenvectors[:, keep] * np.sqrt(eigenvalues[keep])
    coordinates /= coordinates.std(axis=0, keepdims=True) + 1e-8
    injected = context.hidden.copy()
    scale = 3.0 * float(np.std(injected))
    injected[:, :, : len(keep)] += scale * coordinates[:, None, :]
    moved = partial_alignment(
        crossnobis_rdm(injected, precision=precision),
        target_rdm,
        nuisance,
    )["correlation"]
    return float(moved - baseline)


def _collect_bundle(
    model: MetaGRU,
    topology: GridTopology,
    *,
    config: ExperimentConfig,
    seed: int,
    unit_seed: int,
    precision: np.ndarray | None = None,
) -> TopologyBundle:
    units = tuple(select_probe_units(topology, count=96, seed=unit_seed))
    context_seed = seed * 10007 + 211
    histories = config.probe_histories
    mature = config.mature_demonstrations
    early = config.early_swap_demonstrations
    contexts = {
        "A": collect_context(
            model,
            topology,
            units,
            prefix=("A",),
            demonstrations=(mature,),
            histories=histories,
            seed=context_seed,
        ),
        "B": collect_context(
            model,
            topology,
            units,
            prefix=("B",),
            demonstrations=(mature,),
            histories=histories,
            seed=context_seed,
        ),
        "D": collect_context(
            model,
            topology,
            units,
            prefix=("D",),
            demonstrations=(mature,),
            histories=histories,
            seed=context_seed,
        ),
        "sham": collect_random_context(
            model,
            topology,
            units,
            demonstrations=mature,
            histories=histories,
            seed=context_seed,
        ),
        "AB_early": collect_context(
            model,
            topology,
            units,
            prefix=("A", "B"),
            demonstrations=(mature, early),
            histories=histories,
            seed=context_seed,
        ),
        "AB_post": collect_context(
            model,
            topology,
            units,
            prefix=("A", "B"),
            demonstrations=(mature, mature),
            histories=histories,
            seed=context_seed,
        ),
        "AA_post": collect_context(
            model,
            topology,
            units,
            prefix=("A", "A"),
            demonstrations=(mature, mature),
            histories=histories,
            seed=context_seed,
        ),
        "BA_early": collect_context(
            model,
            topology,
            units,
            prefix=("B", "A"),
            demonstrations=(mature, early),
            histories=histories,
            seed=context_seed,
        ),
        "BA_post": collect_context(
            model,
            topology,
            units,
            prefix=("B", "A"),
            demonstrations=(mature, mature),
            histories=histories,
            seed=context_seed,
        ),
        "BB_post": collect_context(
            model,
            topology,
            units,
            prefix=("B", "B"),
            demonstrations=(mature, mature),
            histories=histories,
            seed=context_seed,
        ),
    }
    reachability_a, _ = reachability_rdm(
        topology,
        units,
        "A",
        horizon=config.future_horizon,
    )
    reachability_b, _ = reachability_rdm(
        topology,
        units,
        "B",
        horizon=config.future_horizon,
    )
    nuisance, diagnostics = build_nuisance_rdms(
        topology,
        units,
        horizon=config.future_horizon,
    )
    calibration, test = stable_unit_split(
        units,
        calibration_fraction=0.6,
        salt="constraint-swap-transport-v1",
    )
    if precision is None:
        calibration_hidden = np.concatenate(
            [
                contexts["A"].hidden[calibration],
                contexts["B"].hidden[calibration],
            ],
            axis=0,
        )
        precision = fit_crossnobis_precision(calibration_hidden, shrinkage=0.1)
    return TopologyBundle(
        topology=topology,
        units=units,
        contexts=contexts,
        reachability_a=reachability_a,
        reachability_b=reachability_b,
        nuisance=nuisance,
        nuisance_diagnostics=diagnostics,
        precision=precision,
        calibration=calibration,
        test=test,
    )


def _fit_transport(
    source: ContextProbe,
    target: ContextProbe,
    calibration: np.ndarray,
    *,
    config: ExperimentConfig,
) -> LowRankTransport:
    return fit_low_rank_transport(
        source.hidden[calibration].reshape(-1, source.hidden.shape[-1]),
        target.hidden[calibration].reshape(-1, target.hidden.shape[-1]),
        rank=config.transport_rank,
        ridge=0.001,
    )


def _permuted_transport(
    source: ContextProbe,
    target: ContextProbe,
    calibration: np.ndarray,
    *,
    config: ExperimentConfig,
    seed: int,
) -> LowRankTransport:
    rng = np.random.default_rng(seed)
    permuted = calibration[rng.permutation(len(calibration))]
    return fit_low_rank_transport(
        source.hidden[calibration].reshape(-1, source.hidden.shape[-1]),
        target.hidden[permuted].reshape(-1, target.hidden.shape[-1]),
        rank=config.transport_rank,
        ridge=0.001,
    )


def _decode_score(
    fit_hidden: np.ndarray,
    fit_targets: np.ndarray,
    eval_hidden: np.ndarray,
    eval_targets: np.ndarray,
) -> float:
    x_fit = np.column_stack([np.ones(len(fit_hidden)), fit_hidden])
    penalty = 1e-3 * np.eye(x_fit.shape[1])
    penalty[0, 0] = 0.0
    coefficients = np.linalg.solve(
        x_fit.T @ x_fit + penalty,
        x_fit.T @ fit_targets,
    )
    prediction = np.column_stack([np.ones(len(eval_hidden)), eval_hidden]) @ coefficients
    variance = np.var(eval_targets, axis=0)
    informative = variance > 1e-8
    feature_r2 = 1.0 - np.mean(
        (prediction[:, informative] - eval_targets[:, informative]) ** 2,
        axis=0,
    ) / variance[informative]
    return float(np.mean(np.clip(feature_r2, -1.0, 1.0)))


def _distribution_drift(baseline: np.ndarray, moved: np.ndarray) -> tuple[float, float]:
    base_flat = baseline.reshape(-1, baseline.shape[-1])
    moved_flat = moved.reshape(-1, moved.shape[-1])
    norm_ratio = float(
        np.mean(np.linalg.norm(moved_flat, axis=1))
        / max(np.mean(np.linalg.norm(base_flat, axis=1)), 1e-12)
    )
    base_cov = np.cov(base_flat, rowvar=False)
    moved_cov = np.cov(moved_flat, rowvar=False)
    covariance_drift = float(
        np.linalg.norm(moved_cov - base_cov)
        / max(np.linalg.norm(base_cov), 1e-12)
    )
    return abs(norm_ratio - 1.0), covariance_drift


def _accuracy(logits: np.ndarray, labels: np.ndarray) -> float:
    return float(np.mean(logits.argmax(axis=-1) == labels[:, None]))


def _compatible_rate(
    logits: np.ndarray,
    labels: np.ndarray,
    mask: np.ndarray,
) -> float:
    if not np.any(mask):
        return 0.0
    predictions = logits.argmax(axis=-1)
    return float(np.mean(predictions[mask] == labels[mask, None]))


def _monotone(values: list[float], *, increasing: bool) -> float:
    differences = np.diff(values)
    if increasing:
        return float(np.all(differences >= -0.02))
    return float(np.all(differences <= 0.02))


def _evaluate_transport(
    model: MetaGRU,
    bundle: TopologyBundle,
    *,
    source_key: str,
    target_key: str,
    active: Literal["A", "B"],
    opposite: Literal["A", "B"],
    targeted: LowRankTransport,
    controls: list[LowRankTransport],
    kind: Literal["undo", "rescue"],
) -> dict[str, float]:
    test = bundle.test
    source = bundle.contexts[source_key]
    target = bundle.contexts[target_key]
    source_hidden = source.hidden[test]
    baseline_logits = source.logits[test]
    test_units = [bundle.units[int(index)] for index in test]
    active_labels = np.asarray(
        [oracle_action(unit, active) for unit in test_units]
    )
    opposite_labels = np.asarray(
        [oracle_action(unit, opposite) for unit in test_units]
    )
    moved_hidden = targeted.apply(source_hidden, dose=1.0)
    moved_logits = action_head_logits(model, moved_hidden)
    control_hidden = [control.apply(source_hidden, dose=1.0) for control in controls]
    control_logits = [action_head_logits(model, hidden) for hidden in control_hidden]
    baseline_accuracy = _accuracy(baseline_logits, active_labels)
    moved_accuracy = _accuracy(moved_logits, active_labels)
    control_accuracies = [_accuracy(logits, active_labels) for logits in control_logits]
    reach_a = _subset_rdm(bundle.reachability_a, test)
    reach_b = _subset_rdm(bundle.reachability_b, test)
    nuisance = _subset_nuisance(bundle.nuisance, test)
    baseline_geometry = _geometry(
        source_hidden, reach_a, reach_b, nuisance, bundle.precision
    )
    moved_geometry = _geometry(
        moved_hidden, reach_a, reach_b, nuisance, bundle.precision
    )
    control_geometry = [
        _geometry(hidden, reach_a, reach_b, nuisance, bundle.precision)
        for hidden in control_hidden
    ]
    sign = 1.0 if active == "B" else -1.0
    baseline_specific = sign * baseline_geometry["contrast_B_minus_A"]
    moved_specific = sign * moved_geometry["contrast_B_minus_A"]
    control_specific = [
        sign * geometry["contrast_B_minus_A"]
        for geometry in control_geometry
    ]

    if kind == "undo":
        specific_behavior = (baseline_accuracy - moved_accuracy) - max(
            baseline_accuracy - accuracy for accuracy in control_accuracies
        )
        specific_geometry = (baseline_specific - moved_specific) - max(
            baseline_specific - value for value in control_specific
        )
        discordant = active_labels != opposite_labels
        moved_compatible = _compatible_rate(moved_logits, opposite_labels, discordant)
        control_compatible = max(
            _compatible_rate(logits, opposite_labels, discordant)
            for logits in control_logits
        )
        compatible_shift = moved_compatible - control_compatible
        doses = [0.0, 0.5, 1.0]
        dose_accuracies = [
            _accuracy(
                action_head_logits(model, targeted.apply(source_hidden, dose=dose)),
                active_labels,
            )
            for dose in doses
        ]
        monotone = _monotone(dose_accuracies, increasing=False)
    else:
        specific_behavior = (moved_accuracy - baseline_accuracy) - max(
            accuracy - baseline_accuracy for accuracy in control_accuracies
        )
        specific_geometry = (moved_specific - baseline_specific) - max(
            value - baseline_specific for value in control_specific
        )
        compatible_shift = moved_accuracy - max(control_accuracies)
        doses = [0.0, 0.5, 1.0]
        dose_accuracies = [
            _accuracy(
                action_head_logits(model, targeted.apply(source_hidden, dose=dose)),
                active_labels,
            )
            for dose in doses
        ]
        monotone = _monotone(dose_accuracies, increasing=True)

    fit_hidden = source.hidden[bundle.calibration].reshape(
        -1,
        source.hidden.shape[-1],
    )
    fit_observations = np.repeat(
        np.stack(
            [observation(bundle.topology, bundle.units[index]) for index in bundle.calibration]
        ),
        source.hidden.shape[1],
        axis=0,
    )
    eval_observations = np.repeat(
        np.stack([observation(bundle.topology, bundle.units[index]) for index in test]),
        source.hidden.shape[1],
        axis=0,
    )
    baseline_decode = _decode_score(
        fit_hidden,
        fit_observations,
        source_hidden.reshape(-1, source_hidden.shape[-1]),
        eval_observations,
    )
    moved_decode = _decode_score(
        fit_hidden,
        fit_observations,
        moved_hidden.reshape(-1, moved_hidden.shape[-1]),
        eval_observations,
    )
    norm_drift, covariance_drift = _distribution_drift(source_hidden, moved_hidden)
    return {
        "specific_behavior": float(specific_behavior),
        "compatible_shift": float(compatible_shift),
        "specific_geometry": float(specific_geometry),
        "decode_loss": float(baseline_decode - moved_decode),
        "norm_drift": float(norm_drift),
        "cov_drift": float(covariance_drift),
        "monotone": float(monotone),
    }


def _fit_primary_transports(
    primary: TopologyBundle,
    *,
    config: ExperimentConfig,
    seed: int,
) -> dict[str, tuple[LowRankTransport, list[LowRankTransport]]]:
    specifications = {
        "undo_B": ("B", "A"),
        "undo_A": ("A", "B"),
        "rescue_B": ("AB_early", "B"),
        "rescue_A": ("BA_early", "A"),
    }
    result: dict[str, tuple[LowRankTransport, list[LowRankTransport]]] = {}
    for offset, (name, (source_key, target_key)) in enumerate(specifications.items()):
        targeted = _fit_transport(
            primary.contexts[source_key],
            primary.contexts[target_key],
            primary.calibration,
            config=config,
        )
        controls = [
            _permuted_transport(
                primary.contexts[source_key],
                primary.contexts[target_key],
                primary.calibration,
                config=config,
                seed=seed * 101 + offset,
            )
        ]
        controls.extend(
            matched_random_transport(
                targeted,
                calibration_hidden=primary.contexts[source_key].hidden[
                    primary.calibration
                ],
                seed=seed * 10_007 + offset * 101 + index,
            )
            for index in range(16)
        )
        result[name] = targeted, controls
    return result


def _bundle_metrics(
    model: MetaGRU,
    bundle: TopologyBundle,
    transports: dict[str, tuple[LowRankTransport, list[LowRankTransport]]],
) -> dict[str, float]:
    geometries = {
        name: _geometry(
            context.hidden,
            bundle.reachability_a,
            bundle.reachability_b,
            bundle.nuisance,
            bundle.precision,
        )
        for name in ("A", "B", "AB_post", "AA_post", "BA_post", "BB_post")
        for context in (bundle.contexts[name],)
    }
    geometry_a_specific = (
        geometries["A"]["align_A"] - geometries["A"]["align_B"]
    )
    geometry_b_specific = (
        geometries["B"]["align_B"] - geometries["B"]["align_A"]
    )
    sensory = _pairwise_squared(
        np.stack([observation(bundle.topology, unit) for unit in bundle.units])
    )
    physical = _physical_rdm(bundle.topology, bundle.units)
    hidden_a = crossnobis_rdm(
        bundle.contexts["A"].hidden, precision=bundle.precision
    )
    hidden_b = crossnobis_rdm(
        bundle.contexts["B"].hidden, precision=bundle.precision
    )
    sham = _geometry(
        bundle.contexts["sham"].hidden,
        bundle.reachability_a,
        bundle.reachability_b,
        bundle.nuisance,
        bundle.precision,
    )
    geometry_comparators = {
        "geometry_A_over_sensory": geometries["A"]["align_A"]
        - _rdm_correlation(hidden_a, sensory),
        "geometry_A_over_physical": geometries["A"]["align_A"]
        - _rdm_correlation(hidden_a, physical),
        "geometry_A_over_action": geometries["A"]["align_A"]
        - _rdm_correlation(
            hidden_a, _action_rdm(bundle.topology, bundle.units, "A")
        ),
        "geometry_A_over_sham": geometries["A"]["align_A"] - sham["align_A"],
        "geometry_B_over_sensory": geometries["B"]["align_B"]
        - _rdm_correlation(hidden_b, sensory),
        "geometry_B_over_physical": geometries["B"]["align_B"]
        - _rdm_correlation(hidden_b, physical),
        "geometry_B_over_action": geometries["B"]["align_B"]
        - _rdm_correlation(
            hidden_b, _action_rdm(bundle.topology, bundle.units, "B")
        ),
        "geometry_B_over_sham": geometries["B"]["align_B"] - sham["align_B"],
    }
    swap_tau_ab = (
        geometries["AB_post"]["contrast_B_minus_A"]
        - geometries["AA_post"]["contrast_B_minus_A"]
    )
    swap_tau_ba = (
        geometries["BB_post"]["contrast_B_minus_A"]
        - geometries["BA_post"]["contrast_B_minus_A"]
    )
    no_swap_drift = max(
        abs(
            geometries["AA_post"]["contrast_B_minus_A"]
            - geometries["A"]["contrast_B_minus_A"]
        ),
        abs(
            geometries["BB_post"]["contrast_B_minus_A"]
            - geometries["B"]["contrast_B_minus_A"]
        ),
    )
    undo_b = _evaluate_transport(
        model,
        bundle,
        source_key="B",
        target_key="A",
        active="B",
        opposite="A",
        targeted=transports["undo_B"][0],
        controls=transports["undo_B"][1],
        kind="undo",
    )
    undo_a = _evaluate_transport(
        model,
        bundle,
        source_key="A",
        target_key="B",
        active="A",
        opposite="B",
        targeted=transports["undo_A"][0],
        controls=transports["undo_A"][1],
        kind="undo",
    )
    rescue_b = _evaluate_transport(
        model,
        bundle,
        source_key="AB_early",
        target_key="B",
        active="B",
        opposite="A",
        targeted=transports["rescue_B"][0],
        controls=transports["rescue_B"][1],
        kind="rescue",
    )
    rescue_a = _evaluate_transport(
        model,
        bundle,
        source_key="BA_early",
        target_key="A",
        active="A",
        opposite="B",
        targeted=transports["rescue_A"][0],
        controls=transports["rescue_A"][1],
        kind="rescue",
    )
    return {
        "accuracy_A": bundle.contexts["A"].accuracy,
        "accuracy_B": bundle.contexts["B"].accuracy,
        "accuracy_D": bundle.contexts["D"].accuracy,
        "sham_accuracy": bundle.contexts["sham"].accuracy,
        "known_geometry_lift": _known_geometry_lift(
            bundle.contexts["A"],
            bundle.reachability_a,
            bundle.nuisance,
            baseline=geometries["A"]["align_A"],
            precision=bundle.precision,
        ),
        "geometry_A_specific": float(geometry_a_specific),
        "geometry_B_specific": float(geometry_b_specific),
        **{name: float(value) for name, value in geometry_comparators.items()},
        "swap_tau_AB": float(swap_tau_ab),
        "swap_tau_BA": float(swap_tau_ba),
        "no_swap_drift": float(no_swap_drift),
        **{
            f"undo_B_{name}": value
            for name, value in {
                "specific_harm": undo_b["specific_behavior"],
                "opposite_shift": undo_b["compatible_shift"],
                "geometry_shift": undo_b["specific_geometry"],
                "decode_loss": undo_b["decode_loss"],
                "norm_drift": undo_b["norm_drift"],
                "cov_drift": undo_b["cov_drift"],
                "monotone": undo_b["monotone"],
            }.items()
        },
        **{
            f"undo_A_{name}": value
            for name, value in {
                "specific_harm": undo_a["specific_behavior"],
                "opposite_shift": undo_a["compatible_shift"],
                "geometry_shift": undo_a["specific_geometry"],
                "decode_loss": undo_a["decode_loss"],
                "norm_drift": undo_a["norm_drift"],
                "cov_drift": undo_a["cov_drift"],
                "monotone": undo_a["monotone"],
            }.items()
        },
        **{
            f"rescue_B_{name}": value
            for name, value in {
                "specific_gain": rescue_b["specific_behavior"],
                "compatible_shift": rescue_b["compatible_shift"],
                "geometry_shift": rescue_b["specific_geometry"],
                "decode_loss": rescue_b["decode_loss"],
                "norm_drift": rescue_b["norm_drift"],
                "cov_drift": rescue_b["cov_drift"],
                "monotone": rescue_b["monotone"],
            }.items()
        },
        **{
            f"rescue_A_{name}": value
            for name, value in {
                "specific_gain": rescue_a["specific_behavior"],
                "compatible_shift": rescue_a["compatible_shift"],
                "geometry_shift": rescue_a["specific_geometry"],
                "decode_loss": rescue_a["decode_loss"],
                "norm_drift": rescue_a["norm_drift"],
                "cov_drift": rescue_a["cov_drift"],
                "monotone": rescue_a["monotone"],
            }.items()
        },
    }


def analyze_seed(
    model: MetaGRU,
    *,
    seed: int,
    config: ExperimentConfig,
) -> dict[str, Any]:
    primary_topology = GridTopology("torus", 6, 6)
    transfer_topology = GridTopology("cylinder_x", 7, 7)
    primary = _collect_bundle(
        model,
        primary_topology,
        config=config,
        seed=seed,
        unit_seed=20260727,
    )
    transfer = _collect_bundle(
        model,
        transfer_topology,
        config=config,
        seed=seed,
        unit_seed=20260727,
        precision=primary.precision,
    )
    transports = _fit_primary_transports(primary, config=config, seed=seed)
    hist_a = action_histogram(
        all_decision_units(primary_topology),
        "A",
    )
    hist_b = action_histogram(
        all_decision_units(primary_topology),
        "B",
    )
    rdm_correlation = float(
        np.corrcoef(
            primary.reachability_a[np.triu_indices(len(primary.units), k=1)],
            primary.reachability_b[np.triu_indices(len(primary.units), k=1)],
        )[0, 1]
    )
    return {
        "seed": seed,
        "integrity": {
            "action_histogram_A": hist_a,
            "action_histogram_B": hist_b,
            "action_histograms_match": hist_a == hist_b,
            "reachability_rdm_correlation": rdm_correlation,
            "primary_nuisance": primary.nuisance_diagnostics,
            "transfer_nuisance": transfer.nuisance_diagnostics,
            "calibration_count": int(len(primary.calibration)),
            "test_count": int(len(primary.test)),
            "split_overlap": int(
                len(set(primary.calibration.tolist()) & set(primary.test.tolist()))
            ),
        },
        "primary": _bundle_metrics(model, primary, transports),
        "transfer": _bundle_metrics(model, transfer, transports),
    }


def _intervals(
    rows: list[dict[str, Any]],
    scope: str,
    metrics: Sequence[str],
    *,
    samples: int,
    seed: int,
) -> dict[str, dict[str, float]]:
    return {
        metric: paired_bootstrap_interval(
            [float(row[scope][metric]) for row in rows],
            samples=samples,
            seed=seed + index * 101,
        )
        for index, metric in enumerate(metrics)
    }


PRIMARY_METRICS = (
    "accuracy_A",
    "accuracy_B",
    "accuracy_D",
    "sham_accuracy",
    "known_geometry_lift",
    "geometry_A_specific",
    "geometry_B_specific",
    "geometry_A_over_sensory",
    "geometry_A_over_physical",
    "geometry_A_over_action",
    "geometry_A_over_sham",
    "geometry_B_over_sensory",
    "geometry_B_over_physical",
    "geometry_B_over_action",
    "geometry_B_over_sham",
    "swap_tau_AB",
    "swap_tau_BA",
    "no_swap_drift",
    "undo_B_specific_harm",
    "undo_A_specific_harm",
    "undo_B_opposite_shift",
    "undo_A_opposite_shift",
    "undo_B_geometry_shift",
    "undo_A_geometry_shift",
    "undo_B_decode_loss",
    "undo_A_decode_loss",
    "undo_B_norm_drift",
    "undo_A_norm_drift",
    "undo_B_cov_drift",
    "undo_A_cov_drift",
    "undo_B_monotone",
    "undo_A_monotone",
    "rescue_B_specific_gain",
    "rescue_A_specific_gain",
    "rescue_B_compatible_shift",
    "rescue_A_compatible_shift",
    "rescue_B_geometry_shift",
    "rescue_A_geometry_shift",
    "rescue_B_decode_loss",
    "rescue_A_decode_loss",
    "rescue_B_norm_drift",
    "rescue_A_norm_drift",
    "rescue_B_cov_drift",
    "rescue_A_cov_drift",
    "rescue_B_monotone",
    "rescue_A_monotone",
)


def _gate_from_intervals(
    intervals: dict[str, dict[str, float]],
    *,
    topology_transport: bool,
    direction_counts: dict[str, int],
) -> dict[str, dict[str, Any]]:
    prefix = "transfer " if topology_transport else ""
    competence = (
        intervals["accuracy_A"]["mean"] >= 0.85
        and intervals["accuracy_B"]["mean"] >= 0.85
        and intervals["accuracy_D"]["mean"] >= 0.75
        and intervals["sham_accuracy"]["mean"] <= 0.60
        and intervals["known_geometry_lift"]["lower"] > 0.20
    )
    geometry = (
        intervals["geometry_A_specific"]["lower"] > 0.05
        and intervals["geometry_B_specific"]["lower"] > 0.05
        and direction_counts["A"] >= 28
        and direction_counts["B"] >= 28
        and all(
            intervals[f"geometry_{constraint}_over_{comparator}"]["lower"] > 0.0
            for constraint in ("A", "B")
            for comparator in ("sensory", "physical", "action", "sham")
        )
    )
    swap = (
        intervals["swap_tau_AB"]["lower"] > 0.05
        and intervals["swap_tau_BA"]["lower"] > 0.05
        and intervals["no_swap_drift"]["upper"] < 0.05
    )
    impairment = all(
        [
            intervals["undo_B_specific_harm"]["lower"] > 0.10,
            intervals["undo_A_specific_harm"]["lower"] > 0.10,
            intervals["undo_B_opposite_shift"]["lower"] > 0.05,
            intervals["undo_A_opposite_shift"]["lower"] > 0.05,
            intervals["undo_B_geometry_shift"]["lower"] > 0.0,
            intervals["undo_A_geometry_shift"]["lower"] > 0.0,
            intervals["undo_B_decode_loss"]["upper"] < 0.03,
            intervals["undo_A_decode_loss"]["upper"] < 0.03,
            intervals["undo_B_norm_drift"]["upper"] < 0.10,
            intervals["undo_A_norm_drift"]["upper"] < 0.10,
            intervals["undo_B_cov_drift"]["upper"] < 0.10,
            intervals["undo_A_cov_drift"]["upper"] < 0.10,
            intervals["undo_B_monotone"]["mean"] >= 0.875,
            intervals["undo_A_monotone"]["mean"] >= 0.875,
        ]
    )
    rescue = all(
        [
            intervals["rescue_B_specific_gain"]["lower"] > 0.10,
            intervals["rescue_A_specific_gain"]["lower"] > 0.10,
            intervals["rescue_B_compatible_shift"]["lower"] > 0.05,
            intervals["rescue_A_compatible_shift"]["lower"] > 0.05,
            intervals["rescue_B_geometry_shift"]["lower"] > 0.0,
            intervals["rescue_A_geometry_shift"]["lower"] > 0.0,
            intervals["rescue_B_decode_loss"]["upper"] < 0.03,
            intervals["rescue_A_decode_loss"]["upper"] < 0.03,
            intervals["rescue_B_norm_drift"]["upper"] < 0.10,
            intervals["rescue_A_norm_drift"]["upper"] < 0.10,
            intervals["rescue_B_cov_drift"]["upper"] < 0.10,
            intervals["rescue_A_cov_drift"]["upper"] < 0.10,
            intervals["rescue_B_monotone"]["mean"] >= 0.875,
            intervals["rescue_A_monotone"]["mean"] >= 0.875,
        ]
    )
    return {
        "competence": {
            "pass": competence,
            "rule": f"{prefix}accuracy/control/positive-control thresholds",
        },
        "geometry": {
            "pass": geometry,
            "direction_counts": direction_counts,
            "required_count": 28,
            "rule": (
                f"{prefix}both active-specific lower bounds > 0.05, "
                "28/32 positive directions, and all comparator lower bounds > 0"
            ),
        },
        "swap": {
            "pass": swap,
            "rule": f"{prefix}both swap lower bounds > 0.05 and no-swap drift < 0.05",
        },
        "impairment": {
            "pass": impairment,
            "rule": f"{prefix}both selective-impairment directions and preservation controls",
        },
        "rescue": {
            "pass": rescue,
            "rule": f"{prefix}both selective-rescue directions and preservation controls",
        },
    }


def summarize_registered_rows(
    rows: list[dict[str, Any]],
    *,
    bootstrap_samples: int,
    seed: int,
) -> dict[str, Any]:
    expected_seeds = list(range(32))
    observed_seeds = sorted(int(row.get("seed", -1)) for row in rows)
    if observed_seeds != expected_seeds:
        raise ValueError("registered adjudication requires exactly unique seeds 0 through 31")
    primary_intervals = _intervals(
        rows,
        "primary",
        PRIMARY_METRICS,
        samples=bootstrap_samples,
        seed=seed,
    )
    transfer_intervals = _intervals(
        rows,
        "transfer",
        PRIMARY_METRICS,
        samples=bootstrap_samples,
        seed=seed + 100_000,
    )
    primary_gates = _gate_from_intervals(
        primary_intervals,
        topology_transport=False,
        direction_counts={
            constraint: sum(
                float(row["primary"][f"geometry_{constraint}_specific"]) > 0.0
                for row in rows
            )
            for constraint in ("A", "B")
        },
    )
    transfer_gates = _gate_from_intervals(
        transfer_intervals,
        topology_transport=True,
        direction_counts={
            constraint: sum(
                float(row["transfer"][f"geometry_{constraint}_specific"]) > 0.0
                for row in rows
            )
            for constraint in ("A", "B")
        },
    )
    integrity_rows: list[dict[str, Any]] = [
        integrity
        for row in rows
        if isinstance((integrity := row.get("integrity")), dict)
    ]
    integrity_pass = len(integrity_rows) == len(rows)
    integrity_reasons: list[str] = []
    if not integrity_pass:
        integrity_reasons.append("missing_integrity_rows")
    for integrity in integrity_rows:
        try:
            checks = {
                "action_histograms_match": bool(integrity["action_histograms_match"]),
                "rdm_non_collinear": abs(
                    float(integrity["reachability_rdm_correlation"])
                )
                < 0.95,
                "primary_nuisance_full_rank": bool(
                    integrity["primary_nuisance"]["full_rank"]
                ),
                "transfer_nuisance_full_rank": bool(
                    integrity["transfer_nuisance"]["full_rank"]
                ),
                "primary_vif": float(integrity["primary_nuisance"]["max_vif"])
                < 10.0,
                "transfer_vif": float(integrity["transfer_nuisance"]["max_vif"])
                < 10.0,
                "split_disjoint": int(integrity["split_overlap"]) == 0,
            }
        except (KeyError, TypeError, ValueError):
            integrity_pass = False
            integrity_reasons.append("malformed_integrity_row")
            continue
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            integrity_pass = False
            integrity_reasons.extend(failed)
    both_competent_count = sum(
        1
        for row in rows
        if row["primary"]["accuracy_A"] > 0.80
        and row["primary"]["accuracy_B"] > 0.80
    )
    f1_pass = (
        primary_gates["competence"]["pass"]
        and both_competent_count >= 28
    )
    g5_pass = all(
        transfer_gates[name]["pass"]
        for name in ("competence", "geometry", "swap", "impairment", "rescue")
    )
    gates = {
        "F0_integrity_identifiability": {
            "pass": integrity_pass,
            "failed_checks": sorted(set(integrity_reasons)),
        },
        "F1_competence_measurement_sensitivity": {
            "pass": f1_pass,
            "both_task_seed_count": both_competent_count,
            "required_count": 28,
            "components": primary_gates["competence"],
        },
        "G1_constraint_specific_geometry": primary_gates["geometry"],
        "G2_swap_tracking": primary_gates["swap"],
        "G3_selective_impairment": primary_gates["impairment"],
        "G4_selective_rescue": primary_gates["rescue"],
        "G5_topology_transport": {
            "pass": g5_pass,
            "components": transfer_gates,
            "rule": "all transfer competence, geometry, swap, impairment, and rescue gates",
        },
    }
    verdict = evaluate_gates(gates)
    return {
        "n_seeds": len(rows),
        "bootstrap_samples": bootstrap_samples,
        "primary_intervals": primary_intervals,
        "transfer_intervals": transfer_intervals,
        "verdict": verdict,
    }
