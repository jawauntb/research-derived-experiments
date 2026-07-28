"""IDENT evaluation runner for baselines and one-shot model protocol."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Any

from experiments.ident.eval.baselines import BASELINES, run_baseline_on_item
from experiments.ident.eval.model_adapters import (
    FINAL_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    ChatModel,
    extract_json_object,
    render_intervention_followup,
    render_item_prompt,
)
from experiments.ident.eval.reports import write_report
from experiments.ident.generation import load_jsonl
from experiments.ident.schemas import IdentItem
from experiments.ident.scoring import (
    AggregateScores,
    ItemScore,
    aggregate_scores,
    parse_model_action,
    score_item,
)
from experiments.ident.separators import outcome_for
from experiments.ident.validation import validate_split

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "splits"
RESULTS_DIR = ROOT / "results"


def evaluate_baseline(
    items: list[IdentItem],
    baseline_name: str,
    *,
    seed: int = 0,
) -> tuple[list[ItemScore], AggregateScores, list[dict[str, Any]]]:
    scores: list[ItemScore] = []
    transcripts: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        action, final = run_baseline_on_item(baseline_name, item, seed=seed + i)
        scored = score_item(item, action, final_answer=final)
        scores.append(scored)
        transcripts.append(
            {
                "item_id": item.item_id,
                "baseline": baseline_name,
                "first_action": {
                    "action_type": action.action_type,
                    "intervention_id": action.intervention_id,
                    "answer": action.answer,
                    "identifiable_now": action.identifiable_now,
                    "confidence": action.confidence,
                },
                "final_answer": final,
                "score": scored.to_dict(),
            }
        )
    return scores, aggregate_scores(scores), transcripts


def evaluate_model(
    items: list[IdentItem],
    model: ChatModel,
    *,
    model_name: str,
) -> tuple[list[ItemScore], AggregateScores, list[dict[str, Any]]]:
    scores: list[ItemScore] = []
    transcripts: list[dict[str, Any]] = []
    for idx, item in enumerate(items):
        raw1 = ""
        raw2: str | None = None
        final_answer: str | None = None
        error: str | None = None
        try:
            raw1 = model.complete(system=SYSTEM_PROMPT, user=render_item_prompt(item))
            payload1 = extract_json_object(raw1)
            action = parse_model_action(payload1)
            if action.action_type == "intervene" and action.intervention_id:
                menu = {g.id for g in item.candidate_interventions}
                if action.intervention_id not in menu:
                    # Invalid menu choice: count as failed intervention, not parse crash.
                    scored = score_item(item, action, final_answer="__invalid_intervention__")
                else:
                    outcome = outcome_for(
                        item.true_hypothesis,
                        action.intervention_id,
                        item.response_table,
                    )
                    raw2 = model.complete(
                        system=FINAL_SYSTEM_PROMPT,
                        user=render_intervention_followup(
                            item, action.intervention_id, outcome
                        ),
                    )
                    payload2 = extract_json_object(raw2)
                    final_answer = str(payload2.get("answer"))
                    scored = score_item(item, action, final_answer=final_answer)
            elif action.action_type == "answer":
                final_answer = action.answer
                scored = score_item(item, action, final_answer=final_answer)
            else:
                scored = score_item(item, action, final_answer=final_answer)
        except Exception as exc:  # noqa: BLE001 - record per-item failures for scoring
            error = f"{type(exc).__name__}: {exc}"
            # Fail closed: treat as confident answer-now with invalid answer.
            from experiments.ident.scoring import ModelAction

            action = ModelAction(
                action_type="answer",
                answer="__parse_error__",
                identifiable_now=True,
                live_hypotheses=tuple(item.equivalence_class_before),
                confidence=1.0,
                brief_reason="parse/runtime error",
            )
            scored = score_item(item, action, final_answer="__parse_error__")
        scores.append(scored)
        transcripts.append(
            {
                "item_id": item.item_id,
                "model": model_name,
                "index": idx,
                "raw_stage1": raw1,
                "raw_stage2": raw2,
                "final_answer": final_answer,
                "error": error,
                "score": scored.to_dict(),
            }
        )
        print(
            f"[{model_name}] {idx + 1}/{len(items)} {item.item_id} "
            f"sep={scored.separator_correct} final={scored.final_correct}"
            + (f" ERR={error}" if error else ""),
            flush=True,
        )
    return scores, aggregate_scores(scores), transcripts


def compute_model_gates(
    *,
    model_aggregates: dict[str, AggregateScores],
    oracle_separator_accuracy: float = 1.0,
    oracle_final_accuracy: float = 1.0,
    material_gap: float = 0.10,
) -> dict[str, bool]:
    """G5 capability gap; G7 is assessed by a separate reshuffle run when provided.

    A material gap may appear in separator choice, weakness regret, false certainty,
    or final/post-intervention identification (update-after-evidence failures).
    """
    g5 = any(
        (agg.separator_accuracy <= oracle_separator_accuracy - material_gap)
        or (
            agg.mean_weakness_regret is not None and agg.mean_weakness_regret >= 0.25
        )
        or (agg.false_certainty_rate >= 0.20)
        or (agg.final_accuracy <= oracle_final_accuracy - material_gap)
        or (
            agg.post_intervention_identification is not None
            and agg.post_intervention_identification
            <= oracle_final_accuracy - material_gap
        )
        for agg in model_aggregates.values()
    )
    return {"G5_capability_gap": g5}


def compute_gates(
    *,
    items: list[IdentItem],
    baseline_aggregates: dict[str, AggregateScores],
) -> dict[str, bool]:
    """Construction/eval gates G1–G4 (and partial G6) from baselines."""
    g1 = all(len(item.equivalence_class_before) >= 2 for item in items)
    g2 = all(len(item.minimum_separators) >= 1 for item in items)

    answer_now = baseline_aggregates["answer_now"]
    # Passive bound: answer-now final accuracy should not exceed mean chance beyond
    # sampling error (Hoeffding slack at ~95% for the split size).
    mean_bound = sum(item.passive_chance_bound for item in items) / max(len(items), 1)
    n = max(len(items), 1)
    slack = math.sqrt(math.log(20.0) / (2.0 * n))
    g3 = answer_now.final_accuracy <= mean_bound + slack

    oracle = baseline_aggregates["oracle_weakest_separator"]
    g4 = (oracle.post_intervention_identification or 0.0) >= 0.99 or oracle.final_accuracy >= 0.99

    eig = baseline_aggregates["expected_information_gain"]
    # G6: EIG should not trivially saturate every domain at oracle level.
    g6 = eig.separator_accuracy < 0.999 or eig.mean_weakness_regret not in (0.0, None)

    return {
        "G1_formal_ambiguity": g1,
        "G2_separability": g2,
        "G3_passive_bound": g3,
        "G4_oracle_solvability": g4,
        "G6_nontriviality": g6,
    }


def run_local_baseline_suite(
    *,
    split: str = "test",
    seed: int = 0,
    limit: int | None = None,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    data_path = DATA_DIR / f"{split}.jsonl"
    items = load_jsonl(data_path)
    if limit is not None:
        items = items[:limit]
    validation = validate_split(items)
    if validation.failed:
        raise RuntimeError(f"invalid split: {validation.errors[:3]}")

    aggregates: dict[str, AggregateScores] = {}
    all_transcripts: dict[str, list[dict[str, Any]]] = {}
    for name in BASELINES:
        scores, agg, transcripts = evaluate_baseline(items, name, seed=seed)
        aggregates[name] = agg
        all_transcripts[name] = transcripts

    gates = compute_gates(items=items, baseline_aggregates=aggregates)
    for name, agg in aggregates.items():
        aggregates[name] = AggregateScores(
            n_items=agg.n_items,
            separator_accuracy=agg.separator_accuracy,
            mean_weakness_regret=agg.mean_weakness_regret,
            false_certainty_rate=agg.false_certainty_rate,
            post_intervention_identification=agg.post_intervention_identification,
            mean_efficiency=agg.mean_efficiency,
            final_accuracy=agg.final_accuracy,
            gates=gates,
            by_domain=agg.by_domain,
        )

    summary = {
        "experiment_id": "ident",
        "schema_version": "1.0",
        "split": split,
        "n_items": len(items),
        "seed": seed,
        "gates": gates,
        "status": "pass" if all(gates[g] for g in ("G1_formal_ambiguity", "G2_separability", "G3_passive_bound", "G4_oracle_solvability")) else "fail",
        "baselines": {name: agg.to_dict() for name, agg in aggregates.items()},
    }
    out = out_dir or RESULTS_DIR
    write_report(out / "baseline_summary.json", summary)
    # Public-safe: do not dump full per-item transcripts into committed results by default.
    raw_dir = ROOT.parent.parent / "artifacts" / "ident"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"baseline_transcripts_{split}.json").write_text(
        json.dumps(all_transcripts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run IDENT baseline evaluation")
    parser.add_argument("--split", default="test", choices=["train", "dev", "test"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    summary = run_local_baseline_suite(
        split=args.split,
        seed=args.seed,
        limit=args.limit,
        out_dir=args.out_dir,
    )
    print(json.dumps({"status": summary["status"], "gates": summary["gates"]}, indent=2))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
