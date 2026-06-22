#!/usr/bin/env python3
"""External Contact P2 — uncertainty != error on published ensemble / BALD curves.

Pre-registration: docs/external_contact_preregistration.md (Prediction 2).
This is the Tier-A harness: reads frozen transcribed public numbers from
`experiments/external_contact/p2_uncertainty_public.csv` (committed BEFORE the
check is run, per the shared anti-cheat discipline) and computes the
pre-registered P2a / P2b comparisons in pure Python standard library.

IMPORTANT -- this is INFRASTRUCTURE, not a result:

  * With `--csv PATH` it runs the real check against the committed transcribed
    numbers. The CSV is frozen-now.
  * With `--self-test` it runs the math on SYNTHETIC vectors with known
    structure purely to verify the Pearson r and paired-comparison logic. A
    self-test pass is NOT evidence for the P2 claim.
  * With neither, it prints its status and exits without producing any claim.

Honest caveat baked into the harness (not a post-hoc redefinition; verified
against the Ovadia 2019 appendix on 2026-06-22): Ovadia Table G.1 reports
quartile aggregates across all 80 corrupted CIFAR-10 variants and does NOT
publish per-corruption-severity tables. The literal pre-registered P2a
threshold "per-sample Pearson |r| <= 0.2 on shifted slices" is therefore
NOT directly checkable against the published tables. The harness reports the
strongest available published proxy (75th- vs 25th-percentile ECE ratio across
shifted variants, the aggregate signature of "calibration collapses under
shift") AND records the literal threshold as undecidable -- it does not
silently substitute one for the other.

Sources (all numbers in the CSV are publicly published; lab built none of them):

  * Ovadia et al. 2019, "Can You Trust Your Model's Uncertainty?"
    arXiv:1906.02530, Appendix G Table G.1 (CIFAR-10 corrupted, quartile
    aggregates over 80 shifted variants x 7 methods x 3 metrics).
  * Kirsch et al. 2019, "BatchBALD: Efficient and Diverse Batch Acquisition
    for Deep Bayesian Active Learning." arXiv:1906.08158, Table 1
    (MNIST labels-to-target-accuracy) and Section 4 (CINIC-10 transfer).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean


# ----------------------------- stats (stdlib) -----------------------------
def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else 0.0


# ----------------------------- csv io -----------------------------
def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ----------------------------- P2a: cifar-10-c quartile aggregate proxy -----------------------------
def p2a_aggregate(rows: list[dict]) -> dict:
    """Aggregate ECE / Brier quartiles per method, with q75/q25 spread ratio.

    Original frozen P2a wants per-sample Pearson |r| <= 0.2 on shifted slices.
    Ovadia 2019 Table G.1 does NOT publish that statistic; it reports quartiles
    across 80 shifted variants. The 75th- vs 25th-percentile spread is the
    closest published proxy for "calibration collapses under shift" -- the
    aggregate signature of "uncertainty stops tracking error". We report the
    proxy but DO NOT claim it resolves the literal P2a threshold.
    """
    cifar = [r for r in rows if r["kind"] == "cifar10c_quartile"]
    grouped: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for r in cifar:
        grouped[(r["system"], r["metric"])][r["slice_or_target"]] = float(r["value"])

    summary = {}
    for (system, metric), quart in grouped.items():
        q25 = quart.get("q25")
        q50 = quart.get("q50")
        q75 = quart.get("q75")
        if q25 is None or q75 is None:
            continue
        ratio = (q75 / q25) if q25 > 0 else float("inf")
        summary[f"{system}|{metric}"] = {
            "q25": q25,
            "q50": q50,
            "q75": q75,
            "q75_over_q25": ratio,
        }
    return summary


# ----------------------------- P2b: bald labels-to-target -----------------------------
def p2b_pairs(rows: list[dict]) -> dict:
    bald = [r for r in rows if r["kind"] == "bald_labels_to_target"]
    grouped: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for r in bald:
        grouped[(r["dataset"], r["slice_or_target"])][r["system"]] = float(r["value"])

    out = {}
    for (dataset, target), methods in grouped.items():
        bb = methods.get("batchbald")
        if bb is None:
            continue
        for naive_key in ("bald_reimpl", "bald_gal_2017", "bald_median"):
            naive = methods.get(naive_key)
            if naive is None:
                continue
            gap_labels = naive - bb
            gap_frac = (gap_labels / naive) if naive else 0.0
            out[f"{dataset}|{target}|batchbald_vs_{naive_key}"] = {
                "batchbald_labels": bb,
                "naive_labels": naive,
                "gap_labels": gap_labels,
                "gap_fraction": gap_frac,
                "batchbald_beats_naive": gap_labels > 0,
            }
        # Also compare BatchBALD vs random when present.
        rnd = methods.get("random")
        if rnd is not None:
            out[f"{dataset}|{target}|batchbald_vs_random"] = {
                "batchbald_labels": bb,
                "naive_labels": rnd,
                "gap_labels": rnd - bb,
                "gap_fraction": (rnd - bb) / rnd if rnd else 0.0,
                "batchbald_beats_random": rnd - bb > 0,
            }
    return out


# ----------------------------- self-test (synthetic) -----------------------------
def self_test() -> dict:
    """Validate the math on synthetic data. NOT a scientific result.

    Builds three (uncertainty, error) sample sets: one positively correlated
    ("in-distribution" -- uncertainty tracks error), one near-zero correlated
    ("under shift" -- the predicted P2a collapse), and one negatively
    correlated ("false calm" extreme -- variance is anti-correlated with
    error). Verifies Pearson r recovers these.
    """
    rng = random.Random(20260622)
    n = 200
    xs = [rng.gauss(0.0, 1.0) for _ in range(n)]
    ys_in_dist = [x + rng.gauss(0.0, 0.4) for x in xs]
    ys_under_shift = [rng.gauss(0.0, 1.0) for _ in range(n)]
    ys_false_calm = [-x + rng.gauss(0.0, 0.5) for x in xs]

    r_in = pearson(xs, ys_in_dist)
    r_shift = pearson(xs, ys_under_shift)
    r_fc = pearson(xs, ys_false_calm)

    # Also exercise the P2b pairing logic on synthetic rows.
    fake_rows = [
        {"kind": "bald_labels_to_target", "source": "synth", "system": "batchbald",
         "dataset": "synth", "slice_or_target": "acc_0.90", "metric": "labels",
         "value": "100", "citation": "self_test", "note": "synthetic"},
        {"kind": "bald_labels_to_target", "source": "synth", "system": "bald_reimpl",
         "dataset": "synth", "slice_or_target": "acc_0.90", "metric": "labels",
         "value": "150", "citation": "self_test", "note": "synthetic"},
    ]
    p2b = p2b_pairs(fake_rows)
    pair_key = "synth|acc_0.90|batchbald_vs_bald_reimpl"

    checks = {
        "in_dist_corr_high": r_in > 0.6,
        "under_shift_corr_low": abs(r_shift) < 0.3,
        "false_calm_corr_negative": r_fc < -0.5,
        "p2b_pair_detects_batchbald_win": p2b.get(pair_key, {}).get("batchbald_beats_naive") is True,
        "p2b_gap_fraction_matches": abs(p2b.get(pair_key, {}).get("gap_fraction", 0) - 1.0 / 3.0) < 1e-9,
    }
    return {
        "kind": "SELF_TEST (synthetic, NOT a scientific result)",
        "pearson_in_dist": r_in,
        "pearson_under_shift": r_shift,
        "pearson_false_calm": r_fc,
        "p2b_pair_example": p2b.get(pair_key),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


# ----------------------------- real run -----------------------------
def run_check(csv_path: Path) -> dict:
    rows = read_csv(csv_path)

    p2a = p2a_aggregate(rows)
    p2b = p2b_pairs(rows)

    ens_ece = p2a.get("ensembles|ECE", {})
    van_ece = p2a.get("vanilla|ECE", {})

    p2a_verdict = {
        "literal_P2a_threshold": "per-sample Pearson |r| <= 0.2 on shifted CIFAR-10-C slices",
        "literal_P2a_pass": None,
        "literal_P2a_note": (
            "NOT checkable against published Ovadia 2019 tables. Per-sample "
            "variance-error correlation per corruption severity is not published "
            "(Table G.1 reports quartile aggregates across all 80 shifted variants; "
            "per-severity data appears only in figures). Tier-B (running deep "
            "ensembles on CIFAR-10-C and computing per-sample Pearson r ourselves, "
            "on Modal) is required to evaluate the literal threshold."
        ),
        "aggregate_proxy_threshold": (
            "Ensemble ECE 75th/25th percentile ratio >= 2.0 across shifted variants "
            "AND Ensemble ECE 75th percentile >= 0.05 (absolute miscalibration), "
            "with ensembles still the lowest-ECE method at every quartile "
            "(consistent with 'best uncertainty method still loses calibration "
            "under heavy shift')."
        ),
        "ensemble_ECE_q25": ens_ece.get("q25"),
        "ensemble_ECE_q50": ens_ece.get("q50"),
        "ensemble_ECE_q75": ens_ece.get("q75"),
        "ensemble_ECE_q75_over_q25": ens_ece.get("q75_over_q25"),
        "vanilla_ECE_q25": van_ece.get("q25"),
        "vanilla_ECE_q75": van_ece.get("q75"),
        "vanilla_ECE_q75_over_q25": van_ece.get("q75_over_q25"),
        "aggregate_proxy_pass": (
            ens_ece.get("q75_over_q25") is not None
            and ens_ece["q75_over_q25"] >= 2.0
            and ens_ece.get("q75") is not None
            and ens_ece["q75"] >= 0.05
        ),
    }

    # Ensembles best at every quartile across ECE? (the "even the best method collapses" check)
    ece_groups = {k.split("|", 1)[0]: v for k, v in p2a.items() if k.endswith("|ECE")}
    if ece_groups:
        for q in ("q25", "q50", "q75"):
            vals = {sys: g.get(q) for sys, g in ece_groups.items() if g.get(q) is not None}
            if vals:
                best = min(vals, key=lambda s: vals[s])
                p2a_verdict[f"lowest_ECE_at_{q}"] = best
        p2a_verdict["ensembles_lowest_at_all_quartiles"] = all(
            p2a_verdict.get(f"lowest_ECE_at_{q}") == "ensembles" for q in ("q25", "q50", "q75")
        )

    # P2b: BatchBALD must beat naive-BALD on every available comparison.
    bb_wins = [v.get("batchbald_beats_naive") for k, v in p2b.items() if "batchbald_vs_bald" in k]
    bb_vs_random = [v.get("batchbald_beats_random") for k, v in p2b.items() if "batchbald_vs_random" in k]
    p2b_verdict = {
        "P2b_threshold": (
            "BatchBALD strictly beats naive (top-k) BALD on label budget to reach "
            "target accuracy, across all transcribed comparisons (MNIST and CINIC-10)."
        ),
        "all_comparisons": p2b,
        "n_batchbald_vs_naive_comparisons": len(bb_wins),
        "n_batchbald_wins": sum(1 for w in bb_wins if w is True),
        "P2b_pass": len(bb_wins) > 0 and all(w is True for w in bb_wins),
        "n_batchbald_vs_random_comparisons": len(bb_vs_random),
        "n_batchbald_beats_random": sum(1 for w in bb_vs_random if w is True),
    }

    return {
        "kind": "REAL external transcription check (Tier A)",
        "csv": str(csv_path),
        "n_rows": len(rows),
        "P2a": p2a_verdict,
        "P2b": p2b_verdict,
        "p2a_full_summary": p2a,
        "p2b_full_summary": p2b,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, help="Path to frozen transcribed public-numbers CSV.")
    parser.add_argument("--self-test", action="store_true", help="Validate math on synthetic data.")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.self_test:
        payload = self_test()
    elif args.csv is not None:
        payload = run_check(args.csv)
    else:
        payload = {
            "kind": "HARNESS ONLY -- no result",
            "message": (
                "No CSV supplied. This is infrastructure, not a result. Run "
                "`--self-test` to validate the math, or "
                "`--csv experiments/external_contact/p2_uncertainty_public.csv` "
                "to run the real Tier-A external check against the frozen "
                "transcribed numbers."
            ),
        }

    output = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
