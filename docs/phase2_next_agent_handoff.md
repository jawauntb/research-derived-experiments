# Phase / Arc 2 Handoff for the Next Agent

Date: 2026-06-16  
Repo: `jawauntb/research-derived-experiments`  
Local working repo used for this handoff: `/Users/jawaun/.codex/worktrees/122e/Research Derived Experiments`  
Primary external artifact folder: `/Users/jawaun/Metaphysics of Intelligence/Phase_Arc_2`

This document is a detailed continuation brief for a new agent session. It is
written to preserve the current scientific state, the methodological spine, the
latest artifacts, and the fastest path to the next useful result.

Latest start-here note: `docs/phase2_next_breakthrough_handoff.md`. Use that
note first for the current #127/#128 frontier, Modal-first compute rules, next
breakthrough milestones, chart/PDF guidance, and fresh-branch instructions. This
document remains useful as the longer historical brief.

## 1. Highest-Level Program Shape

The research program is currently organized like this:

```text
Arc 1: Maintained Concern
  Minimal homeostatic agents, self/world attribution, costly null probes,
  detect -> probe -> cool -> re-engage, Metric Stack and Correction Chain.

Arc 2A: Concerned Syntax
  The grammar of the world under concern: causal constituency, intervention
  invention, parse tracking, anti-cheat tests for syntax under viability.

Arc 2B: Viable Computational Bodies
  The grammar of the agent's body under viability: architecture/body motifs,
  admissibility, resource gates, formal guards, executable modules.

Arc 3: Creative Concern Systems
  Convergence: agents invent probes, parses, bodies, and shared grammars that
  are field-validated by formal, behavioral, social, and empirical gates.
```

The core theoretical ladder currently used in the papers is:

```text
difference -> geometry -> syntax -> salience -> valence
          -> action -> attribution -> maintenance
```

The next frontier is not another table inside the same setup. The next frontier
should make a real regime transition:

```text
generated vectors -> rendered pixels -> learned object/part extraction
                 -> intervention invention -> evolved/search-discovered bodies
                 -> Haskell/solver-backed admissibility consumed by Python
```

## 2. Latest Merged State

The latest major merged PRs before the successor handoff were:

- PR #128: `Couple program-body search to the 2A gate`
- Merge commit: `8a93813f34e4f869461e13719820f3914eedaf99`
- Scientific delta: freezes `2A-v1-pixels-observe_pair` and makes 2B
  program-body search consume the empirical 2A intervention-invention gate.

- PR #127: `Add concerned intervention invention gate`
- Merge commit: `3752c9474b8b5c5edd7d71173cd3426bab457953`
- Scientific delta: makes target selection part of the 2A pixel/program task,
  separating target-only, concern-only, random-probe, and surface shortcuts.

Older major merged PR:

- PR #123: `Add vector Phase 2 gates and Haskell ontology`
- Merge commit: `1757d2a176c45804dff05f069eea8bf46bc6a730`
- Branch was deleted remotely after merge.

The immediately prior major PR was:

- PR #122: `Add learned Phase 2 syntax agents`
- Merge commit: `9ea5fb9cba5dcbb03d93280be8c0639bc75074e6`

These PRs moved Phase / Arc 2 from symbolic scaffolds into learned/vector
mechanism gates and a first Haskell typed-ontology foothold.

## 3. Repo Discipline and Required Workflow

Follow the local AGENTS rules:

1. Always start from a fresh fetch/pull of `origin/main`.
2. Work on a fresh `codex/...` branch from `origin/main`.
3. Do not work directly on a stale local branch.
4. Run lints, type checks, and targeted tests if relevant before committing.
5. For most changes here, `python3 scripts/run_quality_checks.py` is the right
   full repo gate.
6. If touching Haskell ontology code, also run:

   ```bash
   (
     cd formal/ontology-hs && cabal test all && cabal run ontology-check
   )
   ```

7. If touching figures, also run:

   ```bash
   uvx --python 3.12 --with matplotlib python scripts/make_phase2_step4_figures.py
   ```

8. If touching papers, render PDFs and visually inspect rendered PNG pages:

   ```bash
   uvx --from markdown-pdf python scripts/render_paper_pdf.py \
     --in papers/concerned_syntax/paper.md \
     --out papers/concerned_syntax/paper.pdf \
     --title 'Constituency Tests for Concerned Representation in Minimal Agents' \
     --author 'Jawaun Brown'

   uvx --from markdown-pdf python scripts/render_paper_pdf.py \
     --in papers/viable_computational_bodies/paper.md \
     --out papers/viable_computational_bodies/paper.pdf \
     --title 'Viability-Guided Evolution of Syntax-Bearing Computational Bodies' \
     --author 'Jawaun Brown'
   ```

