"""Characterize OpenAI dispatch failures in the API black-box benchmark."""

from __future__ import annotations

import argparse
import json
import random
import time
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, cast

from experiments.long_horizon_bottleneck.api_blackbox import (
    ProviderResult,
    make_provider_call,
    parse_csv_arg,
    parse_int_csv_arg,
    read_jsonl,
    write_jsonl,
    write_summary,
)
from experiments.long_horizon_bottleneck.core import (
    PROMPT_JSON_ACTION_THRESHOLD,
    PROMPT_JSON_CONTROL_SCHEMA_THRESHOLD,
    parse_prompt_json_action,
)
from experiments.long_horizon_bottleneck.prompt_json_tasks import (
    SYSTEM_PROMPT,
    context_lines,
    episode_bits,
    format_user_prompt,
    messages,
    prompt_family_user_prompt,
    repair_messages,
    short_user_prompt,
    slot_phrase,
    visible_user_prompt,
)

DISPATCH_CHARACTERIZATION_CONTROLS = (
    "format_control",
    "visible_noop_control",
    "short_copy_control",
)
DISPATCH_CHARACTERIZATION_VARIANTS = (
    "dispatch_original",
    "wording_neutral",
    "copy_assisted",
    "repair_hinted",
)
DISPATCH_CHARACTERIZATION_CASE_TYPES = DISPATCH_CHARACTERIZATION_CONTROLS + DISPATCH_CHARACTERIZATION_VARIANTS


@dataclass(frozen=True)
class DispatchCharacterizationCase:
    case_id: str
    suite: str
    stress_case: str
    case_type: str
    condition: str
    seed: int
    episode: int
    critical_slot: int
    n_slots: int
    slot_gap: int
    variants_per_slot: int
    bits: tuple[int, ...]
    user_prompt: str

    @property
    def expected_value(self) -> int:
        return self.bits[self.critical_slot]

    @property
    def request_count(self) -> int:
        return 3 if self.case_type in DISPATCH_CHARACTERIZATION_VARIANTS else 1

    @property
    def prompt_family(self) -> str:
        return self.case_type


DispatchProviderCall = Callable[[list[dict[str, str]], DispatchCharacterizationCase, str], ProviderResult]


def build_dispatch_characterization_cases(
    *,
    stress_cases: list[str],
    case_types: list[str],
    seeds: int,
    episodes_per_cell: int,
    critical_slot: int,
    n_slots_values: list[int],
    slot_gap_values: list[int],
    variants_per_slot: int,
    base_seed: int,
) -> list[DispatchCharacterizationCase]:
    """Build deterministic diagnostic cases for the known dispatch failure cells."""

    if seeds <= 0:
        raise ValueError("seeds must be positive")
    if episodes_per_cell <= 0:
        raise ValueError("episodes_per_cell must be positive")
    unknown_types = sorted(set(case_types) - set(DISPATCH_CHARACTERIZATION_CASE_TYPES))
    if unknown_types:
        known = ", ".join(DISPATCH_CHARACTERIZATION_CASE_TYPES)
        raise ValueError(f"Unknown dispatch characterization case types {unknown_types}. Known types: {known}")

    all_specs = _external_stress_specs(n_slots_values, slot_gap_values)
    selected_specs = all_specs
    if stress_cases:
        known_cases = {stress_case for _, stress_case, _, _ in all_specs}
        unknown_cases = sorted(set(stress_cases) - known_cases)
        if unknown_cases:
            raise ValueError(f"Unknown stress cases {unknown_cases}. Known cases: {sorted(known_cases)}")
        selected_specs = [spec for spec in all_specs if spec[1] in set(stress_cases)]

    cases: list[DispatchCharacterizationCase] = []
    for stress_index, stress_case, n_slots, slot_gap in selected_specs:
        if not 0 <= critical_slot < n_slots:
            raise ValueError(f"critical_slot={critical_slot} outside n_slots={n_slots}")
        for case_type in case_types:
            condition = _condition_for_case_type(case_type)
            for seed in range(seeds):
                row_seed = _external_dispatch_row_seed(
                    base_seed=base_seed,
                    stress_index=stress_index,
                    seed=seed,
                    critical_slot=critical_slot,
                )
                rng = random.Random(row_seed)
                for episode in range(episodes_per_cell):
                    bits = tuple(episode_bits(rng, n_slots))
                    user_prompt = _user_prompt_for_case_type(
                        case_type,
                        list(bits),
                        critical_slot,
                        n_slots,
                        slot_gap,
                        variants_per_slot,
                    )
                    case_id = "/".join(
                        [
                            "dispatch_characterization",
                            stress_case,
                            case_type,
                            f"slot{critical_slot}",
                            f"seed{seed}",
                            f"episode{episode}",
                        ]
                    )
                    cases.append(
                        DispatchCharacterizationCase(
                            case_id=case_id,
                            suite="dispatch_characterization",
                            stress_case=stress_case,
                            case_type=case_type,
                            condition=condition,
                            seed=row_seed,
                            episode=episode,
                            critical_slot=critical_slot,
                            n_slots=n_slots,
                            slot_gap=slot_gap,
                            variants_per_slot=variants_per_slot,
                            bits=bits,
                            user_prompt=user_prompt,
                        )
                    )
    return cases


