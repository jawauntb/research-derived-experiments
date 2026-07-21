"""Pilot slice runner for the load-bearing prose test.

Loads the frozen fixture plans, extracts claims, produces
delete/negate/paraphrase ablations, runs a baseline plus each
ablation through the plan executor, applies CT harness enforcement,
computes per-claim ``Verdict`` values, and emits sanitized public
rows plus a summary receipt under ``results/pilot/``.

Defaults to the deterministic ``PlanSensitiveFixtureExecutor`` so
``python3 -m experiments.load_bearing_prose_test.run_lbpt_pilot``
runs in CI with zero spend. Pass ``--executor live`` and set
``LBPT_LIVE=1`` plus the CT live env vars to spend against a real
provider.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments.load_bearing_prose_test.ablation import ablate_bundle
from experiments.load_bearing_prose_test.claims import (
    Ablation,
    AblationKind,
    ClaimBundle,
    Verdict,
    digest,
)
from experiments.load_bearing_prose_test.executor import (
    PlanEpisode,
    PlanExecutor,
    build_plan_executor,
    run_plan_episode,
)
from experiments.load_bearing_prose_test.extraction import (
    RuleBasedExtractor,
    default_kappa_vocabulary,
)
from experiments.load_bearing_prose_test.scoring import (
    ClaimVerdictInputs,
    CommitmentSurface,
    aggregate_metrics,
    classify_claim,
    commitment_surface,
)


PACKAGE_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = PACKAGE_DIR / "fixtures"
DEFAULT_RESULTS_DIR = PACKAGE_DIR / "results" / "pilot"
DEFAULT_SUMMARY_PATH = DEFAULT_RESULTS_DIR / "summary.json"
DEFAULT_ROWS_PATH = DEFAULT_RESULTS_DIR / "rows.jsonl"

FIXTURE_FILES: tuple[str, ...] = (
    "artifact_completion_plans.json",
    "recursive_constrained_tool_use_plans.json",
)

# The primary contrast: envelope_only is the raw-executor condition where
# what the plan says most directly steers commitment. envelope_external_guards
# is a control (harness enforcement cleans up regardless of plan wording, so
# ablation deltas should be near zero) — the pilot runs both so Week 3 can
# report the sanity contrast alongside the primary metric.
PRIMARY_CONDITION_BY_FAMILY: dict[str, str] = {
    "artifact_completion": "statechart_g0",
    "recursive_constrained_tool_use": "envelope_only",
}
CONTROL_CONDITION_BY_FAMILY: dict[str, str] = {
    "artifact_completion": "statechart_g3",
    "recursive_constrained_tool_use": "envelope_external_guards",
}


@dataclass(frozen=True)
class PilotRow:
    """One serializable claim-level row emitted by the pilot."""

    family: str
    plan_id: str
    plan_digest: str
    claim_id: str
    claim_text: str
    kappa_mention: bool
    primary_condition: str
    control_condition: str
    baseline_surface_digest: str
    delete_delta: bool
    negate_delta: bool
    paraphrase_delta: bool
    is_load_bearing: bool
    paraphrase_invariant: bool
    control_delete_delta: bool
    control_negate_delta: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "plan_id": self.plan_id,
            "plan_digest": self.plan_digest,
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "kappa_mention": self.kappa_mention,
            "primary_condition": self.primary_condition,
            "control_condition": self.control_condition,
            "baseline_surface_digest": self.baseline_surface_digest,
            "delete_delta": self.delete_delta,
            "negate_delta": self.negate_delta,
            "paraphrase_delta": self.paraphrase_delta,
            "is_load_bearing": self.is_load_bearing,
            "paraphrase_invariant": self.paraphrase_invariant,
            "control_delete_delta": self.control_delete_delta,
            "control_negate_delta": self.control_negate_delta,
        }


def _load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _episode(
    *,
    plan_id: str,
    variant: str,
    plan_text: str,
    family: str,
    task_id: str,
    condition: str,
    kappa: dict[str, Any],
    seed: int,
) -> PlanEpisode:
    return PlanEpisode(
        plan_id=plan_id,
        variant=variant,
        plan_text=plan_text,
        family=family,
        task_id=task_id,
        condition=condition,
        required_artifact=kappa.get("required_artifact"),
        required_capabilities=tuple(kappa.get("required_capabilities", [])),
        forbidden_capabilities=tuple(kappa.get("forbidden_capabilities", [])),
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


def _plan_row(
    *,
    family: str,
    plan_id: str,
    plan_text: str,
    kappa: dict[str, Any],
    executor: PlanExecutor,
    seed: int,
) -> tuple[list[PilotRow], list[Verdict], list[Verdict]]:
    """Run baseline + ablations under both primary and control conditions."""

    extractor = RuleBasedExtractor(
        kappa=default_kappa_vocabulary(
            capabilities=(
                *kappa.get("required_capabilities", []),
                *kappa.get("forbidden_capabilities", []),
            ),
            artifacts=(kappa["required_artifact"],)
            if "required_artifact" in kappa
            else (),
        )
    )
    bundle: ClaimBundle = extractor.extract(plan_id=plan_id, plan_text=plan_text)
    ablations = ablate_bundle(bundle, plan_text)
    ablation_lookup: dict[tuple[str, AblationKind], Ablation] = {
        (a.claim_id, a.kind): a for a in ablations.ablations
    }

    primary_condition = PRIMARY_CONDITION_BY_FAMILY[family]
    control_condition = CONTROL_CONDITION_BY_FAMILY[family]

    def _surfaces_for_condition(condition: str) -> tuple[
        CommitmentSurface, dict[str, dict[AblationKind, CommitmentSurface]]
    ]:
        baseline_ep = _episode(
            plan_id=plan_id,
            variant=f"baseline::{condition}",
            plan_text=plan_text,
            family=family,
            task_id=plan_id,
            condition=condition,
            kappa=kappa,
            seed=seed,
        )
        baseline_surface = _surface_for(episode=baseline_ep, executor=executor)
        per_claim: dict[str, dict[AblationKind, CommitmentSurface]] = {}
        for claim in bundle.claims:
            per_claim[claim.claim_id] = {}
            for kind in (
                AblationKind.DELETE,
                AblationKind.NEGATE,
                AblationKind.PARAPHRASE,
            ):
                ablation = ablation_lookup[(claim.claim_id, kind)]
                ep = _episode(
                    plan_id=plan_id,
                    variant=f"{kind.value}::{claim.claim_id}::{condition}",
                    plan_text=ablation.modified_plan,
                    family=family,
                    task_id=plan_id,
                    condition=condition,
                    kappa=kappa,
                    seed=seed,
                )
                per_claim[claim.claim_id][kind] = _surface_for(
                    episode=ep, executor=executor
                )
        return baseline_surface, per_claim

    primary_base, primary_per_claim = _surfaces_for_condition(primary_condition)
    control_base, control_per_claim = _surfaces_for_condition(control_condition)

    rows: list[PilotRow] = []
    primary_verdicts: list[Verdict] = []
    control_verdicts: list[Verdict] = []
    for claim in bundle.claims:
        primary_v = classify_claim(
            ClaimVerdictInputs(
                claim=claim,
                baseline=primary_base,
                surfaces=primary_per_claim[claim.claim_id],
            )
        )
        control_v = classify_claim(
            ClaimVerdictInputs(
                claim=claim,
                baseline=control_base,
                surfaces=control_per_claim[claim.claim_id],
            )
        )
        primary_verdicts.append(primary_v)
        control_verdicts.append(control_v)
        rows.append(
            PilotRow(
                family=family,
                plan_id=plan_id,
                plan_digest=bundle.plan_digest,
                claim_id=claim.claim_id,
                claim_text=claim.text,
                kappa_mention=claim.mentions_kappa,
                primary_condition=primary_condition,
                control_condition=control_condition,
                baseline_surface_digest=_surface_digest(primary_base),
                delete_delta=primary_v.delete_delta,
                negate_delta=primary_v.negate_delta,
                paraphrase_delta=primary_v.paraphrase_delta,
                is_load_bearing=primary_v.is_load_bearing,
                paraphrase_invariant=primary_v.paraphrase_invariant,
                control_delete_delta=control_v.delete_delta,
                control_negate_delta=control_v.negate_delta,
            )
        )
    return rows, primary_verdicts, control_verdicts


def build_pilot_output(
    *,
    executor: PlanExecutor,
    seed: int = 20260721,
) -> tuple[list[PilotRow], dict[str, Any]]:
    all_rows: list[PilotRow] = []
    family_metrics: dict[str, dict[str, Any]] = {}
    all_primary: list[Verdict] = []
    all_control: list[Verdict] = []
    for fixture_name in FIXTURE_FILES:
        fixture = _load_fixture(FIXTURES_DIR / fixture_name)
        family = fixture["family"]
        kappa = fixture["kappa"]
        family_primary: list[Verdict] = []
        family_control: list[Verdict] = []
        for plan in fixture["plans"]:
            rows, primary_verdicts, control_verdicts = _plan_row(
                family=family,
                plan_id=plan["plan_id"],
                plan_text=plan["plan_text"],
                kappa=kappa,
                executor=executor,
                seed=seed,
            )
            all_rows.extend(rows)
            family_primary.extend(primary_verdicts)
            family_control.extend(control_verdicts)
        primary_metrics = aggregate_metrics(family_primary)
        control_metrics = aggregate_metrics(family_control)
        family_metrics[family] = {
            "kappa": kappa,
            "primary_condition": PRIMARY_CONDITION_BY_FAMILY[family],
            "control_condition": CONTROL_CONDITION_BY_FAMILY[family],
            "primary": primary_metrics.to_dict(),
            "control": control_metrics.to_dict(),
        }
        all_primary.extend(family_primary)
        all_control.extend(family_control)
    overall_primary = aggregate_metrics(all_primary)
    overall_control = aggregate_metrics(all_control)
    payload = {
        "schema_version": "1.0",
        "run_id": f"lbpt_pilot_{executor.adapter_id}_{seed}",
        "package": "load_bearing_prose_test",
        "seed": seed,
        "adapter_id": executor.adapter_id,
        "provider_id": executor.provider_id,
        "model_id": executor.model_id,
        "n_rows": len(all_rows),
        "families": family_metrics,
        "overall": {
            "primary": overall_primary.to_dict(),
            "control": overall_control.to_dict(),
        },
    }
    payload["rows_digest"] = digest([row.to_dict() for row in all_rows])
    payload["summary_digest"] = digest(payload)
    return all_rows, payload


def write_pilot_output(
    *,
    executor: PlanExecutor,
    seed: int = 20260721,
    rows_path: Path = DEFAULT_ROWS_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
) -> tuple[Path, Path]:
    rows, summary = build_pilot_output(executor=executor, seed=seed)
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    with rows_path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row.to_dict(), sort_keys=True) + "\n")
    summary_path.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    return rows_path, summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--executor",
        choices=("fixture", "live"),
        default="fixture",
        help="pick the plan executor",
    )
    parser.add_argument("--seed", type=int, default=20260721)
    parser.add_argument("--rows", type=Path, default=DEFAULT_ROWS_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args()
    executor = build_plan_executor(kind=args.executor)
    rows_path, summary_path = write_pilot_output(
        executor=executor,
        seed=args.seed,
        rows_path=args.rows,
        summary_path=args.summary,
    )
    print(f"wrote rows to {rows_path}")
    print(f"wrote summary to {summary_path}")


if __name__ == "__main__":
    main()
