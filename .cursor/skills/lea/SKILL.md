---
name: lea
description: Use Lea (VIDA-NYU Lean 4 agent backbone) to formalize already-specified claims. Use when asked to prove, formalize, kernel-check, SafeVerify, or machine-check Lean theorems; when standing up LeaChat/LeaOverleaf; or when banking proved vs verified files into this repo. Do not use for new scientific letters, Paper 0 / Complex.log 0, or importing Mathlib into mathlib-free cores.
---

# Lea

## Purpose

Lea is a **Lean 4 agent backbone**. The mathematician (or this agent acting as one) steers the decomposition, intervenes mid-proof, and reviews each claim. It is not an autonomous “dump a paper in, get theorems out” service, and it is not a new scientific object for this program.

In this repo, Lea is the licensed **method** after Papers A–F. The house claim is Possibility 5: delete–repair is SIC’s dynamics. Use Lea to machine-check Python-only load-bearing lemmas. Do not use Lea to invent Paper G.

Primary handoff: `docs/next_agent_lea_handoff_2026-08-17.md`.
Project seed: `docs/lea/`.

## Load references only when needed

- Install / first proof: https://vida-nyu.github.io/Lea/install/
- Design commitments: https://vida-nyu.github.io/Lea/llms.txt
- Blog: https://vida-nyu.github.io/Lea/blog/introducing-lea/
- Source: https://github.com/VIDA-NYU/Lea
- SafeVerify: https://github.com/GasStationManager/SafeVerify
- This program’s blueprint: `docs/lea/blueprint.md`

## Two states, never collapsed

| Word | Means | Not enough |
|---|---|---|
| **Proved** | The file elaborates. Lean accepted it. No `sorry`. | A green UI badge you did not re-run |
| **Verified** | SafeVerify: kernel replay + per-declaration type/body match + axiom whitelist | `lean_check: 0 errors` alone |

Status is derived from the latest Lean verdict. Do not store “proved” as a sticky label in markdown and then skip the checker.

Ways a compile can be clean and the claim still false: namespace shadowing, a supporting definition redefined, a `sorry` arriving through an import. That is why the states stay split.

When SafeVerify was skipped (`./install.sh --target ui --skip-verify`), `/verify` reports unavailable. Say **proved-not-verified**. Re-run setup without `--skip-verify` before claiming verified.

## When to use / when not to

**Use Lea when:**

- A claim is already specified (objects, quantifiers, kill criteria).
- The claim is theorem-level and still Python-only or only cited.
- You can put it on a blueprint node with `uses:` edges.

**Do not use Lea to:**

- Re-prove `repair_paths_disagree`, `CommonSuffScreen`, US-2/US-3, or `eml_zero_identity`.
- Formalize slogans, empirical `Φ` ratios, GD 8/8, extras 43/28, or OpenAI 2026 writeups.
- Touch Paper 0 / `Complex.log 0`.
- Import Mathlib into `formal/structural-intelligence/` cores (`DeleteRepair.lean`, `EmlZeroIdentity.lean`, `Compiler/SquaringSeparation.lean`).
- Fit a cheaper signature so Paper E’s `pair_eq` miss disappears.
- Start a new scientific letter.

## Install

Lea runs on your machine. VIDA hosts the image, not your proofs. You need **one** model key (`OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY`, or LiteLLM / self-hosted vLLM). The app boots without a key; proving does not.

Docker image ≈ 3.7 GB download, ≈ 10.7 GB extracted. Keep ~20 GB free.

```bash
# Option A — Docker (laptop)
git clone https://github.com/VIDA-NYU/Lea.git
cd Lea/apps/lea-standalone
docker compose pull
docker compose up
# http://localhost:8001 — Settings → paste key

# Option B — local (Node 22 + uv + elan)
git clone https://github.com/VIDA-NYU/Lea.git
cd Lea
./install.sh --target ui            # add SafeVerify later without --skip-verify
./start-dev.sh                      # UI at :5173, adapter at :8001
npm run doctor                      # when something is weird
```

Persistence lives under `apps/lea-standalone/{data,config,proofs,projects}`. Do **not** commit those, nor `.env`, nor keys, into this research repo.

## Project cycle

A project outlives a run. It fixes a Lean namespace and three documents:

| File | Role |
|---|---|
| `.lea/instructions.md` | Rules. Agent reads every run. |
| `.lea/memory.md` | Durable facts. Append; do not rewrite history. |
| `.lea/blueprint.md` | Lemma DAG. Status is *not* stored in the file. |

Seed for this program: copy `docs/lea/{instructions,memory,blueprint}.md` into the Lea project (slug `sic-dynamics`, namespace `Lea.SicDynamics`).

Blueprint node format (parser is a line-scan; status/color come from live Lean):

```markdown
## kappa_cheap_not_function
- kind: theorem
- lean: `Lea.SicDynamics.KappaCheap.not_function`
- uses: cheap_signature

Same cheap 5-field signature, two golds.
```

A node is ready iff every `uses:` dependency is discharged.

## Headless API

The FastAPI adapter **is** the backend. There is no second prover server.

| Call | Why |
|---|---|
| `POST /api/runs` | Start a formalization (`project_slug`, `message`, optional `autonomous`) |
| `GET /api/runs/{id}/events` | Typed SSE ledger |
| `POST /api/sessions/{id}/lean-check` | Proved? |
| `POST /api/sessions/{id}/verify` | Verified? |
| `GET/PUT` project docs | instructions / memory / blueprint |

First `lean_check` after Mathlib load can take ~90s; later edits reuse the LSP. If every check is slow, look for `LEA_DISABLE_LSP=1`.

You may edit the Lean file by hand and hand it back. The ledger records who wrote the step.

## Banking into this repo

1. `lean_check` green, no `sorry`.
2. `#print axioms` (empty or an explicit whitelist).
3. SafeVerify if built.
4. Place the file:
   - Finite discrete, no analysis → new file under `formal/structural-intelligence/`. Update the aggregator. **No Mathlib.**
   - Needs Mathlib → `formal/structural-intelligence-mathlib/` or a new Lake package `formal/lea-sic-dynamics/`.
5. Label the paper: proved / verified / still Python.
6. Update `docs/system_design.md` and `docs/module_explainer.md`.
7. Do not add an `experiments/` package just to hold a proof.

## Parallelization

One lemma, one Lean file, one agent, one worktree from `origin/main`. See the Wave 2 table in the handoff. Do not let two agents edit the same file. When `lake lean` is green, mark the PR ready and squash-merge it. Do not wait for the other lanes or for Wave 3 INT. INT only banks aggregator imports, paper labels, and docs after files are already on `main`.

## Quality bar

A Lea run that type-checks and establishes nothing (the LeanMarathon failure mode) is a reject. The statement in Lean must be the statement we asked for. If you cannot write the objects and quantifiers in one paragraph before proving, you are not ready to run Lea.