9. Copy final public PDFs to:

   ```text
   /Users/jawaun/Metaphysics of Intelligence/Phase_Arc_2/
   ```

10. Commit, push, open a PR, and merge when done. The GitHub CLI may complain
    locally because another worktree has `main` checked out. If that happens,
    verify the remote PR state; previous merges succeeded remotely even though
    the local `gh pr merge` post-merge checkout failed. Then delete the remote
    feature branch manually if needed.

## 4. Skills and Research Process

Yes, the research/science tooling has been used, but the next agent should use
it more deliberately and earlier.

### Skills Already Used

- `discovery-regime-audit`: used to structure the research record and to keep
  the distinction clear between scaffold, search, diagnostic result, and real
  regime transition.
- `pdf`: used for PDF rendering and visual page inspection.
- `ce-compound`: consulted for this handoff because the user explicitly asked
  for compounding knowledge and faster future discovery.

### Skills the Next Agent Should Use

Use `discovery-regime-audit` whenever a new experiment changes any of:

- artifact type,
- observation surface,
- intervention language,
- body/architecture grammar,
- formal verifier,
- selection rule,
- gate/metric,
- claim level.

Each real result should answer:

- Old regime: what did the prior setup allow?
- Transition: what changed structurally?
- Transported evidence: which gates were preserved?
- Rejected alternatives: what failed and why?
- Residual finding: what is new beyond reformatting old evidence?
- Readiness: which gates passed/failed?
- Allowed claim: what is the weakest justified claim?
- Next operation: what directly attacks the new bottleneck?

Use `ce-compound` or the local equivalent when a non-obvious method decision is
made. Example: "Haskell should own typed body admissibility, while Python owns
Modal experiments and reports" is worth compounding because it will recur.

Use the PDF skill every time a paper PDF changes. Do not rely on markdown alone.
Tables and charts can clip or split badly.

## 5. Important Current Artifacts

### Arc 2A: Concerned Syntax

Core files:

- `experiments/concerned_syntax/benchmark.py`
- `experiments/concerned_syntax/learned_agents.py`
- `experiments/concerned_syntax/vector_shapes.py`
- `experiments/concerned_syntax/modal_concerned_syntax_sweep.py`
- `experiments/concerned_syntax/modal_learned_agents_sweep.py`
- `experiments/concerned_syntax/modal_vector_shapes_sweep.py`
- `tests/test_concerned_syntax.py`

Public reports:

- `experiments/concerned_syntax/results/pilot_2026_06_16.md`
- `experiments/concerned_syntax/results/modal_sweep_2026_06_16.md`
- `experiments/concerned_syntax/results/learned_agents_modal_2026_06_16.md`
- `experiments/concerned_syntax/results/vector_shapes_local_2026_06_16.md`
- `experiments/concerned_syntax/results/vector_shapes_modal_2026_06_16.md`

Paper:

- `papers/concerned_syntax/paper.md`
- `papers/concerned_syntax/paper.pdf`
- `papers/concerned_syntax/preregistration.md`
- `papers/concerned_syntax/figures/fig1_vector_gate_margins.png`

External PDF copy:

- `/Users/jawaun/Metaphysics of Intelligence/Phase_Arc_2/2A_Concerned_Syntax_2026_06_16.pdf`

Latest core result:

```text
concerned_vector_probe:
  parse-high: 1.000
  action:     1.000
  subtree:    0.804
  high-probe: 1.000
  low-probe:  0.189
  gate:       PASS

passive_vector:
  action remains decent but parse/subtree fail.

restless_vector_probe:
  parse/action pass, low-concern probing fails.

surface_shortcut:
  action prior is not enough; parse/subtree fail.
```

Scientific interpretation:

The vector-observation gate removed candidate-parse descriptors. The visible
surface is deliberately invariant under hidden true/alternate parse swap. The
accepted agent must use a concern-gated intervention to recover the hidden
binding bit. This is stronger than the candidate-parse learned gate.

Allowed claim:

This is a benchmark/mechanism result, not human evidence and not pixel-level
perception. It justifies saying that concerned syntax can be separated from
reward, passive vector inference, and restless uncertainty reduction on a
parse-invariant vector surface.

### Arc 2B: Viable Computational Bodies

Core files:

- `experiments/viable_computational_bodies/search.py`
- `experiments/viable_computational_bodies/modal_body_evolution_sweep.py`
- `experiments/viable_computational_bodies/modal_report.py`
- `experiments/viable_computational_bodies/results/pilot_2026_06_16.md`
- `experiments/viable_computational_bodies/results/modal_sweep_2026_06_16.md`
- `experiments/viable_computational_bodies/results/executable_bodies_modal_2026_06_16.md`
- `experiments/viable_computational_bodies/results/vector_module_bodies_local_2026_06_16.md`
- `experiments/viable_computational_bodies/results/vector_module_bodies_modal_2026_06_16.md`
- `tests/test_viable_computational_bodies.py`

