# Lea project seed — `Lea.SicDynamics`

Copy these three files into a Lea project's `.lea/` directory after you create
the project (UI or `POST /api/runs` with `project_slug=sic-dynamics` and
namespace `Lea.SicDynamics`).

| This repo | Lea project |
|---|---|
| `docs/lea/instructions.md` | `.lea/instructions.md` |
| `docs/lea/memory.md` | `.lea/memory.md` |
| `docs/lea/blueprint.md` | `.lea/blueprint.md` |

Do not treat this folder as a Lake package. Banked Lean still lands under
`formal/` after `lean_check` (and SafeVerify when available).

How to run Lea: [`.cursor/skills/lea/SKILL.md`](../../.cursor/skills/lea/SKILL.md).
What to prove and what not to: [`docs/next_agent_lea_handoff_2026-08-17.md`](../next_agent_lea_handoff_2026-08-17.md).
Local install receipt: [`ENV_STATUS.md`](ENV_STATUS.md).
