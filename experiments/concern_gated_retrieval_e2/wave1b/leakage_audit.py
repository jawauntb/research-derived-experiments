"""Wave 1b statistical leakage-audit primitives (§7 required design, G9).

The Wave 1b preregistration (``experiments/concern_gated_retrieval_e2/
wave1b/PREREGISTRATION.md`` §10) requires two statistical controls on
every permitted-graph feature the learned-geometry axis uses:

1. **Label permutation** — under a random permutation of each episode's
   sealed load-bearing identity across candidate positions, the learned
   graph must NOT place the load-bearing node in the top-K of a
   context-restart :func:`personalized_pagerank` diffusion above chance
   (default ``p < 0.01`` under a one-sided permutation test with the
   ``(n_ge + 1) / (N + 1)`` correction). A label-blind learner shows a
   permutation p-value indistinguishable from the null: it never saw the
   sealed label, so it cannot preferentially route mass toward it.
2. **Randomized generator** — regenerate the same-family episodes with a
   different generator seed offset (identical surface schema, disjoint
   node ids and disjoint sealed answer keys). Re-run the label
   permutation audit on the fresh batch. A learner that only reads
   permitted co-occurrence / temporal-lag / embedding features must pass
   the audit on EVERY generator offset, because none of the offsets
   handed it the sealed key.

Either audit firing is a NON-COMPENSATORY KILL of the Wave 1b L1
representation-contribution claim (``PROMOTION_CONTRACT_L1.md`` G9). The
audit is the statistical companion of the static
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.IntegrityAudit`
AST walker: static clean is necessary but not sufficient because a
learner can still launder answer information through legitimate-looking
co-occurrence surface features. The audit exposes that leak.

Evaluator-only
--------------

Every helper in this module dereferences the sealed
:attr:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeSpec._answer_key`
in its body. Any policy callable whose source imports :func:`audit_label_permutation`
or :func:`audit_randomized_generator` inherits the flagged attribute
reference and fails
:meth:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.IntegrityAudit.assert_clean`.
That refusal is exactly the Wave 1b anti-leakage contract:
statistical-audit code MUST NOT be reachable from any policy code path.

Public interface
----------------

* :func:`audit_label_permutation` — signature
  ``(learn_fn, history, n_permutations=100) -> AuditVerdict``. Reads
  ``history`` as a sequence of sealed :class:`EpisodeSpec` instances
  (evaluator side), converts them to an :class:`EpisodeHistory` visible
  view, and calls ``learn_fn`` on the visible view exactly once. The
  learn_fn signature is ``Callable[[EpisodeHistory], WeightedGraph]``;
  it is the callable the wave1b crossed runner uses to build the
  ``LEARNED`` geometry axis. The permutation baseline is a per-episode
  uniform draw over that episode's ``candidate_nodes``.
* :func:`audit_randomized_generator` — signature
  ``(learn_fn, family, seeds) -> AuditVerdict``. ``family`` is the family
  generator callable (e.g.
  :func:`experiments.concern_gated_retrieval_e2.wave1b.families.delayed_commitments_v2.generate_episode`)
  with signature ``(seed: int, bucket: TemplateBucket) -> EpisodeSpec``.
  The audit iterates over ``generator_offsets``, regenerates episodes at
  ``seed + offset`` for each seed, and runs the label-permutation audit
  on the fresh batch. Overall p-value is the MINIMUM (i.e. worst) across
  offsets; overall observed statistic is the maximum observed hit rate.
* :class:`LeakageError` — RuntimeError subclass raised for API misuse
  (non-``EpisodeSpec`` history, non-``WeightedGraph`` return from
  ``learn_fn``, out-of-range parameters). Distinct from
  :class:`experiments.concern_gated_retrieval_e2.wave0.sealed_env.LeakageError`
  (an AssertionError used by the static AST audit); this one is the
  runtime noncompensatory KILL signal downstream callers may re-raise on
  :attr:`AuditVerdict.passed = False`.
* :class:`AuditVerdict` — immutable receipt with ``audit``, ``passed``,
  ``observed_stat``, ``null_mean``, ``null_std``, ``z_score``,
  ``p_value``, ``tolerance``, ``n_samples``, ``n_permutations``,
  ``reason``.

Determinism
-----------

Both audit functions are byte-deterministic given identical inputs and
identical ``seed`` / ``audit_seed``. The permutation RNG is scoped by
``"cogr-e2-wave1b::{audit_name}::{seed}"``. The generator-offset walk
in :func:`audit_randomized_generator` iterates in the caller-provided
tuple order and reuses the same audit seed for each offset (with a
sub-offset stamp so different offsets get uncorrelated permutation
draws). Deterministic tie-breaking on PPR ranking uses ``(-score,
node_id)`` so equal scores never let RNG order into the top-K set.

Reuse boundary
--------------

Imports frozen Wave 0 primitives
(:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeSpec`,
:class:`~experiments.concern_gated_retrieval_e2.wave0.template_split.TemplateBucket`)
and the pilot's
:class:`~experiments.concern_gated_retrieval.graph.WeightedGraph` /
:func:`~experiments.concern_gated_retrieval.graph.personalized_pagerank`.
Consumes Wave 1b's
:class:`~experiments.concern_gated_retrieval_e2.wave1b.learned_geometry.EpisodeHistory`
+ :class:`~experiments.concern_gated_retrieval_e2.wave1b.learned_geometry.HistoryEpisode`
to build the visible view that ``learn_fn`` sees. Never edits any
imported module.
"""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass
from typing import Callable, Final, Sequence

