"""Wave 1b SET-level oracle-regret metric harness.

The Wave 1b promotion contract (``PROMOTION_CONTRACT_L1.md`` §7)
adjudicates the candidate mechanism on the SET-level oracle-regret
metrics named in ``PREREGISTRATION.md`` §7:

* :func:`compute_oracle_topk_sets` — enumerate ``Δ_task(S)`` for every
  ``S ⊆ V \\ R_t`` with ``|S| ≤ min(budget, 3)`` and return the top-k
  sets by ``Δ``.
* :func:`oracle_recall_at_k` — the SET-level Recall@k formula
  ``|selected_set ∩ union(oracle_top_k_sets)| / k``.
* :func:`simple_regret_set` — ``max_S Δ(S) − Δ(selected_set)``.
* :func:`interaction_recovery` — per-episode recovery receipt for
  planted complementary pairs and avoidance receipt for planted
  dangerous conjunctions.
* :func:`cumulative_regret` — Σ simple_regret_set across episodes.
* :func:`regret_ci` — deterministic bootstrap confidence interval on a
  set of regret values.

Enumeration budget
------------------
Wave 1b synthetic families satisfy ``|V \\ R_t| ≤ 20``. At size 3 the
enumerator visits ``C(20, 0) + C(20, 1) + C(20, 2) + C(20, 3) = 1
+ 20 + 190 + 1140 = 1351`` sets per episode. That is tractable at
``N = 300`` seeds per cell on Modal L4 workers. The enumerator refuses
to run when ``|V \\ R_t|`` exceeds the module-level ceiling
:data:`MAX_ORACLE_ENUMERATION_CARDINALITY` so a family regression that
grows the candidate set silently is loud.

Anti-leakage
------------
:func:`compute_oracle_topk_sets` is EVALUATOR-side. Its body explicitly
dereferences ``episode._answer_key`` — a member of
:attr:`IntegrityAudit.FORBIDDEN_ATTRS`. Any policy callable whose
source imports this function inherits the flagged attribute reference
and fails :meth:`IntegrityAudit.assert_clean`. That behaviour is pinned
by the wave 1b oracle-regret test suite.

The pure-arithmetic metric helpers (:func:`oracle_recall_at_k`,
:func:`simple_regret_set`, :func:`interaction_recovery`,
:func:`cumulative_regret`, :func:`regret_ci`) do NOT dereference sealed
fields directly — they consume already-scored ``Δ`` maps and planted-
bundle records. They are audit-clean in isolation; the sealed access
happens once in :func:`compute_oracle_topk_sets` and its downstream
users own the propagated evaluator-side status.
"""

from __future__ import annotations

import itertools
import math
import random
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Iterable, Mapping, Sequence

from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeContext,
    EpisodeSpec,
    LeakageError,
)
from experiments.concern_gated_retrieval_e2.wave1b.oracle_receipt import (
    OracleReceipt,
)
from experiments.concern_gated_retrieval_e2.wave1b.sealed_env_ext import (
    OracleSealedEnvironment,
    SetOutcome,
)


# --------------------------------------------------------------------------- #
# Enumeration configuration                                                    #
# --------------------------------------------------------------------------- #


#: Maximum candidate cardinality the oracle enumerator will handle.
#: Wave 1b PREREGISTRATION.md §7 promises ``|V \\ R_t| ≤ 20``; the
#: enumerator refuses to run beyond this ceiling so a family regression
#: that grew the candidate set past 20 (and would push the triple
#: enumeration past ``C(21, 3) = 1330``, more than doubling the pair
#: enumeration up to that point) is a loud refusal rather than a silent
#: cost blowup.
MAX_ORACLE_ENUMERATION_CARDINALITY: Final[int] = 20


#: Maximum subset size the enumerator visits. Wave 1b PREREGISTRATION.md
#: §7 stops at feasibility-gated triples; anything larger is out of
#: scope. Held as a module-level constant so a downstream sensitivity
#: study can override it deliberately (and the receipt records the
#: override).
MAX_ORACLE_ENUMERATION_SET_SIZE: Final[int] = 3


