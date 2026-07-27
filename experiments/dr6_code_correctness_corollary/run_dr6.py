"""DR6 scorer — aggregate 3 verifier subagents, apply DR5-wall gates.

Reads verifier_A.json, verifier_B.json, verifier_C.json from the results
directory (produced by three sandboxed subagents that had no shared
context and no view of the ground truth labels). Aggregates per-snippet
scores by median (robust to a single disagreement) and computes the six
preregistered gates from DR6_PREREGISTRATION.md.

Run:
    uv run --no-sync python -m experiments.dr6_code_correctness_corollary.run_dr6
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.dr6_code_correctness_corollary.snippets import SNIPPETS


__all__ = ["main"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
RESULTS_DIR: Final[Path] = _PACKAGE / "results"
VERDICT_PATH: Final[Path] = RESULTS_DIR / "dr6_verdict.json"

VERIFIER_FILES: Final[tuple[str, ...]] = ("verifier_A.json", "verifier_B.json", "verifier_C.json")


def _load_verifiers() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for name in VERIFIER_FILES:
        path = RESULTS_DIR / name
        if not path.is_file():
            raise SystemExit(f"missing verifier output: {path}")
        out.append(json.loads(path.read_text(encoding="utf-8")))
    return out


def _consensus_score(scores_by_verifier: Sequence[int]) -> int:
    """Median across verifiers, integer."""
    return int(round(statistics.median(scores_by_verifier)))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DR6 scoring and gates.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    verifiers = _load_verifiers()

    #: W1 — every verifier produced a score for every snippet.
    snippet_ids = [s.snippet_id for s in SNIPPETS]
    w1 = all(
        all(sid in v.get("scores", {}) for sid in snippet_ids) for v in verifiers
    )
    if not w1:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(
                {
                    "kind": "dr6_verdict",
                    "gates": {"W1_verifier_completeness": {"decision": "NO_GO"}},
                    "overall_decision": "NO_GO",
                    "reading": "verifier crash: at least one score missing",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        print("W1 NO_GO -- verifier output incomplete")
        return 1

    #: Consensus score per snippet.
    per_snippet: dict[str, Any] = {}
    for snippet in SNIPPETS:
        per_verifier = [int(v["scores"][snippet.snippet_id]) for v in verifiers]
        consensus = _consensus_score(per_verifier)
        per_snippet[snippet.snippet_id] = {
            "kind": snippet.kind,
            "surface_form": snippet.surface_form,
            "per_verifier": per_verifier,
            "consensus": consensus,
            "verifier_stdev": statistics.stdev(per_verifier) if len(per_verifier) > 1 else 0.0,
        }

    realisations = [
        per_snippet[s.snippet_id] for s in SNIPPETS if s.kind == "realisation"
    ]
    placebos = [per_snippet[s.snippet_id] for s in SNIPPETS if s.kind == "placebo"]

    realisation_scores = [r["consensus"] for r in realisations]
    placebo_scores = [p["consensus"] for p in placebos]

    #: W2 -- median realisation score >= 6
    realisation_median = statistics.median(realisation_scores)
    w2 = realisation_median >= 6

    #: W3 -- realisation stdev >= 1.5 (visible variation across surface forms)
    realisation_stdev = statistics.stdev(realisation_scores) if len(realisation_scores) > 1 else 0.0
    w3 = realisation_stdev >= 1.5

    #: W4 -- placebo median <= 3
    placebo_median = statistics.median(placebo_scores)
    w4 = placebo_median <= 3

    #: W5 -- at least one placebo scores >= 5 (projection signal)
    w5 = any(p >= 5 for p in placebo_scores)

    #: W6 -- min(realisations) < max(placebos) (overlap = strongest wall signal)
    w6 = min(realisation_scores) < max(placebo_scores)

    all_gates = [w1, w2, w3, w4, w5, w6]
    overall_go = all(all_gates)

    reading: str
    if overall_go:
        reading = (
            "wall_confirmed: DR5 operates in code correctness verification. "
            "Realisation variability + placebo firings + overlap between "
            "placebo and realisation distributions -- exactly the DCR1f pattern "
            "on a completely different corpus."
        )
    elif w1 and w2 and w3 and w4 and not w5 and not w6:
        reading = (
            "no_projection_observed: verifier scored placebos cleanly. DR5 "
            "still holds but this specific verifier is above the wall for this "
            "specific D. Try a harder D or a weaker verifier."
        )
    elif w1 and w2 and w3 and w4 and w5 and not w6:
        reading = (
            "projection_without_overlap: placebo firings exist but do not "
            "exceed any realisation score. Wall partially confirmed."
        )
    elif not w3:
        reading = (
            "verifier_saturated: scores too uniform across realisations. "
            "Try harder snippets or a stricter D."
        )
    elif not w2:
        reading = (
            "verifier_missed_D: realisation median below threshold. Prompt "
            "or D formulation failure; redraft."
        )
    else:
        reading = "mixed_or_inconclusive: see per-gate decisions"

    verdict: dict[str, Any] = {
        "kind": "dr6_verdict",
        "purpose": (
            "Empirical test of DR5's verification wall on code correctness. "
            "3 sandboxed verifier subagents score 5 realisations + 5 placebos "
            "of a naive-UTC datetime commitment."
        ),
        "target_commitment_D": (
            "This Python code implicitly assumes that all datetime values are "
            "timezone-naive and represent UTC."
        ),
        "n_snippets": len(SNIPPETS),
        "n_realisations": len(realisations),
        "n_placebos": len(placebos),
        "per_snippet": per_snippet,
        "summary": {
            "realisation_scores": realisation_scores,
            "realisation_median": realisation_median,
            "realisation_stdev": realisation_stdev,
            "realisation_min": min(realisation_scores),
            "realisation_max": max(realisation_scores),
            "placebo_scores": placebo_scores,
            "placebo_median": placebo_median,
            "placebo_max": max(placebo_scores),
            "overlap_gap_min_realisation_minus_max_placebo": (
                min(realisation_scores) - max(placebo_scores)
            ),
        },
        "gates": {
            "W1_verifier_completeness": {"decision": "GO" if w1 else "NO_GO"},
            "W2_realisation_median_gte_6": {
                "value": realisation_median,
                "threshold": 6,
                "decision": "GO" if w2 else "NO_GO",
            },
            "W3_realisation_variability_gte_1p5": {
                "value": realisation_stdev,
                "threshold": 1.5,
                "decision": "GO" if w3 else "NO_GO",
            },
            "W4_placebo_median_lte_3": {
                "value": placebo_median,
                "threshold": 3,
                "decision": "GO" if w4 else "NO_GO",
            },
            "W5_at_least_one_placebo_triggers": {
                "n_placebos_at_or_above_5": sum(1 for p in placebo_scores if p >= 5),
                "decision": "GO" if w5 else "NO_GO",
            },
            "W6_placebo_realisation_overlap": {
                "min_realisation": min(realisation_scores),
                "max_placebo": max(placebo_scores),
                "decision": "GO" if w6 else "NO_GO",
            },
        },
        "overall_decision": "GO" if overall_go else "NO_GO",
        "licensed_reading": reading,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
