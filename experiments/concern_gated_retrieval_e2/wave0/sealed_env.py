"""Sealed environment interface for the Concern-Gated Retrieval Wave 0 build.

This module is the *only* legal channel between a Wave 0 policy (retrieval,
ranking, concern update) and the evaluator's private ground truth. It exposes:

- ``EpisodeSpec`` — the full evaluator-side episode. It holds role labels,
  future utility, and an answer key. Policy code MUST NOT read those fields.
- ``EpisodeContext`` — the policy-visible view returned by
  ``SealedEnvironment.observe``. It contains only context nodes, care anchors,
  a candidate budget, and candidate node ids; it does not carry role labels,
  utility, or the answer key.
- ``RetrievalChoice`` — the decision the policy submits to the environment.
- ``SealedOutcome`` — the realized reward and post-decision receipt the
  environment returns from ``SealedEnvironment.evaluate``.
- ``SealedEnvironment`` — the sealed environment. ``observe`` returns the
  policy view; ``evaluate`` returns the outcome and may be called at most once
  per episode. Second calls raise ``SealedEvaluationError``.
- ``IntegrityAudit`` — a static AST walker that flags any policy callable
  that dereferences ``EpisodeSpec.role``, ``EpisodeSpec.utility``, or
  ``EpisodeSpec._answer_key``.

Wave 0 scope. This module is calibration and family scaffolding + wrong-prior
initialization. It does NOT model learned memory geometry, concern recovery,
semantic meaning, or selfhood. See
``docs/concern_gated_retrieval_research_program.md`` for the claim ladder.
"""

from __future__ import annotations

import ast
import inspect
from dataclasses import dataclass, field
from textwrap import dedent
from types import MappingProxyType
from typing import Callable, Final, Literal, Mapping


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class SealedEvaluationError(RuntimeError):
    """Raised when the sealed environment contract is violated at runtime.

    Includes: a second ``evaluate`` call on the same episode, an evaluation
    submitted before ``observe`` was called, and a calibration-mode environment
    being asked to hold a confirmatory-family episode.
    """


class LeakageError(AssertionError):
    """Raised when static or runtime analysis detects an anti-leakage breach.

    The Wave 0 anti-leakage contract in
    ``experiments/concern_gated_retrieval_e2/wave0/PREREGISTRATION.md`` §4.1
    enumerates the evaluator-only fields; ``IntegrityAudit`` uses
    ``LeakageError`` to flag any policy callable that dereferences the sealed
    subset (``role``, ``utility``, ``_answer_key``).
    """


# ---------------------------------------------------------------------------
# Enumerations expressed as ``Literal`` type aliases
# ---------------------------------------------------------------------------


TemplateFamilySplit = Literal["calibration", "confirmatory"]
ProceduralFamily = Literal[
    "delayed_commitments", "maintenance_fault", "resource_constrained"
]
SealedMode = Literal["calibration", "confirmatory"]