from experiments.concern_gated_retrieval.graph import (
    WeightedGraph,
    personalized_pagerank,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import EpisodeSpec
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
)
from experiments.concern_gated_retrieval_e2.wave1b.learned_geometry import (
    EpisodeHistory,
    HistoryEpisode,
)


# --------------------------------------------------------------------------- #
# Errors                                                                      #
# --------------------------------------------------------------------------- #


class LeakageError(RuntimeError):
    """Statistical-leakage-audit runtime signal.

    Raised by the audit functions for **API misuse** (non-``EpisodeSpec``
    history entries, non-``WeightedGraph`` learner return, out-of-range
    parameters). Downstream callers may also raise this from
    :func:`raise_if_leaked` when an :class:`AuditVerdict` reports
    ``passed=False`` and the Wave 1b promotion contract demands a KILL.

    Distinct from
    :class:`experiments.concern_gated_retrieval_e2.wave0.sealed_env.LeakageError`
    (which is an ``AssertionError`` used by the static AST audit at
    :meth:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.IntegrityAudit.assert_clean`
    boundary). This one is a ``RuntimeError`` because the statistical
    audit fires at execution time, not at import / definition time.
    """


# --------------------------------------------------------------------------- #
# Constants                                                                   #
# --------------------------------------------------------------------------- #


AUDIT_LABEL_PERMUTATION: Final[str] = "label_permutation"
AUDIT_RANDOMIZED_GENERATOR: Final[str] = "randomized_generator"

#: Default retrieval budget used by the audit's top-K PPR cut. Wave 1b's
#: promotion contract fixes ``k = 3``
#: (``PROMOTION_CONTRACT_L1.md`` "Frozen constants"); the audit inherits
#: that constant so its "top-K" and the L1 gate's Recall@k operate on
#: the same set cardinality.
DEFAULT_TOP_K: Final[int] = 3

#: Default one-sided permutation p-value tolerance. Wave 1b PREREG §10
#: pins the bar at ``p < 0.01``, so ``passed`` is ``True`` iff
#: ``p_value >= tolerance``.
DEFAULT_TOLERANCE: Final[float] = 0.01

#: Default PPR damping. Matches
#: :func:`~experiments.concern_gated_retrieval.graph.personalized_pagerank`'s
#: own default so the audit does not silently drift from the retrieval
#: primitive it is auditing.
DEFAULT_ALPHA: Final[float] = 0.2

#: Default permutation count. The wave1b task brief pins
#: ``n_permutations=100``; kept as a constant so the audit's downstream
#: p-value granularity is uniform across cells and legible in the
#: PROVENANCE receipt.
DEFAULT_N_PERMUTATIONS: Final[int] = 100

