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
- The mechanism-trace follow-up verifies the full program -> observation ->
  belief update -> action chain. `concerned_program_inventor` reaches
  high-concern trace completion `1.000`, useful observation `1.000`,
  posterior correctness `1.000`, action `1.000`, and low-concern trace
  violation `0.151` across five Modal seeds. `target_without_concern` gets a
  perfect high-concern trace but fails the low-concern cap at `1.000`;
  `concern_without_target` keeps the cap but useful observation is only
  `0.087`.
- The next breakthrough gate should add held-out transfer and richer program
  composition, not rerun the same `observe_pair(a,b)` menu.

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
