#!/usr/bin/env python3
"""Run IDENT frontier-model evaluation via OpenRouter."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from experiments.ident.eval.openrouter import DEFAULT_MODELS
from experiments.ident.eval.providers import make_chat_model
from experiments.ident.eval.reports import write_report
from experiments.ident.eval.runner import (
    RESULTS_DIR,
    ROOT,
    compute_model_gates,
    evaluate_baseline,
    evaluate_model,
)
from experiments.ident.generation import load_jsonl
from experiments.ident.schemas import IdentItem
from experiments.ident.validation import validate_split

DATA_DIR = ROOT / "splits"
FRONTIER_MODELS = (
    "openai:gpt-5.6-sol",
    "anthropic:claude-opus-5",
)


def _shuffle_surface(item: IdentItem, rng: random.Random) -> IdentItem:
    """G7 stress: reshuffle hypothesis order and intervention menu order."""
    hyps = list(item.hypotheses)
    rng.shuffle(hyps)
    interventions = list(item.candidate_interventions)
    rng.shuffle(interventions)
    return IdentItem(
        item_id=item.item_id,
        domain=item.domain,
        hypotheses=hyps,
        hypothesis_descriptions=dict(item.hypothesis_descriptions),
        prior_observations=list(item.prior_observations),
        equivalence_class_before=list(item.equivalence_class_before),
        candidate_interventions=interventions,
        response_table={h: dict(v) for h, v in item.response_table.items()},
        minimum_separators=list(item.minimum_separators),
        true_hypothesis=item.true_hypothesis,
        final_query=item.final_query,
        answer=item.answer,
        passive_chance_bound=item.passive_chance_bound,
        distractors=list(item.distractors),
        metadata={**item.metadata, "surface_shuffle_seed": True},
    )


def run_openrouter_eval(
    *,
    models: list[str],
    split: str = "test",
    limit: int | None = 40,
    seed: int = 0,
    robustness_pass: bool = True,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    items = load_jsonl(DATA_DIR / f"{split}.jsonl")
    if limit is not None:
        items = items[:limit]
    validation = validate_split(items)
    if validation.failed:
        raise RuntimeError(f"invalid split: {validation.errors[:3]}")

    # Oracle on the same slice for G5 comparison.
    _, oracle_agg, _ = evaluate_baseline(
        items, "oracle_weakest_separator", seed=seed
    )

    out = out_dir or RESULTS_DIR
    raw_dir = ROOT.parent.parent / "artifacts" / "ident"
    raw_dir.mkdir(parents=True, exist_ok=True)

    model_summaries: dict[str, Any] = {}
    model_aggs = {}
    all_transcripts: dict[str, Any] = {}

    for model_name in models:
        client = make_chat_model(model_name)
        scores, agg, transcripts = evaluate_model(
            items, client, model_name=model_name
        )
        model_aggs[model_name] = agg
        model_summaries[model_name] = agg.to_dict()
        all_transcripts[model_name] = transcripts

        if robustness_pass:
            rng = random.Random(seed + 17)
            shuffled = [_shuffle_surface(item, rng) for item in items]
            _, agg2, transcripts2 = evaluate_model(
                shuffled, client, model_name=f"{model_name}__shuffle"
            )
            model_summaries[f"{model_name}__shuffle"] = agg2.to_dict()
            all_transcripts[f"{model_name}__shuffle"] = transcripts2
            # G7 per model: separator accuracy should not collapse after shuffle.
            delta = abs(agg.separator_accuracy - agg2.separator_accuracy)
            model_summaries[model_name]["robustness_separator_delta"] = delta
            model_summaries[model_name]["robustness_pass"] = delta <= 0.15

    gates = compute_model_gates(
        model_aggregates=model_aggs,
        oracle_separator_accuracy=oracle_agg.separator_accuracy,
        oracle_final_accuracy=oracle_agg.final_accuracy,
    )
    # Aggregate G7 across models if robustness pass ran.
    if robustness_pass:
        gates["G7_robustness"] = all(
            bool(model_summaries[m].get("robustness_pass")) for m in models
        )

    provider_kind = (
        "frontier_direct"
        if any(m.startswith(("openai:", "anthropic:")) for m in models)
        else "openrouter"
    )
    summary = {
        "experiment_id": f"ident_{provider_kind}",
        "schema_version": "1.0",
        "split": split,
        "n_items": len(items),
        "seed": seed,
        "models": models,
        "oracle_on_slice": oracle_agg.to_dict(),
        "gates": gates,
        "status": "pass" if gates.get("G5_capability_gap") else "inconclusive",
        "models_scored": model_summaries,
    }
    summary_name = "frontier_summary.json" if provider_kind == "frontier_direct" else "model_summary.json"
    md_name = summary_name.replace(".json", ".md")
    write_report(out / summary_name, summary)
    (out / md_name).write_text(_model_markdown(summary), encoding="utf-8")
    transcript_name = (
        f"frontier_transcripts_{split}.json"
        if provider_kind == "frontier_direct"
        else f"model_transcripts_{split}.json"
    )
    (raw_dir / transcript_name).write_text(
        json.dumps(all_transcripts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _model_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# IDENT OpenRouter model summary",
        "",
        f"- split: `{summary.get('split')}`",
        f"- n_items: {summary.get('n_items')}",
        f"- status: **{summary.get('status')}**",
        "",
        "## Gates",
        "",
    ]
    for gate, ok in (summary.get("gates") or {}).items():
        lines.append(f"- {'PASS' if ok else 'FAIL'}: `{gate}`")
    lines.extend(["", "## Models", ""])
    oracle = summary.get("oracle_on_slice") or {}
    lines.append(
        f"- `oracle`: separator_acc={oracle.get('separator_accuracy', 0):.3f}, "
        f"final_acc={oracle.get('final_accuracy', 0):.3f}"
    )
    for name, agg in (summary.get("models_scored") or {}).items():
        if name.endswith("__shuffle"):
            continue
        lines.append(
            f"- `{name}`: separator_acc={agg.get('separator_accuracy', 0):.3f}, "
            f"false_certainty={agg.get('false_certainty_rate', 0):.3f}, "
            f"weakness_regret={agg.get('mean_weakness_regret')}, "
            f"final_acc={agg.get('final_accuracy', 0):.3f}, "
            f"robust_delta={agg.get('robustness_separator_delta')}"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="IDENT OpenRouter model eval")
    parser.add_argument(
        "--models",
        nargs="+",
        default=list(DEFAULT_MODELS),
        help=(
            "Model specs: openai:gpt-5.6, anthropic:claude-opus-5, "
            "or OpenRouter slugs like openai/gpt-4o-mini"
        ),
    )
    parser.add_argument(
        "--frontier",
        action="store_true",
        help=f"Use frontier defaults: {' '.join(FRONTIER_MODELS)}",
    )
    parser.add_argument("--split", default="test", choices=["train", "dev", "test"])
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--no-robustness",
        action="store_true",
        help="Skip G7 label/order reshuffle pass",
    )
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    models = list(FRONTIER_MODELS) if args.frontier else list(args.models)
    summary = run_openrouter_eval(
        models=models,
        split=args.split,
        limit=None if args.limit <= 0 else args.limit,
        seed=args.seed,
        robustness_pass=not args.no_robustness,
        out_dir=args.out_dir,
    )
    print(
        json.dumps(
            {
                "status": summary["status"],
                "gates": summary["gates"],
                "n_items": summary["n_items"],
                "models": {
                    k: {
                        "separator_accuracy": v.get("separator_accuracy"),
                        "false_certainty_rate": v.get("false_certainty_rate"),
                        "final_accuracy": v.get("final_accuracy"),
                        "mean_weakness_regret": v.get("mean_weakness_regret"),
                    }
                    for k, v in summary["models_scored"].items()
                    if not k.endswith("__shuffle")
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
