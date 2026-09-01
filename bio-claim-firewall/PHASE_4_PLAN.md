# Phase 4 plan — untrusted proposer + repairer

Derived from an offline read of `~/MIDAS` (2026-08-31). Reuse permission tracked in `PROVENANCE.md`. Every LOC number below is a target; actuals get re-measured when Phase 4 lands.

## Lift budget

- **Direct reuse**: ~657 LOC (provider base + Ollama + OpenAI-compatible + Groq subclass + PromptManager + config profiles + verifier output parser).
- **Adapt**: ~740 LOC (ModelManager minus Marker branch, TrajectoryLogger with biology fields, orchestrator repair loop, verification-status enum renamed, reasoning schema wrappers).
- **Inspiration only** (rewrite fresh, keep the shape): codegen contract error class, checker vs proposer fault split, SafeExecutor process-isolation pattern, category-dispatch repair prompts, versioned prompt directory convention.
- **Skip**: vision pipeline, Marker OCR, SymPy execution sandbox, student-feedback prompts, React frontend, Docker/Railway, FastAPI server.

## Fault-split invariant to preserve

MIDAS: `FAILED_REASONING` (math actually wrong) vs `FAILED_CODEGEN` (verifier broke).
Ours: `REJECTED_<FAULT_CODE>` (claim violates the contract) vs `CHECKER_ERROR` (verifier broke, fail-closed).

The rename in `pipeline/verification/verification_types.py`:

