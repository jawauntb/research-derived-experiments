---
artifact_contract: "ce-handoff/v1"
created_at: "2026-08-17T17:50:00Z"
title: "SIC Dynamics close-out + Lea formalization handoff"
summary: "Papers A–F are merged. Possibility 5 is the house. The next licensed method is Lea (proved ≠ verified), not a new scientific letter. This document is the local-continuation contract and the parallelization plan."
keywords: ["sic-dynamics", "delete-repair", "lea", "formalization", "kappa", "eml", "possibility-5"]
repository: "jawauntb/research-derived-experiments"
base: "main"
head_at_handoff: "ce8b131"
session: "bc-01a00d99-d2d8-7c5e-a8d0-d0090dfd7bdd"
resume_focus: "Stand up Lea, copy docs/lea into a SicDynamics project, prove the Python-only load-bearing lemmas in parallel, SafeVerify, bank Lean, revise papers. Do not start Paper G."
---

# SIC Dynamics + Lea Handoff (2026-08-17)

Read this first if you are continuing locally or as the next cloud agent.

**One sentence:** A–F are done; the written κ is SIC; Lea is how we machine-check the remaining Python-only load-bearing claims; do not invent a new master object.

Canonical close-out: [`papers/sic_dynamics/paper.md`](../papers/sic_dynamics/paper.md).
Lea skill: [`.cursor/skills/lea/SKILL.md`](../.cursor/skills/lea/SKILL.md).
Lea project seed: [`docs/lea/`](lea/README.md).

---

## Resume objective

1. Merge / already-merged this handoff onto `main`.
2. Install Lea (Docker preferred; local Node 22 + uv + elan works).
3. Create project namespace `Lea.SicDynamics`.
4. Copy `docs/lea/{instructions,memory,blueprint}.md` into the project's `.lea/`.
5. Prove the **independent** blueprint nodes in parallel (one lemma, one file, one agent).
6. After `lean_check` green, run SafeVerify. Never collapse proved into verified.
7. Bank honest Lean into this repo. Mathlib-using files go to `formal/structural-intelligence-mathlib/` or a new `formal/lea-sic-dynamics/` Lake package. **Do not import Mathlib into** `DeleteRepair.lean`, `EmlZeroIdentity.lean`, or `Compiler/SquaringSeparation.lean`.
8. Revise `papers/sic_dynamics/paper.md` and the A–F notes with proved vs verified vs still-Python labels.
9. Stop. Do not start a new scientific letter.

---

## Current durable state

`origin/main` at handoff: **`ce8b131`**
`Paper F: write κ; it is SIC, not a new master object (#490)`.

Registry: **105** research packages / **57** structured / **48** legacy.

### Merged PRs that close the letter sequence

| PR | Tip (squash) | What |
|---|---|---|
| 479 | `7f1ad82` | Squaring separation US-1..US-4 |
| 480 | `dac4352` | Delete-the-absolute + constant EML census. Lean `DeleteRepair.lean` |
| 481 | `15770d7` | Variable-x EML k≤5 |
| 482 | `d45cd63` | US-4′ Gibbs half. k=3 `Φ_max/Φ_min=2.015625`. Extra-shell ~1.008. Exact zero identity |
| 484 | `7dea6bd` | Lean `EmlZeroIdentity.lean`. `#print axioms` empty |
| 483 | `b35d9a9` | US-4′ matching-skeleton GD. Zero 8/8 vs singleton 6/8. `phi_holds` |
| 485 | `882fdb1` | Unknown-skeleton GD: 7 vs 7, extras 6 vs 6, `min_size_governs` |
| 486 | `5c962a7` | Frozen-leaf rewrite + Paper B swap cell + synthesis |
| 487 | `6d8f080` | Paper C: Aff(1, Z/3) holonomy ≠ integer Kirchhoff |
| 488 | `4a20674` | Paper D: 196 diamonds, four `s²`; `disanalogy_holds` |
| 489 | `cff0b60` | Paper E: name-blind surgery 6/7; `surgery_killed` |
| 490 | `ce8b131` | Paper F: write κ; `calculus_is_sic` |

Do **not** merge unrelated PR **464** (old Copernicus / auto-merge rule).

### Papers A–F (letter sequence is closed)

