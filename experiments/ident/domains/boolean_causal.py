"""Boolean causal mechanisms with observational masking."""

from __future__ import annotations

import itertools
import random
from typing import Callable

from experiments.ident.actions import make_intervention, make_prior_observation
from experiments.ident.schemas import IdentItem, ObservationValue
from experiments.ident.separators import weakest_identifying_separators

BinaryFn = Callable[[int, int], int]

# Canonical two-input Boolean mechanisms used as the latent hypothesis pool.
MECHANISM_LIBRARY: dict[str, tuple[str, BinaryFn]] = {
    "and": ("y = x1 AND x2", lambda x1, x2: x1 & x2),
    "x1": ("y = x1", lambda x1, x2: x1),
    "x2": ("y = x2", lambda x1, x2: x2),
    "or": ("y = x1 OR x2", lambda x1, x2: x1 | x2),
    "xor": ("y = x1 XOR x2", lambda x1, x2: x1 ^ x2),
    "nand": ("y = NOT (x1 AND x2)", lambda x1, x2: 1 - (x1 & x2)),
    "x1_gt_x2": ("y = 1[x1 > x2]", lambda x1, x2: int(x1 > x2)),
    "x1_implies_x2": ("y = (NOT x1) OR x2", lambda x1, x2: (1 - x1) | x2),
}

INPUT_SPACE = ((0, 0), (0, 1), (1, 0), (1, 1))


def _eval(name: str, x1: int, x2: int) -> int:
    return MECHANISM_LIBRARY[name][1](x1, x2)


def _agree_on(names: list[str], inputs: list[tuple[int, int]]) -> bool:
    for x1, x2 in inputs:
        vals = {_eval(n, x1, x2) for n in names}
        if len(vals) != 1:
            return False
    return True


def _disagree_somewhere(names: list[str]) -> list[tuple[int, int]]:
    return [
        (x1, x2)
        for x1, x2 in INPUT_SPACE
        if len({_eval(n, x1, x2) for n in names}) > 1
    ]


def _neutral_labels(k: int, rng: random.Random) -> list[str]:
    labels = [f"h_{i}" for i in range(k)]
    rng.shuffle(labels)
    return labels


def generate_boolean_causal_item(
    *,
    item_id: str,
    rng: random.Random,
    k: int = 2,
) -> IdentItem:
    """Generate one Boolean IDENT item with exact separator annotations."""
    if k < 2 or k > 4:
        raise ValueError("k must be in [2, 4]")

    names = list(MECHANISM_LIBRARY)
    for _ in range(5000):
        chosen = rng.sample(names, k=k)
        # Choose a nonempty proper subset of inputs as the passive observation support.
        obs_size = rng.choice([1, 2, 3])
        observed_inputs = rng.sample(list(INPUT_SPACE), k=obs_size)
        if not _agree_on(chosen, observed_inputs):
            continue
        separators = _disagree_somewhere(chosen)
        if not separators:
            continue
        # Require that at least one unobserved input separates.
        unobserved_separators = [p for p in separators if p not in observed_inputs]
        if not unobserved_separators:
            continue

        labels = _neutral_labels(k, rng)
        name_to_label = dict(zip(chosen, labels, strict=True))
        label_to_name = {v: k_ for k_, v in name_to_label.items()}

        true_name = rng.choice(chosen)
        true_label = name_to_label[true_name]

        prior = []
        response_table: dict[str, dict[str, ObservationValue]] = {
            label: {} for label in labels
        }
        for idx, (x1, x2) in enumerate(observed_inputs):
            eid = f"o{idx}"
            outcome = _eval(true_name, x1, x2)
            prior.append(
                make_prior_observation(
                    experiment_id=eid,
                    description=f"Passive observation with x1={x1}, x2={x2}",
                    outcome=outcome,
                    payload={"x1": x1, "x2": x2, "kind": "passive"},
                )
            )
            for label, mech_name in label_to_name.items():
                response_table[label][eid] = _eval(mech_name, x1, x2)

        candidates = []
        for x1, x2 in INPUT_SPACE:
            if (x1, x2) in observed_inputs:
                continue
            gid = f"g_set_{x1}{x2}"
            candidates.append(
                make_intervention(
                    intervention_id=gid,
                    description=f"Set x1={x1}, x2={x2} and observe y",
                    cost=1.0,
                    payload={"x1": x1, "x2": x2, "kind": "do"},
                )
            )
            for label, mech_name in label_to_name.items():
                response_table[label][gid] = _eval(mech_name, x1, x2)

        waste_id = "g_more_same"
        candidates.append(
            make_intervention(
                intervention_id=waste_id,
                description=(
                    "Collect 20 additional passive samples restricted to the same "
                    "observed support (still support-limited)"
                ),
                cost=5.0,
                payload={"kind": "more_same", "support": observed_inputs},
            )
        )
        for label, mech_name in label_to_name.items():
            vals = [_eval(mech_name, x1, x2) for x1, x2 in observed_inputs]
            response_table[label][waste_id] = vals[0]

        rng.shuffle(candidates)
        live = labels[:]
        mins = weakest_identifying_separators(
            live, candidates, response_table, true_label
        )
        if not mins:
            continue

        hyp_desc = {
            label: MECHANISM_LIBRARY[label_to_name[label]][0] for label in labels
        }
        presented = labels[:]
        rng.shuffle(presented)

        return IdentItem(
            item_id=item_id,
            domain="boolean_causal",
            hypotheses=presented,
            hypothesis_descriptions=hyp_desc,
            prior_observations=prior,
            equivalence_class_before=sorted(live),
            candidate_interventions=candidates,
            response_table=response_table,
            minimum_separators=[g.id for g in mins],
            true_hypothesis=true_label,
            final_query="Which mechanism generated the system?",
            answer=true_label,
            passive_chance_bound=1.0 / float(len(live)),
            distractors=[waste_id],
            metadata={
                "mechanism_names": {label: label_to_name[label] for label in labels},
                "observed_inputs": observed_inputs,
                "family": "boolean_causal_v1",
            },
        )

    raise RuntimeError("failed to sample a valid boolean_causal item")


def enumerate_hard_pairs(limit: int = 50) -> list[tuple[str, str, list[tuple[int, int]]]]:
    """Utility: list mechanism pairs with nontrivial observational masking."""
    out: list[tuple[str, str, list[tuple[int, int]]]] = []
    for a, b in itertools.combinations(MECHANISM_LIBRARY, 2):
        for r in range(1, 4):
            for support in itertools.combinations(INPUT_SPACE, r):
                support_list = list(support)
                if _agree_on([a, b], support_list) and _disagree_somewhere([a, b]):
                    unobs = [p for p in _disagree_somewhere([a, b]) if p not in support_list]
                    if unobs:
                        out.append((a, b, support_list))
                        if len(out) >= limit:
                            return out
    return out