#: Default generator offsets swept by :func:`audit_randomized_generator`.
#: Every offset stays inside the wave1b calibration seed range
#: ``[100_000, 100_999]`` when combined with the default 40-seed
#: calibration fixture ``range(100_000, 100_040)`` used by the wave1b
#: learner tests, so callers can pass unadjusted seeds and expect the
#: audit to run without a seed-window violation.
DEFAULT_GENERATOR_OFFSETS: Final[tuple[int, ...]] = (0, 200)


# --------------------------------------------------------------------------- #
# AuditVerdict                                                                #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class AuditVerdict:
    """Result receipt from a single leakage-audit call.

    Attributes
    ----------
    audit:
        The name of the audit — one of :data:`AUDIT_LABEL_PERMUTATION`
        or :data:`AUDIT_RANDOMIZED_GENERATOR`.
    passed:
        ``True`` iff ``p_value >= tolerance`` (no evidence of leakage
        beyond the preregistered false-positive floor). Wave 1b's
        promotion contract treats ``False`` as a noncompensatory KILL.
    observed_stat:
        The empirical top-K PPR hit rate at the sealed load-bearing
        node, averaged across the episodes that had a valid restart set
        (non-empty ``context_nodes`` inside the learned graph) and a
        non-empty sealed ``_answer_key``. For
        :data:`AUDIT_RANDOMIZED_GENERATOR` this is the MAXIMUM hit rate
        across the swept generator offsets.
    null_mean, null_std:
        Mean and (Bessel-corrected) standard deviation of the
        per-episode uniform-permutation null hit rate distribution.
    z_score:
        ``(observed_stat - null_mean) / max(null_std, 1e-9)``. Denominator
        floor keeps the receipt finite when the null is degenerate on a
        tiny fixture.
    p_value:
        One-sided permutation p-value ``(n_ge + 1) / (n_permutations
        + 1)`` where ``n_ge`` counts null draws with hit rate ``>=
        observed_stat``. The ``+1`` smoothing is the standard
        permutation-test correction and gives a nonzero p-value even
        when every null draw is strictly below the observed rate. For
        :data:`AUDIT_RANDOMIZED_GENERATOR` this is the MINIMUM (worst)
        p-value across the swept offsets.
    tolerance:
        The p-value threshold below which the audit fires. Default
        :data:`DEFAULT_TOLERANCE`. Recorded on the verdict so a
        downstream receipt can prove which threshold ran.
    n_samples:
        Number of episodes that contributed to ``observed_stat``.
        Episodes with empty context, empty answer key, or an empty
        candidate set are silently excluded (they cannot inform the
        audit). For :data:`AUDIT_RANDOMIZED_GENERATOR` this is the
        aggregate across offsets.
    n_permutations:
        The permutation count that produced ``null_mean`` / ``null_std``.
    reason:
        One-line human-readable summary that the wave1b run receipts
        copy into their PROVENANCE row.
    """

    audit: str
    passed: bool
    observed_stat: float
    null_mean: float
    null_std: float
    z_score: float
    p_value: float
    tolerance: float
    n_samples: int
    n_permutations: int
    reason: str


# --------------------------------------------------------------------------- #
# Internal helpers                                                            #
# --------------------------------------------------------------------------- #


