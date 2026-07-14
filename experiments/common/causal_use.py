"""Graded causal-use metrics for intervention dose-response experiments.

The metric is deliberately intervention-relative.  It compares a target
subspace with a matched wrong-subspace control, normalizes by removed mass,
integrates the positive specific-effect curve, and requires transport across
every declared commitment surface.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from statistics import fmean
from typing import Literal, TypeAlias


FeatureKind: TypeAlias = Literal["causal", "decodable_only", "null"]


@dataclass(frozen=True)
class CausalUseObservation:
    surface: str
    replicate: str
    dose: float
    target_loss_delta: float
    wrong_subspace_loss_delta: float
    removed_mass: float

    def __post_init__(self) -> None:
        if not self.surface or not self.replicate:
            raise ValueError("surface and replicate must be non-empty")
        if self.dose < 0:
            raise ValueError("dose must be non-negative")
        if self.removed_mass <= 0:
            raise ValueError("removed_mass must be positive")

    @property
    def specific_effect_per_mass(self) -> float:
        return (self.target_loss_delta - self.wrong_subspace_loss_delta) / self.removed_mass


@dataclass(frozen=True)
class DosePoint:
    dose: float
    mean_specific_effect_per_mass: float


@dataclass(frozen=True)
class SurfaceUse:
    surface: str
    curve: tuple[DosePoint, ...]
    positive_auc: float


@dataclass(frozen=True)
class CausalUseSummary:
    surfaces: tuple[SurfaceUse, ...]
    transport_score: float
    ci_low: float
    ci_high: float
    replicate_count: int


@dataclass(frozen=True)
class SyntheticSCMEvaluation:
    """Measured decoding and intervention rows from a transparent toy SCM."""

    feature_kind: FeatureKind
    decoding_accuracy: float
    observations: tuple[CausalUseObservation, ...]


def _orientation_free_decoding_accuracy(labels: tuple[int, ...], feature: tuple[int, ...]) -> float:
    direct = sum(label == value for label, value in zip(labels, feature, strict=True))
    inverted = sum(label == -value for label, value in zip(labels, feature, strict=True))
    return max(direct, inverted) / len(labels)


def evaluate_synthetic_scm_feature(feature_kind: FeatureKind) -> SyntheticSCMEvaluation:
    """Measure equal decodability and causal use in a transparent synthetic SCM.

    The causal and decodable-only features both perfectly encode the latent
    label.  The policy is structurally a function of only the causal feature,
    so intervening on the duplicate decodable feature leaves behavior
    unchanged.  The null feature is balanced and predicts the label at chance.
    """

    labels = (1, -1, 1, -1, 1, -1, 1, -1)
    features: dict[FeatureKind, tuple[int, ...]] = {
        "causal": labels,
        "decodable_only": labels,
        "null": (1, 1, -1, -1, 1, 1, -1, -1),
    }
    selected = features[feature_kind]
    observations: list[CausalUseObservation] = []
    for surface, gain in (("choice", 1.0), ("policy", 0.8)):
        baseline_actions = tuple(gain * value for value in features["causal"])
        for replicate_index in range(4):
            for dose in (0.25, 0.5, 1.0):
                if feature_kind == "causal":
                    intervened_causal = tuple((1.0 - dose) * value for value in selected)
                else:
                    intervened_causal = features["causal"]
                intervened_actions = tuple(gain * value for value in intervened_causal)
                target_delta = fmean(
                    (baseline - intervened) ** 2
                    for baseline, intervened in zip(
                        baseline_actions, intervened_actions, strict=True
                    )
                )
                # The matched wrong-subspace intervention changes a feature
                # that is not a parent of policy output in this SCM.
                wrong_subspace_delta = 0.0
                removed_mass = dose * fmean(abs(value) for value in selected)
                observations.append(
                    CausalUseObservation(
                        surface=surface,
                        replicate=f"seed-{replicate_index}",
                        dose=dose,
                        target_loss_delta=target_delta,
                        wrong_subspace_loss_delta=wrong_subspace_delta,
                        removed_mass=removed_mass,
                    )
                )
    return SyntheticSCMEvaluation(
        feature_kind=feature_kind,
        decoding_accuracy=_orientation_free_decoding_accuracy(labels, selected),
        observations=tuple(observations),
    )


def _positive_auc(points: list[DosePoint]) -> float:
    if len(points) < 2:
        raise ValueError("each surface needs at least two distinct doses")
    ordered = sorted(points, key=lambda point: point.dose)
    if len({point.dose for point in ordered}) != len(ordered):
        raise ValueError("dose points must be unique after aggregation")
    area = 0.0
    for left, right in zip(ordered[:-1], ordered[1:], strict=True):
        width = right.dose - left.dose
        if width <= 0:
            raise ValueError("doses must be strictly increasing")
        area += width * (
            max(0.0, left.mean_specific_effect_per_mass)
            + max(0.0, right.mean_specific_effect_per_mass)
        ) / 2.0
    span = ordered[-1].dose - ordered[0].dose
    return area / span


def _summarize(observations: list[CausalUseObservation]) -> tuple[SurfaceUse, ...]:
    grouped: dict[str, dict[float, list[float]]] = {}
    for observation in observations:
        grouped.setdefault(observation.surface, {}).setdefault(observation.dose, []).append(
            observation.specific_effect_per_mass
        )
    surfaces: list[SurfaceUse] = []
    for surface, by_dose in sorted(grouped.items()):
        curve = tuple(
            DosePoint(dose, fmean(values)) for dose, values in sorted(by_dose.items())
        )
        surfaces.append(SurfaceUse(surface, curve, _positive_auc(list(curve))))
    if not surfaces:
        raise ValueError("at least one observation is required")
    return tuple(surfaces)


def _transport_score(observations: list[CausalUseObservation]) -> float:
    return min(surface.positive_auc for surface in _summarize(observations))


def summarize_causal_use(
    observations: list[CausalUseObservation],
    *,
    bootstrap_samples: int = 1000,
    seed: int = 20260714,
) -> CausalUseSummary:
    """Summarize use and a replicate-level bootstrap transport interval."""

    if bootstrap_samples < 1:
        raise ValueError("bootstrap_samples must be positive")
    replicates = sorted({observation.replicate for observation in observations})
    if len(replicates) < 2:
        raise ValueError("at least two independent replicates are required")
    by_replicate: dict[str, list[CausalUseObservation]] = {replicate: [] for replicate in replicates}
    for observation in observations:
        by_replicate[observation.replicate].append(observation)
    expected_cells = {
        (observation.surface, observation.dose) for observation in observations
    }
    for replicate, rows in by_replicate.items():
        cells = {(row.surface, row.dose) for row in rows}
        if cells != expected_cells or len(rows) != len(cells):
            raise ValueError(f"replicate {replicate} does not contain the complete unique dose grid")

    surfaces = _summarize(observations)
    score = min(surface.positive_auc for surface in surfaces)
    rng = random.Random(seed)
    boot: list[float] = []
    for _ in range(bootstrap_samples):
        sample: list[CausalUseObservation] = []
        for replicate in rng.choices(replicates, k=len(replicates)):
            sample.extend(by_replicate[replicate])
        boot.append(_transport_score(sample))
    ordered = sorted(boot)
    low_index = int(0.025 * (len(ordered) - 1))
    high_index = int(0.975 * (len(ordered) - 1))
    return CausalUseSummary(
        surfaces=surfaces,
        transport_score=score,
        ci_low=ordered[low_index],
        ci_high=ordered[high_index],
        replicate_count=len(replicates),
    )
