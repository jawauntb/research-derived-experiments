# Lea ENV status (2026-08-17, local laptop)

Install path: `/Users/jawaun/.local/src/Lea` (local `./install.sh --target ui`, not Docker).
Docker was available but disk was tight (~24 GB free, existing images already large).

| Need | Status |
|---|---|
| Node | v22.23.2 (Lea `.nvmrc`) |
| uv / elan / lake | present; default toolchain set to Lean 4.31.0 so `lake` is on PATH |
| Lea workspace Lean | 4.29.0 (Lea's pin; installed by setup) |
| Model keys | loaded from Doppler `cofounder`/`dev` into Lea's gitignored `.env` (not this repo) |
| SafeVerify / `/verify` | **available** (binary built; not `--skip-verify`) |
| Adapter | `http://127.0.0.1:8001` |
| UI | `./start-dev.sh` → `http://localhost:5173` (not required for the API smoke) |

Project: slug `sic-dynamics`, namespace `Lea.SicDynamics`, repo `proofs/Lea/SicDynamics`.
Seeded `.lea/{instructions,memory,blueprint}.md` from `docs/lea/`.

Smoke (core-only `EvenNat 2`, not Mathlib `Even`):

- `POST /api/sessions/{id}/lean-check` → **ok** (proved)
- `POST /api/sessions/{id}/verify` → **ok** (verified on this smoke file only)

Do not commit Lea's SQLite, `.env`, or `apps/lea-standalone/data/`.
Do not call a green `lean_check` on the SIC lane files "verified" until SafeVerify is run on those files.
