"""Types returned by `src/repairer`.

Shape adapted from MIDAS `verification_orchestrator.py`'s
`_attempt_reasoning_repair` return contract (`Optional[ReasoningOutput]` --
`None` meaning "repair did not produce a usable replacement"), split here
into an explicit `abstained` flag + `reason` string instead of a bare
`None`, since spec/non_goals.md requires the repairer to be able to
*decline* to guess (an explicit `abstain`) rather than silently failing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RepairResult:
    """The repairer's outcome for one `repair()` call.

    `abstained=True` always implies `claim is None` (enforced in
    `__post_init__`) -- callers can branch on `abstained` alone.

    Attributes:
        claim: the repaired claim dict (schema-shaped per the same
            top-level-required-field check `src/proposer` runs), or `None`
            if the model abstained.
        abstained: `True` iff the model declined to propose a repair.
        reason: the model's stated reason. Populated on abstain; may also
            carry a short human-readable note when `claim` is present.
        prompt_ref: the prompt reference resolved by `ModelManager.call`.
        prompt_version: the concrete resolved prompt version.
        provider: which model provider served this call.
        model: the concrete model name/id used.
        tokens_prompt: prompt tokens consumed.
        tokens_completion: completion tokens consumed.
        latency_ms: wall-clock latency of the model call, in milliseconds.
    """

    claim: dict | None
    abstained: bool
    reason: str
    prompt_ref: str
    prompt_version: str
    provider: str
    model: str
    tokens_prompt: int
    tokens_completion: int
    latency_ms: int

    def __post_init__(self) -> None:
        if self.abstained and self.claim is not None:
            raise ValueError("RepairResult: abstained=True requires claim=None")