def _visible_history_from_sealed(
    episodes: Sequence[EpisodeSpec],
) -> EpisodeHistory:
    """Build the policy-visible ``EpisodeHistory`` view from sealed specs.

    The audit is evaluator-side. It reads sealed :class:`EpisodeSpec`
    instances so it can dereference ``_answer_key`` for scoring, but the
    ``learn_fn`` it hands the history to sees only the visible
    :class:`EpisodeHistory` (no ``role``, no ``utility``, no
    ``_answer_key``). Any misuse — e.g. a caller passing raw
    :class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeContext`
    values that lack the sealed fields — is caught here with
    :class:`LeakageError` rather than silently returning a vacuous audit.
    """
    if not isinstance(episodes, Sequence) or isinstance(episodes, (str, bytes)):
        raise LeakageError(
            "audit history must be a Sequence[EpisodeSpec]; got "
            f"{type(episodes).__name__}"
        )
    records: list[HistoryEpisode] = []
    for ep in episodes:
        if not isinstance(ep, EpisodeSpec):
            raise LeakageError(
                "leakage audit requires sealed EpisodeSpec instances; got "
                f"{type(ep).__name__} — the audit dereferences "
                "``ep._answer_key`` which is only available on sealed "
                "EpisodeSpec, not on the policy-visible EpisodeContext."
            )
        records.append(
            HistoryEpisode(
                episode_id=ep.episode_id,
                family=ep.family,
                seed=ep.seed,
                context_nodes=tuple(ep.context_nodes),
                candidate_nodes=tuple(ep.candidate_nodes),
                care_anchors=dict(ep.care_anchors),
            )
        )
    return EpisodeHistory(episodes=tuple(records))


def _episode_top_k(
    graph: WeightedGraph,
    episode: EpisodeSpec,
    *,
    top_k: int,
    alpha: float,
) -> frozenset[str] | None:
    """Return the top-K PPR-scored subset of ``episode.candidate_nodes``.

    Deterministic tie-breaking is ``(-score, node_id)`` so equal-scored
    candidates carry the same top-K assignment across runs. Returns
    ``None`` if the episode has no restart-eligible context node in the
    graph (in which case the audit cannot form a PPR probe and the
    episode is silently excluded from the audit statistic).
    """
    context_in_graph = [
        n for n in episode.context_nodes if n in graph.adjacency
    ]
    if not context_in_graph:
        return None
    restart = {n: 1.0 / len(context_in_graph) for n in context_in_graph}
    result = personalized_pagerank(graph, restart, alpha=alpha)
    scored = [
        (n, float(result.scores.get(n, 0.0))) for n in episode.candidate_nodes
    ]
    scored.sort(key=lambda item: (-item[1], item[0]))
    return frozenset(n for n, _ in scored[:top_k])


def _score_batch(
    graph: WeightedGraph,
    episodes: Sequence[EpisodeSpec],
    *,
    top_k: int,
    alpha: float,
) -> tuple[
    float,
    list[tuple[tuple[str, ...], frozenset[str]]],
]:
    """Return ``(observed_hit_rate, per_episode_records)``.

    Each per-episode record is ``(candidate_nodes, top_k_set)`` — the
    ordered tuple of candidate ids the episode exposes and the top-K
    subset the learned graph places on them. The record set is what the
    permutation null draws from: for each null trial and each record we
    pick one candidate uniformly at random and score a hit iff that
    candidate lives in ``top_k_set``. The sealed answer key is
    dereferenced here (evaluator-only line) so the record set carries
    the label-blind information the null needs.
    """
    hits: list[float] = []
    records: list[tuple[tuple[str, ...], frozenset[str]]] = []
    for ep in episodes:
        answer_key = ep._answer_key  # evaluator-only sealed access
        if not answer_key:
            continue
        top_k_set = _episode_top_k(graph, ep, top_k=top_k, alpha=alpha)
        if top_k_set is None:
            continue
        candidates = tuple(ep.candidate_nodes)
        if not candidates:
            continue
        lb = answer_key[0]
        hits.append(1.0 if lb in top_k_set else 0.0)
        records.append((candidates, top_k_set))
    if not hits:
        return 0.0, []
    return sum(hits) / len(hits), records


def _permutation_null_rates(
    records: Sequence[tuple[tuple[str, ...], frozenset[str]]],
    *,
    n_permutations: int,
    seed_str: str,
) -> list[float]:
    """Draw ``n_permutations`` null hit rates by uniform per-episode label draws.

    The RNG is seeded from ``seed_str`` so a caller who passes the same
    string sees byte-identical null draws; the string is composed
    upstream so different audits ({:data:`AUDIT_LABEL_PERMUTATION`,
    :data:`AUDIT_RANDOMIZED_GENERATOR`}) draw uncorrelated null pools.
    """
    rng = random.Random(seed_str)
    rates: list[float] = []
    for _ in range(int(n_permutations)):
        hits: list[float] = []
        for candidates, top_k_set in records:
            if not candidates:
                continue
            fake_lb = candidates[rng.randrange(len(candidates))]
            hits.append(1.0 if fake_lb in top_k_set else 0.0)
        rates.append(sum(hits) / len(hits) if hits else 0.0)
    return rates


