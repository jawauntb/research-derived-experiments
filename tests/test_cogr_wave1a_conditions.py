"""Wave 1a condition-registry regression tests.

Every test here is scaffolding scope: the tests verify that the six
registered conditions (``FROZEN_WRONG``, ``ONLINE_IPS``, ``ONLINE_DR``,
``ORACLE_CEILING``, ``SHUFFLED``, ``WRONG_AGENT``) instantiate cleanly,
carry the promotion-eligibility flag the Wave 1a preregistration §4 table
declares, and are refused / admitted by ``promotion_admit_condition`` in
the shape the sweep runner will consume. No experiment logic is exercised.
"""

from __future__ import annotations

import pytest

from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
)
from experiments.concern_gated_retrieval_e2.wave0.families.delayed_commitments import (
    generate_episode,
)
from experiments.concern_gated_retrieval_e2.wave1a.conditions import (
    CONDITIONS,
    Condition,
    FROZEN_WRONG,
    ONLINE_DR,
    ONLINE_IPS,
    ORACLE_CEILING,
    PromotionRefused,
    SHUFFLED,
    WRONG_AGENT,
    condition_by_name,
    promotable_conditions,
    promotion_admit_condition,
)


def _one_confirmatory_episode():
    """Return one confirmatory-family EpisodeSpec for the registry tests."""
    return generate_episode(seed=200_000, bucket=TemplateBucket.CONFIRMATION)


def test_registry_contains_the_six_declared_conditions():
    """Every preregistered condition is registered exactly once."""
    expected = {
        FROZEN_WRONG,
        ONLINE_IPS,
        ONLINE_DR,
        ORACLE_CEILING,
        SHUFFLED,
        WRONG_AGENT,
    }
    assert set(CONDITIONS.keys()) == expected
    assert len(CONDITIONS) == 6
    for name, condition in CONDITIONS.items():
        assert isinstance(condition, Condition)
        assert condition.name == name


def test_five_promotable_and_one_ceiling():
    """The oracle is the sole non-promotable condition; all others promote."""
    promotable = promotable_conditions()
    assert len(promotable) == 5
    promotable_names = {c.name for c in promotable}
    assert promotable_names == {
        FROZEN_WRONG,
        ONLINE_IPS,
        ONLINE_DR,
        SHUFFLED,
        WRONG_AGENT,
    }
    assert CONDITIONS[ORACLE_CEILING].promotion_eligible is False


def test_update_rule_tags_match_the_preregistration():
    """Only the two on-line-learned variants carry an update-rule tag."""
    assert CONDITIONS[FROZEN_WRONG].update_rule is None
    assert CONDITIONS[ONLINE_IPS].update_rule == "ips"
    assert CONDITIONS[ONLINE_DR].update_rule == "dr"
    assert CONDITIONS[ORACLE_CEILING].update_rule is None
    assert CONDITIONS[SHUFFLED].update_rule is None
    assert CONDITIONS[WRONG_AGENT].update_rule is None


def test_condition_by_name_round_trips():
    """``condition_by_name`` returns the registered dataclass by name."""
    for name, condition in CONDITIONS.items():
        assert condition_by_name(name) is condition


def test_each_condition_factory_produces_a_valid_prior():
    """Every condition's factory produces a non-negative numeric prior on candidates."""
    episode = _one_confirmatory_episode()
    candidate_set = set(episode.candidate_nodes)
    for name, condition in CONDITIONS.items():
        prior = condition.initial_concern_factory(episode)
        assert isinstance(prior, dict) or hasattr(prior, "items"), name
        for anchor, weight in dict(prior).items():
            assert isinstance(anchor, str) and anchor, name
            assert anchor in candidate_set, (name, anchor)
            assert weight > 0.0, (name, anchor, weight)


def test_promotion_admit_condition_refuses_oracle():
    """The oracle is the sole condition refused by the promotion harness."""
    oracle = CONDITIONS[ORACLE_CEILING]
    with pytest.raises(PromotionRefused, match="oracle_ceiling"):
        promotion_admit_condition(oracle)


def test_promotion_admit_condition_admits_the_other_five():
    """The five promotable conditions round-trip through the harness."""
    for name in (FROZEN_WRONG, ONLINE_IPS, ONLINE_DR, SHUFFLED, WRONG_AGENT):
        condition = CONDITIONS[name]
        assert promotion_admit_condition(condition) is condition