_ALLOWED_SPLITS: Final[frozenset[str]] = frozenset({"calibration", "confirmatory"})
_ALLOWED_FAMILIES: Final[frozenset[str]] = frozenset(
    {"delayed_commitments", "maintenance_fault", "resource_constrained"}
)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EpisodeSpec:
    """Full evaluator-side episode. **NEVER pass this to policy code.**

    The evaluator constructs an ``EpisodeSpec`` and immediately wraps it in a
    ``SealedEnvironment``. Only the sealed environment's public methods
    (``observe`` and ``evaluate``) are exposed to policy code. The three
    sealed fields ``role``, ``utility``, and ``_answer_key`` are enumerated in
    PREREGISTRATION.md §4.1 as evaluator-only; ``IntegrityAudit`` uses their
    names as the forbidden AST attribute set.
    """

    episode_id: str
    template_family_split: TemplateFamilySplit
    family: ProceduralFamily
    seed: int
    context_nodes: tuple[str, ...]
    care_anchors: Mapping[str, float]
    candidate_nodes: tuple[str, ...]
    budget: int
    # ------------------------------------------------------------------
    # Sealed evaluator-only fields — accessing any of these from policy
    # code is a Wave 0 anti-leakage breach.
    # ------------------------------------------------------------------
    role: Mapping[str, str] = field(default_factory=dict)
    utility: Mapping[str, float] = field(default_factory=dict)
    _answer_key: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.template_family_split not in _ALLOWED_SPLITS:
            raise ValueError(
                "template_family_split must be one of "
                f"{sorted(_ALLOWED_SPLITS)}; got {self.template_family_split!r}"
            )
        if self.family not in _ALLOWED_FAMILIES:
            raise ValueError(
                "family must be one of "
                f"{sorted(_ALLOWED_FAMILIES)}; got {self.family!r}"
            )
        if self.budget < 0:
            raise ValueError("budget must be non-negative")
        # Freeze the sealed mappings behind read-only proxies. This is a
        # last-ditch defence against accidental mutation and does not
        # substitute for the anti-leakage guard; nothing here prevents a
        # policy that has been (illegally) handed an EpisodeSpec from
        # reading these fields.
        object.__setattr__(self, "care_anchors", MappingProxyType(dict(self.care_anchors)))
        object.__setattr__(self, "role", MappingProxyType(dict(self.role)))
        object.__setattr__(self, "utility", MappingProxyType(dict(self.utility)))


@dataclass(frozen=True)
class EpisodeContext:
    """Policy-visible view returned by ``SealedEnvironment.observe``.

    The context carries ``template_family_split`` because downstream code
    paths and receipts must be able to verify (and refuse) confirmatory rows
    in a calibration pipeline. It does **not** carry role labels, utility, or
    the answer key.
    """

    episode_id: str
    template_family_split: TemplateFamilySplit
    family: ProceduralFamily
    seed: int
    context_nodes: tuple[str, ...]
    care_anchors: Mapping[str, float]
    candidate_nodes: tuple[str, ...]
    budget: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "care_anchors", MappingProxyType(dict(self.care_anchors)))


@dataclass(frozen=True)
class RetrievalChoice:
    """A retrieval decision submitted to the sealed environment.

    ``selected`` is the tuple of node ids the policy has chosen to load into
    active representation. ``wall_actions`` is the number of side-effect
    actions the policy took while making the decision (probes, updates, or
    external calls) and is passed through to the outcome receipt so
    matched-budget audits can compare policies at equal wall cost.
    """

    selected: tuple[str, ...]
    wall_actions: int = 0

    def __post_init__(self) -> None:
        if self.wall_actions < 0:
            raise ValueError("wall_actions must be non-negative")
        if len(set(self.selected)) != len(self.selected):
            raise ValueError("RetrievalChoice.selected must contain unique node ids")


@dataclass(frozen=True)
class SealedOutcome:
    """Post-decision receipt returned by ``SealedEnvironment.evaluate``.

    Only these four values plus the template-family-split tag are exposed to
    policy code. Every other evaluator-side quantity (per-node role, per-node
    utility, the answer key, oracle-concern arms) stays inside the sealed
    environment.
    """

    realized_reward: float
    constraint_preserved: bool
    misretrieval_cost: float
    wall_actions: int
    template_family_split: TemplateFamilySplit


# ---------------------------------------------------------------------------
# SealedEnvironment
# ---------------------------------------------------------------------------