| Paper | Object | Verdict | Package |
|---|---|---|---|
| A | Taxonomy + Lean + n=4 | Banked | `delete_the_absolute` + `DeleteRepair.lean` |
| B | Swap-cell | `taxonomy_holds` | `delete_repair_swap` |
| C | Connection beyond `List Int` | `cell3_holds` | `delete_repair_connection` |
| D | Shared-diagram disanalogy | `disanalogy_holds` | `delete_repair_disanalogy` |
| E | Typed assumption-surgery | `surgery_killed` | `delete_repair_surgery` |
| F | Write κ | `calculus_is_sic` | `delete_repair_kappa` |

Close-out paper: `papers/sic_dynamics/paper.md`.

### US-4′ process-split (banked, not a general law)

Access is **process-relative**:

| Process | Feels `Φ`? | Receipt |
|---|---|---|
| Gibbs sampler | Yes (2 vs 1 min-shell) | `eml_us4_prime` |
| Known-tree GD | Yes (8/8 vs 6/8) | `eml_us4_gradient` |
| Unknown-tree GD | **No** (7 vs 7) | `eml_us4_search` (`min_size_governs`) |
| Frozen-leaf greedy rewrite | Yes on extras (43 vs 28) | `eml_us4_discrete` (`phi_holds`) |

The extra-basin ratio `43/28 ≈ 1.54` is **not** identified with the Gibbs `Φ` ratio `2.016`.

### Six possibilities, live scoreboard

| # | Claim | Status |
|---|---|---|
| 1 | New universal calculus κ | **Dead as new.** Written function is SIC |
| 2 | Catalog/menu is the engine | **Live, stronger after E/F** |
| 3 | One ladder | **Dead** on A/B harness |
| 4 | Unique linear hierarchy | **Dead** (Path A/B) |
| 5 | SIC’s dynamics | **House. The close.** |
| 6 | Lorentz = Lamport = PE | **Dead** on diamond fibre |

Possibility 5’s *dynamics* reading dies only if someone finds a delete–repair fact outside `(q, K)`. We do not have one. Do not invent one.

### Paper F facts you must not flatten

- **κ_cheap** = Paper E `decide`. **Not a function.** Collision bucket (same cheap signature, golds `{noop, quotient}`):
  - `bag_q_id`, `last_bit_q_id`, `parity_q_id` → gold `quotient`
  - `pair_eq_q_id` → gold `noop`
- **κ_screen** = Kirchhoff mismatch → transport; else coarsest representing menu screen (fewest fibres, then lex name); then restore/quotient/noop. Hits **11/11**. Looks at the menu (disclosed). Theorem 4 / CommonSuffScreen plus a total order.
- **κ_unique** killed: `bag` has 5 representing screens; Path A/B disagree on `(0,1)` vs `(1,1)` (Lean `repair_paths_disagree`, **reused not re-proved**).
- Relabel `0↔3` is natural (`first_bit`/`q_stab0` ↔ `last_bit`/`q_stab_last`).
- Paper E miss: `pair_eq` on `q_id`. Gold is empirical menu-relative representability. Policy input only: `(mixes, n_fibres, n_worlds, y_has_nontrivial_symmetry, connection_mismatch)`.
- Held-out Aff cycle C: `((1,0),(1,0),(2,1),(2,2))` — holonomy `(1,1)`, Kirchhoff `(1,0)`.

### Already Lean (do not re-prove)

Mathlib-free, `formal/structural-intelligence/`, zero `sorry`, no Mathlib:

- `DeleteRepair.lean`: `over_invariance_nogo`, `symmetry_mismatch_nogo`, `cycle_integrates_iff_sum_zero`, `repair_splits_disagreement`, `repair_paths_disagree` / `pathA` / `pathB`
- `EmlZeroIdentity.lean`: `eml_zero_identity*` (`#print axioms` empty)
- `Compiler/SquaringSeparation.lean`: US-2 / US-3
- `CommonSuffScreen.lean`: Theorem 4 coarsest CSS (this **is** κ_screen’s theorem; F only adds a named total order)
- RR-2, TA-1, AF-1/AF-2, and the rest of the SIC cores

Mathlib package already exists: `formal/structural-intelligence-mathlib/` (SICA, SICC, CG-1/CG-2, Halmos–Savage finite, …). Use it if a lemma needs analysis. Do not contaminate the mathlib-free cores.

Paper F itself added **no Lean**. That is the gap Lea is licensed to close.

---

## Claim boundary