# --------------------------------------------------------------------------- #
# PlantedBundles (family-agnostic normalized shape)                            #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class PlantedBundles:
    """Normalized per-episode record of planted bundle structures.

    Each Wave 1b v2 family has its own :class:`BundleManifest` schema
    (``delayed_commitments_v2`` and ``maintenance_fault_v2`` use
    ``Optional`` fields keyed on the template's primary bundle type;
    ``resource_constrained_v2`` plants one of every bundle type per
    episode). :class:`PlantedBundles` is the family-agnostic shape the
    metric helpers consume; :func:`planted_bundles_from_manifest` and
    the family-specific converters build it from a family manifest.
    """

    useful_singletons: tuple[str, ...] = ()
    contradictory_pairs: tuple[tuple[str, str], ...] = ()
    complementary_pairs: tuple[tuple[str, str], ...] = ()
    dangerous_conjunctions: tuple[tuple[str, ...], ...] = ()
    isolation_distractors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.useful_singletons, tuple):
            raise TypeError("useful_singletons must be a tuple[str, ...]")
        for pair in self.complementary_pairs:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise ValueError(
                    "each complementary_pairs entry must be a 2-tuple"
                )
        for pair in self.contradictory_pairs:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise ValueError(
                    "each contradictory_pairs entry must be a 2-tuple"
                )
        for triple in self.dangerous_conjunctions:
            if not isinstance(triple, tuple) or len(triple) < 2:
                raise ValueError(
                    "each dangerous_conjunctions entry must be a tuple with "
                    "at least two members"
                )


def planted_bundles_from_manifest(manifest: Any) -> PlantedBundles:
    """Duck-typed conversion from a family ``BundleManifest`` to :class:`PlantedBundles`.

    The three Wave 1b v2 families share attribute names
    (``useful_singleton``, ``complementary_pair``,
    ``contradictory_pair``, ``dangerous_conjunction``,
    ``isolation_distractor``) but disagree on whether every attribute
    is populated per episode. This converter normalises both schemas
    into :class:`PlantedBundles` — an unpopulated ``None`` becomes an
    empty tuple, a scalar becomes a singleton tuple, a 2-tuple/3-tuple
    becomes a one-element tuple of that tuple.

    ``resource_constrained_v2.BundleManifest`` names its answer-key
    field ``load_bearing_singleton`` rather than ``useful_singleton``;
    the converter reads whichever is present.
    """

    def _get(*names: str) -> Any:
        for name in names:
            if hasattr(manifest, name):
                value = getattr(manifest, name)
                if value is not None:
                    return value
        return None

    useful = _get("useful_singleton", "load_bearing_singleton")
    complementary = _get("complementary_pair")
    contradictory = _get("contradictory_pair")
    dangerous = _get("dangerous_conjunction")
    isolation = _get("isolation_distractor")

    return PlantedBundles(
        useful_singletons=(useful,) if isinstance(useful, str) else tuple(),
        complementary_pairs=(complementary,) if isinstance(complementary, tuple) else tuple(),
        contradictory_pairs=(contradictory,) if isinstance(contradictory, tuple) else tuple(),
        dangerous_conjunctions=(dangerous,) if isinstance(dangerous, tuple) else tuple(),
        isolation_distractors=(isolation,) if isinstance(isolation, str) else tuple(),
    )


