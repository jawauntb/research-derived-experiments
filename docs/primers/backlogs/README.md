# Primer-derived research backlogs

This directory turns the six primer PDFs into executable research backlogs. Each
article has its own source ledger and TODO list; the list preserves the primer's
page/section, the repository surface it affects, a deliverable, and a measurable
pass/fail gate. The supplied PDFs were byte-identical to the copies under
`docs/primers/` before review.

## Article backlogs

| Article | Source signals | Executable TODOs | Backlog |
|---|---:|---:|---|
| The Lineage and the Trajectory | 38 | 35 | [history_lineage_and_trajectory_todo.md](history_lineage_and_trajectory_todo.md) |
| The Mathematics of Constraint | 62 | 66 | [mathematics_of_constraint_todo.md](mathematics_of_constraint_todo.md) |
| What It All Means | 38 | 32 | [philosophy_what_it_means_todo.md](philosophy_what_it_means_todo.md) |
| How This Knowledge Is Made | see ledger | 53 | [science_of_the_program_todo.md](science_of_the_program_todo.md) |
| The Instrument | 32 | 48 | [software_engineering_todo.md](software_engineering_todo.md) |
| Systems That Hold Themselves Together | 32 | 34 | [systems_theory_complexity_todo.md](systems_theory_complexity_todo.md) |

There are **268 article-local TODOs**. Repeated ideas remain in the article
where they were raised, while this index supplies the cross-article execution
order. The source-signal ledger in each file is the coverage audit: every
criticism, tension, limitation, open question, or constructive idea maps to one
or more TODO IDs.

## How to read and execute the lists

- **P0** blocks a valid claim, corrects a factual/math/artifact defect, or closes
  a trust gap. Do it before launching a new large sweep.
- **P1** is the next high-value replication, control, citation, or framework
  hardening step.
- **P2** materially expands external validity, accessibility, or theory breadth.
- **P3** is exploratory and should not be used to rescue a failed P0/P1 gate.
- **new** means no implementation was found; **partial** means relevant code or
  evidence exists but the proposed deliverable/gate is unfinished; **existing**
  means the evidence is already present and the remaining work is correction,
  integration, or replication.

Every item carries the same execution contract: source page/section, concrete
action, affected paths, deliverable, pass/fail gate, dependencies, and rationale.
Items marked as inferences are explicitly labeled rather than presented as
quotes from the primers.

## Recommended cross-article order

The individual backlogs are authoritative; this sequence prevents downstream
experiments from being built on stale claims or untyped evidence.

1. **Repair the evidence surface.** Do the metadata/layout fixes and stale-status
   corrections (H-001, M-003, M-010, P-01/P-02/P-05/P-06, S-001-S-008,
   E-SE-001-E-SE-006, T-SYS-001-T-SYS-004), then add the claim/evidence registry and
   structured gate records.
2. **Make measurements mathematically defensible.** Correct the optimization,
   VOI, geometry, topology, equivariance, bootstrap, metric, and dimension
   definitions (M-001-M-014, M-101-M-115; S-005-S-006; T-SYS-005-T-SYS-010).
3. **Replicate the boundary conditions independently.** Preserve the external
   weakness hard kill, topology mediation negative, concern/XOR correction chain,
   and three-seed caveats while running only preregistered, genuinely
   discriminating extensions (H-006/H-101-H-109, P-05-P-15, S-009-S-018).
4. **Test causal use rather than availability.** Use the philosophy and math
   criteria to align the commitment-surface dose-response, gauge/self-world,
   endogenous-concern, strongest-impostor, and intervention-identifiability
   suites (P-07-P-15, P-25-P-29, M-008-M-010, M-201-M-213).
5. **Harden the research instrument.** Wire PR CI, exact dependency/runtime
   manifests, structured result schemas, public-safe row exporters, typed metrics,
   independent red-team/adjudication, and the ML experiment framework skill
   (S-019-S-053, software backlog E-SE items, P-26-P-29, T-SYS-028-T-SYS-031).
6. **Only then expand the frontier.** Run the many-part, bifurcation/hysteresis,
   viability-kernel, strict autopoiesis, natural-image, cross-substrate, and
   external-recording directions (H-201-H-210, P-16-P-32, M-201-M-506,
   T-SYS-011-T-SYS-034).

## Cross-cutting research reading queue

The article files contain exact per-source reading tasks. Together they call for
primary-source work on cybernetics and autopoiesis; teleosemantics, natural kinds,
Dretske, Dennett, self-models, and normativity; bootstrap and hierarchical
inference; rate-distortion, PAC-Bayes, group representations, topology, and
causal identifiability; active learning and uncertainty; bifurcation,
hysteresis, viability, distributed control, multi-agent systems, and
nonequilibrium dynamics; and the AI-science observability literature. Add each
source to `references/SOURCES.md` only after recording what claim it supports,
what it does not support, and which backlog gate depends on it.
