"""Small deterministic assumption examples for the math primer.

The functions deliberately use finite sets, permutations, and scalar weights so
that every assumption card can be inspected without a scientific-computing
stack. Each card pairs a satisfying example with a case where the named
assumption or bridge predicate fails. These cases do not by themselves prove
that an assumption is necessary for a broader theorem.
"""

from __future__ import annotations

from itertools import combinations
from typing import Callable, Iterable, Mapping, Sequence, TypedDict


class AssumptionResultPayload(TypedDict):
    theorem_id: str
    assumption: str
    example_satisfies_assumption: bool
    failure_case_detected: bool
    satisfying_example: dict[str, object]
    failure_case: dict[str, object]


def _sorted_items(values: Iterable[str]) -> list[str]:
    return sorted(values)


def block_disjointness(blocks: Mapping[str, set[str]]) -> dict[str, object]:
    overlaps = {
        f"{left}|{right}": _sorted_items(blocks[left] & blocks[right])
        for left, right in combinations(sorted(blocks), 2)
        if blocks[left] & blocks[right]
    }
    union_size = len(set().union(*blocks.values())) if blocks else 0
    sum_sizes = sum(len(block) for block in blocks.values())
    return {
        "disjoint": not overlaps,
        "overlaps": overlaps,
        "union_size": union_size,
        "sum_sizes": sum_sizes,
        "bridge_identity_holds": union_size == sum_sizes,
    }


def equal_mass_selector(
    block_masses: Mapping[str, float], compatible: Mapping[str, set[str]]
) -> dict[str, object]:
    scores = {
        hypothesis: sum(block_masses[block] for block in blocks)
        for hypothesis, blocks in compatible.items()
    }
    count_scores = {hypothesis: len(blocks) for hypothesis, blocks in compatible.items()}
    weighted_order = sorted(scores, key=lambda hypothesis: (-scores[hypothesis], hypothesis))
    count_order = sorted(count_scores, key=lambda hypothesis: (-count_scores[hypothesis], hypothesis))
    count_winners = sorted(
        hypothesis for hypothesis, score in count_scores.items() if score == max(count_scores.values())
    )
    weighted_winners = sorted(
        hypothesis for hypothesis, score in scores.items() if score == max(scores.values())
    )
    return {
        "block_masses": dict(sorted(block_masses.items())),
        "count_scores": count_scores,
        "weighted_scores": scores,
        "count_order": count_order,
        "weighted_order": weighted_order,
        "count_winners": count_winners,
        "weighted_winners": weighted_winners,
        "argmax_agrees": count_winners == weighted_winners,
    }


def complete_block_coverage(
    blocks: Mapping[str, set[str]], covered: Mapping[str, set[str]], compatible: set[str]
) -> dict[str, object]:
    claimed_mass = sum(len(blocks[block]) for block in compatible)
    actual_mass = sum(len(covered[block]) for block in compatible)
    complete = all(covered[block] == blocks[block] for block in compatible)
    return {
        "compatible_blocks": sorted(compatible),
        "complete": complete,
        "claimed_mass": claimed_mass,
        "actual_mass": actual_mass,
        "bridge_identity_holds": claimed_mass == actual_mass,
    }


def coherent_c2_action(
    actions: Mapping[str, Callable[[int], int]], outputs: Sequence[int]
) -> dict[str, object]:
    output_set = set(outputs)
    closure_ok = all(
        actions[element](value) in output_set
        for element in ("e", "g")
        for value in outputs
    )
    identity_ok = all(actions["e"](value) == value for value in outputs)
    involution_ok = all(actions["g"](actions["g"](value)) == value for value in outputs)
    return {
        "closure_ok": closure_ok,
        "identity_ok": identity_ok,
        "involution_ok": involution_ok,
        "coherent": closure_ok and identity_ok and involution_ok,
    }


def bounded_transport_loss(values: Sequence[float], deltas: Sequence[float]) -> dict[str, object]:
    if len(values) < 2 or len(deltas) != len(values) - 1:
        raise ValueError("deltas must specify exactly one bound per transport step")
    losses = [left - right for left, right in zip(values, values[1:])]
    bounded = all(loss >= 0 and loss <= delta for loss, delta in zip(losses, deltas))
    lower_bound = values[0] - sum(deltas)
    return {
        "values": list(values),
        "declared_delta": list(deltas),
        "losses": losses,
        "monotone": all(loss >= 0 for loss in losses),
        "bounded": bounded,
        "lower_bound": lower_bound,
        "final_value": values[-1],
        "lower_bound_holds": values[-1] >= lower_bound,
    }


