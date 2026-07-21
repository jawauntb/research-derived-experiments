"""Live pilot runner: planner + extractor + ablations + executor + scoring.

Loads the CT held-out task bank
(``experiments/grounded_statecharts/fixtures/d2_held_out_tasks.json``),
asks a live planner to produce prose plans for every task, atomizes
each plan via the rule-based extractor, produces
delete/negate/paraphrase ablations, and runs baseline + each variant
through the CT live executor under both primary and control
conditions. Applies CT ``condition_policy`` and scores against the
pre-registered commitment-surface tuple.

Requires ``LBPT_LIVE=1`` plus the CT live env (``GROUNDED_HARNESS_LIVE=1``,
provider/model/API-key env vars). Emits sanitized rows and a summary
to ``results/live_pilot/`` — raw provider text is not published.

Uses ``concurrent.futures.ThreadPoolExecutor`` to fan out the
blocking urllib-based provider calls.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments.load_bearing_prose_test.ablation import ablate_bundle
from experiments.load_bearing_prose_test.claims import (
    Ablation,
    AblationKind,
    Verdict,
    digest,
)
from experiments.load_bearing_prose_test.executor import (
    CTPlanLiveExecutor,
    PlanEpisode,
    PlanExecutor,
    run_plan_episode,
)
from experiments.load_bearing_prose_test.extraction import (
    RuleBasedExtractor,
    default_kappa_vocabulary,
)
from experiments.load_bearing_prose_test.planner import LivePlanner, PlannedPlan
from experiments.load_bearing_prose_test.run_lbpt_pilot import (
    CONTROL_CONDITION_BY_FAMILY,
    PRIMARY_CONDITION_BY_FAMILY,
    PilotRow,
)
from experiments.load_bearing_prose_test.scoring import (
    ClaimVerdictInputs,
    CommitmentSurface,
    aggregate_metrics,
    classify_claim,
    commitment_surface,
)


PACKAGE_DIR = Path(__file__).resolve().parent
CT_TASKS_PATH = (
    PACKAGE_DIR.parent
    / "grounded_statecharts"
    / "fixtures"
    / "d2_held_out_tasks.json"
)
DEFAULT_RESULTS_DIR = PACKAGE_DIR / "results" / "live_pilot"
DEFAULT_SUMMARY_PATH = DEFAULT_RESULTS_DIR / "summary.json"
DEFAULT_ROWS_PATH = DEFAULT_RESULTS_DIR / "rows.jsonl"
DEFAULT_PLANS_PATH = DEFAULT_RESULTS_DIR / "plans.jsonl"

# Family kappa comes from the CT condition_policy substrate — mirrors
# the requirements the CT harness enforces, so plans are asked to
# respect the same κ the executor scores against.
FAMILY_KAPPA: dict[str, dict[str, Any]] = {
    "artifact_completion": {
        "required_artifact": "reports/out.md",
        "required_capabilities": ("write_artifact",),
        "forbidden_capabilities": ("deploy",),
    },
    "recursive_constrained_tool_use": {
        "required_artifact": None,
        "required_capabilities": ("delegate",),
        "forbidden_capabilities": ("publish", "deploy", "grant_admin"),
    },
}


@dataclass(frozen=True)
class LiveTaskRef:
    """Just the subset of CT task fields the LBPT pilot needs."""

    task_id: str
    family: str
    title: str
    instruction: str


def _load_ct_tasks(path: Path = CT_TASKS_PATH) -> list[LiveTaskRef]:
    payload = json.loads(path.read_text())
    tasks: list[LiveTaskRef] = []
    for entry in payload:
        tasks.append(
            LiveTaskRef(
                task_id=entry["task_id"],
                family=entry["family"],
                title=entry["title"],
                instruction=entry["instruction"],
            )
        )
    return tasks


def _plan_task(
    *,
    planner: LivePlanner,
    task: LiveTaskRef,
) -> PlannedPlan:
    kappa = FAMILY_KAPPA[task.family]
    return planner.plan_for(
        task_id=task.task_id,
        family=task.family,
        title=task.title,
        instruction=task.instruction,
        required_artifact=kappa["required_artifact"],
        required_capabilities=kappa["required_capabilities"],
        forbidden_capabilities=kappa["forbidden_capabilities"],
    )


def _extractor_for(family: str) -> RuleBasedExtractor:
    kappa = FAMILY_KAPPA[family]
    caps: tuple[str, ...] = (
        *kappa["required_capabilities"],
        *kappa["forbidden_capabilities"],
    )
    artifacts: tuple[str, ...] = (
        (kappa["required_artifact"],) if kappa["required_artifact"] else ()
    )
    return RuleBasedExtractor(
        kappa=default_kappa_vocabulary(capabilities=caps, artifacts=artifacts)
    )


def _episode(
    *,
    task_id: str,
    plan_text: str,
    family: str,
    condition: str,
    variant: str,
    seed: int,
) -> PlanEpisode:
    kappa = FAMILY_KAPPA[family]
    return PlanEpisode(
        plan_id=task_id,
        variant=variant,
        plan_text=plan_text,
        family=family,
        task_id=task_id,
        condition=condition,
        required_artifact=kappa["required_artifact"],
        required_capabilities=kappa["required_capabilities"],
        forbidden_capabilities=kappa["forbidden_capabilities"],
        seed=seed,
    )


def _surface_for(
    *,
    episode: PlanEpisode,
    executor: PlanExecutor,
) -> CommitmentSurface:
    _, evidence = run_plan_episode(episode, executor=executor)
    return commitment_surface(
        family=episode.family,
        evidence=evidence,
        forbidden_capabilities=episode.forbidden_capabilities,
    )


def _surface_digest(surface: CommitmentSurface) -> str:
    return digest(surface.to_dict())


@dataclass(frozen=True)
class _RunKey:
    task_id: str
    condition: str
    variant: str


@dataclass
class _RunSpec:
    key: _RunKey
    episode: PlanEpisode


def _collect_runs(
    *,
    tasks: list[LiveTaskRef],
    plans: dict[str, PlannedPlan],
    seed: int,
) -> tuple[list[_RunSpec], dict[str, list[Ablation]]]:
    """Flatten every (task × condition × variant) into a run list."""

    runs: list[_RunSpec] = []
    ablations_by_task: dict[str, list[Ablation]] = {}
    for task in tasks:
        plan = plans[task.task_id]
        extractor = _extractor_for(task.family)
        bundle = extractor.extract(
            plan_id=task.task_id, plan_text=plan.plan_text
        )
        ablations = ablate_bundle(bundle, plan.plan_text)
        ablations_by_task[task.task_id] = list(ablations.ablations)
        for cond in (
            PRIMARY_CONDITION_BY_FAMILY[task.family],
            CONTROL_CONDITION_BY_FAMILY[task.family],
        ):
            # baseline
            runs.append(
                _RunSpec(
                    key=_RunKey(
                        task_id=task.task_id,
                        condition=cond,
                        variant=f"baseline::{cond}",
                    ),
                    episode=_episode(
                        task_id=task.task_id,
                        plan_text=plan.plan_text,
                        family=task.family,
                        condition=cond,
                        variant=f"baseline::{cond}",
                        seed=seed,
                    ),
                )
            )
            # ablations
            for ablation in ablations.ablations:
                runs.append(
                    _RunSpec(
                        key=_RunKey(
                            task_id=task.task_id,
                            condition=cond,
                            variant=f"{ablation.kind.value}::{ablation.claim_id}::{cond}",
                        ),
                        episode=_episode(
                            task_id=task.task_id,
                            plan_text=ablation.modified_plan,
                            family=task.family,
                            condition=cond,
                            variant=f"{ablation.kind.value}::{ablation.claim_id}::{cond}",
                            seed=seed,
                        ),
                    )
                )
    return runs, ablations_by_task


def _run_all(
    *,
    runs: list[_RunSpec],
    executor: PlanExecutor,
    max_workers: int,
) -> tuple[dict[_RunKey, CommitmentSurface], set[str]]:
    """Run every episode, returning surfaces and the set of failed task_ids.

    Any executor exception drops the *entire task episode* from the
    reported slice per the preregistration's integrity requirement.
    """

    surfaces: dict[_RunKey, CommitmentSurface] = {}
    failures: list[tuple[_RunKey, BaseException]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_key = {
            pool.submit(_surface_for, episode=spec.episode, executor=executor): spec.key
            for spec in runs
        }
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                surfaces[key] = future.result()
            except BaseException as exc:  # noqa: BLE001
                failures.append((key, exc))
    failed_task_ids: set[str] = {key.task_id for key, _ in failures}
    return surfaces, failed_task_ids


def _row(
    *,
    task: LiveTaskRef,
    plan: PlannedPlan,
    claim_id: str,
    claim_text: str,
    kappa_mention: bool,
    primary_base: CommitmentSurface,
    primary_verdict: Verdict,
    control_verdict: Verdict,
) -> PilotRow:
    return PilotRow(
        family=task.family,
        plan_id=task.task_id,
        plan_digest=digest({"plan_text": plan.plan_text}),
        claim_id=claim_id,
        claim_text=claim_text,
        kappa_mention=kappa_mention,
        primary_condition=PRIMARY_CONDITION_BY_FAMILY[task.family],
        control_condition=CONTROL_CONDITION_BY_FAMILY[task.family],
        baseline_surface_digest=_surface_digest(primary_base),
        delete_delta=primary_verdict.delete_delta,
        negate_delta=primary_verdict.negate_delta,
        paraphrase_delta=primary_verdict.paraphrase_delta,
        is_load_bearing=primary_verdict.is_load_bearing,
        paraphrase_invariant=primary_verdict.paraphrase_invariant,
        control_delete_delta=control_verdict.delete_delta,
        control_negate_delta=control_verdict.negate_delta,
    )


def _build_verdicts(
    *,
    tasks: list[LiveTaskRef],
    plans: dict[str, PlannedPlan],
    surfaces: dict[_RunKey, CommitmentSurface],
    ablations_by_task: dict[str, list[Ablation]],
) -> tuple[list[PilotRow], list[Verdict], list[Verdict]]:
    rows: list[PilotRow] = []
    primary_all: list[Verdict] = []
    control_all: list[Verdict] = []
    for task in tasks:
        plan = plans[task.task_id]
        extractor = _extractor_for(task.family)
        bundle = extractor.extract(plan_id=task.task_id, plan_text=plan.plan_text)
        primary_cond = PRIMARY_CONDITION_BY_FAMILY[task.family]
        control_cond = CONTROL_CONDITION_BY_FAMILY[task.family]
        primary_base = surfaces[
            _RunKey(task.task_id, primary_cond, f"baseline::{primary_cond}")
        ]
        control_base = surfaces[
            _RunKey(task.task_id, control_cond, f"baseline::{control_cond}")
        ]
        ablations = ablations_by_task[task.task_id]
        by_claim_kind = {
            (a.claim_id, a.kind): a for a in ablations
        }
        for claim in bundle.claims:
            primary_surfaces: dict[AblationKind, CommitmentSurface] = {}
            control_surfaces: dict[AblationKind, CommitmentSurface] = {}
            for kind in (
                AblationKind.DELETE,
                AblationKind.NEGATE,
                AblationKind.PARAPHRASE,
            ):
                ablation = by_claim_kind[(claim.claim_id, kind)]
                _ = ablation  # variant string is deterministic below
                primary_key = _RunKey(
                    task.task_id,
                    primary_cond,
                    f"{kind.value}::{claim.claim_id}::{primary_cond}",
                )
                control_key = _RunKey(
                    task.task_id,
                    control_cond,
                    f"{kind.value}::{claim.claim_id}::{control_cond}",
                )
                primary_surfaces[kind] = surfaces[primary_key]
                control_surfaces[kind] = surfaces[control_key]
            primary_verdict = classify_claim(
                ClaimVerdictInputs(
                    claim=claim,
                    baseline=primary_base,
                    surfaces=primary_surfaces,
                )
            )
            control_verdict = classify_claim(
                ClaimVerdictInputs(
                    claim=claim,
                    baseline=control_base,
                    surfaces=control_surfaces,
                )
            )
            primary_all.append(primary_verdict)
            control_all.append(control_verdict)
            rows.append(
                _row(
                    task=task,
                    plan=plan,
                    claim_id=claim.claim_id,
                    claim_text=claim.text,
                    kappa_mention=claim.mentions_kappa,
                    primary_base=primary_base,
                    primary_verdict=primary_verdict,
                    control_verdict=control_verdict,
                )
            )
    return rows, primary_all, control_all


def run_live_pilot(
    *,
    seed: int = 20260721,
    max_workers: int = 20,
    limit: int | None = None,
) -> tuple[list[PilotRow], dict[str, Any], list[PlannedPlan]]:
    tasks = _load_ct_tasks()
    if limit is not None:
        tasks = tasks[:limit]

    planner = LivePlanner()
    executor = CTPlanLiveExecutor()

    plan_start = time.time()
    plans: dict[str, PlannedPlan] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_plan_task, planner=planner, task=task): task
            for task in tasks
        }
        for future in as_completed(futures):
            task = futures[future]
            plans[task.task_id] = future.result()
    planning_seconds = time.time() - plan_start

    runs, ablations_by_task = _collect_runs(tasks=tasks, plans=plans, seed=seed)

    run_start = time.time()
    surfaces, failed_task_ids = _run_all(
        runs=runs, executor=executor, max_workers=max_workers
    )
    execution_seconds = time.time() - run_start

    # Drop entire task episodes on any executor failure (integrity rule).
    reported_tasks = [t for t in tasks if t.task_id not in failed_task_ids]
    rows, primary_verdicts, control_verdicts = _build_verdicts(
        tasks=reported_tasks,
        plans=plans,
        surfaces=surfaces,
        ablations_by_task=ablations_by_task,
    )

    family_metrics: dict[str, dict[str, Any]] = {}
    for family in ("artifact_completion", "recursive_constrained_tool_use"):
        family_primary = [
            v
            for v, r in zip(primary_verdicts, rows, strict=True)
            if r.family == family
        ]
        family_control = [
            v
            for v, r in zip(control_verdicts, rows, strict=True)
            if r.family == family
        ]
        family_metrics[family] = {
            "kappa": FAMILY_KAPPA[family],
            "primary_condition": PRIMARY_CONDITION_BY_FAMILY[family],
            "control_condition": CONTROL_CONDITION_BY_FAMILY[family],
            "primary": aggregate_metrics(family_primary).to_dict(),
            "control": aggregate_metrics(family_control).to_dict(),
        }
    overall_primary = aggregate_metrics(primary_verdicts).to_dict()
    overall_control = aggregate_metrics(control_verdicts).to_dict()

    summary = {
        "schema_version": "1.0",
        "run_id": f"lbpt_live_pilot_{seed}",
        "package": "load_bearing_prose_test",
        "seed": seed,
        "adapter_id": executor.adapter_id,
        "provider_id": executor.provider_id,
        "model_id": executor.model_id,
        "n_tasks_requested": len(tasks),
        "n_tasks_reported": len(reported_tasks),
        "n_tasks_dropped": len(failed_task_ids),
        "dropped_task_ids": sorted(failed_task_ids),
        "n_plans": len(plans),
        "n_executor_calls_attempted": len(runs),
        "n_executor_calls_succeeded": len(surfaces),
        "n_rows": len(rows),
        "planning_seconds": round(planning_seconds, 2),
        "execution_seconds": round(execution_seconds, 2),
        "families": family_metrics,
        "overall": {"primary": overall_primary, "control": overall_control},
    }
    summary["rows_digest"] = digest([row.to_dict() for row in rows])
    summary["summary_digest"] = digest(summary)

    plans_list = [plans[task.task_id] for task in tasks]
    return rows, summary, plans_list


def _write_outputs(
    *,
    rows: list[PilotRow],
    summary: dict[str, Any],
    plans: list[PlannedPlan],
    rows_path: Path,
    summary_path: Path,
    plans_path: Path,
) -> None:
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    with rows_path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row.to_dict(), sort_keys=True) + "\n")
    with plans_path.open("w") as handle:
        for plan in plans:
            handle.write(json.dumps(plan.to_dict(), sort_keys=True) + "\n")
    summary_path.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260721)
    parser.add_argument("--max-workers", type=int, default=20)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--rows", type=Path, default=DEFAULT_ROWS_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--plans", type=Path, default=DEFAULT_PLANS_PATH)
    args = parser.parse_args()
    rows, summary, plans = run_live_pilot(
        seed=args.seed,
        max_workers=args.max_workers,
        limit=args.limit,
    )
    _write_outputs(
        rows=rows,
        summary=summary,
        plans=plans,
        rows_path=args.rows,
        summary_path=args.summary,
        plans_path=args.plans,
    )
    print(f"wrote {len(rows)} rows to {args.rows}")
    print(f"wrote summary to {args.summary}")
    print(f"wrote {len(plans)} plans to {args.plans}")
    print(
        f"tasks: reported={summary['n_tasks_reported']} "
        f"dropped={summary['n_tasks_dropped']}"
    )
    print(
        f"overall primary L={summary['overall']['primary']['load_bearing_rate']:.3f}"
        f" P={summary['overall']['primary']['paraphrase_invariance_rate']:.3f}"
    )


if __name__ == "__main__":
    main()
