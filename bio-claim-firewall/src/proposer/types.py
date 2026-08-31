"""Types returned by `src/proposer`.

Shape adapted from MIDAS `src/pipeline/reasoning/types.py`'s
`ReasoningOutput` (a frozen dataclass carrying the parsed model output
plus its own provenance: prompt_ref/prompt_version/provider/model/token
counts/latency), rewritten for the biology claim-grammar contract: instead
of a list of proof steps + final answer, a `ClaimBundle` carries a tuple of
schema-valid `Claim` dicts (untyped `dict` on purpose -- claims are
verified structurally by `src/verifier`, never re-typed into a proposer-
owned Python class; LLM output stays data all the way through).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClaimBundle:
    """The proposer's parsed, contract-checked output for one `propose()` call.

    Attributes:
        claims: the parsed claim dicts, each schema-shaped per
            `spec/claim.schema.json` (required top-level fields present;
            `claim_id` guaranteed to be a UUID string, filled in
            client-side if the model's own value wasn't one). Full
            JSON-Schema conformance (CURIE prefixes, enums, patterns) is
            NOT re-validated here -- that is `src/verifier`'s job.
        prompt_ref: the prompt reference resolved by `ModelManager.call`
            (echoed back on `ChatResponse.prompt_ref`).
        prompt_version: the concrete resolved prompt version (e.g. `"v1"`).
        provider: which model provider served this call.
        model: the concrete model name/id used.
        tokens_prompt: prompt tokens consumed, as reported by the provider.
        tokens_completion: completion tokens consumed.
        latency_ms: wall-clock latency of the model call, in milliseconds.
    """

    claims: tuple[dict, ...]
    prompt_ref: str
    prompt_version: str
    provider: str
    model: str
    tokens_prompt: int
    tokens_completion: int
    latency_ms: int