# --------------------------------------------------------------------------- #
# Enumeration result                                                           #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class OracleEnumeration:
    """Result of a full SET-level oracle enumeration on one episode.

    Attributes
    ----------
    top_k_sets:
        The ``k`` sets with the highest ``Δ_task``, in descending
        ``Δ`` order. Ties broken by lexicographic order over the
        canonical-sorted set tuple so the receipt is deterministic.
    delta_map:
        Every enumerated set (keyed by :class:`frozenset`) mapped to
        its ``Δ_task``. The union of keys is exactly the enumerated
        subset lattice up to :data:`MAX_ORACLE_ENUMERATION_SET_SIZE`.
    outcome_map:
        Every enumerated set mapped to its full
        :class:`SetOutcome` (deltas + provenance fields). Downstream
        analyses (e.g. bundle-awareness bookkeeping in the wave 1b
        PROVENANCE §7 writer) consume this shape.
    total_sets_enumerated:
        Cardinality of ``delta_map``. Reported so a Modal worker can
        record enumeration cost against the family.
    """

    top_k_sets: tuple[tuple[str, ...], ...]
    delta_map: Mapping[frozenset[str], float]
    outcome_map: Mapping[frozenset[str], SetOutcome]
    total_sets_enumerated: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "delta_map", MappingProxyType(dict(self.delta_map))
        )
        object.__setattr__(
            self, "outcome_map", MappingProxyType(dict(self.outcome_map))
        )


# --------------------------------------------------------------------------- #
# compute_oracle_topk_sets                                                     #
# --------------------------------------------------------------------------- #


def _validate_episode(episode: EpisodeSpec) -> tuple[str, ...]:
    """Validate ``episode`` and touch a sealed attribute for the audit.

    Rejects an :class:`EpisodeContext` (policy-visible view) — the
    oracle path requires the sealed :class:`EpisodeSpec`. The explicit
    ``episode._answer_key`` dereference propagates the sealed
    attribute reference into this module so any policy callable that
    imports :func:`compute_oracle_topk_sets` fails
    :meth:`IntegrityAudit.assert_clean`.
    """
    if isinstance(episode, EpisodeContext):
        raise LeakageError(
            "compute_oracle_topk_sets refuses an EpisodeContext (the "
            "policy-visible view). Oracle enumeration requires the sealed "
            "EpisodeSpec; see wave1b/PREREGISTRATION.md §7."
        )
    if not isinstance(episode, EpisodeSpec):
        raise TypeError(
            "compute_oracle_topk_sets requires an EpisodeSpec instance; got "
            f"{type(episode).__name__}"
        )
    # Sentinel dereference — see docstring. Reads a member of
    # ``IntegrityAudit.FORBIDDEN_ATTRS`` so this function's source flags
    # the audit for any downstream policy that references it.
    sealed_answer_key: tuple[str, ...] = episode._answer_key
    return sealed_answer_key


def _enumerate_delta_map(
    episode: EpisodeSpec,
    budget: int,
) -> tuple[dict[frozenset[str], SetOutcome], OracleSealedEnvironment]:
    """Enumerate every subset up to ``min(budget, MAX_SET_SIZE)`` and score it."""
    if not isinstance(budget, int) or isinstance(budget, bool):
        raise TypeError("budget must be a non-boolean int")
    if budget <= 0:
        raise ValueError(f"budget must be positive; got {budget}")

    candidates = tuple(episode.candidate_nodes)
    n = len(candidates)
    if n > MAX_ORACLE_ENUMERATION_CARDINALITY:
        raise ValueError(
            f"oracle enumeration refuses |V \\\\ R_t| = {n} > "
            f"{MAX_ORACLE_ENUMERATION_CARDINALITY}; see "
            "wave1b/PREREGISTRATION.md §7 for the enumeration bound."
        )

    max_set_size = min(budget, MAX_ORACLE_ENUMERATION_SET_SIZE)

    mode = (
        "calibration"
        if episode.template_family_split == "calibration"
        else "confirmatory"
    )
    env = OracleSealedEnvironment(episode, mode=mode)
    # Observe once so the wrapped wave0 env's observe/evaluate contract
    # is respected (a policy path may still call evaluate() later).
    env.observe(seed=episode.seed)

    outcome_map: dict[frozenset[str], SetOutcome] = {}
    for size in range(0, max_set_size + 1):
        for combo in itertools.combinations(candidates, size):
            key = frozenset(combo)
            outcome = env.evaluate_set(key)
            outcome_map[key] = outcome
    return outcome_map, env


