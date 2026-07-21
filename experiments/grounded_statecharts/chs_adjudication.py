"""Independent CHS sealing from pre-registered paired-condition contrasts.

Seals are derived from public-row matched interventions (same task + repeat,
different harness condition), not from the heuristic harvest map. Sealed labels
stay under artifacts/ until an explicit publish step; they never enter episode
rows.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.sanitization import sanitize_public_row

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "grounded_statecharts" / "chs_sealed_live"

PROTOCOL_VERSION = "paired-contrast-seal-1"
PROTOCOL = {
    "version": PROTOCOL_VERSION,
    "independence": (
        "Labels are produced from matched public-row condition contrasts only. "
        "The heuristic harvest predicted_component is never consulted."
    ),
    "rules": (
        {
            "rule_id": "ct_external_recovers_envelope_fail",
            "family": "recursive_constrained_tool_use",
            "fail_condition": "envelope_only",
            "recover_condition": "envelope_external_guards",
            "fail_requires": {"joint_success": False},
            "recover_requires": {"joint_success": True},
            "responsible_component": "orchestration",
            "rationale": (
                "Matched external-guard recovery after envelope-only joint failure "
                "attributes the failure to missing external orchestration guards."
            ),
        },
        {
            "rule_id": "gs_g3_repairs_g0_false_completion",
            "family": "artifact_completion",
            "fail_condition": "statechart_g0",
            "recover_condition": "statechart_g3",
            "fail_requires": {"false_completion": True},
            "recover_requires": {"false_completion": False, "joint_success": True},
            "responsible_component": "orchestration",
            "rationale": (
                "Matched G3 recovery after G0 false completion attributes the "
                "failure to self-report orchestration without artifact guards."
            ),
        },
        {
            "rule_id": "wrong_edge_output_surface",
            "family": None,
            "fail_condition": "wrong_edge_guard",
            "recover_condition": None,
            "fail_requires": {"invalid_transition": True, "joint_success": False},
            "recover_requires": None,
            "responsible_component": "output",
            "rationale": (
                "Wrong-edge invalid transitions are sealed to the output surface "
                "by construction of the wrong_edge_guard condition."
            ),
        },
    ),
    "kill_criteria": (
        "Do not treat heuristic harvest agreement as CHS1.",
        "Do not write responsible_component into public episode rows.",
        "Abstain when a paired recover row is missing or contradicts the rule.",
        "Do not claim six-surface CHS1 from orchestration/output-only seals.",
    ),
}


def _load_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        receipt = sanitize_public_row(row)
        if not receipt.ok:
            raise ValueError(f"row failed sanitization: {row.get('episode_id')}")
        rows.append(dict(receipt.public_row))
    return rows


def _matches(row: Mapping[str, Any], requires: Mapping[str, Any] | None) -> bool:
    if requires is None:
        return True
    return all(row.get(key) is value for key, value in requires.items())


def seal_from_paired_contrasts(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, object]]:
    """Seal labels using only pre-registered paired-condition contrasts."""

    by_key: dict[tuple[str, int], dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for row in rows:
        key = (str(row["task_id"]), int(row["repeat_index"]))
        by_key[key][str(row["condition"])] = row

    sealed: list[dict[str, object]] = []
    for (task_id, repeat_index), conditions in sorted(by_key.items()):
        for rule in PROTOCOL["rules"]:
            family = rule["family"]
            fail_condition = rule["fail_condition"]
            fail_row = conditions.get(str(fail_condition))
            if fail_row is None:
                continue
            if family is not None and fail_row.get("family") != family:
                continue
            if not _matches(fail_row, rule["fail_requires"]):
                continue
            recover_condition = rule["recover_condition"]
            if recover_condition is not None:
                recover_row = conditions.get(str(recover_condition))
                if recover_row is None or not _matches(recover_row, rule["recover_requires"]):
                    continue
                evidence = {
                    "fail_result_digest": fail_row["result_digest"],
                    "recover_result_digest": recover_row["result_digest"],
                    "recover_condition": recover_condition,
                }
            else:
                evidence = {
                    "fail_result_digest": fail_row["result_digest"],
                    "recover_result_digest": None,
                    "recover_condition": None,
                }
            sealed.append(
                {
                    "case_id": f"seal:{fail_row['result_digest']}",
                    "source_episode_id": fail_row["episode_id"],
                    "source_result_digest": fail_row["result_digest"],
                    "task_id": task_id,
                    "family": fail_row["family"],
                    "repeat_index": repeat_index,
                    "fail_condition": fail_condition,
                    "responsible_component": rule["responsible_component"],
                    "fault_id": rule["rule_id"],
                    "rule_id": rule["rule_id"],
                    "protocol_version": PROTOCOL_VERSION,
                    "label_status": "sealed_by_paired_contrast",
                    "evidence": evidence,
                }
            )
    return sealed


def generate_results(
    *,
    rows_path: Path,
    output_dir: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    if "results" in output_dir.parts:
        raise RuntimeError("refusing to write sealed live labels under results/")
    rows = _load_rows(rows_path)
    sealed = seal_from_paired_contrasts(rows)
    components = sorted({str(item["responsible_component"]) for item in sealed})
    summary = {
        "schema_version": "1.0",
        "tier": "live-paired-contrast-seal",
        "protocol_version": PROTOCOL_VERSION,
        "protocol": PROTOCOL,
        "source_rows": str(rows_path),
        "source_row_count": len(rows),
        "sealed_count": len(sealed),
        "components_covered": components,
        "gates": {
            "labels_under_artifacts_only": "results" not in output_dir.parts,
            "heuristic_harvest_not_used": True,
            "six_surface_chs1_claim": False,
            "claim_boundary": (
                "Paired-contrast seals support a narrow orchestration/output "
                "CHS bridge. Full CHS1 still needs withheld labels across all "
                "six surfaces plus matched repair/placebo search."
            ),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "labels.jsonl").write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in sealed)
    )
    return summary
