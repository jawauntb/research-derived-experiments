"""Wave 0 baseline slate for the Concern-Gated Retrieval E2 program.

Every entry in the Wave 0 preregistration §7 baseline slate is exposed here
as a ``rank(context: EpisodeContext, budget: int) -> tuple[str, ...]``
callable. Baselines are pure functions of the sealed
:class:`EpisodeContext` view. None of them dereference the sealed
``role``, ``utility``, or ``_answer_key`` fields on
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeSpec`;
each rank callable is passed through
:meth:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.IntegrityAudit.assert_clean`
at module import so a leaky baseline fails CI at collection time rather
than at experiment time.

The slate contains:

* structural floors — :func:`no_retrieval`, :func:`random_rank`,
  :func:`freq_only`;
* single-source diffusion — :func:`context_only_ppr`,
  :func:`care_only_ppr`;
* two-source fusion — :func:`additive_ppr`,
  :func:`multiplicative_ppr` (the **candidate mechanism** for Wave 1);
* semantic reference — :func:`embedding_similarity`;
* matched-capacity learned reference — :func:`learned_one_stage`
  (small MLP with frozen deterministic init; Wave 1 will fine-tune on
  calibration rows only);
* information-matched second signals — :func:`info_matched_value`,
  :func:`info_matched_priority`, :func:`info_matched_recency`;
* concern-specificity control — :func:`wrong_agent_concern`;
* diagnostic ceiling (never promotable) — :func:`oracle_ceiling`.

The candidate mechanism for Wave 1 is :func:`multiplicative_ppr`
(rarity-corrected Hadamard product of context and concern PPR). Every
Wave 1 promotion contest must beat both the best matched-budget
alternative from this slate and, individually, the
:func:`learned_one_stage` MLP scored at matched compute. The
:func:`oracle_ceiling` baseline is flagged CEILING-ONLY via
:data:`oracle_ceiling.is_ceiling_only` and is refused by
:func:`promotion_admit`.

Wave 0 boundary. This module is calibration and family scaffolding plus
wrong-prior initialization. It does not describe learned memory geometry,
concern recovery, semantic meaning, or selfhood. Those questions belong
to Wave 1 and later; see
``docs/concern_gated_retrieval_research_program.md``.

Reuse boundary. Imports :class:`WeightedGraph` and
:func:`personalized_pagerank` from the frozen L0 pilot at
``experiments/concern_gated_retrieval/graph.py`` and does not fork them.
Imports :func:`rarity_scores` from
:mod:`experiments.concern_gated_retrieval_e2.wave0.graph_learn` and does
not fork it either. Sentence-transformer semantic embeddings are used
when available at import time; when unavailable, a deterministic
per-token hash pseudo-embedding is used instead and the substitution is
recorded in :data:`EMBEDDING_PROVENANCE`.
"""

from __future__ import annotations

import hashlib
import math
import random
from functools import lru_cache
from typing import Any, Callable, Final, Mapping, Sequence

from experiments.concern_gated_retrieval.graph import (
    WeightedGraph,
    personalized_pagerank,
)
from experiments.concern_gated_retrieval_e2.wave0.graph_learn import (
    FAMILY_NAMES as _WAVE0_FAMILY_NAMES,
    build_withheld_graph,
    rarity_scores,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeContext,
    IntegrityAudit,
    LeakageError,
)


# ---------------------------------------------------------------------------
# Public types and markers
# ---------------------------------------------------------------------------


#: Uniform baseline signature. Every baseline in this module (except the
#: factory helpers) implements this exact signature.
RankFn = Callable[[EpisodeContext, int], tuple[str, ...]]


#: Attribute name a rank callable may set to opt out of promotion admission.
#: The Wave 0 promotion harness in :func:`promotion_admit` refuses to run
#: a baseline for which this attribute is truthy.
CEILING_MARKER: Final[str] = "is_ceiling_only"


#: Attribute name a rank callable may set to record its provenance for the
#: calibration receipt (e.g. embedding substitution used).
PROVENANCE_MARKER: Final[str] = "provenance"


# ---------------------------------------------------------------------------
# Candidate-mechanism capacity target
# ---------------------------------------------------------------------------


#: Wave 0's declared parameter-count target for the candidate mechanism
#: (``multiplicative_ppr``). ``multiplicative_ppr`` is an algorithmic
#: ranker with no learned weights; this constant fixes the matched-
#: capacity number the ``learned_one_stage`` MLP must sit within 5% of,
#: so a Wave 1 tie against that MLP cannot be dismissed as "we ran a
#: smaller net". The target is frozen at 128 — chosen so a modest
#: single-hidden-layer MLP over the eight per-candidate features listed
#: in :func:`_candidate_features` reaches it without ballooning compute
#: (see :data:`_MLP_HIDDEN`).
CANDIDATE_MECHANISM_PARAM_COUNT: Final[int] = 128


# Learned-one-stage MLP dimensions. ``in`` is the length of
# :func:`_candidate_features`; ``hidden`` is chosen so total parameter
# count sits within 5% of :data:`CANDIDATE_MECHANISM_PARAM_COUNT`.
_MLP_IN: Final[int] = 8
_MLP_HIDDEN: Final[int] = 13
_MLP_OUT: Final[int] = 1