def enumerate_set_deltas(episode: EpisodeSpec, budget: int) -> OracleEnumeration:
    """Return the full :class:`OracleEnumeration` for one episode.

    EVALUATOR-side. Explicitly dereferences ``episode._answer_key`` at
    the top of the body so :meth:`IntegrityAudit.assert_clean` fires on
    any policy callable whose source imports this function. Delegates
    the actual enumeration to :func:`_enumerate_delta_map`.
    """
    _validate_episode(episode)
    # Sentinel dereference — ``_answer_key`` is a member of
    # ``IntegrityAudit.FORBIDDEN_ATTRS``; touching it here means any
    # policy source that references ``enumerate_set_deltas`` (directly
    # or via re-export) fails the audit.
    _sealed_answer_probe: tuple[str, ...] = episode._answer_key
    del _sealed_answer_probe
    outcome_map, _env = _enumerate_delta_map(episode, budget)
    delta_map = {key: outcome.delta_task for key, outcome in outcome_map.items()}

    # Sort by (-delta, canonical tuple) so ties are broken deterministically.
    ranked = sorted(
        outcome_map.keys(),
        key=lambda s: (-delta_map[s], tuple(sorted(s))),
    )
    top_k_sets = tuple(tuple(sorted(s)) for s in ranked[:budget])
    return OracleEnumeration(
        top_k_sets=top_k_sets,
        delta_map=delta_map,
        outcome_map=outcome_map,
        total_sets_enumerated=len(outcome_map),
    )


def compute_oracle_topk_sets(
    episode: EpisodeSpec,
    budget: int,
) -> tuple[tuple[str, ...], ...]:
    """Return the top-k sets by ``Δ_task(S)`` for one episode.

    See :func:`enumerate_set_deltas` for the ranked companion function
    that also returns the full ``S -> Δ`` map. EVALUATOR-side.

    Parameters
    ----------
    episode:
        The sealed :class:`EpisodeSpec`. Passing an
        :class:`EpisodeContext` raises :class:`LeakageError`.
    budget:
        The retrieval budget ``k`` used both to (a) cap the enumerated
        subset size at ``min(budget, MAX_ORACLE_ENUMERATION_SET_SIZE)``
        and (b) select the top ``k`` returned sets.

    Returns
    -------
    tuple[tuple[str, ...], ...]
        The top ``budget`` sets by ``Δ_task``, in descending ``Δ`` order.
        Each entry is a canonical-sorted tuple of node ids so the
        receipt is deterministic across processes.
    """
    # Sentinel dereference — ``_answer_key`` is a member of
    # ``IntegrityAudit.FORBIDDEN_ATTRS``; touching it directly in this
    # function's body (not just in a called helper) is what causes
    # :meth:`IntegrityAudit.assert_clean` to fail when this function is
    # audited as a policy callable. The Wave 1b oracle-regret test suite
    # pins that behaviour.
    if isinstance(episode, EpisodeSpec):
        _sealed_answer_probe: tuple[str, ...] = episode._answer_key
        del _sealed_answer_probe
    enumeration = enumerate_set_deltas(episode, budget)
    return enumeration.top_k_sets


# --------------------------------------------------------------------------- #
# Metric helpers (pure arithmetic)                                             #
# --------------------------------------------------------------------------- #


