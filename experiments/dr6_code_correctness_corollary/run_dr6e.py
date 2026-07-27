"""DR6e — Claude verifier on DR6d's extended snippet set.

Reads verifier_ext_A/B/C.json from the results directory. Aggregates by
median. Predicted: Claude catches R6 semantically, wall stays absent
even under open enumeration. If R6 scores low, sharpened DR5 is falsified.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.dr6_code_correctness_corollary.run_dr6d import R6_NOVEL
from experiments.dr6_code_correctness_corollary.snippets import SNIPPETS


__all__ = ["main"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
RESULTS_DIR: Final[Path] = _PACKAGE / "results"
VERDICT_PATH: Final[Path] = RESULTS_DIR / "dr6e_verdict.json"

VERIFIER_FILES: Final[tuple[str, ...]] = (
    "verifier_ext_A.json",
    "verifier_ext_B.json",
    "verifier_ext_C.json",
)

U6E_MIN_R6_SCORE: Final[int] = 6


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DR6e scoring.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    verifiers: list[dict[str, Any]] = []
    for name in VERIFIER_FILES:
        path = RESULTS_DIR / name
        if not path.is_file():
            raise SystemExit(f"missing verifier output: {path}")
        verifiers.append(json.loads(path.read_text(encoding="utf-8")))

    snippets = list(SNIPPETS) + [R6_NOVEL]
    per_snippet: dict[str, Any] = {}
    for snippet in snippets:
        per_verifier = [int(v["scores"][snippet.snippet_id]) for v in verifiers]
        consensus = int(round(statistics.median(per_verifier)))
        per_snippet[snippet.snippet_id] = {
            "kind": snippet.kind,
            "surface_form": snippet.surface_form,
            "per_verifier": per_verifier,
            "consensus": consensus,
            "verifier_stdev": statistics.stdev(per_verifier) if len(per_verifier) > 1 else 0.0,
        }

    realisations = [
        per_snippet[s.snippet_id]["consensus"]
        for s in snippets
        if s.kind == "realisation"
    ]
    placebos = [
        per_snippet[s.snippet_id]["consensus"]
        for s in snippets
        if s.kind == "placebo"
    ]
    r6_consensus = per_snippet[R6_NOVEL.snippet_id]["consensus"]

    u6e = r6_consensus >= U6E_MIN_R6_SCORE
    realisation_median = statistics.median(realisations)
    realisation_stdev = statistics.stdev(realisations) if len(realisations) > 1 else 0.0
    placebo_median = statistics.median(placebos)

    w1 = True
    w2 = realisation_median >= 6
    w3 = realisation_stdev >= 1.5
    w4 = placebo_median <= 3
    w5 = any(p >= 5 for p in placebos)
    w6 = min(realisations) <= max(placebos)

    if u6e and not w6:
        reading = (
            "wall_absent_under_open_enumeration_with_semantic_reasoning: "
            "sharpened DR5 confirmed on the (a)-open, (b)-satisfied corner. "
            "Claude caught R6 semantically. Escape via condition (b) is real."
        )
    elif not u6e and w6:
        reading = (
            "wall_present_even_with_Claude: sharpened DR5 falsified. Claude "
            "missed R6 despite semantic-reasoning availability. Refine claim: "
            "semantic reasoning is not sufficient in this case."
        )
    elif not u6e:
        reading = "R6_missed_but_no_overlap: Claude scored R6 low but placebos still lower"
    else:
        reading = "mixed"

    verdict: dict[str, Any] = {
        "kind": "dr6e_verdict",
        "purpose": (
            "Claude verifier on DR6d's extended set (11 snippets). Tests "
            "whether semantic reasoning escapes the wall under open "
            "enumeration."
        ),
        "n_snippets": len(snippets),
        "per_snippet": per_snippet,
        "summary": {
            "realisation_scores": realisations,
            "realisation_median": realisation_median,
            "realisation_stdev": realisation_stdev,
            "realisation_min": min(realisations),
            "R6_consensus": r6_consensus,
            "placebo_scores": placebos,
            "placebo_max": max(placebos),
            "overlap_gap": min(realisations) - max(placebos),
        },
        "gates": {
            "U6e_R6_caught_semantically": {
                "R6_consensus": r6_consensus,
                "threshold": U6E_MIN_R6_SCORE,
                "decision": "GO" if u6e else "NO_GO",
            },
            "W1": {"decision": "GO" if w1 else "NO_GO"},
            "W2_realisation_median_gte_6": {
                "value": realisation_median,
                "decision": "GO" if w2 else "NO_GO",
            },
            "W3_stdev_gte_1p5": {
                "value": realisation_stdev,
                "decision": "GO" if w3 else "NO_GO",
            },
            "W4_placebo_median_lte_3": {
                "value": placebo_median,
                "decision": "GO" if w4 else "NO_GO",
            },
            "W5_placebo_trigger": {"decision": "GO" if w5 else "NO_GO"},
            "W6_overlap": {
                "min_realisation": min(realisations),
                "max_placebo": max(placebos),
                "decision": "GO" if w6 else "NO_GO",
            },
        },
        "overall_decision": "GO" if (u6e and not w6) else "NO_GO",
        "licensed_reading": reading,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
