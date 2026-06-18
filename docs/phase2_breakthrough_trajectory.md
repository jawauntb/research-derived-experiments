# Phase 2 Breakthrough Trajectory

Date: 2026-06-16

This note is the lab-director critique and trajectory reset for Phase / Arc 2.
It is intentionally more aggressive than a handoff. The purpose is to make the
next branches compete for scientific leverage, not PR count.

## Researcher-Lens Critique

Top AI research taste would judge the current process as promising but still
too demo-shaped.

The strong part is real: Arc 2 has moved through symbolic selectors, learned
candidate-parse agents, parse-invariant vectors, pixel-rendered observations,
and a Haskell-backed admissibility checker. The control taxonomy is also good:
surface reward, passive inference, restless inquiry, and concerned syntax fail
or pass for different reasons.

The weak part is that each gate still hands the system too much of the
scientific move. The benchmark asks whether an agent uses a provided probe
well, not whether it invents the next useful experiment. A hostile reviewer
could still say the system is a good benchmark solver with a carefully
designed intervention, not a discovery process.

The Sutton/Silver lens asks what improves with experience and compute. Our
answer is not yet strong enough: we have multi-seed sweeps, but not a scalable
loop that learns experiment design policies, searches over bodies, or discovers
new probe programs.

The Pearl/Scholkopf/Bengio lens asks whether passive prediction has been
separated from causal knowledge. We have begun doing this, but Phase 2 should
now make intervention selection itself causal: the agent should choose a target
whose manipulation disambiguates competing mechanisms.

The Chollet/Lake lens asks for abstraction and held-out composition. Our gates
should stop being mostly i.i.d. seed replications and add held-out role pairs,
parse families, intervention tokens, and surface transformations.

The CausaLab / AI-scientist lens asks for mechanism-trajectory fidelity, not
just final answer accuracy. Phase 2 should record the evolving hypothesis,
chosen program, observation, belief update, and action, so a run can be judged
as a scientific trajectory.

The Feynman/reviewer lens says: build the strongest shortcut first. Every major
result should include a red-team baseline designed to pass the headline metric.
If it passes, the claim dies early. If it fails, the positive result has teeth.

## Process Changes

Each Phase 2 experiment should now pre-register these fields:

- Breakthrough question: the field-facing claim being attacked.
- Old-regime shortcut: the strongest baseline that should almost work.
- Kill criterion: the observation that would make us retract or weaken the
  claim.
- New artifact type: what the old regime could not represent.
- Transfer ladder: the smallest held-out test beyond i.i.d. seeds.
- Mechanism trace: the program, observation, belief update, and action record.
- Residual content: what survived the shortcut and transfer gates.

The branch is not done when code passes. It is done when the result says which
claim tier is allowed:

- Diagnostic: a benchmark separates controls.
- Mechanism: the positive agent composes the required operation.
- Regime transition: a new artifact type or verifier changes what can be
  represented.
- Field claim: the mechanism survives transfer, adversarial shortcuts, and
  literature-nearest baselines.

Most current Arc 2 results are diagnostic-to-mechanism. The next audacious move
is to push toward regime transition.

## Best Next Trajectory

The strongest near-term trajectory is **Concerned Intervention Invention**.

Current pixel agents receive a pair probe that already targets the causal role
pair. That proves concern-gated probe use, but not intervention invention.
The next gate should expose a small program language and require the agent to
choose the useful target:

```text
observe_pair(a,b)
null
```

Then the ladder expands:

```text
observe_pair(a,b)
move(anchor)
ablate(role)
compose(two steps)
search-discovered body consumes the program
Haskell checker validates the body/program contract
held-out role-pair and parse-family transfer
learned object slots replace connected components
```

The minimal gate is intentionally small: from pixels, choose whether to probe
and which pair to probe. The target is not given as `trial.causal_pair`. A
passing agent must learn:

- which object pair is causally relevant from visible role/object features,
- when the ambiguity matters for viability,
- when not to spend probe budget,
- how to act after a useful observation.

Controls should fail in distinct ways:

- surface shortcut: decent action prior, poor hidden binding;
- random program probe: spends budget but rarely targets the useful pair;
- target without concern: finds the pair but probes low-concern cases;
- concern without target: probes at the right times but does not identify the
  useful intervention;
- restless target: identifies high-concern binding but violates the low-concern
  discipline.

## Metrics That Matter Next

The first result on this trajectory should report:

