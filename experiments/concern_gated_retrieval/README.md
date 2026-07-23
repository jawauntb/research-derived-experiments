# Concern-Gated Off-Context Retrieval

This package tests a narrow algorithmic question: on a synthetic memory graph,
does a candidate that is close to both active context and persistent concern
rank above candidates that are close to only one, and can a bounded-observer
future check reject a dual-activated but useless trap?

The package intentionally does not claim to model human memory, discover
semantic meaning, or establish selfhood. Graph roles and simulator utility are
authored fixtures. A positive result is a pipeline and decomposition result.

## Method

1. Warp an undirected memory graph smoothly by non-negative care weights.
2. Run personalized PageRank from active context and care anchors.
3. Rank off-context candidates by a rarity-corrected Hadamard product.
4. Nominate the top three candidates.
5. Retain candidates whose goal-conditioned reachable-future epiplexity
   exceeds the frozen threshold.
6. In the exploratory online condition, update only the concern anchor
   attached to the selected probe using its realized utility.

The epiplexity implementation follows equations (7)-(9) of Zhang and Levin
(2026), *Intelligence from Learnable Novelty*: a frozen random reservoir, a
stable ridge readout, and the spectral log-determinant price.

## Run

```bash
python3 -m experiments.concern_gated_retrieval.run_pilot
```

This writes a deterministic public receipt to `results/summary.json`.

## Verify

```bash
pytest -q tests/test_concern_gated_retrieval.py
```

The frozen design, fatal gates, mathematical objects, and claim boundary are
in [`PREREGISTRATION.md`](PREREGISTRATION.md).