def evaluate_dispatch_characterization_cases(
    cases: list[DispatchCharacterizationCase],
    *,
    model: str,
    provider_name: str,
    provider_call: DispatchProviderCall,
    include_prompts: bool = True,
    include_raw: bool = False,
    sleep_seconds: float = 0.0,
) -> list[dict[str, Any]]:
    """Run diagnostic cases and return phase-scored rows."""

    rows: list[dict[str, Any]] = []
    for case in cases:
        first = provider_call(messages(case.user_prompt), case, "first")
        first_parsed = parse_prompt_json_action(first.text, case.n_slots, case.variants_per_slot)
        row = _base_row(case, model, provider_name)
        row.update(_score_action("first", first_parsed, case))
        row.update(
            {
                "first_text": first.text,
                "first_parsed": _compact_parsed(first_parsed),
                "first_usage": first.usage,
            }
        )
        if include_prompts:
            row["user_prompt"] = case.user_prompt
        if include_raw:
            row["first_raw"] = first.raw

        if case.case_type in DISPATCH_CHARACTERIZATION_VARIANTS:
            failed = provider_call(
                _dispatch_repair_messages(case, first.text, failed=True),
                case,
                "repair_failed",
            )
            failed_parsed = parse_prompt_json_action(failed.text, case.n_slots, case.variants_per_slot)
            success = provider_call(
                _dispatch_repair_messages(case, first.text, failed=False),
                case,
                "repair_success",
            )
            success_parsed = parse_prompt_json_action(success.text, case.n_slots, case.variants_per_slot)
            row.update(_score_action("repair_failed", failed_parsed, case))
            row.update(_score_action("repair_success", success_parsed, case))
            row.update(
                {
                    "repair_failed_text": failed.text,
                    "repair_failed_parsed": _compact_parsed(failed_parsed),
                    "repair_failed_usage": failed.usage,
                    "repair_success_text": success.text,
                    "repair_success_parsed": _compact_parsed(success_parsed),
                    "repair_success_usage": success.usage,
                }
            )
            if include_raw:
                row["repair_failed_raw"] = failed.raw
                row["repair_success_raw"] = success.raw
        rows.append(row)
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    return rows


