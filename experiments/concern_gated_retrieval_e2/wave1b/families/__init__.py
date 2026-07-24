"""Wave 1b family generators (v2 redesigns).

Each Wave 1b family lives in its own ``*_v2`` module and is a redesign of
the corresponding Wave 0 family. The v2 redesigns satisfy two
non-negotiable constraints introduced by Wave 1a's KILL and the Spencer
echo-chamber critique:

* **Recency != oracle** — the load-bearing memory is placed at a
  non-recent event-stream position on at least half of the episodes, and
  every generic-signal baseline (recency, embedding_sim, care_only,
  freq_only, salience, value, priority) falls below the oracle top-k on
  every family. This is enforced by a pre-run assertion callable exposed
  by each family module.
* **Bundle utilities are first-class** — each episode plants useful
  singletons, contradictory pairs, complementary pairs, dangerous
  conjunctions, and isolation distractors, all recorded in the family's
  :class:`BundleManifest` for the wave1b oracle enumerator.

The Wave 0 family modules are imported (never edited) as reference. The
v2 modules do not reuse the wave0 withheld-graph construction because
their bundle-planting requires an event stream whose position ordering
is decoupled from the withheld graph's zone layout.
"""

__all__: list[str] = []
