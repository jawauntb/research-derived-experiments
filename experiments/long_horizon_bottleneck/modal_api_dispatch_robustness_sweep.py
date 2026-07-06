#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Run the OpenAI dispatch robustness characterization on cheap Modal CPU.

This runner expands the targeted dispatch characterization across critical
slots while preserving the same parser, controls, provider adapter, repair
protocol, and stress grid. It uses no GPU and keeps raw rows under gitignored
`artifacts/`.

Recommended dry run:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/long_horizon_bottleneck/modal_api_dispatch_robustness_sweep.py \\
        --dry-run-budget

Recommended bounded run:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/long_horizon_bottleneck/modal_api_dispatch_robustness_sweep.py \\
        --models gpt-4.1-nano --critical-slots 0,1,2,3 \\
        --seeds 3 --episodes-per-cell 1 --max-requests 720
"""

from __future__ import annotations

import importlib
import json
from datetime import date
from pathlib import Path
from typing import Any, cast

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source("experiments")
APP_NAME = "research-derived-api-dispatch-robustness"
MODAL_SECRET_NAME = "llm-api-keys"
DEFAULT_OUT = "artifacts/long_horizon_bottleneck/api_dispatch_robustness_openai_gpt41_nano_summary.json"
DEFAULT_JSONL = "artifacts/long_horizon_bottleneck/api_dispatch_robustness_openai_gpt41_nano_rows.jsonl"
DEFAULT_REPORT = (
    "experiments/long_horizon_bottleneck/results/"
    "zzzzzzzzzzzzzzzzzzzz_api_dispatch_robustness_openai_gpt41_nano_2026_07_06.md"
)

app = modal.App(name=APP_NAME)


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _int_csv(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def _cases_for_slot(
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
):
    from experiments.long_horizon_bottleneck.api_dispatch_characterization import (
        build_dispatch_characterization_cases,
    )

    return build_dispatch_characterization_cases(
        stress_cases=stress_cases,
        case_types=case_types,
        seeds=seeds,
        episodes_per_cell=episodes_per_cell,
        critical_slot=critical_slot,
        n_slots_values=n_slots_values,
        slot_gap_values=slot_gap_values,
        variants_per_slot=variants_per_slot,
        base_seed=base_seed,
    )


@app.function(
    image=IMAGE,
    secrets=[modal.Secret.from_name(MODAL_SECRET_NAME)],
    timeout=7200,
    cpu=1,
    memory=1024,
    single_use_containers=True,
)
def run_critical_slot(
    critical_slot: int,
    provider: str,
    models: list[str],
    stress_cases: list[str],
    case_types: list[str],
    seeds: int,
    episodes_per_cell: int,
    n_slots_values: list[int],
    slot_gap_values: list[int],
    variants_per_slot: int,
    base_seed: int,
    api_key_env: str | None,
    base_url: str | None,
    timeout_seconds: float,
    max_output_tokens: int,
    temperature: float | None,
    sleep_seconds: float,
    include_raw: bool,
) -> dict[str, Any]:
    from experiments.long_horizon_bottleneck.api_blackbox import make_provider_call
    from experiments.long_horizon_bottleneck.api_dispatch_characterization import (
        DispatchProviderCall,
        evaluate_dispatch_characterization_cases,
        total_request_count,
    )

    cases = _cases_for_slot(
        stress_cases=stress_cases,
        case_types=case_types,
        seeds=seeds,
        episodes_per_cell=episodes_per_cell,
        critical_slot=critical_slot,
        n_slots_values=n_slots_values,
        slot_gap_values=slot_gap_values,
        variants_per_slot=variants_per_slot,
        base_seed=base_seed,
    )
    rows: list[dict[str, Any]] = []
    for model in models:
        provider_call = cast(
            DispatchProviderCall,
            make_provider_call(
                provider=provider,
                model=model,
                api_key_env=api_key_env,
                base_url=base_url,
                timeout_seconds=timeout_seconds,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
            ),
        )
        rows.extend(
            evaluate_dispatch_characterization_cases(
                cases,
                model=model,
                provider_name=provider,
                provider_call=provider_call,
                include_prompts=False,
                include_raw=include_raw,
                sleep_seconds=sleep_seconds,
            )
        )
    return {
        "critical_slot": critical_slot,
        "n_cases": len(cases),
        "n_requests": total_request_count(cases) * len(models),
        "rows": rows,
    }


@app.local_entrypoint()
def main(
    provider: str = "openai-responses",
    models: str = "gpt-4.1-nano",
    api_key_env: str | None = None,
    base_url: str | None = None,
    timeout_seconds: float = 60.0,
    max_output_tokens: int = 64,
    temperature: float = 0.0,
    no_temperature: bool = False,
    stress_cases: str = "",
    case_types: str = "",
    seeds: int = 3,
    episodes_per_cell: int = 1,
    critical_slots: str = "0,1,2,3",
    n_slots: str = "4,8",
    slot_gap: str = "8,16",
    variants_per_slot: int = 3,
    base_seed: int = 20261050,
    max_requests: int = 720,
    sleep_seconds: float = 0.05,
    out: str = DEFAULT_OUT,
    jsonl: str = DEFAULT_JSONL,
    report_md: str = DEFAULT_REPORT,
    include_raw: bool = False,
    dry_run_budget: bool = False,
) -> None:
    from experiments.long_horizon_bottleneck.api_dispatch_characterization import (
        DISPATCH_CHARACTERIZATION_CASE_TYPES,
        manifest_from_cases,
        render_dispatch_characterization_markdown,
        summarize_dispatch_characterization_rows,
        summarize_dispatch_robustness,
        total_request_count,
        write_jsonl,
        write_markdown,
    )
    from experiments.long_horizon_bottleneck.api_blackbox import write_summary

    models_list = _csv(models)
    case_types_list: list[str] = _csv(case_types) if case_types else list(DISPATCH_CHARACTERIZATION_CASE_TYPES)
    stress_cases_list = _csv(stress_cases) if stress_cases else []
    critical_slot_values = _int_csv(critical_slots)
    n_slots_values = _int_csv(n_slots)
    slot_gap_values = _int_csv(slot_gap)
    temperature_value = None if no_temperature else temperature

    cases_by_slot = {
        critical_slot: _cases_for_slot(
            stress_cases=stress_cases_list,
            case_types=case_types_list,
            seeds=seeds,
            episodes_per_cell=episodes_per_cell,
            critical_slot=critical_slot,
            n_slots_values=n_slots_values,
            slot_gap_values=slot_gap_values,
            variants_per_slot=variants_per_slot,
            base_seed=base_seed,
        )
        for critical_slot in critical_slot_values
    }
    planned_requests = sum(total_request_count(cases) for cases in cases_by_slot.values()) * len(models_list)
    if planned_requests > max_requests:
        raise SystemExit(f"Request guard failed: {planned_requests} requests exceeds --max-requests {max_requests}.")

    manifest_cases = [case for cases in cases_by_slot.values() for case in cases]
    manifest = manifest_from_cases(
        cases=manifest_cases,
        provider=provider,
        models=models_list,
        base_seed=base_seed,
        max_output_tokens=max_output_tokens,
    )
    manifest.update(
        {
            "runner": "modal_api_dispatch_robustness_sweep",
            "modal_app": APP_NAME,
            "modal_secret": MODAL_SECRET_NAME,
            "critical_slots": critical_slot_values,
            "request_count_by_slot": {
                str(slot): total_request_count(cases) * len(models_list)
                for slot, cases in sorted(cases_by_slot.items())
            },
        }
    )
    if dry_run_budget:
        print(json.dumps({"kind": "dispatch robustness dry run", "manifest": manifest}, indent=2))
        return

    slot_payloads = list(
        run_critical_slot.starmap(
            [
                (
                    critical_slot,
                    provider,
                    models_list,
                    stress_cases_list,
                    case_types_list,
                    seeds,
                    episodes_per_cell,
                    n_slots_values,
                    slot_gap_values,
                    variants_per_slot,
                    base_seed,
                    api_key_env,
                    base_url,
                    timeout_seconds,
                    max_output_tokens,
                    temperature_value,
                    sleep_seconds,
                    include_raw,
                )
                for critical_slot in critical_slot_values
            ]
        )
    )
    rows = [row for payload in slot_payloads for row in payload["rows"]]
    summary = summarize_dispatch_characterization_rows(rows)
    robustness = summarize_dispatch_robustness(summary)
    payload = {
        "kind": "long-horizon dispatch robustness characterization",
        "manifest": manifest,
        "slot_payloads": [
            {
                "critical_slot": item["critical_slot"],
                "n_cases": item["n_cases"],
                "n_requests": item["n_requests"],
                "n_rows": len(item["rows"]),
            }
            for item in slot_payloads
        ],
        "summary": summary,
        "robustness": robustness,
        "rows_jsonl": jsonl,
    }
    write_jsonl(Path(jsonl), rows)
    write_summary(Path(out), payload)
    write_markdown(
        Path(report_md),
        render_dispatch_characterization_markdown(
            payload,
            title="OpenAI Dispatch Robustness Characterization",
            report_date=date.today().isoformat(),
        ),
    )
    print(
        json.dumps(
            {
                "outcome": summary["outcome"],
                "robustness_outcome": robustness["outcome"],
                "n_rows": summary["n_rows"],
                "n_requests": planned_requests,
                "out": out,
                "jsonl": jsonl,
                "report_md": report_md,
            },
            indent=2,
        )
    )