def summarize_dispatch_characterization_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize diagnostic rows into per-axis failure localization."""

    groups: dict[str, dict[str, Any]] = {}
    grouped = _group_rows(rows)
    for key, group_rows in sorted(grouped.items()):
        case_type = str(group_rows[0]["case_type"])
        groups[key] = _summarize_dispatch_group(group_rows, case_type)

    cells: dict[str, dict[str, Any]] = {}
    for row in rows:
        cell_key = _cell_key(row)
        cell = cells.setdefault(
            cell_key,
            {
                "suite": row["suite"],
                "stress_case": row["stress_case"],
                "provider": row["provider"],
                "model": row["model"],
                "critical_slot": row["critical_slot"],
                "n_slots": row["n_slots"],
                "slot_gap": row["slot_gap"],
                "case_gates": {},
                "variant_signatures": {},
            },
        )
        group_key = _group_key(row)
        group = groups[group_key]
        case_type = row["case_type"]
        cell["case_gates"][case_type] = group["gate"]["pass"]
        cell["variant_signatures"][case_type] = group["failure_signature"]

    for cell in cells.values():
        gates = cell["case_gates"]
        controls = [gates.get(control, False) for control in DISPATCH_CHARACTERIZATION_CONTROLS]
        cell["complete"] = set(DISPATCH_CHARACTERIZATION_CASE_TYPES).issubset(gates)
        cell["controls_pass"] = cell["complete"] and all(controls)
        cell["original_pass"] = bool(gates.get("dispatch_original"))
        cell["wording_neutral_pass"] = bool(gates.get("wording_neutral"))
        cell["copy_assisted_pass"] = bool(gates.get("copy_assisted"))
        cell["repair_hinted_pass"] = bool(gates.get("repair_hinted"))
        cell["original_failure_signature"] = cell["variant_signatures"].get("dispatch_original", [])
        cell["diagnosis"] = _diagnose_cell(cell)
        cell["localized"] = cell["controls_pass"] and bool(cell["diagnosis"])

    cell_items = list(cells.values())
    complete = bool(cell_items) and all(cell["complete"] for cell in cell_items)
    controls_pass = complete and all(cell["controls_pass"] for cell in cell_items)
    original_failed_cells = [cell for cell in cell_items if cell["controls_pass"] and not cell["original_pass"]]
    not_reproduced_cells = [cell for cell in cell_items if cell["controls_pass"] and cell["original_pass"]]
    localized_cells = [cell for cell in original_failed_cells if cell["localized"]]
    unresolved_cells = [cell for cell in original_failed_cells if not cell["localized"]]
    reproduced = bool(original_failed_cells)
    all_localized = bool(original_failed_cells) and not unresolved_cells
    if not controls_pass:
        outcome = "inconclusive"
    elif all_localized and not not_reproduced_cells:
        outcome = "localized"
    elif all_localized:
        outcome = "partially_reproduced_localized"
    elif reproduced:
        outcome = "partially_localized"
    else:
        outcome = "failure_not_reproduced"

    return {
        "kind": "long-horizon dispatch failure characterization",
        "n_rows": len(rows),
        "groups": groups,
        "cells": dict(sorted(cells.items())),
        "decision": {
            "complete": complete,
            "controls_pass": controls_pass,
            "original_failure_reproduced": reproduced,
            "localized_cells": len(localized_cells),
            "not_reproduced_cells": len(not_reproduced_cells),
            "unresolved_cells": len(unresolved_cells),
            "all_reproduced_cells_localized": all_localized,
        },
        "outcome": outcome,
    }


def manifest_from_cases(
    *,
    cases: list[DispatchCharacterizationCase],
    provider: str,
    models: list[str],
    base_seed: int,
    max_output_tokens: int,
) -> dict[str, Any]:
    return {
        "suite": "dispatch_characterization",
        "provider": provider,
        "models": models,
        "base_seed": base_seed,
        "n_cases": len(cases),
        "n_requests": total_request_count(cases) * len(models),
        "max_output_tokens": max_output_tokens,
        "case_types": sorted({case.case_type for case in cases}),
        "stress_cases": sorted({case.stress_case for case in cases}),
        "critical_slots": sorted({case.critical_slot for case in cases}),
        "n_slots_values": sorted({case.n_slots for case in cases}),
        "slot_gap_values": sorted({case.slot_gap for case in cases}),
        "expected_max_output_tokens": total_request_count(cases) * len(models) * max_output_tokens,
    }


def manifest_from_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Reconstruct a compact manifest when replaying saved diagnostic rows."""

    return {
        "suite": "dispatch_characterization",
        "provider": _first_row_value(rows, "provider"),
        "models": sorted({str(row["model"]) for row in rows}),
        "base_seed": min((int(row["seed"]) for row in rows), default=None),
        "n_cases": len(rows),
        "n_requests": sum(3 if row["case_type"] in DISPATCH_CHARACTERIZATION_VARIANTS else 1 for row in rows),
        "max_output_tokens": None,
        "case_types": sorted({str(row["case_type"]) for row in rows}),
        "stress_cases": sorted({str(row["stress_case"]) for row in rows}),
        "critical_slots": sorted({int(row["critical_slot"]) for row in rows}),
        "n_slots_values": sorted({int(row["n_slots"]) for row in rows}),
        "slot_gap_values": sorted({int(row["slot_gap"]) for row in rows}),
    }


def total_request_count(cases: list[DispatchCharacterizationCase]) -> int:
    return sum(case.request_count for case in cases)


