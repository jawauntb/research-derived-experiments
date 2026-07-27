"""DR6c — regex verifier on the same D as DR6.

Scores every DR6 snippet under the regex verifier in ``regex_verifier.py``.
Applies the identical W1–W6 gate suite from DR6_PREREGISTRATION.md.
Deterministic; single-shot; no consensus needed since regex is a
function.

Run:
    uv run --no-sync python -m experiments.dr6_code_correctness_corollary.run_dr6c
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.dr6_code_correctness_corollary.regex_verifier import (
    NEGATIVE_PATTERNS,
    POSITIVE_PATTERNS,
    score_snippet,
)
from experiments.dr6_code_correctness_corollary.snippets import SNIPPETS


__all__ = ["main"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
VERDICT_PATH: Final[Path] = _PACKAGE / "results" / "dr6c_verdict.json"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DR6c regex verifier.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    per_snippet: dict[str, Any] = {}
    for snippet in SNIPPETS:
        score = score_snippet(snippet.code)
        per_snippet[snippet.snippet_id] = {
            "kind": snippet.kind,
            "surface_form": snippet.surface_form,
            "score": score,
        }

    realisations = [
        per_snippet[s.snippet_id]["score"]
        for s in SNIPPETS
        if s.kind == "realisation"
    ]
    placebos = [
        per_snippet[s.snippet_id]["score"] for s in SNIPPETS if s.kind == "placebo"
    ]

    w1 = True  # regex verifier is deterministic; completeness is by construction
    realisation_median = statistics.median(realisations)
    w2 = realisation_median >= 6
    realisation_stdev = statistics.stdev(realisations) if len(realisations) > 1 else 0.0
    w3 = realisation_stdev >= 1.5
    placebo_median = statistics.median(placebos)
    w4 = placebo_median <= 3
    w5 = any(p >= 5 for p in placebos)
    w6 = min(realisations) < max(placebos)

    all_gates = [w1, w2, w3, w4, w5, w6]
    overall_go = all(all_gates)

    reading: str
    if overall_go:
        reading = (
            "wall_confirmed_on_regex_verifier: DR5 wall present when (a) D has "
            "canonical form BUT (b) verifier is proposition-independent. "
            "Triangulates the DR6 result -- flipping only condition (b) flips "
            "the outcome, exactly as DR5's sharpened claim predicts."
        )
    elif w2 and not w3:
        reading = (
            "regex_uniform_or_flat: verifier fires on most or no realisations "
            "the same way; may indicate patterns too tight or snippets too "
            "clean. Report and stop."
        )
    elif w2 and w3 and w4 and not w5:
        reading = (
            "regex_narrow_but_no_projection: fires cleanly on realisations, "
            "rejects placebos. Same outcome as DR6 despite different verifier "
            "-- refutes the sharpened claim in the strong form."
        )
    elif not w2:
        reading = (
            "regex_missed_realisations: patterns too narrow; median realisation "
            "score below threshold."
        )
    else:
        reading = "mixed_or_inconclusive"

    verdict: dict[str, Any] = {
        "kind": "dr6c_verdict",
        "purpose": (
            "Same D and snippets as DR6, but a proposition-independent regex "
            "verifier. Tests DR5's condition (b): does flipping only the "
            "verifier from Claude to regex flip the wall from absent to "
            "present?"
        ),
        "target_commitment_D": (
            "This Python code implicitly assumes that all datetime values are "
            "timezone-naive and represent UTC."
        ),
        "verifier": {
            "kind": "regex",
            "positive_patterns": [p[0] for p in POSITIVE_PATTERNS],
            "negative_patterns": [p[0] for p in NEGATIVE_PATTERNS],
            "score_rule": (
                "+2 per positive pattern hit, -3 per negative pattern hit, "
                "clamped to [0, 10]"
            ),
        },
        "n_snippets": len(SNIPPETS),
        "n_realisations": len(realisations),
        "n_placebos": len(placebos),
        "per_snippet": per_snippet,
        "summary": {
            "realisation_scores": realisations,
            "realisation_median": realisation_median,
            "realisation_stdev": realisation_stdev,
            "realisation_min": min(realisations),
            "realisation_max": max(realisations),
            "placebo_scores": placebos,
            "placebo_median": placebo_median,
            "placebo_max": max(placebos),
            "overlap_gap_min_realisation_minus_max_placebo": (
                min(realisations) - max(placebos)
            ),
        },
        "gates": {
            "W1_verifier_completeness": {"decision": "GO"},
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
                "n_placebos_at_or_above_5": sum(1 for p in placebos if p >= 5),
                "decision": "GO" if w5 else "NO_GO",
            },
            "W6_placebo_realisation_overlap": {
                "min_realisation": min(realisations),
                "max_placebo": max(placebos),
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
