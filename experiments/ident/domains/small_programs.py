"""Small numeric programs that agree on supplied tests but differ on one probe."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from experiments.ident.actions import make_intervention, make_prior_observation
from experiments.ident.schemas import IdentItem, ObservationValue
from experiments.ident.separators import weakest_identifying_separators

ProgramFn = Callable[[int], int]


@dataclass(frozen=True)
class TinyProgram:
    name: str
    description: str
    fn: ProgramFn


PROGRAM_LIBRARY: tuple[TinyProgram, ...] = (
    TinyProgram("double", "f(x) = 2x", lambda x: 2 * x),
    TinyProgram("square", "f(x) = x^2", lambda x: x * x),
    TinyProgram("cube", "f(x) = x^3", lambda x: x * x * x),
    TinyProgram("abs", "f(x) = |x|", lambda x: abs(x)),
    TinyProgram("id", "f(x) = x", lambda x: x),
    TinyProgram("neg", "f(x) = -x", lambda x: -x),
    TinyProgram("plus_one", "f(x) = x + 1", lambda x: x + 1),
    TinyProgram("times_zero", "f(x) = 0", lambda x: 0),
    TinyProgram("mod2", "f(x) = x mod 2", lambda x: x % 2),
    TinyProgram("clamp_nonneg", "f(x) = max(x, 0)", lambda x: max(x, 0)),
)

INPUT_POOL = (-3, -2, -1, 0, 1, 2, 3, 4)


def generate_small_program_item(
    *,
    item_id: str,
    rng: random.Random,
    k: int = 2,
) -> IdentItem:
    if k < 2 or k > 4:
        raise ValueError("k must be in [2, 4]")

    programs = list(PROGRAM_LIBRARY)
    for _ in range(8000):
        chosen = rng.sample(programs, k=k)
        obs_size = rng.choice([2, 3, 4])
        observed = rng.sample(INPUT_POOL, k=obs_size)
        if any(len({p.fn(x) for p in chosen}) != 1 for x in observed):
            continue
        separators = [x for x in INPUT_POOL if len({p.fn(x) for p in chosen}) > 1]
        unobserved = [x for x in separators if x not in observed]
        if not unobserved:
            continue

        labels = [f"h_{i}" for i in range(k)]
        rng.shuffle(labels)
        label_to_prog = dict(zip(labels, chosen, strict=True))
        true_label = rng.choice(labels)
        true_prog = label_to_prog[true_label]

        prior = []
        response_table: dict[str, dict[str, ObservationValue]] = {
            label: {} for label in labels
        }
        for idx, x in enumerate(observed):
            eid = f"o{idx}"
            outcome = true_prog.fn(x)
            prior.append(
                make_prior_observation(
                    experiment_id=eid,
                    description=f"Evaluate f({x})",
                    outcome=outcome,
                    payload={"x": x, "kind": "eval"},
                )
            )
            for label, prog in label_to_prog.items():
                response_table[label][eid] = prog.fn(x)

        candidates = []
        probe_pool = [x for x in INPUT_POOL if x not in observed]
        rng.shuffle(probe_pool)
        probes = probe_pool[:4]
        if unobserved[0] not in probes:
            probes[0] = unobserved[0]

        for idx, x in enumerate(probes):
            gid = f"g_eval_{idx}"
            cost = 1.0 if abs(x) <= 2 else 2.0
            candidates.append(
                make_intervention(
                    intervention_id=gid,
                    description=f"Evaluate f at x={x}",
                    cost=cost,
                    payload={"x": x, "kind": "eval"},
                )
            )
            for label, prog in label_to_prog.items():
                response_table[label][gid] = prog.fn(x)

        waste_id = "g_resample_train"
        candidates.append(
            make_intervention(
                intervention_id=waste_id,
                description="Resample 20 more points from the already-tested inputs",
                cost=5.0,
                payload={"kind": "more_same", "xs": observed},
            )
        )
        for label, prog in label_to_prog.items():
            response_table[label][waste_id] = prog.fn(observed[0])

        rng.shuffle(candidates)
        live = labels[:]
        mins = weakest_identifying_separators(
            live, candidates, response_table, true_label
        )
        if not mins:
            continue

        presented = labels[:]
        rng.shuffle(presented)
        hyp_desc = {label: label_to_prog[label].description for label in labels}

        return IdentItem(
            item_id=item_id,
            domain="small_programs",
            hypotheses=presented,
            hypothesis_descriptions=hyp_desc,
            prior_observations=prior,
            equivalence_class_before=sorted(live),
            candidate_interventions=candidates,
            response_table=response_table,
            minimum_separators=[g.id for g in mins],
            true_hypothesis=true_label,
            final_query="Which program generated the observed input-output pairs?",
            answer=true_label,
            passive_chance_bound=1.0 / float(len(live)),
            distractors=[waste_id],
            metadata={
                "program_names": {label: label_to_prog[label].name for label in labels},
                "observed_inputs": observed,
                "family": "small_programs_v1",
            },
        )

    raise RuntimeError("failed to sample a valid small_programs item")