- `FAILED_REASONING` → `REJECTED_CLAIM`
- `FAILED_CODEGEN` → `CHECKER_ERROR`
- Drop `NEEDS_VISUAL_CONTEXT`
- Keep `VERIFIED` → maps to our `ACCEPTED_CONDITIONALLY`
- Keep `UNSUPPORTED` → maps to our `INCONCLUSIVE`
- Keep `FAILED_PIPELINE` → maps to a distinct proposer-side pipeline error (never confuse with `CHECKER_ERROR`)
- Rename `StepVerification` → `ClaimVerdict`
- Drop `CodeExecutionResult.namespace: dict` (we don't exec LLM code)

## Coupling to strip (found in MIDAS)

- `VerificationStatus.FAILED_REASONING` / `FAILED_CODEGEN` names.
- `ReasoningOutput.worked_solution` legacy property.
- `_extract_final_answer` (`\boxed{...}` LaTeX regex).
- `_THINK_RE` / `_STRIP_THINK_RE` (DeepSeek/Qwen `<think>` stripping).
- `<solution>/<step>/<claim>/<latex>/<justification>/<answer>` XML parser (local-Qwen contract) — we go JSON-schema from day one.
- `ReasoningStep.latex_expression` field, `TrajectoryRecord.latex_expression` field.
- `_extract_final_answer_pair` / `_extract_note_field` regex in `verification_orchestrator.py`.
- Model names in `config.yaml`: `phi4-mini-reasoning`, `qwen2.5-coder:7b-instruct`, `qwen2.5vl:7b`, `qwen3:8b`, `gemini-2.5-flash`. Replace with our Phase 4 choice.
- Task names `reasoning` / `verification` / `reasoning_repair` → `proposer` / `checker` / `repairer`.
- `Codegen*Error` category names (`emit_final_count`, `missing_helper`, `simplify_instance_method`, `forbidden_json_dumps`) → replace with biology-contract categories.
- Everything under `pipeline/vision/`, `models/services/`, `pipeline/verification/executor.py`, `pipeline/verification/environment.py`.

## Third-party deps to license-vet independently

All permissive; still record them:

- `pydantic` (MIT), `pyyaml` (MIT), `jinja2` (BSD-3), `httpx` (BSD-3), `tenacity` (Apache-2), `openai` (Apache-2), `ollama` (MIT), `truststore` (MIT), `pillow` (HPND).
- MIDAS does **not** actually use LiteLLM (README aside); providers are wired directly.

## `bio-claim-firewall/src/` layout for Phase 4

```
bio-claim-firewall/
├── prompts/
│   ├── proposer/claim_bundle/v1/{system.j2,user.j2,config.yaml}   # shape from MIDAS prompts/reasoning/solve/v3/
│   └── repairer/claim_repair/{v1,v2}/{system.j2,user.j2,config.yaml} # versioned repair contracts; v2 matches the parser
│
├── src/
│   ├── config/
│   │   ├── config.yaml                     # rewrite: tasks = {proposer, checker, repairer}; drop services.marker/vision/validation/json_repair/group_problems/explain_step
│   │   └── profiles.py                     # LIFT: MIDAS src/config/profiles.py
│   ├── model_manager/
│   │   ├── manager.py                      # ADAPT: MIDAS src/models/manager.py (drop marker branch)
│   │   ├── adapter.py                      # Phase 4c: bridge Phase 4b's call shape to configured prompts
│   │   ├── prompts.py                      # LIFT: MIDAS src/models/prompts.py
│   │   └── providers/
│   │       ├── base.py                     # LIFT: MIDAS src/models/providers/base.py
│   │       ├── ollama.py                   # LIFT: strip image branches
│   │       ├── openai_sdk.py               # LIFT: strip image branches
│   │       └── groq_provider.py            # LIFT
│   ├── proposer/
│   │   ├── types.py                        # REWRITE (bio schema); shape from MIDAS src/pipeline/reasoning/types.py
│   │   ├── proposer.py                     # ADAPT schema wrappers only (lines 22-39, 42-98, 106-201, 294-323)
│   │   └── contract.py                     # REWRITE pydantic ClaimBundleSchema + validator
│   ├── repairer/
│   │   └── repairer.py                     # REWRITE; shape of _attempt_reasoning_repair from MIDAS verification_orchestrator.py:171-293
│   ├── orchestrator/
│   │   ├── orchestrator.py                 # ADAPT verify_with_repair loop (MIDAS verification_orchestrator.py:89-169)
│   │   └── status.py                       # ADAPT VerificationStatus/StepVerification enums (rename per §Fault-split invariant)
│   ├── checker/                            # Phase 3 rule engine lives here; NO MIDAS import
│   │   └── parser.py                       # LIFT: MIDAS src/pipeline/verification/parser.py (rename final_answer_verified key)
│   └── trajectory/
│       └── logger.py                       # ADAPT: MIDAS src/pipeline/trajectory.py (rename fields)
│
└── tests/
    ├── test_prompt_contract.py             # mirror tests/test_baseline_prompt_repair_contracts.py
    ├── test_orchestrator_status_cascade.py # mirror tests/test_verification_pipeline.py
    ├── test_model_manager.py               # mirror tests/manager/test_model_manager.py
    ├── test_prompts.py                     # mirror tests/prompts/test_prompts.py
    └── test_parser_alignment.py            # mirror tests/verification/test_step_alignment.py
```

## Contract-tests to mirror (minimum set)

- **`test_prompt_contract.py`** — configured `prompt_ref` is used verbatim; JSON schema attaches when provider is hosted; missing top-level fields raise `ContractError`; `prompt_version` recorded in trajectory metadata.
- **`test_model_manager.py`** — config validation (missing provider/model/undefined-provider-ref fails at load); task→provider dispatch; timeout precedence (task > default; call-site > task); stats accumulate; `session()` calls `cleanup()`.
- **`test_orchestrator_status_cascade.py`** — every failure branch produces the right status: proposer-JSON-invalid → `CHECKER_ERROR`; rule-engine rejects → `REJECTED_<FAULT_CODE>`; rule cascade all-accept → `ACCEPTED_CONDITIONALLY`.
- **`test_prompts.py`** — versioned load; caching; `StrictUndefined` catches missing template vars; `clear_cache()` works.
- **`test_parser_alignment.py`** — parser emits `duplicate`/`missing`/`unexpected` claim-alignment errors correctly against the JSONL contract.
- **`test_phase4_adapter.py`** — real manager uses configured, versioned proposer/repairer prompts; the adapter preserves metadata and timeout overrides.

## Prohibited moves during Phase 4

- No lifting SymPy-executor code, even for the process-isolation pattern (rewrite if needed).
- No lifting math-domain prompts. All prompts under `bio-claim-firewall/prompts/` are new.
- LLM output stays data. No generated Python / SQL / DSL enters the runtime. The contract validator is pydantic + one hand-written checker function.
- Every prompt file has a version tag in its path; no in-place edits. New version → new subdirectory.
- `MODEL_VERSION`, `PROMPT_VERSION`, seed, and provider go into every trajectory record and every accepted-claim derivation.