def oracle_recall_at_k(
    selected_set: Iterable[str],
    oracle_top_k_sets: Sequence[Sequence[str]],
    budget: int,
) -> float:
    """SET-level Recall@k formula from Wave 1b PREREGISTRATION.md §7.

    ``|selected_set ∩ union(oracle_top_k_sets)| / budget``

    ``budget`` is the ``k`` in Recall@k — the denominator is fixed at
    ``k`` rather than at ``|selected_set|`` per the preregistration
    (a policy that returns ``|S| < k`` is penalised by the fixed
    denominator, which is the intended behaviour). ``k`` must be
    positive.
    """
    if not isinstance(budget, int) or isinstance(budget, bool):
        raise TypeError("budget must be a non-boolean int")
    if budget <= 0:
        raise ValueError(f"budget must be positive; got {budget}")
    selected = frozenset(selected_set)
    oracle_union: set[str] = set()
    for s in oracle_top_k_sets:
        oracle_union.update(s)
    overlap = len(selected & oracle_union)
    # The denominator is capped at ``budget`` per Wave 1b §7. A policy
    # cannot recall more than ``budget`` items because its own
    # selection is capped at ``budget``; the intersection with the
    # oracle union is therefore bounded by ``min(budget, |oracle_union|)``.
    return float(overlap) / float(budget)


def simple_regret_set(
    selected_set: Iterable[str],
    oracle_top_k_sets: Sequence[Sequence[str]],
    delta_sets: Mapping[frozenset[str], float],
) -> float:
    """Return ``max_S Δ(S) − Δ(selected_set)`` — SET-level simple regret.

    Both ``selected_set`` and the best oracle set (the first entry in
    ``oracle_top_k_sets``, which :func:`enumerate_set_deltas` sorts by
    descending ``Δ``) must have entries in ``delta_sets``; a missing
    key raises :class:`KeyError` so a caller bug that scored the
    policy's set on a different scoring pass is loud.

    The returned regret is non-negative because the best oracle set
    is by construction the ``argmax_S Δ(S)`` over the enumerated
    subset lattice, and the policy's set is one of those enumerated
    subsets (Wave 1b policies retrieve at most ``budget`` nodes, and
    :func:`enumerate_set_deltas` enumerates every ``S`` with
    ``|S| ≤ min(budget, 3)``).
    """
    if not oracle_top_k_sets:
        raise ValueError("oracle_top_k_sets must be non-empty")
    best_key = frozenset(oracle_top_k_sets[0])
    if best_key not in delta_sets:
        raise KeyError(
            "oracle_top_k_sets[0] is not scored in delta_sets: "
            f"{sorted(best_key)}"
        )
    selected_key = frozenset(selected_set)
    if selected_key not in delta_sets:
        raise KeyError(
            "selected_set is not scored in delta_sets: "
            f"{sorted(selected_key)}"
        )
    regret = float(delta_sets[best_key]) - float(delta_sets[selected_key])
    # Numerical clamp: the scorer clamps ``Δ`` to ``[-1, 1]``, so a
    # sub-``0`` regret is either the argmax being tied with the
    # policy (regret ~ 0) or floating-point noise.
    return max(0.0, regret)


def interaction_recovery(
    selected_set: Iterable[str],
    planted_bundles: PlantedBundles,
) -> Mapping[str, Any]:
    """Return the interaction-recovery receipt for one episode.

    Reports:

    * ``complementary_recovered`` — tuple of
      ``(pair_members, recovered_flag)`` entries.  ``recovered_flag``
      is True iff both members of the planted complementary pair are
      in ``selected_set``.
    * ``dangerous_avoided`` — tuple of
      ``(triple_members, avoided_flag)`` entries.  ``avoided_flag`` is
      True iff at least one member of the planted dangerous
      conjunction is NOT in ``selected_set``.
    * ``num_complementary_recovered`` — integer summary.
    * ``num_dangerous_avoided`` — integer summary.

    The keys are pinned by :data:`INTERACTION_RECOVERY_KEYS` so the
    schema is stable across the Wave 1b receipt writer and the
    downstream promotion harness.
    """
    if not isinstance(planted_bundles, PlantedBundles):
        raise TypeError(
            "planted_bundles must be a PlantedBundles instance; got "
            f"{type(planted_bundles).__name__}"
        )
    selected = frozenset(selected_set)
    complementary_receipt: list[tuple[tuple[str, str], bool]] = []
    for pair in planted_bundles.complementary_pairs:
        recovered = frozenset(pair).issubset(selected)
        complementary_receipt.append((pair, recovered))
    dangerous_receipt: list[tuple[tuple[str, ...], bool]] = []
    for triple in planted_bundles.dangerous_conjunctions:
        # "Avoided" iff NOT every member is loaded. A partial hit still
        # counts as avoided because the constraint violation only
        # triggers on the full conjunction (see maintenance_fault_v2 for
        # the sealed contract).
        avoided = not frozenset(triple).issubset(selected)
        dangerous_receipt.append((triple, avoided))
    num_complementary = sum(1 for _, r in complementary_receipt if r)
    num_dangerous_avoided = sum(1 for _, a in dangerous_receipt if a)
    return MappingProxyType(
        {
            "complementary_recovered": tuple(complementary_receipt),
            "dangerous_avoided": tuple(dangerous_receipt),
            "num_complementary_recovered": num_complementary,
            "num_dangerous_avoided": num_dangerous_avoided,
        }
    )


