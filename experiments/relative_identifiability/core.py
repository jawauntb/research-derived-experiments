#!/usr/bin/env python3
"""Exact finite specialization of experiment-relative identifiability."""

from __future__ import annotations

import itertools
from collections.abc import Hashable, Iterable
from dataclasses import dataclass
from typing import TypeAlias


Family: TypeAlias = tuple[str, ...]
Block: TypeAlias = tuple[str, ...]
Partition: TypeAlias = tuple[Block, ...]
Transcript: TypeAlias = tuple[Hashable, ...]


def _require_unique(values: tuple[str, ...], label: str) -> None:
    if len(set(values)) != len(values):
        raise ValueError(f"{label} must be unique")


def _require_hashable(value: object, label: str) -> None:
    try:
        hash(value)
    except TypeError as error:
        raise ValueError(f"{label} must be hashable") from error


def _require_homogeneous_types(
    values: Iterable[object],
    label: str,
) -> None:
    """Reject Python values whose cross-type equality would erase distinctions."""

    value_types = {type(value) for value in values}
    if len(value_types) > 1:
        raise ValueError(f"{label} must share one runtime type")


@dataclass(frozen=True)
class FiniteTarget:
    """A named target value aligned with the system's realization order."""

    name: str
    values: tuple[Hashable, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("target name must be nonempty")
        _require_homogeneous_types(self.values, "target values")
        for value in self.values:
            _require_hashable(value, "target values")


@dataclass(frozen=True)
class FiniteExperimentSystem:
    """A finite total table of typed-by-column deterministic observations."""

    name: str
    realizations: tuple[str, ...]
    experiments: tuple[str, ...]
    outcomes: tuple[tuple[Hashable, ...], ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("system name must be nonempty")
        if not self.realizations:
            raise ValueError("realizations must be nonempty")
        _require_unique(self.realizations, "realization names")
        _require_unique(self.experiments, "experiment names")
        if len(self.outcomes) != len(self.realizations):
            raise ValueError("outcome table must have one row per realization")
        for row in self.outcomes:
            if len(row) != len(self.experiments):
                raise ValueError("outcome table must have one outcome per experiment")
            for outcome in row:
                _require_hashable(outcome, "outcomes")
        for experiment_index in range(len(self.experiments)):
            _require_homogeneous_types(
                (row[experiment_index] for row in self.outcomes),
                f"outcomes for experiment {self.experiments[experiment_index]!r}",
            )

    def normalize_family(self, family: Iterable[str]) -> Family:
        """Validate a set-like family and return it in declared experiment order."""

        supplied = tuple(family)
        if len(set(supplied)) != len(supplied):
            raise ValueError("experiment family members must be unique")
        unknown = set(supplied).difference(self.experiments)
        if unknown:
            rendered = ", ".join(sorted(unknown))
            raise ValueError(f"unknown experiment(s): {rendered}")
        selected = set(supplied)
        return tuple(
            experiment for experiment in self.experiments if experiment in selected
        )

    def transcript(self, realization: str, family: Iterable[str]) -> Transcript:
        """Return the complete selected-family transcript for one realization."""

        try:
            realization_index = self.realizations.index(realization)
        except ValueError as error:
            raise ValueError(f"unknown realization: {realization}") from error
        normalized = self.normalize_family(family)
        experiment_indices = tuple(
            self.experiments.index(experiment) for experiment in normalized
        )
        row = self.outcomes[realization_index]
        return tuple(row[index] for index in experiment_indices)

    def partition(self, family: Iterable[str]) -> Partition:
        """Return the observational quotient in stable realization order."""

        normalized = self.normalize_family(family)
        experiment_indices = tuple(
            self.experiments.index(experiment) for experiment in normalized
        )
        blocks: dict[Transcript, list[str]] = {}
        for realization, row in zip(
            self.realizations,
            self.outcomes,
            strict=True,
        ):
            transcript = tuple(row[index] for index in experiment_indices)
            blocks.setdefault(transcript, []).append(realization)
        return tuple(tuple(block) for block in blocks.values())


@dataclass(frozen=True)
class FactorizationCertificate:
    """Evidence that a target is constant on every observational fiber."""

    system_name: str
    target_name: str
    family: Family
    blocks: Partition
    block_targets: tuple[Hashable, ...]

    @property
    def status(self) -> str:
        return "identifiable"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "system": self.system_name,
            "target": self.target_name,
            "family": list(self.family),
            "quotient_blocks": [list(block) for block in self.blocks],
            "block_targets": list(self.block_targets),
        }


@dataclass(frozen=True)
class ObstructionCertificate:
    """A target-distinct pair with an identical complete family transcript."""

    system_name: str
    target_name: str
    family: Family
    left: str
    right: str
    shared_transcript: Transcript
    left_target: Hashable
    right_target: Hashable

    @property
    def status(self) -> str:
        return "obstructed"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "system": self.system_name,
            "target": self.target_name,
            "family": list(self.family),
            "pair": [self.left, self.right],
            "shared_transcript": list(self.shared_transcript),
            "target_values": [self.left_target, self.right_target],
        }


IdentificationResult: TypeAlias = FactorizationCertificate | ObstructionCertificate