def gauge_separation(
    latent_values: Sequence[str], intervention_outputs: Mapping[str, Mapping[str, str]], eta: float
) -> dict[str, object]:
    pairs = list(combinations(latent_values, 2))
    pair_distances = {
        intervention: sum(
            intervention_outputs[intervention][left] != intervention_outputs[intervention][right]
            for left, right in pairs
        )
        for intervention in sorted(intervention_outputs)
    }
    max_distance = max(pair_distances.values(), default=0)
    return {
        "eta": eta,
        "pair_distances": pair_distances,
        "max_distance": max_distance,
        "gauge_fixed": max_distance >= eta,
    }


def commitment_effect(value_with: float, value_without: float, epsilon: float) -> dict[str, object]:
    effect = abs(value_with - value_without)
    return {
        "value_with": value_with,
        "value_without": value_without,
        "effect": effect,
        "epsilon": epsilon,
        "nonzero_effect": effect >= epsilon,
    }


def _assumption_case(
    theorem_id: str,
    assumption: str,
    satisfying_example: dict[str, object],
    failure_case: dict[str, object],
    assumption_test: str,
) -> AssumptionResultPayload:
    return {
        "theorem_id": theorem_id,
        "assumption": assumption,
        "example_satisfies_assumption": satisfying_example[assumption_test] is True,
        "failure_case_detected": failure_case[assumption_test] is False,
        "satisfying_example": satisfying_example,
        "failure_case": failure_case,
    }


def evaluate_all() -> list[AssumptionResultPayload]:
    """Evaluate one satisfying example and one failure case per assumption."""

    outputs = [0, 1, 2]
    satisfying_actions = {
        "e": lambda value: value,
        "g": lambda value: {0: 1, 1: 0, 2: 2}[value],
    }
    violating_actions = {
        "e": lambda value: value,
        "g": lambda value: (value + 1) % 3,
    }
    return [
        _assumption_case(
            "M201_BLOCK_DISJOINTNESS",
            "deployment blocks are pairwise disjoint",
            block_disjointness({"a": {"a1", "a2"}, "b": {"b1"}}),
            block_disjointness({"a": {"a1", "a2"}, "b": {"a2", "b1"}}),
            "bridge_identity_holds",
        ),
        _assumption_case(
            "M201_EQUAL_MASS",
            "all transformation blocks have equal concern mass",
            equal_mass_selector({"a": 2.0, "b": 2.0}, {"h1": {"a"}, "h2": {"b"}}),
            equal_mass_selector({"a": 3.0, "b": 1.0}, {"h1": {"a"}, "h2": {"b"}}),
            "argmax_agrees",
        ),
        _assumption_case(
            "M201_COMPLETE_BLOCK_COVERAGE",
            "a compatible block is covered in full",
            complete_block_coverage({"a": {"a1", "a2"}}, {"a": {"a1", "a2"}}, {"a"}),
            complete_block_coverage({"a": {"a1", "a2"}}, {"a": {"a1"}}, {"a"}),
            "bridge_identity_holds",
        ),
        _assumption_case(
            "M201_COHERENT_OUTPUT_ACTION",
            "the output action respects the C2 identity and composition law",
            coherent_c2_action(satisfying_actions, outputs),
            coherent_c2_action(violating_actions, outputs),
            "coherent",
        ),
        _assumption_case(
            "M201_BOUNDED_TRANSPORT_LOSS",
            "each transport loss is nonnegative and bounded by its declared delta",
            bounded_transport_loss([10.0, 8.0, 7.0], [2.0, 1.0]),
            bounded_transport_loss([10.0, 8.0, 4.0], [2.0, 1.0]),
            "bounded",
        ),
        _assumption_case(
            "M201_GAUGE_SEPARATION",
            "an intervention separates gauge-equivalent latent descriptions by eta",
            gauge_separation(["l0", "l1"], {"probe": {"l0": "A", "l1": "B"}}, 1.0),
            gauge_separation(["l0", "l1"], {"null": {"l0": "A", "l1": "A"}}, 1.0),
            "gauge_fixed",
        ),
        _assumption_case(
            "M201_NONZERO_COMMITMENT_EFFECT",
            "the matched commitment intervention has effect at least epsilon",
            commitment_effect(1.0, 0.0, 0.5),
            commitment_effect(1.0, 1.0, 0.5),
            "nonzero_effect",
        ),
    ]