def _summarise(
    audit: str,
    observed_stat: float,
    null_rates: Sequence[float],
    *,
    tolerance: float,
    n_samples: int,
    reason_prefix: str = "",
) -> AuditVerdict:
    """Bundle observed / null statistics into an :class:`AuditVerdict`.

    Centralised so :func:`audit_label_permutation` and the per-offset
    aggregation in :func:`audit_randomized_generator` compute the p-value
    and z-score identically.
    """
    if not null_rates:
        return AuditVerdict(
            audit=audit,
            passed=True,
            observed_stat=float(observed_stat),
            null_mean=0.0,
            null_std=0.0,
            z_score=0.0,
            p_value=1.0,
            tolerance=float(tolerance),
            n_samples=int(n_samples),
            n_permutations=0,
            reason=(
                f"{reason_prefix}no permutation draws (n_permutations=0 or "
                "no valid audit records); audit vacuous"
            ),
        )
    null_mean = sum(null_rates) / len(null_rates)
    if len(null_rates) > 1:
        null_std = statistics.stdev(null_rates)
    else:
        null_std = 0.0
    z = (observed_stat - null_mean) / max(null_std, 1e-9)
    n_ge = sum(1 for r in null_rates if r >= observed_stat)
    p_value = (n_ge + 1) / (len(null_rates) + 1)
    passed = p_value >= float(tolerance)
    reason = (
        f"{reason_prefix}observed_hit_rate={observed_stat:.4f} vs "
        f"null_mean={null_mean:.4f} (std={null_std:.4f}); "
        f"p={p_value:.4f} (tolerance={tolerance:.4f}); "
        f"n_samples={n_samples}, n_permutations={len(null_rates)}"
    )
    return AuditVerdict(
        audit=audit,
        passed=bool(passed),
        observed_stat=float(observed_stat),
        null_mean=float(null_mean),
        null_std=float(null_std),
        z_score=float(z),
        p_value=float(p_value),
        tolerance=float(tolerance),
        n_samples=int(n_samples),
        n_permutations=int(len(null_rates)),
        reason=reason,
    )


# --------------------------------------------------------------------------- #
# audit_label_permutation                                                     #
# --------------------------------------------------------------------------- #