Paper:

- `papers/viable_computational_bodies/paper.md`
- `papers/viable_computational_bodies/paper.pdf`
- `papers/viable_computational_bodies/preregistration.md`
- `papers/viable_computational_bodies/figures/fig1_vector_module_gate_margins.png`
- `papers/viable_computational_bodies/figures/fig2_haskell_ontology_verdicts.png`

External PDF copy:

- `/Users/jawaun/Metaphysics of Intelligence/Phase_Arc_2/2B_Viable_Computational_Bodies_2026_06_16.pdf`

Latest core result:

```text
modular_concerned_body:
  parse-high:      1.000
  action:          1.000
  high-probe:      1.000
  low-probe:       0.189
  formal:          1.000
  anti-cheat:      0.950
  module coverage: 0.950
  gate:            PASS

passive_vector_body:
  formally admissible, but module coverage and parse fail.

restless_vector_body:
  behavior can pass, but formal/anti-cheat low-concern guard fails.

surface_reward_body:
  shortcut body; action is not enough.
```

Scientific interpretation:

The body-side result now preserves the 2A distinction under vector
observations. A body that lacks active causal binding cannot identify the
hidden binding. A body that has binding but lacks the calibration/formal guard
becomes restless. The accepted body combines surface encoding, concern policy,
causal binding, role-conditioned action, and calibration guard.

Allowed claim:

This is the first vector-observation executable module validation, not full
neural architecture search. It validates the gate shape and body motif logic.

### Haskell Typed Ontology Gate

Core files:

- `formal/ontology-hs/concerned-ontology.cabal`
- `formal/ontology-hs/src/ConcernedOntology.hs`
- `formal/ontology-hs/app/Main.hs`
- `formal/ontology-hs/test/Main.hs`
- `formal/ontology-hs/README.md`

Run:

```bash
(
  cd formal/ontology-hs && cabal test all && cabal run ontology-check
)
```

Current output:

```text
"guarded_syntax_body"
{"formal_valid":true,"resource_cost":12,"violations":[]}
"restless_tree_body"
{"formal_valid":false,"resource_cost":12,"violations":["restless_without_calibration_guard"]}
"modular_concerned_body"
{"formal_valid":true,"resource_cost":8,"violations":[]}
```

Toolchain state:

- GHC installed via Homebrew: GHC 9.14.1
- Cabal installed via Homebrew: cabal-install 3.16.1.0
- Cabal build outputs are ignored through `.gitignore` via `dist-newstyle/`.

Important lesson:

The Haskell checker caught real ontology inconsistencies during development:

1. Concern/calibration guards were initially treated as resource-costed body
   morphology. That over-costed `guarded_syntax_body`. They are now formal
   overlays with cost 0.
2. `role_specific_heads` originally required only `tree_binder`. The vector
   body uses `causal_binding_head`, so the ontology had to explicitly admit
   vector causal binding as a binder role parallel to symbolic tree binding.
3. Restless active binding under concern now requires `calibration_guard`.

Next Haskell step:

Package the Haskell toolchain, or a precomputed Haskell motif-verdict cache,
for Modal-scale body search. Local Python now consumes Haskell JSON verdicts
for arbitrary motif candidates during `program_body_search`; Modal still falls
back to `python_static` unless Cabal is available in the image.

## 6. Research Sources and Citation Practice

Source manifest:

- `references/SOURCES.md`

Core sources already in the program:

- Revencu, Pajot, and Dehaene on syntactic structure in geometric shape
  representations: https://doi.org/10.1037/xge0001890
- Neural Language of Thought Models: https://arxiv.org/abs/2402.01203
- ACE, Active Causal Experimentalist: https://arxiv.org/abs/2602.02451
- CausaLab: https://arxiv.org/abs/2605.26029
- Causal-JEPA: https://arxiv.org/abs/2602.11389
- Representation Learning of Geometric Trees: https://arxiv.org/abs/2408.08799
- Compositional Neuro-Symbolic Reasoning: https://arxiv.org/abs/2604.02434
- Inducing Causal World Models in LLMs for Zero-Shot Physical Reasoning:
  https://arxiv.org/abs/2507.19855

Research-search rule for future agents:

1. Before designing a new experiment, do a targeted arXiv/web search for
   adjacent work from the last 12 to 24 months.
2. Prefer primary sources: arXiv, official project pages, papers, and docs.
3. Add only relevant sources to `references/SOURCES.md`.
4. Cite papers in the relevant paper markdown only when they actually shaped
   the method or interpretation.
5. Do not overfill references with loosely related papers. The source list is
   for accelerating experiment design, not bibliography padding.
6. Use web browsing for current research. Do not assume the agent's memory of
   2026 papers is current.