def summarize_dispatch_robustness(summary: dict[str, Any]) -> dict[str, Any]:
    """Classify a multi-cell dispatch characterization as a robustness result."""

    cells = list(summary["cells"].values())
    complete_cells = [cell for cell in cells if cell["complete"]]
    controls_passing_cells = [cell for cell in complete_cells if cell["controls_pass"]]
    original_failure_cells = [cell for cell in controls_passing_cells if not cell["original_pass"]]
    localized_failure_cells = [cell for cell in original_failure_cells if cell["localized"]]
    unresolved_failure_cells = [cell for cell in original_failure_cells if not cell["localized"]]
    not_reproduced_cells = [cell for cell in controls_passing_cells if cell["original_pass"]]
    failure_rate = (
        len(original_failure_cells) / len(controls_passing_cells)
        if controls_passing_cells
        else None
    )
    if len(controls_passing_cells) != len(cells):
        outcome = "inconclusive"
    elif not original_failure_cells:
        outcome = "failure_not_reproduced"
    elif unresolved_failure_cells:
        outcome = "reproduced_unresolved"
    elif failure_rate == 1.0:
        outcome = "stable_reproduced_localized"
    elif failure_rate is not None and failure_rate >= 0.5:
        outcome = "broad_reproduced_localized"
    else:
        outcome = "sparse_reproduced_localized"

    by_stress: dict[str, dict[str, Any]] = {}
    for cell in cells:
        stress = str(cell["stress_case"])
        bucket = by_stress.setdefault(
            stress,
            {
                "cells": 0,
                "controls_passing_cells": 0,
                "original_failure_cells": 0,
                "localized_failure_cells": 0,
            },
        )
        bucket["cells"] += 1
        if cell["controls_pass"]:
            bucket["controls_passing_cells"] += 1
        if cell["controls_pass"] and not cell["original_pass"]:
            bucket["original_failure_cells"] += 1
        if cell["localized"]:
            bucket["localized_failure_cells"] += 1

    return {
        "kind": "dispatch characterization robustness",
        "outcome": outcome,
        "total_cells": len(cells),
        "complete_cells": len(complete_cells),
        "controls_passing_cells": len(controls_passing_cells),
        "original_failure_cells": len(original_failure_cells),
        "localized_failure_cells": len(localized_failure_cells),
        "unresolved_failure_cells": len(unresolved_failure_cells),
        "not_reproduced_cells": len(not_reproduced_cells),
        "original_failure_cell_rate": failure_rate,
        "by_stress": dict(sorted(by_stress.items())),
    }


def render_dispatch_characterization_markdown(
    payload: dict[str, Any],
    *,
    title: str = "OpenAI Dispatch Failure Characterization",
    report_date: str | None = None,
) -> str:
    manifest = payload.get("manifest", {})
    summary = payload["summary"]
    robustness = payload.get("robustness")
    report_date = report_date or date.today().isoformat()
    lines = [
        f"# {title}",
        "",
        f"Date: {report_date}",
        "",
        "## Outcome",
        "",
        f"Outcome: `{summary['outcome']}`.",
        f"Rows: {summary['n_rows']}; planned requests: {manifest.get('n_requests', 'unknown')}.",
        f"Controls pass: {'yes' if summary['decision']['controls_pass'] else 'no'}.",
        (
            "Original dispatch failure reproduced: "
            f"{'yes' if summary['decision']['original_failure_reproduced'] else 'no'}."
        ),
        (
            "Localized cells: "
            f"{summary['decision']['localized_cells']}; unresolved cells: "
            f"{summary['decision']['unresolved_cells']}."
        ),
        f"Original dispatch failure not reproduced cells: {summary['decision']['not_reproduced_cells']}.",
    ]
    if robustness:
        rate = robustness["original_failure_cell_rate"]
        rate_text = "n/a" if rate is None else f"{rate:.3f}"
        failure_cells = [
            f"{cell['stress_case']} slot {cell['critical_slot']}"
            for cell in summary["cells"].values()
            if cell["controls_pass"] and not cell["original_pass"]
        ]
        lines.extend(
            [
                f"Robustness outcome: `{robustness['outcome']}`.",
                (
                    "Original-failure cells: "
                    f"{robustness['original_failure_cells']}/{robustness['controls_passing_cells']} "
                    f"(rate {rate_text})."
                ),
                f"Gate: reproduced original-failure cells: {', '.join(failure_cells) or 'none'}.",
            ]
        )
    lines.extend(
        [
            "",
            "## Diagnostic Matrix",
            "",
            "| Stress | Critical slot | Original | Neutral wording | Copy-assisted | Repair-hinted | Diagnosis |",
            "|---|---:|---|---|---|---|---|",
        ]
    )
    for cell in sorted(
        summary["cells"].values(),
        key=lambda item: (item["stress_case"], item["critical_slot"]),
    ):
        lines.append(
            "| {stress} | {slot} | {original} | {wording} | {copy} | {repair} | {diagnosis} |".format(
                stress=cell["stress_case"],
                slot=cell["critical_slot"],
                original=_pass_label(cell["original_pass"]),
                wording=_pass_label(cell["wording_neutral_pass"]),
                copy=_pass_label(cell["copy_assisted_pass"]),
                repair=_pass_label(cell["repair_hinted_pass"]),
                diagnosis=", ".join(cell["diagnosis"]) or "none",
            )
        )

    lines.extend(
        [
            "",
            "## Phase Metrics",
            "",
            "| Stress | Critical slot | Variant | First action | Repair-after-error | Success no-op | Failed gates |",
            "|---|---:|---|---:|---:|---:|---|",
        ]
    )
    for key, group in sorted(summary["groups"].items()):
        parts = key.split("/")
        stress = parts[1]
        case_type = parts[4]
        critical_slot = parts[-1].removeprefix("slot")
        if case_type not in DISPATCH_CHARACTERIZATION_VARIANTS:
            continue
        metrics = group["metrics"]
        lines.append(
            "| {stress} | {slot} | {case_type} | {first:.3f} | {repair:.3f} | {noop:.3f} | {failed} |".format(
                stress=stress,
                slot=critical_slot,
                case_type=case_type,
                first=_metric_or_zero(metrics.get("first_action_accuracy")),
                repair=_metric_or_zero(metrics.get("repair_failed_action_accuracy")),
                noop=_metric_or_zero(metrics.get("repair_success_noop_field_accuracy")),
                failed=", ".join(group["failure_signature"]) or "none",
            )
        )

    lines.extend(
        [
            "",
            "## Regime Audit",
            "",
            "- Old regime: the API external-stress benchmark exposed two OpenAI `dispatch` cells with passing controls and failed bottleneck gates.",
            "- Transition: this run keeps the same parser, provider adapter, seeds, stress cells, and repair protocol, but splits the failed dispatch surface into original, neutral-wording, value-copy-assisted, and repair-hinted variants.",
            "- Transported evidence: exact JSON action parser, no-op controls, short-copy controls, failed-repair and success-no-op phases, and the previously failed stress settings.",
            "- Rejected alternatives: the diagnostic does not treat black-box behavior as hidden-state localization and does not add broader provider claims.",
            "- Residual finding: the diagnosis column identifies whether the reproduced failure is relieved by wording, value visibility, or repair hints.",
            "- Allowed claim: black-box behavioral robustness/localization for the tested OpenAI model, slots, and stress cells only.",
            "",
            "## Local Artifacts",
            "",
        ]
    )
    if payload.get("rows_jsonl"):
        lines.append(f"- Rows: `{payload['rows_jsonl']}`")
    return "\n".join(lines) + "\n"


