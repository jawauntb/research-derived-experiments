# Concern-Gated Retrieval E2

Successor package to the frozen L0 pilot at
[`experiments/concern_gated_retrieval/`](../concern_gated_retrieval/). This
package hosts the staged COGR-E2 program described in
[`docs/concern_gated_retrieval_research_program.md`](../../docs/concern_gated_retrieval_research_program.md)
and continued by
[`docs/next_agent_concern_gated_retrieval_handoff_2026-07-23.md`](../../docs/next_agent_concern_gated_retrieval_handoff_2026-07-23.md).

## Reuse boundary

- **Import, never edit:** `experiments/concern_gated_retrieval/graph.py`
  (`WeightedGraph`, `personalized_pagerank`, `coincidence_scores`) and
  `experiments/concern_gated_retrieval/epiplexity.py` are the canonical
  numerical primitives. Wave 0 imports them; it does not fork them.
- **Replace, do not extend:** the pilot's authored graph generator, role
  labels, and constant/shuffled synthetic futures. Wave 0 introduces its own
  procedural family generators, sealed environment interface, and
  adversarially misspecified concern prior.

## Wave layout

| Subpackage | Status | Purpose |
|---|---|---|
| `wave0/` | active | Premise scaffolding, calibration-only variance/headroom estimates, adversarially wrong prior, three procedural families, and a signed promotion contract. Produces frozen thresholds; no confirmatory rows. |
| `wave1/` | not yet created | COGR-E2a concern-recovery screen on fixed withheld geometry, then COGR-E2b learned-geometry confirmation with separate L1 and L2 gate receipts. |
| `wave2+/` | not yet created | Narrow live-agent beachhead, then substrate transfer and safety stressing. |

## Claim boundary for Wave 0

Wave 0's promoted deliverables are:

1. a preregistration (`wave0/PREREGISTRATION.md`) signed before any
   confirmatory row is generated;
2. a frozen promotion contract (`wave0/PROMOTION_CONTRACT.md`); and
3. a calibration receipt with variance estimates and provenance
   (`wave0/PROVENANCE.md`, populated by the Modal calibration step).

Wave 0 does **not** claim learned memory geometry, concern recovery, semantic
meaning, or selfhood. Descriptions to that effect anywhere in this subtree are
a wave-boundary violation.

## Anti-leakage contract

Every dataclass, function, and receipt in this package records which template
family it came from (`calibration` or `confirmatory`). A runtime guard in
`wave0/` refuses to expose a confirmatory row to calibration code paths. See
[`wave0/PREREGISTRATION.md`](wave0/PREREGISTRATION.md) §4 for the enumerated
evaluator-only fields and the guard's invariants.