**Supported (merged):** US-1..US-4; Lean US-2/US-3; DeleteRepair finite headlines + 4×4 matrix; constant-EML size ≠ denotation; variable-x size ≠ function; Gibbs `Φ` ≠ shortest depth; zero identity + Lean; matching-skeleton GD `phi_holds`; unknown-skeleton GD `min_size_governs`; frozen-leaf extras 43 vs 28 `phi_holds`; Paper B `taxonomy_holds`; Paper C `cell3_holds`; Paper D `disanalogy_holds`; Paper E `surgery_killed`; Paper F `calculus_is_sic`.

**Withheld:** neural bootstrap; GD-in-general tracks `Φ`; valence/concern; Lorentz ≅ Lamport ≅ PE as a functor; OpenAI 2026 as theorems; Paper 0 / `Complex.log 0`; function identity from grid except exact zero; “better LLM shipped”; κ as a *new* master object; text nomination / DR/DCR reopen.

**Do not do:**

- Start Paper G or a new letter.
- Reopen DR/DCR text nomination.
- Fight `Complex.log 0`.
- Train a net.
- Fit a fancier cheap signature to erase `pair_eq`.
- Sprinkle `eml` into a transformer and call it a better LLM.
- Smash EML and relativity into one arrow.
- Merge PR 464.
- Import Mathlib into the mathlib-free cores.
- Collapse “the file elaborates” into “SafeVerify passed.”

---

## Scientific-discovery loop (compact)

### Current frame

Odrzywołek’s EML is an *instance* of SIC: completeness is fiber inhabitation, not discovery. The engine we ran is delete–obstruction–repair as **typed motion on SIC’s frontier**. The written repair map is the disclosed menu plus Theorem 4 plus a total order. That is Possibility 5, not a second master object.

### Assumption ledger

| Assumption | Status |
|---|---|
| Completeness = discovery | **Rejected.** Completeness = `q⁻¹(z) ≠ ∅` |
| Formula/tree length is invariant | **Rejected.** `sq` witness: formula length drops, circuit size stays `Θ(n)` |
| One search law (`Φ` always governs access) | **Rejected.** Process-split |
| One ladder (over-invariance = under-invariance = connection) | **Rejected.** A/B |
| Cheap 5-field signature determines gold | **Rejected.** E miss + F collision |
| Unique representing screen | **Rejected.** `bag` has 5 |
| Shared cartoon (diamond) is a shared theorem | **Rejected.** D: four `s²` |
| Integer Kirchhoff is the general connection | **Rejected.** C: Aff(1, Z/3) |
| Delete–repair facts live outside `(q, K)` | **Unkilled, unsupported.** Do not invent |
| Paper 0 is on this path | **Rejected.** Off-path |

### Anomaly map

- `pair_eq` on `q_id`: unused symmetry ≠ leftover privilege. Gold `noop`, cheap rule said `quotient`.
- κ_cheap collision: four worlds, one signature, two golds.
- Unknown-skeleton GD ties 7 vs 7 while Gibbs and known-tree GD feel `Φ`.
- Frozen-leaf extras 43 vs 28 is a `Φ` ranking that is **not** the Gibbs ratio.
- Aff cycle C is Kirchhoff-mismatched; earlier accidental Kirchhoff-flat cycle was a bug, not a result.

### Candidate reframes

1. **House (keep):** delete–repair is SIC’s dynamics. Next work is formalization and catalog, not a new calculus.
2. **Rejected:** κ as a new universal map from cheap diagnostics.
3. **Live, not this tranche:** valence/concern (Possibility 2 adjacent, never claimed here).

### Discriminating predictions

- If κ were a new cheap function, the collision bucket would be empty. It is not.
- If one search law held, unknown-skeleton GD would rank like Gibbs. It does not.
- If the diamond were a shared theorem, `s²` would be constant on the 196 embeddings. It takes four values.

### Severe experiment already run

Papers E and F. Kill criteria were predeclared. E died as a one-shot agent rule. F’s cheap map died as a function. F’s screen map survived and is SIC.

### Next best test

Not a new letter. **Lea on the Python-only load-bearing lemmas** listed in `docs/lea/blueprint.md`. Kill a formalization if: it re-proves Path A/B or CommonSuffScreen; it needs `Complex.log`; it imports Mathlib into a mathlib-free core; it treats an empirical ratio as a theorem; SafeVerify is skipped and the claim is labeled verified.

---

## How this relates to better LLMs (keep this paragraph intact)

Do **not** sprinkle `eml` into a transformer. If the frame is right:

1. Search at **sharing/DAG** level, not formula/tree unrolling (`sq` lesson).
2. Do not **delete working distinctions** (over-invariance / content-only attention).
3. Do not leave an **unearned privileged coordinate** (under-invariance).
4. Do not pretend one search law: `Φ` is process-relative.

