"""DR6g — Claude verifier fully domain-blind.

Prompt says only 'any implicit assumption about how the world works'
with no mention of date/time. Extreme end of DR6f's semantic-access
gradient. Predicts wall substantially returns.
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
VERDICT_PATH: Final[Path] = RESULTS_DIR / "dr6g_verdict.json"

VERIFIER_FILES: Final[tuple[str, ...]] = (
    "verifier_full_blind_A.json",
    "verifier_full_blind_B.json",
    "verifier_full_blind_C.json",
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DR6g scoring.")
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

    #: DR6g gate: further degradation vs DR6f baseline (median 9.0, gap 6, R6 8).
    g1 = r_median < 9
    g2 = overlap_gap < 6
    g3 = r6_score < 8
    g4 = min(realisations) <= max(placebos)  # direct wall

    overall_go = g4 or (g1 and g2 and g3)

    if g4:
        reading = (
            "wall_present_full_blind: fully domain-blind Claude produced "
            "realisation-placebo overlap. Semantic escape requires "
            "domain-relevance in the prompt, not just LLM reasoning."
        )
    elif overall_go:
        reading = (
            "further_degradation_vs_DR6f: fully domain-blind prompt reduced "
            "discrimination further than the D-adjacent DR6f prompt. Gradient "
            "continues; extreme end confirms D-relevance is load-bearing."
        )
    else:
        reading = (
            "domain_blind_still_discriminates: Claude preserved discrimination "
            "even without domain framing. LLM verifier is doing more than "
            "semantic reasoning about D — possibly recognising implicit-vs-"
            "explicit style as a domain-independent signal."
        )

    verdict: dict[str, Any] = {
        "kind": "dr6g_verdict",
        "purpose": "Fully domain-blind Claude verifier — extreme end of semantic-access gradient.",
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
        "gradient_comparison": {
            "DR6e_D_specified": {"r_median": 9.5, "overlap_gap": 7, "R6": 10},
            "DR6f_D_adjacent": {"r_median": 9.0, "overlap_gap": 6, "R6": 8},
            "DR6g_domain_blind": {
                "r_median": r_median, "overlap_gap": overlap_gap, "R6": r6_score
            },
        },
        "gates": {
            "G1_median_below_DR6f": {"value": r_median, "decision": "GO" if g1 else "NO_GO"},
            "G2_gap_below_DR6f": {"value": overlap_gap, "decision": "GO" if g2 else "NO_GO"},
            "G3_R6_below_DR6f": {"value": r6_score, "decision": "GO" if g3 else "NO_GO"},
            "G4_wall_direct": {
                "min_r": min(realisations),
                "max_p": max(placebos),
                "decision": "GO" if g4 else "NO_GO",
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
