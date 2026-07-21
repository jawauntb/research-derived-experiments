"""Deterministic ablation transforms on prose plans.

Scaffold layer: rule-based transforms with no live-model calls. Live
paraphrase (with a rule-based cosine-similarity peer for the audit
described in the preregistration) lands in Week 2 behind the same
env-gated adapter used by ``experiments/grounded_statecharts``.
"""

from __future__ import annotations

import re

from experiments.load_bearing_prose_test.claims import (
    Ablation,
    AblationKind,
    AblationSet,
    Claim,
    ClaimBundle,
)


# Negation rules are applied longest-first to avoid overshadowing
# ("must" would otherwise swallow "must not"). Case-preserving where
# reasonable; the deterministic-executor path is not case-sensitive.
_NEGATION_RULES: tuple[tuple[str, str], ...] = (
    (r"\bmust not\b", "must"),
    (r"\bshall not\b", "shall"),
    (r"\bshould not\b", "should"),
    (r"\bwill not\b", "will"),
    (r"\bmust\b", "must not"),
    (r"\bshall\b", "shall not"),
    (r"\bshould\b", "should not"),
    (r"\bwill\b", "will not"),
    (r"\brequires\b", "does not require"),
    (r"\brequired to\b", "not required to"),
    (r"\bneeds to\b", "does not need to"),
    (r"\bforbidden to\b", "allowed to"),
    (r"\bnot allowed to\b", "allowed to"),
    (r"\ballowed to\b", "not allowed to"),
)

# Paraphrase rules must preserve semantic content by construction so
# the gauge check is meaningful. These are deliberately conservative
# rewrites of obligation modality; content words are untouched.
_PARAPHRASE_RULES: tuple[tuple[str, str], ...] = (
    (r"\bmust not\b", "is prohibited from"),
    (r"\bshall not\b", "is prohibited from"),
    (r"\bshould not\b", "is expected to avoid"),
    (r"\bwill not\b", "is going to avoid"),
    (r"\bmust\b", "is required to"),
    (r"\bshall\b", "is required to"),
    (r"\bshould\b", "is expected to"),
    (r"\bwill\b", "is going to"),
    (r"\brequires\b", "needs"),
    (r"\brequired to\b", "obligated to"),
    (r"\bneeds to\b", "must"),
    (r"\bforbidden to\b", "prohibited from"),
    (r"\bnot allowed to\b", "prohibited from"),
    (r"\ballowed to\b", "permitted to"),
)


def _compile_atomic_rules(
    rules: tuple[tuple[str, str], ...],
) -> tuple[re.Pattern[str], dict[str, str]]:
    """Compile a single regex that matches every rule key exactly once.

    Rules are joined into one alternation, ordered longest-key-first so
    ``must not`` outranks ``must``. Substitution happens through a
    callback that looks up the matched span in ``lookup``, so each
    location is transformed at most once — no round-trips.
    """

    ordered = sorted(rules, key=lambda pair: -len(pair[0]))
    combined = re.compile("|".join(pattern for pattern, _ in ordered), re.IGNORECASE)
    lookup: dict[str, str] = {}
    for pattern, replacement in ordered:
        key = _pattern_key(pattern)
        lookup.setdefault(key, replacement)
    return combined, lookup


def _pattern_key(pattern: str) -> str:
    return pattern.replace(r"\b", "").strip().lower()


def _apply_atomic(
    text: str,
    compiled: tuple[re.Pattern[str], dict[str, str]],
) -> str:
    regex, lookup = compiled

    def _replace(match: re.Match[str]) -> str:
        key = _pattern_key(match.group(0))
        return lookup.get(key, match.group(0))

    return regex.sub(_replace, text)


_NEGATION_COMPILED = _compile_atomic_rules(_NEGATION_RULES)
_PARAPHRASE_COMPILED = _compile_atomic_rules(_PARAPHRASE_RULES)


def _slice_plan(bundle: ClaimBundle, plan_text: str, claim: Claim) -> tuple[str, str, str]:
    if len(plan_text) < claim.end_offset:
        raise ValueError(
            f"plan_text too short for claim {claim.claim_id} (end={claim.end_offset})"
        )
    prefix = plan_text[: claim.start_offset]
    middle = plan_text[claim.start_offset : claim.end_offset]
    suffix = plan_text[claim.end_offset :]
    if middle.strip() != claim.text.strip():
        raise ValueError(
            f"plan_text/bundle mismatch at claim {claim.claim_id}: "
            f"expected {claim.text!r}, found {middle!r}"
        )
    # `bundle` is passed for symmetry with future signatures that will
    # need per-bundle metadata (e.g., extractor version); silence lint.
    _ = bundle
    return prefix, middle, suffix


def delete_claim(bundle: ClaimBundle, plan_text: str, claim: Claim) -> Ablation:
    """Remove the claim sentence and any adjacent whitespace runoff."""

    prefix, _, suffix = _slice_plan(bundle, plan_text, claim)
    # Collapse the join to a single space if both sides had content;
    # otherwise trim leading whitespace on the suffix.
    if prefix and not prefix.endswith(("\n", " ")):
        joined = prefix + " " + suffix.lstrip()
    else:
        joined = prefix + suffix.lstrip()
    modified = joined.rstrip() + ("\n" if plan_text.endswith("\n") else "")
    if not modified.strip():
        # Ensure the modified plan is non-empty for the type invariant.
        modified = "(intentionally emptied by delete ablation)\n"
    return Ablation(
        plan_id=bundle.plan_id,
        claim_id=claim.claim_id,
        kind=AblationKind.DELETE,
        modified_plan=modified,
    )


def negate_claim(bundle: ClaimBundle, plan_text: str, claim: Claim) -> Ablation:
    """Replace the claim sentence with its logical negation."""

    prefix, middle, suffix = _slice_plan(bundle, plan_text, claim)
    negated = _apply_atomic(middle, _NEGATION_COMPILED)
    if negated == middle:
        # No modal verb matched — the extractor found the sentence by a
        # modal, so this is an internal invariant violation.
        raise ValueError(
            f"negate_claim produced no change for claim {claim.claim_id}"
        )
    return Ablation(
        plan_id=bundle.plan_id,
        claim_id=claim.claim_id,
        kind=AblationKind.NEGATE,
        modified_plan=prefix + negated + suffix,
    )


def paraphrase_claim(bundle: ClaimBundle, plan_text: str, claim: Claim) -> Ablation:
    """Replace the claim sentence with a semantics-preserving rewrite."""

    prefix, middle, suffix = _slice_plan(bundle, plan_text, claim)
    paraphrased = _apply_atomic(middle, _PARAPHRASE_COMPILED)
    if paraphrased == middle:
        raise ValueError(
            f"paraphrase_claim produced no change for claim {claim.claim_id}"
        )
    return Ablation(
        plan_id=bundle.plan_id,
        claim_id=claim.claim_id,
        kind=AblationKind.PARAPHRASE,
        modified_plan=prefix + paraphrased + suffix,
    )


def ablate_bundle(bundle: ClaimBundle, plan_text: str) -> AblationSet:
    """Produce all three ablation kinds for every claim in ``bundle``."""

    ablations: list[Ablation] = []
    for claim in bundle.claims:
        ablations.append(delete_claim(bundle, plan_text, claim))
        ablations.append(negate_claim(bundle, plan_text, claim))
        ablations.append(paraphrase_claim(bundle, plan_text, claim))
    return AblationSet(
        bundle_digest=bundle.bundle_digest,
        ablations=tuple(ablations),
    )
