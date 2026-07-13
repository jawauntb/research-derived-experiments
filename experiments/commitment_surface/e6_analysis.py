"""Manifest, trajectory-integrity, and verdict analysis contracts for E6."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from experiments.commitment_surface.e6_core import (
    E6_ACCURACY_METRICS,
    E6_ARM_VALUES,
    E6_COLLAPSE_TOLERANCE,
    E6_CONFIRMATORY_GRID,
    E6_CONFIRMATORY_PARAMETERS,
    E6_GATE_METRICS,
    E6_GENERATIONS_PER_INPUT,
    E6_GENERATOR_COVERAGE_MARGIN,
    E6_PATCH_CE_THRESHOLD,
    E6_PATCH_DIP_TOLERANCE,
    E6_ROUNDS,
    E6_ROUND_INTEGRITY_FIELDS,
    E6_RUN_PROTOCOL_VERSION,
    E6_SELECTION_FRACTION,
    E6_TRANSPORT_RETENTION_FRACTION,
    E6Arm,
    E6GridSpec,
    E6RunKind,
    collapse_trajectory,
)


def _sequence_value(value: object, field: str) -> tuple[object, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{field} must be a sequence")
    return tuple(value)


def _int_sequence_value(value: object, field: str) -> tuple[int, ...]:
    values = _sequence_value(value, field)
    result: list[int] = []
    for item in values:
        if isinstance(item, bool) or not isinstance(item, int):
            raise ValueError(f"{field} must contain only integers")
        result.append(item)
    return tuple(result)


def confirmatory_config_mismatches(
    config: Mapping[str, object],
) -> tuple[str, ...]:
    mismatches = [
        f"unexpected:{field}"
        for field in sorted(set(config) - set(E6_CONFIRMATORY_PARAMETERS))
    ]
    for field, expected in E6_CONFIRMATORY_PARAMETERS.items():
        actual = config.get(field)
        if isinstance(expected, tuple):
            try:
                actual = _sequence_value(actual, field)
            except ValueError:
                mismatches.append(field)
                continue
        if actual != expected:
            mismatches.append(field)
    return tuple(mismatches)


def build_run_manifest(
    config: Mapping[str, object],
    *,
    run_kind: str | E6RunKind,
    implementation_fingerprint: str = E6_RUN_PROTOCOL_VERSION,
    execution_environment: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    try:
        kind = E6RunKind(run_kind)
    except ValueError as error:
        raise ValueError(
            "run_kind must be smoke, development, or confirmatory"
        ) from error
    if not implementation_fingerprint:
        raise ValueError("implementation_fingerprint must be nonempty")
    mismatches = confirmatory_config_mismatches(config)
    if kind is E6RunKind.CONFIRMATORY and mismatches:
        raise ValueError(
            "confirmatory launch drifts from frozen fields: "
            + ", ".join(mismatches)
        )

    sizes = tuple(str(item) for item in _sequence_value(config.get("sizes"), "sizes"))
    moduli = _int_sequence_value(config.get("moduli"), "moduli")
    seed_slots = _int_sequence_value(config.get("seed_slots"), "seed_slots")
    arms = tuple(str(item) for item in _sequence_value(config.get("arms"), "arms"))
    grid = E6GridSpec(sizes, moduli, seed_slots, arms)
    cells = [
        {
            "cell_id": f"{size}__n{modulus}__slot{seed_slot}__{arm}",
            "size": size,
            "n": modulus,
            "seed_slot": seed_slot,
            "arm": arm,
        }
        for size, modulus, seed_slot, arm in grid.expected_keys()
    ]
    fingerprint_source = {
        "protocol_version": E6_RUN_PROTOCOL_VERSION,
        "implementation_fingerprint": implementation_fingerprint,
        "execution_environment": dict(execution_environment or {}),
        "run_kind": kind.value,
        "config": dict(config),
        "cells": cells,
    }
    manifest_id = hashlib.sha256(
        json.dumps(
            fingerprint_source, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    return {
        "manifest_id": manifest_id,
        "protocol_version": E6_RUN_PROTOCOL_VERSION,
        "implementation_fingerprint": implementation_fingerprint,
        "execution_environment": dict(execution_environment or {}),
        "run_kind": kind.value,
        "confirmatory_config_pass": not mismatches,
        "confirmatory_config_mismatches": list(mismatches),
        "expected_cell_count": len(cells),
        "cells": cells,
    }


def grid_spec_for_run_kind(
    run_kind: str | E6RunKind,
) -> E6GridSpec | None:
    kind = E6RunKind(run_kind)
    return E6_CONFIRMATORY_GRID if kind is E6RunKind.CONFIRMATORY else None


def _valid_metric(metric: str, value: object) -> bool:
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not math.isfinite(float(value))
    ):
        return False
    numeric = float(value)
    if metric in E6_ACCURACY_METRICS or metric == "coverage_gain":
        return 0.0 <= numeric <= 1.0
    if metric == "generator_gain":
        return -1.0 <= numeric <= 1.0
    return True


def _round_errors(
    cell: Mapping[str, object], *, rounds: int = E6_ROUNDS
) -> list[str]:
    raw_rounds = cell.get("rounds")
    if isinstance(raw_rounds, str) or not isinstance(raw_rounds, Sequence):
        return ["rounds"]
    if len(raw_rounds) != rounds:
        return ["round_count"]
    errors: list[str] = []
    arm = cell.get("arm")
    if arm not in E6_ARM_VALUES:
        errors.append("arm")
    for index, row in enumerate(raw_rounds, start=1):
        if not isinstance(row, Mapping):
            errors.append(f"round_{index}")
            continue
        if row.get("round") != index:
            errors.append(f"round_{index}.index")
        for metric in E6_GATE_METRICS:
            if not _valid_metric(metric, row.get(metric)):
                errors.append(f"round_{index}.{metric}")
        pool_count = row.get("candidate_pool_count")
        valid_pool_count = (
            not isinstance(pool_count, bool)
            and isinstance(pool_count, int)
            and pool_count > 0
            and pool_count % E6_GENERATIONS_PER_INPUT == 0
        )
        if not valid_pool_count:
            errors.append(f"round_{index}.candidate_pool_count")
        count = row.get("selected_candidate_count")
        valid_selected_count = (
            not isinstance(count, bool) and isinstance(count, int) and count >= 0
        )
        if not valid_selected_count:
            errors.append(f"round_{index}.selected_candidate_count")
        if valid_pool_count and valid_selected_count and arm in E6_ARM_VALUES:
            assert isinstance(pool_count, int)
            expected_count = (
                0
                if arm == E6Arm.A_REF.value
                else max(1, math.floor(pool_count * E6_SELECTION_FRACTION))
            )
            if count != expected_count:
                errors.append(f"round_{index}.selection_fraction")
        digest = row.get("pool_digest")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            errors.append(f"round_{index}.pool_digest")
        for field in E6_ROUND_INTEGRITY_FIELDS:
            if row.get(field) is not True:
                errors.append(f"round_{index}.{field}")
    return errors


def cell_is_reusable(
    cell: Mapping[str, object], manifest_id: str, cell_id: str
) -> bool:
    if (
        cell.get("run_manifest_id") != manifest_id
        or cell.get("cell_id") != cell_id
        or cell.get("integrity_pass") is not True
    ):
        return False
    parts = cell_id.split("__")
    if len(parts) != 4:
        return False
    size, modulus_text, slot_text, arm = parts
    if not modulus_text.startswith("n") or not slot_text.startswith("slot"):
        return False
    try:
        modulus = int(modulus_text.removeprefix("n"))
        seed_slot = int(slot_text.removeprefix("slot"))
    except ValueError:
        return False
    if (
        cell.get("size") != size
        or cell.get("n") != modulus
        or cell.get("seed_slot") != seed_slot
        or cell.get("arm") != arm
    ):
        return False
    return not _round_errors(cell)


def _format_cell_key(key: tuple[str, int, int, str]) -> str:
    size, modulus, seed_slot, arm = key
    return f"{size}/n={modulus}/slot={seed_slot}/{arm}"


def audit_e6_grid(
    cells: Sequence[Mapping[str, object]], spec: E6GridSpec
) -> dict[str, object]:
    expected = set(spec.expected_keys())
    actual: list[tuple[str, int, int, str]] = []
    invalid_key_rows: list[int] = []
    invalid_trajectory_rows: list[dict[str, object]] = []
    integrity_failed_rows: list[int] = []
    for index, cell in enumerate(cells):
        size = cell.get("size")
        modulus = cell.get("n")
        seed_slot = cell.get("seed_slot")
        arm = cell.get("arm")
        if (
            not isinstance(size, str)
            or isinstance(modulus, bool)
            or not isinstance(modulus, int)
            or isinstance(seed_slot, bool)
            or not isinstance(seed_slot, int)
            or not isinstance(arm, str)
        ):
            invalid_key_rows.append(index)
        else:
            actual.append((size, modulus, seed_slot, arm))
        errors = _round_errors(cell)
        if errors:
            invalid_trajectory_rows.append({"row": index, "errors": errors})
        if cell.get("integrity_pass") is not True:
            integrity_failed_rows.append(index)

    counts = Counter(actual)
    actual_set = set(actual)
    missing = sorted(expected - actual_set)
    unexpected = sorted(actual_set - expected)
    duplicates = sorted(key for key, count in counts.items() if count > 1)
    grid_complete = (
        not missing
        and not unexpected
        and not duplicates
        and not invalid_key_rows
        and len(actual) == len(expected)
    )
    cell_data_complete = not invalid_trajectory_rows and not integrity_failed_rows
    return {
        "required": True,
        "expected_cell_count": len(expected),
        "observed_row_count": len(cells),
        "observed_unique_cell_count": len(actual_set),
        "missing_cells": [_format_cell_key(key) for key in missing],
        "unexpected_cells": [_format_cell_key(key) for key in unexpected],
        "duplicate_cells": [_format_cell_key(key) for key in duplicates],
        "invalid_key_rows": invalid_key_rows,
        "invalid_trajectory_rows": invalid_trajectory_rows,
        "grid_complete": grid_complete,
        "cell_data_complete": cell_data_complete,
    }


def _matched_cell_audit(
    cells: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    indexed: dict[tuple[str, int, int, str], Mapping[str, object]] = {}
    key_counts: Counter[tuple[str, int, int, str]] = Counter()
    for cell in cells:
        size = cell.get("size")
        modulus = cell.get("n")
        seed_slot = cell.get("seed_slot")
        arm = cell.get("arm")
        if (
            isinstance(size, str)
            and isinstance(modulus, int)
            and not isinstance(modulus, bool)
            and isinstance(seed_slot, int)
            and not isinstance(seed_slot, bool)
            and isinstance(arm, str)
        ):
            key = (size, modulus, seed_slot, arm)
            key_counts[key] += 1
            indexed.setdefault(key, cell)
    strata = sorted({key[:3] for key in indexed})
    mismatches: list[dict[str, object]] = []
    for key, count in sorted(key_counts.items()):
        if count > 1 and key[3] in {E6Arm.SC.value, E6Arm.CS.value}:
            mismatches.append(
                {"stratum": key[:3], "round": None, "fields": ["duplicate_pair"]}
            )
    matched_rounds = 0
    for stratum in strata:
        sc = indexed.get((*stratum, E6Arm.SC.value))
        cs = indexed.get((*stratum, E6Arm.CS.value))
        if sc is None or cs is None:
            if sc is not None or cs is not None:
                mismatches.append({"stratum": stratum, "round": None, "fields": ["pair"]})
            continue
        sc_rounds, cs_rounds = sc.get("rounds"), cs.get("rounds")
        if (
            isinstance(sc_rounds, str)
            or not isinstance(sc_rounds, Sequence)
            or isinstance(cs_rounds, str)
            or not isinstance(cs_rounds, Sequence)
        ):
            mismatches.append({"stratum": stratum, "round": None, "fields": ["rounds"]})
            continue
        if len(sc_rounds) != len(cs_rounds):
            mismatches.append(
                {"stratum": stratum, "round": None, "fields": ["round_count"]}
            )
            continue
        for round_index, (sc_row, cs_row) in enumerate(
            zip(sc_rounds, cs_rounds), start=1
        ):
            if not isinstance(sc_row, Mapping) or not isinstance(cs_row, Mapping):
                mismatches.append(
                    {"stratum": stratum, "round": round_index, "fields": ["row"]}
                )
                continue
            fields = []
            if sc_row.get("pool_digest") != cs_row.get("pool_digest"):
                fields.append("pool_digest")
            if sc_row.get("candidate_pool_count") != cs_row.get(
                "candidate_pool_count"
            ):
                fields.append("candidate_pool_count")
            if sc_row.get("selected_candidate_count") != cs_row.get(
                "selected_candidate_count"
            ):
                fields.append("selected_candidate_count")
            if fields:
                mismatches.append(
                    {"stratum": stratum, "round": round_index, "fields": fields}
                )
            else:
                matched_rounds += 1
    return {
        "matched_round_count": matched_rounds,
        "mismatches": mismatches,
        "pass": matched_rounds > 0 and not mismatches,
    }


def _trajectory_means(
    cells: Sequence[Mapping[str, object]], arm: E6Arm
) -> dict[str, list[float]]:
    result = {metric: [] for metric in E6_GATE_METRICS}
    arm_cells = [cell for cell in cells if cell.get("arm") == arm.value]
    for round_index in range(E6_ROUNDS):
        for metric in E6_GATE_METRICS:
            values: list[float] = []
            for cell in arm_cells:
                raw_rounds = cell.get("rounds")
                if (
                    isinstance(raw_rounds, str)
                    or not isinstance(raw_rounds, Sequence)
                    or len(raw_rounds) <= round_index
                ):
                    continue
                row = raw_rounds[round_index]
                if not isinstance(row, Mapping):
                    continue
                value = row.get(metric)
                if _valid_metric(metric, value):
                    assert isinstance(value, int | float)
                    values.append(float(value))
            result[metric].append(
                sum(values) / len(values) if values else float("nan")
            )
    return result


def analyze_e6(
    cells: Sequence[Mapping[str, object]],
    *,
    grid_spec: E6GridSpec | None = None,
) -> dict[str, Any]:
    """Apply the frozen E6 trajectory, transport, separator, and integrity gates."""
    present_arms = {
        E6Arm(str(cell["arm"]))
        for cell in cells
        if isinstance(cell.get("arm"), str)
        and str(cell.get("arm")) in E6_ARM_VALUES
    }
    trajectories = {
        arm.value: _trajectory_means(cells, arm) for arm in present_arms
    }
    required_smoke = {E6Arm.SC, E6Arm.CS, E6Arm.A_REF}
    smoke_complete = required_smoke <= present_arms
    finite_smoke = smoke_complete and all(
        math.isfinite(value)
        for arm in required_smoke
        for values in trajectories[arm.value].values()
        for value in values
    )
    integrity_pass = bool(cells) and all(
        cell.get("integrity_pass") is True and not _round_errors(cell)
        for cell in cells
    )
    matched_audit = _matched_cell_audit(cells)
    g5_exposure_integrity = bool(matched_audit["pass"])
    smoke_pass = (
        integrity_pass and finite_smoke and g5_exposure_integrity
    )
    grid_audit = (
        audit_e6_grid(cells, grid_spec)
        if grid_spec is not None
        else {
            "required": False,
            "expected_cell_count": None,
            "observed_row_count": len(cells),
            "grid_complete": False,
            "cell_data_complete": False,
        }
    )

    gates_available = finite_smoke
    if gates_available:
        sc = trajectories[E6Arm.SC.value]
        cs = trajectories[E6Arm.CS.value]
        a_ref = trajectories[E6Arm.A_REF.value]
        cs_accuracy = cs["canonical_ood_accuracy"]
        sc_accuracy = sc["canonical_ood_accuracy"]
        cs_collapse = collapse_trajectory(
            cs_accuracy, tolerance=E6_COLLAPSE_TOLERANCE
        )
        sc_collapse = collapse_trajectory(
            sc_accuracy, tolerance=E6_COLLAPSE_TOLERANCE
        )
        g1_no_collapse = (
            cs_accuracy[-1] >= max(cs_accuracy) - E6_COLLAPSE_TOLERANCE
        )
        sc_no_collapse = (
            sc_accuracy[-1] >= max(sc_accuracy) - E6_COLLAPSE_TOLERANCE
        )
        cs_patch = cs["canonical_normalized_patch_ce"]
        g2_load_bearing_gain = (
            all(
                later >= earlier - E6_PATCH_DIP_TOLERANCE
                for earlier, later in zip(cs_patch, cs_patch[1:])
            )
            and cs_patch[-1] >= E6_PATCH_CE_THRESHOLD
        )
        canonical_lift = (
            cs["canonical_ood_accuracy"][-1]
            - a_ref["canonical_ood_accuracy"][-1]
        )
        paraphrase_lift = (
            cs["paraphrase_ood_accuracy"][-1]
            - a_ref["paraphrase_ood_accuracy"][-1]
        )
        retained = (
            paraphrase_lift / canonical_lift
            if canonical_lift > 0.0
            else float("-inf")
        )
        g3_transport_survival = (
            cs["transported_normalized_patch_ce"][-1]
            >= E6_PATCH_CE_THRESHOLD
            and retained >= E6_TRANSPORT_RETENTION_FRACTION
        )
        separator = [
            generator - coverage
            for generator, coverage in zip(
                cs["generator_gain"], cs["coverage_gain"]
            )
        ]
        g4_not_mere_coverage = all(
            value >= E6_GENERATOR_COVERAGE_MARGIN for value in separator
        )
    else:
        cs_collapse = ()
        sc_collapse = ()
        g1_no_collapse = False
        sc_no_collapse = None
        g2_load_bearing_gain = False
        canonical_lift = float("nan")
        paraphrase_lift = float("nan")
        retained = float("nan")
        g3_transport_survival = False
        separator = []
        g4_not_mere_coverage = False

    confirmatory_ready = bool(
        grid_spec is not None
        and grid_audit["grid_complete"]
        and grid_audit["cell_data_complete"]
        and integrity_pass
        and g5_exposure_integrity
        and all(arm in present_arms for arm in E6Arm)
    )
    verdict = "pending_confirmatory_grid"
    if confirmatory_ready:
        if (
            g1_no_collapse
            and not sc_no_collapse
            and g2_load_bearing_gain
            and g3_transport_survival
            and g4_not_mere_coverage
        ):
            verdict = "surface_supported"
        elif not g1_no_collapse and not sc_no_collapse:
            verdict = "intrinsic_supported"
        else:
            verdict = "kill_or_draw"
    return {
        "n_cells": len(cells),
        "trajectories": trajectories,
        "collapse_trajectories": {
            E6Arm.SC.value: list(sc_collapse),
            E6Arm.CS.value: list(cs_collapse),
        },
        "integrity_pass": integrity_pass,
        "matched_pool_audit": matched_audit,
        "smoke_pass": smoke_pass,
        "confirmatory_ready": confirmatory_ready,
        "grid_audit": grid_audit,
        "g1_no_collapse": g1_no_collapse,
        "sc_expected_collapse": (
            None if sc_no_collapse is None else not sc_no_collapse
        ),
        "g2_load_bearing_gain": g2_load_bearing_gain,
        "canonical_lift_over_a_ref": canonical_lift,
        "paraphrase_lift_over_a_ref": paraphrase_lift,
        "paraphrase_lift_retained": retained,
        "g3_transport_survival": g3_transport_survival,
        "generator_minus_coverage_by_round": separator,
        "g4_not_mere_coverage": g4_not_mere_coverage,
        "g5_exposure_integrity": g5_exposure_integrity,
        "verdict": verdict,
    }
