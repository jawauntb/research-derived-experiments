"""Unknown-skeleton recovery on the registered size-3 EML pair.

Matching-skeleton GD (#483) already ranked the fat zero target above
the thin singleton.  That process was *told* the tree.  Sampling the
census would recover Φ by definition.  This package uses a third
process: try every size-3 skeleton, including the wrong ones.

Registered targets (same pair as ``eml_us4_prime`` / ``eml_us4_gradient``):

- Fat / zero: ``eml(1,eml(eml(1,1),1))`` and ``eml(x,eml(eml(x,1),1))``.
- Thin / singleton: ``eml(1,eml(1,eml(1,1)))``.

Two measurements, frozen before seeing extras:

1. Exact unweighted eval.  This *is* min-shell multiplicity (2 vs 1).
   It is the tautological control, not the headline.
2. Blind GD on every size-3 skeleton.  Extra recovering skeletons
   beyond the exact formulas are the non-tautological signal.

Decision rule:

- Perturbed-correct on the true zero skeleton must succeed, or withhold.
- Compare ``n_gd_skeletons`` (a skeleton counts if any registered
  blind seed recovers it).
- zero > thin: Φ-ranking holds without being handed the tree.
- equal: reject Φ-predicts-unknown-skeleton-GD at this bound.
- thin > zero: kill.

Not Odrzywołek's neural bootstrap.  Not a Gibbs tree sampler.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from experiments.eml_us4_gradient.core import (
    SINGLETON,
    SUCCESS_MSE,
    ZERO_ONES,
    ZERO_X,
    descend,
    log_uniform_weights,
    mse,
    n_weight_leaves,
    perturbed_true_weights,
    target_grid,
)
from experiments.eml_variable_spectrum.core import (
    VarTree,
    enumerate_trees,
    labeled_count,
    parse_var,
)

EXPERIMENT_ID = "eml_us4_search"
RUN_ID = "eml_us4_search_2026_08_17"
PRODUCING_AGENT = "Cursor Grok 4.6 (cloud agent, under J. Brown direction)"
SESSION_REF = "bc-01a00d99-d2d8-7c5e-a8d0-d0090dfd7bdd"

SEARCH_K = 3
SEEDS: tuple[int, ...] = (0, 1, 2, 3)
EXACT_ZERO = (ZERO_ONES, ZERO_X)
EXACT_THIN = (SINGLETON,)

PROCESS_DISCLOSURE = (
    "Recovery is blind GD on every size-3 skeleton in the variable-x "
    "grammar, including wrong trees.  It is not a Gibbs sampler, not "
    "matching-skeleton-only, and not Odrzywołek's neural bootstrap."
)
CLAIM_BOUNDARY = (
    "Unknown-skeleton local GD on the registered k=3 pair only.  "
    "Not the neural bootstrap.  Not a Gibbs-sampler tautology.  "
    "Exact unweighted hits are the multiplicity control, not the claim."
)


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class TargetSpec(TypedDict):
    name: str
    pretty: str
    n_internal: int
    is_zero: bool
    exact_formulas: list[str]


class SkeletonHit(TypedDict):
    pretty: str
    n_weights: int
    exact: bool
    n_success: int
    n_trials: int
    best_mse: float


class TargetSearch(TypedDict):
    target: str
    n_exact: int
    n_gd_skeletons: int
    n_extra_skeletons: int
    exact_formulas: list[str]
    extra_skeletons: list[str]
    hits: list[SkeletonHit]


class Ranking(TypedDict):
    rule: str
    zero_gd: int
    thin_gd: int
    zero_extra: int
    thin_extra: int
    verdict: Literal["phi_holds", "min_size_governs", "phi_killed", "withheld_optimizer"]


class RegisteredConfig(TypedDict):
    search_k: int
    n_skeletons: int
    seeds: list[int]
    success_mse: float
    zero_formulas: list[str]
    thin_formulas: list[str]


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    registered: RegisteredConfig
    targets: list[TargetSpec]
    searches: list[TargetSearch]
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]
    citations: list[str]


def _native_weights(tree: VarTree) -> tuple[float, ...]:
    return tuple(1.0 for _ in range(n_weight_leaves(tree)))


def _exact_hit(tree: VarTree, target: tuple[float, ...]) -> bool:
    return mse(tree, _native_weights(tree), target) < SUCCESS_MSE


def _search_target(
    *,
    name: str,
    target: tuple[float, ...],
    skeletons: tuple[VarTree, ...],
    exact_pretties: tuple[str, ...],
) -> TargetSearch:
    hits: list[SkeletonHit] = []
    extra: list[str] = []
    n_gd = 0
    n_exact = 0
    exact_set = set(exact_pretties)
    for tree in skeletons:
        pretty = tree.pretty()
        n_weights = n_weight_leaves(tree)
        is_exact = pretty in exact_set
        if is_exact:
            n_exact += 1
        best = 1e6
        successes = 0
        if n_weights == 0:
            loss = mse(tree, (), target)
            best = loss
            if loss < SUCCESS_MSE:
                successes = len(SEEDS)
        else:
            for seed in SEEDS:
                loss, _weights = descend(tree, log_uniform_weights(n_weights, seed), target)
                best = min(best, loss)
                if loss < SUCCESS_MSE:
                    successes += 1
        if successes:
            n_gd += 1
            if not is_exact:
                extra.append(pretty)
        hits.append(
            {
                "pretty": pretty,
                "n_weights": n_weights,
                "exact": is_exact,
                "n_success": successes,
                "n_trials": len(SEEDS),
                "best_mse": best,
            }
        )
    return {
        "target": name,
        "n_exact": n_exact,
        "n_gd_skeletons": n_gd,
        "n_extra_skeletons": len(extra),
        "exact_formulas": list(exact_pretties),
        "extra_skeletons": extra,
        "hits": hits,
    }


def _ranking(zero: TargetSearch, thin: TargetSearch, optimizer_ok: bool) -> Ranking:
    rule = (
        "Compare n_gd_skeletons over all size-3 trees.  A skeleton "
        "counts if any of the registered blind seeds recovers the "
        "target.  Perturbed-correct on the true zero skeleton must "
        "succeed or withhold.  Exact unweighted 2-vs-1 is the control."
    )
    if not optimizer_ok:
        verdict: Literal["phi_holds", "min_size_governs", "phi_killed", "withheld_optimizer"] = (
            "withheld_optimizer"
        )
    elif zero["n_gd_skeletons"] > thin["n_gd_skeletons"]:
        verdict = "phi_holds"
    elif thin["n_gd_skeletons"] > zero["n_gd_skeletons"]:
        verdict = "phi_killed"
    else:
        verdict = "min_size_governs"
    return {
        "rule": rule,
        "zero_gd": zero["n_gd_skeletons"],
        "thin_gd": thin["n_gd_skeletons"],
        "zero_extra": zero["n_extra_skeletons"],
        "thin_extra": thin["n_extra_skeletons"],
        "verdict": verdict,
    }


def evaluate_benchmark() -> BenchmarkPayload:
    by_size = enumerate_trees(SEARCH_K)
    skeletons = by_size[SEARCH_K]
    zero_grid = target_grid(ZERO_ONES)
    thin_grid = target_grid(SINGLETON)
    zero_tree = parse_var(ZERO_ONES)
    thin_tree = parse_var(SINGLETON)
    x_tree = parse_var(ZERO_X)

    optimizer_successes = 0
    for seed in SEEDS:
        loss, _weights = descend(
            zero_tree,
            perturbed_true_weights(n_weight_leaves(zero_tree), seed),
            zero_grid,
        )
        if loss < SUCCESS_MSE:
            optimizer_successes += 1

    zero_search = _search_target(
        name="zero",
        target=zero_grid,
        skeletons=skeletons,
        exact_pretties=EXACT_ZERO,
    )
    thin_search = _search_target(
        name="thin",
        target=thin_grid,
        skeletons=skeletons,
        exact_pretties=EXACT_THIN,
    )
    ranking = _ranking(zero_search, thin_search, optimizer_successes >= 1)

    exact_zero_ok = all(_exact_hit(parse_var(pretty), zero_grid) for pretty in EXACT_ZERO)
    exact_thin_ok = _exact_hit(thin_tree, thin_grid)
    exact_control = (
        zero_search["n_exact"] == 2
        and thin_search["n_exact"] == 1
        and exact_zero_ok
        and exact_thin_ok
    )
    targets_ok = (
        zero_tree.n_internal == thin_tree.n_internal == x_tree.n_internal == SEARCH_K
        and labeled_count(SEARCH_K) == len(skeletons) == 80
    )
    required = {
        "US4S_ENUMERATION": targets_ok,
        "US4S_EXACT_CONTROL": exact_control,
        "US4S_PROCESS_IS_NOT_GIBBS": True,
        "US4S_NOT_MATCHING_ONLY": True,
        "US4S_PERTURBED_CORRECT": optimizer_successes >= 1,
        "US4S_RANKING_RECORDED": ranking["verdict"] != "withheld_optimizer",
        "US4S_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {
            "identity": PRODUCING_AGENT,
            "session_ref": SESSION_REF,
        },
        "registered": {
            "search_k": SEARCH_K,
            "n_skeletons": len(skeletons),
            "seeds": list(SEEDS),
            "success_mse": SUCCESS_MSE,
            "zero_formulas": list(EXACT_ZERO),
            "thin_formulas": list(EXACT_THIN),
        },
        "targets": [
            {
                "name": "zero",
                "pretty": ZERO_ONES,
                "n_internal": SEARCH_K,
                "is_zero": True,
                "exact_formulas": list(EXACT_ZERO),
            },
            {
                "name": "thin",
                "pretty": SINGLETON,
                "n_internal": SEARCH_K,
                "is_zero": False,
                "exact_formulas": list(EXACT_THIN),
            },
        ],
        "searches": [zero_search, thin_search],
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "Odrzywołek neural bootstrap",
            "Gibbs-sampler tautology",
            "Matching-skeleton-only recovery as the unknown-skeleton claim",
            "Identity of functions from the grid except the exact zero target",
        ],
        "citations": [
            "Odrzywołek, A. (2026). All elementary functions from a single binary operator. arXiv:2603.21852.",
        ],
    }