“Discover all” splits: write all (completeness) ≠ reach all (access, process-relative) ≠ care which matter (concern/valence — **not done**).

**Not shipped:** a better LLM.

---

## Lea (read this; the skill has the commands)

Docs read for this handoff:

- Home: https://vida-nyu.github.io/Lea/
- llms.txt: https://vida-nyu.github.io/Lea/llms.txt
- Install: https://vida-nyu.github.io/Lea/install/
- Blog (2026-08-11): https://vida-nyu.github.io/Lea/blog/introducing-lea/
- Source: https://github.com/VIDA-NYU/Lea
- Prover (vendored): https://github.com/darturi/lea-prover
- SafeVerify: https://github.com/GasStationManager/SafeVerify

**What Lea is:** a Lean 4 agent backbone. The mathematician steers decomposition, intervenes mid-proof, reviews each claim. Two apps: LeaChat (Docker `:8001` / local Vite `:5173`) and LeaOverleaf. The prover runs **in-process** behind one FastAPI adapter. No hosted Lea account. The only data that leaves the machine is the prompt to your model provider.

**Design commitments we keep:**

- **Proved ≠ verified.** Proved = file elaborates, no `sorry`. Verified = SafeVerify kernel replay + per-declaration type/body match + axiom whitelist. A green `lean_check` is not an audit.
- Status is derived from the latest Lean verdict, never stored as a label.
- Project = namespace + `instructions.md` + `memory.md` + `blueprint.md`.
- Blueprint node ready iff dependency closure is discharged.
- Skills = markdown; roles = YAML.

**This cloud environment at handoff (2026-08-17):**

| Need | Status |
|---|---|
| Disk | ~219 GB free |
| Node | v22.14.0 |
| uv | present |
| elan / lake / lean | present |
| Docker | **absent** |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` | **unset** |

So: local `./install.sh --target ui` can run here once a key exists. Docker cannot. A local laptop with Docker Desktop + a pasted key is the fastest human path. Do not invent a key.

Install (from official docs):

```bash
# Docker (preferred on a laptop)
git clone https://github.com/VIDA-NYU/Lea.git
cd Lea/apps/lea-standalone
docker compose pull
docker compose up
# open http://localhost:8001 — paste key in Settings

