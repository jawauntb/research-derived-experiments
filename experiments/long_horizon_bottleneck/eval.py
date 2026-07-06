"""Command-line evaluator for the long-horizon moved-bottleneck benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.long_horizon_bottleneck.api_blackbox import (
    API_BLACKBOX_CONDITIONS,
    API_PROMPT_FAMILIES,
    build_api_benchmark_cases,
    evaluate_api_cases,
    make_provider_call,
    manifest_from_cases,
    parse_csv_arg,
    parse_int_csv_arg,
    read_jsonl,
    summarize_api_blackbox_rows,
    total_request_count,
    write_jsonl,
    write_summary,
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("prompt_family", "external_stress"), default="prompt_family")
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
    parser.add_argument("--prompt-families", default="standard,compact,ledger")
    parser.add_argument("--conditions", default=",".join(API_BLACKBOX_CONDITIONS))
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--episodes-per-cell", type=int, default=2)
    parser.add_argument("--critical-slots", default="0,1,2,3")
    parser.add_argument("--n-slots", default="4")
    parser.add_argument("--slot-gap", default="8")
    parser.add_argument("--variants-per-slot", type=int, default=3)
    parser.add_argument("--base-seed", type=int, default=20261050)
    parser.add_argument("--max-requests", type=int, default=500)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--out", default="artifacts/long_horizon_bottleneck/api_blackbox_summary.json")
    parser.add_argument("--jsonl", default="artifacts/long_horizon_bottleneck/api_blackbox_rows.jsonl")
    parser.add_argument("--replay-jsonl", help="Score an existing JSONL row file instead of calling a provider.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--omit-prompts", action="store_true")
    parser.add_argument("--include-raw", action="store_true")
    args = parser.parse_args(argv)

    models = parse_csv_arg(args.models)
    prompt_families = parse_csv_arg(args.prompt_families)
    conditions = parse_csv_arg(args.conditions)
    n_slots_values = parse_int_csv_arg(args.n_slots)
    slot_gap_values = parse_int_csv_arg(args.slot_gap)
    critical_slots = parse_int_csv_arg(args.critical_slots)
    temperature = None if args.no_temperature else args.temperature

    if args.replay_jsonl:
        rows = read_jsonl(Path(args.replay_jsonl))
        summary = summarize_api_blackbox_rows(rows)
        payload = {
            "kind": "long-horizon moved-bottleneck black-box replay",
            "replay_jsonl": args.replay_jsonl,
            "summary": summary,
        }
        write_summary(Path(args.out), payload)
        print(json.dumps({"outcome": summary["outcome"], "n_rows": summary["n_rows"], "out": args.out}, indent=2))
        return

    cases = build_api_benchmark_cases(
        suite=args.suite,
        prompt_families=prompt_families,
        conditions=conditions,
        seeds=args.seeds,
        episodes_per_cell=args.episodes_per_cell,
        critical_slots=critical_slots,
        n_slots_values=n_slots_values,
        slot_gap_values=slot_gap_values,
        variants_per_slot=args.variants_per_slot,
        base_seed=args.base_seed,
    )
    manifest = manifest_from_cases(
        cases=cases,
        suite=args.suite,
        provider=args.provider,
        models=models,
        base_seed=args.base_seed,
        max_output_tokens=args.max_output_tokens,
    )
    if total_request_count(cases) * len(models) > args.max_requests:
        raise SystemExit(
            f"Request guard failed: {total_request_count(cases) * len(models)} requests exceeds "
            f"--max-requests {args.max_requests}."
        )
    if args.dry_run:
        print(json.dumps({"kind": "long-horizon moved-bottleneck black-box dry run", "manifest": manifest}, indent=2))
        return

    all_rows = []
    for model in models:
        provider_call = make_provider_call(
            provider=args.provider,
            model=model,
            api_key_env=args.api_key_env,
            base_url=args.base_url,
            timeout_seconds=args.timeout_seconds,
            max_output_tokens=args.max_output_tokens,
            temperature=temperature,
        )
        rows = evaluate_api_cases(
            cases,
            model=model,
            provider_name=args.provider,
            provider_call=provider_call,
            include_prompts=not args.omit_prompts,
            include_raw=args.include_raw,
            sleep_seconds=args.sleep_seconds,
        )
        all_rows.extend(rows)

    summary = summarize_api_blackbox_rows(all_rows)
    write_jsonl(Path(args.jsonl), all_rows)
    payload = {
        "kind": "long-horizon moved-bottleneck black-box benchmark",
        "manifest": manifest,
        "summary": summary,
        "rows_jsonl": args.jsonl,
    }
    write_summary(Path(args.out), payload)
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