Good search queries for the next step:

```text
arXiv 2026 object-centric world models visual intervention planning
arXiv 2026 causal representation learning object slots interventions
arXiv 2026 differentiable program induction geometric shapes
arXiv 2026 neuro-symbolic agents causal program graphs intervention
arXiv 2026 pixel-to-symbol reasoning ARC object extraction causal
Haskell type-level DSL formal methods architecture search JSON verifier
```

Recommended research sprint:

1. Search broadly for 20 to 30 minutes before coding. Use several adjacent
   query families rather than one exact phrase.
2. Keep only sources that change the experiment design, the control condition,
   or the claim boundary.
3. For each source, record a one-line use tag in working notes:

   ```text
   use: method template | baseline | anti-cheat warning | terminology |
        negative control | discussion contrast
   ```

4. Update `references/SOURCES.md` with the canonical URL. Prefer DOI, arXiv
   abstract page, official PDF, OpenReview page, or the project's official
   site over secondary summaries.
5. Add paper-local citations only where the source is actually used in the
   argument. Good citation locations are:
   - the paragraph motivating the benchmark,
   - the paragraph defining a baseline/control,
   - the paragraph explaining why a shortcut is insufficient,
   - the limitations paragraph that prevents overclaiming.
6. Before writing "novel," search for the nearest prior task and state the
   precise delta. Example:

   ```text
   Prior work: object-level latent interventions for world models.
   Delta here: intervention is concern-gated and tested with hidden
   causal-constituency flips under a no-low-concern-probing constraint.
   ```

7. If the literature already solves a subproblem, import it as a baseline or
   implementation motif. Do not spend local effort proving a solved point.
8. If the literature exposes a new shortcut, turn that shortcut into an
   anti-cheat gate before running the main sweep.

Citation standard:

- Use primary sources for technical claims.
- Use the attached/user-provided PDFs as local context, but cite public URLs
  when the paper is public.
- Do not cite a paper for more than it proves. For example, Revencu et al.
  supports human geometric constituency tests, not maintained concern or
  agency.
- Separate "inspired by" from "empirically supported by." The former belongs
  in motivation/discussion; the latter can support a method or claim.
- Every new source should answer: what did it change about the experiment?

## 7. What Is Actually Done

Done:

- Symbolic Concerned Shape Grammar.
- Symbolic selectors: null, flat valence, compression proxy, uncertainty only,
  concerned syntax.
- Local and Modal symbolic sweeps.
- Learned candidate-parse agents.
- Learned candidate-parse executable body validation.
- Vector-observation agents with parse-invariant surfaces.
- Vector module-body validation.
- Pixel-rendered observations with connected-component object extraction and
  local and Modal 5-seed gate validation.
- Minimal pixel-level intervention invention with learned `observe_pair(a,b)`
  target selection and concern gating.
- Rich pixel-level intervention programs over `observe_pair`, `move_anchor`,
  `ablate_pair`, and `compose_move_observe`, with local and Modal 5-seed
  gate validation for `2A-v2-pixels-rich_programs`.
- Python consumption of Haskell JSON verdicts inside learned/vector body
  summaries when the local Haskell checker is available.
- Gate-margin charts for 2A and 2B.
- Haskell typed ontology checker prototype.
- Updated papers and PDFs for 2A and 2B.
- Audit ledger entries for every major Phase 2 transition.

Not done:

- Learned object/part extraction from images beyond algorithmic connected
  components.
- Held-out transfer for the richer intervention-program grammar.
- Open-ended or searched program invention beyond the provided rich grammar.
- Body search or Haskell-in-loop validation against the `2A-v2` rich-program
  contract.
- Evolved/search-discovered executable module bodies under the vector/pixel
  gate.
- Real neural module bodies such as object-slot encoders, graph neural nets,
  differentiable tree binders, mixture-of-experts role heads, or program
  induction components.
- Human experiments on causal syntax/self-world attribution.
- Multi-agent field validation or creative concern systems.

## 8. Recommended Next Goals

### Goal A: Pixel-Rendered Concerned Syntax

Create a pixel-rendered environment from the vector shapes.

Status after PR #125 follow-on branch work: the local version exists at
`experiments/concerned_syntax/pixel_shapes.py`, with a Modal entrypoint at
`experiments/concerned_syntax/modal_pixel_shapes_sweep.py` and a tracked local
report at
`experiments/concerned_syntax/results/pixel_shapes_local_2026_06_16.md`.
The Modal-scale report now lives at
`experiments/concerned_syntax/results/pixel_shapes_modal_2026_06_16.md`.
The 5-seed Modal result passes for `concerned_pixel_probe` with parse-high
`1.000`, action `1.000`, subtree `0.806`, object extraction `1.000`,
high-probe `1.000`, low-probe `0.195`, and gate pass rate `1.000`. It
preserves the surface/passive/restless failure taxonomy. The remaining Goal A
work is a gate-margin figure and replacing the algorithmic extractor with a
learned object-slot or CNN baseline.