def audit_label_permutation(
    learn_fn: Callable[[EpisodeHistory], WeightedGraph],
    history: Sequence[EpisodeSpec],
    n_permutations: int = DEFAULT_N_PERMUTATIONS,
    *,
    top_k: int = DEFAULT_TOP_K,
    tolerance: float = DEFAULT_TOLERANCE,
    seed: int = 0,
    alpha: float = DEFAULT_ALPHA,
) -> AuditVerdict:
    """Return the label-permutation :class:`AuditVerdict` for ``learn_fn``.

    Permutes each episode's load-bearing identity uniformly across that
    episode's ``candidate_nodes`` and compares the true-label top-K PPR
    hit rate against the null distribution. A label-blind learner sits
    at ``p_value ~ null-mean fraction`` (no evidence of leakage). A
    learner that quietly reads the sealed answer key — for example by
    embedding it into a permitted co-occurrence feature — shows up as a
    large-positive z-score and a p-value below ``tolerance``.

    Parameters
    ----------
    learn_fn:
        Callable of shape ``(EpisodeHistory) -> WeightedGraph``. The
        audit calls it exactly once, on the visible-view history built
        from ``history``.
    history:
        Sequence of sealed :class:`EpisodeSpec` instances. Passing
        anything else (raw ``EpisodeContext``, a bare mapping, ...)
        raises :class:`LeakageError` — the audit needs the sealed
        ``_answer_key`` to compute the observed statistic.
    n_permutations:
        Number of null trials. Default :data:`DEFAULT_N_PERMUTATIONS`.
    top_k:
        PPR top-K cut. Default :data:`DEFAULT_TOP_K` (matches the L1
        promotion contract's ``k = 3`` retrieval budget).
    tolerance:
        One-sided p-value threshold. Default :data:`DEFAULT_TOLERANCE`
        (``0.01`` per PREREGISTRATION.md §10).
    seed:
        RNG salt for the permutation draws; two calls with the same
        arguments are byte-identical.
    alpha:
        PPR damping parameter forwarded to
        :func:`~experiments.concern_gated_retrieval.graph.personalized_pagerank`.
    """
    if not callable(learn_fn):
        raise LeakageError("learn_fn must be callable")
    if not isinstance(n_permutations, int) or isinstance(n_permutations, bool):
        raise LeakageError("n_permutations must be a non-boolean int")
    if n_permutations < 1:
        raise LeakageError("n_permutations must be >= 1")
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise LeakageError("top_k must be a non-boolean int >= 1")
    if not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance):
        raise LeakageError("tolerance must be a finite float in [0, 1]")
    if not (0.0 <= float(tolerance) <= 1.0):
        raise LeakageError("tolerance must lie in [0, 1]")
    if not isinstance(alpha, (int, float)) or not math.isfinite(alpha):
        raise LeakageError("alpha must be a finite float in (0, 1]")
    if not (0.0 < float(alpha) <= 1.0):
        raise LeakageError("alpha must lie in (0, 1]")

    visible = _visible_history_from_sealed(history)
    graph = learn_fn(visible)
    if not isinstance(graph, WeightedGraph):
        raise LeakageError(
            "learn_fn must return a WeightedGraph; got "
            f"{type(graph).__name__}"
        )

    # Sentinel dereference — ``_answer_key`` is a member of
    # :attr:`IntegrityAudit.FORBIDDEN_ATTRS`. Its explicit appearance in
    # this function body pins :meth:`IntegrityAudit.assert_clean` to
    # refuse any policy that copies this body wholesale, matching the
    # wave1b convention (see ``oracle_regret.compute_oracle_topk_sets``).
    if history:
        _sealed_answer_probe: tuple[str, ...] = history[0]._answer_key
        del _sealed_answer_probe

    observed, records = _score_batch(
        graph, history, top_k=top_k, alpha=alpha,
    )
    null_rates = _permutation_null_rates(
        records,
        n_permutations=n_permutations,
        seed_str=f"cogr-e2-wave1b::{AUDIT_LABEL_PERMUTATION}::{seed}",
    )
    return _summarise(
        AUDIT_LABEL_PERMUTATION,
        observed,
        null_rates,
        tolerance=tolerance,
        n_samples=len(records),
    )


# --------------------------------------------------------------------------- #
# audit_randomized_generator                                                  #
# --------------------------------------------------------------------------- #