def planted_bundles_recovered(
    selected_set: Iterable[str],
    planted_bundles: PlantedBundles,
) -> Mapping[str, Any]:
    """Return the compact per-episode bundle-recovery summary.

    Used by :class:`OracleReceipt.planted_bundles_recovered` and the
    G6 bundle-awareness gate.

    Keys are pinned by :data:`PLANTED_BUNDLES_RECOVERED_KEYS`.
    """
    selected = frozenset(selected_set)
    useful_recovered = sum(
        1 for node in planted_bundles.useful_singletons if node in selected
    )
    complementary_recovered = sum(
        1
        for pair in planted_bundles.complementary_pairs
        if frozenset(pair).issubset(selected)
    )
    contradictory_avoided = sum(
        1
        for pair in planted_bundles.contradictory_pairs
        if not frozenset(pair).issubset(selected)
    )
    dangerous_avoided = sum(
        1
        for triple in planted_bundles.dangerous_conjunctions
        if not frozenset(triple).issubset(selected)
    )
    isolation_avoided = sum(
        1 for node in planted_bundles.isolation_distractors if node not in selected
    )
    return MappingProxyType(
        {
            "useful_singletons_recovered": useful_recovered,
            "complementary_pairs_recovered": complementary_recovered,
            "contradictory_pairs_avoided": contradictory_avoided,
            "dangerous_conjunctions_avoided": dangerous_avoided,
            "isolation_distractors_avoided": isolation_avoided,
        }
    )


def cumulative_regret(episode_receipts: Sequence[OracleReceipt]) -> float:
    """Return ``Σ simple_regret_set`` across the given receipts."""
    return float(sum(r.simple_regret_set for r in episode_receipts))


# --------------------------------------------------------------------------- #
# Bootstrap confidence interval                                                #
# --------------------------------------------------------------------------- #


#: Default bootstrap resample count for :func:`regret_ci`. 1000 sits
#: below the Wave 1b Modal-worker per-episode cost ceiling while
#: giving the CI bounds ~1% resolution at the 95% level; larger values
#: are available via the ``n_bootstrap`` argument.
DEFAULT_BOOTSTRAP_RESAMPLES: Final[int] = 1000


#: Default confidence level for :func:`regret_ci`. Frozen at 95% per
#: the Wave 1b promotion contract's paired-seed ``Δ - 2σ`` receipt.
DEFAULT_CONFIDENCE_LEVEL: Final[float] = 0.95


#: Deterministic default bootstrap seed. A named constant (rather than
#: a magic literal) so downstream code that reproduces the CI can
#: reference it.
DEFAULT_BOOTSTRAP_SEED: Final[int] = 0