Proposed files:

- `experiments/concerned_syntax/pixel_shapes.py`
- `experiments/concerned_syntax/modal_pixel_shapes_sweep.py`
- `experiments/concerned_syntax/results/pixel_shapes_modal_YYYY_MM_DD.md`
- `papers/concerned_syntax/figures/fig2_pixel_gate_margins.png`

Minimum viable design:

1. Render the six vector parts into small grayscale or RGB images, e.g. 32x32
   or 64x64.
2. Ensure the image is invariant to hidden true/alternate parse swap.
3. Include roles visually through shape/color/texture, not through a direct
   symbolic one-hot.
4. Start with a lightweight local feature extractor, not a huge CNN:
   - connected-component extraction,
   - centroid/radius/color features,
   - pairwise distances,
   - then reuse the vector gate.
5. Then add a tiny CNN/object-slot baseline if needed.
6. Preserve the same controls:
   - surface shortcut,
   - passive pixel/vector,
   - restless probe,
   - concerned probe.

Gate:

```text
parse-high >= 0.75
action >= 0.85
subtree >= 0.75
high-concern probe >= 0.70
low-concern probe <= 0.25
```

Anti-cheat:

- Same final image must admit multiple hidden parses.
- Surface-only model must not receive parse labels or candidate descriptors.
- Probe observation must be causally tied to intervention, not leaked by image
  metadata.
- Report a withheld/rejected smoke if small-run means pass but seed-level gate
  fails.

### Goal B: Python Consumes Haskell Verdicts

Make the Python body evaluator call the Haskell checker or consume its JSON
output.

Status: completed in PR #125. `ontology-check` supports named body verdicts and
`--motifs`; Python consumes those verdicts through
`experiments/viable_computational_bodies/haskell_gate.py` and records
`formal_source`, `formal_valid`, `resource_cost`, and `formal_violations`.
Keep this section as the design record, not as an open task.

Follow-on status: local program-body search now calls `ontology-check --motifs`
for searched candidates and records Haskell-source formal provenance in
`experiments/viable_computational_bodies/results/program_body_search_haskell_local_2026_06_16.md`.
Across the fixed five-seed report set, `viability_guided` reaches body gate
`1.000`, empirical gate `1.000`, formal valid `1.000`, Haskell-source rate
`1.000`, target/useful high `1.000`, and low-probe `0.144`.

Proposed files:

- Extend `formal/ontology-hs/app/Main.hs` to accept body names or motif JSON.
- Add Python helper: `experiments/viable_computational_bodies/haskell_gate.py`.
- Add tests in `tests/test_viable_computational_bodies.py`.

Design:

1. `ontology-check` should support:

   ```bash
   cabal run ontology-check -- modular_concerned_body
   cabal run ontology-check -- --motifs vector_surface_encoder,reward_head,...
   ```

2. Python should call it in a cached way so tests are not painfully slow.
3. Body summaries should record:

   ```text
   formal_source = "haskell"
   formal_valid
   resource_cost
   violations
   ```

4. If Haskell is missing, tests should either:
   - skip the Haskell integration test with a clear message, or
   - run only a pure-Python fallback unit test.

Recommended claim:

Do not claim full formal verification. Claim "typed external admissibility
checker consumed by the empirical gate."

### Goal C: Evolve/Search Over Module Bodies

The current vector module bodies are hand-instantiated. The next 2B breakthrough
is to search over executable bodies that call into the vector/pixel 2A gate.

Possible approach:

1. Define body motifs in Python and Haskell with one shared JSON schema.
2. Generate candidate bodies with:
   - surface encoder,
   - concern policy,
   - causal binding head,
   - action head,
   - calibration guard,
   - optional memory,
   - optional role-specific heads,
   - optional counterfactual rollout.
3. Use the Haskell checker to reject invalid bodies.
4. Train/evaluate surviving bodies on the vector/pixel gate.
5. Use a quality-diversity archive over:
   - parse-high,
   - low-probe discipline,
   - formal validity,
   - module coverage,
   - resource cost,
   - seed stability.

Success condition:

The search discovers `modular_concerned_body`-like motifs without being handed
the four-body comparison set.

### Goal D: Intervention Invention

Current agents are given pair probe and calibration. Arc 2A eventually needs
agents that invent or compose interventions.