def write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def case_to_dict(case: DispatchCharacterizationCase) -> dict[str, Any]:
    data = asdict(case)
    data["bits"] = list(case.bits)
    data["expected_value"] = case.expected_value
    data["request_count"] = case.request_count
    return data


def _external_stress_specs(
    n_slots_values: list[int],
    slot_gap_values: list[int],
) -> list[tuple[int, str, int, int]]:
    return [
        (index, f"{n_slots}_slot_gap{slot_gap}".replace("_slot", "slot"), n_slots, slot_gap)
        for index, (n_slots, slot_gap) in enumerate(
            (n_slots, slot_gap) for n_slots in n_slots_values for slot_gap in slot_gap_values
        )
    ]


def _external_dispatch_row_seed(
    *,
    base_seed: int,
    stress_index: int,
    seed: int,
    critical_slot: int,
) -> int:
    # Matches the prior external-stress dispatch/prompt_json_bottleneck seed block.
    dispatch_family_index = 4
    bottleneck_condition_index = 3
    return (
        base_seed
        + seed
        + 1000 * critical_slot
        + 100_000 * dispatch_family_index
        + 1_000_000 * stress_index
        + 10_000_000 * bottleneck_condition_index
    )


def _condition_for_case_type(case_type: str) -> str:
    if case_type == "format_control":
        return "prompt_json_format_control"
    if case_type == "visible_noop_control":
        return "prompt_json_visible_control"
    if case_type == "short_copy_control":
        return "prompt_json_short_horizon_control"
    if case_type in DISPATCH_CHARACTERIZATION_VARIANTS:
        return "prompt_json_bottleneck"
    raise ValueError(f"Unknown case type {case_type!r}")


def _user_prompt_for_case_type(
    case_type: str,
    bits: list[int],
    critical_slot: int,
    n_slots: int,
    slot_gap: int,
    variants_per_slot: int,
) -> str:
    if case_type == "format_control":
        return format_user_prompt()
    if case_type == "visible_noop_control":
        return visible_user_prompt(bits, critical_slot, variants_per_slot)
    if case_type == "short_copy_control":
        return short_user_prompt(bits, critical_slot, variants_per_slot)
    if case_type in {"dispatch_original", "repair_hinted"}:
        return prompt_family_user_prompt("dispatch", bits, critical_slot, n_slots, slot_gap, variants_per_slot)
    if case_type == "wording_neutral":
        return prompt_family_user_prompt("retrieval", bits, critical_slot, n_slots, slot_gap, variants_per_slot)
    if case_type == "copy_assisted":
        phrase = slot_phrase(critical_slot, variants_per_slot)
        value = bits[critical_slot]
        base = prompt_family_user_prompt("dispatch", bits, critical_slot, n_slots, slot_gap, variants_per_slot)
        return "\n".join(
            [
                base,
                f"Dispatch target record repeated for value-copy audit: {phrase} = {value}.",
                f"Use this exact pair in the dispatcher JSON: slot {phrase}, value {value}.",
            ]
        )
    raise ValueError(f"Unknown case type {case_type!r}")


