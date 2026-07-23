"""Run the deterministic concern-gated off-context retrieval pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from math import isfinite
from pathlib import Path
from typing import Any

from experiments.concern_gated_retrieval.benchmark import (
    EvaluationResult,
    ORACLE_CARE_WEIGHTS,
    candidate_epiplexity,
    epiplexity_control_audit,
    evaluate_episodes,
    generate_episodes,
    learn_care_weights,
)


PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_DIR / "results" / "summary.json"
TRAIN_SEEDS = tuple(range(64))
EVALUATION_SEEDS = tuple(range(64, 128))
REGIMES = ("base", "sparse", "noisy")


def _round(value: float) -> float:
    return round(value, 12)


def _metrics(result: EvaluationResult) -> dict[str, Any]:
    return {
        "episodes": result.episodes,
        "hit_at_1": {
            key: _round(value) for key, value in result.hit_at_1.items()
        },
        "mean_reciprocal_rank": {
            key: _round(value)
            for key, value in result.mean_reciprocal_rank.items()
        },
        "distractor_at_1": {
            key: _round(value) for key, value in result.distractor_at_1.items()
        },
        "verifier_precision": _round(result.verifier_precision),
        "verifier_recall": _round(result.verifier_recall),
        "max_ppr_residual": result.max_ppr_residual,
    }


def _gate(status: bool, value: Any, criterion: str) -> dict[str, Any]:
    return {
        "status": "pass" if status else "fail",
        "value": value,
        "criterion": criterion,
    }


def numerical_validity_pass(
    max_ppr_residual: float,
    minimum_epiplexity_margin_bits: float,
) -> bool:
    return (
        isfinite(max_ppr_residual)
        and isfinite(minimum_epiplexity_margin_bits)
        and max_ppr_residual <= 1e-10
        and minimum_epiplexity_margin_bits >= 0.75
    )


def build_summary() -> dict[str, Any]:
    training = generate_episodes(TRAIN_SEEDS, regimes=("base",))
    learning = learn_care_weights(training)
    evaluation = generate_episodes(EVALUATION_SEEDS, regimes=REGIMES)
    initial_result = evaluate_episodes(evaluation, learning.initial_weights)
    learned_result = evaluate_episodes(evaluation, learning.learned_weights)
    oracle_result = evaluate_episodes(evaluation, ORACLE_CARE_WEIGHTS)
    by_regime = {
        regime: _metrics(
            evaluate_episodes(
                [episode for episode in evaluation if episode.regime == regime],
                learning.learned_weights,
            )
        )
        for regime in REGIMES
    }

    control_audit = epiplexity_control_audit(evaluation)
    representative = evaluation[0]
    representative_by_role = {
        candidate.role: candidate for candidate in representative.candidates
    }
    epiplexity_controls = {
        role: _round(candidate_epiplexity(candidate, representative.seed))
        for role, candidate in representative_by_role.items()
    }

    learned_metrics = _metrics(learned_result)
    single_sided_best = max(
        learned_result.hit_at_1["context"],
        learned_result.hit_at_1["care"],
    )
    weakest_regime_gap = min(
        metrics["hit_at_1"]["coincidence"]
        - max(metrics["hit_at_1"]["context"], metrics["hit_at_1"]["care"])
        for metrics in by_regime.values()
    )
    gates = {
        "NUMERICAL_VALIDITY": _gate(
            numerical_validity_pass(
                learned_result.max_ppr_residual,
                control_audit.minimum_margin_bits,
            ),
            {
                "max_ppr_residual": learned_result.max_ppr_residual,
                "minimum_structured_epiplexity_margin_bits": _round(
                    control_audit.minimum_margin_bits
                ),
                "worst_seed": control_audit.worst_seed,
                "worst_regime": control_audit.worst_regime,
                "worst_control_role": control_audit.worst_control_role,
            },
            "PPR residual <= 1e-10 and worst registered structured-vs-control epiplexity margin >= 0.75 bits.",
        ),
        "DUAL_ACTIVATION_SELECTIVITY": _gate(
            learned_result.hit_at_1["coincidence"] >= 0.85
            and learned_result.hit_at_1["coincidence"] - single_sided_best >= 0.20
            and weakest_regime_gap >= 0.10,
            {
                "coincidence_hit_at_1": learned_result.hit_at_1["coincidence"],
                "best_single_sided_hit_at_1": single_sided_best,
                "aggregate_gap": _round(
                    learned_result.hit_at_1["coincidence"] - single_sided_best
                ),
                "weakest_regime_gap": _round(weakest_regime_gap),
            },
            "Coincidence hit@1 >= 0.85, aggregate gap over both one-sided controls >= 0.20, and each regime gap >= 0.10.",
        ),
        "UTILIZATION_FILTER": _gate(
            learned_result.verifier_precision >= 0.90
            and learned_result.verifier_recall >= 0.90,
            {
                "precision": learned_result.verifier_precision,
                "recall": learned_result.verifier_recall,
            },
            "Goal-conditioned epiplexity filter precision and recall are both >= 0.90 within the top-3 nominations.",
        ),
        "ONLINE_CARE_RECOVERY": _gate(
            learned_result.hit_at_1["coincidence"]
            >= initial_result.hit_at_1["coincidence"]
            and learned_result.hit_at_1["coincidence"]
            >= oracle_result.hit_at_1["coincidence"] - 0.05,
            {
                "initial_hit_at_1": initial_result.hit_at_1["coincidence"],
                "learned_hit_at_1": learned_result.hit_at_1["coincidence"],
                "oracle_hit_at_1": oracle_result.hit_at_1["coincidence"],
            },
            "Exploratory: learned-care coincidence hit@1 does not regress from initialization and is within 0.05 of oracle care.",
        ),
    }
    fatal_gate_ids = (
        "NUMERICAL_VALIDITY",
        "DUAL_ACTIVATION_SELECTIVITY",
        "UTILIZATION_FILTER",
    )
    allowed_claim = (
        "synthetic diagnostic"
        if all(gates[gate_id]["status"] == "pass" for gate_id in fatal_gate_ids)
        else "scaffold only"
    )
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": "concern_gated_retrieval_pilot_2026_07_23",
        "package": "concern_gated_retrieval",
        "allowed_claim": allowed_claim,
        "claim_boundary": (
            "A deterministic typed memory-graph benchmark can test whether "
            "rarity-corrected two-sided PPR plus a goal-conditioned bounded-"
            "observer filter distinguishes dual-relevant nodes from the "
            "registered synthetic controls. This is not human-memory, "
            "selfhood, semantic-meaning, or deployment evidence."
        ),
        "parameters": {
            "train_seeds": [TRAIN_SEEDS[0], TRAIN_SEEDS[-1]],
            "evaluation_seeds": [EVALUATION_SEEDS[0], EVALUATION_SEEDS[-1]],
            "regimes": list(REGIMES),
            "care_learning_rate": 0.2,
            "ppr_alpha": 0.2,
            "warp_strength": 0.45,
            "rarity_exponent": 0.25,
            "nomination_k": 3,
            "epiplexity_threshold_bits": 0.75,
        },
        "care_learning": asdict(learning),
        "epiplexity_control_audit": {
            "minimum_margin_bits": _round(control_audit.minimum_margin_bits),
            "worst_seed": control_audit.worst_seed,
            "worst_regime": control_audit.worst_regime,
            "worst_control_role": control_audit.worst_control_role,
            "role_minimum_bits": {
                role: _round(value)
                for role, value in control_audit.role_minimum_bits.items()
            },
            "role_maximum_bits": {
                role: _round(value)
                for role, value in control_audit.role_maximum_bits.items()
            },
        },
        "epiplexity_controls_bits": epiplexity_controls,
        "initial_care": _metrics(initial_result),
        "learned_care": learned_metrics,
        "oracle_care": _metrics(oracle_result),
        "by_regime_learned_care": by_regime,
        "gates": gates,
        "rejected_alternatives_preserved": [
            "context-only PPR",
            "care-only PPR",
            "additive context-plus-care PPR",
            "unverified coincidence ranking",
            "noise and constant-future utilization controls",
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["summary_digest"] = hashlib.sha256(canonical.encode()).hexdigest()
    return payload


def write_summary(path: Path = DEFAULT_OUTPUT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_summary(), sort_keys=True, indent=2) + "\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    written = write_summary(args.output)
    print(f"wrote {written}")


if __name__ == "__main__":
    main()