Status after PR #126 follow-on branch work: a minimal local version exists at
`experiments/concerned_syntax/intervention_invention.py`, with a Modal
entrypoint at `experiments/concerned_syntax/modal_intervention_invention_sweep.py`
and tracked local/Modal reports at
`experiments/concerned_syntax/results/intervention_invention_local_2026_06_16.md`
and
`experiments/concerned_syntax/results/intervention_invention_modal_2026_06_16.md`.
The agent sees extracted pixel-object features and a menu of `observe_pair(a,b)`
programs. It does not receive `trial.causal_pair` at evaluation time. The
5-seed Modal sweep passes for `concerned_program_inventor` and separates the
target-only and concern-only controls.

Status after the `2A-v2-pixels-rich_programs` follow-on branch: the richer
program-language version exists at
`experiments/concerned_syntax/rich_program_language.py`, with a Modal
entrypoint at `experiments/concerned_syntax/modal_rich_program_language_sweep.py`
and tracked local/Modal reports at
`experiments/concerned_syntax/results/rich_program_language_local_2026_06_17.md`
and
`experiments/concerned_syntax/results/rich_program_language_modal_2026_06_17.md`.
The 5-seed Modal sweep passes for `concerned_program_composer`: parse-high
`1.000`, action `1.000`, family-high `1.000`, target-high `1.000`,
useful-high `1.000`, rich-high `1.000`, low-concern program rate `0.162`,
and gate pass rate `1.000`.

Completed rich grammar:

```text
probe program tokens:
  observe_pair(a,b)
  move(anchor)
  ablate_pair(a,b)
  compose_move_observe(anchor,a,b)
  null
```

The first line of this goal is now complete for `observe_pair(a,b)` target
selection. Held-out transfer is now instrumented and Modal-replicated, but it
fails: the i.i.d. gate pass rate is `1.000`, while mean held-out transfer-slice
gate pass is `0.171`, with weakest slice `role_kind:repair_core`. Movement,
ablation, two-step composition, and Modal-scale replication are now complete in
a provided grammar. The remaining next version is a mechanism that can pass
held-out role/parse transfer, open-ended or searched program discovery, and 2B
body consumption of the `2A-v2` contract.

Gate:

- Agent chooses or composes a probe that makes hidden binding identifiable.
- Probe budget stays below low-concern cap.
- A random probe composer and an uncertainty-only composer fail for distinct
  reasons.

Strong next paper phrase:

```text
Probe availability is not intervention invention.
Intervention invention requires composing an action that makes the concern-
relevant distinction identifiable under cost and no-restless constraints.
```

## 9. How to Parallelize Work Fast

Use massive parallelism, but be disciplined about what can actually run in
parallel.

### Good Parallel Tool Calls

Use `multi_tool_use.parallel` for independent local reads:

- `rg`
- `sed`
- `git diff`
- `git status`
- `pdfinfo`
- `ls`
- reading result reports
- reading paper sections

Do not chain noisy shell commands with separators when parallel tool calls would
be cleaner.

### Good Parallel Research Streams

When designing the next experiment, split thinking into streams:

1. **Method stream:** What is the smallest new artifact/gate transition?
2. **Literature stream:** What recent arXiv papers already solve or constrain
   the idea?
3. **Anti-cheat stream:** What shortcuts would make the result meaningless?
4. **Implementation stream:** What code path touches least surface area?
5. **Paper/report stream:** What result table and figure will make the claim
   legible?

If the environment has multi-agent tools available, use subagents for these
streams. If not, simulate the same structure with parallel reads/searches and
separate notes in the main thread.

### What to Run Remotely

The user explicitly wants Modal used to avoid cooking the local machine.
Treat this as a standing execution rule for Phase 2: local work is for code
inspection, unit tests, type/lint checks, PDF rendering/inspection, and tiny
harness sanity checks only. Multi-seed sweeps, learned-agent training,
architecture/body search, larger image experiments, and anything CPU- or
memory-heavy should run on Modal or another cloud backend by default.
Do not run local multi-seed "just to see" sweeps when a Modal entrypoint exists.

Run local:

- tiny smoke tests,
- unit tests,
- PDF rendering,
- Haskell compile/test,
- figure generation.

Run on Modal:

- multi-seed sweeps,
- any neural/CNN training,
- larger image/pixel experiments,
- architecture/body searches.

Existing Modal pattern:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/concerned_syntax/modal_vector_shapes_sweep.py \
  --train-trials 3000 --test-trials 1200 --epochs 90