def learned_one_stage_parameter_count() -> int:
    """Return the deterministic total parameter count of :func:`learned_one_stage`.

    The MLP is one hidden layer with bias on both layers:
    ``in * hidden + hidden + hidden * out + out``.
    """
    return _MLP_IN * _MLP_HIDDEN + _MLP_HIDDEN + _MLP_HIDDEN * _MLP_OUT + _MLP_OUT


# ---------------------------------------------------------------------------
# Deterministic helpers
# ---------------------------------------------------------------------------


def _episode_salt(context: EpisodeContext, purpose: str) -> str:
    """Return a deterministic per-episode / per-purpose salt string."""
    return (
        f"cogr-wave0-baseline::{purpose}::{context.family}::{context.seed}::"
        f"{context.episode_id}"
    )


def _tie_break_hash(salt: str, node: str) -> int:
    """Return a deterministic integer for tie-breaking rank orderings."""
    key = f"{salt}::{node}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big", signed=False)


def _rank_by_scores(
    scores: Mapping[str, float],
    context: EpisodeContext,
    budget: int,
    purpose: str,
) -> tuple[str, ...]:
    """Return the top-``budget`` candidates by score with a deterministic tie-break.

    Ties are broken by the SHA-256 hash of ``(purpose, family, seed, node)``
    so identical scores never leak candidate-position information into the
    ranking.
    """
    if budget < 0:
        raise ValueError("budget must be non-negative")
    salt = _episode_salt(context, purpose)
    cutoff = min(budget, len(context.candidate_nodes))
    ordered = sorted(
        context.candidate_nodes,
        key=lambda node: (-float(scores.get(node, 0.0)), _tie_break_hash(salt, node)),
    )
    return tuple(ordered[:cutoff])


def _local_graph(context: EpisodeContext) -> WeightedGraph:
    """Build a family-agnostic local graph from the sealed context view.

    The graph joins every context node to every candidate node with a
    base weight (1.0), and adds a light candidate-to-candidate clique
    (0.1) so a single-source PPR restart never leaves nodes with zero
    reachable mass. The construction is a pure function of the exposed
    ``context_nodes`` and ``candidate_nodes`` — evaluator-only fields
    are unreachable from this code path.
    """
    all_nodes = list(dict.fromkeys(list(context.context_nodes) + list(context.candidate_nodes)))
    edges: list[tuple[str, str, float]] = []
    ctx_nodes = tuple(context.context_nodes)
    cands = tuple(context.candidate_nodes)
    for ctx in ctx_nodes:
        for cand in cands:
            edges.append((ctx, cand, 1.0))
    for i in range(len(cands)):
        for j in range(i + 1, len(cands)):
            edges.append((cands[i], cands[j], 0.1))
    if not edges and all_nodes:
        # Degenerate context: keep the graph legal by pairing the first
        # node against itself would be a self-edge (unsupported); instead
        # add a tiny pairwise link between the first two nodes if we can.
        if len(all_nodes) >= 2:
            edges.append((all_nodes[0], all_nodes[1], 1.0))
    return WeightedGraph.from_edges(all_nodes, edges)


def _restart_from(nodes: Sequence[str], candidates: Sequence[str]) -> dict[str, float]:
    """Return a normalized restart distribution over ``nodes``.

    If ``nodes`` is empty, restart on the candidate set uniformly.
    ``personalized_pagerank`` rejects an all-zero restart, so this
    fallback keeps every baseline callable on degenerate contexts.
    """
    if not nodes:
        nodes = candidates
    if not nodes:
        return {}
    mass = 1.0 / len(nodes)
    restart: dict[str, float] = {}
    for node in nodes:
        restart[node] = restart.get(node, 0.0) + mass
    return restart


def _ppr_scores(
    graph: WeightedGraph,
    restart_nodes: Sequence[str],
    candidates: Sequence[str],
) -> dict[str, float]:
    """Run PPR on ``graph`` restarting from ``restart_nodes``, project to candidates."""
    restart = _restart_from(restart_nodes, candidates)
    # personalized_pagerank rejects unknown restart nodes.
    graph_nodes = set(graph.nodes)
    restart = {node: mass for node, mass in restart.items() if node in graph_nodes}
    if not restart:
        return {node: 0.0 for node in candidates}
    result = personalized_pagerank(graph, restart, alpha=0.2, tolerance=1e-9)
    return {node: float(result.scores.get(node, 0.0)) for node in candidates}


def _rarity_correct(scores: Mapping[str, float], rarity: Mapping[str, float]) -> dict[str, float]:
    """Apply a ``score / max(freq, eps) ** 0.25`` rarity correction."""
    eps = 1e-15
    exponent = 0.25
    corrected: dict[str, float] = {}
    for node, score in scores.items():
        r = float(rarity.get(node, 1.0))
        corrected[node] = float(score) / max(r, eps) ** (-exponent)
        # rarity is inverse-frequency: a higher rarity means "rarer",
        # so dividing by rarity ** -0.25 == multiplying by rarity ** 0.25
        # which upweights rare nodes.
    return corrected


# ---------------------------------------------------------------------------
# Rarity batch (uses graph_learn.rarity_scores as required)
# ---------------------------------------------------------------------------