def regret_ci(
    regret_values: Sequence[float],
    *,
    n_bootstrap: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    confidence: float = DEFAULT_CONFIDENCE_LEVEL,
    seed: int = DEFAULT_BOOTSTRAP_SEED,
) -> tuple[float, float]:
    """Deterministic bootstrap CI on the mean of ``regret_values``.

    Uses :class:`random.Random` seeded with ``seed`` so two calls with
    identical arguments return byte-identical bounds. Percentile
    bootstrap; the CI is the ``[(1 - conf)/2, (1 + conf)/2]``
    percentiles of the resampled means.

    Returns ``(0.0, 0.0)`` on an empty input.
    """
    if n_bootstrap <= 0:
        raise ValueError(f"n_bootstrap must be positive; got {n_bootstrap}")
    if not (0.0 < confidence < 1.0):
        raise ValueError(
            f"confidence must lie in (0, 1); got {confidence}"
        )
    values = [float(v) for v in regret_values]
    n = len(values)
    if n == 0:
        return (0.0, 0.0)

    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(n_bootstrap):
        # Independent resample with replacement. ``rng.choices`` matches
        # ``rng.randrange`` in draws but is more concise; use
        # ``rng.randrange`` explicitly so the bootstrap is
        # bit-reproducible across Python versions.
        total = 0.0
        for _ in range(n):
            total += values[rng.randrange(n)]
        means.append(total / n)
    means.sort()
    lower_percentile = (1.0 - confidence) / 2.0
    upper_percentile = 1.0 - lower_percentile
    lo_idx = int(math.floor(lower_percentile * n_bootstrap))
    hi_idx = int(math.ceil(upper_percentile * n_bootstrap)) - 1
    lo_idx = max(0, min(n_bootstrap - 1, lo_idx))
    hi_idx = max(0, min(n_bootstrap - 1, hi_idx))
    return (float(means[lo_idx]), float(means[hi_idx]))


# --------------------------------------------------------------------------- #
# OracleReceipt convenience builder                                            #
# --------------------------------------------------------------------------- #


def build_oracle_receipt(
    *,
    policy: str,
    family: str,
    seed: int,
    selected_set: Iterable[str],
    enumeration: OracleEnumeration,
    planted_bundles: PlantedBundles,
) -> OracleReceipt:
    """Assemble one :class:`OracleReceipt` from an enumeration + planted bundles.

    The wave 1b runner is the intended caller. Kept in this module so
    the runner does not need to reimplement the metric composition
    inline.
    """
    selected_tuple = tuple(sorted(set(selected_set)))
    recall = oracle_recall_at_k(
        selected_tuple, enumeration.top_k_sets, budget=len(enumeration.top_k_sets)
    )
    regret = simple_regret_set(
        selected_tuple, enumeration.top_k_sets, enumeration.delta_map
    )
    ir = interaction_recovery(selected_tuple, planted_bundles)
    pbr = planted_bundles_recovered(selected_tuple, planted_bundles)
    return OracleReceipt(
        policy=policy,
        family=family,
        seed=seed,
        selected_set=selected_tuple,
        oracle_top_k_sets=enumeration.top_k_sets,
        recall_at_k=recall,
        simple_regret_set=regret,
        interaction_recovery=ir,
        planted_bundles_recovered=pbr,
    )


__all__ = [
    "DEFAULT_BOOTSTRAP_RESAMPLES",
    "DEFAULT_BOOTSTRAP_SEED",
    "DEFAULT_CONFIDENCE_LEVEL",
    "MAX_ORACLE_ENUMERATION_CARDINALITY",
    "MAX_ORACLE_ENUMERATION_SET_SIZE",
    "OracleEnumeration",
    "PlantedBundles",
    "build_oracle_receipt",
    "compute_oracle_topk_sets",
    "cumulative_regret",
    "enumerate_set_deltas",
    "interaction_recovery",
    "oracle_recall_at_k",
    "planted_bundles_from_manifest",
    "planted_bundles_recovered",
    "regret_ci",
    "simple_regret_set",
]
