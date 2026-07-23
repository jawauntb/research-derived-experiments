"""Wave 0 procedural family generators.

Each module in this subpackage implements exactly one of the three
procedurally distinct calibration families declared by
``experiments/concern_gated_retrieval_e2/wave0/PREREGISTRATION.md`` §6:

* :mod:`.delayed_commitments` — date-anchored personal obligation vs.
  chronic news-style alarm and calendar trivia.
* :mod:`.maintenance_fault` — early observation that becomes load-bearing
  only after a later symptom appears, opposite chronic critical-alert
  boilerplate.
* :mod:`.resource_constrained` — prior obligation that changes which
  otherwise-valid action is best, opposite a chronic large-transaction
  alarm.

Each family exposes an identical public API::

    generate_episode(seed, bucket, holdout=None) -> EpisodeSpec

so that the Wave 0 calibration slate can iterate over families without
family-specific branching. The families are calibration-only in Wave 0;
they may register confirmatory template ids but only :meth:`
TemplateRegistry.load` under the confirmatory-run env token surfaces
those rows to any caller.

Wave 0 style boundary: the family generators produce sealed
``EpisodeSpec`` rows that carry role labels, utility, and the answer key
inside sealed fields, but they do **not** describe learned memory
geometry, concern recovery, semantic meaning, or selfhood. Wave 0 is
calibration and family scaffolding plus wrong-prior initialization.
"""
