#!/usr/bin/env python3
"""Learned object-slot perception for discovered 2A-v2 semantic profiles.

The discovered semantic-profile gate removed the supplied profile table, but it
still consumed algorithmic connected components. This sidecar transports that
same held-out transfer gate onto learned foreground slots. A tiny learned pixel
foreground model plus slot-local center search produces six object slots from
the RGB image; the discovered profile inducer then fits anonymous cluster-pair
profiles from intervention family success, bound/unbound utility gaps, and
action templates.

This is a learned object-slot bridge for the synthetic six-slot world, not a
natural-image or open-ended slot-attention result. The fixed slot layout and
contract-shaped feedback remain explicit scaffolds.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from experiments.concerned_syntax import rich_program_language as rich
from experiments.concerned_syntax.benchmark import (
    HIGH_CONCERN_KINDS,
    PARSES,
    make_trial,
)
from experiments.concerned_syntax.discovered_semantic_profiles import (
    DiscoveredSemanticInducer,
    DiscoveredSemanticResult,
    evaluate_discovered_agents,
    induce_discovered_semantic_profiles,
    summarize_inducer,
    summarize_results,
    summarize_seed_payloads,
    summarize_slice_payloads,
)
from experiments.concerned_syntax.learned_pixel_extractor import (
    LearnedPixelExtractor,
    attach_learned_components,
    summarize_extractor,
    train_learned_extractor,
)
from experiments.concerned_syntax.pixel_shapes import (
    IMAGE_SIZE,
    PixelExample,
    render_pixel_surface,
)


LEARNED_OBJECT_SLOT_AGENTS: tuple[str, ...] = (
    "learned_rich_program_composer",
    "learned_object_slot_family_only",
    "learned_object_slot_target_only",
    "learned_object_slot_rich_without_concern",
    "learned_object_slot_discovered_world_model",
)

AGENT_RENAME: dict[str, str] = {
    "discovered_semantic_family_only": "learned_object_slot_family_only",
    "discovered_semantic_target_only": "learned_object_slot_target_only",
    "discovered_semantic_rich_without_concern": (
        "learned_object_slot_rich_without_concern"
    ),
    "discovered_semantic_world_model": "learned_object_slot_discovered_world_model",
}

HELDOUT_ROLE_KINDS: tuple[str, ...] = HIGH_CONCERN_KINDS
HELDOUT_TRUE_PARSES: tuple[str, ...] = tuple(parse.name for parse in PARSES)


def make_filtered_raw_pixel_examples(
    *,
    trials: int,
    seed: int,
    include_kinds: set[str] | None = None,
    exclude_kinds: set[str] | None = None,
    include_true_parses: set[str] | None = None,
    exclude_true_parses: set[str] | None = None,
) -> list[PixelExample]:
    """Generate RGB examples without running connected-component extraction."""

    rng = random.Random(seed)
    examples: list[PixelExample] = []
    attempts = 0
    max_attempts = max(10_000, trials * 1_000)
    while len(examples) < trials and attempts < max_attempts:
        trial = make_trial(attempts, rng)
        attempts += 1
        if include_kinds is not None and trial.kind not in include_kinds:
            continue
        if exclude_kinds is not None and trial.kind in exclude_kinds:
            continue
        if (
            include_true_parses is not None
            and trial.true_parse.name not in include_true_parses
        ):
            continue
        if (
            exclude_true_parses is not None
            and trial.true_parse.name in exclude_true_parses
        ):
            continue
        examples.append(
            PixelExample(
                trial=trial,
                image=render_pixel_surface(trial),
                components=(),
            )
        )
    if len(examples) < trials:
        raise ValueError(
            f"could only generate {len(examples)} examples after {attempts} attempts"
        )
    return examples


def _slice_raw_examples(
    *,
    axis: str,
    heldout: str,
    train_trials: int,
    test_trials: int,
    seed: int,
) -> tuple[list[PixelExample], list[PixelExample]]:
    if axis == "role_kind":
        return (
            make_filtered_raw_pixel_examples(
                trials=train_trials,
                seed=seed,
                exclude_kinds={heldout},
            ),
            make_filtered_raw_pixel_examples(
                trials=test_trials,
                seed=seed + 1_300_000,
                include_kinds={heldout},
            ),
        )
    if axis == "true_parse":
        return (
            make_filtered_raw_pixel_examples(
                trials=train_trials,
                seed=seed,
                exclude_true_parses={heldout},
            ),
            make_filtered_raw_pixel_examples(
                trials=test_trials,
                seed=seed + 1_500_000,
                include_true_parses={heldout},
            ),
        )
    raise KeyError(axis)


def _rename_rows(
    rows: list[DiscoveredSemanticResult],
) -> list[DiscoveredSemanticResult]:
    return [
        replace(row, agent=AGENT_RENAME.get(row.agent, row.agent))
        for row in rows
    ]


def summarize_modal_slice_results(
    seed_payloads: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for seed_payload in seed_payloads:
        for slice_payload in seed_payload.get("slice_results", []):
            key = (str(slice_payload["axis"]), str(slice_payload["heldout"]))
            grouped.setdefault(key, []).append(slice_payload)

    slice_results: list[dict[str, Any]] = []
    for (axis, heldout), payloads in sorted(grouped.items()):
        slice_results.append(
            {
                "axis": axis,
                "heldout": heldout,
                "extractor_summary": summarize_seed_payloads(
                    payloads,
                    "extractor_summary",
                ),
                "semantic_summary": summarize_seed_payloads(
                    payloads,
                    "semantic_summary",
                ),
                "agent_summary": summarize_seed_payloads(
                    payloads,
                    "agent_summary",
                ),
            }
        )
    return slice_results


def _train_extractor_examples(
    *,
    trials: int,
    seed: int,
) -> list[PixelExample]:
    return make_filtered_raw_pixel_examples(trials=trials, seed=seed)


def run_slice(
    *,
    axis: str,
    heldout: str,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
    inducer: DiscoveredSemanticInducer,
    extractor: LearnedPixelExtractor,
) -> dict[str, Any]:
    raw_train, raw_test = _slice_raw_examples(
        axis=axis,
        heldout=heldout,
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
    )
    train_examples = attach_learned_components(raw_train, extractor)
    test_examples = attach_learned_components(raw_test, extractor)
    models = rich.train_rich_models(train_examples, seed=seed, epochs=epochs)
    rows = _rename_rows(
        evaluate_discovered_agents(
            test_examples,
            models,
            inducer,
            axis=axis,
            heldout=heldout,
        )
    )
    return {
        "axis": axis,
        "heldout": heldout,
        "extractor_summary": {
            "learned_object_slots": summarize_extractor(test_examples)
        },
        "semantic_summary": {
            "learned_object_slot_profile_inducer": summarize_inducer(
                test_examples,
                inducer,
            )
        },
        "agent_summary": summarize_results(rows),
        "results": [asdict(row) for row in rows],
    }


def run_experiment(
    *,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
    induction_calibration_trials: int = 600,
    extractor_calibration_trials: int = 600,
    extractor_epochs: int | None = None,
    extractor_samples_per_image: int = 96,
    heldout_kinds: tuple[str, ...] = HELDOUT_ROLE_KINDS,
    heldout_parses: tuple[str, ...] = HELDOUT_TRUE_PARSES,
) -> dict[str, Any]:
    effective_extractor_epochs = (
        max(10, epochs // 2) if extractor_epochs is None else extractor_epochs
    )
    raw_extractor_examples = _train_extractor_examples(
        trials=extractor_calibration_trials,
        seed=seed + 2_300_000,
    )
    calibration_extractor = train_learned_extractor(
        raw_extractor_examples,
        seed=seed + 2_500_000,
        epochs=effective_extractor_epochs,
        samples_per_image=extractor_samples_per_image,
    )
    raw_induction_examples = make_filtered_raw_pixel_examples(
        trials=induction_calibration_trials,
        seed=seed + 2_700_000,
    )
    induction_examples = attach_learned_components(
        raw_induction_examples,
        calibration_extractor,
    )
    inducer = induce_discovered_semantic_profiles(
        induction_examples,
        seed=seed + 2_900_000,
        epochs=max(20, epochs),
    )

    slice_payloads: list[dict[str, Any]] = []
    for offset, heldout_kind in enumerate(heldout_kinds):
        slice_payloads.append(
            run_slice(
                axis="role_kind",
                heldout=heldout_kind,
                train_trials=train_trials,
                test_trials=test_trials,
                seed=seed + offset * 10_000,
                epochs=epochs,
                inducer=inducer,
                extractor=calibration_extractor,
            )
        )
    for offset, heldout_parse in enumerate(heldout_parses):
        slice_payloads.append(
            run_slice(
                axis="true_parse",
                heldout=heldout_parse,
                train_trials=train_trials,
                test_trials=test_trials,
                seed=seed + 80_000 + offset * 10_000,
                epochs=epochs,
                inducer=inducer,
                extractor=calibration_extractor,
            )
        )

    return {
        "manifest": {
            "arc": "2A",
            "name": "learned_object_slots_discovered_profiles_transfer",
            "contract": "2A-v2-pixels-rich_programs-transfer",
            "train_trials": train_trials,
            "test_trials": test_trials,
            "induction_calibration_trials": induction_calibration_trials,
            "extractor_calibration_trials": extractor_calibration_trials,
            "extractor_epochs": effective_extractor_epochs,
            "extractor_samples_per_image": extractor_samples_per_image,
            "seed": seed,
            "epochs": epochs,
            "heldout_kinds": list(heldout_kinds),
            "heldout_parses": list(heldout_parses),
            "agents": list(LEARNED_OBJECT_SLOT_AGENTS),
            "program_families": list(rich.PROGRAM_FAMILIES),
            "image_size": IMAGE_SIZE,
            "perception": (
                "learned_foreground_slots_plus_slot_local_center_search"
            ),
            "semantic_induction": (
                "discovered_profiles_from_learned_object_slots"
            ),
            "provided_perception_priors": [
                "synthetic RGB renderer",
                "fixed six-slot layout",
                "slot-local center search",
            ],
            "removed_perception_priors": [
                "algorithmic connected-component extractor in accepted path",
            ],
            "provided_induction_priors": [
                "generic rich-program family menu",
                "bound/unbound parse alternatives",
            ],
            "removed_induction_priors": [
                "semantic kind profile table",
                "kind-to-family mapping",
                "kind-to-role-pair mapping",
                "kind-to-concern-weight mapping",
            ],
            "forbidden_induction_labels": [
                "visible role tokens",
                "example.trial.kind",
                "example.trial.roles",
                "supplied semantic profile table",
                "connected-component features in accepted path",
            ],
            "inducer": inducer.manifest_summary(),
        },
        "extractor_summary": summarize_seed_payloads(
            slice_payloads,
            "extractor_summary",
        ),
        "semantic_summary": summarize_seed_payloads(
            slice_payloads,
            "semantic_summary",
        ),
        "agent_summary": summarize_slice_payloads(slice_payloads),
        "slice_results": slice_payloads,
    }


def _manifest_text(manifest: dict[str, Any]) -> str:
    if "seeds" in manifest:
        return (
            f"{len(manifest['seeds'])} seeds, {manifest['train_trials']} train trials "
            f"per held-out slice/seed, {manifest['test_trials']} test trials per "
            f"held-out slice/seed, {manifest['induction_calibration_trials']} "
            f"profile-induction trials/seed, {manifest['extractor_calibration_trials']} "
            f"extractor calibration images/seed, {manifest['epochs']} SGD epochs, "
            f"{manifest['extractor_epochs']} extractor epochs, role held-outs "
            f"{', '.join(manifest['heldout_kinds'])}, parse held-outs "
            f"{', '.join(manifest['heldout_parses'])}."
        )
    return (
        f"{manifest['train_trials']} train trials per held-out slice, "
        f"{manifest['test_trials']} test trials per held-out slice, "
        f"{manifest['induction_calibration_trials']} profile-induction trials, "
        f"{manifest['extractor_calibration_trials']} extractor calibration images, "
        f"seed {manifest['seed']}, {manifest['epochs']} SGD epochs, "
        f"{manifest['extractor_epochs']} extractor epochs, role held-outs "
        f"{', '.join(manifest['heldout_kinds'])}, parse held-outs "
        f"{', '.join(manifest['heldout_parses'])}."
    )


def write_learned_object_slots_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["agent_summary"]
    extractor = payload["extractor_summary"]["learned_object_slots"]
    semantic = payload["semantic_summary"]["learned_object_slot_profile_inducer"]
    manifest = payload["manifest"]
    slice_results = payload.get("slice_results") or summarize_modal_slice_results(
        payload.get("results", [])
    )
    lines = [
        "# Learned Object Slots Discovered Profiles Transfer",
        "",
        "Date: 2026-06-22",
        "",
        (
            "Question: can learned foreground object slots replace algorithmic "
            "connected components while preserving discovered semantic profiles "
            "and the held-out `2A-v2-pixels-rich_programs` transfer gate?"
        ),
        "",
        f"Manifest: {_manifest_text(manifest)}",
        "",
        "## Learned Object Slots",
        "",
        "| Count | Slot recovery | Scene recovery | Center error |",
        "|---:|---:|---:|---:|",
        (
            "| {count:.3f} | {slot:.3f} | {scene:.3f} | {error:.3f} |".format(
                count=extractor["component_count_rate"],
                slot=extractor["slot_recovery_rate"],
                scene=extractor["scene_recovery_rate"],
                error=extractor["mean_center_error"],
            )
        ),
        "",
        "## Induced Semantics",
        "",
        "| Clusters | Profiles | Cluster purity | Family | Pair | Action template |",
        "|---:|---:|---:|---:|---:|---:|",
        (
            "| {clusters:.0f} | {profiles:.0f} | {purity:.3f} | "
            "{family:.3f} | {pair:.3f} | {action:.3f} |".format(
                clusters=semantic["cluster_count"],
                profiles=semantic["profile_count"],
                purity=semantic["profile_cluster_purity"],
                family=semantic["semantic_family_accuracy"],
                pair=semantic["semantic_pair_accuracy"],
                action=semantic["profile_action_consistency"],
            )
        ),
        "",
        "## Gate Summary",
        "",
        (
            "| Agent | Transfer | Purity | Sem family | Sem pair | Action template | "
            "Family high | Target high | Useful high | Rich high | Low prog | Regret |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for agent, stats in sorted(summary.items()):
        lines.append(
            "| {agent} | {transfer:.3f} | {purity:.3f} | {sem_family:.3f} | "
            "{pair:.3f} | {template:.3f} | {family:.3f} | {target:.3f} | "
            "{useful:.3f} | {rich_prog:.3f} | {low:.3f} | {regret:.3f} |".format(
                agent=agent,
                transfer=stats.get("transfer_gate_pass", 0.0),
                purity=stats["profile_cluster_purity"],
                sem_family=stats["semantic_family_accuracy"],
                pair=stats["semantic_pair_accuracy"],
                template=stats["profile_action_consistency"],
                family=stats["family_accuracy_high_concern"],
                target=stats["target_accuracy_high_concern"],
                useful=stats["useful_program_rate_high_concern"],
                rich_prog=stats["rich_program_rate_high_concern"],
                low=stats["low_concern_program_rate"],
                regret=stats["mean_regret"],
            )
        )

    lines.extend(
        [
            "",
            "## Held-Out Slices",
            "",
            (
                "| Axis | Held-out | Agent | Slot recovery | Purity | Sem pair | "
                "Target high | Useful high | Low prog | Gate |"
            ),
            "|---|---|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for slice_payload in slice_results:
        axis = slice_payload["axis"]
        heldout = slice_payload["heldout"]
        slot_recovery = slice_payload["extractor_summary"]["learned_object_slots"][
            "slot_recovery_rate"
        ]
        for agent, stats in sorted(slice_payload["agent_summary"].items()):
            gate_pass = float(stats["gate_pass"]) >= 0.999
            lines.append(
                "| {axis} | {heldout} | {agent} | {slot:.3f} | {purity:.3f} | "
                "{pair:.3f} | {target:.3f} | {useful:.3f} | {low:.3f} | "
                "{gate} |".format(
                    axis=axis,
                    heldout=heldout,
                    agent=agent,
                    slot=slot_recovery,
                    purity=stats["profile_cluster_purity"],
                    pair=stats["semantic_pair_accuracy"],
                    target=stats["target_accuracy_high_concern"],
                    useful=stats["useful_program_rate_high_concern"],
                    low=stats["low_concern_program_rate"],
                    gate="PASS" if gate_pass else "fail",
                )
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The accepted path does not run the connected-component extractor. "
                "It trains a foreground pixel model, uses fixed slot-local center "
                "search to produce six object slots, induces semantic profiles "
                "from those learned slots, and then runs the same held-out "
                "transfer verifier as the discovered-profile result."
            ),
            "",
            (
                "This is not natural-image object discovery or a full "
                "slot-attention model. The renderer, six-slot layout, and "
                "contract-shaped intervention feedback remain scaffolds. The "
                "bounded claim is that discovered semantic profiles no longer "
                "depend on algorithmic connected-component features in this "
                "synthetic 2A-v2 world."
            ),
            "",
            "Raw JSON remains local under `artifacts/concerned_syntax/`.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-trials", type=int, default=1200)
    parser.add_argument("--test-trials", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260622)
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--induction-calibration-trials", type=int, default=600)
    parser.add_argument("--extractor-calibration-trials", type=int, default=600)
    parser.add_argument("--extractor-epochs", type=int)
    parser.add_argument("--extractor-samples-per-image", type=int, default=96)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    payload = run_experiment(
        train_trials=args.train_trials,
        test_trials=args.test_trials,
        seed=args.seed,
        epochs=args.epochs,
        induction_calibration_trials=args.induction_calibration_trials,
        extractor_calibration_trials=args.extractor_calibration_trials,
        extractor_epochs=args.extractor_epochs,
        extractor_samples_per_image=args.extractor_samples_per_image,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.report:
        write_learned_object_slots_report(args.report, payload)

    print("=== Learned Object Slots Discovered Profiles Transfer Summary ===")
    extractor = payload["extractor_summary"]["learned_object_slots"]
    semantic = payload["semantic_summary"]["learned_object_slot_profile_inducer"]
    print(
        "learned_object_slots "
        f"slot={extractor['slot_recovery_rate']:.3f} "
        f"scene={extractor['scene_recovery_rate']:.3f} "
        f"error={extractor['mean_center_error']:.3f}"
    )
    print(
        "profile_inducer "
        f"clusters={semantic['cluster_count']:.0f} "
        f"profiles={semantic['profile_count']:.0f} "
        f"purity={semantic['profile_cluster_purity']:.3f} "
        f"family={semantic['semantic_family_accuracy']:.3f} "
        f"pair={semantic['semantic_pair_accuracy']:.3f} "
        f"action_template={semantic['profile_action_consistency']:.3f}"
    )
    for agent, stats in sorted(payload["agent_summary"].items()):
        print(
            f"{agent:46s} transfer={stats['transfer_gate_pass']} "
            f"family={stats['family_accuracy_high_concern']:.3f} "
            f"target={stats['target_accuracy_high_concern']:.3f} "
            f"useful={stats['useful_program_rate_high_concern']:.3f} "
            f"low_prog={stats['low_concern_program_rate']:.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
