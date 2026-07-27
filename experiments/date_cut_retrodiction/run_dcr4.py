"""DCR4 — Einstein 1905 as oracle corpus for the trajectory finding.

Preregistered in DCR4_PREREGISTRATION.md. Tests whether Einstein 1905
shows the discussion spike DCR3d predicted: T1 discussed a lot, T1
discussed more than T2, T1 discussion count higher than 1904 pre-cut,
T1 use/discussion ratio lower than any pre-cut year.

Extraction: three sandboxed subagents with the DCR1e presupposition
prompt, output cached under `extractions_einstein1905_pass{1,2,3}/`.
Consensus: 2-of-3 via `consensus.py`.

Tagging (use + discussion): three verifiers per phase with the DCR3c
and DCR3d prompts respectively. Consensus 2-of-3 per proposition, per
category. Prompt SHA-256 pinned identically to DCR3c/DCR3d — no new
prompts are introduced.

Run:
    uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr4
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.date_cut_retrodiction.consensus import build_consensus
from experiments.date_cut_retrodiction.run_dcr3d import (
    CLASS_KEYS,
    VERIFIER_IDS,
    _consensus_tags,
    _load_verifier_outputs,
    _proposition_id,
)


__all__ = ["main"]


_PACKAGE: Final[Path] = Path(__file__).resolve().parent

PASS_DIRS: Final[tuple[Path, ...]] = (
    _PACKAGE / "extractions_einstein1905_pass1",
    _PACKAGE / "extractions_einstein1905_pass2",
    _PACKAGE / "extractions_einstein1905_pass3",
)
CONSENSUS_DIR: Final[Path] = _PACKAGE / "extractions_einstein1905_consensus"
DCR4_DIR: Final[Path] = _PACKAGE / "results" / "dcr4"

VERDICT_PATH: Final[Path] = _PACKAGE / "results" / "dcr4_verdict.json"
DCR3D_VERDICT: Final[Path] = _PACKAGE / "results" / "dcr3d_verdict.json"

USE_PROMPT_PATH: Final[Path] = _PACKAGE / "EXTRACTION_PROMPT_PRESUPPOSITION.md"
DISC_PROMPT_PATH: Final[Path] = _PACKAGE / "DCR3D_PROMPT.md"

MIN_EXTRACTION_COUNT: Final[int] = 15
YEAR: Final[int] = 1905

TAGGER_INPUT: Final[Path] = DCR4_DIR / "tagger_input_einstein_1905.json"


def write_tagger_input() -> Path:
    """Dump consensus propositions to a tagger-ready JSON file.

    Called between extraction and tagging. Each tagger reads this file
    to see the id/statement/quote/kind of every proposition it needs
    to tag.
    """
    consensus_file = CONSENSUS_DIR / "einstein_1905.json"
    if not consensus_file.is_file():
        raise SystemExit(f"missing consensus file: {consensus_file}")
    data = json.loads(consensus_file.read_text())
    propositions = data.get("propositions", [])

    entries = []
    for p in propositions:
        entries.append({
            "id": _proposition_id(p),
            "statement": p.get("statement", ""),
            "quote": p.get("quote", ""),
            "kind": p.get("kind", ""),
        })

    payload = {
        "doc_id": "einstein_1905",
        "cut_year": YEAR,
        "propositions": entries,
    }
    TAGGER_INPUT.parent.mkdir(parents=True, exist_ok=True)
    TAGGER_INPUT.write_text(json.dumps(payload, indent=2) + "\n")
    return TAGGER_INPUT


def _score_einstein_1905() -> dict[str, Any]:
    """Load consensus propositions + verifier tags and compute counts."""
    consensus_file = CONSENSUS_DIR / "einstein_1905.json"
    if not consensus_file.is_file():
        raise SystemExit(f"missing consensus file: {consensus_file}")
    data = json.loads(consensus_file.read_text())
    propositions = data.get("propositions", [])

    use_verifier = _load_verifier_outputs(DCR4_DIR, "inferred", YEAR)
    use_tags = _consensus_tags(
        use_verifier, "required_categories", prediction_field="is_prediction"
    )

    disc_verifier = _load_verifier_outputs(DCR4_DIR, "discussion", YEAR)
    disc_tags = _consensus_tags(disc_verifier, "discussed_categories")

    use_count: dict[str, int] = {c: 0 for c in CLASS_KEYS}
    discussion_count: dict[str, int] = {c: 0 for c in CLASS_KEYS}

    for p in propositions:
        pid = _proposition_id(p)
        u_tags, is_pred = use_tags.get(pid, ((), False))
        d_tags, _ = disc_tags.get(pid, ((), False))
        if is_pred:
            for c in u_tags:
                use_count[c] += 1
        for c in d_tags:
            discussion_count[c] += 1

    ratios: dict[str, float] = {
        c: use_count[c] / (discussion_count[c] + 1) for c in CLASS_KEYS
    }

    return {
        "n_propositions": len(propositions),
        "use_count": use_count,
        "discussion_count": discussion_count,
        "ratios": ratios,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DCR4 Einstein 1905 oracle test.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    parser.add_argument("--skip-consensus", action="store_true")
    args = parser.parse_args(argv)

    if not args.skip_consensus:
        consensus, _ = build_consensus(PASS_DIRS, support_threshold=2)
        CONSENSUS_DIR.mkdir(parents=True, exist_ok=True)
        for doc_id, propositions in consensus.items():
            out = CONSENSUS_DIR / f"{doc_id}.json"
            out.write_text(
                json.dumps(
                    {
                        "doc_id": doc_id,
                        "propositions": [p.as_dict() for p in propositions],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

    einstein = _score_einstein_1905()

    dcr3d = json.loads(DCR3D_VERDICT.read_text())
    cut_1904 = dcr3d["cuts"]["1904"]
    cuts = dcr3d["cuts"]

    t1_disc_1904 = int(cut_1904["discussion_count"]["T1"])
    t1_ratio_1880 = float(cuts["1880"]["ratios"]["T1"])
    t1_ratio_1897 = float(cuts["1897"]["ratios"]["T1"])
    t1_ratio_1904 = float(cuts["1904"]["ratios"]["T1"])
    pre_cut_min_t1_ratio = min(t1_ratio_1880, t1_ratio_1897, t1_ratio_1904)

    q1 = einstein["n_propositions"] >= MIN_EXTRACTION_COUNT
    q2 = einstein["discussion_count"]["T1"] > einstein["discussion_count"]["T2"]
    q3 = einstein["discussion_count"]["T1"] > t1_disc_1904
    q4 = einstein["ratios"]["T1"] < pre_cut_min_t1_ratio

    overall_go = q1 and q2 and q3 and q4

    if overall_go:
        reading = (
            "trajectory_confirmed_on_einstein_1905: T1 is the dominant "
            "discussed commitment in Einstein 1905, discussion count spikes "
            "above the 1904 pre-cut level, and the use/discussion ratio "
            "collapses below every pre-cut year. Consistent with DCR3d's "
            "trajectory interpretation."
        )
    elif not q2:
        reading = (
            "t1_not_dominant_in_einstein_1905: Einstein's paper does not "
            "discuss T1 more than T2 under our consensus tagging. Would "
            "falsify the trajectory framing's specific prediction that "
            "Einstein's move IS the T1 discussion spike."
        )
    elif not q3:
        reading = (
            "no_t1_discussion_spike: T1 discussion count in Einstein 1905 "
            "does not exceed the 1904 pre-cut level. Trajectory framing "
            "weakened."
        )
    elif not q4:
        reading = (
            "t1_ratio_did_not_collapse: T1 ratio in Einstein 1905 is at or "
            "above the pre-cut minimum. Einstein discussed T1 but also used "
            "it heavily — nuanced finding."
        )
    else:
        reading = "extraction_failed_q1"

    verdict: dict[str, Any] = {
        "kind": "dcr4_verdict",
        "purpose": (
            "Fresh preregistered test of DCR3d's trajectory interpretation: "
            "does Einstein 1905 show the T1 discussion spike DCR3d "
            "predicted the deletion cut should show?"
        ),
        "prompt_sha256": {
            "extraction": hashlib.sha256(USE_PROMPT_PATH.read_bytes()).hexdigest(),
            "discussion": hashlib.sha256(DISC_PROMPT_PATH.read_bytes()).hexdigest(),
        },
        "verifiers": list(VERIFIER_IDS),
        "einstein_1905": einstein,
        "pre_cut_reference": {
            "T1_discussion_count_1904": t1_disc_1904,
            "T1_ratio_1880": t1_ratio_1880,
            "T1_ratio_1897": t1_ratio_1897,
            "T1_ratio_1904": t1_ratio_1904,
            "min_pre_cut_T1_ratio": pre_cut_min_t1_ratio,
        },
        "gates": {
            "Q1_extraction_sanity": {
                "n_propositions": einstein["n_propositions"],
                "threshold": MIN_EXTRACTION_COUNT,
                "decision": "GO" if q1 else "NO_GO",
            },
            "Q2_T1_dominates_discussion": {
                "T1_discussion": einstein["discussion_count"]["T1"],
                "T2_discussion": einstein["discussion_count"]["T2"],
                "decision": "GO" if q2 else "NO_GO",
            },
            "Q3_T1_discussion_spike": {
                "einstein_T1_disc": einstein["discussion_count"]["T1"],
                "pre_cut_1904_T1_disc": t1_disc_1904,
                "decision": "GO" if q3 else "NO_GO",
            },
            "Q4_ratio_inversion": {
                "einstein_T1_ratio": einstein["ratios"]["T1"],
                "min_pre_cut_T1_ratio": pre_cut_min_t1_ratio,
                "decision": "GO" if q4 else "NO_GO",
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