def _dispatch_repair_messages(
    case: DispatchCharacterizationCase,
    assistant_text: str,
    *,
    failed: bool,
) -> list[dict[str, str]]:
    if case.case_type == "repair_hinted" and failed:
        phrase = slot_phrase(case.critical_slot, case.variants_per_slot)
        repair_text = (
            "Tool result: ERROR. The previous action failed before recording any value. "
            f"The original dispatch target was {phrase}, and the recorded value was {case.expected_value}. "
            "Repair by emitting the same read_slot JSON action again."
        )
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": case.user_prompt},
            {"role": "assistant", "content": assistant_text},
            {"role": "user", "content": repair_text},
        ]
    return repair_messages(case.user_prompt, assistant_text, failed=failed)


def _base_row(
    case: DispatchCharacterizationCase,
    model: str,
    provider_name: str,
) -> dict[str, Any]:
    return {
        "row_kind": "api_dispatch_characterization",
        "provider": provider_name,
        "model": model,
        "case_id": case.case_id,
        "suite": case.suite,
        "stress_case": case.stress_case,
        "case_type": case.case_type,
        "condition": case.condition,
        "seed": case.seed,
        "episode": case.episode,
        "critical_slot": case.critical_slot,
        "n_slots": case.n_slots,
        "slot_gap": case.slot_gap,
        "variants_per_slot": case.variants_per_slot,
        "expected_value": case.expected_value,
    }


def _score_action(
    prefix: str,
    parsed: dict[str, Any],
    case: DispatchCharacterizationCase,
) -> dict[str, float]:
    schema = float(parsed["valid"])
    call = float(parsed["valid"] and parsed["opcode"] == "call")
    noop = float(parsed["valid"] and parsed["opcode"] == "noop")
    slot = float(parsed["valid"] and parsed["slot"] == case.critical_slot)
    value = float(parsed["valid"] and parsed["value"] == case.expected_value)
    action = float(call and slot and value)
    return {
        f"{prefix}_schema_validity": schema,
        f"{prefix}_call_field_accuracy": call,
        f"{prefix}_noop_field_accuracy": noop,
        f"{prefix}_parsed_slot_accuracy": slot,
        f"{prefix}_parsed_value_accuracy": value,
        f"{prefix}_action_accuracy": action,
    }


def _compact_parsed(parsed: dict[str, Any]) -> dict[str, Any]:
    return {
        "opcode": parsed["opcode"],
        "slot": parsed["slot"],
        "variant_index": parsed["variant_index"],
        "value": parsed["value"],
        "valid": parsed["valid"],
        "executable": parsed["executable"],
        "reason": parsed["reason"],
        "json_text": parsed["json_text"],
    }


def _group_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(_group_key(row), []).append(row)
    return grouped


def _group_key(row: dict[str, Any]) -> str:
    return "/".join(
        [
            str(row["suite"]),
            str(row["stress_case"]),
            str(row["provider"]),
            str(row["model"]),
            str(row["case_type"]),
            f"{row['n_slots']}slot",
            f"gap{row['slot_gap']}",
            f"slot{row['critical_slot']}",
        ]
    )


def _cell_key(row: dict[str, Any]) -> str:
    return "/".join(
        [
            str(row["suite"]),
            str(row["stress_case"]),
            str(row["provider"]),
            str(row["model"]),
            f"{row['n_slots']}slot",
            f"gap{row['slot_gap']}",
            f"slot{row['critical_slot']}",
        ]
    )


