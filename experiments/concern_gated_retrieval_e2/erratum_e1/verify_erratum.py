"""Erratum E1 — reproduce the leak, then show the repair closes it.

Run:
    uv run --no-sync python -m experiments.concern_gated_retrieval_e2.erratum_e1.verify_erratum

Writes ``results/erratum_receipt.json``. Local CPU, seconds, no Modal.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable, Sequence

from experiments.concern_gated_retrieval_e2.wave0.template_split import TemplateBucket

from experiments.concern_gated_retrieval_e2.erratum_e1.inverted_signal_audit import (
    ORACLE_LEAK_THRESHOLD,
    audit_care_anchors,
    format_audit_table,
)
from experiments.concern_gated_retrieval_e2.erratum_e1.prior_repair import (
    DEFAULT_SUPPRESSED_SET_SIZE,
    repair_wrong_prior,
)


__all__ = ["main", "collect_families"]

ROOT = Path(__file__).resolve().parents[3]
RECEIPT_PATH = (
    ROOT
    / "experiments"
    / "concern_gated_retrieval_e2"
    / "erratum_e1"
    / "results"
    / "erratum_receipt.json"
)

N_EPISODES = 300
SEED_START = 100_000


def collect_families() -> list[tuple[str, Callable[[int], Any]]]:
    """Return ``(label, generate(seed))`` for every reachable frozen family."""
    from experiments.concern_gated_retrieval_e2.wave0.families import (
        delayed_commitments as w0_dc,
        maintenance_fault as w0_mf,
    )
    from experiments.concern_gated_retrieval_e2.wave1b.families import (
        delayed_commitments_v2 as w1_dc,
        maintenance_fault_v2 as w1_mf,
    )

    out: list[tuple[str, Callable[[int], Any]]] = []
    for label, mod in (
        ("wave0/delayed_commitments", w0_dc),
        ("wave0/maintenance_fault", w0_mf),
        ("wave1b/delayed_commitments_v2", w1_dc),
        ("wave1b/maintenance_fault_v2", w1_mf),
    ):
        out.append(
            (
                label,
                lambda s, m=mod: m.generate_episode(
                    seed=s, bucket=TemplateBucket.CALIBRATION
                ),
            )
        )
    return out


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify erratum E1.")
    parser.add_argument("--n-episodes", type=int, default=N_EPISODES)
    parser.add_argument("--k", type=int, default=DEFAULT_SUPPRESSED_SET_SIZE)
    parser.add_argument("--out", type=Path, default=RECEIPT_PATH)
    args = parser.parse_args(argv)

    seeds = range(SEED_START, SEED_START + args.n_episodes)
    rows: list[dict[str, Any]] = []
    before_rows = []
    after_rows = []

    for label, generate in collect_families():
        try:
            episodes = [generate(s) for s in seeds]
        except Exception as exc:  # pragma: no cover - family seed-range guards
            rows.append({"family": label, "skipped": f"{type(exc).__name__}: {exc}"})
            continue

        before = audit_care_anchors(episodes)
        repaired = [repair_wrong_prior(e, k=args.k) for e in episodes]
        after = audit_care_anchors(repaired)
        before_rows.append(before)
        after_rows.append(after)

        rows.append(
            {
                "family": label,
                "n_episodes": before.n_episodes,
                "before": {
                    "descending_hit_at_1": before.descending_hit_at_1,
                    "ascending_hit_at_1": before.ascending_hit_at_1,
                    "worst": before.worst,
                    "leaks": before.leaks,
                    "direction": before.direction,
                },
                "after_repair": {
                    "descending_hit_at_1": after.descending_hit_at_1,
                    "ascending_hit_at_1": after.ascending_hit_at_1,
                    "worst": after.worst,
                    "leaks": after.leaks,
                    "direction": after.direction,
                },
            }
        )

    scored = [r for r in rows if "skipped" not in r]
    receipt = {
        "kind": "cogr_erratum_e1_receipt",
        "leak_threshold": ORACLE_LEAK_THRESHOLD,
        "suppressed_set_size_k": args.k,
        "expected_post_repair_hit_at_1": 1.0 / args.k,
        "families": rows,
        "all_leaked_before": bool(scored) and all(r["before"]["leaks"] for r in scored),
        "none_leak_after": bool(scored)
        and not any(r["after_repair"]["leaks"] for r in scored),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    print("BEFORE repair (frozen families, unmodified):")
    print(format_audit_table(before_rows))
    print()
    print(f"AFTER repair (suppressed set k={args.k}):")
    print(format_audit_table(after_rows))
    print()
    print(f"all leaked before : {receipt['all_leaked_before']}")
    print(f"none leak after   : {receipt['none_leak_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
