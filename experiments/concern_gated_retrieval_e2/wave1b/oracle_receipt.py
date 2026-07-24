"""Wave 1b oracle-regret per-episode receipt.

One :class:`OracleReceipt` per ``(policy, family, seed)`` triple. The
receipt is the artifact the wave 1b promotion harness serializes into
``PROVENANCE.md`` §7 and consumes to compute the cell-level oracle-regret
statistics.

Fields
------
* ``policy`` — the wave 1b policy id under test (a
  :mod:`experiments.concern_gated_retrieval_e2.wave0.baselines` name,
  the candidate mechanism ``multiplicative_ppr``, or a Wave 1b-labelled
  ablation such as ``k_split_care_uncertain_audit_70_20_10``).
* ``family`` — the wave 0
  :data:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.ProceduralFamily`
  literal for the row (``delayed_commitments``, ``maintenance_fault``,
  or ``resource_constrained``); the Wave 1b runner records the ``_v2``
  suffix separately in the surrounding row context so this field stays
  aligned with the sealed-env ``family`` tag.
* ``seed`` — the confirmatory seed in ``200000..201999`` (or the
  calibration seed in ``100000..100999`` for calibration receipts).
* ``selected_set`` — the ``S`` the policy chose, in canonical sorted
  order (same convention as
  :attr:`experiments.concern_gated_retrieval_e2.wave1b.sealed_env_ext.SetOutcome.selected_set`).
* ``oracle_top_k_sets`` — the top-k sets by ``Δ_task(S)`` returned by
  :func:`compute_oracle_topk_sets`, in descending ``Δ`` order.
* ``recall_at_k`` — the SET-level Recall@k formula from Wave 1b
  PREREGISTRATION.md §7:
  ``|selected_set ∩ union(oracle_top_k_sets)| / k``.
* ``simple_regret_set`` — ``max_S Δ(S) − Δ(selected_set)`` where the
  ``max_S`` runs over the enumerated oracle sets.
* ``interaction_recovery`` — the per-bundle receipt from
  :func:`interaction_recovery`; a mapping from bundle-type label to a
  tuple of ``(bundle_members, recovered_flag)`` entries plus the two
  summary integers ``num_complementary_recovered`` and
  ``num_dangerous_avoided``.
* ``planted_bundles_recovered`` — a compact per-episode summary of the
  planted bundle types and whether the policy recovered them; used by
  the G6 bundle-awareness gate in ``PROMOTION_CONTRACT_L1.md``.

Evaluator-only.  The receipt itself carries evaluator-side quantities
(oracle top-k, simple regret, interaction recovery) that are computed
against sealed fields. Policy code does not receive the receipt; the
wave 1b runner is the only caller. This module deliberately does not
import ``episode._answer_key``/``role``/``utility`` directly so it can be
touched by lightweight orchestration code without dragging the sealed
attributes into their AST — the receipt is a dumb container.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping


#: Canonical key set for :attr:`OracleReceipt.interaction_recovery`.
#: Fixed here so downstream code (analysis notebooks, ``PROVENANCE.md``
#: writers) can rely on a stable schema.
INTERACTION_RECOVERY_KEYS: Final[tuple[str, ...]] = (
    "complementary_recovered",
    "dangerous_avoided",
    "num_complementary_recovered",
    "num_dangerous_avoided",
)


#: Canonical key set for :attr:`OracleReceipt.planted_bundles_recovered`.
#: Fixed here so downstream code can rely on a stable schema. The four
#: keys mirror the non-singleton bundle types in
#: :data:`experiments.concern_gated_retrieval_e2.wave1b.families.delayed_commitments_v2.BUNDLE_TYPES`.
PLANTED_BUNDLES_RECOVERED_KEYS: Final[tuple[str, ...]] = (
    "useful_singletons_recovered",
    "complementary_pairs_recovered",
    "contradictory_pairs_avoided",
    "dangerous_conjunctions_avoided",
    "isolation_distractors_avoided",
)


@dataclass(frozen=True)
class OracleReceipt:
    """One per-episode oracle-regret receipt.

    Immutable and hashable so downstream aggregation code can key on
    the receipt directly (e.g. deduplicate by
    ``(policy, family, seed)`` at the boundary between the Modal
    worker and the Wave 1b runner's aggregator).
    """

    policy: str
    family: str
    seed: int
    selected_set: tuple[str, ...]
    oracle_top_k_sets: tuple[tuple[str, ...], ...]
    recall_at_k: float
    simple_regret_set: float
    interaction_recovery: Mapping[str, Any]
    planted_bundles_recovered: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.policy, str) or not self.policy:
            raise ValueError("policy must be a non-empty str")
        if not isinstance(self.family, str) or not self.family:
            raise ValueError("family must be a non-empty str")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise TypeError("seed must be a non-boolean int")
        if not isinstance(self.selected_set, tuple):
            raise TypeError("selected_set must be a tuple[str, ...]")
        if not isinstance(self.oracle_top_k_sets, tuple):
            raise TypeError(
                "oracle_top_k_sets must be a tuple[tuple[str, ...], ...]"
            )
        for entry in self.oracle_top_k_sets:
            if not isinstance(entry, tuple):
                raise TypeError(
                    "each oracle_top_k_sets entry must be a tuple[str, ...]"
                )
        if not (0.0 <= float(self.recall_at_k) <= 1.0):
            raise ValueError(
                "recall_at_k must lie in [0, 1]; got "
                f"{self.recall_at_k!r}"
            )
        # simple_regret_set is non-negative by definition (max_S Δ(S) is
        # at least Δ(selected_set) when selected_set is one of the
        # enumerated sets). Reject a negative value defensively.
        if float(self.simple_regret_set) < -1e-12:
            raise ValueError(
                "simple_regret_set must be non-negative; got "
                f"{self.simple_regret_set!r}"
            )
        if not isinstance(self.interaction_recovery, Mapping):
            raise TypeError("interaction_recovery must be a Mapping")
        missing_ir = set(INTERACTION_RECOVERY_KEYS) - set(
            self.interaction_recovery
        )
        if missing_ir:
            raise ValueError(
                "interaction_recovery is missing required keys: "
                f"{sorted(missing_ir)}"
            )
        if not isinstance(self.planted_bundles_recovered, Mapping):
            raise TypeError("planted_bundles_recovered must be a Mapping")
        missing_pbr = set(PLANTED_BUNDLES_RECOVERED_KEYS) - set(
            self.planted_bundles_recovered
        )
        if missing_pbr:
            raise ValueError(
                "planted_bundles_recovered is missing required keys: "
                f"{sorted(missing_pbr)}"
            )
        object.__setattr__(
            self,
            "interaction_recovery",
            MappingProxyType(dict(self.interaction_recovery)),
        )
        object.__setattr__(
            self,
            "planted_bundles_recovered",
            MappingProxyType(dict(self.planted_bundles_recovered)),
        )


__all__ = [
    "INTERACTION_RECOVERY_KEYS",
    "OracleReceipt",
    "PLANTED_BUNDLES_RECOVERED_KEYS",
]
