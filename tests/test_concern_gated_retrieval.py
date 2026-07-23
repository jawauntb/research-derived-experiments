from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from experiments.concern_gated_retrieval.benchmark import (
    EpisodeRanking,
    ORACLE_CARE_WEIGHTS,
    _future_data,
    candidate_epiplexity,
    epiplexity_control_audit,
    evaluate_episodes,
    generate_episode,
    generate_episodes,
    learn_care_weights,
)
from experiments.concern_gated_retrieval import benchmark as benchmark_module
from experiments.concern_gated_retrieval.epiplexity import ReservoirEpiplexity
from experiments.concern_gated_retrieval.graph import (
    WeightedGraph,
    coincidence_scores,
    personalized_pagerank,
)
from experiments.concern_gated_retrieval.run_pilot import (
    DEFAULT_OUTPUT,
    numerical_validity_pass,
    write_summary,
)


def test_personalized_pagerank_is_normalized_and_satisfies_fixed_point() -> None:
    graph = WeightedGraph.from_edges(
        ("a", "b", "c"),
        (("a", "b", 2.0), ("b", "c", 1.0)),
    )

    result = personalized_pagerank(graph, {"a": 1.0})

    assert sum(result.scores.values()) == pytest.approx(1.0, abs=1e-12)
    assert result.l1_residual <= 1e-10
    assert result.scores["a"] > result.scores["c"]


def test_dangling_mass_returns_through_restart_and_alpha_one_is_limit() -> None:
    graph = WeightedGraph.from_edges(
        ("connected_a", "connected_b", "isolated"),
        (("connected_a", "connected_b", 1.0),),
    )

    dangling = personalized_pagerank(graph, {"isolated": 1.0}, alpha=0.2)
    restart_only = personalized_pagerank(
        graph,
        {"connected_a": 1.0, "isolated": 1.0},
        alpha=1.0,
    )

    assert dangling.scores == {
        "connected_a": 0.0,
        "connected_b": 0.0,
        "isolated": 1.0,
    }
    assert restart_only.scores == {
        "connected_a": 0.5,
        "connected_b": 0.0,
        "isolated": 0.5,
    }


def test_coincidence_score_applies_rarity_and_registered_limits() -> None:
    context = {"rare": 0.2, "common": 0.3, "zero_frequency": 0.01}
    care = {"rare": 0.3, "common": 0.2, "zero_frequency": 0.01}
    frequency = {"rare": 0.01, "common": 0.81, "zero_frequency": 0.0}

    corrected = coincidence_scores(
        context,
        care,
        frequency,
        tuple(context),
        rarity_exponent=0.5,
        epsilon=1e-4,
    )
    uncorrected = coincidence_scores(
        context,
        care,
        frequency,
        tuple(context),
        rarity_exponent=0.0,
        epsilon=1e-4,
    )

    assert corrected["rare"] == pytest.approx(0.6)
    assert corrected["common"] == pytest.approx(0.06 / 0.9)
    assert corrected["rare"] > corrected["common"]
    assert corrected["zero_frequency"] == pytest.approx(0.01)
    assert uncorrected == {
        "rare": pytest.approx(0.06),
        "common": pytest.approx(0.06),
        "zero_frequency": pytest.approx(0.0001),
    }


def test_concern_warp_preserves_support_and_increases_concern_edge() -> None:
    graph = WeightedGraph.from_edges(
        ("context", "care", "other"),
        (("context", "care", 1.0), ("context", "other", 1.0)),
    )

    warped = graph.concern_warped({"care": 2.0}, strength=0.5)

    assert set(warped.adjacency["context"]) == {"care", "other"}
    assert warped.adjacency["context"]["care"] > warped.adjacency["context"]["other"]


def test_epiplexity_prices_structure_not_constant_or_shuffled_noise() -> None:
    episode = generate_episode(17)
    by_role = {candidate.role: candidate for candidate in episode.candidates}

    structured = candidate_epiplexity(by_role["load_bearing"], episode.seed)
    constant = candidate_epiplexity(by_role["context_only"], episode.seed)
    noise = candidate_epiplexity(by_role["alarm"], episode.seed)

    assert constant == pytest.approx(0.0, abs=1e-12)
    assert structured > noise + 0.75


def test_shuffled_control_preserves_targets_but_breaks_input_alignment() -> None:
    episode = generate_episode(17)
    by_role = {candidate.role: candidate for candidate in episode.candidates}

    _, structured = _future_data(by_role["load_bearing"], episode.seed)
    _, shuffled = _future_data(by_role["alarm"], episode.seed)

    assert not np.array_equal(structured, shuffled)
    assert np.array_equal(
        np.sort(structured, axis=0),
        np.sort(shuffled, axis=0),
    )


def test_epiplexity_is_invariant_to_orthogonal_output_rotation() -> None:
    estimator = ReservoirEpiplexity(input_dimension=2, width=8, seed=3)
    phase = np.linspace(-1.0, 1.0, 80)
    inputs = np.column_stack((phase, phase**2))
    targets = np.column_stack((phase, 0.5 * phase**2))
    rotation = np.array([[0.0, -1.0], [1.0, 0.0]])

    original = estimator.score(inputs, targets)
    rotated = estimator.score(inputs, targets @ rotation)

    assert original == pytest.approx(rotated, rel=1e-10, abs=1e-10)