@dataclass(frozen=True)
class RefinementCertificate:
    """Exact comparison of two nested experiment-family quotients."""

    system_name: str
    coarse_family: Family
    rich_family: Family
    coarse_blocks: Partition
    rich_blocks: Partition
    added_experiments: Family
    split_blocks: tuple[tuple[Block, ...], ...]
    separating_experiments: Family
    is_refinement: bool
    strict: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "system": self.system_name,
            "coarse_family": list(self.coarse_family),
            "rich_family": list(self.rich_family),
            "coarse_blocks": [list(block) for block in self.coarse_blocks],
            "rich_blocks": [list(block) for block in self.rich_blocks],
            "added_experiments": list(self.added_experiments),
            "split_blocks": [
                [list(block) for block in split] for split in self.split_blocks
            ],
            "separating_experiments": list(self.separating_experiments),
            "is_refinement": self.is_refinement,
            "strict": self.strict,
        }


@dataclass(frozen=True)
class MinimalFamilySearch:
    """All minimum-cardinality identifying families or a terminal obstruction."""

    system_name: str
    target_name: str
    minimum_size: int | None
    families: tuple[Family, ...]
    full_family_obstruction: ObstructionCertificate | None

    @property
    def identifiable(self) -> bool:
        return self.minimum_size is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "system": self.system_name,
            "target": self.target_name,
            "identifiable": self.identifiable,
            "minimum_size": self.minimum_size,
            "families": [list(family) for family in self.families],
            "full_family_obstruction": (
                None
                if self.full_family_obstruction is None
                else self.full_family_obstruction.to_dict()
            ),
        }


def _target_values(
    system: FiniteExperimentSystem,
    target: FiniteTarget,
) -> dict[str, Hashable]:
    if len(target.values) != len(system.realizations):
        raise ValueError("target must have one value per realization")
    return dict(zip(system.realizations, target.values, strict=True))


def identify_target(
    system: FiniteExperimentSystem,
    target: FiniteTarget,
    family: Iterable[str],
) -> IdentificationResult:
    """Factor a target through the quotient or emit the first obstruction."""

    normalized = system.normalize_family(family)
    values = _target_values(system, target)
    blocks = system.partition(normalized)
    block_targets: list[Hashable] = []

    for block in blocks:
        left = block[0]
        left_target = values[left]
        for right in block[1:]:
            right_target = values[right]
            if left_target != right_target:
                return ObstructionCertificate(
                    system_name=system.name,
                    target_name=target.name,
                    family=normalized,
                    left=left,
                    right=right,
                    shared_transcript=system.transcript(left, normalized),
                    left_target=left_target,
                    right_target=right_target,
                )
        block_targets.append(left_target)

    return FactorizationCertificate(
        system_name=system.name,
        target_name=target.name,
        family=normalized,
        blocks=blocks,
        block_targets=tuple(block_targets),
    )


def _partition_refines(fine: Partition, coarse: Partition) -> bool:
    coarse_sets = tuple(set(block) for block in coarse)
    return all(
        any(set(block).issubset(coarse_block) for coarse_block in coarse_sets)
        for block in fine
    )


def _split_blocks(
    coarse: Partition,
    rich: Partition,
) -> tuple[tuple[Block, ...], ...]:
    splits: list[tuple[Block, ...]] = []
    for coarse_block in coarse:
        coarse_members = set(coarse_block)
        pieces = tuple(block for block in rich if coarse_members.intersection(block))
        if len(pieces) > 1:
            splits.append(pieces)
    return tuple(splits)


def _separating_added_experiments(
    system: FiniteExperimentSystem,
    coarse_blocks: Partition,
    added: Family,
) -> Family:
    separating: list[str] = []
    for experiment in added:
        for block in coarse_blocks:
            outcomes = {
                system.transcript(realization, (experiment,))[0]
                for realization in block
            }
            if len(outcomes) > 1:
                separating.append(experiment)
                break
    return tuple(separating)


def analyze_refinement(
    system: FiniteExperimentSystem,
    coarse_family: Iterable[str],
    rich_family: Iterable[str],
) -> RefinementCertificate:
    """Verify the antitone relation between nested families and partitions."""

    coarse = system.normalize_family(coarse_family)
    rich = system.normalize_family(rich_family)
    if not set(coarse).issubset(rich):
        raise ValueError("rich family must contain the coarse family")
    coarse_blocks = system.partition(coarse)
    rich_blocks = system.partition(rich)
    added = tuple(experiment for experiment in rich if experiment not in coarse)
    refinement = _partition_refines(rich_blocks, coarse_blocks)
    return RefinementCertificate(
        system_name=system.name,
        coarse_family=coarse,
        rich_family=rich,
        coarse_blocks=coarse_blocks,
        rich_blocks=rich_blocks,
        added_experiments=added,
        split_blocks=_split_blocks(coarse_blocks, rich_blocks),
        separating_experiments=_separating_added_experiments(
            system,
            coarse_blocks,
            added,
        ),
        is_refinement=refinement,
        strict=coarse_blocks != rich_blocks,
    )


def minimal_identifying_families(
    system: FiniteExperimentSystem,
    target: FiniteTarget,
) -> MinimalFamilySearch:
    """Exhaustively return every smallest family that identifies the target."""

    _target_values(system, target)
    for size in range(len(system.experiments) + 1):
        identifying: list[Family] = []
        for family in itertools.combinations(system.experiments, size):
            result = identify_target(system, target, family)
            if isinstance(result, FactorizationCertificate):
                identifying.append(family)
        if identifying:
            return MinimalFamilySearch(
                system_name=system.name,
                target_name=target.name,
                minimum_size=size,
                families=tuple(identifying),
                full_family_obstruction=None,
            )

    full_result = identify_target(system, target, system.experiments)
    if not isinstance(full_result, ObstructionCertificate):
        raise AssertionError("exhaustive search missed an identifying family")
    return MinimalFamilySearch(
        system_name=system.name,
        target_name=target.name,
        minimum_size=None,
        families=(),
        full_family_obstruction=full_result,
    )
