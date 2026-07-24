"""COGR-E2b — learned-geometry confirmation and L1 / L2 gate (Wave 1b).

This subpackage hosts the COGR-E2b crossed-factorial confirmation described
in ``docs/concern_gated_retrieval_research_program.md`` § "COGR-E2b —
learned-geometry confirmation" and preregistered in
``experiments/concern_gated_retrieval_e2/wave1b/PREREGISTRATION.md``.

Scope boundary
--------------

Wave 1b is a **crossed 3 x 3 x 3 confirmatory step** that issues an **L1
verdict** (representation contribution: learned vs frequency-matched vs
oracle geometry crossed with the Wave 0 adversarially wrong concern) and an
**L2 verdict** (concern recovery + specificity: online-learned concern
crossed with learned geometry) **separately**. Wave 1b CAN reject either
claim on the fatal gates enumerated in ``PREREGISTRATION.md`` §9
(integrity, L1-behavior including SET-level Recall@k dominance and
simple-regret dominance, L1-representation contribution via edge
intervention, L2-recovery, L2-specificity, non-ceiling, adversarial
poisoning, robustness, bundle-awareness). Wave 1b CANNOT establish
semantic meaning or selfhood; those are Wave 3+ objects.

Per the roadmap and Wave 1a promotion contract, a Wave 1a KILL does not
block Wave 1b's L1 rows. Wave 1a's E2a KILL withholds L2 but does not
invalidate an independently supported L1 result. Wave 1b's L2 rows are
additionally conditional on the family-redesign passing the pre-run
oracle-recall assertion enumerated in ``PREREGISTRATION.md`` §4.

Spencer's echo-chamber design corrections (mandatory)
-----------------------------------------------------

Wave 1b implements six design corrections that Wave 1a did not have:

1. **Terminology.** Regret, propensity, and exploration are three distinct
   receipts. Regret measures utility missed; propensity records ``q_t(v)``
   and enables IPS/DR debiasing on the supported set but cannot recover
   information about ``v`` with ``q_t(v) = 0``; exploration is what gives
   neglected candidates nonzero ``q_t``. All three appear in the
   promotion contract.
2. **Family redesigns.** Wave 1a KILLed because ``info_matched_recency``
   reproduced the oracle ceiling byte-for-byte on every family. Wave 1b
   families must place the load-bearing memory at a random non-recent
   position on at least 50% of episodes, cross-tabulate load-bearing role
   against every generic signal, and pass a pre-run assertion that
   ``oracle_recall_at_k(s) < 0.8`` for every generic-signal baseline
   ``s`` on every family.
3. **Bundle utilities.** Utility is not additive: singletons,
   contradictory pairs, complementary pairs, dangerous conjunctions, and
   isolation-distractors are first-class planted objects.
4. **Oracle-regret metric family.** SET-level ``oracle_recall_at_k``,
   ``simple_regret_set``, ``cumulative_regret``, and
   ``interaction_recovery`` are the decisive L1 metrics. Hit@1 is
   diagnostic only.
5. **Split-budget ablation.** ``k_split_care_uncertain_audit`` at
   70/20/10, 50/30/20, and 80/10/10 is a labelled ablation, NOT the
   promotion path.
6. **Utility separation.** ``Delta_task`` is the primary utility; the
   Zhang-Levin epiplexity ``S^phi`` is an optional bonus / tie-breaker /
   dependent variable only, with pre-registered ``beta`` and ``gamma``.

Reuse boundary
--------------

Wave 1b imports frozen Wave 0 and Wave 1a objects and never edits them:

* ``experiments.concern_gated_retrieval_e2.wave0.graph_learn.build_withheld_graph``
  supplies the withheld geometry basis.
* ``experiments.concern_gated_retrieval_e2.wave0.concern_update.LoggedProbePolicy``
  and ``update_concern`` supply the logged-probe policy and IPS/DR
  estimators plus the poisoning guard.
* ``experiments.concern_gated_retrieval_e2.wave0.sealed_env`` supplies
  the sealed environment, ``EpisodeContext``, ``SealedOutcome``, and
  ``IntegrityAudit``.
* ``experiments.concern_gated_retrieval_e2.wave0.template_split``
  supplies the calibration / confirmatory template-split guard.
* ``experiments.concern_gated_retrieval_e2.wave0.baselines`` supplies
  the frozen baseline slate (``BASELINES``, ``match_budget``,
  ``promotion_admit``, ``learned_one_stage_parameter_count``, and the
  ``CANDIDATE_MECHANISM_PARAM_COUNT``).
* Wave 1a is inherited as a screen receipt for the L2 gate only; it does
  not gate L1.

Wave 1b NEVER touches calibration seeds ``100000..100999``; the split
guard raises ``LeakageError`` on misuse. Wave 1b uses the same
confirmatory seed range as Wave 1a, ``200000..201999``, with the paired
seed subranges enumerated in ``PREREGISTRATION.md`` §5.
"""
