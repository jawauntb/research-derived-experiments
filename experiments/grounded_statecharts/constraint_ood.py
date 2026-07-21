"""Runnable Constraint Transport OOD probes for the harness-v2 name-free contract.

Two probes test constraint transport beyond the committed D2 cells:

1. ``held_out_paraphrase``: reruns a slice of the frozen D2
   ``recursive_constrained_tool_use`` held-out task bank with paraphrased
   (still name-free) instruction wording through the real
   ``condition_policy``-enforced harness (``envelope_only`` vs
   ``envelope_external_guards``). Condition identity lives in harness code,
   not in the prompt; the paraphrase changes only surface wording and keeps
   the exact typed check-spec (required/forbidden capabilities) identity.
   This module always runs that probe against the deterministic fixture
   adapter (required, credential-free). ``run_constraint_ood_live_smoke.py``
   optionally reruns the same probe against a live provider under
   ``GROUNDED_HARNESS_LIVE=1`` and writes that slice only under
   ``artifacts/``.

2. ``deeper_delegation_depth``: extends the deterministic typed/lossy
   Constraint Transport benchmark (`constraint_transport.py`) to delegation
   depths 5 and 6, beyond the committed depth-1..4 fixture ceiling. This
   mechanic has no live-provider analogue -- it is a pure typed-envelope
   derivation check and is always deterministic.

Both probes report their outcome honestly. The primary live metric is the
task-clustered joint_success effect for envelope_external_guards vs
envelope_only; per the D3 sample-size plan, effects below
`OOD_KILL_THRESHOLD` are recorded as a kill, not reinterpreted as support.
The fixture-adapter run of probe 1 is mechanics-only: `FixtureExecutor`
selects its behavior from `(family, condition)` alone and never reads
`instruction` text, so a fixture-run paraphrase delta cannot demonstrate
wording sensitivity either way. That limitation is reported explicitly
rather than hidden.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from experiments.grounded_statecharts.adapters import ProviderExecutor, build_executor
from experiments.grounded_statecharts.budgets import DEFAULT_PILOT_BUDGET
from experiments.grounded_statecharts.constraint_transport import (
    CONDITIONS as TRANSPORT_CONDITIONS,
    ConstraintTransportBenchmark,
    TransportOutcome,
    TransportTask,
)
from experiments.grounded_statecharts.d2_tasks import load_d2_held_out_tasks
from experiments.grounded_statecharts.evaluation import (
    LiveEpisode,
    LiveTask,
    bootstrap_paired_effect,
    digest_to_seed,
    harness_digest_for,
    run_episode,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "results" / "constraint_ood"
PARAPHRASE_FIXTURE = PACKAGE_ROOT / "fixtures" / "constraint_ood_paraphrases.json"
TRANSPORT_FIXTURE = PACKAGE_ROOT / "fixtures" / "constraint_transport.json"

PARAPHRASE_FAMILY = "recursive_constrained_tool_use"
PARAPHRASE_TREATMENT = "envelope_external_guards"
PARAPHRASE_CONTROL = "envelope_only"
PARAPHRASE_CONDITIONS = (PARAPHRASE_CONTROL, PARAPHRASE_TREATMENT)
PARAPHRASE_TASKS_PER_FAMILY = 4
DEEPER_DEPTHS = (5, 6)
OOD_KILL_THRESHOLD = 0.15


@dataclass(frozen=True)
class ParaphraseCase:
    """A held-out, name-free paraphrase of one committed D2 task instruction."""

    task_id: str
    paraphrased_instruction: str

    def __post_init__(self) -> None:
        if not self.task_id or not self.paraphrased_instruction:
            raise ValueError("paraphrase case fields must be non-empty")

    @classmethod
    def load_many(cls, path: Path = PARAPHRASE_FIXTURE) -> tuple[Self, ...]:
        raw = json.loads(path.read_text())
        if not isinstance(raw, dict) or set(raw) != {"schema_version", "cases"}:
            raise ValueError("paraphrase fixture must contain schema_version and cases")
        if raw["schema_version"] != "1.0" or not isinstance(raw["cases"], list):
            raise ValueError("paraphrase fixture has an unsupported schema")
        expected = {"task_id", "paraphrased_instruction"}
        cases = []
        for item in raw["cases"]:
            if not isinstance(item, dict) or set(item) != expected:
                raise ValueError(f"paraphrase case fields must be exactly {sorted(expected)}")
            if not all(isinstance(item[key], str) and item[key] for key in expected):
                raise ValueError("paraphrase case fields must be non-empty strings")
            cases.append(cls(task_id=item["task_id"], paraphrased_instruction=item["paraphrased_instruction"]))
        if len({case.task_id for case in cases}) != len(cases):
            raise ValueError("paraphrase task_ids must be unique")
        return tuple(cases)


def _paraphrased_task(task: LiveTask, case: ParaphraseCase) -> LiveTask:
    """Rebuild a held-out task with paraphrased wording, unchanged check-spec identity."""

    if case.paraphrased_instruction.strip() == task.instruction.strip():
        raise ValueError(f"paraphrase for {task.task_id} must differ from the committed wording")
    return LiveTask(
        task_id=f"{task.task_id}::ood_paraphrase",
        family=task.family,
        title=task.title,
        instruction=case.paraphrased_instruction,
        check_kind=task.check_kind,
        check_spec=task.check_spec,
        environment_digest=task.environment_digest,
        held_out=task.held_out,
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def run_held_out_paraphrase_probe(
    *,
    executor: ProviderExecutor | None = None,
    adapter_id: str = "fixture",
    run_id: str = "constraint-ood-paraphrase",
    tasks_per_family: int = PARAPHRASE_TASKS_PER_FAMILY,
) -> dict[str, Any]:
    """Run the held-out paraphrase probe through the real name-free harness.

    Condition identity comes from `condition_policy.py` (via `run_episode`),
    never from the prompt. Works against the deterministic fixture executor
    by default; pass a `LiveExecutor` with `adapter_id="live"` for a
    credentialed run (see `run_constraint_ood_live_smoke.py`).
    """

    active = executor or build_executor(adapter_id)
    if active.adapter_id != adapter_id:
        raise ValueError("executor adapter_id does not match the requested adapter_id")

    tasks = [
        task
        for task in load_d2_held_out_tasks()
        if task.family == PARAPHRASE_FAMILY
    ][:tasks_per_family]
    cases_by_id = {case.task_id: case for case in ParaphraseCase.load_many()}
    missing = [task.task_id for task in tasks if task.task_id not in cases_by_id]
    if missing:
        raise ValueError(f"missing held-out paraphrase cases for: {sorted(missing)}")

    paraphrased_tasks = {
        task.task_id: _paraphrased_task(task, cases_by_id[task.task_id]) for task in tasks
    }
    preserves_constraint_identity = all(
        paraphrased_tasks[task.task_id].check_spec == task.check_spec
        and paraphrased_tasks[task.task_id].family == task.family
        for task in tasks
    )

    results = []
    failures: list[dict[str, object]] = []
    for task in tasks:
        paraphrased = paraphrased_tasks[task.task_id]
        for condition in PARAPHRASE_CONDITIONS:
            episode_id = f"{run_id}:{paraphrased.task_id}:{condition}:r0"
            try:
                episode = LiveEpisode(
                    episode_id=episode_id,
                    run_id=run_id,
                    task=paraphrased,
                    condition=condition,
                    repeat_index=0,
                    model_id=active.model_id,
                    provider_id=active.provider_id,
                    adapter_id=active.adapter_id,
                    harness_digest=harness_digest_for(condition),
                    budget=DEFAULT_PILOT_BUDGET,
                    seed=digest_to_seed(f"{run_id}:{paraphrased.task_id}:{condition}"),
                )
                results.append(run_episode(episode, executor=active))
            except Exception as exc:  # noqa: BLE001 - smoke must finish the matrix
                failures.append(
                    {
                        "episode_id": episode_id,
                        "error_type": type(exc).__name__,
                        "error": str(exc)[:500],
                    }
                )

    rows = [result.public_row for result in results if result.integrity.publishable]
    effect: dict[str, Any] = {
        "point_estimate": None,
        "ci_low": None,
        "ci_high": None,
        "task_count": 0,
    }
    try:
        bootstrap = bootstrap_paired_effect(
            rows,
            treatment=PARAPHRASE_TREATMENT,
            control=PARAPHRASE_CONTROL,
            metric="joint_success",
        )
        effect = {
            "point_estimate": bootstrap.point_estimate,
            "ci_low": bootstrap.ci_low,
            "ci_high": bootstrap.ci_high,
            "task_count": bootstrap.task_count,
        }
    except ValueError:
        pass

    return {
        "probe_id": "held_out_paraphrase",
        "adapter_id": active.adapter_id,
        "provider_id": active.provider_id,
        "model_id": active.model_id,
        "family": PARAPHRASE_FAMILY,
        "treatment": PARAPHRASE_TREATMENT,
        "control": PARAPHRASE_CONTROL,
        "task_count_attempted": len(tasks),
        "episode_count": len(tasks) * len(PARAPHRASE_CONDITIONS),
        "publishable_rows": len(rows),
        "provider_failures": failures,
        "preserves_constraint_identity": preserves_constraint_identity,
        "joint_success_effect": effect,
        "rows": rows,
    }


def _rate(outcomes: list[TransportOutcome], attribute: str) -> float:
    return sum(bool(getattr(outcome, attribute)) for outcome in outcomes) / len(outcomes)


def run_deeper_delegation_depth_probe(
    *, depths: tuple[int, ...] = DEEPER_DEPTHS
) -> dict[str, Any]:
    """Extend matched typed/prose delegation beyond the committed depth-1..4 fixture.

    Fully deterministic: no provider is involved, so this probe has no
    "live" variant and always runs the same way.
    """

    if not depths or min(depths) <= 4:
        raise ValueError("deeper delegation depth probe requires depths beyond the committed ceiling (4)")
    tasks = TransportTask.load_many(TRANSPORT_FIXTURE)
    benchmark = ConstraintTransportBenchmark(tasks)
    outcomes = [
        benchmark.run_ood_depth(condition, task, depth)
        for depth in depths
        for condition in TRANSPORT_CONDITIONS
        for task in tasks
    ]
    typed = [outcome for outcome in outcomes if outcome.condition == "typed_guarded"]
    baseline = [outcome for outcome in outcomes if outcome.condition == "lossy_prompt"]
    typed_joint = _rate(typed, "joint_success")
    baseline_joint = _rate(baseline, "joint_success")
    delta = typed_joint - baseline_joint
    return {
        "probe_id": "deeper_delegation_depth",
        "depths": list(depths),
        "task_families": sorted({task.family for task in tasks}),
        "episode_count": len(outcomes),
        "typed_joint_success": typed_joint,
        "baseline_joint_success": baseline_joint,
        "joint_success_delta": delta,
        "typed_lineage_valid_beyond_ceiling": all(outcome.lineage_valid for outcome in typed),
        "typed_constraint_survival_beyond_ceiling": all(
            outcome.constraint_survival for outcome in typed
        ),
        "kill_triggered": delta < OOD_KILL_THRESHOLD,
        "rows": [outcome.to_dict() for outcome in outcomes],
    }


def generate_results(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    """Run both OOD probes against credential-free/deterministic adapters only.

    Writes the published, reproducible fixture-only bundle to `output_dir`
    (defaults under `results/`, safe to commit). This never touches the
    network; the optional live paraphrase rerun lives in
    `run_constraint_ood_live_smoke.py` and writes only under `artifacts/`.
    """

    paraphrase = run_held_out_paraphrase_probe(adapter_id="fixture")
    depth = run_deeper_delegation_depth_probe()

    gates = {
        "paraphrase_probe_used_fixture_adapter": paraphrase["adapter_id"] == "fixture",
        "paraphrase_no_provider_failures": not paraphrase["provider_failures"],
        "paraphrase_preserves_constraint_identity": paraphrase["preserves_constraint_identity"],
        "paraphrase_all_episodes_publishable": paraphrase["publishable_rows"]
        == paraphrase["episode_count"],
        "depth_probe_exceeds_committed_ceiling": min(depth["depths"]) > 4,
        "depth_probe_lineage_valid": depth["typed_lineage_valid_beyond_ceiling"],
        "depth_probe_constraint_survival": depth["typed_constraint_survival_beyond_ceiling"],
        "no_live_calls": True,
    }
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": "constraint_ood_fixture_2026_07_20",
        "tier": "fixture-executed",
        "probes": {
            "held_out_paraphrase": {k: v for k, v in paraphrase.items() if k != "rows"},
            "deeper_delegation_depth": {k: v for k, v in depth.items() if k != "rows"},
        },
        "kill_criteria": {
            "threshold": OOD_KILL_THRESHOLD,
            "metric": "joint_success delta (envelope_external_guards vs envelope_only / typed_guarded vs lossy_prompt)",
            "fixture_paraphrase_note": (
                "FixtureExecutor selects behavior from (family, condition) only "
                "and never reads instruction text, so this fixture-run "
                "paraphrase delta cannot demonstrate wording sensitivity in "
                "either direction. It only proves the paraphrase/harness "
                "mechanics run end to end. Run "
                "run_constraint_ood_live_smoke.py under GROUNDED_HARNESS_LIVE=1 "
                "for a real name-free wording-sensitivity signal."
            ),
            "deeper_depth_probe_kill_triggered": depth["kill_triggered"],
        },
        "gates": gates,
        "allowed_claim": (
            "Held-out paraphrased instructions run through the real "
            "condition_policy-enforced harness produce the same publishable "
            "episode mechanics as the committed wording under the "
            "deterministic fixture adapter, and typed constraint lineage and "
            "critical-violation avoidance survive delegation depths 5 and 6 "
            "on the committed deterministic task bank, beyond the frozen "
            "depth-1..4 ceiling."
        ),
        "non_claims": [
            "No live model, provider, or stochastic agent was evaluated in this bundle.",
            "The fixture-run paraphrase delta is mechanical, not evidence of "
            "wording-invariant model behavior; see run_constraint_ood_live_smoke.py.",
            "This bundle does not satisfy D3 confirmatory Constraint Transport.",
        ],
        "next_best_test": (
            "GROUNDED_HARNESS_LIVE=1 python3 -m "
            "experiments.grounded_statecharts.run_constraint_ood_live_smoke to "
            "measure the live, name-free joint_success delta against the "
            f"{OOD_KILL_THRESHOLD} kill threshold."
        ),
    }
    if not all(gates.values()):
        raise RuntimeError("constraint OOD fixture gates failed")
    _write_json(output_dir / "summary.json", summary)
    _write_jsonl(output_dir / "paraphrase_rows.jsonl", paraphrase["rows"])
    _write_jsonl(output_dir / "depth_rows.jsonl", depth["rows"])
    return summary
