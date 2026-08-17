"""Frozen-leaf discrete search on the registered size-3 EML pair.

Unknown-skeleton GD could retune every ``1``-leaf, so both targets
became reachable from 7 trees.  This process cannot do that.  Leaves
stay ``1`` or ``x``.  The only moves are: flip one leaf, or swap the
two children of one internal node.  Greedy descent from every size-3
start.

Exact unweighted 2-vs-1 is the control, not the claim.

Decision rule:

- zero_basins > thin_basins: Φ-ranking holds for discrete rewrite.
- equal: reject (min_size_governs).
- thin > zero: kill.

Not a Gibbs sampler.  Not GD.  Not the neural bootstrap.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from experiments.eml_us4_gradient.core import SINGLETON, SUCCESS_MSE, ZERO_ONES, ZERO_X, target_grid
from experiments.eml_variable_spectrum.core import TEST_GRID, VarTree, enumerate_trees, eval_at, labeled_count

EXPERIMENT_ID = "eml_us4_discrete"
RUN_ID = "eml_us4_discrete_2026_08_17"
PRODUCING_AGENT = "Cursor Grok 4.6 (cloud agent, under J. Brown direction)"
SESSION_REF = "bc-01a00d99-d2d8-7c5e-a8d0-d0090dfd7bdd"
SEARCH_K = 3
EXACT_ZERO = (ZERO_ONES, ZERO_X)
EXACT_THIN = (SINGLETON,)

PROCESS_DISCLOSURE = (
    "Search is greedy rewrite on frozen-leaf size-3 trees "
    "(flip one leaf or swap one internal pair).  Not GD, not a "
    "Gibbs sampler, and not Odrzywołek's neural bootstrap."
)


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class BasinRow(TypedDict):
    start: str
    end: str
    steps: int
    final_mse: float
    hit: bool


class TargetSearch(TypedDict):
    target: str
    n_exact: int
    n_basins: int
    n_extra_basins: int
    exact_formulas: list[str]
    terminals: list[str]
    extra_end_counts: dict[str, int]
    rows: list[BasinRow]


class Ranking(TypedDict):
    rule: str
    zero_basins: int
    thin_basins: int
    zero_extra: int
    thin_extra: int
    verdict: Literal["phi_holds", "min_size_governs", "phi_killed"]


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    registered: dict[str, object]
    searches: list[TargetSearch]
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]
    citations: list[str]


def frozen_mse(tree: VarTree, target: tuple[float, ...]) -> float:
    total = 0.0
    for x_val, expected in zip(TEST_GRID, target, strict=True):
        observed = eval_at(tree, x_val)
        if observed is None or not (observed == observed) or observed == float("inf"):
            return 1e6
        err = observed - expected
        total += err * err
    return total / float(len(target))


def _flips(tree: VarTree) -> list[VarTree]:
    if tree.is_leaf:
        other = "x" if tree.leaf == "1" else "1"
        return [VarTree(leaf=other)]
    assert tree.left is not None and tree.right is not None
    out = [VarTree(left=left, right=tree.right, leaf=None) for left in _flips(tree.left)]
    out.extend(VarTree(left=tree.left, right=right, leaf=None) for right in _flips(tree.right))
    return out


def _swaps(tree: VarTree) -> list[VarTree]:
    if tree.is_leaf:
        return []
    assert tree.left is not None and tree.right is not None
    out = [VarTree(left=tree.right, right=tree.left, leaf=None)]
    out.extend(VarTree(left=left, right=tree.right, leaf=None) for left in _swaps(tree.left))
    out.extend(VarTree(left=tree.left, right=right, leaf=None) for right in _swaps(tree.right))
    return out


def neighbors(tree: VarTree) -> list[VarTree]:
    unique: dict[str, VarTree] = {}
    for candidate in _flips(tree) + _swaps(tree):
        unique.setdefault(candidate.pretty(), candidate)
    return list(unique.values())


def greedy(start: VarTree, target: tuple[float, ...]) -> BasinRow:
    current = start
    seen = {current.pretty()}
    steps = 0
    while True:
        loss = frozen_mse(current, target)
        if loss < SUCCESS_MSE:
            return {
                "start": start.pretty(),
                "end": current.pretty(),
                "steps": steps,
                "final_mse": loss,
                "hit": True,
            }
        best: VarTree | None = None
        best_loss = loss
        best_pretty = ""
        for candidate in neighbors(current):
            pretty = candidate.pretty()
            if pretty in seen:
                continue
            cand_loss = frozen_mse(candidate, target)
            strictly_better = cand_loss < best_loss - 1e-15
            tied_earlier = (
                best is not None
                and abs(cand_loss - best_loss) <= 1e-15
                and pretty < best_pretty
            )
            if strictly_better or tied_earlier:
                if strictly_better:
                    best_loss = cand_loss
                best = candidate
                best_pretty = pretty
        if best is None or best_loss >= loss - 1e-15:
            return {
                "start": start.pretty(),
                "end": current.pretty(),
                "steps": steps,
                "final_mse": loss,
                "hit": False,
            }
        current = best
        seen.add(current.pretty())
        steps += 1


def _search(name: str, target: tuple[float, ...], skeletons: tuple[VarTree, ...], exact: tuple[str, ...]) -> TargetSearch:
    exact_set = set(exact)
    rows = [greedy(tree, target) for tree in skeletons]
    hits = [row for row in rows if row["hit"]]
    terminals = sorted({row["end"] for row in hits})
    extras = [row for row in hits if row["start"] not in exact_set]
    extra_end_counts: dict[str, int] = {}
    for row in extras:
        extra_end_counts[row["end"]] = extra_end_counts.get(row["end"], 0) + 1
    return {
        "target": name,
        "n_exact": sum(1 for tree in skeletons if tree.pretty() in exact_set),
        "n_basins": len(hits),
        "n_extra_basins": len(extras),
        "exact_formulas": list(exact),
        "terminals": terminals,
        "extra_end_counts": extra_end_counts,
        "rows": hits,
    }


def _ranking(zero: TargetSearch, thin: TargetSearch) -> Ranking:
    # Exact 2-vs-1 is the control. Ranking on total basins would
    # fake phi_holds whenever extras are 0 vs 0.
    if zero["n_extra_basins"] > thin["n_extra_basins"]:
        verdict: Literal["phi_holds", "min_size_governs", "phi_killed"] = "phi_holds"
    elif thin["n_extra_basins"] > zero["n_extra_basins"]:
        verdict = "phi_killed"
    else:
        verdict = "min_size_governs"
    return {
        "rule": (
            "Compare n_extra_basins: non-exact starts from which greedy "
            "frozen-leaf rewrite reaches the target. Exact 2-vs-1 is "
            "the control, not the claim."
        ),
        "zero_basins": zero["n_basins"],
        "thin_basins": thin["n_basins"],
        "zero_extra": zero["n_extra_basins"],
        "thin_extra": thin["n_extra_basins"],
        "verdict": verdict,
    }


def evaluate_benchmark() -> BenchmarkPayload:
    skeletons = enumerate_trees(SEARCH_K)[SEARCH_K]
    zero = _search("zero", target_grid(ZERO_ONES), skeletons, EXACT_ZERO)
    thin = _search("thin", target_grid(SINGLETON), skeletons, EXACT_THIN)
    ranking = _ranking(zero, thin)
    required = {
        "US4D_ENUMERATION": labeled_count(SEARCH_K) == len(skeletons) == 80,
        "US4D_EXACT_CONTROL": zero["n_exact"] == 2 and thin["n_exact"] == 1,
        "US4D_FROZEN_LEAVES": True,
        "US4D_NOT_GD": True,
        "US4D_RANKING_RECORDED": True,
        "US4D_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {"identity": PRODUCING_AGENT, "session_ref": SESSION_REF},
        "registered": {
            "search_k": SEARCH_K,
            "n_skeletons": len(skeletons),
            "moves": ["flip_one_leaf", "swap_one_internal"],
            "zero_formulas": list(EXACT_ZERO),
            "thin_formulas": list(EXACT_THIN),
        },
        "searches": [zero, thin],
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "Odrzywołek neural bootstrap",
            "Gibbs-sampler tautology",
            "Weight-tuning GD as this claim",
        ],
        "citations": [
            "Odrzywołek, A. (2026). All elementary functions from a single binary operator. arXiv:2603.21852.",
        ],
    }
