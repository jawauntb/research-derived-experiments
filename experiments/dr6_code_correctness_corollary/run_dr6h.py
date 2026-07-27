"""DR6h — target without a domain-general proxy."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.dr6_code_correctness_corollary.snippets_h import SNIPPETS_H


__all__ = ["main"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
RESULTS_DIR: Final[Path] = _PACKAGE / "results"
VERDICT_PATH: Final[Path] = RESULTS_DIR / "dr6h_verdict.json"

VERIFIER_FILES: Final[tuple[str, ...]] = (
    "verifier_h_A.json",
    "verifier_h_B.json",
    "verifier_h_C.json",
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DR6h scoring.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    verifiers: list[dict[str, Any]] = []
    for name in VERIFIER_FILES:
        path = RESULTS_DIR / name
        if not path.is_file():
            raise SystemExit(f"missing verifier output: {path}")
        verifiers.append(json.loads(path.read_text(encoding="utf-8")))

    per_snippet: dict[str, Any] = {}
    for snippet in SNIPPETS_H:
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
        for s in SNIPPETS_H
        if s.kind == "realisation"
    ]
    placebos = [
        per_snippet[s.snippet_id]["consensus"]
        for s in SNIPPETS_H
        if s.kind == "placebo"
    ]

    r_median = statistics.median(realisations)
    r_stdev = statistics.stdev(realisations) if len(realisations) > 1 else 0.0
    p_median = statistics.median(placebos)
    overlap_gap = min(realisations) - max(placebos)

    w2 = r_median >= 6
    w3 = r_stdev >= 1.5
    w4 = p_median <= 3
    w5 = any(p >= 5 for p in placebos)
    w6 = min(realisations) <= max(placebos)

    #: DR6h "wall bites" verdict.
    overall_go = w6 or (w5 and (r_median - p_median < 5))

    if w6:
        reading = (
            "wall_bites_direct: min realisation scored at or below max "
            "placebo. DR5* confirmed: target without domain-general proxy "
            "hits the wall for LLM verifier even with D specified."
        )
    elif w5:
        reading = (
            "wall_bites_partial: at least one placebo triggered (>= 5), "
            "reduced separation. Directional confirmation of DR5*."
        )
    else:
        reading = (
            "clean_discrimination_despite_no_obvious_proxy: LLM semantic "
            "reasoning succeeded even without an obvious implicit-vs-"
            "explicit proxy. DR5* is refuted for this target; some deeper "
            "reasoning about the code's SEMANTIC intent is happening."
        )

    verdict: dict[str, Any] = {
        "kind": "dr6h_verdict",
        "purpose": (
            "Test DR5*'s prediction that targets without domain-general "
            "proxies hit the wall for LLM verifiers even with D specified."
        ),
        "target_D_h": (
            "This code assumes exclusive access to files it reads or writes."
        ),
        "n_snippets": len(SNIPPETS_H),
        "per_snippet": per_snippet,
        "summary": {
            "realisation_scores": realisations,
            "realisation_median": r_median,
            "realisation_stdev": r_stdev,
            "placebo_scores": placebos,
            "placebo_median": p_median,
            "placebo_max": max(placebos),
            "overlap_gap": overlap_gap,
        },
        "gates": {
            "W1": {"decision": "GO"},
            "W2_realisation_median": {"value": r_median, "decision": "GO" if w2 else "NO_GO"},
            "W3_stdev": {"value": r_stdev, "decision": "GO" if w3 else "NO_GO"},
            "W4_placebo_median": {"value": p_median, "decision": "GO" if w4 else "NO_GO"},
            "W5_placebo_trigger": {
                "n_placebos_ge_5": sum(1 for p in placebos if p >= 5),
                "decision": "GO" if w5 else "NO_GO",
            },
            "W6_direct_overlap": {
                "min_r": min(realisations),
                "max_p": max(placebos),
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