- high-concern parse accuracy;
- action accuracy;
- subtree accuracy;
- high-concern probe rate;
- low-concern probe rate;
- high-concern target accuracy;
- useful program rate;
- mean probe cost;
- regret;
- object extraction rate;
- seed-level gate pass rate.

The new gate should require target accuracy, not merely parse/action accuracy.
Otherwise the agent can still be described as using a provided experiment.

Current branch result:

- `concerned_program_inventor` passes the 5-seed Modal gate with high-concern
  parse accuracy `1.000`, action accuracy `1.000`, target accuracy `1.000`,
  useful-program rate `1.000`, low-concern probe rate `0.156`, and gate pass
  rate `1.000`.
- `target_without_concern` proves target selection alone is insufficient:
  target accuracy is `1.000`, but low-concern probe rate is `1.000`.
- `concern_without_target` proves concern gating alone is insufficient:
  low-concern probe rate is `0.156`, but high-concern target accuracy is only
  `0.088`.
- Haskell motif verdicts now participate in local 2B program-body search.
  Across the fixed five-seed report set, `viability_guided` reaches body gate
  `1.000`, empirical gate `1.000`, formal valid `1.000`, Haskell-source rate
  `1.000`, target/useful high `1.000`, and low-probe `0.144`, while
  `reward_only` and `syntax_proxy` fail. This closes the local
  Haskell-in-loop gap for `2A-v1`; Modal still needs either a Haskell-enabled
  image or a precomputed Haskell verdict cache.
- A Modal transfer sweep now makes the `2A-v1` boundary explicit. The i.i.d.
  `concerned_program_inventor` gate still passes, but held-out role/parse
  transfer fails: i.i.d. gate pass `1.000`, mean transfer-slice gate pass
  `0.171`, weakest slice `role_kind:repair_core`. This should be treated as a
  real claim boundary, not as an implementation nuisance.
- The next branch lifts the same contract to `2A-v2-pixels-rich_programs`.
  `concerned_program_composer` chooses among `observe_pair`, `move_anchor`,
  `ablate_pair`, and `compose_move_observe` families and passes the 5-seed
  Modal gate with high-concern parse `1.000`, action `1.000`, family `1.000`,
  target `1.000`, useful-program `1.000`, rich-program `1.000`, low-concern
  program rate `0.162`, and gate pass rate `1.000`.
- The richer controls isolate the remaining claim boundary: `target_without_family`
  gets target accuracy `1.000` but useful-program rate `0.000`;
  `family_without_target` gets family accuracy `1.000` but target accuracy
  `0.080`; `rich_without_concern` gets parse/action/family/target all
  `1.000` but low-concern program rate `1.000`.
- The next breakthrough gate should make the richer `2A-v2` composer pass
  held-out role/parse transfer and move beyond the provided rich grammar toward
  open-ended or searched program composition.

Current coupled 2A/2B result:

- `program_body_search_modal_2026_06_16.md` freezes
  `2A-v1-pixels-observe_pair` and makes 2B program-body search consume the
  actual empirical 2A gate.
- Across five Modal seeds, `viability_guided` reaches body gate `1.000`,
  empirical gate `1.000`, formal valid `1.000`, target/useful high `1.000`,
  low-probe `0.156`, and discovers
  `calibration_guard+causal_binding_head+concern_policy+formal_guard+intervention_planner+reward_head+vector_surface_encoder+world_model`.
- `reward_only` fails as a shortcut body; `syntax_proxy` reaches target/useful
  `1.000` but fails the body gate with low-probe `0.830`.
- The local Haskell-in-loop gap is now closed for `2A-v1`; the next 2B
  breakthrough gate should preserve Haskell-source provenance on Modal and
  consume the future `2A-v2` richer intervention contract.

## Literature Bearings

Recent causal-discovery work points the same direction. ACE frames
experimental design as a learned sequential policy over interventions.
CausaLab separates final prediction from faithful causal-mechanism recovery
and records hypothesis/action trajectories. A-CBO-style critiques of passive
causal discovery sharpen the anti-cheat: passive predictors can fail exactly
where targeted interventions concentrate belief over near-miss causal graphs.

Local delta:

```text
Prior work: active causal discovery and object-level latent interventions.
This branch: concern-gated intervention selection under hidden syntactic
constituency, no-low-concern-probing discipline, and pixel/object surfaces.
```

That is the fastest path from "good benchmark" toward "audacious contribution":
show that maintained concern can organize not only action and representation,
but the invention of experiments that make the world's causal syntax legible.
