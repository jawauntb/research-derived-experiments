"""Validation invariants for IDENT items (gates G1–G4 construction checks)."""

from __future__ import annotations

from dataclasses import dataclass

from experiments.ident.equivalence import equivalence_class
from experiments.ident.schemas import IdentItem
from experiments.ident.separators import (
    identifies_truth,
    separates,
    weakest_identifying_separators,
    weakest_separators,
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...]

    @property
    def failed(self) -> bool:
        return not self.ok


LEAKY_NAME_TOKENS = (
    "true",
    "correct",
    "actual",
    "oracle",
    "answer",
    "ground_truth",
    "winner",
)


def _passive_bound(live_size: int) -> float:
    if live_size <= 0:
        return 0.0
    return 1.0 / float(live_size)


def validate_item(item: IdentItem) -> ValidationResult:
    errors: list[str] = []

    if len(item.hypotheses) < 2:
        errors.append("item must include at least two hypotheses")

    if item.true_hypothesis not in item.hypotheses:
        errors.append("true_hypothesis not in hypotheses")

    if item.answer != item.true_hypothesis and item.answer not in item.hypotheses:
        # Answer may be a mechanism-dependent query result equal to true hyp id in v1.
        errors.append("answer must identify the true hypothesis in v1")

    # Build observation response map: prior experiment ids must appear in a full table.
    # Generators store prior outcomes inside response_table under the same experiment ids
    # used in prior_observations, plus candidate intervention ids.
    observed_responses = item.response_table
    live = equivalence_class(
        item.hypotheses, item.prior_observations, observed_responses
    )
    if sorted(live) != sorted(item.equivalence_class_before):
        errors.append(
            "equivalence_class_before mismatch: "
            f"computed={sorted(live)} recorded={sorted(item.equivalence_class_before)}"
        )

    if len(live) < 2:
        errors.append("G1 fail: initial equivalence class must have size >= 2")

    if item.true_hypothesis not in live:
        errors.append("true hypothesis must match all prior observations")

    # Latent answer must differ across at least two live hypotheses.
    # In v1 the answer is the hypothesis id, so distinct live hyps suffice.
    if len(set(live)) < 2:
        errors.append("latent answer does not differ across live hypotheses")

    candidates = item.candidate_interventions
    if not candidates:
        errors.append("no candidate interventions")

    sep_ids = {
        g.id
        for g in candidates
        if separates(g.id, live, item.response_table)
    }
    if not sep_ids:
        errors.append("G2 fail: no one-step separator among candidates")

    identifying = {
        g.id
        for g in candidates
        if identifies_truth(g.id, live, item.true_hypothesis, item.response_table)
    }
    if not identifying:
        errors.append(
            "active sufficiency fail: no one-step intervention uniquely identifies "
            "the true hypothesis"
        )

    # Annotate minimum separators as minimum-cost *identifying* separators when available.
    computed_mins = [
        g.id
        for g in weakest_identifying_separators(
            live, candidates, item.response_table, item.true_hypothesis
        )
    ]
    if not computed_mins:
        computed_mins = [
            g.id for g in weakest_separators(live, candidates, item.response_table)
        ]
    if sorted(computed_mins) != sorted(item.minimum_separators):
        errors.append(
            "minimum_separators mismatch: "
            f"computed={computed_mins} recorded={item.minimum_separators}"
        )

    expected_bound = _passive_bound(len(live))
    if abs(item.passive_chance_bound - expected_bound) > 1e-12:
        errors.append(
            f"passive_chance_bound mismatch: got {item.passive_chance_bound}, "
            f"expected {expected_bound}"
        )

    # Leak checks: names/descriptions must not reveal truth.
    truth = item.true_hypothesis.lower()
    for hyp_id, desc in item.hypothesis_descriptions.items():
        blob = f"{hyp_id} {desc}".lower()
        if "true mechanism" in blob or "correct mechanism" in blob:
            errors.append(f"leaky hypothesis description for {hyp_id}")
        for token in LEAKY_NAME_TOKENS:
            if token in hyp_id.lower():
                errors.append(f"leaky hypothesis id token '{token}' in {hyp_id}")

    for g in candidates:
        blob = f"{g.id} {g.description}".lower()
        if truth in blob and truth not in {"h0", "h1", "a", "b"}:
            # Avoid false positives on short ids; still block explicit truth strings.
            if len(truth) >= 4 and truth in g.description.lower():
                errors.append(f"intervention description leaks true hypothesis: {g.id}")
        for token in ("separates", "correct intervention", "minimum separator"):
            if token in blob:
                errors.append(f"intervention description leaks separator status: {g.id}")

    # Ordering must not encode truth: first hypothesis / first intervention alone
    # is not an error, but metadata must not include truth markers for public view.
    if item.metadata.get("public_true_hypothesis") is not None:
        errors.append("metadata must not expose public_true_hypothesis")

    return ValidationResult(ok=not errors, errors=tuple(errors))


def validate_split(items: list[IdentItem]) -> ValidationResult:
    errors: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item.item_id in seen:
            errors.append(f"duplicate item_id {item.item_id}")
        seen.add(item.item_id)
        result = validate_item(item)
        if result.failed:
            errors.extend(f"{item.item_id}: {err}" for err in result.errors)
    return ValidationResult(ok=not errors, errors=tuple(errors))