#: Small fixed window of calibration seeds used to compute a rarity
#: batch per family. Kept intentionally short so module import stays
#: fast; the point of ``freq_only`` is only to serve as a chance floor,
#: not to compete with two-sided methods.
_RARITY_SEED_WINDOW: Final[tuple[int, ...]] = tuple(range(100_000, 100_010))


@lru_cache(maxsize=None)
def _rarity_batch_for_family(family: str) -> Mapping[str, float]:
    """Return per-node rarity for one family, computed via ``graph_learn.rarity_scores``.

    Uses the fixed withheld-graph batch across
    :data:`_RARITY_SEED_WINDOW`. Node ids from families whose candidate
    namespace does not match the withheld graph (e.g. ``maintenance_fault``,
    which uses its own ``mf::…`` prefix) will not appear in this batch;
    :func:`freq_only` falls back to a uniform score of ``1.0`` for those
    nodes, and its ranking is therefore ordering-independent — a pure
    chance floor for that family.
    """
    if family not in _WAVE0_FAMILY_NAMES:
        # Unknown family: return an empty batch. Every candidate then
        # falls back to the default uniform score.
        return {}
    # Family-specific size matches the family generators' declared sizes.
    if family == "delayed_commitments":
        size = 32
    elif family == "resource_constrained":
        size = 16
    else:
        # maintenance_fault: use a modest size for the rarity graph (its
        # generator does not use build_withheld_graph, so this rarity
        # table stays effectively empty for that family — that is the
        # documented degeneracy).
        size = 16
    graphs = tuple(
        build_withheld_graph(seed=s, size=size, family=family)
        for s in _RARITY_SEED_WINDOW
    )
    return dict(rarity_scores(iter(graphs)))


# ---------------------------------------------------------------------------
# Embedding provenance
# ---------------------------------------------------------------------------


try:  # pragma: no cover - import-time environment probe
    from sentence_transformers import SentenceTransformer  # type: ignore

    _EMBED_MODEL: Any = None
    try:
        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        _EMBEDDING_SOURCE = "sentence_transformers::all-MiniLM-L6-v2"
    except Exception:  # pragma: no cover - offline / weight fetch failure
        _EMBED_MODEL = None
        _EMBEDDING_SOURCE = "deterministic_pseudo_embedding_hash"
except Exception:  # pragma: no cover - package missing
    _EMBED_MODEL = None
    _EMBEDDING_SOURCE = "deterministic_pseudo_embedding_hash"


#: Provenance string recorded in the calibration receipt for the
#: embedding_similarity baseline. Either ``sentence_transformers::…`` if
#: a frozen sentence-transformer loaded at import time, or
#: ``deterministic_pseudo_embedding_hash`` when the transformer was
#: unavailable and Wave 0 fell back to a per-node SHA-256 pseudo-vector.
#: The substitution is intentional and logged; downstream calibration
#: analysis must record which source produced its rows.
EMBEDDING_PROVENANCE: Final[str] = _EMBEDDING_SOURCE


_PSEUDO_EMBED_DIM: Final[int] = 32