# Local (this cloud box, after a key is present)
git clone https://github.com/VIDA-NYU/Lea.git
cd Lea
./install.sh --target ui          # add SafeVerify later: rerun without --skip-verify
# or full: ./install.sh
./start-dev.sh
# open http://localhost:5173
```

Headless drive (adapter is the API; there is no second prover server):

- `POST /api/runs` with `project_slug`, `message`, optional `autonomous`
- `GET /api/runs/{id}/events` SSE
- `POST /api/sessions/{id}/lean-check`
- `POST /api/sessions/{id}/verify` (SafeVerify; unavailable if installed with `--skip-verify`)
- Project docs: `GET/PUT /api/projects/{id}/docs/{instructions|memory|blueprint}`

`--skip-verify` makes `/verify` report unavailable. Re-run setup without the flag before claiming verified.

---

## Highest-value missed formalizations

Priority is load-bearing and still Python-only. Full DAG: [`docs/lea/blueprint.md`](lea/blueprint.md).

| Priority | Node | Why | Kill if |
|---|---|---|---|
| P0 | `kappa_cheap_not_function` | F’s death of Possibility 1 | You “fix” the signature instead of proving the collision |
| P0 | `kappa_screen_hits_suite` | F’s surviving map is an algorithm, not a slogan | You re-prove CommonSuffScreen |
| P0 | `bag_not_unique` | Uniqueness is dead | You claim uniqueness after a hidden tie-break |
| P1 | `kappa_relabel_natural` | `0↔3` sends first_bit/q_stab0 to last_bit/q_stab_last | You treat names as essence |
| P1 | `affine_escapes_kirchhoff` | Paper C | You claim Lorentz |
| P1 | `poset_not_determine_interval` | Paper D existential | You claim continuum physics |
| P1 | `surgery_miss_pair_eq` | Paper E typed miss | You refit the cheap rule |
| P2 | `dta_n4_representable_iff` | n=4 matrix is Python | You claim general-n |
| P2 | `swap_typed_wins` | Paper B | You reopen enumeration |
| skip | Empirical `Φ` ratios, GD 8/8, extras 43/28 | Diagnostics, not theorems | — |
| skip | Paper 0 / `Complex.log 0` | Off-path | — |
| skip | Path A/B, CSS, US-2/US-3, zero identity | Already Lean | — |

---

## How to finish with massive agent parallelization

Do **not** serialize “read docs → write skill → install → prove lemma 1 → lemma 2.” The skill, seed docs, and inventory are in this PR. The remaining work is environment + one-lemma lanes.

### Wave 0 — already done if this PR is on `main`

- Handoff, skill, `docs/lea/*`, catalog pointers, sic_dynamics “next method” note.

### Wave 1 — environment (one agent, blocking)

**Lane ENV** (single agent; everyone else waits only on the key + `lean_check` daemon):

1. New worktree from `origin/main`. Branch `cursor/lea-setup-7bdd`.
2. Confirm a model key. If missing, stop proving and ask the human to paste one in Lea Settings or export `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY`. Continue copying project docs without a key.
3. Install Lea (Docker on a laptop; `./install.sh` here).
4. `POST /api/runs` or the UI: create project slug `sic-dynamics`, namespace `Lea.SicDynamics`.
5. PUT the three files from `docs/lea/` into `.lea/`.
6. Smoke: “Prove that 2 is even” or the official √2 walkthrough. Then `lean_check`. Then SafeVerify if built.
7. Commit only repo-side notes (which install path, whether `/verify` is available). Do not commit Lea’s SQLite, keys, or `apps/lea-standalone/data/`.

### Wave 2 — one lemma per agent (launch together)

Each lane: **own worktree**, **own Lean file**, **own blueprint node**, **no shared file edits**.

Copy the seed into Lea once (Wave 1). Then each agent opens a **new session on the same project** focused on one ready node.

| Lane | Branch | File to own | Node | Depends on |
|---|---|---|---|---|
| A | `cursor/lea-kappa-cheap-7bdd` | `KappaCheap.lean` | `kappa_cheap_not_function` | finite signatures only |
| B | `cursor/lea-kappa-screen-7bdd` | `KappaScreen.lean` | `kappa_screen_hits_suite` | cite CSS; do not re-prove |
| C | `cursor/lea-kappa-unique-7bdd` | `KappaUnique.lean` | `bag_not_unique` | representing-screen set |
| D | `cursor/lea-kappa-relabel-7bdd` | `KappaRelabel.lean` | `kappa_relabel_natural` | bit-string relabel |
| E | `cursor/lea-aff13-7bdd` | `Aff13.lean` | `affine_escapes_kirchhoff` | `Aff` group laws |
| F | `cursor/lea-diamond-7bdd` | `DiamondInterval.lean` | `poset_not_determine_interval` | two explicit diamonds |
| G | `cursor/lea-surgery-7bdd` | `SurgeryMiss.lean` | `surgery_miss_pair_eq` | cheap signature + gold |
| H | `cursor/lea-n4-iff-7bdd` | `DtaN4.lean` | `dta_n4_representable_iff` | optional; larger |

**Launch prompt template** (paste per lane):

```text
You are lane <LETTER> of the Lea formalization wave.
Read docs/next_agent_lea_handoff_2026-08-17.md and .cursor/skills/lea/SKILL.md.
Work in an isolated git worktree from origin/main.
Own only <FILE>. Prove only blueprint node <NODE> from docs/lea/blueprint.md.
Do not edit other Lean files. Do not re-prove Path A/B or CommonSuffScreen.
Do not touch Complex.log 0. Do not import Mathlib into formal/structural-intelligence/.
Specify the Lean objects before proving. After lean_check green, run SafeVerify if available.
If /verify is unavailable, label the claim proved-not-verified.
Open a draft PR for your file only. Do not start a new scientific letter.
```

If Lea UI is the driver: one session per node, `autonomous` ok for mechanical lemmas, human/agent review of each claim before banking.

If Lea is not up yet: agents may still write **mathlib-free** Lean by hand in `formal/` using existing `lake build`, then later replay through Lea/SafeVerify. Prefer Lea when the key exists. Do not block Wave 2 forever on the UI.

### Wave 3 — bank and label (one integration agent after A–G are green)

**Lane INT:**

1. New worktree `cursor/lea-bank-7bdd` from updated `main`.
2. Import only files that are `lean_check` clean and, if SafeVerify ran, attach the axiom print + verify receipt.
3. Decide package:
   - Finite discrete, no analysis → `formal/structural-intelligence/` **new files**, aggregator update, no Mathlib.
   - Needs Mathlib → `formal/structural-intelligence-mathlib/` or new `formal/lea-sic-dynamics/`.
4. Update `papers/sic_dynamics/paper.md` and the matching A–F paper with a three-way label: **proved / verified / still Python**.
5. Docs sync (`system_design`, `module_explainer`). No new `experiments/` directory unless you also add a real instrument (do not fake one).
6. `python3 scripts/run_quality_checks.py` if any Python changed. Lean CI is the existing `lean-action` job — do not break `lake build`.
7. One PR. Squash-merge after ready.

### Wave 4 — only if Wave 3 is clean (optional, lower value)

- `dta_n4_representable_iff` if H did not run.
- Paper B `swap_typed_wins`.
- Catalog/menu notes (Possibility 2), still **not** a new calculus.
- Do **not** formalize slogans, empirical ratios, or OpenAI 2026.

### Parallelization rules that actually save time

- **Fan out in one turn.** Do not wait for lane A to finish before launching B–G.
- **One file per agent.** Two agents on `KappaScreen.lean` will collide.
- **Cite, don’t rebuild.** Path A/B and CommonSuffScreen are done.
- **Isolated worktrees from `origin/main`.** Never use `/workspace` if it is dirty or on an old branch. Never check out `main` in a second worktree — `/tmp/us4-search` already holds `main` and breaks local `gh pr merge` checkout. GitHub squash still works.
- **Branch names:** `cursor/<descriptive-name>-7bdd`.
- **PRs:** `ManagePullRequest` with `branch_name` and `base_branch=main`. Create draft, mark ready, then `gh pr merge N --squash`.
- **Do not** let later commits overwrite earlier ones on the same PR; rewrite if the history is messy.
- Empty leftover dirs under `experiments/` break `discover_experiment_packages`.
- Frozen historical test string `"N packages at 2026-07-14"` **tracks current N** (105). Do not add a package without bumping it in the same commit.
- `ty`: TypedDict payloads; unwrap `float | None` before `assertAlmostEqual`; `claim_tier` ∈ `{descriptive, internal, external, causal, theoretical}`; manifest `dependencies` = `[]` or `{name, version}` objects.

### What “done” means

The program is done as science when Possibility 5 stays the house and the P0/P1 lemmas are at least **proved** (and **verified** if SafeVerify is built), with papers labeled accordingly.

The program is **not** done if someone:

- announces a new κ,
- trains a net,
- reopens DR/DCR,
- or ships “Lea notes” without a Lean file.

---

## Operating constraints (this repo)

- Human director: Jawaun Brown. Agent-generated code/papers under review.
- Isolated worktrees. `/workspace` is often dirty / on `cursor/eml-zero-identity-lean-7bdd`.
- Known stale worktrees (do not reuse as `main`): `/tmp/us4-search` **is** `main` at an old tip and blocks local merge checkout. `/tmp/paper-{c,d,e,f}` are historical letter branches.
- Quality: `python3 scripts/run_quality_checks.py` before merging substantive Python. `python3 scripts/gen_provenance.py` if experiment results or run commands change.
- Experiment review skill: only when creating/preregistering experiments or promoting discovery claims. This Lea tranche is formalization of **already banked** claims — do not run a new regime-audit as if A–F were unregistered.
- Mathematical claim routing: **does** apply to new theorems. Record objects, quantifiers, assumptions, and a kill before promotion. Pair with `lake build` / `#print axioms` / SafeVerify.
- User-facing replies end with a short Bro explainer.

---

## Local continuation (human laptop)

If this cloud run dies:

```bash
git fetch origin main
git checkout main
git pull origin main
# read:
#   docs/next_agent_lea_handoff_2026-08-17.md
#   .cursor/skills/lea/SKILL.md
#   docs/lea/README.md
#   papers/sic_dynamics/paper.md
```

Then either:

- paste a model key into Lea Settings and run Wave 1–3, or
- spawn cloud agents with the Wave 2 prompt template, one lane each.

Save `papers/sic_dynamics/paper.md` locally if you want the close-out without git. The Lean work still belongs in this repo.

---

## Provenance of this handoff

Written 2026-08-17 in session `bc-01a00d99-d2d8-7c5e-a8d0-d0090dfd7bdd` after Papers A–F merged through #490 (`ce8b131`). Lea pages read: home, llms.txt, install, introducing-lea blog, GitHub README, adapter routes (`/api/runs`, sessions, projects, verify), blueprint parser, bundled `lean_lsp_proving.md` skill. Lea was **not** installed in that session (no Docker, no model key). No new Lean proofs in this PR.
