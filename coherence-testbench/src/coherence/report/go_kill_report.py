"""Auto-generate the Phase-0 GO/KILL report.

The report contains, in the exact order the kill-criterion demands:

    1. pre_registered_thresholds
    2. generalization_curve
    3. cross_vs_per_subject_gap
    4. bits_per_second_MI
    5. confound_ablations
    6. verdict

If a required section is missing from the passed results, the report writer
flags the gap explicitly rather than silently omitting — a missing confound
ablation is not the same as a passed confound ablation.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from typing import Any

from ..config import KillCriterion
from ..evaluate.leave_subjects_out import LSOFoldResult


def _fmt_pct(v: float) -> str:
    return f"{100 * v:.1f}%"


def _generalization_curve(fold_results: list[LSOFoldResult]) -> list[dict[str, float]]:
    by_n: dict[int, list[LSOFoldResult]] = {}
    for r in fold_results:
        by_n.setdefault(r.n_train_subjects, []).append(r)
    curve = []
    for n in sorted(by_n.keys()):
        rs = by_n[n]
        curve.append({
            "n_train_subjects": n,
            "mean_balanced_accuracy": mean(r.balanced_accuracy for r in rs),
            "mean_bits_per_second": mean(r.bits_per_second for r in rs),
            "n_folds": len(rs),
        })
    return curve


def build_report(
    kc: KillCriterion,
    fold_results: list[LSOFoldResult],
    per_subject_baseline_bacc: float,
    confound_ablations: dict[str, dict[str, float]],
    out_dir: Path,
) -> Path:
    """Materialize `report.md` + `report.json` in ``out_dir``.

    ``confound_ablations`` is a dict keyed by confound id (matching the ids in
    kill_criterion.yaml) with at minimum a 'lso_balanced_accuracy' key.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    curve = _generalization_curve(fold_results)
    # Headline metrics: pool by seed, then average across seeds at the
    # largest train-subject bucket in the sweep — that's the 'best available'
    # LSO number the gate should judge against.
    largest_n = max((c["n_train_subjects"] for c in curve), default=0)
    top_folds = [r for r in fold_results if r.n_train_subjects == largest_n]
    if top_folds:
        lso_bacc = mean(r.balanced_accuracy for r in top_folds)
        lso_bps = mean(r.bits_per_second for r in top_folds)
        per_seed_baccs = [r.balanced_accuracy for r in top_folds]
    else:
        lso_bacc = 0.0
        lso_bps = 0.0
        per_seed_baccs = []
    gen_gap = per_subject_baseline_bacc - lso_bacc
    verdict = kc.verdict(lso_bacc, lso_bps, gen_gap, per_seed_baccs)

    lines: list[str] = []
    lines.append("# Phase-0 GO/KILL report")
    lines.append("")
    lines.append(f"**Verdict:** `{verdict}`")
    lines.append("")
    lines.append(f"- kill-criterion version: `{kc.version}`")
    lines.append(f"- kill-criterion sha256:  `{kc.content_hash[:16]}…`")
    lines.append(f"- kill-criterion source:  `{kc.source_path}`")
    lines.append(f"- committed at:           {kc.committed_at} by {kc.committed_by}")
    lines.append("")

    lines.append("## 1. Pre-registered thresholds")
    lines.append("")
    lines.append("| criterion | GO | KILL |")
    lines.append("|---|---|---|")
    lines.append(f"| LSO balanced accuracy | ≥ {kc.go.lso_balanced_accuracy_min:.2f} | ≤ {kc.kill.lso_balanced_accuracy_max:.2f} |")
    lines.append(f"| bits / second         | ≥ {kc.go.bits_per_second_min:.3f}  | ≤ {kc.kill.bits_per_second_max:.3f}  |")
    lines.append(f"| gen. gap (per-subj - LSO) | ≤ {kc.go.generalization_gap_max:.2f} | — |")
    lines.append(f"| per-seed floor        | every seed BA ≥ {kc.go.seed_min_bacc:.2f} across {kc.go.n_seeds} seeds | — |")
    lines.append("")

    lines.append("## 2. Generalization curve")
    lines.append("")
    lines.append("| n train subjects | mean BA | mean bits/s | folds |")
    lines.append("|---:|---:|---:|---:|")
    for row in curve:
        lines.append(
            f"| {row['n_train_subjects']} | {_fmt_pct(row['mean_balanced_accuracy'])} "
            f"| {row['mean_bits_per_second']:.3f} | {row['n_folds']} |"
        )
    lines.append("")

    lines.append("## 3. Cross- vs per-subject gap")
    lines.append("")
    lines.append(f"- per-subject baseline BA (upper bound): {_fmt_pct(per_subject_baseline_bacc)}")
    lines.append(f"- LSO cross-subject BA at n={largest_n}: {_fmt_pct(lso_bacc)}")
    lines.append(f"- gap: {_fmt_pct(gen_gap)}  (GO requires ≤ {_fmt_pct(kc.go.generalization_gap_max)})")
    lines.append("")

    lines.append("## 4. Bits / second (mutual information)")
    lines.append("")
    lines.append(f"- LSO bits/s at n={largest_n}: {lso_bps:.3f}")
    lines.append(f"- GO requires ≥ {kc.go.bits_per_second_min:.3f}, KILL if ≤ {kc.kill.bits_per_second_max:.3f}")
    lines.append("")

    lines.append("## 5. Confound ablations")
    lines.append("")
    if not kc.confounds:
        lines.append("_no confounds declared in kill_criterion.yaml_")
    for c in kc.confounds:
        cid = c.get("id", "?")
        got = confound_ablations.get(cid, {})
        if not got:
            lines.append(f"- **{cid}** — ⚠ NOT RUN. {c.get('description', '').strip()}")
            continue
        lines.append(f"- **{cid}** — LSO BA: {_fmt_pct(got.get('lso_balanced_accuracy', 0.0))}. "
                     f"Mitigation: {c.get('mitigation', '').strip()}")
    lines.append("")

    lines.append("## 6. Verdict")
    lines.append("")
    lines.append(f"**{verdict}**")
    if verdict == "GO":
        lines.append("")
        lines.append("Cross-subject decoding clears the pre-registered thresholds on BBBD. "
                     "Phase 1 (Position) may begin. Continue enforcing LSO-only reporting "
                     "and bits/s alongside accuracy.")
    elif verdict == "KILL":
        lines.append("")
        lines.append("Cross-subject decoding fails the pre-registered thresholds on the "
                     "cleanest available research-grade corpus. Per the kill-criterion, "
                     "**escalate to a human before further build.**")
    else:
        lines.append("")
        lines.append("Neither GO nor KILL fired. Rerun with SSL pretraining enabled and/or "
                     "more compute before making the call. Do NOT proceed to Phase 1.")
    lines.append("")

    md_path = out_dir / "report.md"
    md_path.write_text("\n".join(lines))

    json_path = out_dir / "report.json"
    json_path.write_text(json.dumps({
        "verdict": verdict,
        "kill_criterion_version": kc.version,
        "kill_criterion_sha256": kc.content_hash,
        "lso_balanced_accuracy": lso_bacc,
        "lso_bits_per_second": lso_bps,
        "per_subject_baseline_balanced_accuracy": per_subject_baseline_bacc,
        "generalization_gap": gen_gap,
        "curve": curve,
        "fold_results": [asdict(r) for r in fold_results],
        "confound_ablations": confound_ablations,
    }, indent=2, default=_json_default))
    return md_path


def _json_default(obj: Any) -> Any:
    if isinstance(obj, tuple):
        return list(obj)
    raise TypeError(f"not serializable: {type(obj)}")
