"""Finite-state machines with identical traces on observed strings."""

from __future__ import annotations

import random
from dataclasses import dataclass

from experiments.ident.actions import make_intervention, make_prior_observation
from experiments.ident.schemas import IdentItem, ObservationValue
from experiments.ident.separators import weakest_identifying_separators

ALPHABET = ("0", "1")


@dataclass(frozen=True)
class TinyDFA:
    name: str
    description: str
    kind: str

    def accept(self, string: str) -> int:
        if self.kind == "ends_with_1":
            return int(string.endswith("1")) if string else 0
        if self.kind == "ends_with_0":
            return int(string.endswith("0")) if string else 0
        if self.kind == "has_two_1s":
            return int(string.count("1") >= 2)
        if self.kind == "even_ones":
            return int(string.count("1") % 2 == 0)
        if self.kind == "odd_ones":
            return int(string.count("1") % 2 == 1)
        if self.kind == "starts_with_1":
            return int(string.startswith("1")) if string else 0
        if self.kind == "length_even":
            return int(len(string) % 2 == 0)
        if self.kind == "contains_01":
            return int("01" in string)
        raise KeyError(self.kind)


DFA_LIBRARY: tuple[TinyDFA, ...] = (
    TinyDFA("ends_with_1", "accept iff string ends with 1", "ends_with_1"),
    TinyDFA("ends_with_0", "accept iff string ends with 0", "ends_with_0"),
    TinyDFA("has_two_1s", "accept iff string has at least two 1s", "has_two_1s"),
    TinyDFA("even_ones", "accept iff number of 1s is even", "even_ones"),
    TinyDFA("odd_ones", "accept iff number of 1s is odd", "odd_ones"),
    TinyDFA("starts_with_1", "accept iff string starts with 1", "starts_with_1"),
    TinyDFA("length_even", "accept iff length is even", "length_even"),
    TinyDFA("contains_01", "accept iff string contains substring 01", "contains_01"),
)


def _all_strings(max_len: int) -> list[str]:
    out = [""]
    frontier = [""]
    for _ in range(max_len):
        nxt = []
        for s in frontier:
            for a in ALPHABET:
                t = s + a
                nxt.append(t)
                out.append(t)
        frontier = nxt
    return out


STRINGS = _all_strings(3)


def generate_finite_state_item(
    *,
    item_id: str,
    rng: random.Random,
    k: int = 2,
) -> IdentItem:
    if k < 2 or k > 4:
        raise ValueError("k must be in [2, 4]")

    for _ in range(5000):
        machines = rng.sample(list(DFA_LIBRARY), k=k)
        obs_size = rng.choice([2, 3, 4])
        observed = rng.sample(STRINGS, k=obs_size)
        agree = all(len({m.accept(s) for m in machines}) == 1 for s in observed)
        if not agree:
            continue
        separators = [s for s in STRINGS if len({m.accept(s) for m in machines}) > 1]
        unobserved = [s for s in separators if s not in observed]
        if not unobserved:
            continue

        labels = [f"h_{i}" for i in range(k)]
        rng.shuffle(labels)
        label_to_machine = dict(zip(labels, machines, strict=True))
        true_label = rng.choice(labels)
        true_machine = label_to_machine[true_label]

        prior = []
        response_table: dict[str, dict[str, ObservationValue]] = {
            label: {} for label in labels
        }
        for idx, s in enumerate(observed):
            eid = f"o{idx}"
            outcome = true_machine.accept(s)
            shown = s if s != "" else "ε"
            prior.append(
                make_prior_observation(
                    experiment_id=eid,
                    description=f"Trace on string '{shown}' (accept=1 / reject=0)",
                    outcome=outcome,
                    payload={"string": s, "kind": "trace"},
                )
            )
            for label, machine in label_to_machine.items():
                response_table[label][eid] = machine.accept(s)

        candidates = []
        probe_pool = [s for s in STRINGS if s not in observed]
        rng.shuffle(probe_pool)
        probes = probe_pool[: max(3, min(5, len(probe_pool)))]
        for s in unobserved:
            if s not in probes:
                probes[0] = s
                break

        for idx, s in enumerate(probes):
            gid = f"g_query_{idx}"
            shown = s if s != "" else "ε"
            cost = 1.0 + 0.25 * len(s)
            candidates.append(
                make_intervention(
                    intervention_id=gid,
                    description=f"Query acceptance of string '{shown}'",
                    cost=float(cost),
                    payload={"string": s, "kind": "query"},
                )
            )
            for label, machine in label_to_machine.items():
                response_table[label][gid] = machine.accept(s)

        waste_id = "g_replay_observed"
        candidates.append(
            make_intervention(
                intervention_id=waste_id,
                description="Replay 20 additional traces on the already-observed strings",
                cost=6.0,
                payload={"kind": "more_same", "strings": observed},
            )
        )
        for label, machine in label_to_machine.items():
            response_table[label][waste_id] = machine.accept(observed[0])

        rng.shuffle(candidates)
        live = labels[:]
        mins = weakest_identifying_separators(
            live, candidates, response_table, true_label
        )
        if not mins:
            continue

        presented = labels[:]
        rng.shuffle(presented)
        hyp_desc = {label: label_to_machine[label].description for label in labels}

        return IdentItem(
            item_id=item_id,
            domain="finite_state",
            hypotheses=presented,
            hypothesis_descriptions=hyp_desc,
            prior_observations=prior,
            equivalence_class_before=sorted(live),
            candidate_interventions=candidates,
            response_table=response_table,
            minimum_separators=[g.id for g in mins],
            true_hypothesis=true_label,
            final_query="Which acceptor generated the observed traces?",
            answer=true_label,
            passive_chance_bound=1.0 / float(len(live)),
            distractors=[waste_id],
            metadata={
                "machine_kinds": {
                    label: label_to_machine[label].kind for label in labels
                },
                "observed_strings": observed,
                "family": "finite_state_v1",
            },
        )

    raise RuntimeError("failed to sample a valid finite_state item")