def _summarize_dispatch_group(rows: list[dict[str, Any]], case_type: str) -> dict[str, Any]:
    metrics = {
        "first_schema_validity": _row_mean(rows, "first_schema_validity"),
        "first_action_accuracy": _row_mean(rows, "first_action_accuracy"),
        "first_noop_field_accuracy": _row_mean(rows, "first_noop_field_accuracy"),
        "first_parsed_slot_accuracy": _row_mean(rows, "first_parsed_slot_accuracy"),
        "first_parsed_value_accuracy": _row_mean(rows, "first_parsed_value_accuracy"),
        "repair_failed_schema_validity": _row_mean(rows, "repair_failed_schema_validity"),
        "repair_failed_action_accuracy": _row_mean(rows, "repair_failed_action_accuracy"),
        "repair_failed_parsed_slot_accuracy": _row_mean(rows, "repair_failed_parsed_slot_accuracy"),
        "repair_failed_parsed_value_accuracy": _row_mean(rows, "repair_failed_parsed_value_accuracy"),
        "repair_success_schema_validity": _row_mean(rows, "repair_success_schema_validity"),
        "repair_success_noop_field_accuracy": _row_mean(rows, "repair_success_noop_field_accuracy"),
    }
    if case_type in {"format_control", "visible_noop_control"}:
        gate = {
            "first_schema_valid_ge_0_95": _mean_ge(
                metrics["first_schema_validity"],
                PROMPT_JSON_CONTROL_SCHEMA_THRESHOLD,
            ),
            "first_noop_field_acc_ge_0_85": _mean_ge(
                metrics["first_noop_field_accuracy"],
                PROMPT_JSON_ACTION_THRESHOLD,
            ),
        }
    elif case_type == "short_copy_control":
        gate = {
            "first_schema_valid_ge_0_95": _mean_ge(
                metrics["first_schema_validity"],
                PROMPT_JSON_CONTROL_SCHEMA_THRESHOLD,
            ),
            "first_action_acc_ge_0_85": _mean_ge(metrics["first_action_accuracy"], PROMPT_JSON_ACTION_THRESHOLD),
        }
    elif case_type in DISPATCH_CHARACTERIZATION_VARIANTS:
        gate = {
            "first_schema_valid_ge_0_95": _mean_ge(
                metrics["first_schema_validity"],
                PROMPT_JSON_CONTROL_SCHEMA_THRESHOLD,
            ),
            "first_action_acc_ge_0_85": _mean_ge(metrics["first_action_accuracy"], PROMPT_JSON_ACTION_THRESHOLD),
            "repair_failed_schema_valid_ge_0_95": _mean_ge(
                metrics["repair_failed_schema_validity"],
                PROMPT_JSON_CONTROL_SCHEMA_THRESHOLD,
            ),
            "repair_failed_action_acc_ge_0_85": _mean_ge(
                metrics["repair_failed_action_accuracy"],
                PROMPT_JSON_ACTION_THRESHOLD,
            ),
            "repair_success_schema_valid_ge_0_95": _mean_ge(
                metrics["repair_success_schema_validity"],
                PROMPT_JSON_CONTROL_SCHEMA_THRESHOLD,
            ),
            "repair_success_noop_acc_ge_0_85": _mean_ge(
                metrics["repair_success_noop_field_accuracy"],
                PROMPT_JSON_ACTION_THRESHOLD,
            ),
        }
    else:
        raise ValueError(f"Unknown case type {case_type!r}")
    gate["pass"] = all(gate.values())
    return {
        "case_type": case_type,
        "n_rows": len(rows),
        "metrics": metrics,
        "gate": gate,
        "failure_signature": [name for name, passed in gate.items() if name != "pass" and not passed],
    }


def _diagnose_cell(cell: dict[str, Any]) -> list[str]:
    if not cell["controls_pass"] or cell["original_pass"]:
        return []
    diagnoses: list[str] = []
    signature = set(cell["original_failure_signature"])
    if cell["wording_neutral_pass"]:
        diagnoses.append("dispatch wording/surface")
    if cell["copy_assisted_pass"] and {
        "first_action_acc_ge_0_85",
        "repair_failed_action_acc_ge_0_85",
    }.intersection(signature):
        diagnoses.append("value-copy pressure")
    if cell["repair_hinted_pass"] and "repair_failed_action_acc_ge_0_85" in signature:
        diagnoses.append("repair-memory pressure")
    return diagnoses


