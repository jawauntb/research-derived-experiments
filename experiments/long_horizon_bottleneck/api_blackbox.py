"""Black-box API benchmark helpers for the long-horizon moved bottleneck."""

from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from experiments.long_horizon_bottleneck.core import (
    PROMPT_JSON_ACTION_THRESHOLD,
    PROMPT_JSON_CONTROL_SCHEMA_THRESHOLD,
    parse_csv,
    parse_prompt_json_action,
)
from experiments.long_horizon_bottleneck.prompt_json_tasks import (
    API_PROMPT_FAMILIES,
    SYSTEM_PROMPT,
    episode_bits,
    format_user_prompt,
    messages,
    prompt_family_user_prompt,
    repair_messages,
    short_user_prompt,
    visible_user_prompt,
)

API_BLACKBOX_CONDITIONS = (
    "prompt_json_format_control",
    "prompt_json_visible_control",
    "prompt_json_short_horizon_control",
    "prompt_json_bottleneck",
)


@dataclass(frozen=True)
class ApiBenchmarkCase:
    case_id: str
    suite: str
    stress_case: str
    condition: str
    prompt_family: str
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
        return 3 if self.condition == "prompt_json_bottleneck" else 1


@dataclass(frozen=True)
class ProviderResult:
    text: str
    usage: dict[str, Any]
    raw: dict[str, Any] | None = None


ProviderCall = Callable[[list[dict[str, str]], ApiBenchmarkCase, str], ProviderResult]


