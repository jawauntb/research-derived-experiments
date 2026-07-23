"""COGR-E2a — concern-recovery screen (Wave 1a).

This subpackage hosts the COGR-E2a concern-recovery screen described in
``docs/concern_gated_retrieval_research_program.md`` § "COGR-E2a — concern-
recovery screen" and preregistered in
``experiments/concern_gated_retrieval_e2/wave1a/PREREGISTRATION.md``.

Scope boundary
--------------

Wave 1a is a **screen** for the concern-update rule. It CAN reject the
update rule on any of the fatal gates enumerated in ``PREREGISTRATION.md``
§5 (coverage, propensity accounting, specificity vs generic
value/priority/recency signals, aggregate hiding a family reversal). It
CANNOT establish learned memory geometry (a Wave 1b / COGR-E2b object)
and it CANNOT establish an L2 history-derived-concern-recovery claim
(also a Wave 1b object). Wave 1a's promotable outputs are:

1. a decision on whether the online-learned concern-update rule survives
   the screen; and
2. an off-policy value estimate (IPS + DR) of that rule against the
   Wave 0 frozen-wrong baseline, published only if the screen passes
   every fatal gate.

Reuse boundary
--------------

Wave 1a imports the frozen Wave 0 objects and never edits them:

* ``experiments.concern_gated_retrieval_e2.wave0.graph_learn.build_withheld_graph``
  supplies the fixed withheld geometry.
* ``experiments.concern_gated_retrieval_e2.wave0.concern_update.LoggedProbePolicy``
  supplies the randomized-probe policy with logged propensities.
* ``experiments.concern_gated_retrieval_e2.wave0.concern_update.update_concern``
  supplies the IPS and DR off-policy estimators plus the poisoning
  guard.
* ``experiments.concern_gated_retrieval_e2.wave0.sealed_env`` supplies
  the sealed environment, ``EpisodeContext``, ``SealedOutcome``, and
  ``IntegrityAudit``.
* ``experiments.concern_gated_retrieval_e2.wave0.template_split``
  supplies the calibration/confirmatory template split guard; Wave 1a
  runs with the ``COGR_WAVE0_CONFIRMATORY_RUN`` env token because it is
  the first stage licensed to read confirmatory templates.

Wave 1a NEVER touches calibration seeds ``100000..100999``; the split
guard raises ``LeakageError`` on misuse.
"""