```

For new Modal scripts:

- Use `modal.Image.debian_slim(python_version="3.12")`.
- Include `add_local_python_source("experiments")`.
- Use `cpu=1` for lightweight sweeps unless a real GPU is needed.
- Write raw JSON under ignored `artifacts/...`.
- Write public summaries under `experiments/.../results/...md`.

### Parallel Figure/Paper Work

Once a result is stable:

1. Generate public report.
2. Generate a small figure that makes the anti-cheat failure pattern visible.
3. Insert figure and table into paper.
4. Render PDF.
5. Use Poppler `pdftoppm` and visual inspection on the affected pages.

Do not wait until the end to think about figures. They often clarify which
metric is the actual gate.

## 10. Process Reflection for the Next Agent

What worked well:

- Treating failures as findings. The tiny vector Modal smoke had means that
  looked acceptable but still printed fail because one seed missed a gate. That
  was recorded rather than hidden.
- Moving from symbolic -> learned candidate parse -> vector parse-invariant
  surface. Each step changed the artifact type and preserved old gates.
- Keeping controls sharp. Surface/passive/restless controls now fail for
  different reasons, which makes the result more credible.
- Adding charts after tables. The gate-margin heatmaps make the anti-cheat
  structure much easier to understand.
- Installing Haskell when the user said machine mutation was acceptable. The
  type checker immediately caught ontology assumptions that Python code had
  blurred.

What was slower than it needed to be:

- The Haskell checker was added after the vector gate instead of before the
  body grammar was refined. Next time, define the formal schema earlier and let
  it constrain the experiment design.
- Charts were added after the papers were already rendered. Next time, plan the
  figure with the result table.
- Literature search was useful but could be more systematic. Next time, search
  before implementation and again before writing the discussion.

How to compound faster:

1. Before coding, write the new regime transition in one sentence.
2. List the exact anti-cheat controls before implementing the positive model.
3. Implement the smallest local smoke.
4. Run a tiny Modal smoke to catch packaging and seed instability.
5. Run the full Modal sweep.
6. Immediately add an audit card with accepted, rejected, and residual content.
7. Generate a figure before updating the paper prose.
8. Render and visually inspect PDF pages.
9. Commit/PR/merge while the context is fresh.

The key mental habit:

```text
Do not ask "can we improve the score?"
Ask "what shortcut would make this score meaningless, and can we make that
shortcut fail while the intended mechanism passes?"
```

## 11. Claim-Level Guardrails

Do not overclaim:

- These are not human behavioral experiments.
- These are not neural evidence.
- These are not pixel-level visual perception yet.
- Haskell ADTs are not a proof assistant.
- Modal sweeps are not full architecture search.
- Passing action is not passing syntax.
- Passing parse is not passing concern.
- Passing formal validity is not passing behavior.
- Novel body motifs are not useful unless the field/gates validate them.

Safe current claims:

- Arc 2A now has symbolic, learned candidate-parse, and vector-observation
  gates that separate concerned syntax from reward, compression/proxy,
  passive inference, and restless uncertainty reduction.
- Arc 2B now has symbolic search, executable body validation, vector module
  validation, and a typed Haskell admissibility prototype.
- The current frontier is pixel perception, Modal-packaged Haskell/cache-backed
  body search, and search-discovered executable modules.

## 12. Suggested Immediate Next Branches

### Branch 1: `codex/phase2-haskell-modal-cache`

Goal:

Modal-scale body search consumes Haskell ontology verdicts or a provenance-safe
precomputed Haskell verdict cache.

Definition of done:

- Modal image includes the Haskell checker, or the run consumes a tracked
  Haskell-generated motif verdict cache.
- Modal report records `formal_source = "haskell"` or
  `formal_source = "haskell_cache"` for searched bodies.
- Haskell errors cannot silently become passing Python-static verdicts.
- Papers mention this as admissibility integration, not full formal proof.

### Branch 2: `codex/phase2-pixel-syntax`

Goal:

Pixel-rendered concerned syntax with parse-invariant images.

Definition of done:

- Pixel renderer is deterministic and parse-invariant.
- Surface-only pixel/vector controls fail parse.
- Concerned probe passes on Modal.
- Reports, charts, paper, PDFs updated.

### Branch 3: `codex/phase2-module-search`

Goal:

Search over executable module bodies instead of hand-instantiating four bodies.

Definition of done:

- Candidate bodies generated from a typed motif grammar.
- Haskell rejects invalid candidates.
- Modal evaluates surviving bodies on vector or pixel gate.
- Viability-guided search beats reward-only and novelty-only controls.

### Branch 4: `codex/phase2-intervention-language`

Goal:

Move from choosing a provided probe to composing interventions from primitives.

Definition of done:

- Probe programs are generated/composed.
- Concerned probe composer passes.
- Random/uncertainty-only composers fail.
- Audit records whether this is true intervention invention or still selection.

## 13. Commands Worth Keeping Handy

Full repo quality:

```bash
python3 scripts/run_quality_checks.py
```

Concerned syntax tests:

```bash
python3 -m unittest tests.test_concerned_syntax
```

Body tests:

```bash
python3 -m unittest tests.test_viable_computational_bodies
```

Haskell gate:

```bash
(
  cd formal/ontology-hs && cabal test all && cabal run ontology-check
)
```

Regenerate Phase 2 Step 4 figures:

```bash
uvx --python 3.12 --with matplotlib python scripts/make_phase2_step4_figures.py
```

Vector Modal sweep:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/concerned_syntax/modal_vector_shapes_sweep.py \
  --train-trials 3000 --test-trials 1200 --epochs 90
```

