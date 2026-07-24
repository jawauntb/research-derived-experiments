"""MX1 orchestrator — runs both parts and writes the GO/NO-GO verdict.

Local CPU only. No Modal. Single-shot: the knobs are frozen in
``PREREGISTRATION.md`` section 5 and are not tuned to manufacture a GO.

Run:
    uv run --no-sync python -m experiments.concern_gated_retrieval_e2.mx1_repair_prior.run_mx1
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Sequence

from experiments.concern_gated_retrieval_e2.wave0.sealed_env import SealedEnvironment
from experiments.concern_gated_retrieval_e2.wave0.template_split import TemplateBucket
from experiments.concern_gated_retrieval_e2.wave1b.families import (
    delayed_commitments_v2 as family,
)
from experiments.concern_gated_retrieval_e2.wave1b.sealed_env_ext import (
    compute_set_delta,
)

from experiments.concern_gated_retrieval_e2.mx1_repair_prior.repair_loop import (
    MAX_ATTEMPTS,
    POLICIES,
    EpisodeRun,
    run_episode,
)
from experiments.concern_gated_retrieval_e2.mx1_repair_prior.verifier_split import (
    FaultKind,
    marginal_verifier,
    planted_interaction_members,
    split_verifier,
)


__all__ = ["main", "run_part_a", "run_part_b", "bootstrap_mean_diff_ci"]


# Frozen knobs (PREREGISTRATION.md section 5).
SEED_START: Final[int] = 100_000
N_EPISODES: Final[int] = 600
BOOTSTRAP_RESAMPLES: Final[int] = 2_000
BOOTSTRAP_SEED: Final[int] = 20_260_724

ROOT = Path(__file__).resolve().parents[3]
VERDICT_PATH = (
    ROOT
    / "experiments"
    / "concern_gated_retrieval_e2"
    / "mx1_repair_prior"
    / "results"
    / "mx1_verdict.json"
)


def bootstrap_mean_diff_ci(
    left: Sequence[float],
    right: Sequence[float],
    *,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float]:
    """Paired bootstrap 95% CI for ``mean(left) - mean(right)``."""
    diffs = [a - b for a, b in zip(left, right, strict=True)]
    rng = random.Random(seed)
    n = len(diffs)
    means: list[float] = []
    for _ in range(resamples):
        means.append(statistics.fmean(rng.choices(diffs, k=n)))
    means.sort()
    lo = means[int(0.025 * resamples)]
    hi = means[min(resamples - 1, int(0.975 * resamples))]
    return (float(lo), float(hi))


@dataclass(frozen=True)
class PartAResult:
    per_policy_mean_attempts: dict[str, float]
    per_policy_success_rate: dict[str, float]
    contrasts: dict[str, dict[str, float]]
    passed: bool
    kill_reasons: list[str]
    #: DIAGNOSTIC ONLY -- reported, never used to move the frozen verdict.
    diagnostic_by_pair_presence: dict[str, dict[str, float]]


def run_part_a(seeds: Sequence[int]) -> PartAResult:
    """Within-episode repair loop: repair_guided vs concern and random."""
    runs: dict[str, list[EpisodeRun]] = {p: [] for p in POLICIES}
    pair_flags: list[bool] = []
    for seed in seeds:
        episode = family.generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
        context = SealedEnvironment(episode).observe()
        has_pair = bool(
            getattr(family.bundle_manifest(episode), "complementary_pair", None)
        )
        pair_flags.append(has_pair)
        for policy in POLICIES:
            runs[policy].append(run_episode(episode, context, policy))

    attempts = {p: [float(r.attempts_to_success) for r in runs[p]] for p in POLICIES}
    means = {p: statistics.fmean(attempts[p]) for p in POLICIES}
    success = {
        p: statistics.fmean([1.0 if r.succeeded else 0.0 for r in runs[p]])
        for p in POLICIES
    }

    contrasts: dict[str, dict[str, float]] = {}
    kills: list[str] = []
    for rival in ("concern_sequential", "random_sequential"):
        # Negative diff == repair_guided needed FEWER attempts == better.
        diff = means["repair_guided"] - means[rival]
        lo, hi = bootstrap_mean_diff_ci(attempts["repair_guided"], attempts[rival])
        contrasts[f"repair_guided_vs_{rival}"] = {
            "mean_diff_attempts": diff,
            "ci_lo": lo,
            "ci_hi": hi,
        }
        if not (diff < 0.0 and hi < 0.0):
            kills.append(
                f"PartA::repair_guided did not strictly beat {rival} "
                f"(mean_diff={diff:+.4f}, CI=[{lo:+.4f}, {hi:+.4f}]; "
                "GO requires diff < 0 and CI excluding 0)"
            )

    # DIAGNOSTIC: split by whether the episode actually plants a
    # complementary pair. This does NOT move the frozen verdict above; it is
    # reported so a NO_GO says *why*, in the same spirit as Wave 1b keeping
    # its withheld L2 rows as diagnostics.
    diag: dict[str, dict[str, float]] = {}
    for label, want in (("with_complementary_pair", True), ("without_pair", False)):
        idx = [i for i, f in enumerate(pair_flags) if f is want]
        if not idx:
            continue
        diag[label] = {"n_episodes": float(len(idx))}
        for p in POLICIES:
            diag[label][f"mean_attempts::{p}"] = statistics.fmean(
                [attempts[p][i] for i in idx]
            )
            diag[label][f"success_rate::{p}"] = statistics.fmean(
                [1.0 if runs[p][i].succeeded else 0.0 for i in idx]
            )

    return PartAResult(means, success, contrasts, not kills, kills, diag)


@dataclass(frozen=True)
class PartBResult:
    marginal_mislabeled: int
    split_mislabeled: int
    split_false_verifier_faults: int
    singleton_controls: int
    passed: bool
    kill_reasons: list[str]


def run_part_b(seeds: Sequence[int]) -> PartBResult:
    """Verifier-fault split vs a marginal verifier on planted interactions."""
    marginal_bad = 0
    split_bad = 0
    false_faults = 0
    singletons = 0

    for seed in seeds:
        episode = family.generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
        manifest = family.bundle_manifest(episode)
        groups = planted_interaction_members(manifest)

        # --- the interaction case: is a genuinely useful pair discarded? ---
        pair = getattr(manifest, "complementary_pair", None)
        if pair:
            members = tuple(pair)
            truth = compute_set_delta(episode, members).delta_task
            if truth > 0.0:  # genuinely useful by the SET-level oracle
                if (marginal_verifier(episode, members).value or 0.0) <= 0.0:
                    marginal_bad += 1
                split_out = split_verifier(episode, members, groups)
                if (
                    split_out.fault_kind is FaultKind.REASONING_FAULT
                    and (split_out.value or 0.0) <= 0.0
                ):
                    split_bad += 1

        # --- the control: singletons, where the marginal model IS correct ---
        for node in episode.candidate_nodes:
            singletons += 1
            out = split_verifier(episode, [node], groups)
            if out.fault_kind is FaultKind.VERIFIER_FAULT:
                false_faults += 1

    kills: list[str] = []
    if not split_bad < marginal_bad:
        kills.append(
            f"PartB::split verifier did not reduce mislabeling "
            f"(split={split_bad}, marginal={marginal_bad}; GO requires split < marginal)"
        )
    if false_faults != 0:
        kills.append(
            f"PartB::split verifier raised {false_faults} false VERIFIER_FAULT(s) on "
            f"{singletons} cleanly-scorable singletons; GO requires precision 1.0"
        )

    return PartBResult(marginal_bad, split_bad, false_faults, singletons, not kills, kills)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the MX1 de-risk probe.")
    parser.add_argument("--n-episodes", type=int, default=N_EPISODES)
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    seeds = list(range(SEED_START, SEED_START + args.n_episodes))
    part_a = run_part_a(seeds)
    part_b = run_part_b(seeds)

    if part_a.passed and part_b.passed:
        overall = "GO"
    elif part_a.passed:
        overall = "PARTIAL_GO_A_ONLY"
    elif part_b.passed:
        overall = "PARTIAL_GO_B_ONLY"
    else:
        overall = "NO_GO"

    verdict = {
        "kind": "cogr_mx1_verdict",
        "family": "delayed_commitments_v2",
        "bucket": "CALIBRATION",
        "n_episodes": len(seeds),
        "seed_range": [seeds[0], seeds[-1]],
        "max_attempts": MAX_ATTEMPTS,
        "part_a": {
            "mean_attempts_to_success": part_a.per_policy_mean_attempts,
            "success_rate": part_a.per_policy_success_rate,
            "contrasts": part_a.contrasts,
            "decision": "GO" if part_a.passed else "NO_GO",
            "kill_reasons": part_a.kill_reasons,
            "diagnostic_by_pair_presence": part_a.diagnostic_by_pair_presence,
        },
        "part_b": {
            "useful_pairs_mislabeled_by_marginal": part_b.marginal_mislabeled,
            "useful_pairs_mislabeled_by_split": part_b.split_mislabeled,
            "false_verifier_faults_on_singletons": part_b.split_false_verifier_faults,
            "singleton_controls": part_b.singleton_controls,
            "decision": "GO" if part_b.passed else "NO_GO",
            "kill_reasons": part_b.kill_reasons,
        },
        "overall_decision": overall,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