def test_two_sided_retrieval_beats_one_sided_controls() -> None:
    episodes = generate_episodes(range(20), regimes=("base",))

    result = evaluate_episodes(episodes, ORACLE_CARE_WEIGHTS)

    assert result.hit_at_1["coincidence"] > result.hit_at_1["context"]
    assert result.hit_at_1["coincidence"] > result.hit_at_1["care"]
    assert result.verifier_precision >= 0.9
    assert result.verifier_recall >= 0.9


def test_online_care_updates_only_selected_candidate_utility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    episode = generate_episode(0)
    alarm = next(
        candidate for candidate in episode.candidates if candidate.role == "alarm"
    )

    def choose_alarm(*_args, **_kwargs):
        return {
            "coincidence": EpisodeRanking(
                policy="coincidence",
                ranked_nodes=(alarm.node,),
                top_role=alarm.role,
                load_bearing_rank=None,
                ppr_residual=0.0,
            )
        }

    monkeypatch.setattr(benchmark_module, "rank_episode", choose_alarm)

    learned = learn_care_weights((episode,), learning_rate=0.2)

    assert learned.learned_weights == {
        "commitment": 1.0,
        "family": 1.0,
        "global_alarm": 0.8,
    }
    assert learned.selected_load_bearing_rate == 0.0
    assert learned.mean_selected_utility == -1.0


def test_online_care_update_handles_anchorless_selection_and_clipping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    episode = generate_episode(0)
    by_role = {candidate.role: candidate for candidate in episode.candidates}

    def choose(role: str):
        candidate = by_role[role]

        def rank(*_args, **_kwargs):
            return {
                "coincidence": EpisodeRanking(
                    policy="coincidence",
                    ranked_nodes=(candidate.node,),
                    top_role=candidate.role,
                    load_bearing_rank=None,
                    ppr_residual=0.0,
                )
            }

        return rank

    monkeypatch.setattr(benchmark_module, "rank_episode", choose("context_only"))
    anchorless = learn_care_weights((episode,), learning_rate=10.0)
    assert anchorless.learned_weights == anchorless.initial_weights

    monkeypatch.setattr(benchmark_module, "rank_episode", choose("alarm"))
    clipped = learn_care_weights((episode,), learning_rate=10.0)
    assert clipped.learned_weights["global_alarm"] == 0.05


def test_numerical_gate_fails_on_any_registered_control_margin_breach() -> None:
    episodes = generate_episodes((64, 65), regimes=("base", "noisy"))

    def adversarial_scorer(candidate, seed):
        if candidate.role == "load_bearing":
            return 1.0
        if candidate.role == "alarm" and seed == 65:
            return 1.2
        return 0.0

    audit = epiplexity_control_audit(episodes, scorer=adversarial_scorer)

    assert audit.minimum_margin_bits == pytest.approx(-0.2)
    assert audit.worst_seed == 65
    assert audit.worst_control_role == "alarm"
    assert not numerical_validity_pass(1e-12, audit.minimum_margin_bits)


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_epiplexity_audit_rejects_non_finite_scores(non_finite: float) -> None:
    episode = generate_episode(64)

    def invalid_scorer(candidate, _seed):
        return non_finite if candidate.role == "load_bearing" else 0.0

    with pytest.raises(ValueError, match="must be finite"):
        epiplexity_control_audit((episode,), scorer=invalid_scorer)
    assert not numerical_validity_pass(0.0, non_finite)


def test_epiplexity_audit_requires_a_control_comparison() -> None:
    episode = generate_episode(64)
    load_bearing = next(
        candidate
        for candidate in episode.candidates
        if candidate.role == "load_bearing"
    )
    control_free = replace(episode, candidates=(load_bearing,))

    with pytest.raises(ValueError, match="control comparison"):
        epiplexity_control_audit(
            (control_free,),
            scorer=lambda _candidate, _seed: 1.0,
        )


def test_pilot_summary_is_byte_stable_and_gate_complete(tmp_path: Path) -> None:
    first_path = write_summary(tmp_path / "first.json")
    second_path = write_summary(tmp_path / "second.json")
    first_bytes = first_path.read_bytes()
    second_bytes = second_path.read_bytes()
    frozen_bytes = DEFAULT_OUTPUT.read_bytes()
    first = json.loads(first_bytes)
    second = json.loads(second_bytes)

    assert first_bytes == second_bytes == frozen_bytes
    assert first == second == json.loads(frozen_bytes)
    unsigned = dict(first)
    observed_digest = unsigned.pop("summary_digest")
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    assert observed_digest == hashlib.sha256(canonical.encode()).hexdigest()
    assert set(first["gates"]) == {
        "NUMERICAL_VALIDITY",
        "DUAL_ACTIVATION_SELECTIVITY",
        "UTILIZATION_FILTER",
        "ONLINE_CARE_RECOVERY",
    }
    assert first["allowed_claim"] in {"synthetic diagnostic", "scaffold only"}
