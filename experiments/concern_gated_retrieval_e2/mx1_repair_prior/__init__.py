"""MX1 — minimal de-risk probe for the two MIDAS-style transfers.

MX1 is **not a wave**. Wave 1b falsified L1, so the roadmap's Waves 2-4 do
not open. MX1 asks the single successor question the synthesis paper scopes
in its section 7, at the smallest scale that can answer GO/NO-GO:

* **Part A** — does a *care-independent* within-episode verify->repair loop
  reach the load-bearing memory in fewer attempts than the care model alone,
  and than random? The repair rule under test is retain-and-re-pair: a pick
  that scores about zero *alone* may be one half of a super-additive pair
  rather than worthless.
* **Part B** — does splitting "the memory did not help" (REASONING_FAULT)
  from "our checker could not score this" (VERIFIER_FAULT) stop a genuinely
  useful memory from being mislabelled useless?

Both parts are frozen in ``PREREGISTRATION.md`` before any evaluation row was
generated, including two substrate findings that changed the design (no
persistent cross-episode memory; no care-independent *structural* signal,
because every candidate has identical graph degree).

Everything numeric is imported from the frozen ``wave0``/``wave1b`` packages;
MX1 edits neither.
"""