def audit_randomized_generator(
    learn_fn: Callable[[EpisodeHistory], WeightedGraph],
    family: Callable[..., EpisodeSpec],
    seeds: Sequence[int],
    *,
    bucket: TemplateBucket = TemplateBucket.CALIBRATION,
    generator_offsets: Sequence[int] = DEFAULT_GENERATOR_OFFSETS,
    n_permutations: int = DEFAULT_N_PERMUTATIONS,
    top_k: int = DEFAULT_TOP_K,
    tolerance: float = DEFAULT_TOLERANCE,
    audit_seed: int = 0,
    alpha: float = DEFAULT_ALPHA,
) -> AuditVerdict:
    """Return the randomized-generator :class:`AuditVerdict` for ``learn_fn``.

    Regenerates the same-family episodes under each generator offset in
    ``generator_offsets`` and runs the label-permutation test on each
    regenerated batch independently. The aggregate verdict passes iff
    the WORST (minimum) p-value across offsets still lies above
    ``tolerance``. Reports the MAXIMUM observed hit rate as
    ``observed_stat`` so the reason string surfaces the worst offset
    plainly.

    The two generators produce disjoint node ids (node names include
    the seed) and disjoint sealed answer keys. If ``learn_fn`` truly
    reads only permitted co-occurrence / temporal / embedding features,
    both regenerated batches must pass the label-permutation test — the
    learner had no way to see the sealed key in either.

    Parameters
    ----------
    learn_fn:
        Callable of shape ``(EpisodeHistory) -> WeightedGraph``.
    family:
        Generator callable of shape ``(seed: int, bucket: TemplateBucket)
        -> EpisodeSpec``. Compatible with every Wave 1b family module's
        ``generate_episode`` entry point (extra optional kwargs such as
        ``holdout`` are ignored — the audit calls the generator with
        only the two required positional-or-keyword arguments).
    seeds:
        Base seed sequence. Must be non-empty and every entry must be a
        non-boolean int. The audit shifts each seed by every offset in
        ``generator_offsets``; the family generator is responsible for
        validating the resulting seed against its bucket window.
    bucket:
        :class:`TemplateBucket` value passed through to ``family``.
        Default :attr:`TemplateBucket.CALIBRATION`; callers exercising
        the audit against confirmatory rows pass
        :attr:`TemplateBucket.CONFIRMATION`.
    generator_offsets:
        Sequence of seed-space offsets to sweep. Default
        :data:`DEFAULT_GENERATOR_OFFSETS` (``(0, 200)``) — the two
        offsets together fit inside the 1000-seed calibration window
        for the standard 40-seed fixtures. Callers may pass a larger
        sweep; the audit runs every offset and aggregates.
    n_permutations, top_k, tolerance, alpha:
        Forwarded to :func:`audit_label_permutation` for each offset.
    audit_seed:
        RNG salt. Each offset draws its permutation null from
        ``audit_seed + offset`` so different offsets stay uncorrelated.
    """
    if not callable(learn_fn):
        raise LeakageError("learn_fn must be callable")
    if not callable(family):
        raise LeakageError("family must be callable")
    if not isinstance(seeds, Sequence) or isinstance(seeds, (str, bytes)):
        raise LeakageError(
            "seeds must be a Sequence[int]; got "
            f"{type(seeds).__name__}"
        )
    if not seeds:
        raise LeakageError("seeds must be non-empty")
    for s in seeds:
        if not isinstance(s, int) or isinstance(s, bool):
            raise LeakageError(
                "seeds entries must be non-boolean ints; got "
                f"{type(s).__name__}"
            )
    if not isinstance(bucket, TemplateBucket):
        raise LeakageError(
            "bucket must be a TemplateBucket instance; got "
            f"{type(bucket).__name__}"
        )
    if (
        not isinstance(generator_offsets, Sequence)
        or isinstance(generator_offsets, (str, bytes))
    ):
        raise LeakageError(
            "generator_offsets must be a Sequence[int]; got "
            f"{type(generator_offsets).__name__}"
        )
    if not generator_offsets:
        raise LeakageError("generator_offsets must be non-empty")
    for o in generator_offsets:
        if not isinstance(o, int) or isinstance(o, bool):
            raise LeakageError(
                "generator_offsets entries must be non-boolean ints"
            )

    per_offset: list[tuple[int, float, list[float], int]] = []
    for offset in generator_offsets:
        batch: list[EpisodeSpec] = []
        for base_seed in seeds:
            shifted = int(base_seed) + int(offset)
            episode = family(seed=shifted, bucket=bucket)
            if not isinstance(episode, EpisodeSpec):
                raise LeakageError(
                    "family(seed=..., bucket=...) must return an "
                    f"EpisodeSpec; got {type(episode).__name__} at "
                    f"offset={offset}, seed={shifted}"
                )
            batch.append(episode)

        # Sentinel dereference — mirrors the pattern in
        # :func:`audit_label_permutation` and pins
        # :meth:`IntegrityAudit.assert_clean` to refuse a policy body
        # copied wholesale from here. ``_answer_key`` is a member of
        # :attr:`IntegrityAudit.FORBIDDEN_ATTRS`.
        if batch:
            _sealed_answer_probe: tuple[str, ...] = batch[0]._answer_key
            del _sealed_answer_probe

        visible = _visible_history_from_sealed(batch)
        graph = learn_fn(visible)
        if not isinstance(graph, WeightedGraph):
            raise LeakageError(
                "learn_fn must return a WeightedGraph; got "
                f"{type(graph).__name__} at offset={offset}"
            )
        observed, records = _score_batch(
            graph, batch, top_k=top_k, alpha=alpha,
        )
        null_rates = _permutation_null_rates(
            records,
            n_permutations=n_permutations,
            seed_str=(
                f"cogr-e2-wave1b::{AUDIT_RANDOMIZED_GENERATOR}::"
                f"{audit_seed}::{offset}"
            ),
        )
        per_offset.append((offset, observed, null_rates, len(records)))

    # Aggregate across offsets: worst-case p-value, max observed rate.
    verdicts_per_offset: list[tuple[int, AuditVerdict]] = []
    for offset, observed, null_rates, n_records in per_offset:
        verdicts_per_offset.append(
            (
                offset,
                _summarise(
                    AUDIT_RANDOMIZED_GENERATOR,
                    observed,
                    null_rates,
                    tolerance=tolerance,
                    n_samples=n_records,
                    reason_prefix=f"[offset={offset}] ",
                ),
            )
        )

    if not verdicts_per_offset:
        # generator_offsets is guaranteed non-empty above, but keep the
        # branch so a future callable that returns zero verdicts fails
        # loudly rather than silently passing.
        raise LeakageError(
            "audit_randomized_generator produced no per-offset verdicts"
        )

    worst_offset, worst_verdict = min(
        verdicts_per_offset,
        key=lambda item: (item[1].p_value, -item[1].observed_stat, item[0]),
    )
    best_observed = max(v.observed_stat for _, v in verdicts_per_offset)
    total_samples = sum(v.n_samples for _, v in verdicts_per_offset)
    passed = all(v.passed for _, v in verdicts_per_offset)
    reason = (
        f"worst offset={worst_offset}: "
        f"observed_max={best_observed:.4f}; "
        f"p_min={worst_verdict.p_value:.4f} "
        f"(tolerance={tolerance:.4f}); "
        f"offsets_swept={[o for o, _ in verdicts_per_offset]}; "
        f"per_offset_p={[round(v.p_value, 4) for _, v in verdicts_per_offset]}; "
        f"n_samples={total_samples}"
    )
    return AuditVerdict(
        audit=AUDIT_RANDOMIZED_GENERATOR,
        passed=bool(passed),
        observed_stat=float(best_observed),
        null_mean=float(worst_verdict.null_mean),
        null_std=float(worst_verdict.null_std),
        z_score=float(worst_verdict.z_score),
        p_value=float(worst_verdict.p_value),
        tolerance=float(tolerance),
        n_samples=int(total_samples),
        n_permutations=int(worst_verdict.n_permutations),
        reason=reason,
    )


