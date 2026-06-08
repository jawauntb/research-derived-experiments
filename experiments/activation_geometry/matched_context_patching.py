#!/usr/bin/env python3
"""Helpers for matched-context activation patching diagnostics."""

from __future__ import annotations

from typing import Any


OPTION_ROLES = ("source", "target", "distractor")
PATCH_MODES = ("target", "distractor", "random", "source_noop")


def option_order_key(order: tuple[str, str, str]) -> str:
    initials = {
        "source": "s",
        "target": "t",
        "distractor": "d",
    }
    return "".join(initials[role] for role in order)


def calibration_prompt(
    *,
    source_text: str,
    labels_by_role: dict[str, str],
    option_order: tuple[str, str, str],
) -> str:
    invalid_roles = sorted(set(option_order) - set(OPTION_ROLES))
    if invalid_roles:
        raise ValueError(f"Unknown option roles: {', '.join(invalid_roles)}")
    lines = [
        source_text,
        "",
        "Choose the closest related concept.",
    ]
    for slot, role in zip(("A", "B", "C"), option_order, strict=True):
        lines.append(f"{slot}. {labels_by_role[role]}")
    lines.append("Answer:")
    return "\n".join(lines)


def patch_concept_for_mode(pair: dict[str, Any], mode: str) -> str:
    if mode == "target":
        return str(pair["right"])
    if mode == "distractor":
        return str(pair["distractor"])
    if mode == "random":
        return str(pair["random_patch"])
    if mode == "source_noop":
        return str(pair["left"])
    raise ValueError(f"Unknown patch mode: {mode}")


def matched_context_prompt(
    *,
    pair: dict[str, Any],
    mode: str,
    source_text_by_concept: dict[str, str],
    labels_by_role: dict[str, str],
    option_order: tuple[str, str, str],
) -> dict[str, str]:
    patch_concept_id = patch_concept_for_mode(pair, mode)
    if patch_concept_id not in source_text_by_concept:
        raise ValueError(f"Missing source text for patch concept: {patch_concept_id}")
    return {
        "patch_concept": patch_concept_id,
        "prompt": calibration_prompt(
            source_text=source_text_by_concept[patch_concept_id],
            labels_by_role=labels_by_role,
            option_order=option_order,
        ),
    }