def _pseudo_embedding(text: str) -> tuple[float, ...]:
    """Deterministic per-token pseudo-embedding via SHA-256 chunks."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    # Extend by re-hashing to reach _PSEUDO_EMBED_DIM * 4 bytes.
    buf = bytearray()
    counter = 0
    while len(buf) < _PSEUDO_EMBED_DIM * 4:
        buf.extend(hashlib.sha256(digest + counter.to_bytes(4, "big")).digest())
        counter += 1
    vec: list[float] = []
    for i in range(_PSEUDO_EMBED_DIM):
        chunk = int.from_bytes(buf[i * 4 : i * 4 + 4], "big", signed=False)
        # Map to [-1, 1] deterministically.
        vec.append(chunk / (2**32 - 1) * 2.0 - 1.0)
    # L2-normalize so cosine similarity == dot product.
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return tuple(x / norm for x in vec)


def _embed_node(node: str) -> tuple[float, ...]:
    """Return the frozen embedding vector for a node id."""
    if _EMBED_MODEL is not None:  # pragma: no cover - runtime-only branch
        vec = _EMBED_MODEL.encode(node, normalize_embeddings=True)
        return tuple(float(x) for x in vec)
    return _pseudo_embedding(node)


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    denom = math.sqrt(na) * math.sqrt(nb)
    if denom <= 0:
        return 0.0
    return dot / denom


# ---------------------------------------------------------------------------
# The rank functions
# ---------------------------------------------------------------------------


def no_retrieval(context: EpisodeContext, budget: int) -> tuple[str, ...]:
    """Floor baseline: return an empty selection regardless of budget."""
    if budget < 0:
        raise ValueError("budget must be non-negative")
    return ()


def random_rank(context: EpisodeContext, budget: int) -> tuple[str, ...]:
    """Chance-floor baseline: deterministic per-episode shuffle."""
    if budget < 0:
        raise ValueError("budget must be non-negative")
    salt = _episode_salt(context, "random")
    rng = random.Random(salt)
    pool = list(context.candidate_nodes)
    rng.shuffle(pool)
    cutoff = min(budget, len(pool))
    return tuple(pool[:cutoff])


def freq_only(context: EpisodeContext, budget: int) -> tuple[str, ...]:
    """Rarity-inverse baseline via ``graph_learn.rarity_scores``.

    Nodes are ranked by their inverse-frequency score across the fixed
    withheld-graph rarity batch for ``context.family``. Higher scores
    (rarer nodes) are preferred. Candidates outside the withheld-graph
    namespace fall back to a uniform default; on such families the
    ranking is decided by the deterministic tie-break and behaves as a
    chance floor, which is the documented degenerate case.
    """
    rarity = _rarity_batch_for_family(context.family)
    scores = {node: float(rarity.get(node, 1.0)) for node in context.candidate_nodes}
    return _rank_by_scores(scores, context, budget, "freq_only")


def context_only_ppr(context: EpisodeContext, budget: int) -> tuple[str, ...]:
    """Personalized PageRank restarting from ``context.context_nodes``."""
    graph = _local_graph(context)
    scores = _ppr_scores(graph, tuple(context.context_nodes), tuple(context.candidate_nodes))
    return _rank_by_scores(scores, context, budget, "context_only_ppr")


def care_only_ppr(context: EpisodeContext, budget: int) -> tuple[str, ...]:
    """PPR restarting from concern anchors — no context signal."""
    graph = _local_graph(context)
    anchors = tuple(node for node, weight in context.care_anchors.items() if weight > 0)
    scores = _ppr_scores(graph, anchors, tuple(context.candidate_nodes))
    return _rank_by_scores(scores, context, budget, "care_only_ppr")


def additive_ppr(context: EpisodeContext, budget: int) -> tuple[str, ...]:
    """Additive fusion of context and concern PPR scores."""
    graph = _local_graph(context)
    ctx_scores = _ppr_scores(graph, tuple(context.context_nodes), tuple(context.candidate_nodes))
    anchors = tuple(node for node, weight in context.care_anchors.items() if weight > 0)
    care_scores = _ppr_scores(graph, anchors, tuple(context.candidate_nodes))
    scores = {
        node: float(ctx_scores.get(node, 0.0)) + float(care_scores.get(node, 0.0))
        for node in context.candidate_nodes
    }
    return _rank_by_scores(scores, context, budget, "additive_ppr")


def multiplicative_ppr(context: EpisodeContext, budget: int) -> tuple[str, ...]:
    """Rarity-corrected Hadamard product — Wave 0 candidate mechanism.

    Implements ``(r_ctx * r_care) * rarity ** 0.25`` on each candidate
    node. Rarity is drawn from the withheld-graph batch computed at
    import time via ``graph_learn.rarity_scores`` so the correction
    matches the frozen pilot's numerical semantics.

    This is the baseline Wave 1 promotion contests will center on. Wave 0
    does not claim it wins; Wave 0 records its variance and headroom so
    a Wave 1 loss to the additive fusion or the ``learned_one_stage`` MLP
    is adjudicable.
    """
    graph = _local_graph(context)
    ctx_scores = _ppr_scores(graph, tuple(context.context_nodes), tuple(context.candidate_nodes))
    anchors = tuple(node for node, weight in context.care_anchors.items() if weight > 0)
    care_scores = _ppr_scores(graph, anchors, tuple(context.candidate_nodes))
    rarity = _rarity_batch_for_family(context.family)
    scores: dict[str, float] = {}
    for node in context.candidate_nodes:
        product = float(ctx_scores.get(node, 0.0)) * float(care_scores.get(node, 0.0))
        r = float(rarity.get(node, 1.0))
        scores[node] = product * max(r, 1e-15) ** 0.25
    return _rank_by_scores(scores, context, budget, "multiplicative_ppr")


def embedding_similarity(context: EpisodeContext, budget: int) -> tuple[str, ...]:
    """Frozen semantic-similarity baseline.

    Ranks each candidate by mean cosine similarity to the context nodes.
    Uses the frozen ``all-MiniLM-L6-v2`` sentence-transformer when it
    loads at import time; otherwise falls back to a deterministic
    per-token SHA-256 pseudo-embedding. The substitution is recorded in
    :data:`EMBEDDING_PROVENANCE` and on the callable's ``provenance``
    attribute.
    """
    if not context.context_nodes:
        # No context to compare against — degenerate; use candidate-only
        # self-similarity, which after L2-normalization is 1.0 for every
        # candidate, so the tie-break decides.
        scores = {node: 1.0 for node in context.candidate_nodes}
        return _rank_by_scores(scores, context, budget, "embedding_similarity")
    ctx_vectors = tuple(_embed_node(node) for node in context.context_nodes)
    scores: dict[str, float] = {}
    for cand in context.candidate_nodes:
        cand_vec = _embed_node(cand)
        sims = tuple(_cosine(cand_vec, v) for v in ctx_vectors)
        scores[cand] = sum(sims) / max(len(sims), 1)
    return _rank_by_scores(scores, context, budget, "embedding_similarity")


# ---------------------------------------------------------------------------
# Learned one-stage MLP (matched-capacity reference)
# ---------------------------------------------------------------------------


def _candidate_features(
    context: EpisodeContext,
    node: str,
    ctx_ppr: Mapping[str, float],
    care_ppr: Mapping[str, float],
    rarity: Mapping[str, float],
) -> tuple[float, ...]:
    """Return the eight per-candidate features fed to :func:`learned_one_stage`.

    The features are policy-visible only: context-PPR score, care-PPR
    score, rarity, care-anchor weight, per-candidate degree (in the
    local graph), a context-adjacency flag, a self-hash tie-break float,
    and a constant bias term. None of them read sealed EpisodeSpec
    fields.
    """
    ctx_score = float(ctx_ppr.get(node, 0.0))
    care_score = float(care_ppr.get(node, 0.0))
    rarity_score = float(rarity.get(node, 1.0))
    care_weight = float(context.care_anchors.get(node, 0.0))
    degree = float(len(context.context_nodes))
    ctx_adj = 1.0 if node in context.context_nodes else 0.0
    tie_hash = (_tie_break_hash(_episode_salt(context, "learned_one_stage"), node) % 10_000) / 10_000.0
    bias = 1.0
    return (ctx_score, care_score, rarity_score, care_weight, degree, ctx_adj, tie_hash, bias)


def _init_mlp_weights() -> tuple[list[list[float]], list[float], list[float], float]:
    """Deterministic frozen initialization for the Wave 0 MLP.

    Wave 0's promise is calibration and scaffolding: the MLP has a
    frozen deterministic init (SHA-256-derived), and any future
    fine-tuning happens under a Wave 1 preregistration. The weights are
    laid out as:

    * ``w1`` : hidden x in
    * ``b1`` : hidden
    * ``w2`` : out x hidden
    * ``b2`` : out (scalar since out == 1)
    """
    rng = random.Random("cogr-wave0-baseline::learned_one_stage::frozen_init")
    w1 = [[rng.uniform(-0.5, 0.5) for _ in range(_MLP_IN)] for _ in range(_MLP_HIDDEN)]
    b1 = [rng.uniform(-0.1, 0.1) for _ in range(_MLP_HIDDEN)]
    w2 = [rng.uniform(-0.5, 0.5) for _ in range(_MLP_HIDDEN)]
    b2 = rng.uniform(-0.1, 0.1)
    return w1, b1, w2, b2


_MLP_W1, _MLP_B1, _MLP_W2, _MLP_B2 = _init_mlp_weights()


def _mlp_score(features: Sequence[float]) -> float:
    """Forward-pass the frozen MLP on a single feature vector."""
    hidden: list[float] = []
    for h in range(_MLP_HIDDEN):
        acc = _MLP_B1[h]
        row = _MLP_W1[h]
        for i in range(_MLP_IN):
            acc += row[i] * float(features[i])
        # Tanh keeps activations bounded so the ranking never explodes.
        hidden.append(math.tanh(acc))
    out = _MLP_B2
    for h in range(_MLP_HIDDEN):
        out += _MLP_W2[h] * hidden[h]
    return float(out)


def learned_one_stage(context: EpisodeContext, budget: int) -> tuple[str, ...]:
    """Frozen small MLP ranker; matched-capacity reference for Wave 1.

    Consumes eight policy-visible per-candidate features
    (:func:`_candidate_features`) and scores each candidate via a
    single-hidden-layer tanh MLP with deterministic init. Total
    parameter count is within 5% of
    :data:`CANDIDATE_MECHANISM_PARAM_COUNT`; see
    :func:`learned_one_stage_parameter_count`.

    Wave 0 leaves the weights frozen. Wave 1 will fine-tune on
    calibration rows only under a signed preregistration; the training
    interface is a Wave 1 object and is not exposed here.
    """
    graph = _local_graph(context)
    ctx_ppr = _ppr_scores(graph, tuple(context.context_nodes), tuple(context.candidate_nodes))
    anchors = tuple(node for node, weight in context.care_anchors.items() if weight > 0)
    care_ppr = _ppr_scores(graph, anchors, tuple(context.candidate_nodes))
    rarity = _rarity_batch_for_family(context.family)
    scores: dict[str, float] = {}
    for node in context.candidate_nodes:
        features = _candidate_features(context, node, ctx_ppr, care_ppr, rarity)
        scores[node] = _mlp_score(features)
    return _rank_by_scores(scores, context, budget, "learned_one_stage")


# ---------------------------------------------------------------------------
# Information-matched second-signal baselines
# ---------------------------------------------------------------------------


def _utility_probabilities_from_care(context: EpisodeContext) -> dict[str, float]:
    """Convert the wrong-prior care anchors into a policy-visible utility proxy.

    Wave 0's wrong-prior overweights alarms and suppresses the true
    load-bearing region. The ``info_matched_value`` baseline consumes
    that same signal — no sealed field — normalized into a probability
    over the candidate set. This is the "generic value / advantage"
    second signal the L1 gate must beat: if a matched-budget policy that
    only sees this proxy already picks the right candidates, the
    two-source retriever's gain vanishes.
    """
    raw = {
        node: max(float(context.care_anchors.get(node, 0.0)), 0.0)
        for node in context.candidate_nodes
    }
    total = sum(raw.values())
    if total <= 0:
        # Fallback: uniform over candidates.
        share = 1.0 / max(len(context.candidate_nodes), 1)
        return {node: share for node in context.candidate_nodes}
    return {node: value / total for node, value in raw.items()}


def info_matched_value(context: EpisodeContext, budget: int) -> tuple[str, ...]:
    """Generic value/advantage second-signal proxy.

    Ranks candidates by utility probabilities computed only from
    ``context.care_anchors``. Sealed ``utility`` is not consulted.
    """
    scores = _utility_probabilities_from_care(context)
    return _rank_by_scores(scores, context, budget, "info_matched_value")


def info_matched_priority(context: EpisodeContext, budget: int) -> tuple[str, ...]:
    """Task-priority second-signal proxy.

    Priority is defined as ``care_weight * ctx_ppr`` — the wrong prior
    focused on the currently reachable neighborhood. This is what a
    generic priority second-signal would look like in a calibration
    experiment without a separate learned priority signal; the L1 gate
    must beat this too.
    """
    graph = _local_graph(context)
    ctx_ppr = _ppr_scores(graph, tuple(context.context_nodes), tuple(context.candidate_nodes))
    scores: dict[str, float] = {}
    for node in context.candidate_nodes:
        care_weight = float(context.care_anchors.get(node, 0.0))
        scores[node] = care_weight * float(ctx_ppr.get(node, 0.0))
    return _rank_by_scores(scores, context, budget, "info_matched_priority")


def info_matched_recency(context: EpisodeContext, budget: int) -> tuple[str, ...]:
    """Recency-weighted second-signal proxy.

    Recency is defined as ``1 / (1 + distance_from_first_context_node)``
    across the candidate ordering — the calibration surface's proxy for
    "most recently seen". Deterministic in the candidate order the
    family generator emitted (which is fixed per template).
    """
    _episode_salt(context, "info_matched_recency")
    if not context.candidate_nodes:
        return ()
    scores: dict[str, float] = {}
    for i, node in enumerate(context.candidate_nodes):
        scores[node] = 1.0 / (1.0 + i)
    return _rank_by_scores(scores, context, budget, "info_matched_recency")


# ---------------------------------------------------------------------------
# Wrong-agent concern control
# ---------------------------------------------------------------------------


def _wrong_agent_permutation(context: EpisodeContext) -> dict[str, float]:
    """Return a wrong-agent concern map derived by permuting anchor weights.

    Weights over the candidate set are permuted using a deterministic
    per-episode PRNG. The load-bearing region's suppressed weight almost
    always moves off the true target, and an alarm-region weight almost
    always moves onto a different node. The permutation preserves the
    multiset of weights — this is the "same distribution, different
    agent" condition Wave 0's specificity gate requires.
    """
    salt = _episode_salt(context, "wrong_agent_concern")
    rng = random.Random(salt)
    cands = list(context.candidate_nodes)
    weights = [float(context.care_anchors.get(node, 0.0)) for node in cands]
    permuted_indices = list(range(len(cands)))
    rng.shuffle(permuted_indices)
    permuted: dict[str, float] = {}
    for i, node in enumerate(cands):
        permuted[node] = weights[permuted_indices[i]]
    return permuted


def wrong_agent_concern(context: EpisodeContext, budget: int) -> tuple[str, ...]:
    """Concern anchors reassigned to a different agent's profile.

    Applies :func:`_wrong_agent_permutation` to obtain a permuted
    concern map, then runs the same multiplicative-PPR fusion as the
    candidate mechanism against that wrong-agent concern. If the
    two-source retriever's benefit is real (agent-specific), this
    baseline must degrade against ``multiplicative_ppr`` in expectation
    over the calibration slate.
    """
    graph = _local_graph(context)
    ctx_scores = _ppr_scores(graph, tuple(context.context_nodes), tuple(context.candidate_nodes))
    wrong_care = _wrong_agent_permutation(context)
    care_anchors = tuple(node for node, weight in wrong_care.items() if weight > 0)
    care_scores = _ppr_scores(graph, care_anchors, tuple(context.candidate_nodes))
    rarity = _rarity_batch_for_family(context.family)
    scores: dict[str, float] = {}
    for node in context.candidate_nodes:
        product = float(ctx_scores.get(node, 0.0)) * float(care_scores.get(node, 0.0))
        r = float(rarity.get(node, 1.0))
        scores[node] = product * max(r, 1e-15) ** 0.25
    return _rank_by_scores(scores, context, budget, "wrong_agent_concern")


# ---------------------------------------------------------------------------
# Oracle ceiling (CEILING-ONLY, never promotable)
# ---------------------------------------------------------------------------


#: Module-level registry populated by the evaluator side before running
#: :func:`oracle_ceiling`. Keys are ``episode_id``; values are the
#: sealed answer key for that episode. Populating this registry is a
#: privileged evaluator operation; the sealed environment does not
#: expose this data to policy code.
_ORACLE_ANSWERS: dict[str, tuple[str, ...]] = {}


def register_oracle_answer(episode_id: str, answer_key: Sequence[str]) -> None:
    """Register the sealed answer key for one episode (evaluator-side).

    Only Wave 0 evaluator code (the calibration scorer) calls this. The
    registration lives outside the sealed environment so that
    :func:`oracle_ceiling`'s callable body never dereferences a sealed
    :class:`EpisodeSpec` field and therefore passes
    :meth:`IntegrityAudit.assert_clean` at import.
    """
    if not isinstance(episode_id, str) or not episode_id:
        raise ValueError("episode_id must be a non-empty string")
    _ORACLE_ANSWERS[episode_id] = tuple(answer_key)


def clear_oracle_answers() -> None:
    """Drop every registered oracle answer. Used by tests between rows."""
    _ORACLE_ANSWERS.clear()


def oracle_ceiling(context: EpisodeContext, budget: int) -> tuple[str, ...]:
    """Diagnostic ceiling: use pre-registered oracle answers.

    **CEILING-ONLY.** Refused by :func:`promotion_admit`; must never
    enter a Wave 1 promotion contest. The rank callable reads only the
    module-level oracle registry and the sealed context; it does not
    dereference any sealed ``role``, ``utility``, or ``_answer_key``
    field, so it passes :meth:`IntegrityAudit.assert_clean`. The oracle
    information is supplied out-of-band by evaluator code that calls
    :func:`register_oracle_answer` before evaluation.
    """
    answer = _ORACLE_ANSWERS.get(context.episode_id, ())
    ordered = [node for node in answer if node in context.candidate_nodes]
    if len(ordered) >= budget:
        return tuple(ordered[:budget])
    # Not enough oracle picks — pad with a deterministic tie-break over
    # the remaining candidates.
    remaining = [node for node in context.candidate_nodes if node not in ordered]
    salt = _episode_salt(context, "oracle_ceiling")
    remaining.sort(key=lambda node: _tie_break_hash(salt, node))
    padded = ordered + remaining
    cutoff = min(budget, len(padded))
    return tuple(padded[:cutoff])


# Flag the oracle as CEILING-ONLY. Setting this attribute is the sole
# affordance the Wave 0 promotion harness uses to refuse a baseline.
setattr(oracle_ceiling, CEILING_MARKER, True)


# ---------------------------------------------------------------------------
# Matched-budget wrapper
# ---------------------------------------------------------------------------


#: Static FLOP estimate for one ``multiplicative_ppr`` call on a
#: representative Wave 0 episode. Wave 0 uses a coarse count (one
#: multiply-add per PPR iteration per edge times two PPR runs plus the
#: rarity correction). Wave 1 will replace this with a measured cost;
#: the constant lives here so the ``match_budget`` wrapper has a
#: concrete number to enforce.
CANDIDATE_MECHANISM_FLOPS: Final[int] = 32_000


class BudgetExceeded(RuntimeError):
    """Raised by :func:`match_budget` when the wrapped baseline overruns.

    The wave-wide matched-compute rule is that Wave 1 confirmatory rows
    are scored at matched FLOPs between the ``learned_one_stage`` MLP
    and the candidate mechanism. This exception is the runtime signal
    that a Wave 0 measurement broke the matched-budget contract before
    it reached the calibration receipt.
    """


def _estimate_flops(baseline: Callable[..., Any], context: EpisodeContext) -> int:
    """Return the static FLOP estimate for one call to ``baseline``.

    Wave 0 uses a lookup table over baseline identity; the numbers are
    order-of-magnitude estimates suitable for enforcing matched compute
    against the candidate mechanism.
    """
    n_candidates = max(len(context.candidate_nodes), 1)
    if baseline is multiplicative_ppr:
        return CANDIDATE_MECHANISM_FLOPS
    if baseline is additive_ppr:
        return CANDIDATE_MECHANISM_FLOPS  # two PPR runs, one add
    if baseline is context_only_ppr or baseline is care_only_ppr:
        return CANDIDATE_MECHANISM_FLOPS // 2
    if baseline is learned_one_stage:
        # PPR feature extraction + MLP forward pass per candidate.
        return CANDIDATE_MECHANISM_FLOPS + n_candidates * (
            _MLP_IN * _MLP_HIDDEN + _MLP_HIDDEN * _MLP_OUT + _MLP_HIDDEN
        )
    if baseline is embedding_similarity:
        return n_candidates * _PSEUDO_EMBED_DIM * max(len(context.context_nodes), 1) * 2
    if baseline is wrong_agent_concern:
        return CANDIDATE_MECHANISM_FLOPS  # same shape as multiplicative_ppr
    if baseline in (info_matched_value, info_matched_priority, info_matched_recency):
        return n_candidates * 4
    if baseline is freq_only:
        return n_candidates * 2
    if baseline is random_rank:
        return n_candidates
    if baseline is no_retrieval:
        return 0
    if baseline is oracle_ceiling:
        return n_candidates
    # Unknown baseline — return a conservative upper bound so the wrapper
    # errs on the side of admitting nothing beyond its declared cost.
    return CANDIDATE_MECHANISM_FLOPS * 4


def match_budget(baseline: Callable[..., Any], target_flops: int) -> RankFn:
    """Return a ``rank(context, budget)`` wrapper that enforces matched FLOPs.

    The wrapper attaches:

    * ``reported_flops`` — the static FLOP estimate for one call;
    * ``target_flops`` — the ceiling passed by the caller;
    * ``wrapped`` — a reference to the original baseline.

    On each call the wrapper checks the reported FLOPs against
    ``target_flops`` and raises :class:`BudgetExceeded` if the estimate
    exceeds the target. This is the Wave 0 mechanism for guaranteeing
    that a Wave 1 comparison of :func:`learned_one_stage` against the
    candidate mechanism runs at matched compute. Wave 1 will replace the
    static estimate with a measured cost; the wrapper interface stays
    stable so callers do not need to change.
    """
    if target_flops <= 0:
        raise ValueError("target_flops must be positive")

    _wrapped_baseline = baseline
    _cap = target_flops

    class _MatchedBudgetRank:
        reported_flops = _estimate_flops
        target_flops = _cap
        wrapped = _wrapped_baseline

        def __call__(self, context: EpisodeContext, budget: int) -> tuple[str, ...]:
            reported = _estimate_flops(_wrapped_baseline, context)
            if reported > _cap:
                raise BudgetExceeded(
                    f"baseline {getattr(_wrapped_baseline, '__name__', _wrapped_baseline)!r} reported "
                    f"{reported} FLOPs but matched-budget target was {_cap}"
                )
            return _wrapped_baseline(context, budget)

    return _MatchedBudgetRank()


# ---------------------------------------------------------------------------
# Promotion harness
# ---------------------------------------------------------------------------


class PromotionRefused(RuntimeError):
    """Raised when the Wave 0 promotion harness refuses to admit a baseline.

    The only Wave 0 refusal is a ceiling-only baseline (``is_ceiling_only``
    truthy). Every other baseline is admitted; the actual promotion
    decision (whether it wins) happens in Wave 1.
    """


def promotion_admit(baseline: Callable[..., Any]) -> RankFn:
    """Return ``baseline`` if it is legal for a promotion contest; else raise.

    A ceiling baseline is refused. The refusal message is stable so
    calibration receipts can regex-match on it.
    """
    if getattr(baseline, CEILING_MARKER, False):
        raise PromotionRefused(
            f"baseline {getattr(baseline, '__name__', baseline)!r} is flagged "
            "CEILING-ONLY and cannot enter a Wave 0 / Wave 1 promotion contest"
        )
    return baseline  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Baseline registry
# ---------------------------------------------------------------------------


#: Canonical order of the Wave 0 baseline slate. Downstream calibration
#: receipts iterate this dict so per-baseline rows land in a stable
#: order. ``oracle_ceiling`` sits at the end and is admitted by name
#: only to the diagnostic-ceiling code path; :func:`promotion_admit`
#: refuses it.
BASELINES: Final[dict[str, RankFn]] = {
    "no_retrieval": no_retrieval,
    "random": random_rank,
    "freq_only": freq_only,
    "context_only_ppr": context_only_ppr,
    "care_only_ppr": care_only_ppr,
    "additive_ppr": additive_ppr,
    "multiplicative_ppr": multiplicative_ppr,
    "embedding_similarity": embedding_similarity,
    "learned_one_stage": learned_one_stage,
    "info_matched_value": info_matched_value,
    "info_matched_priority": info_matched_priority,
    "info_matched_recency": info_matched_recency,
    "wrong_agent_concern": wrong_agent_concern,
    "oracle_ceiling": oracle_ceiling,
}


#: The candidate mechanism the Wave 1 promotion contest centers on.
CANDIDATE_MECHANISM: Final[RankFn] = multiplicative_ppr


# ---------------------------------------------------------------------------
# Provenance tagging
# ---------------------------------------------------------------------------


setattr(embedding_similarity, PROVENANCE_MARKER, EMBEDDING_PROVENANCE)


# ---------------------------------------------------------------------------
# Import-time IntegrityAudit
# ---------------------------------------------------------------------------


def _audit_all_baselines_at_import() -> None:
    """Run :meth:`IntegrityAudit.assert_clean` on every rank callable.

    Raises :class:`LeakageError` at import time if a baseline
    dereferences ``role``, ``utility``, or ``_answer_key``. This is the
    CI-visible anti-leakage tripwire named by Wave 0 PREREGISTRATION.md
    §4.3(2).
    """
    for name, baseline in BASELINES.items():
        try:
            IntegrityAudit.assert_clean(baseline)
        except LeakageError as exc:  # pragma: no cover - defensive re-raise
            raise LeakageError(
                f"Wave 0 baseline {name!r} failed IntegrityAudit at import: {exc}"
            ) from exc


_audit_all_baselines_at_import()


__all__ = [
    "BASELINES",
    "BudgetExceeded",
    "CANDIDATE_MECHANISM",
    "CANDIDATE_MECHANISM_FLOPS",
    "CANDIDATE_MECHANISM_PARAM_COUNT",
    "CEILING_MARKER",
    "EMBEDDING_PROVENANCE",
    "PROVENANCE_MARKER",
    "PromotionRefused",
    "RankFn",
    "additive_ppr",
    "care_only_ppr",
    "clear_oracle_answers",
    "context_only_ppr",
    "embedding_similarity",
    "freq_only",
    "info_matched_priority",
    "info_matched_recency",
    "info_matched_value",
    "learned_one_stage",
    "learned_one_stage_parameter_count",
    "match_budget",
    "multiplicative_ppr",
    "no_retrieval",
    "oracle_ceiling",
    "promotion_admit",
    "random_rank",
    "register_oracle_answer",
    "wrong_agent_concern",
]
