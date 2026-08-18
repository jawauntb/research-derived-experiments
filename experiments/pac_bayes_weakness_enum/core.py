"""Exact |X|≤7 PAC-Bayes weakness tournament.

Enumerates H = Y^X for each frozen family, scores repository weakness
under aligned / incomplete / wrong / random transformation families,
and evaluates the sketch's kill criteria. Langford–Seeger–Maurer is
used only as a numerical plug-in on these finite numbers; it is not
proved here.

Python-enumerated. Not Lean. Not a neural PAC-Bayes bound.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from collections.abc import Iterator, Sequence
from fractions import Fraction
from itertools import product
from typing import Any

from .families import (
    DELTA,
    FAMILIES,
    GROUP_NAMES,
    HYPERPRIOR_WEIGHT,
    IID_MS,
    IID_SEEDS,
    PI_SCHEDULES,
    VACUOUS_BOUND,
    FamilySpec,
)

EXPERIMENT_ID = "pac_bayes_weakness_enum"
RUN_ID = "pac_bayes_weakness_enum_2026_08_18"
PRODUCING_AGENT = "Cursor Grok 4.6 (under J. Brown direction)"
SESSION_REF = "551a32dd-382d-4456-91cf-669ec091a0a1"

PROCESS_DISCLOSURE = (
    "Predeclared finite PAC-Bayes tournament from "
    "papers/weakness_invariance_neurips/pac_bayes_weakness_sketch.md. "
    "One reduced domain per family, |X|=|Y|≤7, ambient H=Y^X enumerated "
    "exactly. Groups, truths, OOD splits, π schedules, IID seeds, m, and "
    "δ were frozen before the class counts were inspected. The "
    "Langford–Seeger–Maurer kl inequality is a numerical plug-in "
    "(cited, not proved). Neural posteriors stay out."
)

Fn = tuple[int, ...]
Group = tuple[Fn, ...]


def factorial(n: int) -> int:
    out = 1
    for k in range(2, n + 1):
        out *= k
    return out


def iter_functions(n: int) -> Iterator[Fn]:
    yield from product(range(n), repeat=n)


def hamming(f: Sequence[int], g: Sequence[int]) -> int:
    return sum(int(a != b) for a, b in zip(f, g, strict=True))


def compatible(f: Sequence[int], g: Sequence[int], group: Sequence[Sequence[int]]) -> bool:
    n = len(f)
    for h in group:
        if all(f[g[x]] == h[f[x]] for x in range(n)):
            return True
    return False


def _is_cyclic_rotations(group: Sequence[Sequence[int]], n: int) -> bool:
    expected = {tuple((x + k) % n for x in range(n)) for k in range(n)}
    return len(group) == n and set(map(tuple, group)) == expected


def _is_dihedral(group: Sequence[Sequence[int]], n: int) -> bool:
    rots = {tuple((x + k) % n for x in range(n)) for k in range(n)}
    refs = {tuple((k - x) % n for x in range(n)) for k in range(n)}
    return set(map(tuple, group)) == rots | refs


def weakness_cyclic(f: Sequence[int], n: int) -> int:
    count = 0
    for k in range(n):
        shift = (f[k % n] - f[0]) % n
        if all(f[(x + k) % n] == (f[x] + shift) % n for x in range(n)):
            count += 1
    return count


def weakness_dihedral(f: Sequence[int], n: int) -> int:
    count = 0
    for k in range(n):
        rot_img = [(x + k) % n for x in range(n)]
        ref_img = [(k - x) % n for x in range(n)]
        if _dihedral_compatible(f, rot_img, n):
            count += 1
        if _dihedral_compatible(f, ref_img, n):
            count += 1
    return count


def _dihedral_compatible(f: Sequence[int], g_img: Sequence[int], n: int) -> bool:
    shift = (f[g_img[0]] - f[0]) % n
    if all(f[g_img[x]] == (f[x] + shift) % n for x in range(n)):
        return True
    pivot = (f[g_img[0]] + f[0]) % n
    return all(f[g_img[x]] == (pivot - f[x]) % n for x in range(n))


def weakness_family(f: Sequence[int], group: Sequence[Sequence[int]]) -> int:
    n = len(f)
    if _is_cyclic_rotations(group, n):
        return weakness_cyclic(f, n)
    if _is_dihedral(group, n):
        return weakness_dihedral(f, n)
    return sum(1 for g in group if compatible(f, g, group))


def weakness_symmetric(f: Sequence[int]) -> int:
    """Count g in S_n with f(x)=f(y) iff f(g(x))=f(g(y))."""

    fibers: dict[int, int] = {}
    for value in f:
        fibers[value] = fibers.get(value, 0) + 1
    size_mult = Counter(fibers.values())
    count = 1
    for size, multiplicity in size_mult.items():
        count *= factorial(multiplicity) * (factorial(size) ** multiplicity)
    return count


def weakness(f: Sequence[int], group: Sequence[Sequence[int]], *, full_sym: bool) -> int:
    if full_sym:
        return weakness_symmetric(f)
    return weakness_family(f, group)


def group_order(spec: FamilySpec, name: str) -> int:
    if name == "aligned" and spec["aligned_is_full_symmetric"]:
        return factorial(spec["n"])
    return len(spec["groups"][name])


def level_cards(weights: Sequence[int], order: int) -> list[int]:
    hist = [0] * (order + 1)
    for w in weights:
        hist[w] += 1
    cards = [0] * (order + 1)
    running = 0
    for k in range(order, 0, -1):
        running += hist[k]
        cards[k] = running
    return cards


def schedule_weights(order: int, name: str) -> list[int]:
    if name == "uniform":
        return [0] + [1] * order
    if name == "high":
        return [0] + list(range(1, order + 1))
    if name == "low":
        return [0] + list(range(order, 0, -1))
    raise ValueError(name)


def mixture_pi(cards: Sequence[int], schedule: str) -> list[Fraction]:
    order = len(cards) - 1
    raw = schedule_weights(order, schedule)
    live = [k for k in range(1, order + 1) if cards[k] > 0]
    total = sum(raw[k] for k in live)
    pi = [Fraction(0)] * (order + 1)
    if total == 0:
        return pi
    for k in live:
        pi[k] = Fraction(raw[k], total)
    return pi


def mixture_mass(weak: int, cards: Sequence[int], pi: Sequence[Fraction]) -> Fraction:
    mass = Fraction(0)
    for k in range(1, weak + 1):
        if cards[k] == 0:
            continue
        mass += pi[k] / cards[k]
    return mass


def kl_dirac(mass: Fraction) -> float:
    if mass <= 0:
        return math.inf
    return -math.log(float(mass))


def binary_kl(p: float, q: float) -> float:
    if q <= 0.0 or q >= 1.0:
        if p == q:
            return 0.0
        return math.inf
    kl = 0.0
    if p > 0.0:
        kl += p * math.log(p / q)
    if p < 1.0:
        kl += (1.0 - p) * math.log((1.0 - p) / (1.0 - q))
    return kl


def invert_kl(p: float, rhs: float) -> float:
    """Largest q in [p, 1] with kl(p||q) ≤ rhs."""

    if rhs < 0.0:
        return p
    if binary_kl(p, 1.0 - 1e-15) <= rhs:
        return 1.0
    lo, hi = p, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if binary_kl(p, mid) <= rhs:
            lo = mid
        else:
            hi = mid
    return lo


def lsm_extra(m: int, delta: float = DELTA) -> float:
    return math.log(2.0 * math.sqrt(m) / delta)


def lsm_bound(lhat: float, kl: float, m: int, delta: float = DELTA) -> float:
    rhs = (kl + lsm_extra(m, delta)) / m
    return invert_kl(lhat, rhs)


def patch_fn(truth: Fn, train: Sequence[int], fill: int | None = None) -> Fn:
    n = len(truth)
    train_set = set(train)
    out = []
    for x in range(n):
        if x in train_set:
            out.append(truth[x])
        elif fill is None:
            out.append(x)
        else:
            out.append(fill)
    return tuple(out)


def named_probes(spec: FamilySpec) -> dict[str, Fn]:
    truth = spec["truth"]
    train = spec["ood_train"]
    return {
        "truth": truth,
        "shortcut": patch_fn(truth, train, fill=None),
        "memorizer": patch_fn(truth, train, fill=0),
    }


def risk_on(f: Sequence[int], truth: Sequence[int], xs: Sequence[int]) -> float:
    if not xs:
        return 0.0
    return sum(int(f[x] != truth[x]) for x in xs) / len(xs)


def population_risk(f: Sequence[int], truth: Sequence[int]) -> float:
    return hamming(f, truth) / len(truth)


def sample_iid(n: int, m: int, seed: int) -> tuple[int, ...]:
    rng = random.Random(seed)
    return tuple(rng.randrange(n) for _ in range(m))


def train_perfect(truth: Fn, sample: Sequence[int]) -> Iterator[Fn]:
    constrained = {x: truth[x] for x in sample}
    n = len(truth)
    free = [x for x in range(n) if x not in constrained]
    if not free:
        yield truth
        return
    for values in product(range(n), repeat=len(free)):
        out = list(truth)
        for x, value in zip(free, values, strict=True):
            out[x] = value
        for x, y in constrained.items():
            out[x] = y
        yield tuple(out)


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2:
        return None
    rx = _ranks(xs)
    ry = _ranks(ys)
    return _pearson(rx, ry)


def _ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x == 0.0 or den_y == 0.0:
        return None
    return num / (den_x * den_y)


def fixed_action_cyclic_count(n: int) -> int:
    """|{f : f(x+1)=f(x)+1 ∀x}| = n for C_n, ρ = id."""

    count = 0
    for f in iter_functions(n):
        if all(f[(x + 1) % n] == (f[x] + 1) % n for x in range(n)):
            count += 1
    return count


def _scorer(spec: FamilySpec, name: str):
    n = spec["n"]
    group = spec["groups"][name]
    if name == "aligned" and spec["aligned_is_full_symmetric"]:
        return lambda f: weakness_symmetric(f)
    if _is_dihedral(group, n):
        return lambda f: weakness_dihedral(f, n)
    if _is_cyclic_rotations(group, n):
        return lambda f: weakness_cyclic(f, n)
    return lambda f: weakness_family(f, group)


def collect_weakness(spec: FamilySpec) -> dict[str, list[int]]:
    scorers = {name: _scorer(spec, name) for name in GROUP_NAMES}
    out: dict[str, list[int]] = {name: [] for name in GROUP_NAMES}
    for f in iter_functions(spec["n"]):
        for name in GROUP_NAMES:
            out[name].append(scorers[name](f))
    return out


def certificates_for_fn(
    f: Fn,
    spec: FamilySpec,
    weakness_row: dict[str, int],
    cards: dict[str, list[int]],
    pis: dict[str, dict[str, list[Fraction]]],
) -> dict[str, Any]:
    row: dict[str, Any] = {"weakness": weakness_row}
    masses: dict[str, dict[str, str]] = {}
    kls: dict[str, dict[str, float]] = {}
    hyper_mass = Fraction(0)
    for name in GROUP_NAMES:
        masses[name] = {}
        kls[name] = {}
        for schedule in PI_SCHEDULES:
            mass = mixture_mass(weakness_row[name], cards[name], pis[name][schedule])
            masses[name][schedule] = str(mass)
            kls[name][schedule] = kl_dirac(mass)
            if schedule == "uniform":
                hyper_mass += HYPERPRIOR_WEIGHT * mass
    row["mass"] = masses
    row["kl"] = kls
    row["hyper_mass_uniform"] = str(hyper_mass)
    row["hyper_kl_uniform"] = kl_dirac(hyper_mass)
    row["population_risk"] = population_risk(f, spec["truth"])
    row["ood_risk"] = risk_on(f, spec["truth"], spec["ood_test"])
    return row


def _weakness_row(f: Fn, spec: FamilySpec, scorers: dict[str, Any] | None = None) -> dict[str, int]:
    active = scorers or {name: _scorer(spec, name) for name in GROUP_NAMES}
    return {name: active[name](f) for name in GROUP_NAMES}


def evaluate_family(spec: FamilySpec) -> dict[str, Any]:
    n = spec["n"]
    ambient = n**n
    scorers = {name: _scorer(spec, name) for name in GROUP_NAMES}
    weights = collect_weakness(spec)
    cards = {name: level_cards(weights[name], group_order(spec, name)) for name in GROUP_NAMES}
    pis = {
        name: {schedule: mixture_pi(cards[name], schedule) for schedule in PI_SCHEDULES}
        for name in GROUP_NAMES
    }
    probes = named_probes(spec)
    probe_rows: dict[str, Any] = {}
    for probe_name, fn in probes.items():
        wrow = _weakness_row(fn, spec, scorers)
        probe_rows[probe_name] = {
            "function": list(fn),
            **certificates_for_fn(fn, spec, wrow, cards, pis),
        }

    iid_rows = []
    for m in IID_MS:
        for seed in IID_SEEDS:
            sample = sample_iid(n, m, seed)
            labeled = {x: spec["truth"][x] for x in sample}
            w_aligned: list[float] = []
            kl_aligned: list[float] = []
            kl_hyper: list[float] = []
            n_perfect = 0
            truth_lhat = risk_on(spec["truth"], spec["truth"], sample)
            for h in train_perfect(spec["truth"], sample):
                n_perfect += 1
                wrow = _weakness_row(h, spec, scorers)
                cert = certificates_for_fn(h, spec, wrow, cards, pis)
                w_aligned.append(float(wrow["aligned"]))
                kl_aligned.append(cert["kl"]["aligned"]["uniform"])
                kl_hyper.append(cert["hyper_kl_uniform"])
            truth_kl = probe_rows["truth"]["kl"]["aligned"]["uniform"]
            truth_bound = lsm_bound(truth_lhat, truth_kl, m)
            iid_rows.append(
                {
                    "m": m,
                    "seed": seed,
                    "unique_train": len(labeled),
                    "n_train_perfect": n_perfect,
                    "truth_lhat": truth_lhat,
                    "truth_bound": truth_bound,
                    "spearman_w_vs_kl_aligned": spearman(w_aligned, kl_aligned),
                    "spearman_w_vs_kl_hyper": spearman(w_aligned, kl_hyper),
                }
            )

    level_profile = {
        name: {str(k): cards[name][k] for k in range(1, len(cards[name])) if cards[name][k]}
        for name in GROUP_NAMES
    }
    return {
        "family_id": spec["family_id"],
        "n": n,
        "ambient_card": ambient,
        "enumerated": ambient,
        "orbits": spec["orbits"],
        "group_orders": {name: group_order(spec, name) for name in GROUP_NAMES},
        "level_cards": level_profile,
        "probes": probe_rows,
        "iid": iid_rows,
        "fixed_action_eq_count": (
            fixed_action_cyclic_count(n) if spec["family_id"] == "cyclic" else None
        ),
    }


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def evaluate_kills(families: list[dict[str, Any]]) -> dict[str, Any]:
    card_ok = all(row["ambient_card"] == row["enumerated"] == row["n"] ** row["n"] for row in families)
    mass_ok = True
    for row in families:
        for probe in row["probes"].values():
            for name in GROUP_NAMES:
                order = row["group_orders"][name]
                cards = [0] * (order + 1)
                for k_str, count in row["level_cards"][name].items():
                    cards[int(k_str)] = count
                for schedule in PI_SCHEDULES:
                    pi = mixture_pi(cards, schedule)
                    mass = mixture_mass(probe["weakness"][name], cards, pi)
                    if str(mass) != probe["mass"][name][schedule]:
                        mass_ok = False

    cyclic = next(row for row in families if row["family_id"] == "cyclic")
    fixed_ok = cyclic["fixed_action_eq_count"] == cyclic["n"] == 7

    iid_vacuous = False
    hyper_identical = True
    for row in families:
        for item in row["iid"]:
            if item["m"] != 8:
                continue
            if item["truth_bound"] >= VACUOUS_BOUND:
                iid_vacuous = True
            corr = item["spearman_w_vs_kl_hyper"]
            if corr is not None and abs(corr + 1.0) > 1e-12:
                hyper_identical = False

    weight_flip = False
    ood_wrong_tight = False
    ood_kill_families: list[str] = []
    for row in families:
        truth = row["probes"]["truth"]
        shortcut = row["probes"]["shortcut"]
        signs = [
            _sign(
                shortcut["kl"]["aligned"][schedule] - truth["kl"]["aligned"][schedule]
            )
            for schedule in PI_SCHEDULES
        ]
        if len(set(signs)) > 1:
            weight_flip = True
        if shortcut["ood_risk"] > 0.0 and truth["ood_risk"] == 0.0:
            tight_wrong = min(
                shortcut["kl"]["wrong"]["uniform"],
                shortcut["kl"]["random"]["uniform"],
            )
            if tight_wrong <= truth["kl"]["aligned"]["uniform"]:
                ood_wrong_tight = True
                ood_kill_families.append(row["family_id"])

    kills = {
        "class_count_contradiction": not (card_ok and mass_ok and fixed_ok),
        "iid_vacuous": iid_vacuous,
        "hyperprior_no_extra_info": hyper_identical,
        "wrong_group_tight_ood_fail": ood_wrong_tight,
        "weight_sign_flip": weight_flip,
        "neural_untransported": True,
    }
    if kills["class_count_contradiction"]:
        verdict = "instrument_failed"
    elif kills["iid_vacuous"]:
        verdict = "finite_iid_killed"
    elif kills["wrong_group_tight_ood_fail"] or kills["weight_sign_flip"]:
        verdict = "finite_iid_holds_ood_or_weight_killed"
    else:
        verdict = "finite_iid_holds"

    gates = {
        "PB_ENUM_CARDINALITY": card_ok,
        "PB_MASS_FORMULA": mass_ok,
        "PB_FIXED_ACTION": fixed_ok,
        "PB_IID_NONVACUOUS": not iid_vacuous,
        "PB_WEIGHT_STABLE": not weight_flip,
        "PB_HYPERPRIOR_ADDS_INFO": not hyper_identical,
        "PB_OOD_WRONG_GROUP": not ood_wrong_tight,
        "PB_NEURAL_WITHHELD": True,
        "PB_RANKING_RECORDED": True,
        "PB_CLAIM_BOUNDARY": True,
    }
    return {
        "kills": kills,
        "gates": gates,
        "verdict": verdict,
        "ood_kill_families": ood_kill_families,
    }


def evaluate_benchmark() -> dict[str, Any]:
    families = [evaluate_family(spec) for spec in FAMILIES]
    ranking = evaluate_kills(families)
    withheld = [
        "Langford–Seeger–Maurer is cited as a numerical plug-in, not proved.",
        "Neural / stochastic parameter-space PAC-Bayes stays out.",
        "The prefix/coset OOD lane is not certified by the IID kl inequality.",
        "Measure-theoretic T4, CT-1 MDL, classical T7 ICA, unconditional "
        "SIC-C-c, TA-2-cover, RR-1-unique, and SIC-A-gen stay analytic-open.",
    ]
    return {
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "status": "fail" if ranking["verdict"] == "instrument_failed" else "pass",
        "producing_agent": {
            "identity": PRODUCING_AGENT,
            "session_ref": SESSION_REF,
        },
        "process_disclosure": PROCESS_DISCLOSURE,
        "gates": ranking["gates"],
        "kills": ranking["kills"],
        "ranking": {
            "verdict": ranking["verdict"],
            "ood_kill_families": ranking["ood_kill_families"],
            "rule": (
                "instrument_failed if class counts, mass formula, or the "
                "cyclic fixed-action count break. finite_iid_killed if the "
                "m=8 aligned truth bound is ≥ 0.99 on any seed. "
                "finite_iid_holds_ood_or_weight_killed if the IID lane is "
                "non-vacuous but a wrong/random group matches the truth "
                "certificate while the shortcut fails OOD, or π flips the "
                "truth-vs-shortcut KL sign. finite_iid_holds otherwise. "
                "hyperprior_no_extra_info and neural_untransported are "
                "recorded independently and do not rename the verdict."
            ),
        },
        "families": families,
        "withheld": withheld,
        "registered": {
            "iid_seeds": list(IID_SEEDS),
            "iid_ms": list(IID_MS),
            "delta": DELTA,
            "pi_schedules": list(PI_SCHEDULES),
            "vacuous_bound": VACUOUS_BOUND,
        },
    }


def wave11_toy_masses() -> tuple[Fraction, Fraction]:
    """Registered {shortcut, invariant} masses from WeaknessMixture."""

    cards = [0, 2, 1]
    pi = [Fraction(0), Fraction(1, 2), Fraction(1, 2)]
    return mixture_mass(1, cards, pi), mixture_mass(2, cards, pi)
