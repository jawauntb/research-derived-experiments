"""DR6f — Claude verifier with D withheld from prompt.

Tests DR5's condition (b) sharpness: is knowing D load-bearing for the
semantic-reasoning escape route? Prediction: wall reappears when D is
not stated.
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
VERDICT_PATH: Final[Path] = RESULTS_DIR / "dr6f_verdict.json"

VERIFIER_FILES: Final[tuple[str, ...]] = (
    "verifier_blind_A.json",
    "verifier_blind_B.json",
    "verifier_blind_C.json",
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DR6f scoring.")
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

    r_median = statistics.median(realisations)
    p_median = statistics.median(placebos)
    overlap_gap = min(realisations) - max(placebos)
    r6_score = per_snippet[R6_NOVEL.snippet_id]["consensus"]

    #: DR6f-specific gates.
    #: F1 -- D-withholding reduces realisation median relative to DR6e (9.5).
    f1 = r_median < 9
    #: F2 -- overlap-gap is smaller than DR6e's +7.
    f2 = overlap_gap < 7
    #: F3 -- R6 score falls below its DR6e level (10).
    f3 = r6_score < 10
    #: F4 -- wall present: any realisation scores at or below any placebo.
    f4 = min(realisations) <= max(placebos)

    #: Overall GO on DR6f question: wall reappeared when D was withheld.
    #: Requires either F4 directly (overlap) or F1+F2+F3 (degradation
    #: without full overlap yet).
    overall_go = f4 or (f1 and f2 and f3)

    reading: str
    if f4:
        reading = (
            "wall_reappeared_direct: withholding D from the prompt "
            "produced realisation-placebo overlap. Confirms sharpened DR5 "
            "condition (b): semantic escape requires D-knowledge, not "
            "just LLM verification generally."
        )
    elif overall_go:
        reading = (
            "wall_reappeared_by_degradation: withholding D reduced "
            "realisation-placebo separation across every measure, though "
            "no direct overlap. Directional confirmation of DR5's D-"
            "knowledge requirement."
        )
    else:
        reading = (
            "no_wall_without_D: Claude preserved discrimination even "
            "without D in the prompt. Semantic escape may be more general "
            "than DR5 originally required -- possibly relying on stylistic "
            "or structural cues correlated with D."
        )

    verdict: dict[str, Any] = {
        "kind": "dr6f_verdict",
        "purpose": "Test whether D-knowledge is load-bearing for LLM semantic escape",
        "n_snippets": len(snippets),
        "per_snippet": per_snippet,
        "summary": {
            "realisation_scores": realisations,
            "realisation_median": r_median,
            "R6_score": r6_score,
            "placebo_scores": placebos,
            "placebo_median": p_median,
            "placebo_max": max(placebos),
            "overlap_gap": overlap_gap,
        },
        "dr6e_comparison": {
            "dr6e_realisation_median": 9.5,
            "dr6e_R6_score": 10,
            "dr6e_overlap_gap": 7,
        },
        "gates": {
            "F1_realisation_median_dropped": {
                "value": r_median,
                "dr6e_value": 9.5,
                "decision": "GO" if f1 else "NO_GO",
            },
            "F2_overlap_gap_reduced": {
                "value": overlap_gap,
                "dr6e_value": 7,
                "decision": "GO" if f2 else "NO_GO",
            },
            "F3_R6_score_reduced": {
                "value": r6_score,
                "dr6e_value": 10,
                "decision": "GO" if f3 else "NO_GO",
            },
            "F4_wall_present_direct": {
                "min_realisation": min(realisations),
                "max_placebo": max(placebos),
                "decision": "GO" if f4 else "NO_GO",
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
