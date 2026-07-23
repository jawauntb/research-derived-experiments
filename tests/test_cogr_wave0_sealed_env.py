"""Wave 0 sealed environment tests.

The four tests below are the anti-leakage regression suite named by the
Wave 0 preregistration §4.3 for the sealed-env module:

* ``test_evaluate_called_twice_raises`` — single-shot ``evaluate`` gate.
* ``test_observe_cannot_see_roles_utility_or_answer_key`` — the
  policy-visible ``EpisodeContext`` never carries a sealed field.
* ``test_integrity_audit_flags_a_bad_policy`` — the static AST audit
  raises ``LeakageError`` when a policy dereferences a sealed attribute.
* ``test_integrity_audit_passes_a_clean_policy`` — a clean policy
  passes the same audit.
"""

from __future__ import annotations

import pytest

from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeContext,
    EpisodeSpec,
    IntegrityAudit,
    LeakageError,
    RetrievalChoice,
    SealedEnvironment,
    SealedEvaluationError,
    SealedOutcome,
)


def _make_episode(*, split: str = "calibration") -> EpisodeSpec:
    return EpisodeSpec(
        episode_id="DC-C-01-seed-100000",
        template_family_split=split,  # ty: ignore[invalid-argument-type]  # noqa
        family="delayed_commitments",
        seed=100_000,
        context_nodes=("ctx_a", "ctx_b"),
        care_anchors={"anchor_alarm": 1.0, "anchor_commit": 0.05},
        candidate_nodes=("target_commit", "target_alarm", "distractor_1"),
        budget=2,
        role={
            "target_commit": "load_bearing",
            "target_alarm": "alarm",
            "distractor_1": "distractor",
        },
        utility={"target_commit": 0.8, "target_alarm": -0.1, "distractor_1": 0.0},
        _answer_key=("target_commit",),
    )


# ---------------------------------------------------------------------------
# (a) evaluate() twice raises
# ---------------------------------------------------------------------------


def test_evaluate_called_twice_raises() -> None:
    env = SealedEnvironment(_make_episode())
    env.observe(seed=100_000)
    outcome = env.evaluate(RetrievalChoice(selected=("target_commit",), wall_actions=1))

    assert isinstance(outcome, SealedOutcome)
    assert outcome.constraint_preserved is True
    assert outcome.realized_reward == pytest.approx(0.8)
    assert env.evaluated is True

    with pytest.raises(SealedEvaluationError, match="only be called once"):
        env.evaluate(RetrievalChoice(selected=("target_commit",), wall_actions=1))


# ---------------------------------------------------------------------------
# (b) observe() cannot see roles / utility / answer key
# ---------------------------------------------------------------------------


def test_observe_cannot_see_roles_utility_or_answer_key() -> None:
    episode = _make_episode()
    env = SealedEnvironment(episode)
    context = env.observe(seed=100_000)

    assert isinstance(context, EpisodeContext)

    # The policy-visible view exposes only these attribute names.
    exposed = {name for name in vars(context) if not name.startswith("__")}
    forbidden = {"role", "utility", "_answer_key"}
    assert exposed.isdisjoint(forbidden), (
        f"EpisodeContext leaks sealed field(s): {sorted(exposed & forbidden)}"
    )

    # And attribute access for those names raises AttributeError.
    for name in forbidden:
        with pytest.raises(AttributeError):
            getattr(context, name)


# ---------------------------------------------------------------------------
# (c) IntegrityAudit flags a bad policy
# ---------------------------------------------------------------------------


def _bad_policy(spec: EpisodeSpec) -> tuple[str, ...]:
    # This policy directly reads the sealed answer key. The static audit
    # must flag it before it is ever run against a live environment.
    key = spec._answer_key
    return tuple(key[:1])


def _bad_policy_via_role(spec: EpisodeSpec) -> str:
    return next(iter(spec.role.values()))


def _bad_policy_via_utility(spec: EpisodeSpec) -> float:
    return float(sum(spec.utility.values()))


def test_integrity_audit_flags_a_bad_policy() -> None:
    for bad in (_bad_policy, _bad_policy_via_role, _bad_policy_via_utility):
        with pytest.raises(LeakageError, match="sealed EpisodeSpec attribute"):
            IntegrityAudit.assert_clean(bad)


# ---------------------------------------------------------------------------
# (d) IntegrityAudit passes a clean policy
# ---------------------------------------------------------------------------


def _clean_policy(context: EpisodeContext) -> RetrievalChoice:
    # A clean policy sees only the sealed context. It selects the first
    # ``budget`` candidates and reports the number of side actions it took.
    budget = context.budget
    picks = context.candidate_nodes[:budget]
    return RetrievalChoice(selected=picks, wall_actions=len(picks))


def test_integrity_audit_passes_a_clean_policy() -> None:
    # Must not raise.
    IntegrityAudit.assert_clean(_clean_policy)

    # And the clean policy actually runs against a sealed environment
    # without touching evaluator-only state.
    env = SealedEnvironment(_make_episode())
    context = env.observe(seed=100_000)
    choice = _clean_policy(context)
    outcome = env.evaluate(choice)
    assert isinstance(outcome, SealedOutcome)
    assert outcome.wall_actions == len(choice.selected)