def build_api_benchmark_cases(
    *,
    suite: str,
    prompt_families: list[str],
    conditions: list[str],
    seeds: int,
    episodes_per_cell: int,
    critical_slots: list[int],
    n_slots_values: list[int],
    slot_gap_values: list[int],
    variants_per_slot: int,
    base_seed: int,
) -> list[ApiBenchmarkCase]:
    """Build deterministic black-box benchmark cases."""

    if suite not in {"prompt_family", "external_stress"}:
        raise ValueError("suite must be 'prompt_family' or 'external_stress'")
    if seeds <= 0:
        raise ValueError("seeds must be positive")
    if episodes_per_cell <= 0:
        raise ValueError("episodes_per_cell must be positive")
    if variants_per_slot <= 0:
        raise ValueError("variants_per_slot must be positive")

    unknown_families = sorted(set(prompt_families) - set(API_PROMPT_FAMILIES))
    if unknown_families:
        known = ", ".join(API_PROMPT_FAMILIES)
        raise ValueError(f"Unknown prompt families {unknown_families}. Known families: {known}")
    unknown_conditions = sorted(set(conditions) - set(API_BLACKBOX_CONDITIONS))
    if unknown_conditions:
        known = ", ".join(API_BLACKBOX_CONDITIONS)
        raise ValueError(f"Unknown conditions {unknown_conditions}. Known conditions: {known}")

    stress_specs = _stress_specs(suite, n_slots_values, slot_gap_values)
    cases: list[ApiBenchmarkCase] = []
    for stress_index, (stress_case, n_slots, slot_gap) in enumerate(stress_specs):
        for family_index, prompt_family in enumerate(prompt_families):
            for condition_index, condition in enumerate(conditions):
                for critical_slot in critical_slots:
                    if not 0 <= critical_slot < n_slots:
                        raise ValueError(f"critical_slot={critical_slot} outside n_slots={n_slots}")
                    for seed in range(seeds):
                        row_seed = (
                            base_seed
                            + seed
                            + 1000 * critical_slot
                            + 100_000 * family_index
                            + 1_000_000 * stress_index
                            + 10_000_000 * condition_index
                        )
                        rng = random.Random(row_seed)
                        for episode in range(episodes_per_cell):
                            bits = tuple(episode_bits(rng, n_slots))
                            user_prompt = _user_prompt_for_condition(
                                condition,
                                prompt_family,
                                list(bits),
                                critical_slot,
                                n_slots,
                                slot_gap,
                                variants_per_slot,
                            )
                            case_id = "/".join(
                                [
                                    suite,
                                    stress_case,
                                    prompt_family,
                                    condition,
                                    f"slot{critical_slot}",
                                    f"seed{seed}",
                                    f"episode{episode}",
                                ]
                            )
                            cases.append(
                                ApiBenchmarkCase(
                                    case_id=case_id,
                                    suite=suite,
                                    stress_case=stress_case,
                                    condition=condition,
                                    prompt_family=prompt_family,
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


def evaluate_api_cases(
    cases: list[ApiBenchmarkCase],
    *,
    model: str,
    provider_name: str,
    provider_call: ProviderCall,
    include_prompts: bool = True,
    include_raw: bool = False,
    sleep_seconds: float = 0.0,
) -> list[dict[str, Any]]:
    """Run cases through a provider and return scored JSON-serializable rows."""

    rows: list[dict[str, Any]] = []
    for case in cases:
        first = provider_call(messages(case.user_prompt), case, "first")
        first_parsed = parse_prompt_json_action(first.text, case.n_slots, case.variants_per_slot)
        row = _score_first_action(case, first_parsed)
        row.update(
            {
                "row_kind": "api_blackbox",
                "provider": provider_name,
                "model": model,
                "case_id": case.case_id,
                "suite": case.suite,
                "stress_case": case.stress_case,
                "condition": case.condition,
                "prompt_family": case.prompt_family,
                "seed": case.seed,
                "episode": case.episode,
                "critical_slot": case.critical_slot,
                "n_slots": case.n_slots,
                "slot_gap": case.slot_gap,
                "variants_per_slot": case.variants_per_slot,
                "expected_value": case.expected_value,
                "first_text": first.text,
                "first_parsed": _compact_parsed(first_parsed),
                "first_usage": first.usage,
            }
        )
        if include_prompts:
            row["user_prompt"] = case.user_prompt
        if include_raw:
            row["first_raw"] = first.raw

        if case.condition == "prompt_json_bottleneck":
            failed = provider_call(
                repair_messages(case.user_prompt, first.text, failed=True),
                case,
                "repair_failed",
            )
            failed_parsed = parse_prompt_json_action(failed.text, case.n_slots, case.variants_per_slot)
            success = provider_call(
                repair_messages(case.user_prompt, first.text, failed=False),
                case,
                "repair_success",
            )
            success_parsed = parse_prompt_json_action(success.text, case.n_slots, case.variants_per_slot)
            row.update(_score_repair_actions(case, failed_parsed, success_parsed))
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


def summarize_api_blackbox_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize black-box API rows into benchmark gates."""

    groups: dict[str, dict[str, Any]] = {}
    cells: dict[str, dict[str, Any]] = {}
    grouped = _group_rows(rows)
    for key, group_rows in sorted(grouped.items()):
        condition = str(group_rows[0]["condition"])
        group = _summarize_api_group(group_rows, condition)
        groups[key] = group

        cell_key = _cell_key(group_rows[0])
        cell = cells.setdefault(
            cell_key,
            {
                "suite": group_rows[0]["suite"],
                "stress_case": group_rows[0]["stress_case"],
                "provider": group_rows[0]["provider"],
                "model": group_rows[0]["model"],
                "prompt_family": group_rows[0]["prompt_family"],
                "n_slots": group_rows[0]["n_slots"],
                "slot_gap": group_rows[0]["slot_gap"],
                "condition_gates": {},
            },
        )
        cell["condition_gates"][condition] = group["gate"]["pass"]

    for cell in cells.values():
        condition_gates = cell["condition_gates"]
        controls = [value for condition, value in condition_gates.items() if condition != "prompt_json_bottleneck"]
        cell["controls_pass"] = bool(controls) and all(controls)
        cell["bottleneck_pass"] = bool(condition_gates.get("prompt_json_bottleneck", False))
        expected_conditions = set(API_BLACKBOX_CONDITIONS)
        cell["complete"] = expected_conditions.issubset(condition_gates)
        cell["pass"] = cell["complete"] and cell["controls_pass"] and cell["bottleneck_pass"]

    cell_items = list(cells.values())
    complete = bool(cell_items) and all(cell["complete"] for cell in cell_items)
    controls_pass = complete and all(cell["controls_pass"] for cell in cell_items)
    bottleneck_pass = complete and all(cell["bottleneck_pass"] for cell in cell_items)
    positive = controls_pass and bottleneck_pass
    strong_negative = controls_pass and not bottleneck_pass
    decision = {
        "complete": complete,
        "controls_pass": controls_pass,
        "bottleneck_pass": bottleneck_pass,
        "positive": positive,
        "strong_negative": strong_negative,
    }
    outcome = "positive" if positive else "strong_negative" if strong_negative else "inconclusive"
    return {
        "n_rows": len(rows),
        "groups": groups,
        "cells": dict(sorted(cells.items())),
        "decision": decision,
        "outcome": outcome,
    }


def make_provider_call(
    *,
    provider: str,
    model: str,
    api_key_env: str | None = None,
    base_url: str | None = None,
    timeout_seconds: float = 60.0,
    max_output_tokens: int = 64,
    temperature: float | None = 0.0,
    retries: int = 2,
) -> ProviderCall:
    """Create a provider call function."""

    if provider == "fixture":
        return _fixture_provider(model)
    if provider == "fixture_wrong_bottleneck":
        return _fixture_provider(model, wrong_bottleneck=True)
    if provider == "openai-responses":
        api_key = _api_key(api_key_env or "OPENAI_API_KEY")
        return _openai_responses_provider(api_key, model, base_url, timeout_seconds, max_output_tokens, temperature, retries)
    if provider in {"openai-chat", "openai-compatible"}:
        env_name = api_key_env or "OPENAI_API_KEY"
        api_key = _api_key(env_name)
        resolved_base_url = base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        return _openai_chat_provider(api_key, model, resolved_base_url, timeout_seconds, max_output_tokens, temperature, retries)
    if provider == "anthropic":
        api_key = _api_key(api_key_env or "ANTHROPIC_API_KEY")
        return _anthropic_provider(api_key, model, base_url, timeout_seconds, max_output_tokens, retries)
    if provider == "gemini":
        api_key = _api_key(api_key_env or "GEMINI_API_KEY")
        return _gemini_provider(api_key, model, base_url, timeout_seconds, max_output_tokens, temperature, retries)
    raise ValueError(f"Unknown provider {provider!r}")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_summary(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def total_request_count(cases: list[ApiBenchmarkCase]) -> int:
    return sum(case.request_count for case in cases)


def manifest_from_cases(
    *,
    cases: list[ApiBenchmarkCase],
    suite: str,
    provider: str,
    models: list[str],
    base_seed: int,
    max_output_tokens: int,
) -> dict[str, Any]:
    return {
        "suite": suite,
        "provider": provider,
        "models": models,
        "base_seed": base_seed,
        "n_cases": len(cases),
        "n_requests": total_request_count(cases),
        "max_output_tokens": max_output_tokens,
        "prompt_families": sorted({case.prompt_family for case in cases}),
        "conditions": sorted({case.condition for case in cases}),
        "stress_cases": sorted({case.stress_case for case in cases}),
        "n_slots_values": sorted({case.n_slots for case in cases}),
        "slot_gap_values": sorted({case.slot_gap for case in cases}),
        "expected_max_output_tokens": total_request_count(cases) * max_output_tokens,
    }


def _stress_specs(suite: str, n_slots_values: list[int], slot_gap_values: list[int]) -> list[tuple[str, int, int]]:
    if suite == "prompt_family":
        if len(n_slots_values) != 1 or len(slot_gap_values) != 1:
            raise ValueError("prompt_family suite expects one n_slots value and one slot_gap value")
        n_slots = n_slots_values[0]
        slot_gap = slot_gap_values[0]
        return [(f"{n_slots}slot_gap{slot_gap}", n_slots, slot_gap)]
    return [
        (f"{n_slots}slot_gap{slot_gap}", n_slots, slot_gap)
        for n_slots in n_slots_values
        for slot_gap in slot_gap_values
    ]


def _user_prompt_for_condition(
    condition: str,
    prompt_family: str,
    bits: list[int],
    critical_slot: int,
    n_slots: int,
    slot_gap: int,
    variants_per_slot: int,
) -> str:
    if condition == "prompt_json_format_control":
        return format_user_prompt()
    if condition == "prompt_json_visible_control":
        return visible_user_prompt(bits, critical_slot, variants_per_slot)
    if condition == "prompt_json_short_horizon_control":
        return short_user_prompt(bits, critical_slot, variants_per_slot)
    if condition == "prompt_json_bottleneck":
        return prompt_family_user_prompt(prompt_family, bits, critical_slot, n_slots, slot_gap, variants_per_slot)
    raise ValueError(f"Unknown condition {condition!r}")


def _score_first_action(case: ApiBenchmarkCase, parsed: dict[str, Any]) -> dict[str, Any]:
    schema = float(parsed["valid"])
    noop = float(parsed["opcode"] == "noop" and parsed["valid"])
    slot = float(parsed["valid"] and parsed["slot"] == case.critical_slot)
    value = float(parsed["valid"] and parsed["value"] == case.expected_value)
    call = float(parsed["opcode"] == "call" and parsed["valid"])
    if case.condition in {"prompt_json_format_control", "prompt_json_visible_control"}:
        final = noop
    elif case.condition in {"prompt_json_short_horizon_control", "prompt_json_bottleneck"}:
        final = float(call and slot and value)
    else:
        final = 0.0
    return {
        "schema_validity": schema,
        "closed_loop_final_accuracy": final,
        "first_noop_field_accuracy": noop,
        "first_parsed_slot_accuracy": slot,
        "first_parsed_value_accuracy": value,
    }


def _score_repair_actions(
    case: ApiBenchmarkCase,
    failed_parsed: dict[str, Any],
    success_parsed: dict[str, Any],
) -> dict[str, Any]:
    failed_slot = float(failed_parsed["valid"] and failed_parsed["slot"] == case.critical_slot)
    failed_value = float(failed_parsed["valid"] and failed_parsed["value"] == case.expected_value)
    success_noop = float(success_parsed["valid"] and success_parsed["opcode"] == "noop")
    return {
        "repair_failed_schema_validity": float(failed_parsed["valid"]),
        "repair_failed_parsed_slot_accuracy": failed_slot,
        "repair_failed_parsed_value_accuracy": failed_value,
        "repair_success_noop_field_accuracy": success_noop,
        "repair_success_schema_validity": float(success_parsed["valid"]),
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
        key = "/".join(
            [
                str(row["suite"]),
                str(row["stress_case"]),
                str(row["provider"]),
                str(row["model"]),
                str(row["prompt_family"]),
                str(row["condition"]),
                f"{row['n_slots']}slot",
                f"gap{row['slot_gap']}",
            ]
        )
        grouped.setdefault(key, []).append(row)
    return grouped


def _cell_key(row: dict[str, Any]) -> str:
    return "/".join(
        [
            str(row["suite"]),
            str(row["stress_case"]),
            str(row["provider"]),
            str(row["model"]),
            str(row["prompt_family"]),
            f"{row['n_slots']}slot",
            f"gap{row['slot_gap']}",
        ]
    )


def _summarize_api_group(rows: list[dict[str, Any]], condition: str) -> dict[str, Any]:
    metrics = {
        "closed_loop_final_accuracy": _row_mean(rows, "closed_loop_final_accuracy"),
        "schema_validity": _row_mean(rows, "schema_validity"),
        "first_noop_field_accuracy": _row_mean(rows, "first_noop_field_accuracy"),
        "first_parsed_slot_accuracy": _row_mean(rows, "first_parsed_slot_accuracy"),
        "first_parsed_value_accuracy": _row_mean(rows, "first_parsed_value_accuracy"),
        "repair_failed_schema_validity": _row_mean(rows, "repair_failed_schema_validity"),
        "repair_failed_parsed_slot_accuracy": _row_mean(rows, "repair_failed_parsed_slot_accuracy"),
        "repair_failed_parsed_value_accuracy": _row_mean(rows, "repair_failed_parsed_value_accuracy"),
        "repair_success_noop_field_accuracy": _row_mean(rows, "repair_success_noop_field_accuracy"),
        "repair_success_schema_validity": _row_mean(rows, "repair_success_schema_validity"),
    }
    if condition == "prompt_json_format_control":
        gate = {
            "schema_validity_ge_0_95": _mean_ge(metrics["schema_validity"], PROMPT_JSON_CONTROL_SCHEMA_THRESHOLD),
            "first_noop_field_acc_ge_0_85": _mean_ge(metrics["first_noop_field_accuracy"], PROMPT_JSON_ACTION_THRESHOLD),
        }
    elif condition == "prompt_json_visible_control":
        gate = {
            "closed_loop_final_accuracy_ge_0_85": _mean_ge(
                metrics["closed_loop_final_accuracy"],
                PROMPT_JSON_ACTION_THRESHOLD,
            ),
            "first_noop_field_acc_ge_0_85": _mean_ge(metrics["first_noop_field_accuracy"], PROMPT_JSON_ACTION_THRESHOLD),
            "schema_validity_ge_0_95": _mean_ge(metrics["schema_validity"], PROMPT_JSON_CONTROL_SCHEMA_THRESHOLD),
        }
    elif condition == "prompt_json_short_horizon_control":
        gate = {
            "closed_loop_final_accuracy_ge_0_85": _mean_ge(
                metrics["closed_loop_final_accuracy"],
                PROMPT_JSON_ACTION_THRESHOLD,
            ),
            "first_schema_valid_ge_0_95": _mean_ge(metrics["schema_validity"], PROMPT_JSON_CONTROL_SCHEMA_THRESHOLD),
            "first_parsed_slot_acc_ge_0_85": _mean_ge(
                metrics["first_parsed_slot_accuracy"],
                PROMPT_JSON_ACTION_THRESHOLD,
            ),
            "first_parsed_value_acc_ge_0_85": _mean_ge(
                metrics["first_parsed_value_accuracy"],
                PROMPT_JSON_ACTION_THRESHOLD,
            ),
        }
    elif condition == "prompt_json_bottleneck":
        gate = {
            "closed_loop_final_accuracy_ge_0_85": _mean_ge(
                metrics["closed_loop_final_accuracy"],
                PROMPT_JSON_ACTION_THRESHOLD,
            ),
            "first_schema_valid_ge_0_95": _mean_ge(metrics["schema_validity"], PROMPT_JSON_CONTROL_SCHEMA_THRESHOLD),
            "first_parsed_slot_acc_ge_0_85": _mean_ge(
                metrics["first_parsed_slot_accuracy"],
                PROMPT_JSON_ACTION_THRESHOLD,
            ),
            "first_parsed_value_acc_ge_0_85": _mean_ge(
                metrics["first_parsed_value_accuracy"],
                PROMPT_JSON_ACTION_THRESHOLD,
            ),
            "repair_failed_schema_valid_ge_0_95": _mean_ge(
                metrics["repair_failed_schema_validity"],
                PROMPT_JSON_CONTROL_SCHEMA_THRESHOLD,
            ),
            "repair_failed_parsed_slot_acc_ge_0_85": _mean_ge(
                metrics["repair_failed_parsed_slot_accuracy"],
                PROMPT_JSON_ACTION_THRESHOLD,
            ),
            "repair_failed_parsed_value_acc_ge_0_85": _mean_ge(
                metrics["repair_failed_parsed_value_accuracy"],
                PROMPT_JSON_ACTION_THRESHOLD,
            ),
            "repair_success_noop_field_acc_ge_0_85": _mean_ge(
                metrics["repair_success_noop_field_accuracy"],
                PROMPT_JSON_ACTION_THRESHOLD,
            ),
            "repair_success_schema_valid_ge_0_95": _mean_ge(
                metrics["repair_success_schema_validity"],
                PROMPT_JSON_CONTROL_SCHEMA_THRESHOLD,
            ),
        }
    else:
        raise ValueError(f"Unknown condition {condition!r}")
    gate["pass"] = all(gate.values())
    return {
        "condition": condition,
        "n_rows": len(rows),
        **metrics,
        "gate": gate,
    }


def _row_mean(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return sum(values) / len(values) if values else None


def _mean_ge(value: float | None, threshold: float) -> bool:
    return value is not None and value >= threshold


def _api_key(env_name: str) -> str:
    api_key = os.environ.get(env_name)
    if not api_key:
        raise RuntimeError(f"Missing API key environment variable {env_name}")
    return api_key


def _fixture_provider(model: str, *, wrong_bottleneck: bool = False) -> ProviderCall:
    def call(message_list: list[dict[str, str]], case: ApiBenchmarkCase, phase: str) -> ProviderResult:
        del message_list
        if phase == "repair_success" or case.condition in {
            "prompt_json_format_control",
            "prompt_json_visible_control",
        }:
            text = '{"tool":"noop"}'
        elif wrong_bottleneck and case.condition == "prompt_json_bottleneck":
            text = f'{{"tool":"read_slot","slot":"0","value":{case.expected_value}}}'
        else:
            text = (
                '{"tool":"read_slot",'
                f'"slot":"{_slot_phrase(case.critical_slot, case.variants_per_slot)}",'
                f'"value":{case.expected_value}'
                "}"
            )
        return ProviderResult(text=text, usage={"fixture": True, "model": model})

    return call


def _slot_phrase(slot: int, variants_per_slot: int) -> str:
    from experiments.long_horizon_bottleneck.prompt_json_tasks import slot_phrase

    return slot_phrase(slot, variants_per_slot)


def _openai_responses_provider(
    api_key: str,
    model: str,
    base_url: str | None,
    timeout_seconds: float,
    max_output_tokens: int,
    temperature: float | None,
    retries: int,
) -> ProviderCall:
    root = (base_url or "https://api.openai.com/v1").rstrip("/")
    url = f"{root}/responses"

    def call(message_list: list[dict[str, str]], case: ApiBenchmarkCase, phase: str) -> ProviderResult:
        del case, phase
        payload: dict[str, Any] = {
            "model": model,
            "input": message_list,
            "max_output_tokens": max_output_tokens,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        raw = _post_json(url, {"Authorization": f"Bearer {api_key}"}, payload, timeout_seconds, retries)
        text = str(raw.get("output_text") or _extract_openai_responses_text(raw)).strip()
        return ProviderResult(text=text, usage=_usage(raw), raw=raw)

    return call


def _openai_chat_provider(
    api_key: str,
    model: str,
    base_url: str,
    timeout_seconds: float,
    max_output_tokens: int,
    temperature: float | None,
    retries: int,
) -> ProviderCall:
    url = f"{base_url.rstrip('/')}/chat/completions"

    def call(message_list: list[dict[str, str]], case: ApiBenchmarkCase, phase: str) -> ProviderResult:
        del case, phase
        payload: dict[str, Any] = {
            "model": model,
            "messages": message_list,
            "max_tokens": max_output_tokens,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        raw = _post_json(url, {"Authorization": f"Bearer {api_key}"}, payload, timeout_seconds, retries)
        text = str(raw["choices"][0]["message"].get("content") or "").strip()
        return ProviderResult(text=text, usage=_usage(raw), raw=raw)

    return call


def _anthropic_provider(
    api_key: str,
    model: str,
    base_url: str | None,
    timeout_seconds: float,
    max_output_tokens: int,
    retries: int,
) -> ProviderCall:
    url = f"{(base_url or 'https://api.anthropic.com/v1').rstrip('/')}/messages"

    def call(message_list: list[dict[str, str]], case: ApiBenchmarkCase, phase: str) -> ProviderResult:
        del case, phase
        system = "\n\n".join(message["content"] for message in message_list if message["role"] == "system")
        anthropic_messages = [message for message in message_list if message["role"] != "system"]
        payload = {
            "model": model,
            "max_tokens": max_output_tokens,
            "system": system,
            "messages": anthropic_messages,
        }
        raw = _post_json(
            url,
            {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            payload,
            timeout_seconds,
            retries,
        )
        text_parts = [block.get("text", "") for block in raw.get("content", []) if block.get("type") == "text"]
        return ProviderResult(text="".join(text_parts).strip(), usage=_usage(raw), raw=raw)

    return call


def _gemini_provider(
    api_key: str,
    model: str,
    base_url: str | None,
    timeout_seconds: float,
    max_output_tokens: int,
    temperature: float | None,
    retries: int,
) -> ProviderCall:
    model_name = model if model.startswith("models/") else f"models/{model}"
    quoted_model = urllib.parse.quote(model_name, safe="/")
    root = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
    url = f"{root}/{quoted_model}:generateContent?key={urllib.parse.quote(api_key)}"

    def call(message_list: list[dict[str, str]], case: ApiBenchmarkCase, phase: str) -> ProviderResult:
        del case, phase
        system = "\n\n".join(message["content"] for message in message_list if message["role"] == "system")
        user_text = "\n\n".join(message["content"] for message in message_list if message["role"] != "system")
        generation_config: dict[str, Any] = {"maxOutputTokens": max_output_tokens}
        if temperature is not None:
            generation_config["temperature"] = temperature
        payload = {
            "systemInstruction": {"parts": [{"text": system or SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": user_text}]}],
            "generationConfig": generation_config,
        }
        raw = _post_json(url, {}, payload, timeout_seconds, retries)
        text_parts: list[str] = []
        for candidate in raw.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if "text" in part:
                    text_parts.append(part["text"])
        return ProviderResult(text="".join(text_parts).strip(), usage=_usage(raw), raw=raw)

    return call


def _post_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_seconds: float,
    retries: int,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request_headers = {
        "Content-Type": "application/json",
        "User-Agent": "research-derived-long-horizon-benchmark/0.1",
        **headers,
    }
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        request = urllib.request.Request(url, data=body, headers=request_headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code < 500 or attempt == retries:
                detail = error.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"Provider HTTP {error.code}: {detail}") from error
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
            if attempt == retries:
                raise RuntimeError(f"Provider request failed: {error}") from error
        time.sleep(min(2.0, 0.5 * (attempt + 1)))
    raise RuntimeError(f"Provider request failed: {last_error}")


def _extract_openai_responses_text(raw: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in raw.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and "text" in content:
                chunks.append(str(content["text"]))
    return "".join(chunks)


def _usage(raw: dict[str, Any]) -> dict[str, Any]:
    usage = raw.get("usage")
    return usage if isinstance(usage, dict) else {}


def case_to_dict(case: ApiBenchmarkCase) -> dict[str, Any]:
    data = asdict(case)
    data["bits"] = list(case.bits)
    data["expected_value"] = case.expected_value
    data["request_count"] = case.request_count
    return data


def parse_csv_arg(value: str) -> list[str]:
    return parse_csv(value)


def parse_int_csv_arg(value: str) -> list[int]:
    return [int(item) for item in parse_csv(value)]
