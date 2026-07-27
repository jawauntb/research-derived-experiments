#!/usr/bin/env python3
"""Finite-agent constructions and exact future-commitment quotient checks."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Literal, TypeAlias

import numpy as np


Family: TypeAlias = Literal["parity", "modulo_three", "order"]
Condition: TypeAlias = Literal["RP_CP", "RD_CP", "RP_CA", "RD_CA"]
Word: TypeAlias = tuple[str, ...]

ALPHABET = ("zero", "one", "advance", "reset")
OUTPUTS = ("defer", "reject", "accept")
FAMILIES: tuple[Family, ...] = ("parity", "modulo_three", "order")
CONDITIONS: tuple[Condition, ...] = ("RP_CP", "RD_CP", "RP_CA", "RD_CA")
COORDINATE_DIMENSION = 8


@dataclass(frozen=True)
class ConditionSpec:
    representation_preserved: bool
    constraint_preserved: bool


CONDITION_SPECS: dict[Condition, ConditionSpec] = {
    "RP_CP": ConditionSpec(
        representation_preserved=True,
        constraint_preserved=True,
    ),
    "RD_CP": ConditionSpec(
        representation_preserved=False,
        constraint_preserved=True,
    ),
    "RP_CA": ConditionSpec(
        representation_preserved=True,
        constraint_preserved=False,
    ),
    "RD_CA": ConditionSpec(
        representation_preserved=False,
        constraint_preserved=False,
    ),
}


@dataclass(frozen=True)
class FiniteAgent:
    """A deterministic Moore agent with an injective coordinate realization."""

    name: str
    states: tuple[str, ...]
    alphabet: tuple[str, ...]
    transitions: np.ndarray
    outputs: tuple[str, ...]
    coordinates: np.ndarray


@dataclass(frozen=True)
class RegisteredFamily:
    family: Family
    base: FiniteAgent
    mutant: FiniteAgent


@dataclass(frozen=True)
class ConditionPair:
    """One registered factorial comparison against a canonical left agent."""

    family: Family
    seed: int
    condition: Condition
    left: FiniteAgent
    right: FiniteAgent
    alignment: np.ndarray
    relation: np.ndarray
    metrics: dict[str, float | int | None]
    scramble_integrity: dict[str, bool]
    formal_checks: dict[str, bool]

    def to_row(self) -> dict[str, Any]:
        spec = CONDITION_SPECS[self.condition]
        return {
            "family": self.family,
            "seed": self.seed,
            "condition": self.condition,
            "representation_preserved": spec.representation_preserved,
            "constraint_preserved": spec.constraint_preserved,
            **self.metrics,
            "scramble_integrity": self.scramble_integrity,
            "formal_checks": self.formal_checks,
        }


def _memory_size(family: Family) -> int:
    return 2 if family == "parity" else 3


def _state_index(phase: int, memory: int, memory_size: int) -> int:
    return phase * memory_size + memory


def _structural_coordinates(memory_size: int) -> np.ndarray:
    rows: list[list[float]] = []
    for phase in range(3):
        for memory in range(memory_size):
            phase_scaled = phase / 2.0
            memory_scaled = memory / max(memory_size - 1, 1)
            rows.append(
                [
                    phase_scaled,
                    memory_scaled,
                    phase_scaled * memory_scaled,
                    phase_scaled**2,
                    memory_scaled**2,
                    float(phase == 2),
                    float(memory == 0),
                    1.0,
                ]
            )
    return np.asarray(rows, dtype=np.float64)


def _memory_update(family: Family, memory: int, action: str) -> int:
    if family == "parity":
        return memory if action == "zero" else memory ^ 1
    if family == "modulo_three":
        increment = 1 if action == "zero" else 2
        return (memory + increment) % 3
    if family == "order":
        return 1 if action == "zero" else 2
    raise ValueError(f"Unknown family: {family}")


def _terminal_output(family: Family, memory: int) -> str:
    if family in {"parity", "modulo_three"}:
        return "accept" if memory == 0 else "reject"
    if family == "order":
        return "accept" if memory == 1 else "reject"
    raise ValueError(f"Unknown family: {family}")


def build_family(family: Family) -> FiniteAgent:
    """Build one registered delayed-commitment machine family."""

    if family not in FAMILIES:
        raise ValueError(f"Unknown family: {family}")
    memory_size = _memory_size(family)
    states = tuple(
        f"phase_{phase}_memory_{memory}"
        for phase in range(3)
        for memory in range(memory_size)
    )
    transitions = np.zeros((len(states), len(ALPHABET)), dtype=np.int64)
    outputs: list[str] = []
    for phase in range(3):
        for memory in range(memory_size):
            source = _state_index(phase, memory, memory_size)
            for action_index, action in enumerate(ALPHABET):
                if action in {"zero", "one"}:
                    next_phase = phase
                    next_memory = _memory_update(family, memory, action)
                elif action == "advance":
                    next_phase = min(phase + 1, 2)
                    next_memory = memory
                else:
                    next_phase = 0
                    next_memory = 0
                transitions[source, action_index] = _state_index(
                    next_phase,
                    next_memory,
                    memory_size,
                )
            outputs.append("defer" if phase < 2 else _terminal_output(family, memory))
    agent = FiniteAgent(
        name=family,
        states=states,
        alphabet=ALPHABET,
        transitions=transitions,
        outputs=tuple(outputs),
        coordinates=_structural_coordinates(memory_size),
    )
    verify_agent(agent)
    return agent


def build_mutant(agent: FiniteAgent, family: Family) -> FiniteAgent:
    """Alter one delayed, load-bearing transition without changing coordinates."""

    verify_agent(agent)
    memory_size = _memory_size(family)
    transitions = agent.transitions.copy()
    source = _state_index(0, 0, memory_size)
    action_index = agent.alphabet.index("zero" if family == "order" else "one")
    transitions[source, action_index] = source
    mutant = FiniteAgent(
        name=f"{family}_delayed_mutant",
        states=agent.states,
        alphabet=agent.alphabet,
        transitions=transitions,
        outputs=agent.outputs,
        coordinates=agent.coordinates.copy(),
    )
    verify_agent(mutant)
    witness = shortest_distinguishing_word(agent, source, mutant, source)
    if witness is None or len(witness) < 2:
        raise ValueError("Registered mutant is not delayed and load-bearing")
    return mutant


def build_registered_family(family: Family) -> RegisteredFamily:
    base = build_family(family)
    return RegisteredFamily(
        family=family,
        base=base,
        mutant=build_mutant(base, family),
    )


def verify_agent(agent: FiniteAgent) -> dict[str, int | bool]:
    """Fail closed on typing, totality, output, and coordinate integrity."""

    n_states = len(agent.states)
    if n_states < 1 or len(set(agent.states)) != n_states:
        raise ValueError("states must be nonempty and unique")
    if not agent.alphabet or len(set(agent.alphabet)) != len(agent.alphabet):
        raise ValueError("alphabet must be nonempty and unique")
    if agent.transitions.shape != (n_states, len(agent.alphabet)):
        raise ValueError("transition table has the wrong shape")
    if not np.issubdtype(agent.transitions.dtype, np.integer):
        raise ValueError("transition targets must be integers")
    if np.any(agent.transitions < 0) or np.any(agent.transitions >= n_states):
        raise ValueError("transition target lies outside the state set")
    if len(agent.outputs) != n_states or not set(agent.outputs).issubset(OUTPUTS):
        raise ValueError("outputs must be typed and defined for every state")
    if agent.coordinates.shape != (n_states, COORDINATE_DIMENSION):
        raise ValueError("coordinates have the wrong shape")
    if not np.all(np.isfinite(agent.coordinates)):
        raise ValueError("coordinates must be finite")
    unique_coordinates = np.unique(agent.coordinates, axis=0)
    if len(unique_coordinates) != n_states:
        raise ValueError("coordinates must be injective")
    return {
        "n_states": n_states,
        "transition_total": True,
        "coordinate_injective": True,
    }


def run_word(agent: FiniteAgent, state: int, word: Word) -> int:
    """Return the state reached after one finite intervention word."""

    if state < 0 or state >= len(agent.states):
        raise ValueError("state lies outside the agent")
    action_to_index = {action: index for index, action in enumerate(agent.alphabet)}
    current = state
    for action in word:
        if action not in action_to_index:
            raise ValueError(f"Unknown action: {action}")
        current = int(agent.transitions[current, action_to_index[action]])
    return current


def commitment_after(agent: FiniteAgent, state: int, word: Word) -> str:
    return agent.outputs[run_word(agent, state, word)]


def cross_bisimulation(left: FiniteAgent, right: FiniteAgent) -> np.ndarray:
    """Compute the greatest cross-agent commitment bisimulation."""

    _verify_shared_interface(left, right)
    relation = np.asarray(
        [
            [left_output == right_output for right_output in right.outputs]
            for left_output in left.outputs
        ],
        dtype=bool,
    )
    while True:
        refined = relation.copy()
        for left_state in range(len(left.states)):
            for right_state in range(len(right.states)):
                if not relation[left_state, right_state]:
                    continue
                for action_index in range(len(left.alphabet)):
                    left_next = int(left.transitions[left_state, action_index])
                    right_next = int(right.transitions[right_state, action_index])
                    if not relation[left_next, right_next]:
                        refined[left_state, right_state] = False
                        break
        if np.array_equal(refined, relation):
            return relation
        relation = refined


def quotient_partition(agent: FiniteAgent) -> tuple[tuple[int, ...], ...]:
    """Return the stable Moore-machine partition in deterministic block order."""

    verify_agent(agent)
    blocks = _group_by_signature(
        range(len(agent.states)),
        lambda state: (agent.outputs[state],),
    )
    while True:
        block_of = {
            state: block_index
            for block_index, block in enumerate(blocks)
            for state in block
        }
        refined = _group_by_signature(
            range(len(agent.states)),
            lambda state: (
                agent.outputs[state],
                tuple(
                    block_of[int(agent.transitions[state, action_index])]
                    for action_index in range(len(agent.alphabet))
                ),
            ),
        )
        if refined == blocks:
            return blocks
        blocks = refined


def _group_by_signature(
    states: Any,
    signature: Any,
) -> tuple[tuple[int, ...], ...]:
    groups: dict[Any, list[int]] = {}
    for state in states:
        groups.setdefault(signature(state), []).append(int(state))
    blocks = [tuple(sorted(group)) for group in groups.values()]
    return tuple(sorted(blocks, key=lambda block: block[0]))


def shortest_distinguishing_word(
    left: FiniteAgent,
    left_state: int,
    right: FiniteAgent,
    right_state: int,
) -> Word | None:
    """Find the shortest future word with different commitments, if one exists."""

    _verify_shared_interface(left, right)
    if left.outputs[left_state] != right.outputs[right_state]:
        return ()
    queue: deque[tuple[int, int, Word]] = deque([(left_state, right_state, ())])
    visited = {(left_state, right_state)}
    while queue:
        current_left, current_right, prefix = queue.popleft()
        for action_index, action in enumerate(left.alphabet):
            next_left = int(left.transitions[current_left, action_index])
            next_right = int(right.transitions[current_right, action_index])
            word = prefix + (action,)
            if left.outputs[next_left] != right.outputs[next_right]:
                return word
            pair = (next_left, next_right)
            if pair not in visited:
                visited.add(pair)
                queue.append((next_left, next_right, word))
    return None


def distinguishing_word_lengths(
    left: FiniteAgent,
    right: FiniteAgent,
) -> np.ndarray:
    """Return all shortest product-state witness lengths, or -1 if equivalent."""

    _verify_shared_interface(left, right)
    n_left = len(left.states)
    n_right = len(right.states)
    distances = np.full((n_left, n_right), -1, dtype=np.int64)
    queue: deque[tuple[int, int]] = deque()
    for left_state in range(n_left):
        for right_state in range(n_right):
            if left.outputs[left_state] != right.outputs[right_state]:
                distances[left_state, right_state] = 0
                queue.append((left_state, right_state))

    left_predecessors = _transition_predecessors(left)
    right_predecessors = _transition_predecessors(right)
    while queue:
        left_state, right_state = queue.popleft()
        next_distance = int(distances[left_state, right_state]) + 1
        for action_index in range(len(left.alphabet)):
            for left_previous in left_predecessors[action_index][left_state]:
                for right_previous in right_predecessors[action_index][right_state]:
                    if distances[left_previous, right_previous] >= 0:
                        continue
                    distances[left_previous, right_previous] = next_distance
                    queue.append((left_previous, right_previous))
    return distances


def _transition_predecessors(
    agent: FiniteAgent,
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    per_action: list[tuple[tuple[int, ...], ...]] = []
    for action_index in range(len(agent.alphabet)):
        targets: list[list[int]] = [[] for _ in agent.states]
        for source in range(len(agent.states)):
            target = int(agent.transitions[source, action_index])
            targets[target].append(source)
        per_action.append(tuple(tuple(sources) for sources in targets))
    return tuple(per_action)


def conjugate(
    agent: FiniteAgent,
    permutation: np.ndarray,
    aligned_coordinates: np.ndarray,
    *,
    name: str,
) -> FiniteAgent:
    """Relabel an agent while assigning a new coordinate realization."""

    verify_agent(agent)
    n_states = len(agent.states)
    if sorted(int(value) for value in permutation) != list(range(n_states)):
        raise ValueError("permutation must be a bijection")
    if aligned_coordinates.shape != agent.coordinates.shape:
        raise ValueError("aligned coordinates have the wrong shape")
    transitions = np.zeros_like(agent.transitions)
    outputs = [""] * n_states
    coordinates = np.zeros_like(agent.coordinates)
    states = [""] * n_states
    for old_state in range(n_states):
        new_state = int(permutation[old_state])
        states[new_state] = f"scrambled_{new_state}"
        outputs[new_state] = agent.outputs[old_state]
        coordinates[new_state] = aligned_coordinates[old_state]
        for action_index in range(len(agent.alphabet)):
            old_target = int(agent.transitions[old_state, action_index])
            transitions[new_state, action_index] = int(permutation[old_target])
    result = FiniteAgent(
        name=name,
        states=tuple(states),
        alphabet=agent.alphabet,
        transitions=transitions,
        outputs=tuple(outputs),
        coordinates=coordinates,
    )
    verify_agent(result)
    return result


def verify_conjugacy(
    left: FiniteAgent,
    right: FiniteAgent,
    alignment: np.ndarray,
) -> bool:
    """Check output and transition conjugacy for one registered alignment."""

    _verify_shared_interface(left, right)
    if sorted(int(value) for value in alignment) != list(range(len(right.states))):
        return False
    if len(left.states) != len(right.states):
        return False
    for left_state in range(len(left.states)):
        right_state = int(alignment[left_state])
        if left.outputs[left_state] != right.outputs[right_state]:
            return False
        for action_index in range(len(left.alphabet)):
            left_target = int(left.transitions[left_state, action_index])
            right_target = int(right.transitions[right_state, action_index])
            if int(alignment[left_target]) != right_target:
                return False
    return True


def _scramble(
    agent: FiniteAgent,
    *,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, dict[str, bool]]:
    rng = np.random.default_rng(seed)
    n_states = len(agent.states)
    permutation = rng.permutation(n_states)
    if np.array_equal(permutation, np.arange(n_states)):
        permutation = np.roll(permutation, 1)
    aligned_coordinates = rng.normal(size=(n_states, COORDINATE_DIMENSION)).astype(
        np.float64
    )
    while len(np.unique(aligned_coordinates, axis=0)) != n_states:
        aligned_coordinates = rng.normal(size=(n_states, COORDINATE_DIMENSION)).astype(
            np.float64
        )
    base_rdm = _euclidean_rdm(agent.coordinates)
    scrambled_rdm = _euclidean_rdm(aligned_coordinates)
    row_preserved = np.all(
        agent.coordinates == aligned_coordinates,
        axis=1,
    )
    integrity = {
        "coordinate_injective": True,
        "no_aligned_row_preserved": bool(not np.any(row_preserved)),
        "geometry_changed": bool(not np.array_equal(base_rdm, scrambled_rdm)),
        "nonidentity_permutation": bool(
            not np.array_equal(permutation, np.arange(n_states))
        ),
    }
    if not all(integrity.values()):
        raise ValueError("Registered coordinate scramble failed integrity")
    return permutation, aligned_coordinates, integrity


def _euclidean_rdm(coordinates: np.ndarray) -> np.ndarray:
    differences = coordinates[:, None, :] - coordinates[None, :, :]
    return np.sqrt(np.sum(differences * differences, axis=-1))


def _rdm_correlation(left: np.ndarray, right: np.ndarray) -> float:
    triangle = np.triu_indices(left.shape[0], k=1)
    left_vector = left[triangle]
    right_vector = right[triangle]
    if float(np.std(left_vector)) < 1e-12 or float(np.std(right_vector)) < 1e-12:
        return 0.0
    return float(np.corrcoef(left_vector, right_vector)[0, 1])


def _verify_shared_interface(left: FiniteAgent, right: FiniteAgent) -> None:
    verify_agent(left)
    verify_agent(right)
    if left.alphabet != right.alphabet:
        raise ValueError("agents must share the same intervention alphabet")


def _pair_metrics(
    left: FiniteAgent,
    right: FiniteAgent,
    alignment: np.ndarray,
    relation: np.ndarray,
) -> tuple[dict[str, float | int | None], dict[str, bool]]:
    aligned_coordinates = right.coordinates[alignment]
    row_equality = np.all(left.coordinates == aligned_coordinates, axis=1)
    current_agreement = [
        left.outputs[state] == right.outputs[int(alignment[state])]
        for state in range(len(left.states))
    ]
    depth_one_agreement: list[bool] = []
    for left_state in range(len(left.states)):
        right_state = int(alignment[left_state])
        for action_index in range(len(left.alphabet)):
            left_target = int(left.transitions[left_state, action_index])
            right_target = int(right.transitions[right_state, action_index])
            depth_one_agreement.append(
                left.outputs[left_target] == right.outputs[right_target]
            )
    aligned_relation = relation[np.arange(len(left.states)), alignment]
    witness_lengths = distinguishing_word_lengths(left, right)
    aligned_witness_lengths = witness_lengths[
        np.arange(len(left.states)),
        alignment,
    ]
    differing_witness_lengths = aligned_witness_lengths[aligned_witness_lengths >= 0]
    witness_bound = len(left.states) * len(right.states)
    relation_witness_consistent = bool(np.array_equal(relation, witness_lengths < 0))
    finite_witness_lengths = witness_lengths[witness_lengths >= 0]
    all_witnesses_bounded = bool(np.all(finite_witness_lengths < witness_bound))
    left_partition = quotient_partition(left)
    right_partition = quotient_partition(right)
    metrics: dict[str, float | int | None] = {
        "coordinate_equality": float(np.mean(row_equality)),
        "coordinate_geometry_correlation": _rdm_correlation(
            _euclidean_rdm(left.coordinates),
            _euclidean_rdm(aligned_coordinates),
        ),
        "current_output_agreement": float(np.mean(current_agreement)),
        "depth_one_agreement": float(np.mean(depth_one_agreement)),
        "quotient_agreement": float(np.mean(aligned_relation)),
        "behavioral_disagreement": float(
            len(differing_witness_lengths) / len(left.states)
        ),
        "shortest_witness_length": (
            int(np.min(differing_witness_lengths))
            if len(differing_witness_lengths)
            else None
        ),
        "left_quotient_blocks": len(left_partition),
        "right_quotient_blocks": len(right_partition),
    }
    formal_checks = {
        "relation_witness_consistent": relation_witness_consistent,
        "all_witnesses_bounded": all_witnesses_bounded,
        "left_partition_fixed_point": _partition_is_congruence(
            left,
            left_partition,
        ),
        "right_partition_fixed_point": _partition_is_congruence(
            right,
            right_partition,
        ),
    }
    return metrics, formal_checks


def _partition_is_congruence(
    agent: FiniteAgent,
    partition: tuple[tuple[int, ...], ...],
) -> bool:
    block_of = {
        state: block_index
        for block_index, block in enumerate(partition)
        for state in block
    }
    for block in partition:
        outputs = {agent.outputs[state] for state in block}
        if len(outputs) != 1:
            return False
        for action_index in range(len(agent.alphabet)):
            targets = {
                block_of[int(agent.transitions[state, action_index])] for state in block
            }
            if len(targets) != 1:
                return False
    return True


def build_condition_pair(
    family: Family,
    *,
    seed: int,
    condition: Condition,
    registered_family: RegisteredFamily | None = None,
) -> ConditionPair:
    """Build and evaluate one preregistered factorial cell."""

    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition}")
    fixture = registered_family or build_registered_family(family)
    if fixture.family != family:
        raise ValueError("registered family does not match requested family")
    base = fixture.base
    mutant = fixture.mutant
    spec = CONDITION_SPECS[condition]
    source = base if spec.constraint_preserved else mutant
    if not spec.representation_preserved:
        permutation, scrambled_coordinates, integrity = _scramble(
            base,
            seed=seed * 101 + FAMILIES.index(family) * 100_003 + 17,
        )
        right = conjugate(
            source,
            permutation,
            scrambled_coordinates,
            name=f"{family}_{condition.lower()}_{seed}",
        )
        alignment = permutation
    else:
        right = FiniteAgent(
            name=f"{family}_{condition.lower()}_{seed}",
            states=source.states,
            alphabet=source.alphabet,
            transitions=source.transitions.copy(),
            outputs=source.outputs,
            coordinates=source.coordinates.copy(),
        )
        alignment = np.arange(len(base.states), dtype=np.int64)
        integrity = {
            "coordinate_injective": True,
            "no_aligned_row_preserved": False,
            "geometry_changed": False,
            "nonidentity_permutation": False,
        }
    relation = cross_bisimulation(base, right)
    metrics, formal_checks = _pair_metrics(base, right, alignment, relation)
    formal_checks["conjugacy_when_constraint_preserved"] = (
        verify_conjugacy(base, right, alignment) if spec.constraint_preserved else True
    )
    formal_checks["nonconjugacy_when_constraint_altered"] = (
        not verify_conjugacy(base, right, alignment)
        if not spec.constraint_preserved
        else True
    )
    return ConditionPair(
        family=family,
        seed=seed,
        condition=condition,
        left=base,
        right=right,
        alignment=alignment,
        relation=relation,
        metrics=metrics,
        scramble_integrity=integrity,
        formal_checks=formal_checks,
    )