Intervention-invention local run:

```bash
python3 -m experiments.concerned_syntax.intervention_invention \
  --train-trials 1200 --test-trials 500 --seed 20260616 --epochs 60 \
  --out artifacts/concerned_syntax/intervention_invention_local.json \
  --agent-report experiments/concerned_syntax/results/intervention_invention_local_2026_06_16.md
```

Intervention-invention Modal sweep:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/concerned_syntax/modal_intervention_invention_sweep.py \
  --train-trials 3000 --test-trials 1200 --epochs 90
```

Rich-program Modal sweep:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/concerned_syntax/modal_rich_program_language_sweep.py \
  --train-trials 3000 --test-trials 1200 --epochs 90
```

Program-body search against 2A-v1:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/viable_computational_bodies/modal_program_body_search.py \
  --generations 24 --population 24 \
  --train-trials 3000 --test-trials 1200 --epochs 90
```

Render PDFs:

```bash
uvx --from markdown-pdf python scripts/render_paper_pdf.py \
  --in papers/concerned_syntax/paper.md \
  --out papers/concerned_syntax/paper.pdf \
  --title 'Constituency Tests for Concerned Representation in Minimal Agents' \
  --author 'Jawaun Brown'

uvx --from markdown-pdf python scripts/render_paper_pdf.py \
  --in papers/viable_computational_bodies/paper.md \
  --out papers/viable_computational_bodies/paper.pdf \
  --title 'Viability-Guided Evolution of Syntax-Bearing Computational Bodies' \
  --author 'Jawaun Brown'
```

Copy PDFs to external folder:

```bash
cp papers/concerned_syntax/paper.pdf \
  '/Users/jawaun/Metaphysics of Intelligence/Phase_Arc_2/2A_Concerned_Syntax_2026_06_16.pdf'

cp papers/viable_computational_bodies/paper.pdf \
  '/Users/jawaun/Metaphysics of Intelligence/Phase_Arc_2/2B_Viable_Computational_Bodies_2026_06_16.pdf'
```

## 14. Final Orientation for the Next Agent

The user wants results, not stopping points. Still, the correct rhythm is:

```text
small local smoke -> Modal full sweep -> audit -> chart -> paper/PDF -> checks
-> commit -> PR -> merge -> continue
```

The fastest path to a real next breakthrough is probably:

1. Treat the Modal-scale `2A-v2-pixels-rich_programs` grammar as available but
   not final.
2. Fix the failed held-out role-pair/parse-family transfer gate so the rich
   composer cannot be only an i.i.d. color/position reader.
3. Move beyond the provided grammar into open-ended or searched program
   discovery.
4. Route searched/evolved bodies through Haskell admissibility before evaluating
   them on the vector/pixel/program gates.
5. Make 2B consume the `2A-v2-pixels-rich_programs` contract instead of only
   the `2A-v1-pixels-observe_pair` contract.

Why that path:

- It attacks the biggest current limitation: provided interventions and
  i.i.d. target selection.
- It preserves the successful gate structure.
- It keeps the Haskell formal layer operational instead of decorative.
- It creates a clean story for the next paper revision:

```text
candidate parse -> vector surface -> pixel surface -> program selection,
Python-only formal guard -> Haskell-in-the-loop admissibility,
hand-instantiated bodies -> searched/evolved bodies.
```

That is how to keep compounding instead of circling.

Latest coupled result after PR #127:

- `experiments/viable_computational_bodies/results/program_body_search_modal_2026_06_16.md`
  freezes `2A-v1-pixels-observe_pair` and evaluates 2B searched bodies against
  the real 2A program gate.
- Across five Modal seeds, `viability_guided` reaches body gate `1.000`,
  empirical gate `1.000`, formal valid `1.000`, target/useful high `1.000`,
  low probe `0.156`, and discovers
  `calibration_guard+causal_binding_head+concern_policy+formal_guard+intervention_planner+reward_head+vector_surface_encoder+world_model`.
- The Haskell-backed local follow-up report
  `experiments/viable_computational_bodies/results/program_body_search_haskell_local_2026_06_16.md`
  uses the same five report seeds at `1200/500/60`, records
  `formal_source = "haskell"` for searched bodies, and reaches
  `viability_guided` body gate `1.000`, empirical gate `1.000`, formal valid
  `1.000`, target/useful high `1.000`, and low probe `0.144`.
- `reward_only` fails as a shortcut body; `syntax_proxy` reaches target/useful
  `1.000` but fails body gate with low-probe `0.830`.