# --------------------------------------------------------------------------- #
# Optional convenience: KILL on a failing verdict                             #
# --------------------------------------------------------------------------- #


def raise_if_leaked(verdict: AuditVerdict) -> None:
    """Raise :class:`LeakageError` iff ``verdict.passed`` is ``False``.

    A convenience for callers who want the noncompensatory KILL to
    manifest as a raised exception rather than an inspected boolean.
    Never raises on ``passed=True``. Kept out of the audit-function
    bodies so the audit itself always returns a receipt for logging /
    PROVENANCE regardless of whether the caller wants to abort.
    """
    if not isinstance(verdict, AuditVerdict):
        raise LeakageError(
            "raise_if_leaked requires an AuditVerdict; got "
            f"{type(verdict).__name__}"
        )
    if verdict.passed:
        return
    raise LeakageError(
        f"leakage audit {verdict.audit!r} FAILED: {verdict.reason}"
    )


__all__ = [
    "AUDIT_LABEL_PERMUTATION",
    "AUDIT_RANDOMIZED_GENERATOR",
    "AuditVerdict",
    "DEFAULT_ALPHA",
    "DEFAULT_GENERATOR_OFFSETS",
    "DEFAULT_N_PERMUTATIONS",
    "DEFAULT_TOLERANCE",
    "DEFAULT_TOP_K",
    "LeakageError",
    "audit_label_permutation",
    "audit_randomized_generator",
    "raise_if_leaked",
]
