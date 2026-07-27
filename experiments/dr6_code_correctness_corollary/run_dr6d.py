"""DR6d — regex verifier on an extended snippet set with one novel realisation.

Adds a sixth realisation, ``R6_json_field_no_tz``, whose surface form is
not present in the DR6c regex verifier's pattern list. Runs the
unchanged ``regex_verifier.py`` against the extended set; predicts (per
DR6D_PREREGISTRATION.md §1) that R6 scores 0 while R1-R5 score 2 each,
directly triggering W6 (realisation-placebo overlap).

Run:
    uv run --no-sync python -m experiments.dr6_code_correctness_corollary.run_dr6d
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.dr6_code_correctness_corollary.regex_verifier import score_snippet
from experiments.dr6_code_correctness_corollary.snippets import SNIPPETS, Snippet


__all__ = ["main", "R6_NOVEL"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
VERDICT_PATH: Final[Path] = _PACKAGE / "results" / "dr6d_verdict.json"


#: The novel realisation. Drafted from the surface-form label
#: "parses a datetime from a JSON field that lacks any timezone
#: information" WITHOUT looking at the regex verifier's patterns. The
#: helper constructs the datetime via `datetime(year, month, ...)` from
#: parsed integers rather than through any of the paths the regex covers.
R6_NOVEL: Final[Snippet] = Snippet(
    snippet_id="R6_json_field_no_tz",
    kind="realisation",
    surface_form="datetime from JSON dict integer fields, no tz",
    code="""\
from datetime import datetime


def load_event(payload: dict) -> datetime:
    \"\"\"Reconstruct an event datetime from a JSON dict of integer fields.

    Callers rely on a fleet-wide convention that all such payloads are
    already in UTC, so the resulting datetime is intentionally naive.
    \"\"\"
    ts = payload["created_at"]
    return datetime(
        year=ts["year"],
        month=ts["month"],
        day=ts["day"],
        hour=ts["hour"],
        minute=ts["minute"],
        second=ts["second"],
    )


def is_before_boundary(payload: dict, boundary: datetime) -> bool:
    return load_event(payload) < boundary
""",
)


def _extended_snippets() -> tuple[Snippet, ...]:
    return SNIPPETS + (R6_NOVEL,)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DR6d with novel realisation.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    snippets = _extended_snippets()
    per_snippet: dict[str, Any] = {}
    for snippet in snippets:
        score = score_snippet(snippet.code)
        per_snippet[snippet.snippet_id] = {
            "kind": snippet.kind,
            "surface_form": snippet.surface_form,
            "score": score,
        }

    realisations = [
        per_snippet[s.snippet_id]["score"] for s in snippets if s.kind == "realisation"
    ]
    placebos = [
        per_snippet[s.snippet_id]["score"] for s in snippets if s.kind == "placebo"
    ]

    r6_score = per_snippet[R6_NOVEL.snippet_id]["score"]

    u6 = r6_score == 0
    realisation_median = statistics.median(realisations)
    w2 = realisation_median >= 6
    realisation_stdev = statistics.stdev(realisations) if len(realisations) > 1 else 0.0
    w3 = realisation_stdev >= 1.5
    placebo_median = statistics.median(placebos)
    w4 = placebo_median <= 3
    w5 = any(p >= 5 for p in placebos)
    #: W6 -- ANY realisation scores <= max(placebo).  This is the wall.
    w6 = min(realisations) <= max(placebos)

    if u6 and w6:
        reading = (
            "wall_present_on_open_enumeration: DR5 directly confirmed. Regex "
            "verifier caught the 5 enumerated realisations but missed the 6th "
            "novel one, and the 6th realisation scored at or below every "
            "placebo. Exactly the DCR1f pattern replayed on code correctness."
        )
    elif not u6:
        reading = (
            "regex_caught_R6: the novel realisation was not novel enough. "
            "R6 must be redrafted so it embodies D without matching any of "
            "the 5 patterns the regex has."
        )
    else:
        reading = "mixed_or_inconclusive"

    verdict: dict[str, Any] = {
        "kind": "dr6d_verdict",
        "purpose": (
            "Extend DR6c's snippet set with one novel realisation the regex "
            "was not designed for. Test whether the DR5 wall now bites."
        ),
        "target_commitment_D": (
            "This Python code implicitly assumes that all datetime values are "
            "timezone-naive and represent UTC."
        ),
        "n_snippets": len(snippets),
        "novel_realisation_id": R6_NOVEL.snippet_id,
        "per_snippet": per_snippet,
        "summary": {
            "realisation_scores": realisations,
            "realisation_median": realisation_median,
            "realisation_stdev": realisation_stdev,
            "realisation_min": min(realisations),
            "R6_novel_score": r6_score,
            "placebo_scores": placebos,
            "placebo_max": max(placebos),
            "overlap_gap_min_realisation_minus_max_placebo": (
                min(realisations) - max(placebos)
            ),
        },
        "gates": {
            "U6_regex_missed_novel_realisation": {
                "R6_score": r6_score,
                "decision": "GO" if u6 else "NO_GO",
            },
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
        #: Overall verdict is on the DR6d question: does the wall bite when
        #: the realisation set becomes open-ended? U6 + W6 = wall present.
        "overall_decision": "GO" if (u6 and w6) else "NO_GO",
        "licensed_reading": reading,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
