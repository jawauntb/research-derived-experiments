"""Erratum E1 — the concern prior is a perfect inverted oracle.

Sorting candidates by *ascending* ``care_anchors`` and taking the first
achieves ``hit@1 = 1.000`` on every COGR family tested, including the
confirmatory pool Wave 1b ran on. ``care_anchors`` is a policy-visible field,
so a one-line policy outperforms every mechanism the program built.

Root cause: Wave 0 PREREGISTRATION section 5 was implemented as
``prior[load_bearing] = W_COMMIT_INIT`` -- suppressing exactly one node, which
is the answer -- making the suppressed value a unique identifier for the
target.

This package does three things and edits nothing frozen:

* :mod:`.inverted_signal_audit` -- the gate that would have caught it. For
  every policy-visible signal, score candidates in BOTH directions.
* :mod:`.prior_repair` -- suppress a *set* including non-answers, so ascending
  concern yields a shortlist rather than the answer.
* :mod:`.verify_erratum` -- reproduce the leak on the frozen families, then
  show the repair closes it.

See ``ERRATUM.md`` for the full validity table. In short: Wave 1b's L1 KILL and
MX1's Part B stand (the leak cancels in a paired contrast that holds concern
constant); Wave 0's "10x below baseline" is re-explained rather than
invalidated; and every absolute performance number in the program was measured
on a substrate where one line scores 1.000.
"""