def _row_mean(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return sum(values) / len(values) if values else None


def _mean_ge(value: float | None, threshold: float) -> bool:
    return value is not None and value >= threshold


def _metric_or_zero(value: float | None) -> float:
    return 0.0 if value is None else float(value)


def _pass_label(value: bool) -> str:
    return "pass" if value else "fail"


def _first_row_value(rows: list[dict[str, Any]], key: str) -> Any:
    return rows[0].get(key) if rows else None


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        choices=(
            "fixture",
            "fixture_wrong_bottleneck",
            "openai-responses",
            "openai-chat",
            "openai-compatible",
            "anthropic",
            "gemini",
        ),
        default="fixture",
    )
    parser.add_argument("--models", default="fixture-perfect")
    parser.add_argument("--api-key-env")
    parser.add_argument("--base-url")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-output-tokens", type=int, default=64)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--no-temperature", action="store_true")
    parser.add_argument("--case-types", default=",".join(DISPATCH_CHARACTERIZATION_CASE_TYPES))
    parser.add_argument("--stress-cases", default="")
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--episodes-per-cell", type=int, default=1)
    parser.add_argument("--critical-slot", type=int, default=0)
    parser.add_argument("--n-slots", default="4,8")
    parser.add_argument("--slot-gap", default="8,16")
    parser.add_argument("--variants-per-slot", type=int, default=3)
    parser.add_argument("--base-seed", type=int, default=20261050)
    parser.add_argument("--max-requests", type=int, default=100)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument(
        "--out",
        default="artifacts/long_horizon_bottleneck/api_dispatch_characterization_summary.json",
    )
    parser.add_argument(
        "--jsonl",
        default="artifacts/long_horizon_bottleneck/api_dispatch_characterization_rows.jsonl",
    )
    parser.add_argument("--report-md")
    parser.add_argument("--replay-jsonl", help="Score an existing JSONL row file instead of calling a provider.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--omit-prompts", action="store_true")
    parser.add_argument("--include-raw", action="store_true")
    args = parser.parse_args(argv)

    models = parse_csv_arg(args.models)
    case_types = parse_csv_arg(args.case_types)
    stress_cases = parse_csv_arg(args.stress_cases) if args.stress_cases else []
    n_slots_values = parse_int_csv_arg(args.n_slots)
    slot_gap_values = parse_int_csv_arg(args.slot_gap)
    temperature = None if args.no_temperature else args.temperature

    if args.replay_jsonl:
        rows = read_jsonl(Path(args.replay_jsonl))
        summary = summarize_dispatch_characterization_rows(rows)
        manifest = manifest_from_rows(rows)
        payload = {
            "kind": "long-horizon dispatch failure characterization replay",
            "replay_jsonl": args.replay_jsonl,
            "manifest": manifest,
            "summary": summary,
            "rows_jsonl": args.replay_jsonl,
        }
        write_summary(Path(args.out), payload)
        if args.report_md:
            write_markdown(Path(args.report_md), render_dispatch_characterization_markdown(payload))
        print(json.dumps({"outcome": summary["outcome"], "n_rows": summary["n_rows"], "out": args.out}, indent=2))
        return

    cases = build_dispatch_characterization_cases(
        stress_cases=stress_cases,
        case_types=case_types,
        seeds=args.seeds,
        episodes_per_cell=args.episodes_per_cell,
        critical_slot=args.critical_slot,
        n_slots_values=n_slots_values,
        slot_gap_values=slot_gap_values,
        variants_per_slot=args.variants_per_slot,
        base_seed=args.base_seed,
    )
    manifest = manifest_from_cases(
        cases=cases,
        provider=args.provider,
        models=models,
        base_seed=args.base_seed,
        max_output_tokens=args.max_output_tokens,
    )
    request_count = total_request_count(cases) * len(models)
    if request_count > args.max_requests:
        raise SystemExit(f"Request guard failed: {request_count} requests exceeds --max-requests {args.max_requests}.")
    if args.dry_run:
        print(
            json.dumps(
                {"kind": "long-horizon dispatch failure characterization dry run", "manifest": manifest},
                indent=2,
            )
        )
        return

    all_rows = []
    for model in models:
        provider_call = cast(
            DispatchProviderCall,
            make_provider_call(
                provider=args.provider,
                model=model,
                api_key_env=args.api_key_env,
                base_url=args.base_url,
                timeout_seconds=args.timeout_seconds,
                max_output_tokens=args.max_output_tokens,
                temperature=temperature,
            ),
        )
        rows = evaluate_dispatch_characterization_cases(
            cases,
            model=model,
            provider_name=args.provider,
            provider_call=provider_call,
            include_prompts=not args.omit_prompts,
            include_raw=args.include_raw,
            sleep_seconds=args.sleep_seconds,
        )
        all_rows.extend(rows)

    summary = summarize_dispatch_characterization_rows(all_rows)
    write_jsonl(Path(args.jsonl), all_rows)
    payload = {
        "kind": "long-horizon dispatch failure characterization",
        "manifest": manifest,
        "summary": summary,
        "rows_jsonl": args.jsonl,
    }
    write_summary(Path(args.out), payload)
    if args.report_md:
        write_markdown(Path(args.report_md), render_dispatch_characterization_markdown(payload))
    print(
        json.dumps(
            {
                "outcome": summary["outcome"],
                "n_rows": summary["n_rows"],
                "rows_jsonl": args.jsonl,
                "out": args.out,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