class SealedEnvironment:
    """Single-shot sealed environment for one Wave 0 episode.

    The constructor holds the full :class:`EpisodeSpec`, including role
    labels, utility, and the answer key. It exposes only:

    * :meth:`observe` — returns an :class:`EpisodeContext` view stripped of
      every evaluator-only field. May be called any number of times; the
      view is stateless.
    * :meth:`evaluate` — scores a :class:`RetrievalChoice` against the
      sealed answer key and utility, returns a :class:`SealedOutcome`, and
      then refuses further evaluations. The single-shot rule is a fatal
      Wave 0 integrity gate: a policy that could probe the sealed reward
      more than once could implicitly regress the evaluator.

    ``mode`` selects the runtime family-split guard. In ``"calibration"``
    mode the environment refuses to hold an episode whose
    ``template_family_split`` is ``"confirmatory"``; that guard is what
    keeps confirmatory rows out of calibration code paths.
    """

    def __init__(
        self,
        episode: EpisodeSpec,
        *,
        mode: SealedMode = "calibration",
    ) -> None:
        if mode not in _ALLOWED_SPLITS:
            raise ValueError(
                f"mode must be one of {sorted(_ALLOWED_SPLITS)}; got {mode!r}"
            )
        if mode == "calibration" and episode.template_family_split == "confirmatory":
            raise SealedEvaluationError(
                "SealedEnvironment(mode='calibration') refuses to hold a "
                "confirmatory-family episode; see PREREGISTRATION.md §4."
            )
        if mode == "confirmatory" and episode.template_family_split == "calibration":
            raise SealedEvaluationError(
                "SealedEnvironment(mode='confirmatory') refuses to hold a "
                "calibration-family episode; see PREREGISTRATION.md §4."
            )
        self._episode: EpisodeSpec = episode
        self._mode: SealedMode = mode
        self._observed: bool = False
        self._evaluated: bool = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def mode(self) -> SealedMode:
        return self._mode

    @property
    def evaluated(self) -> bool:
        return self._evaluated

    def observe(self, seed: int | None = None) -> EpisodeContext:
        """Return the policy-visible view of the episode.

        The ``seed`` argument overrides the episode's construction seed for
        policy-side randomization (so calibration policies can log
        propensities against a stated seed); it never influences the sealed
        outcome computation. The returned context contains only context
        nodes, care anchors, budget, and candidate ids.
        """

        self._observed = True
        effective_seed = self._episode.seed if seed is None else int(seed)
        return EpisodeContext(
            episode_id=self._episode.episode_id,
            template_family_split=self._episode.template_family_split,
            family=self._episode.family,
            seed=effective_seed,
            context_nodes=self._episode.context_nodes,
            care_anchors=dict(self._episode.care_anchors),
            candidate_nodes=self._episode.candidate_nodes,
            budget=self._episode.budget,
        )

    def evaluate(self, choice: RetrievalChoice) -> SealedOutcome:
        """Score a retrieval decision. May be called **at most once**.

        A second call raises :class:`SealedEvaluationError`. Calling
        ``evaluate`` before ``observe`` is also a contract violation (a
        policy has no legitimate way to construct a choice without having
        first seen the candidate set). The returned :class:`SealedOutcome`
        contains only the realized reward, a boolean constraint flag, the
        misretrieval cost, the wall-action count, and the template-family
        split; every evaluator-only field is dropped.
        """

        if self._evaluated:
            raise SealedEvaluationError(
                "SealedEnvironment.evaluate() may only be called once per "
                "episode; a second call is a Wave 0 anti-leakage breach."
            )
        if not self._observed:
            raise SealedEvaluationError(
                "SealedEnvironment.evaluate() called before observe(); "
                "policies must obtain the sealed context first."
            )
        self._evaluated = True
        return self._score(choice)

    # ------------------------------------------------------------------
    # Internal scoring
    # ------------------------------------------------------------------

    def _score(self, choice: RetrievalChoice) -> SealedOutcome:
        answer_set = frozenset(self._episode._answer_key)
        candidate_set = frozenset(self._episode.candidate_nodes)
        selected_set = frozenset(choice.selected)

        unknown = selected_set - candidate_set
        if unknown:
            raise SealedEvaluationError(
                "RetrievalChoice references nodes outside the observed "
                f"candidate set: {sorted(unknown)}"
            )
        if len(choice.selected) > self._episode.budget:
            raise SealedEvaluationError(
                "RetrievalChoice exceeds the budget declared by the episode."
            )

        hit_reward = sum(
            float(self._episode.utility.get(node, 0.0))
            for node in selected_set & answer_set
        )
        miss_penalty = sum(
            max(float(self._episode.utility.get(node, 0.0)), 0.0) * 0.25
            for node in selected_set - answer_set
        )
        realized_reward = max(-1.0, min(1.0, hit_reward - miss_penalty))
        constraint_preserved = bool(answer_set) and answer_set.issubset(selected_set)
        misretrieval_cost = float(len(selected_set - answer_set))

        return SealedOutcome(
            realized_reward=float(realized_reward),
            constraint_preserved=constraint_preserved,
            misretrieval_cost=misretrieval_cost,
            wall_actions=int(choice.wall_actions),
            template_family_split=self._episode.template_family_split,
        )


