"""DCR3e — post-hoc trajectory quantification of DCR3d's finding.

DCR3d showed the use/discussion ratio for T1 peaks at 1880 (4.5),
holds first place at 1897 (1.5), then drops to rank 2 at 1904 (1.25)
as precursors (Poincaré 1898, Larmor 1900, Lorentz 1904) start
discussing simultaneity. The intepretation was: deletability is a
build-up state that peaks before the deletion.

DCR3e formalises the trajectory measure and quantifies the drop
per class.

**Honest label: this is NOT a fresh preregistered test.** I already
have DCR3d's data across all three cuts. Any measure I define now on
that data is post-hoc fitting. DCR3e reports the drop analytically
so the trajectory finding has explicit numbers, but the "T1 wins"
outcome here cannot be counted as a preregistered success. For a
fresh preregistered test, see DCR4 (Einstein 1905 as oracle corpus).

Run:
    uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr3e
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final, Sequence


__all__ = ["main"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
DCR3D_VERDICT: Final[Path] = _PACKAGE / "results" / "dcr3d_verdict.json"
VERDICT_PATH: Final[Path] = _PACKAGE / "results" / "dcr3e_verdict.json"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DCR3e post-hoc trajectory quantification.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    dcr3d = json.loads(DCR3D_VERDICT.read_text())
    cuts = dcr3d["cuts"]

    #: ratio(C, year) for each C in {T1, T2, T3}
    ratios: dict[str, dict[str, float]] = {c: {} for c in ("T1", "T2", "T3")}
    for year_str, cut_data in cuts.items():
        for c, r in cut_data.get("ratios", {}).items():
            ratios[c][year_str] = r

    def drop(c: str, from_year: str, to_year: str) -> float:
        return ratios[c].get(from_year, 0.0) - ratios[c].get(to_year, 0.0)

    #: Three trajectory metrics.
    drop_1880_to_1904 = {c: drop(c, "1880", "1904") for c in ratios}
    drop_1897_to_1904 = {c: drop(c, "1897", "1904") for c in ratios}
    #: Larger drop means the commitment is being brought into discussion
    #: — its silent-load-bearing signal is fading. Under the interpretation
    #: DCR3d proposed, this is the deletability-transition signal.

    def rank_by(scores: dict[str, float]) -> list[dict[str, Any]]:
        ordered = sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
        return [{"class": k, "drop": v} for k, v in ordered]

    ranking_full = rank_by(drop_1880_to_1904)
    ranking_recent = rank_by(drop_1897_to_1904)

    t1_rank_full = next(
        (i + 1 for i, e in enumerate(ranking_full) if e["class"] == "T1"), -1
    )
    t1_rank_recent = next(
        (i + 1 for i, e in enumerate(ranking_recent) if e["class"] == "T1"), -1
    )

    verdict: dict[str, Any] = {
        "kind": "dcr3e_verdict",
        "honest_status": (
            "POST-HOC: DCR3e is an analytic quantification of DCR3d's "
            "trajectory finding, not a fresh preregistered test. The scoring "
            "rule was chosen AFTER seeing DCR3d's cross-cut ratios. Any 'GO' "
            "outcome here cannot be counted as an independent empirical "
            "success. DCR4 (Einstein 1905 as oracle) is the preregistered "
            "companion for actual falsification."
        ),
        "purpose": (
            "Quantify DCR3d's trajectory finding: measure the DROP in each "
            "class's use/discussion ratio across the three cuts. Under DCR3d's "
            "interpretation, the class with the largest drop is the one being "
            "brought into discussion — the deletability-transition signal."
        ),
        "ratios_per_cut": ratios,
        "drop_1880_to_1904": drop_1880_to_1904,
        "drop_1897_to_1904": drop_1897_to_1904,
        "ranking_by_full_drop_1880_1904": ranking_full,
        "ranking_by_recent_drop_1897_1904": ranking_recent,
        "T1_rank_by_full_drop": t1_rank_full,
        "T1_rank_by_recent_drop": t1_rank_recent,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