# ---------------------------------------------------------------------------
# IntegrityAudit
# ---------------------------------------------------------------------------


class IntegrityAudit:
    """Static AST audit for policy callables.

    ``IntegrityAudit.assert_clean(policy)`` parses the source of ``policy``
    (and, when :meth:`assert_clean` is called with ``recurse=True``, of the
    callables it dispatches to whose source is available to
    :func:`inspect.getsource`) and raises :class:`LeakageError` on any
    :class:`ast.Attribute` node whose attribute name is in
    :attr:`FORBIDDEN_ATTRS`.

    The forbidden set is deliberately narrow — ``role``, ``utility``,
    ``_answer_key`` — because those are the sealed :class:`EpisodeSpec`
    fields called out by the Wave 0 preregistration §4.1. The audit is
    conservative: any attribute access with one of those names is flagged,
    regardless of the receiver's static type. This over-triggers on
    unrelated same-named attributes but never under-triggers on the sealed
    fields, which is the correct direction for an integrity gate.

    The audit is a static check only. It does not replace the runtime
    single-shot ``evaluate`` guard, the calibration/confirmatory split
    guard, or the future runtime ``PolicyView`` wrapper described in
    PREREGISTRATION.md §4.3.
    """

    FORBIDDEN_ATTRS: Final[frozenset[str]] = frozenset(
        {"role", "utility", "_answer_key"}
    )

    @staticmethod
    def assert_clean(policy: Callable[..., object], *, recurse: bool = False) -> None:
        """Raise :class:`LeakageError` if ``policy`` dereferences a sealed field.

        ``recurse`` walks nested ``def``/``lambda`` bodies inside the same
        source unit; it does not follow calls into other modules because
        those bodies live in other source units and are audited separately
        by their own callers.
        """

        source = IntegrityAudit._get_source(policy)
        tree = ast.parse(source)
        offenders: list[tuple[str, int]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in IntegrityAudit.FORBIDDEN_ATTRS:
                offenders.append((node.attr, getattr(node, "lineno", -1)))
            if not recurse and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                # ast.walk will still descend, so this branch is only a
                # hook for future extensions; currently we audit the whole
                # source unit unconditionally.
                continue
        if offenders:
            attrs = ", ".join(f"{name} (line {line})" for name, line in offenders)
            raise LeakageError(
                "policy dereferences sealed EpisodeSpec attribute(s): "
                f"{attrs}. See wave0/PREREGISTRATION.md §4.1."
            )

    @staticmethod
    def _get_source(policy: Callable[..., object]) -> str:
        try:
            raw = inspect.getsource(policy)
        except (OSError, TypeError) as exc:
            raise LeakageError(
                "IntegrityAudit.assert_clean requires access to the "
                "callable's source via inspect.getsource; got "
                f"{type(exc).__name__}: {exc}"
            ) from exc
        return dedent(raw)


__all__ = [
    "EpisodeContext",
    "EpisodeSpec",
    "IntegrityAudit",
    "LeakageError",
    "ProceduralFamily",
    "RetrievalChoice",
    "SealedEnvironment",
    "SealedEvaluationError",
    "SealedMode",
    "SealedOutcome",
    "TemplateFamilySplit",
]
